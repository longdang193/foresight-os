---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: foresight-os-workbook-analysis-path-convergence
targets:
  - src/foresight_os/domain/models.py
  - src/foresight_os/domain/analysis_inputs.py
  - src/foresight_os/controller/policy.py
  - src/foresight_os/controller/recipes.py
  - src/foresight_os/persistence/analysis_store.py
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/runtime/capabilities.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/runtime/execution_gate.py
  - src/foresight_os/runtime/participants.py
  - src/foresight_os/analysis/workbook_inputs.py
  - src/foresight_os/analysis/workbook_engine.py
  - src/foresight_os/analysis/workbook_runner.py
  - src/foresight_os/analysis/portfolio_resilience.py
  - src/foresight_os/analysis/supplier_resilience.py
  - src/foresight_os/analysis/ev_capacity_investment.py
  - src/foresight_os/analysis/technology_radar.py
  - src/foresight_os/analysis/powerbi_strategic_portfolio.py
  - src/foresight_os/analysis/foresight_validator.py
  - src/foresight_os/runtime/executors.py
  - src/foresight_os/vertical_slice.py
  - src/foresight_os/cli.py
  - src/foresight_os/schemas/execution_recipe.schema.json
  - tests/test_analysis_input_contract.py
  - tests/test_workbook_engine.py
  - tests/test_workbook_runner.py
  - tests/test_local_toolbelt.py
  - tests/test_stage_inputs.py
  - tests/test_controller_selection.py
  - tests/test_runtime_boundaries.py
  - tests/test_evidence_workflow.py
  - tests/test_portfolio_resilience.py
  - tests/test_supplier_and_ev_resilience.py
  - tests/test_technology_powerbi_validator.py
  - tests/test_vertical_slice.py
  - tests/test_cli.py
  - evaluation/probes/optimization_measurement.py
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/compare_optimization_receipts.py
  - README.md
  - docs/architecture.md
  - docs/getting-started.md
  - docs/evidence-and-evaluation.md
  - evaluation/README.md
  - docs/superpowers/plans/2026-10-18-1414-foresight-os-workbook-analysis-path-convergence-plan.md
---

# ForesightOS Workbook Analysis Path Convergence

## Goal

Converge the five independent XLSX domain workflows on one strict, deterministic,
run-owned workbook-analysis path without weakening provenance, review, acceptance,
invalidation, bounded-resource, cancellation, or receipt-reuse behavior.

The implementation must preserve the existing `AnalysisState` and `AnalysisStore`
as the only durable analytical owners. `WorkbookReadCache` remains the existing
bounded read-cache primitive. The new scoped material representation is ephemeral
and must not become a second cache, source registry, analysis store, or provenance
format.

The current primary checkout is dirty and is at the merge base of the current
remote `main`. Execution of this plan must use a dedicated worktree from the
freshly fetched `origin/main`; the verified planning base on 2026-10-18 is
`71981cd2b0ba1e83f9bbf01c4e477ec08c00903b`. The primary checkout must remain
unchanged.

## Review Of The Verdict

The pasted review is directionally correct and should be accepted as the target
architecture, with these repository-specific corrections:

### Accepted conclusions

- Explicit workbook selections must fail closed. A missing named sheet, table, or
  range must produce a typed blocked-input failure rather than silently falling
  back to the worksheet used range.
- Global requirements and stage-local requirements must remain distinct. A stage
  receives only the global requirements plus its own requirements, not the union
  of every stage's capabilities and participants.
- Workbook analysis should use one run-owned context with one immutable source
  snapshot per source locator, one shared layout-resolution boundary, one scoped
  material view, deterministic domain logic, and the existing review and
  human-acceptance lifecycle.
- External research and agent orchestration are optional boundaries. They must be
  entered only when a stage contract requires them.
- Evidence materialization should be scoped to calculation and data-quality needs;
  provenance must remain available for every retained item.
- Low-level XLSX parsing, state-write reduction, and process isolation are
  measurement-gated follow-up work, not assumptions of correctness.

### Corrections required before execution

- The current `origin/main` already owns `AnalysisInputContract` and
  `NormalizedIntent` in `src/foresight_os/domain/analysis_inputs.py`. It also
  already owns `WorkbookContext` in `src/foresight_os/runtime/local_toolbelt.py`
  and has the shared workbook-input helpers in
  `src/foresight_os/analysis/workbook_inputs.py`. The plan must extend those
  owners rather than create parallel definitions.
- The five exercise analyzers already accept an input contract and optional
  workbook context on `origin/main`, but still duplicate domain workflow
  lifecycle code. The missing convergence is the pure deterministic engine and
  the standalone workflow runner, not another input-contract layer.
- `foresight_validator.py` is a cross-exercise validator and remains a consumer
  of the five analyzers in the first migration wave.
- The CLI `analyze` command currently calls the frozen CSV `run_vertical_slice`
  path. The migration must preserve the public command and test contract while
  moving its normal workbook execution to the production runner; the frozen
  case-001 behavior remains an explicit compatibility adapter until parity is
  proven.
- The current dirty changes are from an older local merge base and must not be
  treated as the implementation baseline. Task 1 must compare them with the
  freshly fetched `origin/main` before any work is ported or discarded.

### Explicit non-goals

- No second durable analysis store, workbook cache, source registry, or
  provenance representation.
- No generic DAG engine or declarative DSL for domain calculations.
- No universal process isolation for XLSX parsing.
- No custom XLSX parser before matched benchmark evidence establishes a material
  parsing cost and an owned correctness strategy.
- No silent removal of the frozen vertical slice, legacy recipe fields, or public
  CLI behavior without compatibility tests and documentation updates.

## Implementation Outcomes

### Strict, stage-local workbook input contracts

`WorkBrief` and `RecipeStage` preserve global and stage-local requirements through
serialization, recipe selection, approval fingerprints, and execution. Workbook
selection accepts explicit sheets, tables, ranges, canonical column mappings, and
scope fields. Missing explicit inputs fail with a typed blocked-input result;
used-range discovery is available only when the contract explicitly requests
discovery or provides no explicit selection.

### One reusable workbook material boundary

