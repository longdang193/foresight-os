---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: foresight-os-workbook-analysis-identity-and-cold-path
targets:
  - src/foresight_os/domain/analysis_inputs.py
  - src/foresight_os/analysis/workbook_inputs.py
  - src/foresight_os/analysis/workbook_engine.py
  - src/foresight_os/analysis/workbook_runner.py
  - src/foresight_os/analysis/workbook_registry.py
  - src/foresight_os/analysis/review_core.py
  - src/foresight_os/analysis/reviewer.py
  - src/foresight_os/analysis/review_workflow.py
  - src/foresight_os/analysis/portfolio_resilience.py
  - src/foresight_os/analysis/supplier_resilience.py
  - src/foresight_os/analysis/ev_capacity_investment.py
  - src/foresight_os/analysis/technology_radar.py
  - src/foresight_os/analysis/powerbi_strategic_portfolio.py
  - src/foresight_os/persistence/analysis_store.py
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/runtime/execution_gate.py
  - src/foresight_os/runtime/executors.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/runtime/agent_workflow.py
  - src/foresight_os/controller/policy.py
  - src/foresight_os/controller/recipes.py
  - src/foresight_os/cli.py
  - src/foresight_os/schemas/execution_recipe.schema.json
  - pyproject.toml
  - evaluation/probes/optimization_measurement.py
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/compare_optimization_receipts.py
  - tests/
  - docs/architecture.md
  - README.md
---

# Workbook Analysis Identity And Cold Path

## Goal

Make workbook-consuming execution correct and source-bound before changing the
measured XLSX hot path. Then remove only duplicate cold-path work that survives
matched correctness and performance evidence. Preserve the existing durable
analytical owner and lifecycle boundaries:

```text
approved brief
  -> resolve exact (stage_id, domain) contract
  -> apply domain defaults once
  -> capture one immutable workbook snapshot
  -> resolve layout
  -> build scoped material
  -> run material-only analyzer
  -> canonical commit/review
  -> source-bound stage receipt
  -> optional artifact rendering
```

The execution base is `origin/main` at
`958439893142d213889b4147d18d80ee83fafa23`. The current primary checkout is
dirty and must remain untouched; execution uses a new dedicated worktree from
that base.

## Review Of The Recommendation

The recommendation is implementation-ready after narrowing its ownership and
evidence boundaries. The following findings are justified by current repository
state.

### [P1] Workbook source is not part of receipt reuse identity

`StageReceipt` stores `source_revision`, but `reusable_for()` does not compare it
and `_stage_fingerprints()` does not include the current workbook SHA. Changing a
workbook in place can therefore reuse a committed result with a matching logical
input fingerprint. The fix applies only to workbook-consuming stages; non-workbook
stages remain source-neutral.

### [P1] Runtime contract lookup is domain-only

`ExecutionGate.execute()` builds `analysis_contracts` keyed by domain, while a
recipe can contain stage-scoped contracts for the same domain. The deterministic
executor then reads `contracts[domain]`. This can select the wrong contract even
when receipt fingerprints distinguish stage scope. One resolver must own exact
stage lookup, global fallback, duplicate detection, and fail-closed behavior.

### [P1] Defaults are applied after layout/material decisions

`WorkbookAnalysisEngine` and `WorkbookLayoutSpec` receive the declared contract,
while the five material adapters still call `merge_input_contract()` later.
Required tables, selection, and scope can therefore differ between direct API and
approved execution. Default resolution must precede layout and materialization;
the compatibility merge helper may remain as a wrapper around that resolver.

### [P1] Period parsing has two interpretations

`AnalysisInputContract._parse_period()` treats a standalone month as ending in
December, and workbook material matching has a separate interval parser. A
request for `2026-01` can therefore include rows outside January. One parser must
define validation and material matching. The safe rule is full containment: a row
interval must be contained by the requested interval; a coarse row such as `2026`
does not satisfy a fine request such as `2026-01`.

### [P2] Cold-path and duplicate-work evidence is incomplete

The existing optimization comparator gates aggregate XLSX p95 and general pattern
latency, but does not independently gate first-run/cold workbook behavior. The
reported cold regression can be hidden by an aggregate result. Capture/hash counts,
openpyxl load count, selected versus scanned material, materialization, persistence,
and reuse cases need separate evidence before optimization claims are accepted.

### [P2] Dependency and configuration cleanup is valid but not a latency fix

Analyzer dispatch, defaults, and analyzer versions are scattered. Deterministic
review imports also pass through `agent_framework`, while `pyproject.toml` still
declares `pandas` although repository source search finds no runtime import. These
are maintainability and packaging concerns. They stay separate from XLSX latency
claims and require an installation smoke test.

## Preserved Invariants And Non-Goals

- `AnalysisState` and `AnalysisStore` remain the only durable analytical state owners.
- `WorkbookContext` remains the only run-owned source snapshot/read-cache owner.
- After bounded capture, the immutable `SourceSnapshot` is authoritative for the
  in-flight run; filesystem changes affect only the next execution.
