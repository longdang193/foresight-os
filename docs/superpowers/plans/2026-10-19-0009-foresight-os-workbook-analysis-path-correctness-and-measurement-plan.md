---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: foresight-os-workbook-analysis-path-correctness-and-measurement
targets:
  - src/foresight_os/domain/analysis_inputs.py
  - src/foresight_os/analysis/workbook_inputs.py
  - src/foresight_os/analysis/workbook_engine.py
  - src/foresight_os/analysis/workbook_runner.py
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/runtime/executors.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/runtime/execution_gate.py
  - src/foresight_os/runtime/capabilities.py
  - src/foresight_os/controller/policy.py
  - src/foresight_os/controller/proposal.py
  - src/foresight_os/controller/recipes.py
  - src/foresight_os/domain/validation.py
  - src/foresight_os/domain/approval.py
  - src/foresight_os/domain/models.py
  - src/foresight_os/schemas/execution_recipe.schema.json
  - src/foresight_os/analysis/evidence_workflow.py
  - src/foresight_os/analysis/review_workflow.py
  - src/foresight_os/analysis/result_committer.py
  - src/foresight_os/analysis/portfolio_resilience.py
  - src/foresight_os/analysis/supplier_resilience.py
  - src/foresight_os/analysis/ev_capacity_investment.py
  - src/foresight_os/analysis/technology_radar.py
  - src/foresight_os/analysis/powerbi_strategic_portfolio.py
  - src/foresight_os/persistence/analysis_store.py
  - src/foresight_os/cli.py
  - pyproject.toml
  - README.md
  - tests/
  - evaluation/probes/
  - evaluation/README.md
  - docs/
---

# Workbook Analysis Path: Correctness and Measurement

## Goal

Finish the workbook-analysis convergence that PR #35 established without
replacing its architecture. The implementation must make scope selection,
physical workbook binding, stage-domain admission, provider-free approved
execution, lazy capability activation, cancellation, acceptance settlement, and
resource ownership correct before interpreting or optimizing the observed XLSX
latency regression.

The plan starts from current `origin/main` commit `71981cd2b0ba1e83f9bbf01c4e477ec08c00903b`
and preserves `AnalysisState`/`AnalysisStore` as the durable analytical owner,
`WorkbookContext` as the source snapshot/read owner, and the existing
`WorkbookAnalysisEngine`/`WorkbookWorkflowRunner` separation.

## Review Of The Verdict

The verdict is sound and its ordering is justified. It correctly rejects an
optimization-first response because the current path still has correctness and
integration questions that can invalidate latency conclusions. The following
items are accepted as implementation requirements:

- Canonical domain mappings must drive scope predicates before generic header
  guessing; missing applicable dimensions must fail closed, while irrelevant
  dimensions remain explicitly not applicable.
- Logical workbook bindings and physical sheet/range selection must be compiled
  together, with explicit selections failing closed rather than silently using a
  used-range fallback.
- Global contracts are available inventory/defaults, not implicit execution
  domains. Every deterministic workbook stage must name exactly one domain.
- The existing `RecipeStage.analysis_domains` representation remains the wire
  contract; a stage-scoped `AnalysisInputContract.stage_id` selects the domain,
  while global contracts provide compatible defaults only.
- All-local approved recipes must complete through the normal proposal,
  approval, admission, execution, and committed-result path with no provider
  client or credentials.
- Deterministic approved execution must receive one explicit local workbook
  source, validate it at admission, and bind its captured SHA to the stage
  receipt without creating a second source catalog.
- External capabilities/resources must be activated at the stage boundary, not
  eagerly for the whole recipe.
- Blocking workbook work must use the existing bounded worker pattern and
  cooperative cancellation; acceptance must settle before cancellation can
  publish or commit a result.
- Accepted analytical state must survive report/artifact failure.

The following are measurement-gated follow-ups rather than pre-accepted fixes:
zero-copy/indexed material views, dropping ordinary out-of-scope provenance,
lazy evidence resolution, accepted-result reuse, persistence protocol changes,
second-load elimination, process isolation, and dependency cleanup. They are
included only after focused parity and matched benchmark evidence identify a
benefit. No new cache, parser, orchestration layer, analytical store, or
provenance format is authorized.

## Implementation Outcomes

### Correct and explicit workbook inputs

Each deterministic domain has one domain-owned specification for logical tables,
physical selection, canonical columns, scope bindings, units, and compatibility
defaults. Analyzer identity is a separate execution identity, not part of the
material input-contract fingerprint. Resolved layouts compile these decisions
before materialization, preserve comparison/validation rows when required, and return
typed blocked-input failures for missing required data.

### Correct approved execution and lifecycle settlement

Proposal validation rejects zero or multiple deterministic domains for a
workbook-computation stage. The normal approved execution path requires one
explicit local workbook source for deterministic stages, supports credential-free
all-local recipes, activates external resources lazily, runs blocking workbook
work through the bounded worker mechanism, propagates typed cancellation and
input failures, disposes only owned contexts, and leaves accepted state intact
when report generation fails.

