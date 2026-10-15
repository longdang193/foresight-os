import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_delivery_is_host_facing_and_not_a_participant_skill():
    skill_path = ROOT / ".agents" / "skills" / "foresight-delivery" / "SKILL.md"
    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    architecture_text = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "src" / "foresight_os" / "skills" / "manifest.json").read_text(encoding="utf-8"))

    assert skill_path.is_file()
    assert ".agents/skills/" in agents_text
    assert "foresight-delivery" in architecture_text
    assert "foresight-delivery" not in {item["id"] for item in manifest["skills"]}


def test_delivery_procedure_keeps_pause_cancel_deferred():
    delivery_text = (ROOT / ".agents" / "skills" / "foresight-delivery" / "SKILL.md").read_text(encoding="utf-8")

    assert "provider success without local receipt persistence" in delivery_text
    assert "Cross-process pause and cancel remain deferred" in delivery_text