- `StageReceipt` remains the only durable recipe-reuse authority.
- `WorkbookAnalysisEngine` remains the shared deterministic composition path.
- Domain functions retain business calculations; they do not acquire orchestration responsibilities.
- Accepted analytical state remains accepted when artifact rendering fails.
- Existing public analyzer signatures and CSV compatibility remain until parity proof permits a separate removal.
- No new global cache, reuse database, parser abstraction, process isolation layer, analytical store, or provenance representation is introduced.
- Performance work does not weaken locks, pending-token freshness, revision protection, canonical validation, review, invalidation, or atomic writes.

## Implementation Outcomes

1. Workbook stage receipts cannot be reused across changed source bytes, while
   unchanged source bytes remain reusable.
2. Every deterministic stage resolves exactly one contract using stage scope first,
   then an unambiguous global-domain fallback; missing or ambiguous bindings fail closed.
3. Defaults and period semantics are applied once before selection/materialization.
4. Admission and execution share one immutable `SourceSnapshot` captured with the
   approved byte limit and cancellation callback, without persisting a second
   workbook catalog or holding the persistence lock during expensive I/O.
5. Direct analyzers, standalone workflows, CLI execution, and approved runtime use
   the same material-only calculation path and preserve artifact outcomes.
6. Cancellation reaches the bounded workbook worker and expensive material/domain
   loops without publishing half-settled state.
7. XLSX cold-path optimization is accepted only after a behavior-neutral,
   workload-specific baseline establishes separate correctness, resource, cold,
   warm, source-change, scope-change, reuse, and history evidence plus an
   empirical cold noise floor.
8. Configuration and deterministic review imports have one canonical maintenance
   owner; any dependency removal is proven by isolated installation and local-path tests.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-test-driven-development`, `skill-backend-verification`, `skill-systematic-debugging`, `skill-performance-optimization`, `skill-verification-before-completion`.
- Isolation: new dedicated worktree from `origin/main` at the base SHA above; do not copy dirty files from the primary checkout.
- Commit policy: one verified commit per bounded change set; no commit before its task-local proof passes.
- Preauthorized local actions: inspect source and tests, create the declared dedicated worktree, edit owned files, run named local checks and probes, and retain task-owned evidence outside the committed source diff.
- User-approval actions: push, merge, publication, external writes, destructive recovery, discard, and cleanup.
- Parallel ownership: none; Tasks 2, 3A, 3B, 3C, 4, 5, 6, and 7 serialize shared owners, with Task 8 as the fan-in barrier.
- Sequential fallback: execute Tasks 1, 2, 3A, 3B, 3C, 4, 5, 6, 7, and 8 in order.
- Stop conditions: source or contract ambiguity, failed parity, changed base, missing fixture, failed resource guard, persistence invariant regression, or any need for an unapproved behavioral choice.
- Proposed branch: `codex/foresight-os-workbook-analysis-identity-cold-path`.

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/foresight-os-workbook-analysis-identity-cold-path`
- Base commit: `958439893142d213889b4147d18d80ee83fafa23`
- Expected workspace: clean dedicated worktree; unrelated dirty primary-checkout changes preserved and excluded
- Next action: hand off the verified worktree to the explicitly authorized Git disposition
- Blockers: none

## Task Breakdown

| Task | State | Owner | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- |
| 1 | `completed` | lead | none | clean dedicated worktree and baseline receipts | `work/optimization-baseline/baseline-receipt.json`; pytest, isolated compile, Markdown links, and baseline probe verified |
| 2 | `completed` | lead | 1 | source-aware identity, contract resolution, and period tests pass | `PYTHONPATH=src python -m pytest -q tests/test_analysis_input_contract.py tests/test_selective_reuse.py tests/test_workbook_engine.py tests/test_runtime_boundaries.py tests/test_execution_gate.py` passed: 119 tests; isolated `python -m compileall -q src tests evaluation` passed |
| 3A | `completed` | lead | 2 | one authoritative snapshot and safe lock ownership | `PYTHONPATH=src python -m pytest -q tests/test_local_toolbelt.py tests/test_execution_gate.py` passed: 90 tests; source mutation, adopted snapshot, capture limits, cancellation, and lock-scope proof included |
| 3B | `completed` | lead | 3A | public/runtime/CLI path parity | `PYTHONPATH=src python -m pytest -q tests/test_workbook_path_parity.py tests/test_analysis_input_contract.py tests/test_supplier_and_ev_resilience.py tests/test_technology_powerbi_validator.py tests/test_brief_portability.py tests/test_workbook_engine.py tests/test_workbook_runner.py` passed; direct, standalone, CLI, and deterministic approved-runtime parity covered |
| 3C | `completed` | lead | 3B | cancellation settlement and artifact retry behavior | `PYTHONPATH=src python -m pytest -q tests/test_workbook_runner.py tests/test_workbook_path_parity.py tests/test_cli.py tests/test_runtime_boundaries.py tests/test_local_toolbelt.py` passed; cancellation, artifact failure independence, CLI artifact fields, and retry-only rendering covered |
| 4 | `completed` | lead | 1-3C | behavior-neutral instrumentation and workload gates | `work/optimization-baseline/instrumented-baseline-receipt.json`; focused instrumentation/comparator tests and release probe verified; matched base comparison marked reader instrumentation unavailable on the uninstrumented base |
| 5 | `deferred` | lead | 1-4 | measured candidate optimizations pass matched gates | no XLSX reader candidate retained; baseline evidence is behavior/performance proof only and candidate optimization remains deferred |
| 6 | `completed` | lead | 2, 3B | registry and analyzer-version tests pass | `tests/test_workbook_registry.py` plus contract/runtime boundary suites pass; lazy registry owns defaults, dispatch, and versions |
| 7 | `completed` | lead | 3B, 3C | local review imports work without external provider initialization | `tests/test_review_hardening.py` subprocess import proof passes; provider dependency/package removal intentionally deferred |
| 8 | `completed` | lead | 2-7 | full verification and documentation reconciliation pass | `python -m pytest -q`, `python -m compileall -q src tests evaluation`, the tracked Markdown-link checker, and `git diff --check` passed; focused anomaly-probe tests passed without changing the preserved receipt hash; Task 5 remains explicitly deferred and the retained optimization receipts remain outside the source implementation diff |

