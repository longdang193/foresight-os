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


async def _boundary_probes() -> dict[str, bool]:
    from foresight_os.controller.budgets import BudgetState
    from foresight_os.runtime.capabilities import CapabilityDefinition, instrument_tool
    from foresight_os.runtime.local_toolbelt import ToolbeltError, spreadsheet_read
    from foresight_os.runtime.metrics import BudgetExceededError, RunMetrics

    calls = []

    async def tool():
        calls.append(True)

    metrics = RunMetrics("anomaly-boundaries", "DIRECT", "direct")
    wrapped = instrument_tool(tool, CapabilityDefinition("probe", "local_deterministic"), {"budget": BudgetState(5, 1, 5, max_tool_calls=1), "metrics": metrics})
    await wrapped()
    try:
        await wrapped()
    except BudgetExceededError:
        budget = len(calls) == 1 and metrics.budget_failures == 1
    else:
        budget = False

    try:
        spreadsheet_read(ROOT / "tests" / "fixtures" / "analyst_multisheet.xlsx", cancel_check=lambda: True)
    except ToolbeltError as error:
        cancellation = str(error) == "cancelled"
    else:
        cancellation = False

    try:
        await asyncio.wait_for(asyncio.sleep(0.01), timeout=0)
    except asyncio.TimeoutError:
        timeout = True
    else:
        timeout = False
    return {"budget": budget, "cancellation": cancellation, "timeout": timeout}


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
        try:
            open_files = len(process.open_files())
        except (psutil.Error, OSError):
            open_files = None
        try:
            child_processes = len(process.children(recursive=True))
        except (psutil.Error, OSError):
            child_processes = None
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


async def _mixed_schedule(index: int) -> dict:
    if index % 4 == 0:
        return {"scenario": "success", **await _run_once(index)}
    if index % 4 == 1:
        return {"scenario": "concurrent", "results": await asyncio.gather(_run_once(index), _run_once(index + 10000))}
    if index % 4 == 2:
        return {"scenario": "boundary", "boundaries": await _boundary_probes()}
    try:
        await asyncio.wait_for(asyncio.sleep(0.01), timeout=0)
    except asyncio.TimeoutError:
        return {"scenario": "timeout", "timeout": True}
    return {"scenario": "timeout", "timeout": False}


async def _leak_control_probe() -> bool:
    before = _snapshot()
    retained = [bytearray(1024 * 1024)]
    task = asyncio.create_task(asyncio.sleep(60))
    try:
        after = _snapshot()
        detected = _sample_has_resource_drift({"before": before, "after": after})
        detected = detected or after["memory_bytes"] > before["memory_bytes"]
        return detected
    finally:
        retained.clear()
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


def _sample_has_resource_drift(sample: dict) -> bool:
    before = sample["before"]
    after = sample["after"]
    for key in ("unfinished_tasks", "open_files", "child_processes", "handles"):
        if before.get(key) is not None and after.get(key) is not None and after[key] > before[key]:
            return True
    return False


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
        outcome = await _mixed_schedule(index + 10)
        gc.collect()
        after = _snapshot()
        samples.append({"before": before, "after": after})
        if outcome.get("scenario") == "success":
            state_hashes.append(outcome["state_hash"])
            if not outcome["cleanup_complete"] or outcome["failure_class"] is not None:
                failures.append(outcome)
            if baseline is None:
                baseline = outcome
            elif outcome != baseline:
                failures.append({"failure_class": "metric_drift"})
        elif outcome.get("scenario") == "concurrent":
            failures.extend(item for item in outcome["results"] if not item["cleanup_complete"] or item["failure_class"] is not None)
        elif outcome.get("scenario") == "boundary" and not all(outcome["boundaries"].values()):
            failures.append(outcome)
        elif outcome.get("scenario") == "timeout" and not outcome["timeout"]:
            failures.append(outcome)
    memory_values = [sample["after"]["memory_bytes"] for sample in samples]
    memory_growth = max(0, max(memory_values) - memory_values[0]) if memory_values else 0
    memory_growth_exceeded = memory_growth > 4 * 1024 * 1024
    handle_values = [sample["after"]["handles"] for sample in samples if sample["after"]["handles"] is not None]
    monotonic_handles = bool(handle_values) and all(left <= right for left, right in zip(handle_values, handle_values[1:])) and handle_values[-1] > handle_values[0]
    boundaries = await _boundary_probes()
    leak_control_detected = await _leak_control_probe()
    resource_leak_samples = [index for index, sample in enumerate(samples) if _sample_has_resource_drift(sample)]
    result = {
        "mode": "anomaly",
        "status": "failed" if failures or resource_leak_samples or memory_growth_exceeded or len(set(state_hashes)) != 1 or monotonic_handles or not all(boundaries.values()) or not leak_control_detected else "verified",
        "runs": runs,
        "seed": seed,
        "warmup_runs": warmup,
        "state_hash_stable": len(set(state_hashes)) == 1,
        "monotonic_handle_accumulation": monotonic_handles,
        "memory_min": min(memory_values) if memory_values else None,
        "memory_max": max(memory_values) if memory_values else None,
        "memory_growth_bytes": memory_growth,
        "memory_growth_exceeded": memory_growth_exceeded,
        "failures": failures,
        "boundary_probes": boundaries,
        "leak_control_detected": leak_control_detected,
        "resource_leak_samples": resource_leak_samples,
        "samples": samples,
    }
    tracemalloc.stop()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--seed", default="846f4ed")
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--output-root", type=Path, default=ROOT / "work" / "toolbelt-probes")
    args = parser.parse_args()
    report = asyncio.run(run_probe(args.runs, args.seed, args.warmup))
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "anomaly-probe.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
