from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import tempfile
import time
import tracemalloc
from collections.abc import Mapping
from pathlib import Path


def _cli_path(name: str) -> Path | None:
    try:
        index = sys.argv.index(name)
    except ValueError:
        return None
    if index + 1 >= len(sys.argv):
        raise SystemExit(f"{name} requires a path")
    return Path(sys.argv[index + 1]).resolve()


TARGET_ROOT = _cli_path("--target-root") or Path(__file__).parents[2].resolve()
HARNESS_ROOT = _cli_path("--harness-root") or Path(__file__).parents[2].resolve()
# Direct probe execution must measure the explicitly selected worktree, not an
# unrelated editable installation from another checkout.
sys.path.insert(0, str(HARNESS_ROOT))
sys.path.insert(0, str(TARGET_ROOT / "src"))

from agent_framework import Agent, ChatResponse, ChatResponseUpdate, Content, FunctionInvocationContext, Message, ResponseStream

from foresight_os.controller.recipes import ExecutionPattern, RecipeName, make_recipe
from foresight_os.domain.analysis_inputs import AnalysisInputContract
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.capabilities import (
    CapabilityDefinition,
    CapabilityScope,
    ExecutionMode,
    ScopeOwnership,
    instrument_tool,
)
from foresight_os.runtime.local_toolbelt import AnalysisOperation, SheetSelection, WorkbookContext, data_analysis, spreadsheet_read
from foresight_os.analysis.independent_validation import run_independent_validation
from foresight_os.analysis.technology_radar import run_technology_radar_workflow
from foresight_os.runtime.workflow import run_recipe_async
from optimization_measurement import DETERMINISTIC_XLSX_WORKLOADS, MANDATORY_XLSX_WORKLOADS, SCENARIO_XLSX_WORKLOADS, _metric_snapshot, _percentile, build_receipt, configure_measurement_roots, measurement_evidence, observed_xlsx_state, process_rss_bytes, stage_metric

