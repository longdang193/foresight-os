---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: foresight-os-correctness-measurement-pass
targets:
  - src/foresight_os/analysis/workbook_inputs.py
  - src/foresight_os/analysis/powerbi_strategic_portfolio.py
  - src/foresight_os/analysis/evidence_workflow.py
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/analysis/result_committer.py
  - src/foresight_os/persistence/analysis_store.py
  - src/foresight_os/analysis/review_workflow.py
  - evaluation/probes/optimization_measurement.py
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/compare_optimization_receipts.py
  - evaluation/README.md
  - tests/test_analysis_input_contract.py
  - tests/test_evidence_workflow.py
  - tests/test_local_toolbelt.py
  - tests/test_orchestration_patterns.py
  - tests/test_result_committer.py
  - tests/test_optimization_measurement.py
  - tests/test_runtime_boundaries.py
  - docs/superpowers/plans/2026-10-17-15-50-foresight-os-correctness-measurement-pass-plan.md
---

# ForesightOS Correctness And Measurement Pass

## Goal

Finish the remaining correctness boundaries identified in the consolidated
verdict, repair the benchmark so it measures the real shared-context path, and
remove only duplicated runtime work that is proven to be active after the
correctness fixes. Preserve the existing content-addressed provenance,
bounded-resource, cancellation, transactional-publication, canonical-result,
independent-review, and durable-receipt contracts.

This plan is intentionally smaller than a new architecture programme. The
three P0 correctness changes and truthful benchmark are mandatory. Authority,
retained-memory, eviction, compatibility, and orchestration changes are
measurement-gated and must be recorded as deferred when the evidence does not
show material benefit.

## Implementation Outcomes

### Exact table-local input contracts

Explicit column mappings resolve against the exact table that consumes the
canonical field and fail clearly when that table lacks the requested source
column. Omitted mappings retain documented compatibility behavior. A mapping
present only in another table can never be silently ignored. Power BI analysis
retains the selected period identity and provenance through the mapped table.

### Bounded, cancellable workbook publication

Standalone XLSX finding workflows reject oversized inputs before retaining a
full capture, use one workflow-owned `WorkbookContext` when the caller does
not provide one, and deterministically close only resources they own. A final
cancellation check runs immediately before reusable cache/authority
publication while rollback remains possible. Cancelled new work leaves no new
reusable state and preserves an earlier valid committed revision.

### Single-pass typed synthesis

Single typed stage output is structurally bounded and normalized once before
durable commit, using only the stage-declared dependency records for reference
resolution. Multi-output synthesis keeps its merge and conflict checks.
Commit-time provenance, dependency, currentness, and persistence checks remain
owned by their existing canonical owners. Active synthesis cancellation is
measured; worker offload is implemented only if the measured cancellation
latency is material.

### Truthful repeated-investigation evidence

The optimization probe reuses one `WorkbookContext` for repeated identical
finding investigations and reports repeated distributions plus separate
capture, parse, currentness, read-cache, analysis-cache, and retained-resource
counters. Local workbook correctness remains valid when optional provider or
MCP evidence is unavailable. Correctness, regression-threshold acceptance, and
optimization demonstration are reported as separate outcomes.

### Conditional simplification