### Measurement-backed reduction of repeated work

After correctness parity, the implementation removes only measured overhead from
material views, evidence construction, repeated accepted runs, persistence, and
parsing. Benchmark receipts distinguish correctness, lifecycle, resource, and
optimization evidence, and unsupported optimizations remain explicitly deferred.

### Regression and documentation coverage

Focused adversarial tests cover renamed bindings, missing dimensions, period
intervals, units, provider-free execution, lazy activation, cancellation,
artifact failure, resource disposal, and accepted-result reuse. Maintained docs
describe the canonical path and its deferred compatibility boundaries.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-plan-document-reviewer`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `optional worktree`; use a dedicated worktree from fresh `origin/main` because the primary checkout is dirty
- Commit policy: `no commits during execution`; checkpoint commits require a later explicit Git disposition approval
- Preauthorized local actions: inspect source/tests/docs, edit declared files, run focused and repository-required checks, and generate local benchmark receipts without external publication
- User-approval actions: push, merge, pull-request publication, external provider calls, destructive cleanup, discarding unrelated work, or widening the declared scope
- Parallel ownership: `none`; controller, runtime, workbook, persistence, and benchmark contracts share owners and must be serialized
- Sequential fallback: complete each task and its proof in order; do not start measurement-gated optimization before the correctness and lifecycle gates pass

## Coordination State

- Lead controller: current Codex session
- Plan status: `completed`
- Execution state: completed and verified
- Source of truth: this Git-tracked plan plus repository source/tests; runtime session state is not recovery state
- Shared-write policy: one lead owns all edits because `analysis_inputs.py`, `workbook_inputs.py`, `workflow.py`, `execution_gate.py`, `workbook_runner.py`, and benchmark fixtures form one contract chain
- Recovery rule: after interruption, inspect Git status, this plan, and the latest task-local evidence before resuming; never infer completion from a prior chat summary
- External state: no provider, network, publication, or merge action is part of this plan

## Task Breakdown

### Task 1: Establish the post-PR baseline and reproduce correctness boundaries

**Purpose:**
- Establish a clean evidence boundary after PR #35 and turn each verdict P0 into a focused reproducible test or an explicitly disproven hypothesis.

**Task Function:**
- Baseline and contract reconciliation

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: baseline work is bounded, source-first, and does not require a specialized executor.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller owns repository baseline reconciliation.

**Specification Coverage:**
- Verdict P0 correctness and integration findings; matched PR #35 latency/resource evidence; dirty-primary-checkout constraint.

**Required Skills:**
- `skill-backend-verification`, `skill-performance-optimization`

**Files And Symbols:**
- Inspect: `src/foresight_os/analysis/workbook_inputs.py:WorkbookLayoutSpec`, `resolve_workbook_layout`, `_row_matches_scope`, `build_material_view`
- Inspect: `src/foresight_os/controller/policy.py:stage_analysis_domains`, `stage_contract_fingerprints`
- Inspect: `src/foresight_os/runtime/execution_gate.py:ExecutionGate`, `src/foresight_os/runtime/workflow.py:run_recipe_async`
- Inspect: `src/foresight_os/analysis/workbook_runner.py:WorkbookWorkflowRunner.run`
- Modify: `tests/test_analysis_input_contract.py`, `tests/test_workbook_engine.py`, `tests/test_controller_selection.py`, `tests/test_runtime_boundaries.py`, `tests/test_workbook_runner.py`, and one named local probe under `evaluation/probes/` only where a missing regression proof is confirmed
- Verify: convergence commit `fb57d73fb30c5a6f485fc4fe10a0e9d888dcac91` and matched benchmark receipts for XLSX p95, cold workbook, reuse, allocation, RSS, soak, and correctness

**Dependencies:**
- Fresh `origin/main` inspection; no implementation task may assume a verdict finding is still present without checking current source.

**Authority:**
- Preauthorized local actions: read repository state and add focused regression tests/probes that document confirmed current behavior
- Stop for: unrelated dirty-file changes, a changed remote base, or any need to alter existing benchmark fixtures outside the declared baseline scope

**Steps:**
- [x] Step 1: Record the exact base commit, current worktree state, and existing completed convergence-plan status without touching unrelated primary-checkout files.
- [x] Step 2: Add adversarial tests for renamed logical/physical bindings, missing applicable dimensions, month/range boundaries, units, and global-contract stage leakage only where current behavior reproduces the issue.
- [x] Step 3: Add or identify direct-boundary tests for provider-free admission, lazy capability activation, cancellation settlement, artifact failure after acceptance, and context disposal.
- [x] Step 4: Freeze the matched benchmark command, workload, environment, and receipt fields used by later optimization tasks.

**Verification:**
- [x] `python -m pytest -q tests/test_analysis_input_contract.py tests/test_workbook_engine.py tests/test_controller_selection.py tests/test_runtime_boundaries.py tests/test_workbook_runner.py`
- Expected: each confirmed P0 has a failing regression test or a recorded source-backed decision that it is already fixed; no unrelated test failure is attributed to this plan.

**Exit Criteria:**
- The baseline and every P0 have an executable proof target, with confirmed fixes separated from hypotheses and no optimization change made.

### Task 2: Compile domain-owned workbook bindings and scope predicates

**Purpose:**
- Make one canonical domain specification compile logical tables, physical selections, canonical columns, applicable dimensions, units, intervals, and comparison rows before parsing/materialization.

**Task Function:**
- Canonical input-contract and layout implementation

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: contract-heavy backend change with focused deterministic tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: validation remains in the task-local backend tests.

**Specification Coverage:**
- Verdict P0 scope and physical-selection findings; `AnalysisInputContract` and `WorkbookContext` single-source ownership.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/domain/analysis_inputs.py:AnalysisInputContract`, `NormalizedIntent.contract_for_domain`
- Modify: `src/foresight_os/domain/analysis_inputs.py:AnalysisInputContract` and the domain-spec owner selected by existing contract ownership; `src/foresight_os/analysis/workbook_inputs.py:WorkbookLayoutSpec`, `ResolvedWorkbookLayout`, `MaterialView`, `resolve_workbook_layout`, `_scope_value`, `_scope_matches`, `_row_matches_scope`, `build_material_view`
- Modify: `src/foresight_os/runtime/local_toolbelt.py:SheetSelection`, `WorkbookReadResult`, `WorkbookContext` only where the compiled physical selection or cancellation boundary requires it
- Verify: `tests/test_analysis_input_contract.py`, `tests/test_workbook_engine.py`, `tests/test_local_toolbelt.py`

