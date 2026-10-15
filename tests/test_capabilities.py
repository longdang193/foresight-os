import asyncio

import pytest

from foresight_os.runtime.capabilities import (
    CapabilityBinding,
    CapabilityBindingKind,
    CapabilityDefinition,
    CapabilityOwnership,
    CapabilityResolver,
    CapabilityScope,
    prepare_capability_context,
)
from foresight_os.runtime.participants import AgentFactory, ParticipantConfig


class Closeable:
    def __init__(self):
        self.closed = False

    async def close(self):
        self.closed = True


def test_resolver_is_lazy_and_reuses_run_scope_binding():
    scope = CapabilityScope()
    resource = Closeable()
    calls = []
    resolver = CapabilityResolver({"graph": CapabilityDefinition("graph", "local_deterministic")})

    context = {
        "scope": scope,
        "local_capabilities": {
            "graph": CapabilityBinding(lambda _: calls.append(True) or resource, CapabilityBindingKind.RESOURCE_FACTORY, CapabilityOwnership.OWNED, fingerprint="graph-resource"),
        },
    }
    first = resolver.resolve(("graph",), context)
    second = resolver.resolve(("graph",), context)

    assert first["graph"].tool is resource
    assert second["graph"].tool is resource
    assert len(calls) == 1
    asyncio.run(scope.close())
    assert resource.closed


def test_tool_binding_is_not_invoked_during_resolution():
    calls = []

    def tool(_context):
        calls.append(True)

    resolver = CapabilityResolver({"tool": CapabilityDefinition("tool", "local_deterministic")})
    result = resolver.resolve(("tool",), {"local_capabilities": {"tool": CapabilityBinding(tool)}})

    assert result["tool"].tool is tool
    assert calls == []


def test_async_resource_factory_is_supported_by_async_resolution():
    resource = Closeable()

    async def factory(_context):
        return resource

    scope = CapabilityScope()
    resolver = CapabilityResolver({"resource": CapabilityDefinition("resource", "external_read")})
    result = asyncio.run(
        resolver.resolve_async(
            ("resource",),
            {"scope": scope, "local_capabilities": {"resource": CapabilityBinding(factory, CapabilityBindingKind.RESOURCE_FACTORY, CapabilityOwnership.OWNED)}},
        )
    )

    assert result["resource"].tool is resource
    asyncio.run(scope.close())
    assert resource.closed


def test_run_cache_does_not_alias_distinct_bindings_for_one_capability():
    scope = CapabilityScope()
    first = object()
    second = object()
    resolver = CapabilityResolver({"resource": CapabilityDefinition("resource", "external_read")})

    result = resolver.resolve(
        ("resource",),
        {"scope": scope, "local_capabilities": {"resource": CapabilityBinding(lambda _: first, CapabilityBindingKind.RESOURCE_FACTORY, fingerprint="first")}},
    )
    replacement = resolver.resolve(
        ("resource",),
        {"scope": scope, "local_capabilities": {"resource": CapabilityBinding(lambda _: second, CapabilityBindingKind.RESOURCE_FACTORY, fingerprint="second")}},
    )

    assert result["resource"].tool is first
    assert replacement["resource"].tool is second


def test_resolver_reports_unavailable_and_human_mutation_denial():
    resolver = CapabilityResolver(
        {
            "missing": CapabilityDefinition("missing", "external_read"),
            "write": CapabilityDefinition("write", "external_mutation", "write", approval_policy="HUMAN"),
        }
    )
    result = resolver.resolve(("missing", "write"), {"scope": CapabilityScope()})

    assert not result["missing"].available
    assert "unavailable" in result["missing"].reason
    assert not result["write"].available
    assert "approval" in result["write"].reason


def test_factory_rejects_participant_capability_denial():
    class Client:
        def as_agent(self, **kwargs):
            return object()

    resolver = CapabilityResolver({"missing": CapabilityDefinition("missing", "external_read")})
    with pytest.raises(RuntimeError, match="unavailable"):
        AgentFactory(Client()).create(
            ParticipantConfig("scout", "scout", "search", capability_ids=("missing",)),
            {"capability_resolver": resolver, "scope": CapabilityScope()},
        )


def test_factory_guides_json_safe_spreadsheet_tool_arguments():
    captured = {}

    class Client:
        def as_agent(self, **kwargs):
            captured.update(kwargs)
            return object()

    context = prepare_capability_context(("spreadsheet_read",), {"scope": CapabilityScope()}, human_approved=True)
    AgentFactory(Client()).create(
        ParticipantConfig("analyst", "analyst", "read a workbook", capability_ids=("spreadsheet_read",)),
        context,
    )

    assert "omit limits" in captured["instructions"].lower()


def test_prepare_capability_context_is_shared_and_preserves_fingerprints():
    scope = CapabilityScope()

    context = prepare_capability_context(
        ("spreadsheet_read",),
        {
            "scope": scope,
            "human_approved": True,
            "capability_fingerprints": ("local-toolbelt-v1",),
        },
    )

    assert context["scope"] is scope
    assert context["required_capabilities"] == ("spreadsheet_read",)
    assert context["capability_fingerprints"] == ("local-toolbelt-v1",)
    assert context["capability_resolutions"]["spreadsheet_read"].available