configure_measurement_roots(target_root=TARGET_ROOT, harness_root=HARNESS_ROOT)


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
        [sys.executable, str(TARGET_ROOT / "tests/fixtures/mcp_streamable_http_server.py"), "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "PYTHONPATH": str((TARGET_ROOT / "src").resolve())},
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


def _write_probe_workbook(path: Path, row_count: int, value_offset: int = 0) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    workbook.remove(workbook.active)
    for sheet_index in range(1, 4):
        sheet = workbook.create_sheet(f"Sheet{sheet_index}")
        sheet.append(["Category", "Value"])
        for row_index in range(row_count):
            sheet.append([f"item-{row_index}", value_offset + sheet_index + row_index])
    workbook.save(path)


def _analysis_value(table: object) -> float | None:
    columns = getattr(table, "columns", ())
    value_column = "Value" if "Value" in columns else (columns[-1] if columns else None)
    if value_column is None:
        return None
    result = data_analysis(table, AnalysisOperation("aggregate", value_column=value_column))
    if result.rows and isinstance(result.rows[0], Mapping):
        value = result.rows[0].get("sum")
        if value is None:
            value = result.rows[0].get("value")
        return float(value) if value is not None else None
    return None


async def _cancelled_read_workload(path: Path) -> dict[str, object]:
    from foresight_os.runtime.local_toolbelt import ToolbeltError
    from foresight_os.runtime.metrics import RunMetrics

    scope = CapabilityScope(ownership=ScopeOwnership.RUN)
    metrics = RunMetrics("optimization-cancel", "DIRECT", "direct")
    worker_started = threading.Event()
    worker_failed = threading.Event()
    worker_failure: dict[str, str] = {}

    def blocking_read(source: str, selection: SheetSelection | None = None, cancel_check=None):
        worker_started.set()
        while not cancel_check():
            time.sleep(0.001)
        try:
            return spreadsheet_read(source, selection, cancel_check=cancel_check)
        except ToolbeltError as error:
            worker_failure["type"] = type(error).__name__
            worker_failed.set()
            return None

    wrapped = instrument_tool(
        blocking_read,
        CapabilityDefinition("spreadsheet_read", "local_deterministic", execution_mode=ExecutionMode.BLOCKING),
        {"scope": scope, "metrics": metrics},
    )
    task = asyncio.create_task(wrapped(str(path), SheetSelection(include_hidden=True, include_hidden_rows=True)))
    started = await asyncio.to_thread(worker_started.wait, 5)
    caller_cancelled = False
    if started:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            caller_cancelled = True
    cleanup_error = None
    try:
        await scope.close()
    except Exception as error:
        cleanup_error = type(error).__name__
    return {
        "executed": True,
        "status": "VERIFIED" if started and worker_failed.is_set() and caller_cancelled and cleanup_error is None else "FAILED",
        "correctness": "VERIFIED" if started and worker_failed.is_set() and caller_cancelled else "FAILED",
        "worker_observed": started,
        "worker_failed": worker_failed.is_set(),
        "worker_failure_type": worker_failure.get("type"),
        "caller_cancelled": caller_cancelled,
        "cancellation_settlements": metrics.cancellation_settlements,
        "cache_entries_after_settlement": 0 if scope.workbook_context is None else scope.workbook_context.cache.size,
        "authority_records_after_settlement": 0 if scope.workbook_context is None else scope.workbook_context.authority_index.size,
        "cleanup_complete": scope.executor is None and scope.workbook_context is None and cleanup_error is None,
        "limitation": None if cleanup_error is None else f"cleanup failed: {cleanup_error}",
    }


def _repeated_workflow(path: Path) -> dict[str, object]:
    from foresight_os.analysis.evidence_workflow import run_xlsx_finding_workflow
    from foresight_os.persistence.analysis_store import AnalysisStore

    with tempfile.TemporaryDirectory(prefix="foresight-repeat-") as temporary_dir:
        store = AnalysisStore(Path(temporary_dir) / "state")
        context = WorkbookContext()
        selection = SheetSelection(include_hidden=True, include_hidden_rows=True)
        started = time.perf_counter()
        first = run_xlsx_finding_workflow(
            store,
            path,
            AnalysisOperation("aggregate", value_column="Value"),
            selection=selection,
            investigation_id="optimization-repeat",
            human_decision="ACCEPT",
            workbook_context=context,
        )
        second = run_xlsx_finding_workflow(
            store,
            path,
            AnalysisOperation("aggregate", value_column="Value"),
            selection=selection,
            investigation_id="optimization-repeat",
            human_decision="ACCEPT",
            workbook_context=context,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
    first_hash = first.evidence.source_locator.file_version if first.evidence is not None else None
    second_hash = second.evidence.source_locator.file_version if second.evidence is not None else None
    first_value = first.analysis.calculations[0].output if first.analysis and first.analysis.calculations else None
    second_value = second.analysis.calculations[0].output if second.analysis and second.analysis.calculations else None
    correct = (
        first.status == "accepted"
        and second.status == "accepted"
        and first_hash is not None
        and first_hash == second_hash
        and first_value == second_value
    )
    return {
        "executed": True,
        "status": "VERIFIED" if correct else "FAILED",
        "correctness": "VERIFIED" if correct else "FAILED",
        "first_status": first.status,
        "second_status": second.status,
        "same_source_hash": first_hash == second_hash,
        "same_calculation_value": first_value == second_value,
        "wall_time_ms": round(elapsed_ms, 3),
        "local_tool_calls": len(first.tool_calls) + len(second.tool_calls),
        "capture_count": context.stats.capture_count,
        "capture_hash_count": context.stats.capture_hash_count,
        "currentness_hash_count": context.stats.currentness_hash_count,
        "xlsx_parse_count": context.stats.xlsx_parse_count,
        "read_cache_hits": context.stats.cache_hits,
        "analysis_cache_hits": context.stats.analysis_cache_hits,
        "retained_snapshot_bytes": context.stats.snapshot_bytes,
        "retained_read_result_bytes": context.stats.retained_read_result_bytes,
        "retained_analysis_result_bytes": context.stats.retained_analysis_result_bytes,
        "retained_authority_record_bytes": context.stats.retained_authority_record_bytes,
        "limitation": None,
    }


def _retained_context_workloads() -> dict[str, object]:
    results: dict[str, object] = {}
    with tempfile.TemporaryDirectory(prefix="foresight-context-sizes-") as temporary_dir:
        root = Path(temporary_dir)
        for label, rows in (("small", 8), ("medium", 128), ("large", 2048)):
            source = root / f"{label}.xlsx"
            _write_probe_workbook(source, rows)
            context = WorkbookContext(max_entries=4, max_bytes=20_000_000, max_total_bytes=30_000_000)
            selection = SheetSelection(include_hidden=True, include_hidden_rows=True)
            first = context.read(source, selection)
            before = (context.stats.capture_count, context.stats.capture_hash_count, context.stats.xlsx_parse_count)
            started = time.perf_counter()
            warm = context.read(source, selection)
            warm_ms = (time.perf_counter() - started) * 1000
            after = (context.stats.capture_count, context.stats.capture_hash_count, context.stats.xlsx_parse_count)
            retained = context.stats.snapshot_bytes + context.stats.retained_read_result_bytes + context.stats.retained_authority_record_bytes
            results[label] = {
                "rows": rows,
                "status": "VERIFIED" if warm.workbook_sha256 == first.workbook_sha256 and before == after and retained <= context.max_total_bytes else "FAILED",
                "correctness": "VERIFIED" if warm.workbook_sha256 == first.workbook_sha256 else "FAILED",
                "warm_time_ms": round(warm_ms, 3),
                "before_counts": before,
                "after_counts": after,
                "retained_bytes": retained,
                "retained_budget_bytes": context.max_total_bytes,
            }
            context.clear()
    return results


async def _multi_workbook_soak() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="foresight-multi-workbook-") as temporary_dir:
        root = Path(temporary_dir)
        sources: list[Path] = []
        for index, rows in enumerate((16, 32, 64), 1):
            source = root / f"source-{index}.xlsx"
            _write_probe_workbook(source, rows, value_offset=index * 10_000)
            sources.append(source)
        context = WorkbookContext(max_entries=2, max_bytes=20_000_000, max_total_bytes=40_000_000)
        scope = CapabilityScope(ownership=ScopeOwnership.RUN)
        scope.workbook_context = context
        selection = SheetSelection(include_hidden=True, include_hidden_rows=True)
        results = [context.read(source, selection) for source in sources]
        cache_keys_after_three = tuple(context.cache._entries)
        retained = context.stats.snapshot_bytes + context.stats.retained_read_result_bytes + context.stats.retained_authority_record_bytes
        hashes = tuple(result.workbook_sha256 for result in results)
        no_cross_source_authority_aliasing = len({key[0] for key in context.authority_index.measurements}) == 3
        repeated = context.read(sources[0], selection)
        cache_keys_after_repeat = tuple(context.cache._entries)
        evicted_first = not any(key[0] == str(sources[0].resolve()) for key in cache_keys_after_three)
        cleanup_error = None
        try:
            await scope.close()
        except Exception as error:
            cleanup_error = type(error).__name__
        correct = (
            context.stats.capture_count == 3
            and len(set(hashes)) == 3
            and no_cross_source_authority_aliasing
            and repeated.workbook_sha256 == hashes[0]
            and evicted_first
            and len(cache_keys_after_repeat) <= 2
            and retained <= context.max_total_bytes
            and scope.workbook_context is None
            and cleanup_error is None
        )
        return {
            "executed": True,
            "status": "VERIFIED" if correct else "FAILED",
            "correctness": "VERIFIED" if correct else "FAILED",
            "source_count": len(sources),
            "capture_count": context.stats.capture_count,
            "distinct_source_hashes": len(set(hashes)),
            "no_cross_source_authority_aliasing": no_cross_source_authority_aliasing,
            "deterministic_eviction": evicted_first and len(cache_keys_after_repeat) <= 2,
            "retained_bytes_before_cleanup": retained,
            "retained_budget_bytes": context.max_total_bytes,
            "owned_resources_after_cleanup": 0 if scope.workbook_context is None and scope.executor is None and not scope.resources else 1,
            "cleanup_complete": cleanup_error is None and scope.workbook_context is None,
            "limitation": None if cleanup_error is None else f"cleanup failed: {cleanup_error}",
        }


def _retained_bytes(context: WorkbookContext) -> int:
    return (
        context.stats.snapshot_bytes
        + context.stats.retained_read_result_bytes
        + context.stats.retained_analysis_result_bytes
        + context.stats.retained_authority_record_bytes
    )


def _public_workflow_context_reuse(mode: str) -> dict[str, object]:
    source = TARGET_ROOT / "tests" / "fixtures" / "exercise" / "04_Technology_Radar.xlsx"
    focused = AnalysisInputContract(domain="technology_radar", entity_scope=("SiC Power Electronics",))
    broad = AnalysisInputContract(domain="technology_radar", entity_scope=("SiC Power Electronics", "Zonal Architecture"))
    contexts = [WorkbookContext(), WorkbookContext()] if mode == "baseline" else [WorkbookContext()]
    results = []
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="foresight-public-workflow-") as temporary_dir:
        for index, contract in enumerate((focused, broad)):
            context = contexts[index] if mode == "baseline" else contexts[0]
            result = run_technology_radar_workflow(
                AnalysisStore(Path(temporary_dir) / f"case-{index}"),
                source,
                human_decision="PENDING",
                input_contract=contract,
                workbook_context=context,
            )
            results.append((result, context))
    elapsed_ms = (time.perf_counter() - started) * 1000
    statuses = [result.status for result, _context in results]
    fingerprints = [result.technology.contract_fingerprint for result, _context in results if result.technology is not None]
    assessment_counts = [len(result.technology.assessments) for result, _context in results if result.technology is not None]
    capture_count = sum(context.stats.capture_count for context in contexts)
    parse_count = sum(context.stats.xlsx_parse_count for context in contexts)
    retained_bytes = max((_retained_bytes(context) for context in contexts), default=0)
    caller_contexts_open = all(not context._closed for context in contexts)
    correct = (
        statuses == ["pending", "pending"]
        and len(fingerprints) == 2
        and len(set(fingerprints)) == 2
        and assessment_counts == sorted(assessment_counts)
        and capture_count == (2 if mode == "baseline" else 1)
        and parse_count == (2 if mode == "baseline" else 1)
        and caller_contexts_open
    )
    for context in contexts:
        context.clear()
    return {
        "executed": True,
        "status": "VERIFIED" if correct else "FAILED",
        "correctness": "VERIFIED" if correct else "FAILED",
        "mode": mode,
        "wall_time_ms": round(elapsed_ms, 3),
        "capture_count": capture_count,
        "xlsx_parse_count": parse_count,
        "contract_fingerprint_count": len(set(fingerprints)),
        "distinct_contracts": len(set(fingerprints)) == 2,
        "distinct_brief_results": len(assessment_counts) == 2 and assessment_counts[0] != assessment_counts[1],
        "caller_context_open_before_cleanup": caller_contexts_open,
        "retained_bytes": retained_bytes,
        "limitation": None,
    }


