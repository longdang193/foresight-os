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
from foresight_os.persistence.analysis_store import AnalysisStore, StageReceipt
from foresight_os.runtime.workflow import _canonical_result_hash, _stage_cache_key


def _recipe() -> ExecutionRecipe:
    base = make_recipe(RecipeName.DIRECT)
    first = RecipeStage("first", ExecutionPattern.DIRECT, ({"id": "first", "purpose": "first"},), "prompt", "typed-result", {})
    second = RecipeStage("second", ExecutionPattern.DIRECT, ({"id": "second", "purpose": "second"},), "prompt", "typed-result", {})
    return ExecutionRecipe(base.name, base.pattern, base.roles, base.max_agent_steps, base.max_correction_rounds, base.max_total_agent_calls, base.completion, base.escalation, base.partial_result, stages=(first, second))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    recipe = _recipe()
    first_output = {"stage": "first"}
    second_output = {"stage": "second"}
    cache = {
        _stage_cache_key(recipe.stages[0], "start", ()): {"status": "committed", "provenance_complete": True, "result_references": ["claim-first"], "result_hashes": [_canonical_result_hash(first_output)], "output": {"tampered": True}},
        _stage_cache_key(recipe.stages[1], first_output, ()): {"status": "committed", "provenance_complete": True, "result_references": ["claim-second"], "result_hashes": [_canonical_result_hash(second_output)], "output": {"tampered": True}},
    }
    cache_path = args.output_root / "cache.json"
    cache_path.write_text(json.dumps(cache, sort_keys=True), encoding="utf-8")
    code = """
import asyncio, json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from evaluation.probes.run_selective_reuse_probe import _recipe
from foresight_os.runtime.workflow import run_recipe_async
cache = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
canonical_records = {'claim-first': {'stage': 'first'}, 'claim-second': {'stage': 'second'}}
result = asyncio.run(run_recipe_async(_recipe(), 'start', run_context={'stage_cache': cache, 'canonical_records': canonical_records}))
print(json.dumps({'cache_hits': result.metrics.cache_hits, 'reassessed_stages': result.metrics.reassessed_stages, 'model_calls': result.metrics.model_calls, 'output': result.outputs[-1]}))
"""
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    completed = subprocess.run([sys.executable, "-c", code, str(ROOT), str(cache_path)], capture_output=True, text=True, env=env, check=False)
    report: dict[str, object] = {"fresh_process": True, "returncode": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}
    if completed.returncode == 0:
        observed = json.loads(completed.stdout)
        report["observed"] = observed
        report["passed"] = observed == {"cache_hits": 2, "reassessed_stages": 0, "model_calls": 0, "output": second_output}
    else:
        report["passed"] = False
    store = AnalysisStore(args.output_root / "receipt-store")
    receipt = StageReceipt("first", "input-v1", result_references=("claim-1",), result_hashes=("hash-1",), status="committed", committed=True, provenance_complete=True)
    store.save_stage_receipt(receipt)
    report["receipt_reusable"] = store.load_stage_receipts()["first"].reusable()
    report["passed"] = bool(report["passed"] and report["receipt_reusable"])
    (args.output_root / "selective-reuse-report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