**Dependencies:**
- Task 1 baseline tests and current contract inventory.

**Authority:**
- Preauthorized local actions: extend existing input/layout/read owners and add deterministic fixture tests without introducing a second cache or parser
- Stop for: a required behavior that needs a new durable schema, a new provenance format, or silent compatibility fallback not covered by an explicit test

**Steps:**
- [x] Step 1: Define the domain-owned binding model using existing `AnalysisInputContract` data and compatibility defaults; keep `AnalysisInputContract.fingerprint` material-only and expose a separate `analyzer_fingerprint`/`analyzer_version` for stage identity, receipts, metrics, and reuse.
- [x] Step 2: Compile declared logical-to-physical table, sheet, range, and column bindings into one `SheetSelection` before `spreadsheet_read`; let `WorkbookContext.read()` and its reader/preflight verify that requested physical objects exist, then let `ResolvedWorkbookLayout` verify logical bindings and canonical columns without a preliminary metadata-read pass.
- [x] Step 3: Resolve explicit canonical mappings as authoritative; keep generic header inference compatibility-only, and compile predicates with explicit `applicable`, `not_applicable`, and `required_but_missing` states.
- [x] Step 4: Implement interval-aware period/month/range matching, unit filtering, and comparison/baseline retention without treating absent required scope fields as unconstrained.
- [x] Step 5: Preserve source locators and aggregate exclusion diagnostics while keeping the material representation ephemeral.

**Verification:**
- [x] `python -m pytest -q tests/test_analysis_input_contract.py tests/test_workbook_engine.py tests/test_local_toolbelt.py`
- Expected: renamed tables/columns resolve only through declared mappings, invalid explicit selections fail closed, period and unit predicates select the expected rows, and all retained evidence keeps source hashes/locators.

**Exit Criteria:**
- `ResolvedWorkbookLayout` is the only logical-to-physical owner, scope semantics are explicit and deterministic, and all Task 1 input regressions pass.

### Task 3: Enforce one explicit workbook domain per deterministic stage

**Purpose:**
- Separate available contract inventory from stage execution scope and validate deterministic workbook stages during proposal construction and approval.

**Task Function:**
- Recipe admission and stage-contract convergence

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: controller change with approval-fingerprint and recipe compatibility implications.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: proposal and approval tests provide the required contract proof.