Only measured regressions or active duplicate production paths may justify
authority-token, retained-memory, cache-eviction, `stage_cache`, repeated
normalization, schema-construction, or wrapper changes. Unjustified structural
work is recorded as deferred rather than added speculatively.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`, `skill-plan-document-reviewer`
- Isolation: `dedicated Git worktree created from origin/main@27002c03b0c837ab8937b9c7e34a89bf35322b3f`
- Commit policy: `no commits during execution`; the lead controller records task proof before any separately authorized branch disposition
- Preauthorized local actions: `create or reuse the named worktree, edit only declared plan-lane files, run focused tests, run the repository verification commands, and write benchmark artifacts outside Git`
- User-approval actions: `push, pull-request creation, review assignment, merge, deletion of user artifacts, destructive recovery, and cleanup of the preserved primary checkout`
- Parallel ownership: `none; same-worktree writes are sequential`
- Sequential fallback: `reconcile the remote baseline, then execute Tasks 2 through 8 in order; stop before a gated task when its prerequisite evidence is missing or contradictory`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/foresight-os-correctness-measurement-pass`
- Base commit: `27002c03b0c837ab8937b9c7e34a89bf35322b3f`
- Expected workspace: `dedicated clean worktree from 27002c03b0c837ab8937b9c7e34a89bf35322b3f; preserve the primary checkout's existing modified and untracked files without copying or staging them`
- Next action: `branch finishing after verified completion; commit, push, open PR, review, and merge are separately authorized lifecycle actions`
- Blockers: `none; primary checkout is dirty but intentionally excluded from the execution worktree`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `complete` | dedicated worktree | `lead controller` | none | baseline and owner inventory | pinned SHA verified; named owners and tests present; focused baseline tests passed |
| Task 2 | `complete` | dedicated worktree | `lead controller` | Task 1 | table-local mapping regressions | Power BI now passes full mappings to the table-local helper; cross-table source and multi-consumer refresh regressions pass |
| Task 3 | `complete` | dedicated worktree | `lead controller` | Task 1 | cancellation, rollback, bounds, cleanup tests | limits/cancellation propagated; context ownership and rollback regressions pass |
| Task 4 | `complete` | dedicated worktree | `lead controller` | Tasks 2 and 3 | frozen benchmark references and comparator proof | frozen harness digest `11c17bda3805d1bc0125adc2165eb2a90b8c83ff7cbe75c44528ac79911f5b0c`; pristine reference and post-Tasks-2–3 optimization baseline both valid with local correctness `VERIFIED`; optional MCP failure isolated; receipts stored under `$env:TEMP\foresight-os-next-pass` |
| Task 5 | `complete` | dedicated worktree | `lead controller` | Task 4 | single-output synthesis tests and cancellation measurement | single typed output reaches the committer as `StageAnalyticalResult` after one normalization; focused orchestration/committer tests pass; 20/20 cancellation settlements measured, p50 `0.111 ms`, p95 `0.177 ms`, max `0.223 ms`; worker offload deferred |
| Task 6 | `complete` | dedicated worktree | `lead controller` | Tasks 4 and 5 | gated cache/authority evidence or explicit deferral | no runtime optimization justified: retained-state estimates and peak allocation unchanged, RSS `-0.618%`, repeated-investigation path `+6.952%` versus optimization baseline, cache/eviction/cross-source authority checks `VERIFIED`; authority/memory/eviction and lock-scope candidates explicitly deferred |
| Task 7 | `complete` | dedicated worktree | `lead controller` | Tasks 4–6 | mandatory compatibility audit and optional safe deletions | `stage_cache` retained — live reuse, provenance, and tamper tests; `normalize_work_brief` retained — distinct controller, gate, and domain consumers; schema retained — preflight/runtime boundary consumers; wrapper cleanup deferred — no proven duplicate owner or migration-safe deletion; focused inventory tests pass |
| Task 8 | `complete` | dedicated worktree | `lead controller` | Tasks 1–7 | full repository and benchmark verification | full pytest and compile checks passed; Markdown-link check passed; review-cycle-1 findings fixed with focused regressions for dependency scope, record budgets, and durable cancellation settlement; review-cycle-2 race finding fixed with an ownership-aware rollback regression; final frozen-harness comparison passed with local correctness `VERIFIED`, regression threshold `VERIFIED`, optimization demonstration `NOT_MEASURED` by design; incidental probe artifact restored and final scope reconciled |

## Task Breakdown

### Task 1: Reconcile the execution baseline

**Purpose:**
- Establish a clean, isolated starting point that contains the merged PR #31 correctness work without importing unrelated primary-checkout changes.

**Task Function:**
- Baseline reconciliation and ownership inventory.

**Template Profile:**
- Executor: `lead controller`
- Selection basis: single-controller sequential execution owns Git identity, source ownership, and task boundaries.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller owns baseline acceptance.

**Specification Coverage:**
- Preserve PR #31 correctness changes; keep Git, the plan, and the dedicated worktree as the recovery source.

**Required Skills:**
- `skill-using-git-worktrees`, `skill-plan-document-reviewer`

**Files And Symbols:**
- Inspect: `origin/main@27002c03b0c837ab8937b9c7e34a89bf35322b3f`
- Inspect: `src/foresight_os/runtime/local_toolbelt.py:SourceSnapshot`, `WorkbookContext`, `WorkbookReadCache`, `spreadsheet_read`, `data_analysis`
- Inspect: `src/foresight_os/analysis/workbook_inputs.py:validate_mapping_targets`, `apply_column_mappings`, `apply_table_column_mappings`
- Inspect: `src/foresight_os/analysis/evidence_workflow.py:run_xlsx_finding_workflow`, `_run_xlsx_finding_workflow`
- Inspect: `evaluation/probes/run_optimization_probe.py:_repeated_workflow`, `_retained_context_workloads`, `_measure_workbook`
- Verify: `git status --short`, `git rev-parse HEAD`, `git diff --check`

**Dependencies:**
- The remote `main` ref has been fetched and resolves to `27002c03b0c837ab8937b9c7e34a89bf35322b3f`.

**Authority:**
- Preauthorized local actions: create or reuse the dedicated worktree from the declared base and read source, tests, plans, and Git metadata.
- Stop for: a base commit mismatch, unexpected copied dirty files, or any need to reset, clean, stash, or overwrite the primary checkout.

**Steps:**
- [ ] Step 1: Create or attach the dedicated worktree at the declared branch and verify its `HEAD` equals the declared base before editing.
- [ ] Step 2: Inventory the canonical owners and current tests listed above, recording any symbol drift in the plan's Evidence field rather than inventing a parallel owner.
- [ ] Step 3: Confirm the primary checkout remains unchanged and all benchmark output will be written outside both Git worktrees.

**Verification:**
- [ ] `git status --short` in the dedicated worktree is empty before edits.
- Expected: `HEAD` is `27002c03b0c837ab8937b9c7e34a89bf35322b3f`; primary-checkout modifications are absent from the worktree.