The existing `WorkbookContext` owns run-scoped snapshots and bounded read results
for one or more source locators. `ResolvedWorkbookLayout` maps domain logical
inputs to actual workbook tables, sheets, ranges, columns, units, and provenance.
`MaterialView` applies period, entity, scenario, and unit scope without copying
unrelated rows into durable state. The material view is fingerprinted from source,
layout, contract, and scope identity; it is not a second cache.

### Pure deterministic engine plus one standalone workflow runner

`WorkbookAnalysisEngine` owns contract resolution, context reuse, layout/material
construction, and domain analyzer invocation. It returns a typed deterministic
domain result and performs no persistence, review, human acceptance, or report
emission. `WorkbookWorkflowRunner` wraps that engine for standalone workflows and
owns pending publication, independent review, human acceptance, report generation,
status conversion, and cleanup. The five domain analyzers retain domain-specific
calculations and report content but no longer clone generic lifecycle mechanics.

### Optional runtime layered over the deterministic path

Workbook-only stages run through a typed `executor_kind=deterministic_local`
execution boundary with
no participant construction, provider initialization, model calls, synthesis
rounds, or correction loops unless the stage contract explicitly requires them.
External research remains demand-driven and stage-scoped. Agent-backed stages
continue to use the existing capability and approval boundaries.

This pass promises zero agent/provider execution for deterministic stages. It does
not promise installation-level removal of `agent-framework`; packaging decoupling
is a separate change unless a later approved task changes `pyproject.toml` and
lazy-import boundaries.

### Measured optimization and truthful compatibility

The production path has parity fixtures and a benchmark receipt that separates
correctness, resource safety, lifecycle settlement, and performance. Evidence
includes capture/parse counts, materialized evidence counts, serialized state
bytes, model and correction calls, repeated-work counts, peak RSS, and actual
cancellation settlement latency. Optimizations are applied only when the matched
baseline/release comparison demonstrates a material improvement without a
correctness or resource regression.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-using-git-worktrees`, `skill-plan-document-reviewer`, `skill-executing-plans`, `skill-backend-verification`, `skill-test-driven-development`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: dedicated worktree from the recorded `main` commit; preserve the dirty primary checkout
- Commit policy: `no commits during execution`; checkpoint commits require separate user authorization
- Preauthorized local actions: read and edit the declared source, test, evaluation, documentation, and plan files; create the dedicated worktree; run declared local tests and benchmarks; write benchmark output under `work/` or the system temporary directory
- User-approval actions: commit, push, merge, publication, external provider calls, destructive cleanup, reset, stash, discard, or changing the primary checkout
- Parallel ownership: `none`; shared contract, runner, analyzer, and receipt changes are intentionally serialized
- Sequential fallback: execute Tasks 1 through 9 in order in the same dedicated worktree; do not begin a later task when its dependency proof is absent

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `detached HEAD` in `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\workbook-analysis-path\foresight-OS`
- Base commit: `71981cd2b0ba1e83f9bbf01c4e477ec08c00903b` (`origin/main` verified on 2026-10-18; re-fetch and revalidate immediately before execution)
- Expected workspace: `dedicated worktree clean at freshly verified origin/main; primary checkout retains its existing dirty and untracked files`
- Next action: `run final repository verification and independent completion verification`
- Blockers: `none`; a base mismatch, unexpected copied files, or required destructive cleanup blocks execution

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `complete` | dedicated worktree | `lead controller` | none | baseline inventory and focused regression results | focused tests passed; baseline receipt at `C:\Users\HOANG PHI LONG DANG\AppData\Local\Temp\foresight-workbook-baseline-20261018.json` |
| Task 2 | `complete` | dedicated worktree | `lead controller` | Task 1 | stage-local contract and strict selection tests | focused contract, schema, persistence, approval, and toolbelt tests passed |
| Task 3 | `complete` | dedicated worktree | `lead controller` | Task 2 | existing input-contract extension and layout/material/provenance tests | focused input, toolbelt, material-view, evidence, and calculation tests passed |
| Task 4 | `complete` | dedicated worktree | `lead controller` | Task 3 | pure engine boundary tests | engine and focused input/toolbelt tests passed |
| Task 5 | `complete` | dedicated worktree | `lead controller` | Task 4 | standalone workflow lifecycle tests | runner, review, persistence, and invalidation tests passed |
| Task 6 | `complete` | dedicated worktree | `lead controller` | Task 5 | five-analyzer semantic parity tests | domain fixture suites passed; compatibility adapters retained |
| Task 7 | `complete` | dedicated worktree | `lead controller` | Task 6 | typed deterministic executor and runtime isolation tests | runtime, execution-gate, persistence, and group-chat suites passed |
| Task 8 | `complete` | dedicated worktree | `lead controller` | Task 7 | explicit CLI dispatch and matched benchmark receipts | CLI tests passed; comparison receipt recorded a truthful latency regression and no optimization claim |
| Task 9 | `in_progress` | dedicated worktree | `lead controller` | Tasks 1–8 | full repository, documentation, and plan verification | documentation reconciled; final verification pending |

## Task Breakdown

### Task 1: Reconcile the current remote baseline and freeze ownership

**Purpose:**
- Establish the authoritative starting point at the freshly fetched `origin/main`,
  capture the pre-change performance receipt, and record which input/context owners
  already exist before any implementation edits.

**Task Function:**
- Baseline reconciliation, ownership inventory, and immutable comparison setup.

**Template Profile:**
- Controller-selected: `lead controller`
- Selection basis: the task owns Git identity, dirty-worktree protection, baseline
  evidence, and the distinction between existing owners and proposed extensions.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller owns the baseline gate.

**Specification Coverage:**
- Use current `origin/main`, not the local merge base, as the implementation base.
- Preserve the dirty primary checkout without importing unreviewed edits.
- Capture performance before the refactor so the later release receipt has an
  immutable pre-change comparison.

**Required Skills:**
- `skill-using-git-worktrees`, `skill-plan-document-reviewer`, `skill-performance-optimization`

**Files And Symbols:**
- Inspect: `src/foresight_os/domain/analysis_inputs.py:AnalysisInputContract`, `NormalizedIntent`, `normalize_work_brief`
- Inspect: `src/foresight_os/runtime/local_toolbelt.py:WorkbookReadCache`, `WorkbookContext`, `spreadsheet_read`
- Inspect: `src/foresight_os/analysis/workbook_inputs.py:read_workbook`, `require_table`, `apply_table_column_mappings`, `row_evidence`
- Inspect: all five `analyze_*` and `run_*_workflow` pairs in the domain analyzers
- Inspect: `src/foresight_os/analysis/foresight_validator.py:validate_exercises`, `run_validator_workflow`
- Inspect: `src/foresight_os/controller/recipes.py:RecipeStage`, `src/foresight_os/controller/policy.py:select_recipe`
- Inspect: `src/foresight_os/runtime/capabilities.py:ExecutionMode`, `src/foresight_os/runtime/executors.py:AnalystExecutor`, `ReviewerExecutor`
- Verify: `tests/test_analysis_input_contract.py`, `tests/test_brief_portability.py`, `tests/test_local_toolbelt.py`, `tests/test_stage_inputs.py`, `tests/test_optimization_measurement.py`

**Dependencies:**
- A fresh fetch resolves `origin/main` to `71981cd2b0ba1e83f9bbf01c4e477ec08c00903b` or a newer verified commit.
- The primary checkout remains untouched; no reset, stash, checkout, or cleanup is permitted there.

**Authority:**
- Preauthorized local actions: fetch `origin/main`, create or attach the declared dedicated worktree, create a separate immutable baseline worktree, and read source, tests, plans, Git metadata, and primary-checkout status.
- Stop for: remote-base drift that is not re-recorded, unexpected copied dirty files, or any need to mutate or discard primary-checkout work.

**Steps:**
- [x] Step 1: Fetch `origin/main`, record the resolved SHA, and create the implementation worktree and detached baseline worktree from that exact SHA.
- [x] Step 2: Verify the implementation worktree is clean and the primary checkout retains its existing dirty and untracked files.
- [x] Step 3: Run the focused existing owner and analyzer tests without changing fixtures.
- [x] Step 4: Run the optimization probe from the detached baseline worktree and store its receipt outside both worktrees.
- [x] Step 5: Record the ownership matrix: `AnalysisInputContract`/`NormalizedIntent`, `WorkbookContext`, shared workbook helpers, analyzer domain functions, lifecycle wrappers, and runtime executor boundaries.

**Verification:**
- [x] `git -C $env:FORESIGHT_WORKTREE rev-parse HEAD` and `git -C $env:FORESIGHT_BASELINE rev-parse HEAD`
- Expected: both worktrees resolve to the same freshly verified `origin/main` SHA and are clean.
- [x] `python -m pytest -q tests/test_analysis_input_contract.py tests/test_brief_portability.py tests/test_local_toolbelt.py tests/test_stage_inputs.py tests/test_optimization_measurement.py`
- Expected: existing origin/main behavior passes before edits.
- [x] `Push-Location $env:FORESIGHT_BASELINE; python evaluation/probes/run_optimization_probe.py --mode baseline --fixture tests/fixtures/analyst_multisheet.xlsx --output $env:FORESIGHT_BASELINE_RECEIPT; Pop-Location`
- Expected: the receipt records the immutable baseline revision, fixture digest, environment, and measured workload.

**Exit Criteria:**
- The implementation and baseline worktrees are pinned to the same verified remote
  base, the pre-change receipt exists, and all proposed owners are distinguished
  from existing canonical owners.

### Task 2: Enforce stage-local requirements and strict workbook selection

**Purpose:**
- Close the two correctness boundaries that can silently change analytical scope:
  leaked stage requirements and missing explicit workbook selections.

**Task Function:**
- Contract normalization and fail-closed input validation.

**Template Profile:**
- Controller-selected: `lead controller`
- Selection basis: shared domain and controller contracts affect every later task;
  serialized identity must be fixed before new runner fingerprints are defined.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused contract and toolbelt regression tests validate the boundary.

**Specification Coverage:**
- A stage receives global requirements plus its own requirements only.
- Explicit missing sheets, tables, and ranges produce typed blocked-input failures.
- Used-range discovery remains available only for discovery requests or absent
  explicit selections.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/domain/models.py:WorkStage`, `ExecutionIntent`, `WorkBrief.to_dict`