## Task Details

### Task 1: Establish the current-base baseline and change map

**Purpose:** Freeze a reproducible baseline before changing identity or performance behavior.
**Task Function:** repository inspection, baseline measurement, and plan handoff.
**Template Profile:** Controller-selected: `none (lead controller)`; Selection basis: inline sequential execution keeps this read-only baseline with the lead controller.
**Specification Coverage:** base selection, preserved dirty-work requirement, matched workload evidence.
**Required Skills:** `skill-executing-plans`, `skill-verification-before-completion`, `skill-performance-optimization`.
**Files And Symbols:** `evaluation/probes/optimization_measurement.py`, `evaluation/probes/run_optimization_probe.py`, `evaluation/probes/compare_optimization_receipts.py`; current `StageReceipt`, `NormalizedIntent.contract_for_domain()`, `ExecutionGate`, `DeterministicLocalExecutor`, `WorkbookContext`, `WorkbookAnalysisEngine`.
**Dependencies:** none.
**Authority:**
- Preauthorized local actions: fetch and verify the pinned base, create the dedicated worktree, run baseline commands, and write task-owned receipts outside the committed source diff.
- Stop for: base drift, missing fixture, failed baseline checks, or any request to modify the dirty primary checkout or delete existing work artifacts.
**Steps:**
1. Run `git fetch origin main`, assert that `git rev-parse origin/main` equals `958439893142d213889b4147d18d80ee83fafa23`, then create the dedicated worktree and record its path, branch, and base SHA in coordination state.
2. Run `python -m pytest -q`, `python -m compileall -q src tests evaluation`, `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/getting-started.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`, and `git diff --check`.
3. Run the existing optimization probe in baseline mode against `tests/fixtures/analyst_multisheet.xlsx` and retain the receipt outside the committed source diff.
4. Record current capture/hash/load counters, cold, warm, changed-source, changed-scope, reuse, persistence, and growing-history measurements; identify which counters do not yet exist before implementation.
**Verification:** all baseline commands pass; the receipt records fixture SHA, commit SHA, environment, sample counts, and separate workload labels.
**Exit Criteria:** the dedicated worktree is clean, the baseline is reproducible, and no optimization change begins without a named before/after metric.

### Task 2: Make workbook identity and contract resolution authoritative