**Exit Criteria:**
- The isolated baseline and canonical owner inventory are recorded, and Task 2 can begin without touching the preserved primary checkout.

### Task 2: Enforce table-local exact mappings

**Purpose:**
- Prevent explicit Power BI mappings from being silently ignored when the mapped source header exists in a different table.

**Task Function:**
- Contract-boundary correction for table-scoped input resolution.

**Template Profile:**
- Executor: `lead controller`
- Selection basis: single-controller sequential execution keeps the bounded correctness change and its tests in one owner lane.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused contract tests provide the task-local validator.

**Specification Coverage:**
- Explicit mappings are exact-or-fail within the consuming table; omitted mappings alone may use compatibility behavior.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/test first: `src/foresight_os/analysis/workbook_inputs.py:apply_table_column_mappings`, `validate_mapping_targets`
- Modify: `src/foresight_os/analysis/powerbi_strategic_portfolio.py:analyze_powerbi_strategic_portfolio`
- Verify: `tests/test_analysis_input_contract.py` mapping tests and `tests/test_technology_powerbi_validator.py`

**Dependencies:**
- Task 1 complete; exact current table-consumption sets are recorded from the baseline.

**Authority:**
- Preauthorized local actions: inspect and test the existing table-scoped helper, modify only the Power BI consumer and focused mapping tests, and run the named test modules.
- Stop for: a required mapping contract change outside the workbook-input and Power BI owners, or a fixture that requires changing stored analytical truth.

**Steps:**
- [ ] Step 1: Remove the Power BI consumer's workbook-global mapping validation and source-header prefilter; pass `contract.column_mappings` directly to the existing `apply_table_column_mappings()` helper for each consuming table.
- [ ] Step 2: Prove through focused tests that the existing helper enforces `MISSING_MAPPED_COLUMN` for a non-empty explicit mapping absent from the exact table, while omitted mappings retain compatibility behavior.
- [ ] Step 3: Add a fixture where the source header exists in another table and assert the target-table analysis fails instead of silently using canonical/default data.
- [ ] Step 4: Preserve period labels, source locators, workbook hashes, and numeric results for valid mapped and unmapped cases.

**Verification:**
- [ ] `python -m pytest -q tests/test_analysis_input_contract.py tests/test_technology_powerbi_validator.py`
- Expected: valid renamed revenue and refresh mappings still pass; cross-table explicit mappings fail clearly; no existing period/provenance regressions occur.

**Exit Criteria:**
- Every explicit mapping used by the Power BI recipe is validated against its consuming table, and the regression fixture proves silent cross-table ignore is impossible.

### Task 3: Close publication cancellation and standalone capture ownership

**Purpose:**
- Ensure cancellation and input limits are enforced at the final reusable-publication boundary without losing prior valid committed state.

**Task Function:**
- Transaction and resource-lifecycle hardening at the workbook-analysis boundary.

**Template Profile:**
- Executor: `lead controller`
- Selection basis: single-controller sequential execution keeps rollback, resource ownership, and backend failure paths aligned.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct boundary tests are the task-local validator.