- Inspect/modify: `src/foresight_os/controller/recipes.py:RecipeStage`, `ExecutionRecipe.to_dict`, `ExecutionRecipe.from_dict`
- Inspect/modify: `src/foresight_os/controller/policy.py:stage_requirements`, `stage_capabilities`, `_recipe_for_patterns`
- Inspect/modify: `src/foresight_os/persistence/analysis_store.py:load_brief`, `save_brief`, `load_recipe`, `save_recipe`
- Inspect/modify: `src/foresight_os/runtime/local_toolbelt.py:_coerce_sheet_selection`, `spreadsheet_read`
- Inspect/modify: `src/foresight_os/schemas/execution_recipe.schema.json`
- Verify: `tests/test_stage_inputs.py`, `tests/test_controller_selection.py`, `tests/test_local_toolbelt.py`, `tests/test_execution_approval_fingerprint.py`

**Dependencies:**
- Task 1 baseline matrix and current dirty-change inventory.

**Authority:**
- Preauthorized local actions: edit the declared contract, controller, persistence, schema, toolbelt, and focused test files; run focused local tests.
- Stop for: a required recipe or approval fingerprint change that cannot preserve existing serialized inputs, or a selection change that would broaden scope for an existing caller.

**Steps:**
- [x] Step 1: Define the serialized stage contract fields for `analysis_domains`, stage-local research requirements, `executor_kind`, and an input-contract reference/fingerprint; keep explicit workbook selections in the existing `AnalysisInputContract` rather than duplicating them in `RecipeStage`, and preserve legacy fields during load.
- [x] Step 2: Make recipe selection and stage capability derivation use only `global + current stage` requirements; keep aggregate requirements only in diagnostics and proposal views.
- [x] Step 3: Add a typed `MissingWorkbookInputError` under the existing toolbelt boundary and reject missing named sheets, tables, and ranges before used-range fallback.
- [x] Step 4: Preserve explicit discovery semantics and add regression fixtures for missing table, missing sheet, missing range, and mixed web/workbook stages.
- [x] Step 5: Verify approval and recipe fingerprints remain stable for semantically equivalent legacy inputs and change when stage-local input identity changes.

