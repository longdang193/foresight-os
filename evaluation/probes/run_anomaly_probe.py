import argparse
import asyncio
import gc
import hashlib
import json
import sys
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "src"))

from foresight_os.controller.recipes import RecipeName, make_recipe
from foresight_os.runtime.workflow import run_recipe_async


def _snapshot() -> dict[str, int | None]:
    try:
        import psutil

        process = psutil.Process()
        open_files = None
        child_processes = None
        try:
            handles = process.num_handles()
        except (AttributeError, psutil.Error, OSError):
            handles = None
    except ImportError:
        open_files = child_processes = handles = None
    return {
        "open_files": open_files,
        "child_processes": child_processes,
        "handles": handles,
        "unfinished_tasks": len([task for task in asyncio.all_tasks() if not task.done()]),
        "memory_bytes": tracemalloc.get_traced_memory()[0],
    }


async def _run_once(index: int) -> dict:
    result = await run_recipe_async(make_recipe(RecipeName.DIRECT), "bounded anomaly probe", run_id=f"anomaly-{index}")
    state_hash = hashlib.sha256(json.dumps(result.outputs, sort_keys=True, default=str).encode()).hexdigest()
    return {
        "state_hash": state_hash,
        "cleanup_complete": result.metrics.cleanup_complete,
        "failure_class": result.metrics.failure_class,
        "tool_calls": result.metrics.tool_calls,
        "model_calls": result.metrics.model_calls,
    }


async def run_probe(runs: int, seed: str, warmup: int = 10) -> dict:
    import random

    random.seed(seed)
    tracemalloc.start()
    for index in range(warmup):
        await _run_once(index)
    samples = []
    state_hashes = []
    failures = []
    baseline = None
    for index in range(runs):
        gc.collect()
        before = _snapshot()
        outcome = await _run_once(index + 10)
        gc.collect()
        after = _snapshot()
        samples.append({"before": before, "after": after})
        state_hashes.append(outcome["state_hash"])
        if not outcome["cleanup_complete"] or outcome["failure_class"] is not None:
            failures.append(outcome)
        if baseline is None:
            baseline = outcome
        elif outcome != baseline:
            failures.append({"failure_class": "metric_drift"})
    memory_values = [sample["after"]["memory_bytes"] for sample in samples]
    handle_values = [sample["after"]["handles"] for sample in samples if sample["after"]["handles"] is not None]
    monotonic_handles = bool(handle_values) and all(left <= right for left, right in zip(handle_values, handle_values[1:])) and handle_values[-1] > handle_values[0]
    result = {
        "mode": "anomaly",
        "status": "failed" if failures or len(set(state_hashes)) != 1 or monotonic_handles else "verified",
        "runs": runs,
        "seed": seed,
        "warmup_runs": warmup,
        "state_hash_stable": len(set(state_hashes)) == 1,
        "monotonic_handle_accumulation": monotonic_handles,
        "memory_min": min(memory_values) if memory_values else None,
        "memory_max": max(memory_values) if memory_values else None,
        "failures": failures,
        "samples": samples,
    }
    tracemalloc.stop()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--seed", default="846f4ed")
    parser.add_argument("--warmup", type=int, default=10)
    args = parser.parse_args()
    report = asyncio.run(run_probe(args.runs, args.seed, args.warmup))
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