**Specification Coverage:**
- Final cancellation check before publication; bounded capture before full retention; deterministic workflow-owned cleanup; preservation of earlier committed state; compatibility for caller-provided snapshots.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/runtime/local_toolbelt.py:ToolbeltLimits`, `SourceSnapshot.capture`, `WorkbookContext.capture`, `WorkbookContext.read`, `WorkbookContext.analyze`, `WorkbookContext.currentness`, `WorkbookContext.transaction`, `_publish_read_result`
- Inspect/modify: `src/foresight_os/analysis/evidence_workflow.py:run_xlsx_finding_workflow`, `_run_xlsx_finding_workflow`; add `limits: ToolbeltLimits | Mapping[str, Any] | None`, `cancel_check: Callable[[], bool] | None`, and `snapshot: SourceSnapshot | None` while preserving the existing `workbook_context` parameter.
- Inspect: `src/foresight_os/persistence/analysis_store.py:save_pending`, `commit_revision`
- Inspect: `src/foresight_os/analysis/review_workflow.py:accept_pending_analysis`
- Verify: `tests/test_evidence_workflow.py`, `tests/test_local_toolbelt.py`, `tests/test_runtime_boundaries.py`

**Dependencies:**
- Task 1 complete; Task 2 mapping changes must not alter the workbook transaction contract.

**Authority:**
- Preauthorized local actions: modify only the named runtime/workflow owners and focused backend tests; use temporary fixtures under pytest-managed directories.
- Stop for: any need to change `AnalysisStore` revision semantics, delete an existing accepted revision, or broaden persistence/review ownership without a new approved specification.

**Steps:**
- [ ] Step 1: Define the ownership matrix: a caller-provided `WorkbookContext` is reused and never closed; a caller-provided `SourceSnapshot` is reused and never recaptured; when neither is supplied, the workflow creates a bounded context and clears it in `finally`.
- [ ] Step 2: Use `ToolbeltLimits.max_bytes` as the source-capture limit and keep `WorkbookContext.max_bytes` as retained cache capacity; do not pass the cache budget as the read limit.
- [ ] Step 3: For the snapshot compatibility path, reject `snapshot.byte_count > limits.max_bytes` before parsing and verify `snapshot.is_current(cancel_check=cancel_check)` after analysis; do not claim to prevent a caller that already captured an oversized snapshot.
- [ ] Step 4: Propagate `cancel_check` through read, analysis, currentness, and the transaction publication boundary. The final sequence is operation complete → cancellation check → retained-budget check → cache/authority transaction commit.
- [ ] Step 5: Roll back only mutations from the cancelled transaction, preserve prior accepted state, and keep stage-receipt publication out of this XLSX workflow task because `run_recipe_async()` owns that boundary.
- [ ] Step 6: Add success, oversize, caller-snapshot, caller-context, cancellation-after-wait, persistence-rejection, and cleanup assertions.

**Verification:**
- [ ] `python -m pytest -q tests/test_evidence_workflow.py tests/test_local_toolbelt.py tests/test_runtime_boundaries.py`
- Expected: oversized standalone input fails before full capture; caller snapshots are validated but not recaptured; cancellation leaves zero new cache/authority mutations; prior accepted state remains loadable; workflow-created contexts close on every terminal path; caller-owned contexts remain open.

**Exit Criteria:**
- The direct workbook boundary proves bounded capture, rollback-safe cancellation, truthful currentness, and deterministic ownership cleanup.

### Task 4: Repair and freeze the benchmark before optimization

**Purpose:**
- Produce one frozen harness and two digest-bound references: pristine main as the regression reference, and the post-Tasks-2–3 tree as the optimization baseline.

**Task Function:**
- Benchmark contract repair and reproducible evidence generation.

**Template Profile:**
- Executor: `lead controller`
- Selection basis: single-controller sequential execution owns the frozen harness, fixture determinism, and performance evidence.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: comparator tests and local receipt checks provide validation.

**Specification Coverage:**
- One `WorkbookContext` is reused for identical repeated investigations; counters and distributions identify the actual path; optional provider/MCP failures do not invalidate local workbook correctness.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `evaluation/probes/run_optimization_probe.py:_repeated_workflow`, `_retained_context_workloads`, `_measure_workbook`, `main`
- Inspect/modify: `evaluation/probes/optimization_measurement.py:MANDATORY_XLSX_WORKLOADS`, `_metric_snapshot`, `_summarize_samples`, `build_receipt`, `measurement_evidence`
- Inspect/modify: `evaluation/probes/compare_optimization_receipts.py:compare`, `validate_stability`
- Verify: `tests/test_optimization_measurement.py`
- Document: `evaluation/README.md` measurement status and limitation rules

**Dependencies:**
- Tasks 2 and 3 complete; no synthesis, authority, memory, eviction, or compatibility optimization is applied before the references are captured.

**Authority:**
- Preauthorized local actions: modify only the named probe, comparator, test, and evaluation documentation files; copy the repaired harness and write raw receipts under an external temporary directory.
- Stop for: a workload that cannot prove local correctness, a provider failure that is incorrectly treated as a local failure, or a benchmark that reads from either measured Git worktree.

**Steps:**
- [x] Step 1: Make the probe accept explicit `--target-root` and `--harness-root` values; import the measured package from `target-root/src` and load benchmark helpers only from the frozen harness root.
- [x] Step 2: Record separate harness digest, measured target commit, measured target `source_tree_sha256`, fixture digest, Python/environment, limits, warmups, and sample-count metadata in every receipt. Make `process_runs` count actual independent process runs or remove it.
- [x] Step 3: Copy the repaired `optimization_measurement.py`, `run_optimization_probe.py`, and `compare_optimization_receipts.py` to `$env:TEMP\foresight-os-next-pass\frozen-harness`; this directory is not either measured source root.
- [x] Step 4: Run the frozen harness against a clean temporary worktree at exact SHA `27002c03b0c837ab8937b9c7e34a89bf35322b3f` and against the current implementation worktree after Tasks 2–3; record the latter digest as the optimization baseline without committing it.
- [x] Step 5: Make the receipt report `correctness`, `regression_threshold`, and `optimization_demonstrated` independently, with `VERIFIED`, `FAILED`, `NOT_MEASURED`, or `DEFERRED` plus a limitation for non-verified outcomes.
- [x] Step 6: Ensure optional MCP/provider failure affects only its external evidence field; local workbook correctness and cache counters remain evaluable.
- [x] Step 7: Update comparator tests so zero denominators, missing workloads, unstable samples, increased calls, harness mismatch, target mismatch, and resource regressions are rejected without collapsing a valid local correctness result.

**Verification:**
- [x] `python -m pytest -q tests/test_optimization_measurement.py`
- [ ] `$env:NEXT_PASS_ROOT = Join-Path $env:TEMP "foresight-os-next-pass"; $env:IMPLEMENTATION_WORKTREE = (Get-Location).Path; New-Item -ItemType Directory -Force -Path "$env:NEXT_PASS_ROOT\frozen-harness", "$env:NEXT_PASS_ROOT\references"`
- [ ] `if (Test-Path "$env:NEXT_PASS_ROOT\regression-worktree") { if (-not (Test-Path "$env:NEXT_PASS_ROOT\regression-worktree\.git")) { throw "refusing to reuse non-worktree path" }; if ((git -C "$env:NEXT_PASS_ROOT\regression-worktree" rev-parse HEAD).Trim() -ne "27002c03b0c837ab8937b9c7e34a89bf35322b3f") { throw "regression worktree is not at the declared SHA" } } else { git worktree add --detach "$env:NEXT_PASS_ROOT\regression-worktree" 27002c03b0c837ab8937b9c7e34a89bf35322b3f }`
- [ ] `Copy-Item evaluation/probes/optimization_measurement.py, evaluation/probes/run_optimization_probe.py, evaluation/probes/compare_optimization_receipts.py "$env:NEXT_PASS_ROOT\frozen-harness"`
- [ ] `Push-Location "$env:NEXT_PASS_ROOT\frozen-harness"; python evaluation/probes/run_optimization_probe.py --mode baseline --target-root "$env:NEXT_PASS_ROOT\regression-worktree" --harness-root "$env:NEXT_PASS_ROOT\frozen-harness" --fixture "$env:NEXT_PASS_ROOT\regression-worktree\tests\fixtures\analyst_multisheet.xlsx" --output "$env:NEXT_PASS_ROOT\references\regression-reference.json" --measurement-mode full; Pop-Location`
- [ ] `Push-Location "$env:NEXT_PASS_ROOT\frozen-harness"; python evaluation/probes/run_optimization_probe.py --mode baseline --target-root "$env:IMPLEMENTATION_WORKTREE" --harness-root "$env:NEXT_PASS_ROOT\frozen-harness" --fixture "$env:IMPLEMENTATION_WORKTREE\tests\fixtures\analyst_multisheet.xlsx" --output "$env:NEXT_PASS_ROOT\references\optimization-baseline.json" --measurement-mode full; Pop-Location`
- Expected: both receipts carry identical harness metadata but distinct target metadata; repeated investigation shows one capture and one parse for identical material; local correctness is independent from external evidence; no optimization claim is made from a regression ceiling alone.

**Exit Criteria:**
- The frozen harness produces a valid regression reference and optimization baseline that can attribute later synthesis/cache changes without requiring a checkpoint commit.

### Task 5: Remove duplicate single-output synthesis normalization

**Purpose:**
- Keep one semantic normalization of a single typed result between provider decoding and canonical commit while retaining canonical validation and multi-output merge behavior.

**Task Function:**
- Runtime synthesis-path simplification with cancellation measurement.

**Template Profile:**
- Executor: `lead controller`
- Selection basis: single-controller sequential execution keeps cross-owner runtime semantics and validation evidence together.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: orchestration and committer regressions cover the boundary.

**Specification Coverage:**
- Single-output synthesis normalizes once semantically; commit-time canonical checks remain authoritative; the external `run_recipe_async()` result shape and `stage_outputs` audit material remain unchanged.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`, `skill-performance-optimization`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/runtime/workflow.py:_synthesize_stage_outputs`, `run_recipe_async`
- Inspect/modify: `src/foresight_os/analysis/result_committer.py:normalize_stage_result`, `CanonicalResultCommitter.__call__`
- Verify: `tests/test_orchestration_patterns.py`, `tests/test_result_committer.py`
- Measure: frozen harness synthesis-cancellation workload and `evaluation/probes/optimization_measurement.py` sample schema

**Dependencies:**
- Task 4 complete; the optimization baseline receipt is valid and the canonical result/persisted-review owners remain unchanged.

**Authority:**
- Preauthorized local actions: modify only the synthesis/committer boundary and focused tests; rerun the frozen harness after the change; do not move persistence into a background worker.
- Stop for: evidence that the committer requires a second semantic normalization pass, loss of typed internal validation, changed public result shape, or a worker-boundary redesign that lacks a separate approved decision.

**Steps:**
- [x] Step 1: Preflight payload byte limits, normalize the single typed output once semantically, retain the typed internal representation, and pass it through to the committer without re-decoding it.
- [x] Step 2: Keep per-participant normalization, conflict detection, alias resolution, and merge behavior for true multi-output synthesis.
- [x] Step 3: Add call-count, invalid-relationship, public-result-shape, and `stage_outputs` audit tests proving the single path is one semantic pass while durable dependency/provenance checks still reject bad output.
- [x] Step 4: Measure active cancellation-to-settlement distributions; defer worker offload unless the evidence establishes material synchronous delay and a separately approved worker-boundary change is available.

**Verification:**
- [x] `python -m pytest -q tests/test_orchestration_patterns.py tests/test_result_committer.py`
- [ ] Compare the final synthesis workload against `$env:TEMP\foresight-os-next-pass\references\optimization-baseline.json` using the unchanged frozen harness.
- Expected: single-output semantic normalization is one pass; structural bounds and dangling references still fail; multi-output conflict tests pass; public result and audit shapes are unchanged; cancellation evidence is explicit.

**Exit Criteria:**
- Redundant single-output semantic normalization is removed without weakening canonical validation or changing the external workflow contract.

### Task 6: Apply measurement-gated authority, memory, and eviction changes

**Purpose:**
- Improve bookkeeping only when Task 5 demonstrates a material alternating-workbook, authority-rescan, retained-memory, or eviction problem.

**Task Function:**
- Evidence-gated runtime optimization.

**Template Profile:**
- Executor: `lead controller`
- Selection basis: single-controller sequential execution applies at most one measured runtime change at a time.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: local toolbelt regressions and the repaired benchmark validate any accepted change.

**Specification Coverage:**
- Keep live-file currentness separate from authority validity; use local validity tokens, deterministic retained ownership, and coherent weighted/LRU eviction only when measurements justify them.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify only if evidence passes the gate: `src/foresight_os/runtime/local_toolbelt.py:AuthorityIndex`, `WorkbookContext`, `WorkbookReadCache`, `_retained_size`, `WorkbookStats`; conditionally include `src/foresight_os/analysis/evidence_workflow.py:run_xlsx_finding_workflow` only if lock or transaction-scope narrowing is the measured candidate.
- Verify only if changed: `tests/test_local_toolbelt.py`, `tests/test_evidence_workflow.py`, `evaluation/probes/run_optimization_probe.py:_retained_context_workloads`

**Dependencies:**
- Task 5 receipt contains complete local correctness and counter evidence.

**Authority:**
- Preauthorized local actions: make only the smallest measured runtime change and its focused tests; otherwise record a `DEFERRED` gate result without editing runtime code.
- Stop for: missing counters, no material measured benefit, loss of explicit source-currentness checks, cross-workbook authority aliasing, or retained bytes exceeding the declared budget.

**Steps:**
- [x] Step 1: Compare alternating-workbook rescans, deterministic retained-state accounting estimates, Python peak allocations from `tracemalloc`, process RSS, eviction behavior, and cache-hit distributions against the declared thresholds; label these as separate metrics.
- [x] Step 2: Accept a runtime optimization only when it shows at least a 20% p95 non-provider latency improvement, or a 15% reduction in the named retained-state accounting estimate, or a separately justified reduction in `tracemalloc` peak allocation or process RSS, or removes a proven live duplicate path with unchanged correctness and no increase in equivalent model/tool calls. Do not describe retained-state accounting as peak memory.
- [x] Step 3: If the gate passes, implement one bounded change: source/view-local authority validity, one-time retained ownership weights, or a unified weighted/LRU policy; do not combine unrelated mechanisms in one patch. **Outcome:** deferred; no gate passed.
- [x] Step 4: Add regression tests for provenance, currentness, cross-source authority isolation, deterministic eviction, cleanup, and budget limits. **Outcome:** existing focused tests and Task 4 workload assertions cover these contracts; no runtime change required.
- [x] Step 5: Re-run the repaired benchmark and accept the change only when correctness remains verified and the targeted metric improves without increasing equivalent model/tool calls; otherwise record `DEFERRED` and explicitly defer any unmeasured lock/transaction-scope candidate. **Outcome:** `DEFERRED` for authority, retained-memory, eviction, and lock/transaction-scope changes.

**Verification:**
- [x] `python -m pytest -q tests/test_local_toolbelt.py tests/test_evidence_workflow.py`
- [ ] Re-run the Task 4 frozen benchmark and comparator when runtime code changes.
- Expected: either a recorded `DEFERRED` result with the measured reason, or a targeted improvement with unchanged correctness, provenance, currentness, cleanup, and budget evidence.

**Exit Criteria:**
- No speculative cache/authority architecture remains; every accepted change has a named before/after metric and focused regression proof.

### Task 7: Audit and remove only live compatibility duplication

**Purpose:**
- Remove redundant compatibility paths only after consumer inventory proves they are no longer part of the normal production path.

**Task Function:**
- Selective deletion and contract-preserving cleanup.

**Template Profile:**
- Executor: `lead controller`
- Selection basis: single-controller sequential execution owns the consumer inventory and deletion safety decision.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository-wide focused tests and source inventory validate cleanup.

**Specification Coverage:**
- One reuse decision per stage; no duplicate brief normalization, schema construction, or domain wrapper lifecycle when a canonical owner already serves the consumer.

**Required Skills:**
- `skill-refactoring-assessment`, `gitnexus-impact-analysis`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/workflow.py:_stage_cache_key`, `_committed_cache_output`, `run_recipe_async`
- Inspect: `src/foresight_os/domain/analysis_inputs.py:NormalizedIntent`, `normalize_work_brief`
- Inspect: `src/foresight_os/controller/policy.py`, `src/foresight_os/runtime/execution_gate.py`, and all `stage_cache` consumers
- Inspect: `src/foresight_os/analysis/result_committer.py:analysis_stage_result_schema`
- Verify: `tests/test_selective_reuse.py`, `tests/test_stage_inputs.py`, `tests/test_controller_selection.py`, `tests/test_result_committer.py`