**Specification Coverage:**
- Verdict P0 orchestration finding; preservation of research/review executor kinds and approval identity.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/controller/policy.py:stage_requirements`, `stage_analysis_domains`, `stage_contract_fingerprints`
- Inspect: `src/foresight_os/controller/recipes.py:RecipeStage`, recipe serialization and validation
- Modify: `src/foresight_os/controller/policy.py`, `src/foresight_os/controller/recipes.py`, `src/foresight_os/domain/validation.py`, `src/foresight_os/schemas/execution_recipe.schema.json`
- Verify: `tests/test_controller_selection.py`, `tests/test_approval_contract.py`, `tests/test_stage_inputs.py`

**Dependencies:**
- Task 2 canonical domain specification and fingerprints.

**Authority:**
- Preauthorized local actions: update recipe/policy validation and its focused tests while preserving backward-compatible serialization where current callers depend on it
- Stop for: an approval fingerprint migration or recipe schema change that cannot preserve stale-approval rejection and persisted snapshot compatibility

**Steps:**
- [x] Step 1: Keep global contracts available for inventory/default resolution but exclude unrelated global domains from stage execution selection.
- [x] Step 2: Keep the existing `RecipeStage.analysis_domains` wire representation and enforce `deterministic_local => len(stage.analysis_domains) == 1` and `agent/review => stage.analysis_domains == ()`; do not add a parallel singular field.
- [x] Step 3: Use a stage-scoped `AnalysisInputContract.stage_id` as the explicit domain selection. A global contract supplies compatible defaults/inventory only and never selects a stage domain.
- [x] Step 4: Make review/interpretation stages consume committed upstream records and retain their intended agent or review executor kind.
- [x] Step 5: Include the selected domain contract and separate analyzer identity in stage fingerprints and approval projections without copying all global contracts into every stage.

**Verification:**
- [x] `python -m pytest -q tests/test_controller_selection.py tests/test_approval_contract.py tests/test_stage_inputs.py`
- Expected: proposal validation rejects zero or multiple `analysis_domains` for deterministic stages, rejects non-empty domains on agent/review stages, stage-scoped contracts select the domain, unrelated global contracts do not become deterministic, and approved recipe fingerprints change when the selected contract or analyzer identity changes.

**Exit Criteria:**
- Every deterministic stage has one explicit `analysis_domains` entry selected by its stage-scoped contract, every agent/review stage has no analysis domain, and every downstream stage receives only the records and contract identity it is declared to consume.

### Task 4: Complete provider-free approved execution and lazy capability activation

**Purpose:**
- Define the canonical workbook-source binding and make all-local approved recipes execute through the normal gate without a provider client while retaining explicit admission, capability, budget, and external-failure boundaries.

**Task Function:**
- Approved execution boundary implementation

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: high-risk admission/lifecycle change requiring direct integration proof.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct gate integration tests are the authoritative validator.

**Specification Coverage:**
- Verdict P0 provider-free execution and eager-resource findings.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/execution_gate.py:ExecutionGate.admit`, `ExecutionGate.execute`, `_preflight_recipe`
- Inspect: `src/foresight_os/cli.py:execute` command dispatch and `src/foresight_os/runtime/maf_probe.py:build_configured_client`
- Inspect: `src/foresight_os/runtime/workflow.py:run_recipe_async`, capability preparation and stage dispatch
- Modify: `src/foresight_os/runtime/execution_gate.py`, `src/foresight_os/runtime/workflow.py`, `src/foresight_os/runtime/capabilities.py`, `src/foresight_os/cli.py`
- Verify: `tests/test_approval_persistence.py`, `tests/test_approval_contract.py`, `tests/test_runtime_boundaries.py`, `tests/test_cli.py`

**Dependencies:**
- Task 3 explicit stage-domain and contract-fingerprint rules.

**Authority:**
- Preauthorized local actions: change local admission/dispatch and mocked capability activation with no provider authentication or network calls
- Stop for: any need to weaken approval, expose credentials, activate real external providers, or mark blocked external work as successful

**Steps:**
- [x] Step 1: Add one explicit local workbook-source input to the approved execution boundary (`execute --workbook` and a typed `workbook_source` argument); require it for deterministic stages, validate its existence/type during admission, and return `BLOCKED_INPUT` when it is absent or invalid.
- [x] Step 2: Capture the source SHA through the existing `WorkbookContext`/`SourceSnapshot` path once at admission or first read, place that source identity in the deterministic stage fingerprint/receipt, and do not create a second source catalog or hide the binding only in `run_context`; the approved recipe remains source-agnostic and the explicit execute input supplies the source identity for that run.
- [x] Step 3: Permit `client=None` when every stage is deterministic-local; defer `build_configured_client` in `cli.py` behind a lazy factory or equivalent existing boundary until the first external stage requires it.
- [x] Step 4: Keep recipe-wide metadata admission, but activate capabilities/resources at the stage boundary and memoize them in the existing run-owned `CapabilityScope`.
- [x] Step 5: Ensure a completed local stage persists its receipt/result even when a later external stage is `BLOCKED_EXTERNAL`.
- [x] Step 6: Add the credential-free `propose -> approve -> execute --workbook -> committed result` integration test and a lazy-activation test that asserts no provider construction occurred before the external stage.

**Verification:**
- [x] `python -m pytest -q tests/test_approval_persistence.py tests/test_approval_contract.py tests/test_runtime_boundaries.py tests/test_cli.py`
- Expected: all-local approved execution commits a result with `client=None`, external capability creation is absent until required, and blocked external stages preserve truthful status and prior local receipts.

**Exit Criteria:**
- The normal approved execution gate is provider-free for all-local recipes and cannot silently convert unavailable external resources into completion.

### Task 5: Settle blocking workbook execution, cancellation, and artifact failure independently

**Purpose:**
- Run synchronous workbook analysis through the existing bounded worker path, propagate cooperative cancellation, close only owned workbook contexts, and decouple accepted analytical state from report/artifact settlement.

