# Task 1 Evidence: Owner Inventory And Frozen Baseline

## Workspace identity

- Primary checkout: `C:\Users\HOANG PHI LONG DANG\repos\foresight-OS`
- Primary checkout state: dirty before execution; preserved and not edited.
- Implementation worktree: `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\correctness-first-deletion-pass\foresight-OS`
- Creation mechanism: platform-managed linked worktree.
- Branch: `codex/correctness-first-deletion-pass`
- Base commit: `14bd69644b7012639c00a65fa94cdd67f52b4c62`
- Activation HEAD: `14bd69644b7012639c00a65fa94cdd67f52b4c62`
- Commit/push/merge/reset/cleanup: not authorized and not performed.

## Canonical owners confirmed

- `src/foresight_os/runtime/local_toolbelt.py` owns `WorkbookContext`,
  `WorkbookReadCache`, source snapshots, authority registration, retained-byte
  accounting, `spreadsheet_read`, and `data_analysis`.
- `src/foresight_os/analysis/workbook_inputs.py` owns shared workbook reads,
  table-local explicit column mappings, canonical-column validation, and row
  extraction helpers.
- `src/foresight_os/domain/analysis_inputs.py` owns `NormalizedIntent` and
  `AnalysisInputContract`; `NormalizedIntent.fingerprint` already includes
  contracts, stages, policies, dependencies, source needs, and limits.
- `src/foresight_os/runtime/workflow.py` owns stage fingerprints, the
  compatibility `stage_cache` path, `StageReceipt` reuse, synthesis, and
  production stage dispatch.
- `src/foresight_os/persistence/analysis_store.py` owns durable `StageReceipt`
  persistence and canonical analysis state.
- `src/foresight_os/analysis/evidence_workflow.py` directly composes workbook
  reads, deterministic analysis, review, and persistence; it currently bypasses
  a single context-level analysis publication transaction.

## Defect reproduction matrix

| Reviewed concern | Task 1 result | Evidence |
| --- | --- | --- |
| Nested cached-result mutation | `REPRODUCED` | Added `tests/test_local_toolbelt.py::test_analysis_cache_hit_is_immune_to_nested_result_mutation`; the returned `AnalysisResult.rows[0]` is mutable and corrupts the next cache hit while leaving `deterministic_key` unchanged. |
| Rejected analysis publication | `REPRODUCED` | Added `tests/test_evidence_workflow.py::test_xlsx_finding_workflow_rolls_back_analysis_cache_when_persistence_rejects`; a rejecting `save_pending` leaves `context.cache.analysis_bytes == 784`. |
| Direct workflow publication bypass | `CONFIRMED_BY_SOURCE` | `run_xlsx_finding_workflow` calls `data_analysis` with cache/authority internals directly after `WorkbookContext.read`; no context-level analysis transaction exists. |
| Explicit mapping fallback | `NOT_REPRODUCED` | Existing `tests/test_analysis_input_contract.py` covers missing mapped sources and canonical-name fallback; both passed in the Task 1 focused suite. |
| Single-output synthesis bypass | `NOT_REPRODUCED` | Existing direct synthesis payload preflight test passed; `_synthesize_stage_outputs` checks payload bytes before returning one output. |
| Warm-hit authority scanning | `CONFIRMED_BY_SOURCE` | `WorkbookContext.read` rebuilds an authority-key set from every cached measurement on each warm hit; existing test proves transaction bypass but not O(1) authority validity. |

## Frozen measurement protocol

- Base/release identity: exact Git commit plus the probe's tracked-source tree
  digest over `src`, `tests`, `evaluation`, `.github`, `README.md`, and
  `pyproject.toml`.
- Harness identity: `evaluation/probes/run_optimization_probe.py`,
  `evaluation/probes/optimization_measurement.py`, and
  `evaluation/probes/compare_optimization_receipts.py`; receipt schema is
  currently version `2`. Task 4 must add an explicit harness version and
  top-level identity validation before matched comparison.
- Fixture: `tests/fixtures/analyst_multisheet.xlsx`, SHA-256
  `3f381b148ab6f2d0942061964b3851b26e4a66c224dd0866d431cc3c9d52d123`.
- Workload: two warmups; ten measured samples; five process-level patterns;
  mandatory workbook workloads are cold read, same-view repeat, different
  selection, analyst/validator reuse, repeated investigation, retained-context
  growth, multi-workbook isolation, and blocking cancellation.
- Warm/cold rules: warmups are discarded; repeated samples stay in one
  run-owned context where the workload requires reuse; source changes and
  alternate selections remain separate workload identities.
- Aggregation: report p50/p90/p95 latency, peak allocation, retained read /
  analysis / authority bytes, cache/capture/parse/currentness counters, stage
  reuse and call economics; do not merge correctness status into timing.
- Environment: Python executable/version, platform, package freeze, worktree
  path, commit, source digest, and fixture digest are recorded.
- Unsupported or unavailable provider/model dimensions are `FINAL_ONLY`,
  `NOT_MEASURED`, `DEFERRED`, or `BLOCKED_EXTERNAL`; they cannot create a
  passing optimization gate.
- Timing thresholds are secondary decision thresholds only: p95 regression
  <=20%, peak allocation regression <=15%, RSS regression <=15%, and no
  economic regression or reused-stage new calls. Correctness, rollback,
  provenance, cancellation, and cleanup remain mandatory regardless of timing.

## Baseline commands and result

- Focused suite: `python -m pytest -q tests/test_local_toolbelt.py tests/test_runtime_boundaries.py tests/test_result_committer.py tests/test_selective_reuse.py tests/test_evidence_workflow.py tests/test_optimization_measurement.py`
- Focused suite result: `PASS` before the two new red reproductions.
- Baseline probe: `python evaluation/probes/run_optimization_probe.py --mode baseline --fixture tests/fixtures/analyst_multisheet.xlsx --output work/correctness-first-deletion-20261017/task-1/baseline/receipt.json`
- Baseline receipt: `work/correctness-first-deletion-20261017/task-1/baseline/receipt.json`
- Baseline status: local workbook workloads and native MCP fixture `VERIFIED`;
  the process emitted a non-fatal MCP exit-stack cleanup warning, which remains
  a follow-up verification concern rather than evidence of analytical success.
- Baseline revision: commit
  `14bd69644b7012639c00a65fa94cdd67f52b4c62`, source digest
  `fe32c46f06128910d71cd4cb20f03ae5fac293ca6fc03425cb47c02b87f8cf11`.