**Dependencies:**
- Task 4 benchmark and Task 5 synthesis are complete; Task 6 has either completed with evidence or recorded a deferral.

**Authority:**
- Preauthorized local actions: inventory every candidate and record its consumers, canonical replacement owner, lifecycle, and compatibility status. Delete or translate a compatibility path only when a live duplicate is proven and the replacement owner is recorded; update focused tests and maintained documentation for any deletion.
- Stop for: an unbounded consumer inventory, a legacy path still used by persisted receipts or public inputs, or any need to change schema compatibility without migration evidence.

**Steps:**
- [x] Step 1: Mandatory inventory: enumerate `stage_cache` reads/writes, repeated `normalize_work_brief` calls, repeated schema construction, and wrapper constructors with symbol search plus impact evidence, even when no edit is expected.
- [x] Step 2: For each candidate, identify the canonical owner and prove equivalent lifecycle, identity, error, provenance, and invalidation behavior.
- [x] Step 3: Translate compatibility data once at the runtime boundary or remove only the proven-dead producer/consumer pair; preserve a bounded read path for persisted historical receipts when required. **Outcome:** no safe deletion or translation target identified.
- [x] Step 4: Run focused reuse, input, controller, and committer tests; record an explicit outcome for every candidate, including `stage_cache: retained — live compatibility consumer found`, `brief normalization: retained — distinct boundary consumers`, `schema construction: retained — preflight/runtime boundary consumers`, and `domain wrappers: deferred — migration cost exceeds demonstrated benefit`.

