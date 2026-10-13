from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "src"))

from foresight_os.controller.recipes import ExecutionPattern, ExecutionRecipe, RecipeName, RecipeStage, make_recipe
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.workflow import CanonicalStageResult, _canonical_result_hash, run_recipe_async


def _recipe() -> ExecutionRecipe:
    base = make_recipe(RecipeName.DIRECT)
    first = RecipeStage("first", ExecutionPattern.DIRECT, ({"id": "first", "purpose": "first"},), "prompt", "typed-result", {})
    second = RecipeStage("second", ExecutionPattern.DIRECT, ({"id": "second", "purpose": "second"},), "prompt", "typed-result", {}, dependencies=("first",))
    third = RecipeStage("third", ExecutionPattern.DIRECT, ({"id": "third", "purpose": "third"},), "prompt", "typed-result", {})
    return ExecutionRecipe(base.name, base.pattern, base.roles, base.max_agent_steps, base.max_correction_rounds, base.max_total_agent_calls, base.completion, base.escalation, base.partial_result, stages=(first, second, third))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    recipe = _recipe()
    receipt_root = args.output_root / "receipt-store"
    canonical_path = args.output_root / "canonical-records.json"
    code = """
import asyncio, json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from evaluation.probes.run_selective_reuse_probe import _recipe
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.workflow import CanonicalStageResult, _canonical_result_hash, run_recipe_async
recipe = _recipe()
store = AnalysisStore(Path(sys.argv[2]))
mode = sys.argv[3]
canonical_path = Path(sys.argv[4])
canonical_records = json.loads(canonical_path.read_text(encoding='utf-8')) if canonical_path.exists() else {}
if mode == 'mutate':
    canonical_records['claim-first'] = {'stage': 'first', 'revision': 'changed'}
mutation = 'changed' if mode == 'mutate' else 'base'
def commit(stage, _output, _context):
    stage_id = stage.stage_id
    reference = f'claim-{stage_id}'
    output = {'stage': stage_id, 'revision': mutation}
    return CanonicalStageResult((reference,), (_canonical_result_hash(output),), output)
run_context = {'analysis_store': store, 'canonical_records': canonical_records}
if mode != 'reuse':
    run_context['canonical_result_committer'] = commit
result = asyncio.run(run_recipe_async(recipe, 'start', run_context=run_context))
if mode == 'cold':
    canonical_path.write_text(json.dumps(run_context['canonical_records'], sort_keys=True), encoding='utf-8')
print(json.dumps({'cache_hits': result.metrics.cache_hits, 'reassessed_stages': result.metrics.reassessed_stages, 'model_calls': result.metrics.model_calls, 'output': result.outputs[-1]}))
"""
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    runs = {}
    for mode in ("cold", "reuse", "mutate"):
        completed = subprocess.run([sys.executable, "-c", code, str(ROOT), str(receipt_root), mode, str(canonical_path)], capture_output=True, text=True, env=env, check=False)
        runs[mode] = {"returncode": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}
        if completed.returncode == 0:
            runs[mode]["observed"] = json.loads(completed.stdout)
    expected_reuse = {"cache_hits": 3, "reassessed_stages": 0, "model_calls": 0, "output": {"stage": "third", "revision": "base"}}
    expected_mutation = {"cache_hits": 1, "reassessed_stages": 2, "model_calls": 0, "output": {"stage": "third", "revision": "base"}}
    report: dict[str, object] = {
        "fresh_process": True,
        "runs": runs,
        "receipt_reusable": AnalysisStore(receipt_root).load_stage_receipts().get("first").reusable(),
    }
    report["passed"] = bool(
        runs.get("cold", {}).get("returncode") == 0
        and runs.get("reuse", {}).get("observed") == expected_reuse
        and runs.get("mutate", {}).get("observed") == expected_mutation
        and report["receipt_reusable"]
    )
    (args.output_root / "selective-reuse-report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