**Task Function:**
- Runtime lifecycle and settlement hardening

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: runtime concurrency and durable-state side effects require high-confidence direct boundary proof.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing runtime boundary and runner lifecycle tests are the required validator.

**Specification Coverage:**
- Verdict P0 runtime, cancellation, resource ownership, and artifact-failure findings.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/executors.py:DeterministicLocalExecutor.execute`, `src/foresight_os/runtime/local_toolbelt.py:_check_cancel`, `WorkbookContext.clear`
- Inspect: `src/foresight_os/runtime/workflow.py:run_recipe_async`, `ensure_not_cancelled`, scope cleanup and stage settlement
- Inspect: `src/foresight_os/analysis/workbook_runner.py:WorkbookWorkflowRunner.run`
- Modify: `src/foresight_os/runtime/executors.py`, `src/foresight_os/runtime/workflow.py`, `src/foresight_os/runtime/local_toolbelt.py`, `src/foresight_os/analysis/workbook_runner.py`, and `src/foresight_os/analysis/review_workflow.py` only where ownership/settlement proof requires it
- Verify: `tests/test_runtime_boundaries.py`, `tests/test_local_toolbelt.py`, `tests/test_workbook_runner.py`, `tests/test_evidence_workflow.py`

**Dependencies:**
- Task 4 approved dispatch and existing worker/cancellation primitives.

**Authority:**
- Preauthorized local actions: use existing bounded worker and cancellation mechanisms, add deterministic mocks, and change local settlement handling without deleting accepted state
- Stop for: a new unbounded executor, forceful thread termination, destructive state recovery, or a change that marks cancellation as success without a settled status

**Steps:**
- [x] Step 1: Dispatch synchronous workbook analysis via the existing bounded blocking-worker mechanism and preserve context propagation.
- [x] Step 2: Propagate typed deterministic outcomes: `engine.cancelled` becomes `RunCanceledError`/the runtime cancellation class, `engine.blocked_input` becomes the typed input/tool admission failure, and `engine.failed` becomes a deterministic execution failure rather than a provider failure.
- [x] Step 3: Pass `cancel_check` through source reads, archive preflight, material view construction, and domain calculations; check before each durable transition.
- [x] Step 4: Define the durable cancellation linearization point: cancellation may abort before `AnalysisStore` commit begins; once the atomic commit begins, it settles and later cancellation cannot rewrite accepted state as cancelled.
- [x] Step 5: Preserve caller cancellation and settle worker cleanup deterministically, including worker failure during cancellation.
- [x] Step 6: Keep `WorkbookContext.clear()` as the existing idempotent lifecycle primitive used by `CapabilityScope.close()`; do not introduce a competing `close()` semantic unless a separate compatibility-safe change is approved.
- [x] Step 7: Split acceptance from report rendering so a render failure keeps `status="accepted"` and returns a separate `artifact_status="failed"` plus artifact error; retries render only the artifact and do not rerun analytical acceptance.

**Verification:**
- [x] `python -m pytest -q tests/test_runtime_boundaries.py tests/test_local_toolbelt.py tests/test_workbook_runner.py tests/test_evidence_workflow.py`
- Expected: cancellation is cooperative and truthful, owned resources close exactly once, borrowed resources remain usable, and accepted state remains loadable after report failure.

**Exit Criteria:**
- Deterministic XLSX execution no longer blocks the async loop, cancellation and cleanup have direct proof, and artifact settlement cannot undo analytical acceptance.

### Task 6: Measure the corrected path and gate material/evidence reductions independently

**Purpose:**
- Attribute the corrected path's remaining cost before choosing among indexed/zero-copy material, rejected-row pruning, or demand-driven evidence.

**Task Function:**
- Corrected-path profiling and independently gated materialization reduction

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: optimization is allowed only after correctness and lifecycle gates, with matched before/after evidence.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: parity tests and benchmark receipts are the validation boundary.

**Specification Coverage:**
- Verdict P1 material/evidence findings; preservation of provenance and deterministic outputs.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/analysis/workbook_inputs.py:MaterialView`, `build_material_view`
- Inspect: `src/foresight_os/domain/models.py:Evidence`, `src/foresight_os/analysis/evidence_workflow.py`, domain `row_evidence` call sites
- Modify: `src/foresight_os/analysis/workbook_inputs.py`, `src/foresight_os/runtime/local_toolbelt.py`, `src/foresight_os/analysis/evidence_workflow.py`, and affected domain analyzers only after Task 1 benchmark identifies the owner of the regression
- Verify: `tests/test_workbook_engine.py`, `tests/test_local_toolbelt.py`, `tests/test_evidence_workflow.py`, all five domain parity test modules, and matched optimization receipts

**Dependencies:**
- Tasks 1–5 complete; correctness and lifecycle tests green. Task 6 measurement must run before any candidate implementation.

**Authority:**
- Preauthorized local actions: implement only benchmark-supported material/evidence reductions with parity fixtures and local benchmark runs
- Stop for: any loss of source locators, hashes, units, calculation inputs, review behavior, or a benchmark result that does not use the frozen matched workload