**Verification:**
- [x] `python -m pytest -q tests/test_selective_reuse.py tests/test_stage_inputs.py tests/test_controller_selection.py tests/test_result_committer.py`
- [x] `rg -n "stage_cache|normalize_work_brief|analysis_stage_result_schema" src tests evaluation`
- Expected: each remaining compatibility consumer has a named owner and test; deleted paths have no live references; equivalent accepted output has no increase in model/tool calls.

**Exit Criteria:**
- The inventory is complete; cleanup is limited to proven duplication, with no second registry, store, schema, receipt, or evidence format introduced; edits are optional when the audit proves a live consumer or migration cost makes retention safer.

### Task 8: Reconcile documentation and perform final verification

**Purpose:**
- Prove the final implementation against repository contracts and leave an auditable plan/evidence boundary.

**Task Function:**
- Final verification and evidence reconciliation.

**Template Profile:**
- Executor: `lead controller`
- Selection basis: single-controller sequential execution owns final proof coverage and repository-wide risk.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: `skill-verification-before-completion` owns final acceptance.

**Specification Coverage:**
- All mandatory correctness gates pass; measurement limitations and deferred work are truthful; no unrelated dirty artifacts enter the implementation branch.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all changed files from Tasks 2–7
- Modify: `evaluation/README.md` and this plan only when maintained guidance or durable task evidence changed
- Verify: `README.md`, `AGENTS.md`, `docs/architecture.md`, `docs/evidence-and-evaluation.md`, and `tests/test_markdown_links.py`

