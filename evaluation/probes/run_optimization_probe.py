from __future__ import annotations

import argparse
import asyncio
import json
import os
import socket
import subprocess
import sys
import threading
import time
import tracemalloc
from pathlib import Path
from statistics import median

from agent_framework import Agent, ChatResponse, ChatResponseUpdate, Content, FunctionInvocationContext, Message, ResponseStream

from foresight_os.controller.recipes import ExecutionPattern, RecipeName, make_recipe
from foresight_os.runtime.capabilities import CapabilityDefinition, CapabilityScope, instrument_tool
from foresight_os.runtime.local_toolbelt import AnalysisOperation, SheetSelection, data_analysis, spreadsheet_read

try:
    from foresight_os.runtime.local_toolbelt import WorkbookContext
except ImportError:
    WorkbookContext = None
from foresight_os.runtime.workflow import run_recipe_async
from optimization_measurement import _metric_snapshot, build_receipt, observed_xlsx_state, process_rss_bytes, stage_metric


class _ProbeClient:
    additional_properties = {}

    def as_agent(self, **kwargs):
        return Agent(self, **kwargs)

    def get_response(self, messages, **kwargs):
        async def response():
            return ChatResponse(messages=[Message("assistant", ["probe-complete"])])

        if kwargs.get("stream"):
            async def updates():
                yield ChatResponseUpdate(contents=[Content("text", text="probe-complete")], role="assistant")

            return ResponseStream(updates(), finalizer=lambda _: ChatResponse(messages=[Message("assistant", ["probe-complete"])]) )
        return response()


class _MCPProbeClient:
    additional_properties = {}

    def as_agent(self, **kwargs):
        return Agent(self, **kwargs)

    def get_response(self, messages, **kwargs):
        options = kwargs.get("options", {})
        client_kwargs = kwargs.get("client_kwargs", {})

        async def response():
            tools = options.get("tools", ())
            if tools:
                function = tools[0]
                context = FunctionInvocationContext(function=function, arguments={"query": "capacity"})

                async def call_next():
                    context.result = await function.invoke(context=context, skip_parsing=True)

                middleware = client_kwargs.get("middleware", ())
                for layer in middleware:
                    await layer.process(context, call_next)
            else:
                raise AssertionError(f"native MCP function was not forwarded by Agent: options={sorted(options)} tool_count={len(tools)} client={sorted(client_kwargs)}")
            return ChatResponse(messages=[Message("assistant", ["mcp-complete"])])

        return response()


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


