from foresight_os.domain.models import ExecutionIntent
from foresight_os.wayfinding import create_work_brief, refine_work_brief


def test_refinement_records_typed_intent_and_preferences_without_topology_resolution():
    brief = refine_work_brief(
        create_work_brief("Question", investigation_id="refine"),
        user_preferences={"review": "independent"},
        required_capabilities=("spreadsheet_read",),
        preferred_patterns=("sequential",),
    )
    assert isinstance(brief.execution_intent, ExecutionIntent)
    assert brief.execution_intent.required_capabilities == ("spreadsheet_read",)
    assert brief.execution_intent.preferred_patterns == ("sequential",)
    assert brief.user_preferences["review"] == "independent"