**Dependencies:**
- Tasks 1–7 complete or explicitly deferred with evidence.

**Authority:**
- Preauthorized local actions: run final commands, inspect the diff, update maintained documentation and plan evidence, and write external benchmark receipts.
- Stop for: any failed required check, stale task state, unrecorded scope change, unexpected generated artifact, or unresolved primary-checkout contamination.

**Steps:**
- [x] Step 1: Run the full test and compile suite from the dedicated worktree.
- [x] Step 2: Run the Markdown-link checks when documentation paths changed.
- [x] Step 3: Re-run the baseline/release benchmark comparison against identical fixture, environment, warmup, sample, and limit settings.
- [x] Step 4: Inspect `git diff --check`, changed-file list, and generated artifact exclusions; reconcile task evidence and deferrals in the plan.

**Verification:**
- [x] `python -m pytest -q` — passed: 100% completion, with the repository's expected skips.
- [x] `python -m compileall -q src tests evaluation` — passed.
- [x] `python -m pytest -q tests/test_markdown_links.py` — passed.
- [x] `git diff --check` — passed.
- [x] The Task 4 comparator against the final source tree and the exact regression reference at `27002c03b0c837ab8937b9c7e34a89bf35322b3f` — `gate: PASS`; post-race-fix p95 `+12.551%`, peak allocation `+0.010%`, RSS `+0.131%`, economics unchanged; local correctness `VERIFIED`, regression threshold `VERIFIED`, optimization demonstration `NOT_MEASURED` with the explicit limitation that this comparison is a regression gate.
- Expected: all required checks pass; benchmark statuses are truthful; raw receipts remain outside Git; the final diff contains only approved plan-lane files. **Observed:** satisfied; frozen harness digest `11c17bda3805d1bc0125adc2165eb2a90b8c83ff7cbe75c44528ac79911f5b0c`, implementation source-tree digest `87860fa26bb309a17d4b81c10d64287086dd9f459eb663c3f1382d9b1c336fe3`, and regression-reference source-tree digest `e20d5b3d5361c88467fe9fd1c94e50104423fd8227e7627d1de133568e7ec42c` were recorded in the external receipts under `$env:TEMP\foresight-os-next-pass`.

**Exit Criteria:**
- `skill-verification-before-completion` can return `verified` with no unresolved required task, failed required check, stale status, or unrecorded scope deviation.

## Verification