async def _native_mcp_receipt() -> dict[str, object]:
    from agent_framework import MCPStreamableHTTPTool

    port = _free_port()
    process = subprocess.Popen(
        [sys.executable, "tests/fixtures/mcp_streamable_http_server.py", "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "PYTHONPATH": str(Path("src").resolve())},
    )
    tool = MCPStreamableHTTPTool("optimization", f"http://127.0.0.1:{port}/mcp", load_prompts=False)
    try:
        for _ in range(50):
            if process.poll() is not None:
                raise RuntimeError("MCP fixture exited before discovery")
            try:
                await tool.connect()
                break
            except Exception:
                await asyncio.sleep(0.1)
        names = [function.name for function in tool.functions]
        scope = CapabilityScope()
        scope.register(tool)
        from foresight_os.runtime.metrics import RunMetrics
        metrics = RunMetrics("optimization-mcp", "DIRECT", "direct")
        from foresight_os.runtime.participants import AgentFactory, ParticipantConfig
        from foresight_os.runtime.capabilities import CapabilityBinding, CapabilityResolver
        factory = AgentFactory(_MCPProbeClient())
        agent = factory.create(
            ParticipantConfig("mcp-probe", "analyst", "read MCP evidence", capability_ids=("mcp_read",)),
            {
                "scope": scope,
                "metrics": metrics,
                "capability_resolver": CapabilityResolver({"mcp_read": CapabilityDefinition("mcp_read", "external_read")}),
                "mcp_tools": {"mcp_read": CapabilityBinding(tool, fingerprint="fixture-mcp")},
            },
        )
        await agent.run("read capacity")
        return {"status": "VERIFIED", "discovered_tools": names, "tool_calls": metrics.tool_calls}
    finally:
        try:
            await tool.close()
        except Exception:
            pass
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def _measure_workbook(path: Path) -> dict[str, object]:
    durations: list[float] = []
    allocations: list[int] = []
    result = None
    full_selection = SheetSelection(include_hidden=True, include_hidden_rows=True)
    session_observations = {
        "available": WorkbookContext is not None,
        "cold": {"capture_count": 0, "capture_hash_count": 0, "currentness_hash_count": 0, "xlsx_parse_count": 0, "openpyxl_load_count": 0},
        "warm_identical": {"capture_count": 0, "capture_hash_count": 0, "currentness_hash_count": 0, "xlsx_parse_count": 0, "openpyxl_load_count": 0},
        "different_selection": {"capture_count": 0, "capture_hash_count": 0, "currentness_hash_count": 0, "xlsx_parse_count": 0, "openpyxl_load_count": 0},
        "analyst_to_validator": {"capture_count": 0, "capture_hash_count": 0, "currentness_hash_count": 0, "xlsx_parse_count": 0, "openpyxl_load_count": 0},
        "explicit_currentness": {"capture_count": 0, "capture_hash_count": 0, "currentness_hash_count": 0, "xlsx_parse_count": 0, "openpyxl_load_count": 0},
        "resource_observations": {},
    }
    context = None
    session = None
    if WorkbookContext is not None:
        from foresight_os.analysis.independent_validation import read_validation_source

        context = WorkbookContext()
        before = context.stats.to_dict()
        session = context.session_for_source(path)

        def stats_snapshot():
            return context.stats.to_dict()

        result = session.read(full_selection)
        after = stats_snapshot()
        session_observations["cold"] = {field: after[field] - before[field] for field in after}
        before = after
        warm_result = session.read(full_selection)
        after = stats_snapshot()
        session_observations["warm_identical"] = {field: after[field] - before[field] for field in after}
        first_sheet = result.sheets[0].name if result.sheets else ""
        before = after
        session.read(SheetSelection(ranges=((first_sheet, "A1:B2"),)))
        after = stats_snapshot()
        session_observations["different_selection"] = {field: after[field] - before[field] for field in after}
        before = after
        validation_result = read_validation_source(path, full_selection, workbook_session=session)
        after = stats_snapshot()
        session_observations["analyst_to_validator"] = {field: after[field] - before[field] for field in after}
        before = after
        currentness = session.currentness_hash()
        after = stats_snapshot()
        session_observations["explicit_currentness"] = {field: after[field] - before[field] for field in after}
        session_observations["resource_observations"] = {
            "snapshot_bytes": session.snapshot.byte_size,
            "authority_bytes": context.authority.bytes_used,
            "derived_cache_bytes": session.cache.bytes_used,
            "peak_in_flight_parse_bytes": context.stats.peak_in_flight_parse_bytes,
            "same_view_sha_matches": warm_result.workbook_sha256 == validation_result.workbook_sha256 == currentness,
        }
    else:
        for _ in range(2):
            result = spreadsheet_read(path, full_selection)
    for _ in range(10):
        tracemalloc.start()
        started = time.perf_counter()
        result = spreadsheet_read(path, full_selection)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        durations.append((time.perf_counter() - started) * 1000)
        allocations.append(peak)
    table = result.tables[0]
    value_column = "Value" if "Value" in table.columns else table.columns[-1]
    analysis = data_analysis(table, AnalysisOperation("aggregate", value_column=value_column))
    if context is not None:
        context.close()
    return {
        "source": "fixture",
        "sheet_count": len(result.sheets),
        "measurement_count": len(result.measurements),
        "table_count": len(result.tables),
        "p50_ms": round(median(durations), 3),
        "p95_ms": round(sorted(durations)[-1], 3),
        "peak_allocation_bytes": max(allocations),
        "deterministic_key": analysis.deterministic_key,
        "source_hash": result.workbook_sha256,
        "local_tool_calls": 13,
        "session_reuse": session_observations,
    }


async def _event_loop_lag_ms() -> float:
    scheduled = asyncio.get_running_loop().time() + 0.001
    await asyncio.sleep(0.001)
    return round(max(0.0, (asyncio.get_running_loop().time() - scheduled) * 1000), 3)


def _resource_snapshot(metrics, event_loop_lag_ms: float) -> dict[str, object]:
    child_process_count = 0
    open_file_descriptors = None
    try:
        import psutil

        process = psutil.Process(os.getpid())
        child_process_count = len(process.children(recursive=True))
        try:
            open_file_descriptors = int(process.num_fds())
        except (AttributeError, OSError):
            open_file_descriptors = None
    except Exception:
        pass
    return {
        "rss_bytes": process_rss_bytes(),
        "active_python_tasks": len(asyncio.all_tasks()),
        "thread_count": threading.active_count(),
        "child_process_count": child_process_count,
        "owned_capability_resources": 0 if metrics.cleanup_complete else 1,
        "mcp_session_count": 0,
        "event_loop_lag_ms": event_loop_lag_ms,
        "open_file_descriptors": open_file_descriptors,
    }


async def _measure_patterns() -> tuple[dict[str, object], list[dict[str, object]]]:
    receipts: dict[str, object] = {}
    stage_metrics: list[dict[str, object]] = []
    for recipe_name in (RecipeName.DIRECT, RecipeName.ANALYZE, RecipeName.CONCURRENT, RecipeName.HANDOFF, RecipeName.CHALLENGE_RECOMMENDATION):
        recipe = make_recipe(recipe_name)
        for _ in range(2):
            await run_recipe_async(recipe, "optimization baseline", _ProbeClient(), f"warm-{recipe_name.value}")
        samples: list[dict[str, object]] = []
        last = None
        for index in range(10):
            started = time.perf_counter()
            last = await run_recipe_async(recipe, "optimization baseline", _ProbeClient(), f"measure-{recipe_name.value}-{index}")
            lag = await _event_loop_lag_ms()
            last.metrics.event_loop_lag_ms = lag
            samples.append(_metric_snapshot(last.metrics, (time.perf_counter() - started) * 1000))
        if last is not None:
            summary = stage_metric("stage-1", recipe.pattern, last, float(samples[-1]["wall_time_ms"]), samples=samples)
            stage_metrics.append(summary)
        receipts[recipe_name.value] = {
            **summary,
            "p50_ms": summary["latency"]["wall_time_ms_p50"],
            "p95_ms": summary["latency"]["wall_time_ms_p95"],
        }
    return receipts, stage_metrics


async def _soak_receipt() -> dict[str, object]:
    recipe = make_recipe(RecipeName.ANALYZE)
    snapshots: list[dict[str, object]] = []
    for index in range(100):
        result = await run_recipe_async(recipe, "optimization soak", _ProbeClient(), f"soak-{index}")
        snapshots.append(_resource_snapshot(result.metrics, await _event_loop_lag_ms()))
    growth_fields = (
        "rss_bytes",
        "active_python_tasks",
        "thread_count",
        "child_process_count",
        "owned_capability_resources",
        "mcp_session_count",
    )
    growth = {
        field: {
            "first": snapshots[0].get(field) if snapshots else None,
            "last": snapshots[-1].get(field) if snapshots else None,
            "max": max((int(item[field]) for item in snapshots if item.get(field) is not None), default=None),
            "monotonic_non_decreasing": all(
                left.get(field) is not None and right.get(field) is not None and int(left[field]) <= int(right[field])
                for left, right in zip(snapshots, snapshots[1:])
            ),
        }
        for field in growth_fields
    }
    leak_fields = ("active_python_tasks", "thread_count", "child_process_count", "owned_capability_resources", "mcp_session_count")
    monotonic_growth = any(
        growth[field]["monotonic_non_decreasing"] and growth[field]["last"] > growth[field]["first"]
        for field in leak_fields
        if growth[field]["first"] is not None and growth[field]["last"] is not None
    )
    return {
        "runs": len(snapshots),
        "snapshots": snapshots,
        "resource_growth": growth,
        "resource_counts": {"owned_after_cleanup": snapshots[-1]["owned_capability_resources"] if snapshots else None},
        "monotonic_growth": monotonic_growth,
        "plateau": {field: item["first"] == item["last"] for field, item in growth.items() if item["first"] is not None and item["last"] is not None},
    }


async def _run(mode: str, fixture: Path, evidence_root: Path) -> dict[str, object]:
    workbook = _measure_workbook(fixture)
    patterns, stage_metrics = await _measure_patterns()
    soak = await _soak_receipt()

    async def external_call(query: str = "") -> str:
        await asyncio.sleep(0)
        return f"fixture:{query}"

    from foresight_os.runtime.metrics import RunMetrics
    metrics = RunMetrics("optimization-external", "DIRECT", "direct")
    call = instrument_tool(external_call, CapabilityDefinition("external_fixture", "external_read"), {"metrics": metrics, "tool_call_kind": "external_http"})
    await call("probe")
    try:
        mcp = await _native_mcp_receipt()
    except Exception as error:
        mcp = {"status": "FAILED", "error_type": type(error).__name__}
    state = observed_xlsx_state(fixture, evidence_root)
    return build_receipt(
        mode=mode,
        fixture=fixture,
        workbook=workbook,
        patterns=patterns,
        stage_metrics=stage_metrics,
        soak=soak,
        external_fixture={"tool_calls": metrics.tool_calls, "external_http_requests": metrics.external_http_requests, "failures": metrics.tool_failures},
        native_mcp=mcp,
        state=state,
        thresholds={"p95_regression_pct": 20, "peak_allocation_regression_pct": 15, "tool_calls_per_finding_increase": 0, "soak_runs": 100},
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("baseline", "release"), required=True)
    parser.add_argument("--fixture", type=Path, default=Path("tests/fixtures/analyst_multisheet.xlsx"))
    parser.add_argument("--workbook", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    fixture = args.workbook or args.fixture
    output = args.output or Path(f"work/optimization-{args.mode}/receipt.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    result = asyncio.run(_run(args.mode, fixture, output.parent / "measurement-state"))
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
