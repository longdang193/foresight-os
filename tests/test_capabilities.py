import asyncio

import pytest

from foresight_os.runtime.capabilities import CapabilityDefinition, CapabilityResolver, CapabilityScope
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

    context = {"scope": scope, "local_capabilities": {"graph": lambda _: calls.append(True) or resource}}
    first = resolver.resolve(("graph",), context)
    second = resolver.resolve(("graph",), context)

    assert first["graph"].tool is resource
    assert second["graph"].tool is resource
    assert len(calls) == 1
    asyncio.run(scope.close())
    assert resource.closed


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