Final verification runs from the dedicated implementation worktree after all
mandatory tasks and any measurement-gated accepted changes:

- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `python -m pytest -q tests/test_markdown_links.py`
- `git diff --check`
- `$env:NEXT_PASS_ROOT = Join-Path $env:TEMP "foresight-os-next-pass"; $env:IMPLEMENTATION_WORKTREE = (Get-Location).Path; New-Item -ItemType Directory -Force -Path "$env:NEXT_PASS_ROOT\release"`
- `if (-not (Test-Path "$env:NEXT_PASS_ROOT\regression-worktree\.git")) { throw "run the Task 4 frozen-harness setup first" }`
- `Push-Location "$env:NEXT_PASS_ROOT\frozen-harness"; python evaluation/probes/run_optimization_probe.py --mode baseline --target-root "$env:NEXT_PASS_ROOT\regression-worktree" --harness-root "$env:NEXT_PASS_ROOT\frozen-harness" --fixture "$env:NEXT_PASS_ROOT\regression-worktree\tests\fixtures\analyst_multisheet.xlsx" --output "$env:NEXT_PASS_ROOT\release\regression-reference.json" --measurement-mode full; Pop-Location`
- `Push-Location "$env:NEXT_PASS_ROOT\frozen-harness"; python evaluation/probes/run_optimization_probe.py --mode release --target-root "$env:IMPLEMENTATION_WORKTREE" --harness-root "$env:NEXT_PASS_ROOT\frozen-harness" --fixture "$env:IMPLEMENTATION_WORKTREE\tests\fixtures\analyst_multisheet.xlsx" --output "$env:NEXT_PASS_ROOT\release\receipt.json" --measurement-mode full; Pop-Location`
- `Push-Location "$env:NEXT_PASS_ROOT\frozen-harness"; python evaluation/probes/compare_optimization_receipts.py --baseline "$env:NEXT_PASS_ROOT\release\regression-reference.json" --release "$env:NEXT_PASS_ROOT\release\receipt.json"; Pop-Location`
- `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- `git status --short`
- `git diff --name-only`
- `git diff --stat`
- `git diff --check`
- `source_tree_sha256` in each benchmark receipt matches the measured target tree

The benchmark must use the same fixture, Python executable, dependency set,
limits, warmups, measured sample count, and host conditions for baseline and
release. If a metric cannot be measured reliably, record `NOT_MEASURED` with a
concrete limitation; never convert an unavailable provider result into a local
workbook failure or claim optimization from a regression ceiling alone.

## Completion Criteria

The plan is ready for completion verification when:

1. The isolated worktree is based on `27002c03b0c837ab8937b9c7e34a89bf35322b3f` and the primary checkout's existing work is untouched.
2. Explicit Power BI mappings are exact-or-fail within the consuming table, while omitted mappings preserve compatibility behavior.
3. Oversized standalone workbooks are rejected before full capture, workflow-owned contexts always close, and caller-owned contexts remain caller-owned.
4. Cancellation before durable publication rolls back pending and accepted-file mutations and leaves no new cache or authority state; cancellation observed after the accepted commit is treated as a settled success rather than a post-commit failure.
5. Single-output synthesis is normalized once without weakening structural, dependency, provenance, or durable commit validation.
6. The repeated-investigation probe reuses one context and reports capture, parse, currentness, cache, retained-resource, correctness, threshold, and optimization evidence separately.
7. Authority, retained-memory, eviction, compatibility, and orchestration changes are either backed by named measurements and regressions or explicitly deferred.
8. The mandatory compatibility audit records every candidate and selective deletion removes no live consumer path or introduces a duplicate owner; safe retention is an accepted outcome.
9. Full tests, compile checks, link checks, diff checks, and the final source-tree-bound benchmark comparison pass or carry explicit truthful limitations.
10. This plan remains `proposed` until an approved execution flow activates it; completion status is not inferred from checked boxes.

## Self-Review

- Verdict coverage: table-local mappings are Task 2; publication cancellation and bounded capture are Task 3; shared-context benchmark repair is Task 4; single-output normalization and active cancellation are Task 5; conditional P1 optimization is Task 6; selective deletion is Task 7; reconciliation and full proof are Task 8.
- Repository alignment: all named post-PR owners exist on `origin/main@27002c03b0c837ab8937b9c7e34a89bf35322b3f`; the current dirty primary checkout is explicitly excluded from execution.
- Ownership: workbook input rules remain in `workbook_inputs.py`, runtime resource ownership remains in `local_toolbelt.py`, durable persistence remains in `analysis_store.py`, review validity remains in `review_workflow.py`, and benchmark truth remains in `evaluation/probes`.
- Gating: no authority, memory, cache, orchestration, or deletion refactor is mandatory without the Task 4 benchmark and relevant Task 5 evidence; failed evidence produces a recorded deferral.
- Verification: every task has exact files, symbols, dependencies, authority, task-local proof, and an observable exit condition; final commands are named and runnable from the dedicated worktree.
- Placeholder scan: no unresolved path, symbol, owner, command, or behavior placeholder is used. Benchmark output is anchored to the Windows `$env:TEMP\foresight-os-next-pass` directory outside the worktrees.