**Verification:**
- [x] `python -m pytest -q tests/test_stage_inputs.py tests/test_controller_selection.py tests/test_execution_approval_fingerprint.py tests/test_local_toolbelt.py`
- Expected: stage-local capability and participant tests prove no cross-stage leakage; explicit selection failures are typed and never read the used range.
- [x] `python -m pytest -q tests/test_analysis_schema.py tests/test_persistence.py`
- Expected: legacy recipe and brief serialization remains loadable and round-trippable.

**Exit Criteria:**
- The normalized contract is the single owner of stage-local requirements, and
  all explicit workbook selections fail closed without changing discovery callers.

### Task 3: Extend the shared workbook input and material-view layer

**Purpose:**
- Introduce one source snapshot and layout-resolution boundary that can serve all
  five domain analyzers without creating another durable store or cache.

**Task Function:**
- Shared input-model and provenance-preserving materialization design.

**Template Profile:**
- Controller-selected: `lead controller`
- Selection basis: the new shared owner is a high-coupling contract and requires
  direct provenance, identity, bounds, and cancellation proof.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: input-contract and toolbelt tests provide the required direct proof.

**Specification Coverage:**
- The existing `WorkbookContext` remains the run-owned context and can hold
  immutable source snapshots keyed by source locator; it reuses the existing
  bounded `WorkbookReadCache` rather than introducing a second cache.
- `ResolvedWorkbookLayout` owns logical-to-physical sheet/table/range/column
  mapping and layout fingerprinting.
- `MaterialView` is ephemeral, scoped, provenance-safe, and fingerprinted from
  source, layout, contract, and scope.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Modify: `src/foresight_os/domain/analysis_inputs.py:AnalysisInputContract`, `NormalizedIntent`, `normalize_work_brief` only for fields that the shared workbook contract still lacks
- Modify: `src/foresight_os/runtime/local_toolbelt.py:WorkbookContext`, `WorkbookReadCache`, `spreadsheet_read` without creating a second context or cache owner
- Extend: `src/foresight_os/analysis/workbook_inputs.py:WorkbookLayoutSpec`, `ResolvedWorkbookLayout`, `MaterialView`, `resolve_workbook_layout`, `build_material_view`
- Modify: `src/foresight_os/runtime/capabilities.py:CapabilityScope` workbook-cache construction and cleanup
- Verify: `src/foresight_os/domain/models.py:SourceLocator`, `MeasurementKey`, `Evidence`, `CalculationRecord`
- Add: `tests/test_analysis_input_contract.py`
- Verify: `tests/test_local_toolbelt.py`, `tests/test_evidence_candidates.py`, `tests/test_calculation_revision.py`

**Dependencies:**
- Task 2 strict selection and serialized contract behavior.

**Authority:**
- Preauthorized local actions: extend the existing domain contract, toolbelt context, and workbook-input helpers plus focused tests.
- Stop for: any design that persists `MaterialView`, duplicates `AnalysisStore`, stores provenance outside existing `SourceLocator`/measurement types, or requires global mutable workbook state.

**Steps:**
- [x] Step 1: Extend the existing `AnalysisInputContract` and `NormalizedIntent` with only the missing canonical fields for decision question, horizon, periods, entities, scenarios, units, explicit selections, column mappings, and compatibility version; preserve their existing serialization and fingerprint owners.
- [x] Step 2: Extend the existing `WorkbookContext` to reuse or capture source snapshots by source locator, carry source SHA, cancellation state, limits, and the existing `WorkbookReadCache`, and keep decision question and horizon outside the material workbook contract.
- [x] Step 3: Define `WorkbookLayoutSpec` and `ResolvedWorkbookLayout` in `analysis/workbook_inputs.py` with exact logical table names, accepted physical mappings, required columns, unit policy, and source-range provenance.
- [x] Step 4: Define `MaterialView` as an immutable scoped projection that retains source-row provenance and only materializes rows needed by the selected scope; preserve data-quality rows that explain rejected or incomplete inputs.
- [x] Step 5: Add tests for source identity, layout identity, contract identity, changed scope, unchanged source reuse, multiple source locators, missing mappings, provenance retention, bounds, and cancellation.

**Verification:**
- [x] `python -m pytest -q tests/test_workbook_engine.py tests/test_analysis_input_contract.py tests/test_local_toolbelt.py tests/test_evidence_candidates.py tests/test_calculation_revision.py`
- Expected: identical source and contract reuse one context; changed scope creates a new material-view fingerprint without recapturing the source; every retained row resolves to workbook SHA, sheet, and source range.
- [x] Direct boundary probe using `WorkbookContext` with a missing selection and a cancellation callback.
- Expected: missing input returns the typed blocked-input error; cancellation settles before the context is exposed to the analyzer; cache cleanup leaves no owned resources.

**Exit Criteria:**
- The new input layer is the only owner of workbook selection resolution and scoped
  materialization, and it has no durable state or cache distinct from existing owners.

### Task 4: Implement the pure deterministic workbook-analysis engine

**Purpose:**
- Centralize source/context/layout/material preparation and domain invocation
  without taking ownership of persistence or workflow lifecycle.

**Task Function:**
- Pure deterministic analysis composition.

**Template Profile:**
- Controller-selected: `lead controller`
- Selection basis: the engine is the shared input and domain boundary used by
  five analyzers and the runtime executor.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct engine tests prove deterministic composition; workflow
  lifecycle proof belongs to Task 5.

**Specification Coverage:**
- `WorkbookAnalysisEngine` owns contract normalization, context reuse, layout
  resolution, material-view construction, domain invocation, and deterministic
  diagnostics.
- The engine returns a typed domain result and does not persist state, publish
  pending analysis, run review, accept findings, render reports, or own the full
  workflow lifecycle.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Add: `src/foresight_os/analysis/workbook_engine.py:DomainAnalysis`, `DomainAnalyzer`, `WorkbookAnalysisEngine`, `WorkbookEngineResult`
- Verify: `src/foresight_os/domain/analysis_inputs.py:AnalysisInputContract`, `src/foresight_os/runtime/local_toolbelt.py:WorkbookContext`, `src/foresight_os/analysis/workbook_inputs.py:MaterialView`
- Add: `tests/test_workbook_engine.py`
- Verify: `tests/test_analysis_input_contract.py`, `tests/test_local_toolbelt.py`, `tests/test_evidence_candidates.py`

