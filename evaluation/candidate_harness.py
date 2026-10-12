from dataclasses import asdict
from pathlib import Path

from foresight_os.controller.recipes import RecipeName, make_recipe
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.workflow import run_recipe
from foresight_os.vertical_slice import run_vertical_slice


def run_candidate(case_dir: Path, candidate: str, work_dir: Path | None = None) -> dict:
    work_dir = work_dir or case_dir.parents[2] / "work" / case_dir.name / candidate
    outcome = run_vertical_slice(case_dir / "workbook.csv", work_dir, human_accept=True)
    state = AnalysisStore(work_dir).load_analysis() if outcome.accepted else None
    recipe_name = {
        "ordinary": RecipeName.DIRECT,
        "semantic": RecipeName.ANALYZE,
        "sequential": RecipeName.ANALYZE_REVIEW,
        "controller": RecipeName.ANALYZE_REVIEW,
        "concurrent": RecipeName.CONCURRENT,
        "handoff": RecipeName.HANDOFF,
        "group_chat": RecipeName.CHALLENGE_RECOMMENDATION,
    }[candidate]
    result = run_recipe(make_recipe(recipe_name), f"Evaluate {case_dir.name}.")
    return {
        "candidate": candidate,
        "outcome": outcome,
        "state": state,
        "metrics": asdict(result.metrics),
    }
