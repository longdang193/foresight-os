import asyncio

import pytest

from foresight_os.controller.recipes import RecipeName, make_recipe
from foresight_os.domain.approval import AdaptationEnvelope
from foresight_os.runtime.execution_gate import classify_material_changes
from foresight_os.runtime.metrics import RunCanceledError
from foresight_os.runtime.orchestration import RunControl
from foresight_os.runtime.workflow import run_recipe_async


def test_cancel_settles_before_new_stage_dispatch():
    control = RunControl("cancelled")
    control.request_cancel()
    with pytest.raises(RunCanceledError, match="canceled"):
        asyncio.run(run_recipe_async(make_recipe(RecipeName.DIRECT), "Question", run_context={"run_control": control}))


def test_pause_waits_until_resume_before_stage_dispatch():
    control = RunControl("paused")
    control.request_pause()

    async def run():
        task = asyncio.create_task(run_recipe_async(make_recipe(RecipeName.DIRECT), "Question", run_context={"run_control": control}))
        await asyncio.sleep(0.02)
        assert not task.done()
        control.request_resume()
        return await task

    result = asyncio.run(run())
    assert result.metrics.settled
    assert any(event.event == "paused" for event in control.events)


def test_material_change_classification_respects_narrow_envelope():
    envelope = AdaptationEnvelope(allowed_operations=("bounded_retry", "reduced_concurrency"))
    changes = classify_material_changes(
        {"retry": 0, "provider": "local"},
        {"retry": 1, "provider": "external"},
        envelope,
    )
    assert {item["field"] for item in changes} == {"retry", "provider"}
    assert next(item for item in changes if item["field"] == "retry")["requires_reapproval"] is False
    assert next(item for item in changes if item["field"] == "provider")["requires_reapproval"] is True