**Dependencies:**
- Task 3 shared input and provenance contracts.

**Authority:**
- Preauthorized local actions: add the engine and focused tests; update only the
  declared analyzer protocol references needed to consume its result.
- Stop for: any engine path that writes durable state, performs review or
  acceptance, emits a report, or turns provider success into analytical truth.

**Steps:**
- [x] Step 1: Define the analyzer protocol and typed result carrying domain-produced analytical state or domain facts, source/layout/contract fingerprints, material-view diagnostics, and deterministic status information without persistence concerns.
- [x] Step 2: Implement engine stages in order: normalize the existing input contract, acquire or reuse context, resolve layout, build material view, invoke the domain analyzer, and return the typed deterministic result.
- [x] Step 3: Represent missing inputs, malformed analyzer output, and cancellation as typed engine outcomes that the workflow runner can map to repository status classes without message-substring branching.
- [x] Step 4: Add engine-owned metrics for source captures, parse count, materialized evidence count, and deterministic diagnostics; leave review, acceptance, report, and lifecycle metrics to Task 5.
- [x] Step 5: Prove same source/contract/scope reuse is deterministic and changed scope changes the material fingerprint without rerunning unrelated source capture.

**Verification:**
- [x] `python -m pytest -q tests/test_workbook_engine.py tests/test_analysis_input_contract.py tests/test_local_toolbelt.py tests/test_evidence_candidates.py`
- Expected: the engine has no persistence, review, acceptance, or report side effects; repeated deterministic inputs produce the same result and fingerprints.
- [x] Direct engine boundary test with a fake analyzer and a run-owned `WorkbookContext`.
- Expected: one source capture for a reused source locator, typed missing-input and cancellation outcomes, retained provenance, and no `AnalysisStore` access.

**Exit Criteria:**
- A pure engine can execute one deterministic workbook analyzer and return a
  typed result without owning persistence, review, acceptance, or reporting.

### Task 5: Add the standalone workbook workflow runner

**Purpose:**
- Wrap the pure engine in the existing standalone workflow lifecycle without
  duplicating persistence, review, acceptance, or report-gating owners.

**Task Function:**
- Workflow lifecycle adapter around `WorkbookAnalysisEngine`.

**Template Profile:**
- Controller-selected: `lead controller`
- Selection basis: the runner crosses analysis, review, persistence, acceptance,
  cancellation, and reporting boundaries and must preserve their existing contracts.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct runner tests and existing review/persistence tests cover the boundary.

**Specification Coverage:**
- `WorkbookWorkflowRunner` invokes the engine, publishes pending state through
  `AnalysisStore`, runs independent review, applies human acceptance, renders
  only accepted current state, converts typed failures to existing statuses, and
  cleans up owned resources.
- Recipe execution invokes the engine directly and does not nest the full
  workflow runner or duplicate persistence and acceptance.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Add: `src/foresight_os/analysis/workbook_runner.py:WorkbookWorkflowRunner`, `WorkbookWorkflowResult`
- Modify: `src/foresight_os/analysis/review_workflow.py:review_and_accept_pending_analysis` only where runner metadata must be carried without changing acceptance semantics
- Verify: `src/foresight_os/persistence/analysis_store.py:save_pending`, `update_pending`, `commit_revision`, `load_pending`
- Verify: `src/foresight_os/analysis/reviewer.py:review_analysis_state`, `src/foresight_os/domain/challenge.py:derive_finding_views`
- Add: `tests/test_workbook_runner.py`
- Verify: `tests/test_review_workflow.py`, `tests/test_persistence.py`, `tests/test_invalidation.py`, `tests/test_review_hardening.py`

**Dependencies:**
- Task 4 pure engine and Task 3 shared input/provenance contracts.

**Authority:**
- Preauthorized local actions: add the workflow runner and modify only the
  declared review integration points and focused tests.
- Stop for: any runner path that bypasses `AnalysisStore`, accepts conclusions
  without current review and human acceptance, or emits a report before an
  accepted current state exists.

**Steps:**
- [x] Step 1: Define the runner result and lifecycle adapter around the engine's typed result, preserving source/layout/contract fingerprints and domain diagnostics.
- [x] Step 2: Implement pending publication, independent review, human decision, accepted-state report rendering, status conversion, cancellation settlement, and cleanup through existing owners.
- [x] Step 3: Prevent nested persistence or duplicate acceptance when the engine is invoked from recipe execution; keep recipe execution responsible for stage receipt and later analytical review boundaries.
- [x] Step 4: Add runner-owned metrics for state bytes, review calls, acceptance status, and cancellation settlement while retaining engine metrics from Task 4.
- [x] Step 5: Prove idempotent lifecycle behavior for the same source/contract/scope and explicit invalidation when retained analytical inputs change.

**Verification:**
- [x] `python -m pytest -q tests/test_workbook_runner.py tests/test_review_workflow.py tests/test_persistence.py tests/test_invalidation.py tests/test_review_hardening.py`
- Expected: pending, accepted, rejected, blocked-input, blocked-external, cancelled, and stale-review paths preserve existing state transitions and no report is emitted before accepted current findings.
- [x] Direct runner boundary test with a real workbook engine and a real temporary `AnalysisStore`.
- Expected: one source capture, one pending publication, one review attachment, one explicit acceptance decision, and deterministic cleanup.

**Exit Criteria:**
- A standalone workflow runner wraps the pure engine through the full existing
  lifecycle without duplicating persistence, review, acceptance, or reporting owners.

### Task 6: Migrate the five domain analyzers and preserve parity

**Purpose:**
- Move the production XLSX analyzers onto the shared input and runner contracts
  without changing their domain calculations, findings, provenance, or reports.

**Task Function:**
- Domain adapter migration and behavioral parity.

**Template Profile:**
- Controller-selected: `lead controller`
- Selection basis: five consumers share the engine and workflow runner but have disjoint domain logic;
  serial migration prevents hidden contract drift and makes parity failures local.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing domain fixture tests plus runner tests validate parity.

**Specification Coverage:**
- Portfolio, supplier, EV, technology, and Power BI analyzers keep domain-specific
  calculations and report content.