**Steps:**
- [x] Step 1: Instrument source capture, extraction, layout resolution, material construction, calculations, evidence, state construction, review, serialization, and report boundaries, then run the corrected-path matched baseline.
- [x] Step 2: Implement indexed/zero-copy views and precompiled predicates only if material construction/allocation is a measured significant boundary; otherwise record the candidate as deferred.
- [x] Step 3: Prune ordinary rejected-row provenance only if retained allocation/state evidence justifies it; retain detailed provenance for retained rows and quality failures; otherwise record the candidate as deferred.
- [x] Step 4: Materialize evidence on demand only if evidence construction, state growth, review, or serialization is a measured significant boundary; otherwise record the candidate as deferred.
- [x] Step 5: For each candidate independently implemented, rerun domain parity, provenance, lifecycle, and matched benchmark checks before accepting or reverting that candidate.

**Verification:**
- [x] `python -m pytest -q tests/test_workbook_engine.py tests/test_local_toolbelt.py tests/test_evidence_workflow.py tests/test_portfolio_resilience.py tests/test_supplier_and_ev_resilience.py tests/test_technology_powerbi_validator.py`
- [x] Run the repository's matched PR #35 optimization probe and receipt comparison with identical workload/environment.
- Expected: correctness and provenance remain identical; allocation/state-size/review/persistence metrics improve only where measured; no optimization claim is accepted without matched evidence.

**Exit Criteria:**
- Each material/evidence candidate is independently implemented only when its named boundary is significant, and every non-significant candidate is explicitly deferred with measurement evidence.

### Task 7: Converge analyzer entry points and preserve one reuse authority

**Purpose:**
- Ensure direct analyzers and runtime stages consume the same domain-owned defaults and scoped material. Preserve `StageReceipt` as the sole durable recipe-execution reuse owner; allow standalone reuse only when existing durable metadata already proves the full identity.

**Task Function:**
- Domain entry-point convergence and reuse contract

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: cross-domain compatibility change with invalidation and receipt-reuse risk.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: acceptance, invalidation, and receipt tests are the required validator.