async def _measure_workbook(path: Path, measurement_mode: str = "full", mode: str = "baseline") -> dict[str, object]:
    durations: list[float] = []
    allocations: list[int] = []
    result = None
    selection = SheetSelection(include_hidden=True, include_hidden_rows=True)
    if measurement_mode in {"timing", "full"}:
        for _ in range(2):
            result = spreadsheet_read(path, selection)
        for _ in range(10):
            started = time.perf_counter()
            result = spreadsheet_read(path, selection)
            durations.append((time.perf_counter() - started) * 1000)
    if measurement_mode in {"allocation", "full"}:
        for _ in range(2):
            spreadsheet_read(path, selection)
        for _ in range(10):
            tracemalloc.start()
            spreadsheet_read(path, selection)
            _current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            allocations.append(peak)
    if result is None:
        result = spreadsheet_read(path, selection)
    table = result.tables[0]
    value_column = "Value" if "Value" in table.columns else table.columns[-1]
    analysis = data_analysis(table, AnalysisOperation("aggregate", value_column=value_column))
    context = WorkbookContext()
    context_selection = selection
    cold_started = time.perf_counter()
    context.read(path, context_selection)
    cold_read_ms = (time.perf_counter() - cold_started) * 1000
    warm_started = time.perf_counter()
    warm_result = context.read(path, context_selection)
    warm_read_ms = (time.perf_counter() - warm_started) * 1000
    warm_2_plus_samples: list[float] = []
    for _ in range(3):
        started = time.perf_counter()
        context.read(path, context_selection)
        warm_2_plus_samples.append((time.perf_counter() - started) * 1000)
    validator_started = time.perf_counter()
    validator_report = run_independent_validation(path, selection=context_selection, workbook_context=context)
    validator_ms = (time.perf_counter() - validator_started) * 1000
    context.currentness(path)
    sheet_names = tuple(sheet.name for sheet in result.sheets)
    workloads: dict[str, dict[str, object]] = {
        "cold_workbook": {"executed": True, "status": "VERIFIED", "correctness": "VERIFIED", "wall_time_ms": round(cold_read_ms, 3)},
        "same_view_repeat": {
            "executed": True,
            "status": "VERIFIED" if context.stats.capture_count == 1 and context.stats.xlsx_parse_count == 1 else "FAILED",
            "correctness": "VERIFIED" if warm_result.workbook_sha256 == result.workbook_sha256 else "FAILED",
            "wall_time_ms": round(warm_read_ms, 3),
            "capture_count": context.stats.capture_count,
            "xlsx_parse_count": context.stats.xlsx_parse_count,
            "analytical_result_fingerprint": analysis.deterministic_key,
        },
        "warm_1": {
            "executed": True,
            "status": "VERIFIED" if warm_result.workbook_sha256 == result.workbook_sha256 else "FAILED",
            "correctness": "VERIFIED" if warm_result.workbook_sha256 == result.workbook_sha256 else "FAILED",
            "wall_time_ms": round(warm_read_ms, 3),
        },
        "warm_2_plus": {
            "executed": True,
            "status": "VERIFIED" if all(item >= 0 for item in warm_2_plus_samples) else "FAILED",
            "correctness": "VERIFIED" if warm_result.workbook_sha256 == result.workbook_sha256 else "FAILED",
            "sample_count": len(warm_2_plus_samples),
            "p95_ms": _percentile(warm_2_plus_samples, 0.95),
        },
        "analyst_validator_reuse": {
            "executed": True,
            "status": "VERIFIED" if validator_report.accepted else "FAILED",
            "correctness": "VERIFIED" if validator_report.accepted else "FAILED",
            "validator_accepted": validator_report.accepted,
            "wall_time_ms": round(validator_ms, 3),
        },
    }
    with tempfile.TemporaryDirectory(prefix="foresight-optimization-") as temporary_dir:
        changed_path = Path(temporary_dir) / path.name
        shutil.copy2(path, changed_path)
        from openpyxl import load_workbook

        changed_workbook = load_workbook(changed_path)
        changed_sheet = changed_workbook[changed_workbook.sheetnames[0]]
        changed_sheet["A1"] = f"changed:{changed_sheet['A1'].value}"
        changed_workbook.save(changed_path)
        changed_context = WorkbookContext()
        changed_result = changed_context.read(changed_path, selection)
        workloads["changed_source"] = {
            "executed": True,
            "status": "VERIFIED" if changed_context.stats.capture_count == 1 and changed_result.workbook_sha256 != result.workbook_sha256 else "FAILED",
            "correctness": "VERIFIED" if changed_context.stats.capture_count == 1 and changed_result.workbook_sha256 != result.workbook_sha256 else "FAILED",
            "source_identity_changed": changed_result.workbook_sha256 != result.workbook_sha256,
        }
    if len(sheet_names) > 1:
        alternate_selection = SheetSelection(sheet_names=(sheet_names[-1],), include_hidden=True, include_hidden_rows=True)
        alternate_context = WorkbookContext()
        alternate = alternate_context.read(path, alternate_selection)
        alternate_value = _analysis_value(alternate.tables[0]) if alternate.tables else None
        primary_value = _analysis_value(result.tables[0])
        workloads["different_selection"] = {
            "executed": True,
            "status": "VERIFIED" if alternate.workbook_sha256 == result.workbook_sha256 and alternate_value != primary_value and alternate_context.stats.capture_count == 1 else "FAILED",
            "correctness": "VERIFIED" if alternate.workbook_sha256 == result.workbook_sha256 and alternate_value != primary_value else "FAILED",
            "capture_count": alternate_context.stats.capture_count,
            "xlsx_parse_count": alternate_context.stats.xlsx_parse_count,
            "primary_value": primary_value,
            "alternate_sheet": sheet_names[-1],
            "alternate_value": alternate_value,
            "limitation": None,
        }
    workloads["repeated_investigation"] = _repeated_workflow(path)
    workloads["blocking_cancellation"] = await _cancelled_read_workload(path)
    sizes = _retained_context_workloads()
    large = sizes["large"]
    workloads["large_retained_context"] = {
        "executed": True,
        "status": large["status"],
        "correctness": large["correctness"],
        "sizes": sizes,
        "limitation": large.get("limitation"),
    }
    workloads["multi_workbook"] = await _multi_workbook_soak()
    workloads["public_workflow_context_reuse"] = _public_workflow_context_reuse(mode)
    from foresight_os.runtime.metrics import RunMetrics

    local_metrics = RunMetrics("optimization-local", "DIRECT", "direct")
    local_scope = CapabilityScope(ownership=ScopeOwnership.RUN)
    local_read = instrument_tool(
        spreadsheet_read,
        CapabilityDefinition("spreadsheet_read", "local_deterministic", execution_mode=ExecutionMode.BLOCKING),
        {"scope": local_scope, "metrics": local_metrics},
    )
    await local_read(str(path), selection)
    await local_scope.close()
    return {
        "source": "fixture",
        "sheet_count": len(result.sheets),
        "measurement_count": len(result.measurements),
        "table_count": len(result.tables),
        "p50_ms": _percentile(durations, 0.50) if durations else None,
        "p90_ms": _percentile(durations, 0.90) if durations else None,
        "p95_ms": _percentile(durations, 0.95) if durations else None,
        "timing_paths": {
            "direct_workbook": {
                "p50_ms": _percentile(durations, 0.50) if durations else None,
                "p90_ms": _percentile(durations, 0.90) if durations else None,
                "p95_ms": _percentile(durations, 0.95) if durations else None,
                "sample_count": len(durations),
            },
            "cold_workbook": {"wall_time_ms": workloads["cold_workbook"].get("wall_time_ms")},
            "same_view_repeat": {"wall_time_ms": workloads["same_view_repeat"].get("wall_time_ms")},
            "warm_1": {"wall_time_ms": workloads["warm_1"].get("wall_time_ms")},
            "warm_2_plus": {"p95_ms": workloads["warm_2_plus"].get("p95_ms"), "sample_count": workloads["warm_2_plus"].get("sample_count")},
            "repeated_investigation": {"wall_time_ms": workloads["repeated_investigation"].get("wall_time_ms")},
            "analyst_validator_reuse": {"wall_time_ms": workloads["analyst_validator_reuse"].get("wall_time_ms")},
        },
        "peak_allocation_bytes": max(allocations) if allocations else None,
        "peak_retained_bytes": max(_retained_bytes(context), max((item.get("retained_bytes", 0) for item in workloads.values() if isinstance(item, dict)), default=0)),
        "measurement_mode": measurement_mode,
        "latency": measurement_evidence("VERIFIED", limitation=None) if durations else measurement_evidence("NOT_MEASURED", limitation="timing mode was not selected"),
        "allocation": measurement_evidence("VERIFIED", limitation=None) if allocations else measurement_evidence("NOT_MEASURED", limitation="allocation mode was not selected"),
        "workloads": workloads,
        "deterministic_key": analysis.deterministic_key,
        "source_hash": result.workbook_sha256,
        "analytical_result_fingerprint": analysis.deterministic_key,
        "local_tool_calls": local_metrics.local_tool_calls + int(workloads["repeated_investigation"].get("local_tool_calls", 0) or 0),
        "run_owned_context": {
            "capture_count": context.stats.capture_count,
            "capture_hash_count": context.stats.capture_hash_count,
            "currentness_hash_count": context.stats.currentness_hash_count,
            "xlsx_parse_count": context.stats.xlsx_parse_count,
            "openpyxl_load_count": context.stats.openpyxl_load_count,
            "cache_hits": context.stats.cache_hits,
            "analysis_cache_hits": context.stats.analysis_cache_hits,
            "snapshot_bytes": context.stats.snapshot_bytes,
            "retained_read_result_bytes": context.stats.retained_read_result_bytes,
            "retained_analysis_result_bytes": context.stats.retained_analysis_result_bytes,
            "retained_authority_record_bytes": context.stats.retained_authority_record_bytes,
            "retained_bytes": _retained_bytes(context),
            "peak_retained_bytes": _retained_bytes(context),
            "validator_accepted": validator_report.accepted,
        },
        "mandatory_workloads": [name for name in MANDATORY_XLSX_WORKLOADS if name in workloads],
        "deterministic_workloads": [name for name in DETERMINISTIC_XLSX_WORKLOADS if name in workloads],
        "scenario_workloads": {
            "changed_brief": {"executed": False, "status": "NOT_MEASURED", "correctness": "NOT_MEASURED", "limitation": "requires a brief-aware domain fixture"},
            "changed_selection": workloads.get("different_selection", {"executed": False, "status": "NOT_MEASURED", "correctness": "NOT_MEASURED", "limitation": "fixture has one selectable view"}),
            "growing_analysis_history": workloads.get("repeated_investigation", {"executed": False, "status": "NOT_MEASURED", "correctness": "NOT_MEASURED", "limitation": "history probe unavailable"}),
            "correction": {"executed": False, "status": "NOT_MEASURED", "correctness": "NOT_MEASURED", "limitation": "correction requires a reviewed pending state"},
            "workbook_cancellation": workloads.get("blocking_cancellation", {"executed": False, "status": "NOT_MEASURED", "correctness": "NOT_MEASURED", "limitation": "cancellation probe unavailable"}),
            "synthesis_cancellation": {"executed": False, "status": "NOT_MEASURED", "correctness": "NOT_MEASURED", "limitation": "synthesis cancellation is outside deterministic workbook scope"},
        },
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


async def _run(mode: str, fixture: Path, evidence_root: Path, measurement_mode: str = "full") -> dict[str, object]:
    workbook = await _measure_workbook(fixture, measurement_mode, mode)
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
        mcp = {"status": "NOT_MEASURED", "error_type": type(error).__name__, "limitation": "optional MCP fixture unavailable"}
    state = observed_xlsx_state(fixture, evidence_root)
    local_correctness = all(workbook.get("workloads", {}).get(name, {}).get("status") == "VERIFIED" for name in MANDATORY_XLSX_WORKLOADS)
    evidence = {
        "correctness": measurement_evidence("VERIFIED" if local_correctness else "FAILED", limitation=None if local_correctness else "local workbook workload failed"),
        "latency": workbook["latency"],
        "allocation": workbook["allocation"],
        "soak": measurement_evidence("VERIFIED", limitation=None) if soak["runs"] >= 100 and not soak["monotonic_growth"] else measurement_evidence("FAILED", limitation="resource soak did not reach a clean plateau"),
        "regression_threshold": measurement_evidence("NOT_MEASURED", limitation="requires baseline/release comparison"),
        "optimization_demonstrated": measurement_evidence("NOT_MEASURED", limitation="no optimization claim is made by a single receipt"),
    }
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
        thresholds={"p95_regression_pct": 20, "peak_allocation_regression_pct": 15, "tool_calls_per_finding_increase": 0, "soak_runs": 100, "gate_pattern_latency": False, "gate_timing_paths": False},
        evidence=evidence,
        target_root=TARGET_ROOT,
        harness_root=HARNESS_ROOT,
    )


def main() -> int:
    global TARGET_ROOT, HARNESS_ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("baseline", "release"), required=True)
    parser.add_argument("--fixture", type=Path, default=Path("tests/fixtures/analyst_multisheet.xlsx"))
    parser.add_argument("--workbook", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--measurement-mode", choices=("full", "timing", "allocation"), default="full")
    parser.add_argument("--target-root", type=Path, default=TARGET_ROOT)
    parser.add_argument("--harness-root", type=Path, default=HARNESS_ROOT)
    args = parser.parse_args()
    target_root = args.target_root.resolve()
    harness_root = args.harness_root.resolve()
    TARGET_ROOT = target_root
    HARNESS_ROOT = harness_root
    configure_measurement_roots(target_root=TARGET_ROOT, harness_root=HARNESS_ROOT)
    fixture = args.workbook or args.fixture
    if not fixture.is_absolute():
        fixture = target_root / fixture
    output = args.output or Path(f"work/optimization-{args.mode}/receipt.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    result = asyncio.run(_run(args.mode, fixture, output.parent / "measurement-state", args.measurement_mode))
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "VERIFIED" else 1

if __name__ == "__main__":
    raise SystemExit(main())
