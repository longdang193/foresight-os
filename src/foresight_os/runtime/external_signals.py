from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from foresight_os.runtime.capabilities import CapabilityBinding, CapabilityBindingKind, CapabilityOwnership


class HostedMCPError(RuntimeError):
    def __init__(self, failure_class: str, message: str):
        super().__init__(message)
        self.failure_class = failure_class


@dataclass(frozen=True)
class HostedMCPProvider:
    provider_id: str
    capability_id: str
    endpoint: str
    credential_env: str
    auth_mode: str
    allowed_tools: tuple[str, ...] | None = None
    credential_optional: bool = False


HOSTED_MCP_PROVIDERS = {
    "github": HostedMCPProvider(
        "github",
        "technology_signals",
        "https://api.githubcopilot.com/mcp/",
        "GITHUB_MCP_TOKEN",
        "bearer",
        (
            "get_file_contents",
            "get_latest_release",
            "list_commits",
            "list_issues",
            "list_pull_requests",
            "list_releases",
            "search_code",
            "search_commits",
            "search_issues",
            "search_pull_requests",
            "search_repositories",
        ),
    ),
    "alpha_vantage": HostedMCPProvider(
        "alpha_vantage",
        "market_signals",
        "https://mcp.alphavantage.co/mcp",
        "ALPHAVANTAGE_API_KEY",
        "query",
        (
            "GLOBAL_QUOTE",
            "MARKET_STATUS",
            "NEWS_SENTIMENT",
            "SYMBOL_SEARCH",
            "TIME_SERIES_DAILY",
            "TREASURY_YIELD",
            "CPI",
            "REAL_GDP",
        ),
    ),
    "fred": HostedMCPProvider(
        "fred",
        "macro_signals",
        "https://mcp.stlouisfed.org",
        "FRED_MCP_TOKEN",
        "bearer",
        None,
    ),
}


def _alpha_endpoint(endpoint: str, api_key: str) -> str:
    parts = urlsplit(endpoint)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["apikey"] = api_key
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _fingerprint(provider: HostedMCPProvider, endpoint: str, credential: str) -> str:
    parts = urlsplit(endpoint)
    safe_endpoint = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    digest = hashlib.sha256(credential.encode("utf-8")).hexdigest()[:16]
    return f"{provider.provider_id}-mcp-v1:{safe_endpoint}:{digest}"


def create_hosted_mcp_tool(
    provider_id: str,
    credential: str,
    *,
    endpoint: str | None = None,
    tool_factory: Any | None = None,
    allowed_tools: tuple[str, ...] | None = None,
) -> Any:
    provider = HOSTED_MCP_PROVIDERS.get(provider_id)
    if provider is None:
        raise HostedMCPError("configuration", f"unknown hosted MCP provider: {provider_id}")
    if not credential.strip() and not provider.credential_optional:
        raise HostedMCPError("missing_credential", f"missing credential for {provider.credential_env}")
    try:
        if tool_factory is None:
            from agent_framework import MCPStreamableHTTPTool

            tool_factory = MCPStreamableHTTPTool
    except ImportError as error:
        raise HostedMCPError("dependency_missing", "agent-framework MCP support is not installed") from error
    target = endpoint or provider.endpoint
    static_headers: dict[str, str] = {}
    if provider.auth_mode == "bearer":
        static_headers["Authorization"] = f"Bearer {credential}"
    elif provider.auth_mode == "query":
        target = _alpha_endpoint(target, credential)
    else:
        raise HostedMCPError("configuration", f"unsupported auth mode: {provider.auth_mode}")
    effective_allowed_tools = allowed_tools or provider.allowed_tools
    if provider_id == "fred" and not effective_allowed_tools:
        raise HostedMCPError("read_policy_missing", "FRED MCP requires an explicit read-only tool allowlist")
    kwargs: dict[str, Any] = {
        "name": f"foresight-{provider.provider_id}",
        "url": target,
        "load_prompts": False,
        "approval_mode": "never_require",
        "terminate_on_close": False,
    }
    if effective_allowed_tools is not None:
        kwargs["allowed_tools"] = effective_allowed_tools
    if static_headers:
        kwargs["static_headers"] = static_headers
    return tool_factory(**kwargs)


def load_hosted_mcp_bindings(
    environment: Mapping[str, str] | None = None,
    *,
    tool_factory: Any | None = None,
    required_capabilities: set[str] | tuple[str, ...] | None = None,
    activate: bool = True,
) -> dict[str, CapabilityBinding]:
    values = os.environ if environment is None else environment
    bindings: dict[str, CapabilityBinding] = {}
    for provider_id, provider in HOSTED_MCP_PROVIDERS.items():
        if required_capabilities is not None and provider.capability_id not in required_capabilities:
            continue
        credential = str(values.get(provider.credential_env, "")).strip()
        if not credential:
            continue
        endpoint = str(values.get(f"FORESIGHT_{provider_id.upper()}_MCP_URL", provider.endpoint)).strip()
        allowed_tools = None
        if provider_id == "fred":
            read_tool = str(values.get("FRED_MCP_READ_TOOL", "")).strip()
            if read_tool:
                allowed_tools = (read_tool,)
        fingerprint = _fingerprint(provider, endpoint, credential)
        if activate:
            value = create_hosted_mcp_tool(
                provider_id,
                credential,
                endpoint=endpoint,
                tool_factory=tool_factory,
                allowed_tools=allowed_tools,
            )
            bindings[provider.capability_id] = CapabilityBinding(
                value,
                ownership=CapabilityOwnership.OWNED,
                fingerprint=fingerprint,
            )
            continue

        def factory(
            _context: Mapping[str, Any],
            *,
            provider_id: str = provider_id,
            credential: str = credential,
            endpoint: str = endpoint,
            allowed_tools: tuple[str, ...] | None = allowed_tools,
        ) -> Any:
            return create_hosted_mcp_tool(
                provider_id,
                credential,
                endpoint=endpoint,
                tool_factory=tool_factory,
                allowed_tools=allowed_tools,
            )

        bindings[provider.capability_id] = CapabilityBinding(
            factory,
            kind=CapabilityBindingKind.RESOURCE_FACTORY,
            ownership=CapabilityOwnership.OWNED,
            fingerprint=fingerprint,
        )
    return bindings


def bind_hosted_mcp(provider_id: str, credential: str, **kwargs: Any) -> CapabilityBinding:
    provider = HOSTED_MCP_PROVIDERS.get(provider_id)
    if provider is None:
        raise HostedMCPError("configuration", f"unknown hosted MCP provider: {provider_id}")
    endpoint = str(kwargs.get("endpoint") or provider.endpoint)
    tool = create_hosted_mcp_tool(
        provider_id,
        credential,
        tool_factory=kwargs.get("tool_factory"),
        endpoint=endpoint,
        allowed_tools=kwargs.get("allowed_tools"),
    )
    return CapabilityBinding(
        tool,
        ownership=CapabilityOwnership.OWNED,
        fingerprint=_fingerprint(provider, endpoint, credential),
    )
