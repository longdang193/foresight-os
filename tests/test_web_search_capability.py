import asyncio
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from foresight_os.controller.budgets import BudgetState
from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeName, RecipeStage
from foresight_os.runtime.capabilities import CapabilityResolver, CapabilityScope, instrument_tool
from foresight_os.runtime.metrics import RunMetrics
from foresight_os.runtime.web_search import (
    ConfiguredWebSearchProvider,
    SearxngWebSearchProvider,
    WebSearchCapability,
    WebSearchError,
    WebSearchHit,
    bind_web_search,
    load_configured_web_search_provider,
)
from foresight_os.runtime.workflow import run_recipe_async


class _Provider:
    name = "fixture-web"
    fingerprint = "fixture-web-v1"

    async def search(self, query, *, max_results=5, freshness=None):
        return [WebSearchHit("Capacity report", "https://example.test/capacity", "Capacity remains uncertain.", source=self.name)]


def test_web_search_capability_returns_validated_candidates_without_raw_payload():
    results = asyncio.run(WebSearchCapability(_Provider())("capacity"))

    assert len(results) == 1
    assert results[0]["capability_id"] == "web_search"
    assert results[0]["acquisition_kind"] == "web_search"
    assert results[0]["provenance"]["url"] == "https://example.test/capacity"
    assert "raw_result" not in results[0]


def test_web_search_rejects_empty_query_and_malformed_result():
    with_error = WebSearchCapability(_Provider())
    try:
        asyncio.run(with_error("  "))
    except WebSearchError as error:
        assert "empty" in str(error)
    else:
        raise AssertionError("empty query was accepted")

    class MalformedProvider(_Provider):
        async def search(self, query, *, max_results=5, freshness=None):
            return [{"title": "", "url": "", "snippet": ""}]

    try:
        asyncio.run(WebSearchCapability(MalformedProvider())("capacity"))
    except WebSearchError as error:
        assert "source identity" in str(error)
    else:
        raise AssertionError("malformed result was accepted")


def test_configured_provider_runs_through_capability_resolution_and_instrumentation():
    seen = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            seen["authorization"] = self.headers.get("Authorization")
            seen["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            payload = json.dumps({
                "results": [{
                    "title": "Capacity report",
                    "url": "https://example.test/capacity",
                    "snippet": "Capacity remains uncertain.",
                }],
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        provider = ConfiguredWebSearchProvider(f"http://127.0.0.1:{server.server_port}/search", "secret-token")
        scope = CapabilityScope()
        metrics = RunMetrics("web-search", "WEB_SEARCH", "web_search")
        resolver = CapabilityResolver()
        resolved = asyncio.run(resolver.resolve_async(("web_search",), {
            "scope": scope,
            "metrics": metrics,
            "budget": BudgetState(5, 1, 5, max_tool_calls=2),
            "participant_data_scope": ("public",),
            "adapters": {"web_search": bind_web_search(provider)},
        }))
        tool = instrument_tool(resolved["web_search"].tool, resolved["web_search"].definition, {"scope": scope, "metrics": metrics, "budget": BudgetState(5, 1, 5, max_tool_calls=2)})
        results = asyncio.run(tool("capacity"))

        assert results[0]["capability_id"] == "web_search"
        assert metrics.tool_calls == 1
        assert seen["authorization"] == "Bearer secret-token"
        assert seen["body"]["query"] == "capacity"
        assert "secret-token" not in json.dumps(results)
        asyncio.run(scope.close())
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_searxng_provider_uses_json_search_endpoint_and_normalizes_fields():
    seen = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen["path"] = self.path
            payload = json.dumps({
                "results": [{
                    "title": "SearXNG result",
                    "url": "https://example.test/searxng",
                    "content": "A result returned by the local metasearch service.",
                    "publishedDate": "2026-10-13",
                    "engine": "fixture",
                }],
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        provider = SearxngWebSearchProvider(f"http://127.0.0.1:{server.server_port}", language="en")
        hits = asyncio.run(provider.search("local search", max_results=3))

        assert hits == [{
            "title": "SearXNG result",
            "url": "https://example.test/searxng",
            "snippet": "A result returned by the local metasearch service.",
            "published_at": "2026-10-13",
            "source": "searxng:fixture",
        }]
        assert "q=local+search" in seen["path"]
        assert "format=json" in seen["path"]
        assert "language=en" in seen["path"]
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_configured_provider_loader_selects_searxng_explicitly():
    provider = load_configured_web_search_provider({
        "FORESIGHT_WEB_SEARCH_PROVIDER": "searxng",
        "FORESIGHT_WEB_SEARCH_URL": "http://127.0.0.1:8888",
    })

    assert isinstance(provider, SearxngWebSearchProvider)
    assert provider.name == "searxng"


def test_run_scope_wires_web_search_into_a_real_participant_tool_cycle():
    class Agent:
        id = "participant-1"

        def __init__(self, tools):
            self.tools = tools

        async def run(self, prompt):
            return type("Response", (), {"value": await self.tools[0]("capacity")})()

        async def close(self):
            return None

    class Client:
        def as_agent(self, **kwargs):
            return Agent(kwargs["tools"])

    stage = RecipeStage(
        "stage-1",
        ExecutionPattern.DIRECT,
        ({"id": "participant-1", "purpose": "retrieve evidence", "capability_ids": ("web_search",)},),
        "prompt",
        "typed-result",
        {"max_agent_steps": 5, "max_total_agent_calls": 3},
    )
    recipe = ExecutionRecipe(
        RecipeName.DIRECT,
        "direct",
        [],
        5,
        1,
        3,
        "complete",
        "review",
        "partial",
        stages=(stage,),
    )

    result = asyncio.run(run_recipe_async(recipe, "find capacity", Client(), run_context={"web_search_provider": _Provider()}))

    assert result.outputs[0][0]["capability_id"] == "web_search"
    assert result.metrics.tool_calls == 1
    assert result.metrics.cleanup_complete
