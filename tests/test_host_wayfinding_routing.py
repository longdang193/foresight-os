import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_repo_local_wayfinding_route_is_unique_and_host_facing():
    skill_path = ROOT / ".agents" / "skills" / "foresight-wayfinding" / "SKILL.md"
    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "src" / "foresight_os" / "skills" / "manifest.json").read_text(encoding="utf-8"))

    assert skill_path.is_file()
    assert ".agents/skills/foresight-wayfinding/SKILL.md" in agents_text
    assert "foresight-wayfinding" not in {item["id"] for item in manifest["skills"]}
    assert "src/foresight_os/skills" in agents_text


def test_canonical_intake_does_not_require_generic_map_artifact():
    store_source = (ROOT / "src" / "foresight_os" / "persistence" / "analysis_store.py").read_text(encoding="utf-8")
    proposal_source = (ROOT / "src" / "foresight_os" / "controller" / "proposal.py").read_text(encoding="utf-8")
    approval_source = (ROOT / "src" / "foresight_os" / "artifacts" / "approval.py").read_text(encoding="utf-8")

    assert "map.md" not in store_source
    assert "map.md" not in proposal_source
    assert "map.md" not in approval_source