**Purpose:** Prevent stale or cross-stage workbook reuse and ensure one effective contract controls selection, materialization, execution, and fingerprints.
**Task Function:** canonical contract/identity implementation with focused regression proof.
**Template Profile:** Controller-selected: `none (lead controller)`; Selection basis: canonical identity work is tightly coupled and remains with the lead controller.
**Specification Coverage:** P1 source identity, stage/domain lookup, defaults, and period semantics.
**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-systematic-debugging`.
**Files And Symbols:** `src/foresight_os/persistence/analysis_store.py:StageReceipt.reusable_for`; `src/foresight_os/runtime/workflow.py:_stage_fingerprints`; `src/foresight_os/runtime/execution_gate.py:ExecutionGate`; `src/foresight_os/runtime/executors.py:DeterministicLocalExecutor`; `src/foresight_os/domain/analysis_inputs.py:NormalizedIntent.contract_for_domain`, `_parse_period`, `AnalysisInputContract`; `src/foresight_os/analysis/workbook_inputs.py:WorkbookLayoutSpec`, `_period_interval`, `_scope_matches`; `src/foresight_os/analysis/workbook_engine.py:WorkbookAnalysisEngine`; five domain adapters; `tests/test_selective_reuse.py`, `tests/test_execution_gate.py`, `tests/test_analysis_input_contract.py`, `tests/test_workbook_engine.py`.
**Dependencies:** Task 1.
**Authority:**
- Preauthorized local actions: edit canonical contract, receipt, runtime lookup, and focused test owners; run focused correctness checks.
- Stop for: unresolved contract semantics, persistence-protocol changes, new cache/registry/store proposals, or failed source/contract parity.
**Steps:**
1. Add the current workbook SHA to the workbook-stage semantic fingerprint and as an explicit `reusable_for()` input; compare it only for stages declaring `analysis_domains` and keep non-workbook receipts source-neutral.
 2. Define one resolver on `NormalizedIntent` for `(stage_id, domain)` that returns an exact stage contract, then one unambiguous global-domain contract, and raises a validation error for duplicate candidates or missing deterministic bindings. Domain defaults complete a declared binding; they never manufacture a missing stage binding.
3. Pass a stage-qualified contract map or resolver into `ExecutionGate`, `run_recipe_async`, and `DeterministicLocalExecutor`; remove domain-only lookup from the execution path while preserving serialized recipe compatibility.
 4. Add `resolve_workbook_contract(domain, declared_contract)` at the workbook input owner. It merges defaults once, validates the resolved contract, and becomes the input to layout, materialization, analyzer execution, and receipt identity. Preserve partial-contract compatibility, including the distinction between omitted `required_tables` and an explicit empty requirement. Keep `merge_input_contract()` as a compatibility wrapper only.
 5. Make `_parse_period()` the only period parser. Support year, month, quarter, and ranged forms such as `2026`, `2026-01`, `2026-Q1`, `2025-01:2026-03`, and `2025-Q4:2026-Q2`; normalize each to inclusive month endpoints, use full interval containment for row matching, and reject coarse row labels for fine-grained requests.
 6. Add tests for same-path source mutation, unchanged-source reuse, two stages using one domain with different contracts, stage-over-global precedence, duplicate/missing fail-closed bindings, partial contracts including omitted versus empty `required_tables`, and all supported period forms.
**Verification:** focused tests pass; a changed workbook byte produces a fresh stage; unchanged bytes reuse; direct and approved paths report the same effective contract fingerprint and selected rows.
**Exit Criteria:** no workbook receipt can reuse a result from a different source SHA or stage contract, and no late adapter merge remains authoritative.

### Task 3A: Make snapshot and lock ownership authoritative

**Purpose:** Remove duplicate source capture without weakening approval, revision, or persistence invariants.
**Task Function:** run-boundary ownership refactor with source and lock regression proof.
**Template Profile:** Controller-selected: `none (lead controller)`; Selection basis: snapshot ownership and lock semantics are high-risk shared runtime changes.
**Specification Coverage:** P1 single snapshot, source authority, cancellation-aware bounded capture, and lock scope.
**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-systematic-debugging`.
**Files And Symbols:** `src/foresight_os/runtime/execution_gate.py:_preflight_recipe`, `ExecutionGate`; `src/foresight_os/runtime/local_toolbelt.py:SourceSnapshot`, `WorkbookContext.read`, `spreadsheet_read`; `src/foresight_os/persistence/analysis_store.py`; snapshot, execution-gate, and persistence tests.
**Dependencies:** Task 2.
**Authority:**
- Preauthorized local actions: edit snapshot capture, workbook-context consumption, lock scope, and focused boundary tests.
- Stop for: any need to weaken approval projection, recipe/brief identity, revision checks, pending/commit transitions, borrowed-context ownership, or resource/cancellation limits.
**Steps:**
1. Fetch and assert the pinned base before creating the worktree if Task 1 did not already complete that check.
2. Capture one immutable `SourceSnapshot` after the small approval/store identity check using the approved workbook byte limit and cancellation callback; carry it in the run-owned context, and make `WorkbookContext.read()` consume it without recapturing the same source.
3. Treat the captured snapshot as authoritative for all reads, calculations, provenance, fingerprints, and receipt identity. Do not re-read or re-hash the source path before dispatch or commit; filesystem mutation after capture affects only the next execution.
4. Move expensive capture/preflight outside the persistence lock while retaining approval projection, recipe fingerprint, brief investigation id, revision checks, and pending/commit safeguards.
5. Add source-mutation, capture-count, resource-limit, cancellation, and lock-scope tests.
**Verification:** source capture/load counters show one run-owned snapshot; source mutation after capture does not change the in-flight result; oversized/cancelled capture fails before materialization; persistence invariants remain unchanged.
**Exit Criteria:** one bounded snapshot is the sole source authority for a run, and persistence locks do not cover expensive workbook I/O.

### Task 3B: Converge public and approved workbook paths

