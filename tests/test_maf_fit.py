from foresight_os.runtime.capabilities import (
    CapabilityDecision,
    DEFERRED_CAPABILITIES,
    REQUIRED_CAPABILITIES,
)
from foresight_os.runtime.maf_probe import (
    checkpoint_round_trip,
    maf_package_available,
    probe_capabilities,
    vertical_slice_guardrail,
)
from foresight_os.runtime.workflow import run_sequential_steps


def test_probe_returns_one_decision_for_every_required_capability():
    results = {result.name: result for result in probe_capabilities()}

    assert set(REQUIRED_CAPABILITIES).issubset(results)
    assert all(result.decision in CapabilityDecision for result in results.values())
    if not maf_package_available():
        assert all(results[name].decision == CapabilityDecision.UNSUPPORTED for name in REQUIRED_CAPABILITIES)
    else:
        assert results["single_agent"].decision == CapabilityDecision.ADAPT_AT_BOUNDARY
        assert results["sequential_review"].decision == CapabilityDecision.USE_NATIVE
        assert results["checkpoint_restart"].decision == CapabilityDecision.USE_NATIVE


def test_checkpoint_round_trip_uses_maf_storage():
    assert maf_package_available()
    assert checkpoint_round_trip()


def test_group_chat_and_magentic_are_deferred():
    results = {result.name: result for result in probe_capabilities()}

    assert all(results[name].decision == CapabilityDecision.DEFER for name in DEFERRED_CAPABILITIES)


def test_vertical_slice_guardrail_is_explicit():
    guardrail = vertical_slice_guardrail()

    assert guardrail.max_agent_steps == 5
    assert guardrail.max_correction_rounds == 1
    assert guardrail.max_total_agent_calls == 3
    assert "no accepted recommendation" in guardrail.exhaustion_outcome


def test_sequential_review_uses_native_workflow_builder():
    assert run_sequential_steps(["analyst", "reviewer"])["completed_stages"] == ["analyst", "reviewer"]
