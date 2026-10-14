import pytest

from foresight_os.domain.models import ExecutionIntent, WorkBrief
from foresight_os.domain.validation import ValidationError, validate_work_brief


def test_legacy_pattern_override_migrates_to_required_intent_without_reemitting_legacy_field():
    value = validate_work_brief({
        "investigation_id": "legacy",
        "decision_question": "Question",
        "scope": [],
        "desired_deliverables": ["answer"],
        "assumptions": [],
        "open_dependencies": [],
        "current_direction": "direction",
        "next_useful_step": "next",
        "execution_pattern_override": "sequential",
    })
    assert value["execution_intent"]["required_patterns"] == ["sequential"]
    assert "execution_pattern_override" not in value


def test_canonical_work_brief_serialization_keeps_preferences_and_intent_only():
    brief = WorkBrief(
        "current",
        "Question",
        [],
        ["answer"],
        [],
        [],
        "direction",
        "next",
        user_preferences={"review": "independent"},
        execution_intent=ExecutionIntent(preferred_patterns=("sequential",)),
    )
    value = validate_work_brief(brief)
    assert value["user_preferences"] == {"review": "independent"}
    assert value["execution_intent"]["preferred_patterns"] == ["sequential"]
    assert "execution_pattern_override" not in value


def test_required_and_preferred_intent_conflict_is_rejected():
    with pytest.raises(ValidationError, match="require and prefer"):
        validate_work_brief({
            "investigation_id": "conflict",
            "decision_question": "Question",
            "scope": [],
            "desired_deliverables": ["answer"],
            "assumptions": [],
            "open_dependencies": [],
            "current_direction": "direction",
            "next_useful_step": "next",
            "execution_intent": {
                "required_patterns": ["direct"],
                "preferred_patterns": ["direct"],
            },
        })


def test_producer_null_fields_are_rejected_by_the_schema():
    with pytest.raises(ValidationError, match="not of type 'string'"):
        validate_work_brief({
            "investigation_id": "producer-null",
            "decision_question": "Question",
            "scope": [],
            "desired_deliverables": ["answer"],
            "assumptions": [],
            "open_dependencies": [],
            "current_direction": "direction",
            "next_useful_step": "next",
            "producer": {"id": None, "source": None, "contract_version": None},
        })


def test_producer_unknown_fields_are_rejected_by_the_schema():
    with pytest.raises(ValidationError, match="unexpected"):
        validate_work_brief({
            "investigation_id": "producer-extra",
            "decision_question": "Question",
            "scope": [],
            "desired_deliverables": ["answer"],
            "assumptions": [],
            "open_dependencies": [],
            "current_direction": "direction",
            "next_useful_step": "next",
            "producer": {
                "id": "producer",
                "source": "source",
                "contract_version": "1",
                "unexpected": "value",
            },
        })