**Purpose:** Make direct APIs, standalone workflows, CLI execution, and approved runtime use the same material-only engine path.
**Task Function:** compatibility-wrapper convergence with calculation and provenance parity proof.
**Template Profile:** Controller-selected: `none (lead controller)`; Selection basis: the public-path refactor has broad consumers and requires a single coordinating owner.
**Specification Coverage:** direct wrapper parity, shared engine ownership, and preserved public signatures.
**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`.
**Files And Symbols:** `src/foresight_os/runtime/executors.py:DeterministicLocalExecutor`; `src/foresight_os/runtime/workflow.py:run_recipe_async`; `src/foresight_os/analysis/workbook_engine.py:WorkbookAnalysisEngine.run`; `src/foresight_os/analysis/workbook_runner.py:WorkbookWorkflowRunner`; five domain public analyzers and `_analyze_*_material`; `src/foresight_os/cli.py`; corresponding analyzer, runner, execution, and runtime-boundary tests.
**Dependencies:** Task 3A.
**Authority:**
- Preauthorized local actions: edit public analyzer adapters, shared engine dispatch, runner/executor wiring, CLI compatibility output, and parity tests.
- Stop for: changed public signatures, duplicated business-calculation ownership, divergent selection/provenance, or failed direct/runtime/CLI parity.
**Steps:**
1. Refactor each public analyzer to resolve the effective contract, invoke the shared engine, and delegate business calculations to its material-only function.
2. Pass the run-owned snapshot and resolved contract through standalone workflow, deterministic executor, and approved runtime paths.
3. Keep legacy signatures and CSV compatibility as wrappers until parity tests pass.
4. Add equivalent selection, failure, provenance, and calculation assertions across direct API, standalone workflow, CLI, and approved runtime.
**Verification:** all four entry-point families produce equivalent selections, calculations, failure statuses, and provenance for the same fixture and contract.
**Exit Criteria:** the shared engine is the only workbook composition path and compatibility wrappers add no alternate analysis logic.

### Task 3C: Complete cancellation and artifact lifecycle behavior

**Purpose:** Preserve truthful lifecycle settlement when cancellation or artifact rendering fails.
**Task Function:** lifecycle boundary hardening with failure and retry proof.
**Template Profile:** Controller-selected: `none (lead controller)`; Selection basis: lifecycle and artifact state changes must remain serialized with the lead controller.
**Specification Coverage:** cancellation settlement, artifact independence, and retry rendering.
**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-systematic-debugging`.
**Files And Symbols:** `src/foresight_os/runtime/workflow.py:run_recipe_async`; `src/foresight_os/analysis/workbook_runner.py:WorkbookWorkflowRunner`; `src/foresight_os/cli.py`; analysis, artifact, execution, and runtime-boundary tests.
**Dependencies:** Task 3B.
**Authority:**
- Preauthorized local actions: edit cancellation checkpoints, compatibility result fields, CLI JSON, retry-render behavior, and focused lifecycle tests.
- Stop for: pending or committed half-results, lost cancellation, accepted-state mutation after renderer failure, or any new durable artifact/provenance owner.
**Steps:**
1. Propagate the existing cancellation callback through selected extraction, material predicate evaluation, domain loops, evidence/state construction, and pre-persistence checks; wait for the bounded worker before reporting settlement.
2. Extend compatibility workflow results and CLI JSON with `artifact_status` and `artifact_error`; keep accepted analytical state accepted when rendering fails.
3. Add retry-render over the accepted revision without rerunning workbook analysis or review, and prove it with call-count assertions.
**Verification:** cancellation leaves no pending or committed half-result; renderer failure preserves accepted state; retry avoids analysis/review calls and reports artifact outcome truthfully.
**Exit Criteria:** lifecycle and artifact outcomes remain truthful across cancellation, render failure, and retry.

### Task 4: Establish behavior-neutral instrumentation and workload gates

