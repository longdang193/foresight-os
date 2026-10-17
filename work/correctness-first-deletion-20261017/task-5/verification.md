# Task 5 Verification

## Implementation

- Cached workbook and analysis results now carry construction-time retained-byte weights.
- Cache publication consumes the retained weight instead of recomputing `repr(...)`.
- Authority mutations advance a generation token.
- `WorkbookContext` reuses authority validation for warm hits, restores evicted authority transactionally, snapshots validation tokens for rollback, and prunes tokens for evicted cache entries.
- Warm-hit source normalization avoids reconstructing an immutable result when the source identity is unchanged.

## Focused proof

Commands:

```text
python -m pytest -q tests/test_optimization_measurement.py
python -m pytest -q tests/test_local_toolbelt.py tests/test_runtime_boundaries.py tests/test_optimization_measurement.py
```

Results:

- Optimization measurement tests: `10 passed`.
- Task 5 focused suites: `120 passed`.
- New retained-size and authority-generation regressions pass.
- Existing authority-eviction, rollback, cancellation, cleanup, and bounded-cache tests pass.

## Matched release evidence

```text
python evaluation/probes/run_optimization_probe.py --mode release --fixture tests/fixtures/analyst_multisheet.xlsx --output work/correctness-first-deletion-20261017/task-5/final/receipt.json
python evaluation/probes/compare_optimization_receipts.py --baseline work/correctness-first-deletion-20261017/task-4/base/receipt.json --release work/correctness-first-deletion-20261017/task-5/final/receipt.json --output work/correctness-first-deletion-20261017/task-5/comparison.json
```

The final receipt and comparison use the same frozen harness, fixture, workload identity, and mandatory workload set as Task 4. The comparison gate is `PASS`:

- Mandatory workbook workloads: all `VERIFIED`.
- Correctness, allocation, latency, and soak evidence: `VERIFIED`.
- Accepted finding count: unchanged at `1`.
- Per-finding economics: unchanged.
- Peak allocation regression: `0.0%`.
- RSS regression: `0.446%`.
- Workbook p95 regression: `10.442%` (threshold `20%`).
- Timing paths remain within the `20%` regression threshold; warm same-view repeat improves by `23.551%`.
- No reused stage issued new model or tool calls.

Provider/MCP warnings emitted by the probe remain separate from the credential-free local workbook evidence and do not change the local acceptance result.
