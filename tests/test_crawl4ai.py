import asyncio
import sys
from types import SimpleNamespace

import pytest

from foresight_os.domain.evidence import normalize_evidence_candidate
from foresight_os.runtime.capabilities import CapabilityResolver, CapabilityScope
from foresight_os.runtime.crawl4ai import Crawl4AIError, Crawl4AICapability, bind_crawl4ai
from foresight_os.runtime.participants import AgentFactory, ParticipantConfig


class _FakeCrawler:
    closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        self.closed = True

    async def arun(self, url):
        return SimpleNamespace(
            success=True,
            status_code=200,
            url=url,
            markdown="# Report\nCapacity remains uncertain.",
            links={"internal": ["https://example.test/next"]},
        )


def test_crawl4ai_returns_provenance_and_proof(monkeypatch):
    monkeypatch.setitem(sys.modules, "crawl4ai", SimpleNamespace(AsyncWebCrawler=_FakeCrawler))
    result = asyncio.run(Crawl4AICapability(fixture_hosts={"example.test"})("https://example.test/report", "capacity"))

    assert result["capability_id"] == "web_crawl"
    assert result["provenance"]["http_status"] == "200"
    assert result["retrieval_proof"].is_valid()
    assert "raw_result" not in result
    assert normalize_evidence_candidate(result).source_locator.file_version == result["provenance"]["content_hash"]


def test_crawl4ai_rejects_private_urls():
    with pytest.raises(Crawl4AIError) as error:
        asyncio.run(Crawl4AICapability()("http://127.0.0.1:8080/private"))
    assert error.value.failure_class == "blocked_network_target"


def test_crawl4ai_is_injected_into_maf_agent_tools(monkeypatch):
    monkeypatch.setitem(sys.modules, "crawl4ai", SimpleNamespace(AsyncWebCrawler=_FakeCrawler))
    captured = {}

    class Client:
        def as_agent(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(id=kwargs["id"])

    scope = CapabilityScope()
    factory = AgentFactory(Client())
    factory.create(
        ParticipantConfig("analyst", "analyst", "crawl", capability_ids=("web_crawl",), data_scope=("public",)),
        {
            "scope": scope,
            "capability_resolver": CapabilityResolver(),
            "adapters": {"web_crawl": bind_crawl4ai(Crawl4AICapability(fixture_hosts={"example.test"}))},
        },
    )
    result = asyncio.run(captured["tools"][0]("https://example.test/report"))

    assert result["capability_id"] == "web_crawl"
    assert captured["tools"][0].capability_id == "web_crawl"


def test_crawl4ai_uses_concrete_installed_strategy(monkeypatch):
    import crawl4ai
    from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

    class CompatibleCrawler(_FakeCrawler):
        def __init__(self, **kwargs):
            self.strategy = kwargs.get("crawler_strategy")

        async def arun(self, url, **kwargs):
            assert isinstance(self.strategy, AsyncPlaywrightCrawlerStrategy)
            return await super().arun(url)

    monkeypatch.setattr(crawl4ai, "AsyncWebCrawler", CompatibleCrawler)
    result = asyncio.run(Crawl4AICapability(fixture_hosts={"example.test"})("https://example.test/report"))
    assert result["capability_id"] == "web_crawl"