**Purpose:** Create the measurement system and instrumented baseline before changing XLSX behavior.
**Task Function:** benchmark schema, instrumentation, and acceptance-gate design.
**Template Profile:** Controller-selected: `none (lead controller)`; Selection basis: performance evidence must be owned by the same controller that accepts or defers candidates.
**Specification Coverage:** P1 workload-specific gates, cold-regression detection, and P2 persistence evidence.
**Required Skills:** `skill-performance-optimization`, `skill-test-driven-development`, `skill-backend-verification`.
**Files And Symbols:** `evaluation/probes/optimization_measurement.py`, `evaluation/probes/run_optimization_probe.py`, `evaluation/probes/compare_optimization_receipts.py`, `tests/test_optimization_measurement.py`, `src/foresight_os/runtime/local_toolbelt.py:WorkbookStats`, `src/foresight_os/persistence/analysis_store.py`.
**Dependencies:** Tasks 1-3C.
**Authority:**
- Preauthorized local actions: add behavior-neutral counters, workload definitions, comparator logic, persistence timing, and measurement tests.
- Stop for: instrumentation that changes XLSX behavior, non-comparable fixtures/environments, missing repeated-cold samples, or any acceptance rule that weakens correctness/resource gates.
**Steps:**
1. Extend the workload schema with named cold-first-run, warm same-view, changed-brief/scope, changed-source, analyst-validator reuse, repeated-investigation, and growing-history cases.
2. Add counters for archive sheets scanned, selected sheets/cells, openpyxl loads, formula detection, capture/hash count, materialized rows, materialization time, and persistence bytes/time without changing behavior.
3. Instrument persistence transitions separately: load accepted state, merge, validate, serialize/write pending, attach review, commit, serialize/write committed state, and record receipt.
4. Capture an instrumentation-only baseline with identical fixture SHA, environment metadata, workload definitions, and at least ten process-cold samples; report p50/p95 and dispersion, and derive an empirical noise floor before evaluating candidates.
5. Define independent gates for correctness/resource status, cold p95, warm/reuse latency, selected/scanned material, openpyxl load count, capture/hash count, and persistence bytes/time. A cold regression is material when relative delta exceeds 20% and absolute delta exceeds the measured noise floor; if the noise floor cannot be estimated reliably, the candidate result is `not_measured` and cannot be accepted.
6. Add comparator tests for mismatched workloads, cold regressions hidden by aggregate p95, source-change reuse, unstable repeats, and growing-history results.
**Verification:** the instrumentation-only baseline is behavior-identical, receipts contain separate workload labels and counters, and the comparator reports correctness, resource, cold, warm, reuse, and persistence evidence independently.
**Exit Criteria:** no behavioral optimization begins until the workload gates and empirical cold noise floor are recorded in a reproducible baseline receipt.

### Task 5: Optimize the measured XLSX cold path one candidate at a time

**Purpose:** Remove only duplicate XLSX work that survives matched correctness, resource, and workload-specific performance evidence.
**Task Function:** bounded local-reader optimization with candidate-level retain/revert decisions.
**Template Profile:** Controller-selected: `none (lead controller)`; Selection basis: each candidate changes a shared reader path and needs controlled sequential comparison.
**Specification Coverage:** P1 cold-path optimization and P2 materialization efficiency.
**Required Skills:** `skill-performance-optimization`, `skill-test-driven-development`, `skill-backend-verification`.
**Files And Symbols:** `src/foresight_os/runtime/local_toolbelt.py:_preflight_xlsx_archive`, `spreadsheet_read`, `WorkbookStats`, `TypedTable`; `src/foresight_os/analysis/workbook_inputs.py:build_material_view`; `tests/test_local_toolbelt.py`, `tests/test_workbook_engine.py`; `evaluation/probes/`.
**Dependencies:** Task 4.
**Authority:**
- Preauthorized local actions: edit XLSX reader/materialization code, add focused resource/formula tests, run one-candidate matched probes, and retain or revert candidates based on the declared gates.
- Stop for: changed parser semantics, weakened archive/row/cell/merged limits, formula or cached-value drift, provenance changes, cancellation regressions, or a candidate that does not improve its named workload without a correctness tradeoff.
**Steps:**
1. Apply candidate A: return selection-aware preflight facts from `_preflight_xlsx_archive`, preserve whole-archive safety limits, and count selected rows/cells for material limits while skipping unrelated sheets for selected-material accounting; measure and retain or revert.
2. Apply candidate B: detect formulas only in selected material and skip the `data_only=True` load only when selected material is formula-free; retain both workbook views for formula-bearing selections; measure and retain or revert.
3. Apply candidate C only if the preceding evidence identifies materialization as a material cost: compile a table-scoped predicate containing normalized columns, allowed entity/scenario/unit sets, parsed period intervals, and required-dimension policy; measure and retain or defer.
4. For every candidate, run the focused fixture/resource/formula/provenance tests and the matched baseline/release comparator before accepting the change. Do not require candidate C merely because it appears locally efficient.
5. Remove a duplicate persistence read/serialization only if Task 4 evidence proves it is dominant on growing history and focused tests show identical revision, token, invalidation, review, provenance, and atomic-write behavior; otherwise record the deferral without changing the protocol.
**Verification:** all existing XLSX fixtures retain identical canonical results, evidence, hashes, and failure statuses; resource limits fail closed; each retained candidate has a passing cold/warm/reuse/resource gate and a recorded before/after receipt.
**Exit Criteria:** only measured candidates remain implemented; candidates without evidence remain unimplemented and are recorded as deferrals.

### Task 6: Consolidate workbook domain configuration and analyzer identity

