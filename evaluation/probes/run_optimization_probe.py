from __future__ import annotations

import argparse
import asyncio
import json
import os
import socket
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path
from statistics import median

from agent_framework import Agent, ChatResponse, ChatResponseUpdate, Content, FunctionInvocationContext, Message, ResponseStream

from foresight_os.controller.recipes import ExecutionPattern, RecipeName, make_recipe
from foresight_os.runtime.capabilities import CapabilityDefinition, CapabilityScope, instrument_tool
from foresight_os.runtime.local_toolbelt import AnalysisOperation, SheetSelection, data_analysis, spreadsheet_read
from foresight_os.runtime.workflow import run_recipe_async
from optimization_measurement import build_receipt, observed_xlsx_state, stage_metric


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
    for _ in range(2):
        result = spreadsheet_read(path, SheetSelection(include_hidden=True, include_hidden_rows=True))
    for _ in range(10):
        tracemalloc.start()
        started = time.perf_counter()
        result = spreadsheet_read(path, SheetSelection(include_hidden=True, include_hidden_rows=True))
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        durations.append((time.perf_counter() - started) * 1000)
        allocations.append(peak)
    table = result.tables[0]
    value_column = "Value" if "Value" in table.columns else table.columns[-1]
    analysis = data_analysis(table, AnalysisOperation("aggregate", value_column=value_column))
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
    }


async def _measure_patterns() -> tuple[dict[str, object], list[dict[str, object]]]:
    receipts: dict[str, object] = {}
    stage_metrics: list[dict[str, object]] = []
    for recipe_name in (RecipeName.DIRECT, RecipeName.ANALYZE, RecipeName.CONCURRENT, RecipeName.HANDOFF, RecipeName.CHALLENGE_RECOMMENDATION):
        recipe = make_recipe(recipe_name)
        for _ in range(2):
            await run_recipe_async(recipe, "optimization baseline", _ProbeClient(), f"warm-{recipe_name.value}")
        samples: list[float] = []
        last = None
        for index in range(10):
            started = time.perf_counter()
            last = await run_recipe_async(recipe, "optimization baseline", _ProbeClient(), f"measure-{recipe_name.value}-{index}")
            samples.append((time.perf_counter() - started) * 1000)
        if last is not None:
            stage_metrics.append(stage_metric("stage-1", recipe.pattern, last, samples[-1]))
        receipts[recipe_name.value] = {
            "p50_ms": round(median(samples), 3),
            "p95_ms": round(sorted(samples)[-1], 3),
            "model_calls": last.metrics.model_calls if last else 0,
            "cleanup_complete": bool(last and last.metrics.cleanup_complete),
        }
    return receipts, stage_metrics


async def _soak_receipt() -> dict[str, object]:
    recipe = make_recipe(RecipeName.ANALYZE)
    resource_counts: list[int] = []
    for index in range(100):
        result = await run_recipe_async(recipe, "optimization soak", _ProbeClient(), f"soak-{index}")
        resource_counts.append(0 if result.metrics.cleanup_complete else 1)
    return {
        "runs": len(resource_counts),
        "resource_counts": {"owned_after_cleanup": resource_counts[-1] if resource_counts else 0},
        "monotonic_growth": any(right > left for left, right in zip(resource_counts, resource_counts[1:])),
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
    call = instrument_tool(external_call, CapabilityDefinition("external_fixture", "external_read"), {"metrics": metrics})
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
        external_fixture={"tool_calls": metrics.tool_calls, "failures": metrics.tool_failures},
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