- Generic workbook acquisition, fixed sheet assumptions, evidence plumbing,
  persistence, review, acceptance, and exception conversion move to shared owners.
- `foresight_validator.py` remains a cross-exercise validator and consumes the
  migrated analyzer contracts rather than becoming a second runner.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `src/foresight_os/analysis/portfolio_resilience.py:analyze_portfolio_resilience`, `run_portfolio_resilience_workflow`
- Modify: `src/foresight_os/analysis/supplier_resilience.py:analyze_supplier_resilience`, `run_supplier_resilience_workflow`
- Modify: `src/foresight_os/analysis/ev_capacity_investment.py:analyze_ev_capacity_investment`, `run_ev_capacity_investment_workflow`
- Modify: `src/foresight_os/analysis/technology_radar.py:analyze_technology_radar`, `run_technology_radar_workflow`
- Modify: `src/foresight_os/analysis/powerbi_strategic_portfolio.py:analyze_powerbi_strategic_portfolio`, `run_powerbi_strategic_portfolio_workflow`
- Modify only for integration: `src/foresight_os/analysis/foresight_validator.py:validate_exercises`, `run_validator_workflow`
- Verify: `tests/test_portfolio_resilience.py`, `tests/test_supplier_and_ev_resilience.py`, `tests/test_technology_powerbi_validator.py`, `tests/test_evidence_workflow.py`
- Add: parity assertions in `tests/test_workbook_runner.py`

**Dependencies:**
- Task 5 workflow runner, Task 4 engine, and Task 3 material-view contracts.

**Authority:**
- Preauthorized local actions: migrate the five declared analyzers, their integration tests, and the validator adapter without changing unrelated runtime or persistence modules.
- Stop for: any parity failure that changes a calculation, evidence locator, FindingView status, report acceptance rule, or explicit workbook scope without a separately recorded contract decision.

**Steps:**
- [x] Step 1: Define one `WorkbookLayoutSpec` and one `AnalysisInputContract` adapter for each analyzer, replacing hard-coded `SheetSelection` construction at the analyzer boundary.
- [x] Step 2: Change each analyzer's domain entry point to consume `MaterialView` and return `DomainAnalysis`; retain a thin source-path compatibility adapter for existing direct callers during migration.
- [x] Step 3: Replace each duplicated workflow wrapper with `WorkbookWorkflowRunner.run`, keep domain entry points on `WorkbookAnalysisEngine`, and preserve each report renderer's accepted-state guard and output path.
- [x] Step 4: Update the validator to call the migrated domain entry points and keep its cross-exercise checks, planted anomalies, and source-specific validation behavior.
- [x] Step 5: Compare semantic parity for all existing XLSX fixtures: calculation values, retained evidence IDs and locators, findings/statements/statuses, review coverage, source SHA, report meaning/text, and acceptance behavior; prove every retained reference resolves and do not require full `AnalysisState` hash equality when scoped evidence reduction intentionally changes serialization.

**Verification:**
- [x] `python -m pytest -q tests/test_portfolio_resilience.py tests/test_supplier_and_ev_resilience.py tests/test_technology_powerbi_validator.py tests/test_evidence_workflow.py tests/test_workbook_runner.py`
- Expected: all five analyzers preserve fixture results, provenance, FindingViews, lifecycle statuses, and accepted report gates while using the shared engine and workflow runner.
- [x] Run the five migrated analyzer workflows directly against their existing XLSX fixtures using isolated `work/` directories.
- Expected: each workflow leaves an explicit state/report outcome and no provider or agent call occurs for workbook-only analysis; public CLI dispatch is verified separately in Task 8.

**Exit Criteria:**
- All five production domain workflows use the shared engine and standalone runner;
  the validator remains a consumer; parity evidence records intentional output
  differences and proves removed evidence was unreferenced or out of scope.

### Task 7: Add the deterministic-local runtime path

**Purpose:**
- Keep deterministic workbook stages out of generic agent orchestration while
  preserving approval, stage receipts, settlement, and external-stage behavior.

**Task Function:**
- Typed executor dispatch and runtime boundary simplification.

**Template Profile:**
- Controller-selected: `lead controller`
- Selection basis: executor dispatch, participant creation, capability scope, and
  stage settlement share one runtime boundary and must be changed together.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: runtime-boundary and execution tests provide direct proof.

**Specification Coverage:**
- A stage with `executor_kind=deterministic_local` does not construct participants or
  providers and does not spend agent-call or correction budgets.
- A stage requiring web, MCP, document, or adaptive reasoning still uses the
  existing capability, approval, and settlement boundaries.
- Recipe execution invokes the pure engine through a typed executor and never
  nests the standalone workflow runner.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Add/modify: `src/foresight_os/runtime/executors.py:DeterministicLocalExecutor`, typed handler dispatch, and executor result mapping
- Modify: `src/foresight_os/runtime/workflow.py:run_recipe_async`, stage dispatch and settlement paths
- Modify: `src/foresight_os/runtime/execution_gate.py:execute_approved_recipe` and approval checks only where deterministic-local admission is required
- Modify: `src/foresight_os/runtime/participants.py:AgentFactory.create` and `src/foresight_os/runtime/capabilities.py:CapabilityScope` to avoid initialization for local stages
- Verify: `tests/test_runtime_boundaries.py`, `tests/test_execution_gate.py`, `tests/test_execution_persistence.py`, `tests/test_group_chat.py`

**Dependencies:**
- Task 2 stage-local contracts, Task 5 workflow runner, and Task 6 analyzer parity.

**Authority:**
- Preauthorized local actions: edit the declared runtime executor, workflow, gate,
  participant/capability boundaries, and focused tests; run local boundary probes
  with provider-free fixtures.
- Stop for: a change that bypasses required execution approval, makes external capability failures look local, or removes the public `analyze`/`run_vertical_slice` contract without a compatibility path.