**Purpose:** Give defaults, analyzer dispatch, and explicit analyzer versions one canonical owner without adding orchestration.
**Task Function:** static registry consolidation and identity tests.
**Template Profile:** Controller-selected: `none (lead controller)`; Selection basis: static configuration ownership is lower risk but still touches shared dispatch and identity consumers.
**Specification Coverage:** P2 configuration maintenance and analyzer-version discipline.
**Required Skills:** `skill-code-standards`, `skill-test-driven-development`.
**Files And Symbols:** new `src/foresight_os/analysis/workbook_registry.py`; `src/foresight_os/analysis/workbook_inputs.py:default_workbook_contract`, `workbook_analyzer_version`, `workbook_analyzer_fingerprint`; `src/foresight_os/runtime/executors.py:_default_workbook_analyzers`; five domain adapters; `tests/test_workbook_registry.py`, `tests/test_selective_reuse.py`.
**Dependencies:** Tasks 2 and 3B.
**Authority:**
- Preauthorized local actions: edit static workbook registry metadata, analyzer lookup/version wiring, and focused configuration tests.
- Stop for: business-calculation moves, eager provider imports, a second lifecycle owner, or registry behavior that changes compatibility APIs without proof.
**Steps:**
1. Define `DomainWorkbookSpec` with domain, default-contract factory, lazy analyzer module/symbol resolver, and explicit analyzer version; register all five supported domains once without importing every analyzer at registry import time.
2. Make default resolution, analyzer lookup, and analyzer fingerprints delegate to the registry; remove duplicated analyzer maps and `_WORKBOOK_ANALYZER_VERSIONS` ownership.
3. Resolve the analyzer callable only when dispatch occurs, and keep the registry free of eager imports and plugin behavior.
4. Add tests for complete domain coverage, unknown-domain failure, stable version fingerprints, analyzer lookup, and receipt invalidation when the explicit version changes.
5. Document the release rule that a behavior-changing analyzer edit requires an explicit registry version bump; do not hash Python source at runtime.
**Verification:** all five analyzers resolve through one registry, compatibility APIs remain stable, and direct/local execution does not import external providers merely to inspect workbook metadata.
**Exit Criteria:** defaults, dispatch, and analyzer identity have one canonical configuration owner.

### Task 7: Isolate deterministic review and local execution from provider imports

**Purpose:** Make provider-free local analysis dependency-isolated without changing agent-assisted behavior.
**Task Function:** import-boundary refactor and packaging smoke proof.
**Template Profile:** Controller-selected: `none (lead controller)`; Selection basis: packaging and import-boundary changes require one owner for compatibility and dependency evidence.
**Specification Coverage:** P2 dependency isolation and maintenance separation.
**Required Skills:** `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`.
**Files And Symbols:** new `src/foresight_os/analysis/review_core.py`; new `src/foresight_os/runtime/agent_workflow.py`; `src/foresight_os/analysis/reviewer.py`, `src/foresight_os/analysis/review_workflow.py`, `src/foresight_os/analysis/evidence_workflow.py`, `src/foresight_os/runtime/workflow.py`, `src/foresight_os/runtime/executors.py`, `src/foresight_os/runtime/capabilities.py`, `src/foresight_os/runtime/participants.py`, `pyproject.toml`; import-boundary tests.
**Dependencies:** Tasks 3B and 3C.
**Authority:**
- Preauthorized local actions: edit deterministic review facades, provider-boundary imports, packaging metadata, and isolated import/installation tests.
- Stop for: changed public reviewer imports, provider-enabled regressions, unproven dependency removal, or any credential/external-write requirement.
**Steps:**
1. Move `ReviewResult`, objection parsing, deterministic review policies, and pure review helpers into `analysis/review_core.py` with no `agent_framework` import.
2. Keep `analysis/reviewer.py` and `review_workflow.py` as compatibility facades while moving skill/provider execution to an agent-boundary module.
3. Move or lazily import `agent_framework` workflow builders, middleware, and provider-specific types so importing deterministic workbook/review primitives does not initialize external providers.
4. Build an isolated wheel/import smoke environment and run local XLSX/review tests without provider initialization; separately run provider-enabled tests with `agent-framework` installed.
5. After deterministic imports pass, evaluate moving `agent-framework` to an `agents`/provider extra. Make that packaging change only if CLI/API compatibility and provider-enabled installation tests pass; otherwise retain it as a core dependency and record the import-boundary improvement only.
6. Search source and dynamic import paths for `pandas`. Remove it from core dependencies only if isolated packaging and supported local analysis tests pass without it; otherwise retain it and record the exact consumer or packaging constraint.
**Verification:** local import and execution succeed without provider initialization; provider-enabled tests retain current behavior; `agent-framework` is either proven optional or explicitly retained; dependency changes are reported as maintenance evidence, not XLSX latency evidence.
**Exit Criteria:** deterministic and agent-assisted boundaries are explicit, and dependency changes are either proven or explicitly deferred.

### Task 8: Reconcile documentation and perform final verification

