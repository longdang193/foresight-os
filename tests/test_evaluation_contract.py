import hashlib
import json
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).parents[1]
CASE = ROOT / "evaluation" / "cases" / "case-001"


def test_evaluation_contract_contains_frozen_case_and_reference_findings():
    decision = (CASE / "decision.md").read_text(encoding="utf-8")
    workbook = (CASE / "workbook.csv").read_text(encoding="utf-8")
    reference = json.loads((CASE / "reference.json").read_text(encoding="utf-8"))

    assert "Should the strategy team increase investment" in decision
    assert "Northern Europe" in workbook
    assert reference["case_id"] == "case-001"
    assert len(reference["reference_findings"]) == 3
    assert len(reference["contradictions"]) == 1


def test_reference_locators_are_reproducible_and_complete():
    reference = json.loads((CASE / "reference.json").read_text(encoding="utf-8"))

    for finding in reference["reference_findings"]:
        locator = finding["source_locator"]
        assert set(locator) == {
            "file_version",
            "sheet",
            "range",
            "units",
            "transformation",
            "calculation",
        }
        assert all(locator.values())


def test_three_level_contract_preserves_fair_comparison():
    evaluation = (ROOT / "evaluation" / "README.md").read_text(encoding="utf-8")
    baseline = (ROOT / "evaluation" / "baseline" / "README.md").read_text(encoding="utf-8")

    assert "A — ordinary prompt" in evaluation
    assert "B — semantic" in evaluation
    assert "C — coordination" in evaluation
    assert "same level-B inputs" in baseline
    assert "same case, rubric, source version" in baseline


def test_case_is_deterministic_and_contains_no_customer_data_markers():
    paths = sorted(CASE.glob("*"))
    first = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
    second = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
    content = "\n".join(path.read_text(encoding="utf-8") for path in paths if path.suffix in {".md", ".json", ".csv"})

    assert first == second
    assert "customer" not in content.lower()
    assert "confidential" not in content.lower()


def test_candidate_score_reads_the_selected_recipe_output(tmp_path: Path):
    import sys

    sys.path.insert(0, str(ROOT / "evaluation"))
    from candidate_harness import run_candidate
    from run import _score_candidate

    reference = json.loads((CASE / "reference.json").read_text(encoding="utf-8"))
    candidate = run_candidate(CASE, "sequential", tmp_path / "candidate")
    baseline = _score_candidate(candidate, reference)
    claim = candidate["recipe_output"]["analysis_state"].claims[0]
    candidate["recipe_output"]["analysis_state"] = replace(
        candidate["recipe_output"]["analysis_state"],
        claims=[replace(claim, statement="mutated candidate output")],
    )

    changed = _score_candidate(candidate, reference)

    assert changed["finding_coverage"] < baseline["finding_coverage"]


def test_candidate_score_fails_closed_without_recipe_output():
    import sys

    sys.path.insert(0, str(ROOT / "evaluation"))
    from run import _score_candidate

    reference = json.loads((CASE / "reference.json").read_text(encoding="utf-8"))
    score = _score_candidate({"metrics": {"pattern": "sequential"}}, reference)

    assert not score["admitted"]