**Steps:**
- [x] Step 1: Add and validate typed `executor_kind=deterministic_local` in the recipe contract; derive it from normalized stage requirements rather than from analyzer name and preserve `ExecutionMode` for its existing runtime meaning.
- [x] Step 2: Route deterministic-local stages through `DeterministicLocalExecutor` to `WorkbookAnalysisEngine`; keep generic participant/provider construction for agent or external stages only and never invoke the full workflow runner from recipe execution.
- [x] Step 3: Preserve execution approval and analytical acceptance as separate boundaries; record deterministic-local approval in the same recipe/approval fingerprint model.
- [x] Step 4: Make external research demand-driven from explicit stage research needs or evidence gaps; prove a workbook-only stage causes zero provider setup and model calls even when another stage requires web search.
- [x] Step 5: Preserve stage receipts, result committing, cancellation, cleanup, and later analytical review boundaries while ensuring typed executor results cannot be mistaken for accepted analytical state.

**Verification:**
- [x] `python -m pytest -q tests/test_runtime_boundaries.py tests/test_execution_gate.py tests/test_execution_persistence.py tests/test_group_chat.py`
- Expected: deterministic-local stages have zero participant/provider/model calls; external stages retain approval, budgets, cleanup, and explicit blocked-external outcomes.
- [x] Direct runtime boundary probe using deterministic-local stage tests and the existing external-stage boundary suite.
- Expected: the deterministic stage performs zero participant/provider/model calls; the external stage retains approval, budgets, cleanup, and explicit blocked-external outcomes.

**Exit Criteria:**
- Deterministic workbook analysis does not pay generic agent/runtime costs, and
  recipe execution preserves stage receipts, result committing, cancellation, and
  later analytical review boundaries.

### Task 8: Add explicit CLI dispatch and apply only evidence-selected optimization

**Purpose:**
- Route public CLI inputs explicitly and measure the converged path with matched
  workloads before making at most one secondary optimization.

**Task Function:**
- Explicit CLI dispatch, compatibility preservation, performance measurement, and
  gated optimization decision.

**Template Profile:**
- Controller-selected: `lead controller`
- Selection basis: CLI routing and benchmark interpretation determine whether the
  public path exercises the intended implementation and whether an optimization is justified.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: CLI dispatch tests and the benchmark comparator provide direct validation.

**Specification Coverage:**
- CSV compatibility, explicit XLSX domain dispatch, correctness, regression
  threshold, and optimization-demonstrated outcomes remain separate.
- Measure cold/warm reads, source captures, parse counts, materialized evidence,
  serialized state bytes, model/correction calls, repeated work, peak RSS, soak
  cleanup, and cancellation settlement latency.
- Optimize only the selected measured owner; record every unselected proposal as
  an explicit deferral rather than implementing speculative cleanup.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`

**Files And Symbols:**
- Modify: `src/foresight_os/cli.py:main`, parser definitions, and `analyze` dispatch
- Modify: `src/foresight_os/vertical_slice.py:run_vertical_slice` only as the CSV compatibility adapter
- Verify: `tests/test_cli.py`, `tests/test_vertical_slice.py`
- Modify: `evaluation/probes/optimization_measurement.py:build_receipt`, metric snapshots, workload metadata
- Modify: `evaluation/probes/run_optimization_probe.py:main` and workload runners
- Modify: `evaluation/probes/compare_optimization_receipts.py:main` and threshold checks
- Verify: `src/foresight_os/runtime/local_toolbelt.py:WorkbookContext`, `WorkbookReadCache`, `spreadsheet_read`
- Verify: `src/foresight_os/analysis/workbook_engine.py:WorkbookAnalysisEngine`, `src/foresight_os/analysis/workbook_runner.py:WorkbookWorkflowRunner`
- Add/modify: `tests/test_optimization_measurement.py`
- Update: `evaluation/README.md`, `docs/evidence-and-evaluation.md`

**Dependencies:**
- Tasks 1–7 complete with parity and deterministic-local isolation proven.

**Authority:**
- Preauthorized local actions: edit the declared CLI, compatibility adapter,
  benchmark, and focused test files; run matched local benchmark workloads and
  write only to `work/` or the system temporary directory.
- Stop for: missing matched baseline/release metadata, correctness mismatch, increased resource use, unreliable sample stability, or any optimization requiring a new cache/store or process boundary without a separate approved scope.

**Steps:**
- [x] Step 1: Add explicit CLI dispatch: CSV continues through `run_vertical_slice`; XLSX `analyze` requires `--domain` or an existing brief with exactly one resolvable analysis domain, and missing or ambiguous domain returns `BLOCKED_INPUT`.
- [x] Step 2: Reject filename/layout guessing and add CLI/compatibility tests covering CSV, explicit XLSX domain, missing domain, and ambiguous domain.
- [x] Step 3: Extend receipts with source/layout/contract fingerprints, environment, fixture digest, sample counts, evidence/state-size metrics, capture/parse counts, repeated-work counts, and cancellation settlement observations.
- [x] Step 4: Run baseline from the immutable Task 1 baseline worktree and release from the implementation worktree against the same fixture, Python environment, limits, warmups, and measured-run counts; keep output outside both Git worktrees.
- [x] Step 5: Compare correctness and resource safety independently from latency; select no more than one optimization owner from measured evidence and record deferred persistence, parser, dependency, topology, and process-isolation work without implementing it speculatively.

**Verification:**
- [x] `python -m pytest -q tests/test_cli.py tests/test_vertical_slice.py tests/test_optimization_measurement.py`
- Expected: missing workloads, zero denominators, unstable samples, fixture mismatch, increased calls, resource regressions, and correctness failures are rejected with explicit statuses.
- [x] Baseline receipt: `C:\Users\HOANG PHI LONG DANG\AppData\Local\Temp\foresight-workbook-baseline-20261018.json`
- [x] Release receipt: `C:\Users\HOANG PHI LONG DANG\AppData\Local\Temp\foresight-workbook-release-20261018.json`
- [x] Comparison receipt: `C:\Users\HOANG PHI LONG DANG\AppData\Local\Temp\foresight-workbook-comparison-20261018.json`
- Expected: receipts are comparable, correctness is verified, cleanup is complete, and optimization is claimed only when the owned threshold is met. Actual: correctness, allocation, RSS, soak, and MAF pattern evidence are verified; the XLSX p95 regression is `45.895%`, `cold_workbook` is `92.531%`, and `analyst_validator_reuse` is `26.15%`, so the regression gate failed and no optimization is claimed.

**Exit Criteria:**
- The benchmark produces truthful receipts and either one measured optimization
  is proven safe and material or the optimization tail is explicitly deferred.

### Task 9: Reconcile documentation and perform final verification

**Purpose:**
- Ensure source, tests, schemas, maintained guidance, and the plan describe the
  same supported workbook path and that the final change is ready for independent
  completion verification.

**Task Function:**
- Final source-of-truth reconciliation and verification handoff.

**Template Profile:**
- Controller-selected: `lead controller`
- Selection basis: final verification owns cross-task consistency, documentation
  links, generated schema alignment, and truthful status reporting.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification is delegated to `skill-verification-before-completion` after the lead reconciles the tree.

**Specification Coverage:**
- Documentation reflects actual CLI, workbook contract, deterministic-local path,
  external-stage boundary, provenance, review, acceptance, and benchmark behavior.
- No required task, scope deviation, stale ledger state, or unrecorded deferral
  remains.

**Required Skills:**
- `skill-plan-document-reviewer`, `skill-verification-before-completion`

**Files And Symbols:**
- Verify: all declared source, test, schema, evaluation, and documentation targets
- Inspect: `git diff --check`, `git status --short`, plan coordination ledger and task evidence
- Run: `scripts/check_markdown_links.py`

**Dependencies:**
- Tasks 1–7 complete and all task-local exit criteria satisfied.

**Authority:**
- Preauthorized local actions: reconcile declared documentation, schema, plan ledger, and test references; run final local verification commands.
- Stop for: unresolved required failure, stale plan state, unrecorded scope expansion, or any need to commit, publish, reset, discard, or clean unrelated files.

**Steps:**
- [x] Step 1: Re-read the final source and tests for owner duplication, stale names, and generated-schema drift.
- [x] Step 2: Update `README.md`, `docs/architecture.md`, `docs/getting-started.md`, `docs/evidence-and-evaluation.md`, and `evaluation/README.md` only from the implemented source-of-truth behavior.
- [x] Step 3: Record task evidence, deviations, deferred optimizations, benchmark limitations, and the next dependency-ready action in this plan.
- [x] Step 4: Run final repository verification and hand the plan to `skill-verification-before-completion`; do not mark the plan completed from checked boxes alone.

**Verification:**
- [x] `python -m pytest -q`
- [x] `python -m compileall -q src tests evaluation`
- [x] `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/getting-started.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- [x] `git diff --check`
- [x] `git status --short --branch`
- Expected: all required checks pass, links resolve, the dedicated worktree contains only declared changes, the primary dirty checkout is unchanged, and unavailable external evidence is labeled rather than converted into success.