**Purpose:** Prove all outcomes together and leave a recoverable plan state.
**Task Function:** final integration verification, documentation update, and handoff.
**Template Profile:** Controller-selected: `none (lead controller)`; Selection basis: final verification and plan-state reconciliation remain lead-controller responsibilities.
**Specification Coverage:** all implementation outcomes, preserved invariants, and explicit deferrals.
**Required Skills:** `skill-verification-before-completion`, `skill-plan-document-reviewer`, `skill-backend-verification`.
**Files And Symbols:** `docs/architecture.md`, `README.md`, this plan, all focused tests and evaluation receipts.
**Dependencies:** Tasks 2-7.
**Authority:**
- Preauthorized local actions: update maintained documentation, run final checks and matched probes, inspect Git/worktree state, and record truthful evidence.
- Stop for: undocumented behavior, failed required checks, stale base/head evidence, copied disposable artifacts, or any request to mark the plan completed without verification.
**Steps:**
1. Update architecture and maintained guidance to describe source-bound receipt reuse, exact stage/domain resolution, one snapshot path, artifact independence, and separate performance gates.
2. Run `python -m pytest -q`, `python -m compileall -q src tests evaluation`, `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/getting-started.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`, and `git diff --check`.
3. Run matched baseline/release probes for cold, warm, source-change, scope-change, reuse, and growing-history cases; compare with `evaluation/probes/compare_optimization_receipts.py`.
4. Inspect `git diff --stat`, `git diff --name-status`, generated-surface changes, and `git status --short --branch`; confirm no primary-checkout files or disposable artifacts were copied into the branch. Retain the tracked anomaly receipt as probe evidence: its runtime memory counters vary between valid runs, and the confirmed overwrite cause was the CLI test's default tracked output path, now isolated under `tmp_path`.
5. Record verified outcomes, retained deferrals, residual risks, and exact base/head SHAs; set plan status `completed` after `skill-verification-before-completion` returns `verified`.
**Verification:** all commands and matched gates pass, or each failed/blocked dimension is truthfully recorded as `FAILED`, `BLOCKED_INPUT`, `BLOCKED_EXTERNAL`, or `not_measured`.
**Exit Criteria:** a fresh verification handoff can prove every implementation outcome from the plan and Git state alone.

## Verification

Structural proof and performance proof remain separate:

- Focused correctness proof covers source mutation, unchanged-source reuse,
  stage-specific contracts, defaults, year/month/quarter/ranged period
  containment, direct/runtime/CLI parity, cancellation settlement, artifact
  failure, and retry rendering.
- Backend boundary proof covers admission, workbook read, materialization,
  canonical commit/review, receipt reuse, and failure/blocked paths.
- Resource proof covers archive safety, selected-material limits, formula/cached
  values, hidden rows, provenance, and cancellation.
- Performance proof uses identical fixture SHA, environment, sample counts, and
  workload definitions for baseline/release; cold, warm, changed-source,
  changed-scope, reuse, and growth gates are reported independently. Cold
  acceptance uses repeated process-cold samples and an empirical noise floor;
  a candidate is not accepted when that floor is not measurable.
- Final repository proof runs the full test suite, compile check, Markdown-link
  checker, diff check, and clean dedicated-worktree inspection.

## Completion Criteria

The plan is ready for completion verification when:

1. source-bound receipt reuse, exact stage/domain contract resolution, default
   timing, and canonical period parsing are implemented and focused tests pass;
2. Tasks 3A-3C prove one authoritative snapshot, public/runtime/CLI parity,
   truthful cancellation settlement, artifact failure independence, and retry
   rendering without repeated analysis;
3. Task 4 records a behavior-neutral baseline with workload-specific gates and
   an empirical cold noise floor before Task 5 accepts any reader optimization;
4. every retained optimization has matched correctness, resource, cold, warm,
   reuse, and history evidence, while deferred candidates and persistence
   changes are recorded truthfully;
5. registry, analyzer-version, deterministic-review import, and packaging
   outcomes are either proven or explicitly deferred; and
6. final verification reports exact base/head SHAs, required command results,
   documentation reconciliation, and no copied disposable artifacts.

The plan remains `proposed` until `skill-verification-before-completion`
returns `verified`.

## Explicit Deferrals

- Do not replace openpyxl or introduce a second parser.
- Do not add a global workbook cache, standalone reuse database, provenance format,
  process-isolation mechanism, or incremental persistence database.
- Do not prune provenance or make evidence lazy without a separate measured proof.
- Do not report dependency savings as XLSX latency improvements.
- Do not remove `pandas` unless isolated packaging and supported local-path tests
  prove it is unused.
- Do not mark this plan `completed` until `skill-verification-before-completion`
  returns `verified`.

## Self-Review

- Every justified P1/P2 finding maps to one task and a task-local proof.
- Contract resolution and source identity precede snapshot convergence and any
  optimization, preventing performance work from masking stale reuse.
- Existing owners remain authoritative; the registry and import-boundary modules
  are small compatibility/metadata boundaries, not new orchestration systems.
- Performance candidates have independent correctness/resource gates and explicit
  deferral rules for persistence and dependency changes.
- The plan names exact files, symbols, commands, dependencies, stop conditions,
  and final evidence without relying on placeholder tasks.
