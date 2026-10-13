import asyncio

from evaluation.probes.run_external_signal_probe import _provider_result_is_success
from foresight_os.runtime.capabilities import CapabilityResolver, CapabilityScope
from foresight_os.runtime.external_signals import (
    HOSTED_MCP_PROVIDERS,
    bind_hosted_mcp,
    create_hosted_mcp_tool,
    load_hosted_mcp_bindings,
)
from foresight_os.runtime.participants import AgentFactory, ParticipantConfig


class FakeMCPTool:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.closed = False

    async def close(self):
        self.closed = True


def test_provider_specs_are_read_only_and_vendor_neutral():
    assert set(HOSTED_MCP_PROVIDERS) == {"github", "alpha_vantage", "fred"}
    assert {item.capability_id for item in HOSTED_MCP_PROVIDERS.values()} == {
        "technology_signals",
        "market_signals",
        "macro_signals",
    }
    assert all(item.auth_mode in {"bearer", "query"} for item in HOSTED_MCP_PROVIDERS.values())


def test_alpha_endpoint_keeps_credentials_out_of_fingerprint_and_uses_query_auth():
    binding = bind_hosted_mcp("alpha_vantage", "secret", tool_factory=FakeMCPTool)
    assert "secret" not in binding.fingerprint
    assert binding.value.kwargs["url"].endswith("apikey=secret")
    assert "allowed_tools" in binding.value.kwargs


def test_load_bindings_requires_explicit_credentials():
    assert load_hosted_mcp_bindings({}, tool_factory=FakeMCPTool) == {}
    bindings = load_hosted_mcp_bindings(
        {"GITHUB_MCP_TOKEN": "github-token", "ALPHAVANTAGE_API_KEY": "alpha-key"},
        tool_factory=FakeMCPTool,
    )
    assert set(bindings) == {"technology_signals", "market_signals"}


def test_hosted_mcp_tool_is_injected_into_maf_agent_and_scope_closes_it():
    captured = {}

    class Client:
        def as_agent(self, **kwargs):
            captured.update(kwargs)
            return object()

    binding = bind_hosted_mcp("github", "github-token", tool_factory=FakeMCPTool)
    scope = CapabilityScope()
    resolver = CapabilityResolver()
    AgentFactory(Client()).create(
        ParticipantConfig("analyst", "analyst", "find technology signals", capability_ids=("technology_signals",), data_scope=("public",)),
        {"scope": scope, "capability_resolver": resolver, "mcp_tools": {"technology_signals": binding}},
    )
    assert captured["tools"][0] is binding.value
    asyncio.run(scope.close())
    assert binding.value.closed


def test_unknown_provider_is_rejected():
    try:
        create_hosted_mcp_tool("unknown", "token", tool_factory=FakeMCPTool)
    except Exception as error:
        assert getattr(error, "failure_class", None) == "configuration"
    else:
        raise AssertionError("unknown provider should fail")


def test_fred_requires_explicit_read_only_allowlist():
    try:
        bind_hosted_mcp("fred", "token", tool_factory=FakeMCPTool)
    except Exception as error:
        assert getattr(error, "failure_class", None) == "read_policy_missing"
    else:
        raise AssertionError("FRED should require a read-only allowlist")

    binding = bind_hosted_mcp("fred", "token", tool_factory=FakeMCPTool, allowed_tools=("series_observations",))
    assert binding.value.kwargs["allowed_tools"] == ("series_observations",)


def test_external_probe_rejects_provider_error_envelopes():
    assert not _provider_result_is_success("alpha_vantage", {"Information": "The Global Quote endpoint is rate limited. Retry tomorrow."})
    assert _provider_result_is_success("alpha_vantage", {"Global Quote": {"01. symbol": "IBM", "05. price": "1.0"}})
    assert not _provider_result_is_success("github", {"message": "Bad credentials", "items": []})
    assert _provider_result_is_success("github", {"total_count": 0, "items": []})
    assert not _provider_result_is_success("fred", {"Information": "rate limit"})
    assert _provider_result_is_success("fred", {"observations": []})