**Exit Criteria:**
- The plan is ready for completion verification with all outcomes, task proofs,
  deviations, deferrals, and final commands reconciled.

## Verification

Final artifact verification is one fresh pass after all task-local checks:

- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/getting-started.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- `git diff --check`
- matched baseline/release benchmark comparison from Task 8
- dedicated-worktree `git status --short --branch` and declared-target diff inspection

Structural proof must be reported separately from provider availability, model
quality, human acceptance, and any performance dimension that was not measured.

## Completion Criteria

The plan is ready for completion verification when:

1. `WorkBrief`, `WorkStage`, `RecipeStage`, and persisted recipes preserve
   global/stage-local requirements and approval identity without cross-stage
   capability leakage.
2. Explicit workbook selections fail closed, while discovery callers retain their
   existing used-range behavior.
3. `WorkbookContext`, `ResolvedWorkbookLayout`, and `MaterialView` are the sole
   ephemeral workbook-input owners and do not create a second cache, store, or
   provenance format.
4. `WorkbookAnalysisEngine` owns deterministic source/context/layout/material
   composition without persistence or workflow side effects, and
   `WorkbookWorkflowRunner` preserves pending, accepted, rejected, blocked-input,
   blocked-external, cancellation, review-currentness, invalidation, and
   report-gating semantics.
5. All five production XLSX analyzers use the shared engine and workflow runner
   and preserve fixture values, evidence locators, source hashes, findings,
   reports, and accepted-state guards.
6. `foresight_validator.py` remains a cross-exercise validator rather than a
   competing workflow owner.
7. Deterministic-local stages initialize no providers or participants and make no
   model calls; external stages retain explicit approval, capability, budget,
   cleanup, and failure boundaries.
8. The public `analyze` command uses explicit CSV/XLSX dispatch with fail-closed
   XLSX domain selection, while `run_vertical_slice` remains supported and
   documented with provider-free regression proof.
9. Benchmark receipts separate correctness, regression safety, resource safety,
   lifecycle settlement, and optimization claims; at most one secondary
   optimization is accepted from matched evidence.
10. Full tests, compilation, Markdown-link checks, diff checks, documentation,
    plan ledger, and dedicated-worktree boundaries agree with repository truth.

The plan may be marked `completed` only after
`skill-verification-before-completion` returns `verified`. A checked box is
progress evidence, not completion proof.

## Self-Review

- Spec coverage: every recommendation in the pasted review maps to Tasks 2–8;
  Task 1 corrects repository-state and architecture assumptions; Task 9 owns
  documentation and final proof.
- Ownership: `AnalysisStore` remains durable state owner; `local_toolbelt.py`
  remains source capture and bounded read owner; `analysis_inputs.py` owns the
  canonical input contract; `workbook_inputs.py` owns layout/material resolution;
  `workbook_engine.py` owns pure deterministic composition; `workbook_runner.py`
  owns standalone lifecycle; domain modules own calculations; controller/runtime
  modules own stage admission and optional capabilities.
- Compatibility: legacy recipe fields, the CLI `analyze` command, and
  `run_vertical_slice` remain until parity proof exists; `foresight_validator.py`
  is not duplicated into the runner.
- Measurement: state-size, parser, dependency, process-isolation, and full
  persistence-write changes are gated by Task 8 and explicitly deferred when
  evidence is absent.
- Shared writes: the plan is sequential because controller, toolbelt, runner,
  analyzer, persistence, and benchmark changes share contracts; no parallel lane
  is safe without a later approved decomposition.
- Verification: focused tests cover each boundary, Task 8 covers explicit CLI
  dispatch and matched performance/resource evidence, and Task 9 runs the
  repository-required final commands through the verification skill.
