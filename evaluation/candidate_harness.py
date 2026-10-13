from dataclasses import asdict
from pathlib import Path
import tempfile

from foresight_os.controller.recipes import RecipeName, make_recipe
from foresight_os.controller.policy import select_recipe
from foresight_os.controller.task_shape import TaskShape
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.workflow import run_recipe
from foresight_os.vertical_slice import run_vertical_slice
from foresight_os.wayfinding import create_work_brief
from participant_scope import ParticipantScope


def run_candidate(
    case_dir: Path,
    candidate: str,
    work_dir: Path | None = None,
    output_root: Path | None = None,
    participant_scope: ParticipantScope | None = None,
) -> dict:
    if work_dir is not None and output_root is not None:
        raise ValueError("pass work_dir or output_root, not both")
    work_dir = work_dir or (output_root / case_dir.name / candidate if output_root else Path(tempfile.mkdtemp(prefix="foresight-eval-") ) / case_dir.name / candidate)
    workbook = participant_scope.resolve(case_dir / "workbook.csv") if participant_scope is not None else case_dir / "workbook.csv"
    outcome = run_vertical_slice(workbook, work_dir, human_accept=True)
    state = AnalysisStore(work_dir).load_analysis() if outcome.accepted else None
    recipe_name = {
        "direct": RecipeName.DIRECT,
        "ordinary": RecipeName.DIRECT,
        "semantic": RecipeName.ANALYZE,
        "sequential": RecipeName.ANALYZE_REVIEW,
        "controller": RecipeName.ANALYZE_REVIEW,
        "concurrent": RecipeName.CONCURRENT,
        "handoff": RecipeName.HANDOFF,
        "group_chat": RecipeName.CHALLENGE_RECOMMENDATION,
    }.get(candidate)
    recipe = (
        select_recipe(
            create_work_brief(f"Evaluate {case_dir.name}."),
            TaskShape(independent_subtasks=True, interactive_deliberation=True, review_required=True),
        )
        if candidate == "composed"
        else make_recipe(recipe_name)
    )
    result = run_recipe(recipe, f"Evaluate {case_dir.name}.")
    recipe_output = {
        "pattern": result.metrics.pattern,
        "status": "completed" if result.metrics.settled and result.metrics.failure_class is None else "failed",
        "analysis_state": state,
    }
    return {
        "candidate": candidate,
        "outcome": outcome,
        "state": state,
        "analysis_state": state,
        "recipe_output": recipe_output,
        "artifact": outcome.report_path if outcome.accepted else None,
        "run_id": result.metrics.run_id,
        "metrics": asdict(result.metrics),
    }
