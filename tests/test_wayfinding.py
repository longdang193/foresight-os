from foresight_os.domain.models import ExecutionIntent, MethodProvenance
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


def test_work_brief_accepts_caller_supplied_method_provenance_without_host_file_access(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    brief = create_work_brief(
        "Question",
        producer=MethodProvenance(
            id="foresight-wayfinding",
            source=".agents/skills/foresight-wayfinding/SKILL.md",
            contract_version="1",
            content_sha256="abc123",
        ),
    )

    assert brief.producer.id == "foresight-wayfinding"
    assert brief.execution_intent is None