**Specification Coverage:**
- Verdict P1 duplicated defaults, stale paths, safe reuse, and single-source-of-truth findings.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/analysis/workbook_engine.py:WorkbookAnalysisEngine`, `src/foresight_os/analysis/workbook_runner.py:merge_input_contract`
- Inspect: five production analyzers under `src/foresight_os/analysis/`, `src/foresight_os/analysis/result_committer.py`, `src/foresight_os/persistence/analysis_store.py:StageReceipt`, and `src/foresight_os/runtime/workflow.py:_committed_cache_output`, `_canonical_provenance_matches`
- Modify: `src/foresight_os/analysis/workbook_engine.py`, `src/foresight_os/analysis/workbook_runner.py`, the five domain analyzers, `src/foresight_os/analysis/result_committer.py`, and `src/foresight_os/runtime/workflow.py` only where existing receipt semantics need to carry the separate analyzer identity
- Verify: `tests/test_workbook_runner.py`, `tests/test_analysis_input_contract.py`, `tests/test_persistence.py`, `tests/test_execution_persistence.py`, `tests/test_runtime_boundaries.py`, and the five domain test modules

**Dependencies:**
- Tasks 2–6 establish canonical contracts, scoped material, lifecycle settlement, and measured optimization candidates. Task 6 may conclude that no material/evidence optimization should land.

**Authority:**
- Preauthorized local actions: remove duplicated compatibility defaults and use existing receipts/canonical records to verify reuse without bypassing review or acceptance
- Stop for: any proposal to add a standalone reuse index/schema, or any reuse path lacking source/layout/contract/analyzer/dependency identity, current review, committed provenance, or explicit fresh/reaccept behavior

**Steps:**
- [x] Step 1: Make all direct analyzers delegate default/layout/scope decisions to the shared domain specification and consume only scoped material.
- [x] Step 2: Keep compatibility wrappers thin and preserve their public return shapes until parity tests prove removal is safe.
- [x] Step 3: Make recipe execution use `StageReceipt` as the sole durable reuse authority, with source snapshot, resolved layout, material-only input contract, separate analyzer identity, dependency records, invalidation state, and review currentness in its existing matching logic.
- [x] Step 4: For standalone `WorkbookWorkflowRunner`, reuse only when existing `AnalysisState`/`ReviewRecord` metadata already proves that full identity; if it does not, defer standalone reuse rather than add a second persistence schema.
- [x] Step 5: Add explicit fresh/reaccept tests and verify changed source, contract, analyzer, dependency, or review invalidation prevents reuse.

**Verification:**
- [x] `python -m pytest -q tests/test_workbook_runner.py tests/test_analysis_input_contract.py tests/test_analysis_store.py tests/test_runtime_boundaries.py tests/test_portfolio_resilience.py tests/test_supplier_and_ev_resilience.py tests/test_technology_powerbi_validator.py`
- Expected: recipe runs reuse only exact current `StageReceipt` results, standalone reuse is deferred when existing metadata is insufficient, changed identities force fresh work, and all five analyzers preserve existing fixture outputs and evidence locators.

**Exit Criteria:**
- One canonical domain path serves direct and recipe execution; `StageReceipt` remains the sole durable recipe reuse authority; standalone reuse never adds a second schema or bypasses provenance, invalidation, review, or acceptance guards.

### Task 8: Profile persistence, parsing, and dependency surface; apply only measured changes

**Purpose:**
- Investigate remaining XLSX p95/cold latency, state-growth, and dependency-surface causes independently, then apply only changes whose evidence improves the owned target or proves a deployment/maintenance boundary without weakening correctness.

**Task Function:**
- Performance diagnosis and bounded cleanup

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: performance work requires named workload, metric, threshold owner, and regression proof.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: benchmark receipts and repository tests provide the validation boundary.

**Specification Coverage:**
- Verdict P1/P2 profiling, persistence, parsing, optional dependency, double-load, and maintenance findings.

**Required Skills:**
- `skill-performance-optimization`

**Files And Symbols:**
- Inspect: `src/foresight_os/persistence/analysis_store.py`, `src/foresight_os/runtime/local_toolbelt.py:spreadsheet_read`, `pyproject.toml`
- Modify: `evaluation/probes/optimization_measurement.py`, `evaluation/probes/run_optimization_probe.py`, `evaluation/probes/compare_optimization_receipts.py`, `pyproject.toml`, and owning code only for a measured candidate
- Verify: `tests/test_persistence.py`, `tests/test_execution_persistence.py`, `tests/test_local_toolbelt.py`, `pyproject.toml` dependency declarations, and the matched benchmark receipt set

**Dependencies:**
- Tasks 1 and 6 provide instrumented boundaries and a valid post-correctness baseline.

**Authority:**
- Preauthorized local actions: run local profiling/benchmarking and make small measured optimizations with regression tests
- Stop for: unmeasured persistence protocol changes, parser replacement, process isolation, dependency removal without import/runtime proof, or a result below the owned threshold

**Steps:**
- [x] Step 1: Attribute XLSX p95 and cold regressions separately to source capture/hash, archive preflight, formula/cached loads, extraction, layout/material, calculations, evidence, state, review, persistence, and report boundaries.
- [x] Step 2: Profile pending/review/commit serialization before changing write protocol.
- [x] Step 3: Revisit the second XLSX load only if cold parsing remains a dominant measured cost after Tasks 2 and 6.
- [x] Step 4: Verify provider/agent imports are optional and lazy for local execution; accept that maintenance/deployment improvement on import-isolation and package tests even if XLSX p95 is unchanged. Verify whether `pandas` has no runtime or dynamic consumer before removing or changing the dependency.
- [x] Step 5: Record accepted and deferred candidates in receipts with correctness, resource, lifecycle, and optimization dimensions separated.

**Verification:**
- [x] Run the matched optimization probe and receipt comparison used in Task 1.
- [x] `python -m pytest -q`
- Expected: any accepted optimization has identical workload/environment evidence, passes correctness/resource/lifecycle checks, and does not hide a regression behind a single aggregate latency number.

**Exit Criteria:**
- Remaining performance work is either measured and implemented with proof or explicitly deferred with the diagnostic evidence that ruled it out.

### Task 9: Reconcile documentation and perform final verification

**Purpose:**
- Align maintained guidance, plan evidence, and repository verification with the implemented canonical path and explicit deferrals.

**Task Function:**
- Documentation and completion reconciliation

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: documentation and final verification are bounded after implementation fan-in.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification skill owns completion evidence.

**Specification Coverage:**
- Repository verification requirements, documentation ownership, and final release criteria from the verdict.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `README.md`, `docs/architecture.md`, `docs/getting-started.md`, `docs/evidence-and-evaluation.md`, `evaluation/README.md`
- Modify: only the maintained documentation files whose behavior changed, plus this plan's task evidence and deferral record
- Verify: `scripts/check_markdown_links.py`, repository status, declared-target diff, and all final commands below

**Dependencies:**
- Tasks 1–8 complete, including recorded deviations and deferred candidates.

**Authority:**
- Preauthorized local actions: update maintained documentation and run fresh local verification against the final diff
- Stop for: any missing required proof, stale plan status, undocumented scope deviation, or request for Git publication/merge

**Steps:**
- [x] Step 1: Document the canonical workbook path, explicit stage-domain rule, provider-free execution boundary, cancellation/settlement behavior, and compatibility deferrals.
- [x] Step 2: Reconcile all task checkboxes, benchmark receipts, deviations, and deferred optimizations against current source/tests.
- [x] Step 3: Run final verification and report structural proof separately from provider availability, human acceptance, and unmeasured performance claims.

**Verification:**
- [x] `python -m pytest -q`
- [x] `python -m compileall -q src tests evaluation`
- [x] `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/getting-started.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- [x] `git diff --check`
- Expected: all required checks pass, links resolve, the final diff contains only declared changes, and the plan remains `proposed` until a separate completion-verification step returns `verified`.

**Exit Criteria:**
- The implementation is ready for `skill-verification-before-completion`; no required task, proof, deviation, or deferral is unresolved.

## Verification

Final artifact verification is one fresh post-fan-in pass:

- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/getting-started.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- `git diff --check`
- matched before/after benchmark receipt comparison for the frozen workbook workload
- dedicated-worktree `git status --short --branch` and declared-target diff inspection

## Execution Evidence And Deferrals

- Focused and full test suites pass, including workbook scope/layout, provider-free
  approved execution, cancellation settlement, artifact failure, persistence,
  receipt reuse, and all five production XLSX analyzer fixtures.
- Fresh matched receipts are stored at `work/optimization-baseline/receipt.json`,
  `work/optimization-release/receipt.json`, and
  `work/optimization-comparison.json`. The comparator accepted the matched run:
  correctness, allocation, resource, lifecycle, native MCP, and soak dimensions
  are `VERIFIED`; XLSX p95 changed by `+3.503%` and peak allocation by `0.0%`.
- No material/evidence optimization was accepted. The selected
  `public_workflow_context_reuse` candidate remains `NOT_MEASURED`, and the
  cold-workbook path is noisy and above its local timing-path threshold; no
  single receipt is treated as an optimization claim.
- Persistence protocol changes, parser replacement, process isolation, pandas
  removal, and ordinary rejected-row provenance pruning remain explicitly
  deferred because the matched evidence did not establish a justified benefit.

Structural correctness, lifecycle settlement, resource safety, human acceptance,
provider availability, and performance optimization claims must be reported as
separate evidence dimensions. A passing test suite alone does not establish an
optimization claim.

## Completion Criteria

The plan is ready for completion verification when:

1. Every deterministic workbook stage uses exactly one existing `analysis_domains` entry selected by a stage-scoped contract, every explicit workbook binding fails closed when missing, and every deterministic execution has one explicit validated workbook source.
2. Canonical mappings drive scope predicates with explicit dimension applicability, interval-aware periods, unit filtering, and preserved comparison/validation inputs.
3. Provider-free approved execution completes all-local recipes through committed analytical state without constructing external providers.
4. External capabilities activate only at stage boundaries, and blocked external stages remain truthful without erasing completed local receipts.
5. Blocking workbook work uses the bounded worker path, cancellation settles cooperatively, and owned contexts close without closing borrowed contexts.
6. Accepted analytical state survives report/artifact failure with `status="accepted"` plus a separate artifact outcome and remains reviewable/reusable under existing invalidation rules.
7. Material/evidence candidates are independently measured and gated; recipe reuse remains owned by `StageReceipt`; standalone reuse is deferred when existing metadata is insufficient; persistence, parsing, and dependency changes are backed by parity/matched evidence or explicit deferrals.
8. All five production XLSX analyzers use the canonical path without duplicated scope/default decisions, while compatibility entry points remain stable until parity proves removal safe.
9. Focused tests, full tests, compilation, Markdown-link checks, diff checks, benchmark receipts, documentation, and plan state agree with repository truth.

Approved deferrals unless later evidence changes their priority:

- Do not introduce a second cache, parser, orchestration layer, analytical store, or provenance format.
- Keep the CSV vertical-slice path as compatibility/demo behavior until a separate approved scope removes it.
- Do not replace the XLSX parser, change persistence write protocol, add process isolation, or remove `pandas` solely from intuition.
- Do not claim optimization from a single aggregate p95, cold-run, or reuse measurement without correctness and matched-environment evidence.

The plan may be marked `completed` only after
`skill-verification-before-completion` returns `verified`; checked boxes are
progress records, not proof.

## Self-Review

- Verdict coverage: P0 scope/layout, stage-domain, source binding, provider-free gate, lazy capability, cancellation, and artifact-settlement findings map to Tasks 2–5; P1/P2 optimization, reuse, persistence, and dependency findings map to Tasks 6–8; repository and documentation requirements map to Tasks 1 and 9.
- Ownership: `AnalysisStore` remains the durable owner; `WorkbookContext` owns source capture/read state; `workbook_inputs.py` owns layout/material resolution; `workbook_engine.py` remains pure; `workbook_runner.py` owns lifecycle; controller/runtime own admission and capability policy.
- Ordering: baseline and correctness precede optimization; stage and gate semantics precede runtime settlement; corrected-path measurement precedes each material/evidence candidate; analyzer convergence and existing receipt reuse follow those measurements; persistence/parser/dependency profiling remains last and measurement-gated.
- Scope: no task introduces a parallel cache, parser, orchestration layer, analytical store, or provenance format; CSV compatibility remains deferred.
- Proof: every material backend task names focused direct-boundary tests, and final verification separates structural, lifecycle, resource, acceptance, provider, and performance evidence.
