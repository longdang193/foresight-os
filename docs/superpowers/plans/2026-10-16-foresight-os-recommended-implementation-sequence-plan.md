---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: foresight-os-recommended-implementation-sequence
targets:
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/runtime/capabilities.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/runtime/execution_gate.py
  - src/foresight_os/runtime/participants.py
  - src/foresight_os/controller/policy.py
  - src/foresight_os/controller/recipes.py
  - src/foresight_os/controller/proposal.py
  - src/foresight_os/domain/models.py
  - src/foresight_os/domain/validation.py
  - src/foresight_os/analysis/result_committer.py
  - src/foresight_os/analysis/evidence_workflow.py
  - src/foresight_os/analysis/independent_validation.py
  - src/foresight_os/analysis/foresight_validator.py
  - src/foresight_os/analysis/workbook_inputs.py
  - src/foresight_os/persistence/analysis_store.py
  - src/foresight_os/persistence/recovery.py
  - src/foresight_os/persistence/invalidation.py
  - src/foresight_os/runtime/orchestration.py
  - src/foresight_os/controller/budgets.py
  - src/foresight_os/runtime/metrics.py
  - src/foresight_os/domain/challenge.py
  - tests/test_local_toolbelt.py
  - tests/test_orchestration_patterns.py
  - tests/test_result_committer.py
  - tests/test_runtime_boundaries.py
  - tests/test_capabilities.py
  - tests/test_selective_reuse.py
  - tests/test_stage_inputs.py
  - tests/test_controller_selection.py
  - tests/test_execution_gate.py
  - tests/test_review_hardening.py
  - tests/test_participant_scope.py
  - tests/test_work_brief_compatibility.py
  - tests/test_technology_powerbi_validator.py
  - tests/test_persistence.py
  - tests/test_invalidation.py
  - tests/test_optimization_measurement.py
  - tests/test_markdown_links.py
  - docs/architecture.md
  - docs/evidence-and-evaluation.md
  - README.md
  - evaluation/README.md
  - .github/workflows/ci.yml
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/compare_optimization_receipts.py
  - evaluation/probes/optimization_measurement.py
---

# ForesightOS Recommended Implementation Sequence

## Goal

Adopt the supplied verdict as a bounded architecture-simplification program:
preserve source identity, provenance, calculation semantics, review,
invalidation, human acceptance, cancellation, resource ownership, and the
existing Microsoft Agent Framework boundary while reducing duplicate owners,
repeated normalization, broad recovery, unnecessary source movement, and
unmeasured workbook work.

Implementation is authorized only in the isolated worktree recorded below. This
plan does not authorize publication, provider calls, commits, or deletion of
unrelated worktree files.

## Review Of The Verdict

### Adopted conclusions

- Typed participant synthesis, recovery breadth, and setup-time resource
  ownership are correctness and operational concerns, not optional polish.
- Source identity must describe the exact bytes analyzed; live reads, pinned
  reads, currentness checks, and new captures need explicit semantics.
- `AnalysisState`/`AnalysisStore` remain the durable analytical authority.
- The ordinary execution path should be Direct or Sequential; advanced
  patterns remain explicit opt-in paths.
- Workbook reuse must be measured on the production investigation path before
  any deeper parsed-workbook representation is introduced.

The executable dependency order is `Task 1 → Task 2 → Task 3 → Task 6 → Task 4
→ Task 5 → Task 7 → Task 8`: correctness and lifecycle closure come first,
then workbook integration and measurement, then controller/synthesis
simplification, cleanup, and final verification. Task numbering remains stable
for the existing handoff ledger.

### Required corrections before execution

- The supplied critique refers to a newer merged `main` than this planning
  checkout. Task 1 therefore performs only a bounded drift check before
  implementation: confirm the current merged `HEAD`, confirm the named owners
  still exist, and reproduce the focused regressions. Do not repeat a
  repository-wide architecture investigation or infer that newer owners are
  absent from the implementation target based on this stale checkout.
- `RecipeStage` is the strongest runtime plan candidate, but `ExecutionRecipe`
  still owns serialized top-level compatibility fields and approval fingerprints.
  Migration must preserve that boundary rather than rewrite the schema at once.
- The current workbook path already has `WorkbookReadCache` and process-global
  authority maps. Release C must consolidate them through the existing workbook
  session plan, not add a second cache, registry, or parsed-workbook store.
- Domain contract validation must remain separate from generic workbook parsing:
  brief/analysis contracts belong to domain or analyzer owners; generic source,
  selection, bounds, formula/cache, and provenance checks belong to the toolbelt.
- There must be exactly one source-capture implementation. Task 2 owns the
  byte-exact `SourceSnapshot`/captured-source primitive; Task 6 wraps it in a
  run-owned `WorkbookContext` and must not reimplement capture.
- Baseline measurement precedes optimization. No performance claim is accepted
  without matched workload, fixture, environment, implementation identity, and
  correctness evidence.

### Refinements from the latest verdict

- Treat the reproduced hidden-row cache alias (`10` returned instead of `30`)
  as a Release A correctness gate, not a performance observation. The cache
  key must include an immutable workbook-view identity and may not use only
  `TypedTable.id`.
- Make `WorkbookViewIdentity`/`material_fingerprint` explicit: source digest,
  canonical selection, hidden-sheet/row policy, selected ranges/tables, and
  parser/schema interpretation must distinguish material views while physical
  cell provenance remains separate.
- Make snapshot-only validation explicit: ZIP inspection, size checks, parsing,
  formula/cache inspection, and provenance all consume captured bytes. Reopening
  the mutable source is allowed only for an explicit currentness check.
- Keep one pinned source version per locator per run. A new live version begins a
  new admitted source/context path rather than turning `WorkbookContext` into a
  version registry.
- Make retention publication transactional: compute privately, check
  cancellation/budget/context state, then publish cache and authority entries
  atomically; failed, cancelled, over-budget, or closed-context work publishes
  no reusable state.
- Keep both semantic `openpyxl` loads when formula truth requires them; the
  consolidation removes duplicate source capture and extraction, not the
  formula/data-only distinction.
- Treat the existing `NormalizedIntent` and `AnalysisInputContract` owners on
  the current merged `main` as canonical. Do not reinterpret raw brief/stage
  inputs in the controller or create parallel models; if the bounded drift check
  finds a different owner, stop and reconcile the plan before implementation.
- Cancellation proof must assert that worker settlement completes and the
  caller still receives `asyncio.CancelledError`; a converted success or
  generic failure is not acceptable.
- Analyst-to-validator extraction reuse is a hard structural gate for identical
  snapshot/selection/limits: zero new captures, source hashes, and XLSX parses,
  with at least one read-cache hit. Timing is informative only when its baseline
  is reliable; noisy timing must not block a correctness release.
- Keep runtime completion, pending persistence, and accepted analytical state
  distinct. A late cleanup failure must remain visible in run status without
  mutating an already accepted revision.

## Implementation Outcomes

### Release A — correctness and ownership

The system captures and hashes exactly the bytes it analyzes, validates
workbook contracts before expensive work, keeps live and pinned semantics
distinct, prevents resource creation outside the cleanup boundary, and
publishes accepted analytical state transactionally.

### Release B — execution simplification

The controller consumes one normalized policy input, resolves one canonical
stage plan, computes stage identity once from relevant inputs, passes canonical
dependency references instead of copying records, and performs bounded typed
synthesis with typed failure classes and targeted correction.

### Release C — measured workbook reuse

One run-owned workbook context supports one pinned immutable source version per
locator, bounded same-snapshot reuse, multiple-workbook accounting, bounded
reads, and shared deterministic extraction for analyst and validator paths.

### Release D — maintenance reduction

Compatibility owners, duplicate authority probes, CI duplication, and stale
architecture guidance are reduced only after Releases A–C are proven. No new
store, registry, recovery engine, orchestration framework, or persistent parsed
workbook database is introduced.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-plan-document-reviewer`, `skill-executing-plans`, `skill-backend-verification`, `skill-test-driven-development`, `skill-performance-optimization`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: isolated native worktree at `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\recommended-sequence-followup\foresight-OS`
- Commit policy: `no commits during execution unless separately approved`
- Preauthorized local actions: inspect declared source/tests/docs, edit declared plan and implementation files during approved execution, run declared local checks, preserve unrelated user files
- User-approval actions: branch/worktree creation, commits, pushes, merges, external provider calls, destructive cleanup, and compatibility-data deletion
- Parallel ownership: none; shared controller, workbook, persistence, and cleanup contracts require serialization
- Sequential fallback: execute Tasks 1, 2, 3, 6, 4, 5, 7, and 8 in that order

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/recommended-sequence-followup`
- Base commit: `1e76c2e4242b42f3bcbccd8a4b5551782f86a733` (`origin/main` at execution preparation)
- Expected workspace: isolated worktree; preserve unrelated user artifacts in the primary checkout and any pre-existing task-owned worktree files
- Next action: branch finishing is eligible after the verified handoff; publication and merge remain Git disposition actions
- Blockers: `none; commit, push, merge, provider calls, and destructive cleanup remain separately authorized actions`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | isolated implementation workspace | `lead controller` | none | matched baseline receipt | `work/optimization-baseline/receipt.md`; focused tests passed |
| Task 2 | `completed` | isolated implementation workspace | `lead controller` | Task 1 | Release A boundary tests | `work/optimization-baseline/task-2-tests.txt`; focused suite passed |
| Task 3 | `completed` | isolated implementation workspace | `lead controller` | Task 2 | lifecycle/publication tests | `work/optimization-baseline/task-3-tests.txt`; focused suite passed; workbook rollback regression passed |
| Task 6 | `completed` | isolated implementation workspace | `lead controller` | Tasks 2–3 | matched reuse comparison | `work/optimization-baseline/task-6-tests.txt`; `task-6-structural-receipt.json`; structural gates passed; latency/resource soak not measured |
| Task 4 | `completed` | isolated implementation workspace | `lead controller` | Tasks 3 and 6 | controller/fingerprint tests | `work/optimization-baseline/task-4-tests.txt`; suite passed |
| Task 5 | `completed` | isolated implementation workspace | `lead controller` | Tasks 3, 4, and 6 | synthesis/recovery tests | `work/optimization-baseline/task-5-tests.txt`; suite passed |
| Task 7 | `completed` | isolated implementation workspace | `lead controller` | Tasks 4–6 | maintenance/docs/CI checks | `work/optimization-baseline/task-7-verification.txt`; active compatibility owners retained; optional cleanup deferred |
| Task 8 | `completed` | isolated implementation workspace | `lead controller` | Tasks 2–7 | full verification | `work/optimization-baseline/final-pytest.txt`; compileall, Markdown links, diff check, and final scope inspection passed |

## Task Breakdown

### Task 1: Freeze scope and establish a matched baseline

**Purpose:**
- Convert the verdict into measurable acceptance gates, confirm the implementation
  base, and protect unrelated working-tree artifacts before implementation begins.

**Task Function:**
- Perform a bounded pre-execution drift check, reproduce focused regressions, and
  record matched baseline workbook measurements; do not repeat a repository-wide
  architecture study.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: repository-wide scope and dirty workspace require one owner
  to establish authoritative baseline evidence.

**Validator Profile:**
- Controller-selected: `none`

**Specification Coverage:**
- Measurement-first optimization, preserved invariants, explicit non-goals, and
  separation of structural proof from model quality.

**Required Skills:**
- `skill-performance-optimization`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/workflow.py:_synthesize_stage_outputs`
- Inspect: `src/foresight_os/runtime/local_toolbelt.py:WorkbookReadCache`,
  `_sha256_file`, `spreadsheet_read`, `data_analysis`, `calculation`
- Inspect: `src/foresight_os/runtime/capabilities.py:CapabilityScope`
- Inspect: `src/foresight_os/controller/policy.py:select_recipe` and
  `src/foresight_os/controller/recipes.py:RecipeStage`
- Inspect: `src/foresight_os/analysis/result_committer.py` and
  `src/foresight_os/persistence/analysis_store.py`
- Inspect: `src/foresight_os/analysis/foresight_validator.py:validate_exercises`
  and `src/foresight_os/runtime/orchestration.py:RunControl`
- Verify: `tests/test_optimization_measurement.py` and the existing workbook
  session plan at `docs/superpowers/plans/2026-10-15-22-36-foresight-os-workbook-session-reuse-plan.md`

**Dependencies:**
- None. Source and tests are authoritative over the verdict where they differ.

**Authority:**
- Preauthorized local actions: inspect source, tests, docs, Git status, and
  existing receipts; write only baseline evidence in the implementation workspace
- Stop for: external execution, destructive cleanup, or a baseline that cannot
  distinguish cold, warm, currentness, and full-investigation costs

**Steps:**
- [ ] Step 1: Start from current merged `main`, record the actual base SHA, and
  confirm only the named owners and focused regression locations still exist. If
  the checkout is stale or an owner has drifted, stop and reconcile the plan
  before implementation; do not repeat the full architecture investigation.
- [ ] Step 2: Confirm the direct callers needed for source identity, workbook
  reads, controller policy, typed synthesis, recovery, persistence, resource
  cleanup, and publication so later tasks have verified write ownership.
- [ ] Step 3: Record fixture hashes, dependency versions, environment,
  implementation identity, dirty paths, and current correctness results.
- [ ] Step 4: Measure representative cold read, same-view repeat, different
  selection, analyst-to-validator extraction, currentness check, cancellation,
  multiple workbooks, repeated investigation, and end-to-end time to a usable
  result. Prefer external or harness measurement for baseline; if runtime
  counters are added, use equivalent instrumentation for baseline and release
  and separate `capture_hash_count`, `currentness_hash_count`,
  `xlsx_parse_count`, `openpyxl_load_count`, and `cache_hits`.
- [ ] Step 5: Reproduce the hidden-row cache-alias fixture and record the
  expected distinct outputs before changing the cache. The release gate is
  that the two views cannot return one another's result.
- [ ] Step 6: Freeze non-goals: no distributed cache, parsed-workbook database,
  filesystem watcher, second analytical store, generic recovery engine, new
  orchestration pattern, or source registry.

**Verification:**
- [ ] `python -m pytest -q tests/test_optimization_measurement.py tests/test_controller_selection.py tests/test_execution_gate.py`
- Expected: baseline evidence is deterministic, redacted, and labels missing
  external or human-quality evidence as unavailable rather than passing; the
  production path is identified before optimization changes begin.

**Exit Criteria:**
- Baseline schema, workload, fixture, environment, and correctness gates are
  fixed for later comparison.

### Task 2: Make source capture and analysis contracts correct

**Purpose:**
- Implement Release A exact source identity, live/pinned semantics, hardened
  input contracts, and removal of redundant domain pre-hashes.

**Task Function:**
- Add one cancellable `SourceSnapshot`/captured-source primitive, while keeping
  domain contract validation, analyzer mappings, and generic workbook parsing
  in their respective canonical owners.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: provenance and trust-boundary changes stay in canonical
  local toolbelt/domain owners.

**Validator Profile:**
- Controller-selected: `none`

**Specification Coverage:**
- Exact SHA identity, immutable workbook-view/material identity,
  formula/cache semantics, cell/range provenance, live vs pinned reads,
  immutable approved inputs, explicit mapping/unit/policy failures, and exactly
  one source-capture implementation.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`,
  `skill-code-standards`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/local_toolbelt.py:WorkbookReadCache`,
  `_sha256_file`, `spreadsheet_read`, `SheetSelection`, `AnalysisOperation`,
  `UnitSpec`, `WorkbookReadResult`, and the canonical
  `WorkbookViewIdentity`/`material_fingerprint` owner after Task 1 drift check
- Modify: `src/foresight_os/domain/models.py` and
  `src/foresight_os/domain/validation.py` only as compatibility adapters around
  the existing `AnalysisInputContract` owner; do not add another model
- Modify: `src/foresight_os/analysis/evidence_workflow.py:run_xlsx_finding_workflow`
- Modify: `src/foresight_os/analysis/independent_validation.py` source-read and
  extraction entry points
- Modify: `src/foresight_os/analysis/foresight_validator.py:validate_exercises`
  and `_row_evidence` only to consume the admitted workbook identity
- Modify only where baseline confirms overlap: `portfolio_resilience.py`,
  `supplier_resilience.py`, `technology_radar.py`, `ev_capacity_investment.py`,
  and `powerbi_strategic_portfolio.py`
- Verify: `tests/test_local_toolbelt.py`, `tests/test_evidence_workflow.py`,
  `tests/test_ncc_independent_validation.py`, and portability tests

**Dependencies:**
- Task 1 baseline and owner map.

**Authority:**
- Preauthorized local actions: add the single source primitive, harden the
  existing input/mapping owners, and add focused tests while preserving public
  toolbelt payloads and formula/cache trust
- Stop for: metadata-only identity, silent pinned refresh, a persistent source
  registry, weakened provenance, generic-reader/domain coupling, or an untested
  parallel contract layer

**Steps:**
- [ ] Step 1: Add or harden exactly one immutable captured-source representation
  owned by the toolbelt; capture must stream chunks with cancellation checks and
  reject `max_bytes` before retaining an oversized source. Its SHA, byte count,
  and bytes/file are the inputs to ZIP inspection, size validation, parsing,
  formula/cache inspection, and provenance. Add or harden one immutable
  `WorkbookViewIdentity`/
  `material_fingerprint` containing source digest, canonical selection,
  hidden-sheet/row policy, selected ranges/tables, and parser/schema
  interpretation. Do not use caller-supplied `TypedTable.id` alone and do not
  add a run-level cache/context here.
- [ ] Step 2: Make live reads, pinned reads, explicit currentness checks, and
  new captures distinct. Repeated live reads must not silently reuse a pinned
  version. Allow at most one pinned source version per locator per run; a new
  live version starts a new admitted source/context path rather than an implicit
  in-context version registry. Task 6 must wrap this primitive rather than
  reimplement capture.
- [ ] Step 3: Check cancellation during capture, hashing, preflight, and parse;
  do not publish a read or trusted result after cancellation or source change.
- [ ] Step 4: Harden the existing canonical analysis-input contract: deep-freeze
  nested mappings, conversion rates, limits, and policy values; validate period
  syntax, month/calendar ranges, units/currency, duplicate/missing-value
  policies, and supported calculations/checks before expensive parsing. Strengthen
  the existing `AnalysisInputContract` owner rather than creating a second
  contract; if Task 1 finds a different owner on merged `main`, stop and
  reconcile the plan before implementation.
- [ ] Step 5: Keep explicit column mappings and required tables in analyzer/input
  owners, where missing or ambiguous mappings fail explicitly with a stable
  `MISSING_MAPPED_COLUMN`-class result. Explicit configuration must be exact or
  fail; legacy defaults are compatibility-only when configuration is omitted and
  must never replace invalid explicit configuration. Keep generic
  `local_toolbelt.py` validation limited to source, selection, range/table
  bounds, resource limits, formula/cache semantics, parsing, and provenance.
- [ ] Step 6: Remove redundant pre-hashes from every production workbook
  analyzer and validator only after capture is authoritative; retain currentness
  hashes where the trust boundary requires a fresh check.
- [ ] Step 7: Add the race regression: capture source A, replace the live path
  with B, analyze the pinned snapshot, and prove SHA, parsed values, ZIP/preflight,
  and provenance remain A while `check_current(snapshot)` reports stale.

**Verification:**
- [x] Focused workbook/contract/validator suite passed; this checkout uses `tests/test_supplier_and_ev_resilience.py` and has no standalone `test_technology_radar.py` or `test_ev_capacity_investment.py`.
- Expected: provenance is exact, invalid contracts fail early, formula/cache
  behavior is unchanged, explicit mappings/policies fail clearly, legacy
  defaults remain compatibility-only, the hidden-row cache views cannot alias,
  hidden-sheet/range and equivalent-selection identities remain distinct or
  equivalent as appropriate, source-version changes and reused caller IDs
  cannot authorize stale hits, join inputs participate in identity, and
  cancellation/source mutation cannot publish trusted output.

**Exit Criteria:**
- Every trusted workbook result has byte-exact identity and explicit read
  semantics; verified paths have no duplicate domain pre-hash.

### Task 3: Close ownership and publication boundaries

**Purpose:**
- Finish Release A lifecycle guarantees: admission before resource creation,
  setup inside cleanup boundaries, worker settlement, and transactional publication.

**Task Function:**
- Make the run/scope owner explicit and prove no worker can publish into a closed
  scope or leave resources behind.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: lifecycle changes cross runtime, capability, persistence,
  and result-commit boundaries and require serialized ownership.

**Validator Profile:**
- Controller-selected: `none`

**Specification Coverage:**
- Cancellation/resource ownership, setup-time cleanup holes, worker settlement
  before workbook cleanup, transactional retained-state publication, separate
  run outcome versus durable acceptance, and publication atomicity.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/capabilities.py:CapabilityScope`,
  `CapabilityResolver.resolve_async`, `prepare_capability_context`
- Modify: `src/foresight_os/runtime/workflow.py:run_recipe_async`,
  `_close_agents`, stage dispatch, and final cleanup
- Modify: `src/foresight_os/runtime/execution_gate.py` admission/setup ordering
- Modify: `src/foresight_os/analysis/result_committer.py` publication boundary
- Modify only where required: `src/foresight_os/persistence/analysis_store.py`
- Verify: `tests/test_capabilities.py`, `tests/test_runtime_boundaries.py`,
  `tests/test_result_committer.py`, `tests/test_persistence.py`,
  `tests/test_invalidation.py`

**Dependencies:**
- Task 2 source and cancellation semantics.

**Authority:**
- Preauthorized local actions: adjust setup, settlement, cleanup, and commit
  sequencing with direct boundary tests
- Stop for: deletion of durable state, changed acceptance semantics, external
  publication, or a second persistence owner

**Steps:**
- [ ] Step 1: Perform resource-free static admission first. Defer any
  resource-backed capability validation until the owned runtime scope exists,
  then register every successfully created owned resource immediately.
- [ ] Step 2: Reserve preventive budget capacity before dispatch and before
  retaining result/resource state. For cache, authority, and receipt retention,
  compute privately, check cancellation/budget/context-open state, then publish
  atomically; failed, cancelled, over-budget, or closed-context work publishes
  no new reusable entry, authority record, or receipt.
- [ ] Step 3: Stop new admission, signal cancellation, settle workers/futures,
  shut down executors, close workbook contexts, then close remaining resources.
- [ ] Step 4: Re-raise `asyncio.CancelledError` after worker settlement rather
  than converting cancellation into success or a generic failure; add a direct
  regression test for a blocking local capability and a staged workflow.
- [ ] Step 5: Prevent writes to closed scopes and prevent cleanup failures from
  being reported as accepted publication.
- [ ] Step 6: Preserve atomic pending/accepted transitions through existing
  `AnalysisStore` and result committer; keep runtime completion, pending
  persistence, and accepted analytical state distinct. A late cleanup failure
  remains visible in run status and does not mutate an already accepted revision;
  if the current policy requires acceptance after cleanup, move the existing
  acceptance transition to that boundary rather than adding a status-only flag.
  Add no parallel store.

**Verification:**
- [x] `python -m pytest -q tests/test_capabilities.py tests/test_runtime_boundaries.py tests/test_result_committer.py tests/test_persistence.py tests/test_invalidation.py`
- Expected: setup failures clean up partial resources, workers settle before
  cleanup completes, blocking cancellation still raises
  `asyncio.CancelledError` after settlement, closed scopes reject publication,
  budget failures publish no reusable receipt or retained cache/authority state,
  and accepted state is written only after validation. Cover worker failure
  during cancellation settlement, repeated cancellation during settlement and
  cleanup, partial setup failure, post-close wrapper calls, cleanup failure,
  primary-plus-cleanup failure, and context closure during publication.

**Exit Criteria:**
- Ownership starts before creation, ends after settlement, and publication is
  atomic and failure-aware.

### Task 4: Normalize controller policy and canonicalize stage identity

**Purpose:**
- Implement Release B single policy input, Direct/Sequential default, one
  canonical stage plan, and relevant-only stage fingerprints without breaking
  recipe/approval compatibility.

**Task Function:**
- Make the repository's existing `normalize_work_brief()` → `NormalizedIntent`
  boundary authoritative for recipe selection and reuse. The controller must
  not reinterpret raw `WorkBrief`, `ExecutionIntent`, or stage structures after
  normalization.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: policy is centralized but still derives facts from multiple
  structures; this is a controller-owner refactor.

**Validator Profile:**
- Controller-selected: `none`

**Specification Coverage:**
- Existing `NormalizedIntent` as the sole controller-policy input, `RecipeStage`
  as runtime plan, Direct/Sequential defaults, one stage identity, and
  relevant-only contract fingerprints.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Modify: `src/foresight_os/controller/policy.py:select_recipe`,
  `_recipe_for_patterns`, and normalization boundary
- Modify: `src/foresight_os/controller/recipes.py:StageInput`, `RecipeStage`,
  `ExecutionRecipe`, `make_recipe`
- Modify: `src/foresight_os/controller/proposal.py:build_execution_recipe`,
  `validate_execution_recipe_contract`
- Modify: `src/foresight_os/runtime/execution_gate.py` and the existing
  `NormalizedIntent`/`normalize_work_brief()` owner
- Modify: `src/foresight_os/runtime/workflow.py:_stage_fingerprints`,
  `_stage_cache_key`, and stage context construction
- Verify: `tests/test_controller_selection.py`, `tests/test_stage_inputs.py`,
  `tests/test_selective_reuse.py`, `tests/test_approval_contract.py`,
  `tests/test_execution_approval_fingerprint.py`

**Dependencies:**
- Task 3 publication and lifecycle boundaries; Task 6 workbook integration and
  measured reuse. Execute this task after Task 6 even though its stable task
  number is lower than Task 6.

**Authority:**
- Preauthorized local actions: migrate selection and fingerprints to the existing
  normalization path and add narrow compatibility translation at the recipe
  serialization boundary while preserving
  serialized recipes, approval fingerprints, explicit overrides, and review-required topology
- Stop for: removing persisted fields, making advanced patterns implicit, or
  changing user-authorized topology without focused compatibility proof

**Steps:**
- [ ] Step 1: Use the existing `normalize_work_brief()` → `NormalizedIntent`
  boundary as the only controller-policy input and verify it contains every
  datum currently required from `WorkBrief`, `ExecutionIntent`, `TaskShape`, and
  `WorkStage`. If the refreshed base does not contain that owner, stop and
  reconcile the plan before implementation rather than introducing a fallback
  normalization model.
- [ ] Step 2: Make `select_recipe` consume the normalized intent once, preserve
  explicit user topology overrides and review constraints, and default ordinary
  work to Direct or Sequential.
- [ ] Step 3: Compute `StageIdentity` once from relevant input, capabilities,
  review policy, limits, and dependencies. Stage contract fingerprints must be
  limited to contracts directly used by the stage plus contracts of declared
  dependencies; unrelated contract changes must not invalidate the stage.
- [ ] Step 4: Keep `ExecutionRecipe` serialization as a compatibility boundary
  until approval and receipt consumers are migrated and tested.

**Verification:**
- [x] `python -m pytest -q tests/test_controller_selection.py tests/test_stage_inputs.py tests/test_selective_reuse.py tests/test_approval_contract.py tests/test_execution_approval_fingerprint.py tests/test_execution_gate.py`
- Expected: equivalent relevant inputs reuse the same identity, irrelevant
  changes—including unrelated analysis contracts—do not invalidate reuse, and
  legacy recipes still validate.

**Exit Criteria:**
- Controller policy is interpreted once; runtime receives one deterministic stage
  plan and one stage identity per stage.

### Task 5: Bound synthesis and target recovery

**Purpose:**
- Implement typed-result simplification without weakening canonical validation,
  provenance, conflict visibility, or persistence.

**Task Function:**
- Replace repeated whole-result fixed-point normalization with bounded
  namespace/index/dependency traversal and typed correction decisions. Records
  may be traversed topologically; each record and relationship must be indexed
  and normalized only a bounded number of times.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: synthesis is a high-risk shared runtime boundary with direct
  consumers and existing regression coverage.

**Validator Profile:**
- Controller-selected: `none`

**Specification Coverage:**
- Participant namespaces, canonical dependency references, bounded synthesis,
  conflict preservation, typed recovery codes, cooperative cancellation, and
  targeted correction.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`,
  `skill-code-standards`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/workflow.py:_synthesize_stage_outputs`,
  correction loop in `run_recipe_async`, and stage context
- Modify: `src/foresight_os/analysis/result_committer.py:normalize_stage_result`
  and canonical reference validation
- Modify: `src/foresight_os/domain/challenge.py:collect_material_inputs` only
  where calculation/dependency closure still performs repeated whole-state
  rescans; preserve review-closure semantics and material conflicts
- Modify: `src/foresight_os/runtime/participants.py` dependency-reference
  instructions and output contract guidance
- Modify only for typed trust-boundary errors: `src/foresight_os/domain/validation.py`
- Verify: `tests/test_orchestration_patterns.py`, `tests/test_result_committer.py`,
  `tests/test_runtime_boundaries.py`, `tests/test_review_hardening.py`,
  `tests/test_participant_scope.py`

**Dependencies:**
- Task 4 canonical stage identity and Task 3 publication boundaries.

**Authority:**
- Preauthorized local actions: refactor synthesis/correction within existing
  result and validation owners; retain alias/provenance regression tests
- Stop for: silent conflict resolution, participant-order authority, unbounded
  recursion, exception-message substring matching, or a generic recovery engine

**Steps:**
- [ ] Step 1: Represent a participant-local key as `(participant_id, local_id)`
  and map it to a canonical result ID only after validation; do not encode the
  participant ID permanently into durable analytical IDs unless required by an
  existing contract.
- [ ] Step 2: Resolve calculations in dependency order, relationships after
  endpoints exist, deduplicate equal fingerprints, and reject unresolved or
  materially conflicting records without repeated whole-result fixed-point passes.
  Use the existing relation/dependency index rather than introducing a generic
  graph or recovery engine.
- [ ] Step 3: Before normalization, preflight participant count, record count,
  relationship count, and approximate payload size. Then enforce hard bounds for
  records, relationships, aliases, dependency depth, and normalization
  operations; check cancellation at safe traversal intervals. Use a small fixed
  failure-code contract:
  `MALFORMED_OUTPUT`, `UNRESOLVED_REFERENCE`, `AMBIGUOUS_ALIAS`,
  `MATERIAL_CONFLICT`, `INVALID_RELATIONSHIP`, `MISSING_INPUT`, `SOURCE_STALE`,
  `PROVIDER_INTERRUPTION`, and `BUDGET_EXHAUSTED`.
- [ ] Step 4: Remove exception-message substring recovery and tolerance switches
  that silently change validation behavior; route recovery only through the
  typed failure-code policy.
- [ ] Step 5: Correct only the affected component: normalize unambiguous IDs,
  correct malformed participant output once, correct/reject invalid
  relationships locally, block missing source/mapping/unit dependents, preserve
  conflicts for review, retry only interrupted provider calls, and preserve
  partial state on budget/source-change failure without publication.
- [ ] Step 6: Give participants the relevant dependency content needed for
  reasoning, but pass canonical dependency IDs and matching hashes in the output
  contract; stop copying full existing evidence into later participant outputs.
  A participant may reference only records in the stage's declared dependency
  closure and authorization scope; host validation must confirm ID existence,
  hash match, non-invalidation, authorization, and allowed dependency.

**Verification:**
- [x] `python -m pytest -q tests/test_orchestration_patterns.py tests/test_result_committer.py tests/test_runtime_boundaries.py tests/test_review_hardening.py tests/test_participant_scope.py`
- Expected: aliases are deterministic, equal duplicates collapse, conflicts
  remain visible, malformed relationships do not rerun successful work, typed
  recovery replaces string-driven branching, cancellation checkpoints are
  effective, and all bounds terminate safely. Prove correcting participant B
  does not rerun participant A, source tools, completed calculations, or the
  validator unless logically required.

**Exit Criteria:**
- Typed synthesis is one bounded deterministic transformation and recovery
  targets the failing component rather than rerunning the whole stage.

### Task 6: Add one run-owned workbook context and measure reuse

**Purpose:**
- Implement Release C after Release A correctness/lifecycle closure and before
  Release B controller/synthesis simplification, so workbook bottlenecks are
  measured without orchestration refactor noise.

**Task Function:**
- Reuse validated design constraints from the earlier workbook-session plan,
  rederive implementation from the current execution base, and place one
  `WorkbookContext` over Task 2's source snapshots before proving the warm path.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: this is a high-risk performance and lifecycle change and
  remains one serialized owner.

**Validator Profile:**
- Controller-selected: `none`

**Specification Coverage:**
- Multi-workbook budgets, same-view reuse, bounded source-aware reads,
  analyst/validator extraction sharing as a hard gate, one pinned source version
  per locator per run, authority lifetime, and measured reuse. Level-2
  parsed-workbook reuse remains out of scope.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`,
  `skill-test-driven-development`

**Files And Symbols:**
- Use as design evidence only: `docs/superpowers/plans/2026-10-15-22-36-foresight-os-workbook-session-reuse-plan.md`
- Modify through current canonical owners: `src/foresight_os/runtime/local_toolbelt.py`,
  `src/foresight_os/runtime/capabilities.py`, `src/foresight_os/runtime/workflow.py`,
  `src/foresight_os/analysis/independent_validation.py`, and affected analysis callers
- Verify: `tests/test_local_toolbelt.py`, `tests/test_capabilities.py`,
  `tests/test_runtime_boundaries.py`, `tests/test_ncc_independent_validation.py`,
  `tests/test_optimization_measurement.py`

**Dependencies:**
- Tasks 2–3. The earlier workbook-session plan is source material only; do not
  adopt its task ledger or assume its older repository model remains valid.

**Authority:**
- Preauthorized local actions: implement bounded sessions, migrate direct
  callers, add matched receipts, and update focused tests
- Stop for: distributed/persistent caches, hidden parsed-workbook reuse,
  unbounded memory, cache-eviction authority loss, or unmeasured performance claims

**Steps:**
- [ ] Step 1: Make the final owner model explicit: `CapabilityScope` owns one
  `WorkbookContext`; `WorkbookContext` owns one pinned `SourceSnapshot` per
  locator for the run, a derived-result cache, an `AuthorityIndex`, and workbook
  statistics. It wraps Task 2 capture; it does not capture or hash sources
  independently or become a source-version registry.
- [ ] Step 2: Migrate `WorkbookReadCache` into or behind that context, remove
  process-global authority maps after callers migrate, and replace
  `CapabilityScope.workbook_cache` rather than leaving parallel owners.
- [ ] Step 3: Account separately for snapshot bytes, retained read-result bytes,
  retained analysis-result bytes, retained authority-record bytes, temporary
  storage, and peak in-flight parser memory. Replace retained-size rescans with
  incremental accounting, enforce one aggregate run budget, and reject before
  retaining state above the configured bound.
- [ ] Step 4: Reuse complete results only for identical snapshot/selection/limits.
  One `spreadsheet_read` request may request the smallest bounded group of
  required sheets/ranges subject to aggregate row, cell, result-size, and sheet
  limits; blanket full-workbook reads remain forbidden. A later different
  selection may parse again in Level 1; do not retain a hidden parsed-workbook
  representation.
- [ ] Step 5: Share immutable deterministic extraction with independent
  validation while keeping judgment, checks, and review outcomes independent.
  Preserve both formula/data-only `openpyxl` semantic loads and share only the
  captured snapshot and verified extraction result. Identical analyst-to-validator
  snapshot/selection/limits must produce zero new captures, source hashes, and
  XLSX parses, with at least one read-cache hit.
- [ ] Step 6: Run matched baseline/release comparison with separate optimization
  and platform-regression receipts. Make structural gates hard: warm identical
  view has zero new captures, zero new capture hashes, zero new XLSX parses, and
  at least one cache hit; analyst-to-validator same view has zero new captures,
  source hashes, and parses; currentness has exactly one intentional currentness
  hash; different Level-1 selections may reparse without a new source
  capture/hash. Freeze the cold-path regression budget before comparison. If
  latency is noisy, do not advertise a speedup and do not block a correctness
  release on the missing timing claim.

**Verification:**
- [ ] `python -m pytest -q tests/test_local_toolbelt.py tests/test_capabilities.py tests/test_runtime_boundaries.py tests/test_ncc_independent_validation.py tests/test_technology_powerbi_validator.py tests/test_optimization_measurement.py`
- Expected: identical views avoid redundant work, different views reuse source
  identity safely, currentness hashes the mutable source, validator extraction
  is shared without collapsing formula/data-only semantics, and cleanup leaves
  no run-owned state. Resource/soak evidence shows bounded retained resources
  across multiple workbooks and repeated investigations.

**Exit Criteria:**
- Production-path measurements satisfy the frozen structural and resource gates
  without a measured cold-path regression beyond the agreed baseline budget. A
  noisy latency baseline is recorded as unmeasured rather than treated as a
  required speedup or a failed correctness gate.

### Task 7: Remove only proven maintenance duplication

**Purpose:**
- Remove only owners made obsolete by Tasks 2–6 after behavior and performance
  are proven. Keep unrelated maintenance as a follow-up rather than blocking
  runtime optimization.

**Task Function:**
- Retire migrated cache/authority owners and update directly affected guidance;
  defer vertical-slice cleanup, recipe-field removal, broad CI restructuring,
  and process-policy changes unless Tasks 2–6 make them necessary.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cleanup spans configuration, docs, CI, and compatibility
  surfaces; one owner must reconcile maintained guidance.

**Validator Profile:**
- Controller-selected: `none`

**Specification Coverage:**
- Required cache/authority migration cleanup, directly affected documentation,
  and verification that existing CI cancellation remains sufficient. Optional
  vertical-slice, recipe-compatibility,
  persistence, and process cleanup is explicitly deferred.

**Required Skills:**
- `skill-code-standards`, `skill-performance-optimization`

**Files And Symbols:**
- Modify only proven migrated-owner targets in `src/foresight_os/runtime/local_toolbelt.py`,
  `src/foresight_os/runtime/capabilities.py`, and `.github/workflows/ci.yml`
- Modify directly affected guidance in `docs/architecture.md`,
  `docs/evidence-and-evaluation.md`, `README.md`, and `evaluation/README.md`
- Verify: `tests/test_local_toolbelt.py`, `tests/test_capabilities.py`,
  `tests/test_markdown_links.py`, and CI YAML inspection

**Dependencies:**
- Tasks 4–6 release comparison and no unresolved ownership findings.

**Authority:**
- Preauthorized local actions: remove demonstrably unused duplicate paths,
  update maintained docs, and inspect existing CI concurrency cancellation
- Stop for: deleting active compatibility readers, removing unique evidence
  jobs, changing provider/MCP authority, or adding a new store/registry

**Steps:**
- [ ] Step 1: Search all consumers before deleting or replacing cache fields,
  process-global authority maps, or `CapabilityScope.workbook_cache`; retain
  compatibility readers until migration is proven.
- [ ] Step 2: Verify the existing CI cancellation behavior for superseded runs;
  do not add a duplicate mechanism. Change CI only if Task 1 confirms the
  behavior is absent or directly obsolete, and still do not change
  `push`/`pull_request` trigger structure or remove unique evidence jobs.
- [ ] Step 3: Update maintained guidance only where Tasks 2–6 changed behavior;
  leave historical plans as history rather than parallel specifications.
- [ ] Step 4: Record deferred vertical-slice, recipe-compatibility, persistence,
  and process-policy cleanup as follow-up work instead of expanding this task.

**Verification:**
- [x] `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- [x] `python -m pytest -q tests/test_local_toolbelt.py tests/test_capabilities.py tests/test_markdown_links.py`
- Expected: no active consumer loses its owner, docs agree with source
  behavior, and CI keeps distinct evidence boundaries.

**Exit Criteria:**
- Required migrated owners are removed only where the canonical replacement and
  regression proof are explicit; optional cleanup is recorded as deferred.

### Task 8: Perform final verification and reconcile the plan

**Purpose:**
- Establish fresh repository-wide proof and make deviations, deferrals, and
  remaining risks explicit before branch disposition.

**Task Function:**
- Verify implementation outcomes against source, tests, receipts, and Git diff.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance requires one controller to reconcile all
  task evidence and scope.

**Validator Profile:**
- Controller-selected: `none`

**Specification Coverage:**
- Definition of done, preserved invariants, explicit non-goals, and truthful
  status reporting.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify all declared targets, final optimization/platform receipts, and Git
  status/diff; do not edit generated files unless canonical inputs changed

**Dependencies:**
- Tasks 1–7 complete with task-local proof.

**Authority:**
- Preauthorized local actions: run declared verification, inspect final diff,
  reconcile plan evidence, and record blocked/unmeasured outcomes
- Stop for: failed required checks, stale release fingerprints, unrecorded scope
  changes, or claims requiring uncollected external/human evidence

**Steps:**
- [ ] Step 1: Run focused backend checks for each changed owner, then the full
  repository suite and compile checks.
- [ ] Step 2: Run `git diff --check`, inspect the tracked diff, and confirm
  unrelated untracked artifacts remain untouched.
- [ ] Step 3: Confirm final source-tree fingerprint matches the release receipt
  and baseline/release identities match for workload, fixture, environment,
  dependencies, schema, harness, and exact verified source tree. Confirm
  runtime completion, pending persistence, and accepted analytical state remain
  separately represented in the final receipts/status evidence.
- [ ] Step 4: Record deviations, blocked external evidence, deferred Level-2
  reuse, and follow-up work; only the verification skill may mark this plan
  `completed` after returning `verified`.

**Verification:**
- [ ] `python -m pytest -q`
- [ ] `python -m compileall -q src tests evaluation`
- [ ] `git diff --check`
- [ ] Run the declared production-path optimization comparison and resource/soak
  checks from Task 6, if their baseline and harness receipts are available.
- Expected: deterministic checks pass; unavailable provider, human-quality, or
  noisy latency evidence is labeled truthfully rather than converted to a pass;
  structural no-redundancy and resource gates remain hard requirements.

**Exit Criteria:**
- `skill-verification-before-completion` returns `verified`; the final tree and
  receipts agree; no required task or scope deviation is unresolved.

## Verification

Final verification is one authoritative pass after task-local checks:

- [x] `python -m pytest -q` — passed with two expected skips.
- [x] `python -m compileall -q src tests evaluation` — passed.
- [x] `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs` — checked 36 paths.
- [x] matched structural reuse receipt from Task 6 — all structural gates passed; latency and resource-soak dimensions remain `not_measured`.
- [x] final `git status --short --branch`, `git diff --check`, and declared-target diff inspection — passed on `codex/recommended-sequence-followup`.

Structural proof must be reported separately from provider availability, model
quality, human acceptance, and any performance dimension not measured.

Final residuals are explicit: active cache/authority compatibility consumers
remain and optional cleanup is deferred; no latency speedup or resource-soak
claim is made without a matched harness receipt; external-provider and human
acceptance evidence are not part of this local verification.

## Completion Criteria

The plan is ready for completion verification when:

1. Source identity, immutable workbook-view identity, live/pinned semantics,
   contract validation, cancellation, cleanup, and transactional publication are
   proven by focused tests.
2. There is exactly one source-capture implementation, and `WorkbookContext`
   wraps its `SourceSnapshot` values rather than reimplementing capture.
3. Domain contract validation stays out of generic XLSX parsing; generic source,
   selection, bounds, formula/cache, and provenance checks stay in the toolbelt.
4. Controller policy is normalized once and stage reuse uses only relevant
   identity: direct stage contracts plus declared dependency contracts.
5. Typed synthesis is bounded, namespaced, conflict-aware, and uses canonical
   references instead of copied dependency records; references are authorized.
6. Recovery corrects affected components without broad stage reruns and uses
   typed failure classes rather than exception-message substring checks.
7. Workbook reuse is run-owned, uses one pinned source version per locator per
   run, is bounded and measured on the production path, and does not claim
   parsed-workbook reuse beyond the implemented level; structural count and
   resource gates are satisfied, while noisy latency is labeled unmeasured.
8. Required migrated owners are removed, while optional maintenance cleanup is
   recorded as deferred rather than blocking runtime acceptance.
9. Documentation and CI describe actual behavior without trigger restructuring.
10. Full verification passes, the final receipt matches the exact verified tree,
    run outcome is distinct from durable acceptance, and unavailable evidence is
    labeled explicitly.

The plan may be marked `completed` only after
`skill-verification-before-completion` returns `verified`. A checked box is
progress evidence, not completion proof.

## Self-Review

- Verdict coverage: Releases A–D map to Tasks 2–7; Task 1 adds the bounded
  reproduce/baseline gate; Task 8 owns final reconciliation. The execution order
  is 1, 2, 3, 6, 4, 5, 7, 8 so workbook integration precedes orchestration
  simplification.
- Repository reconciliation: Task 1 confirms current merged `main`, owner
  presence, and focused regressions without repeating a full architecture study.
- Ownership: `AnalysisState`/`AnalysisStore` remain durable owners;
  `local_toolbelt.py` owns the single source primitive and generic extraction;
  `CapabilityScope` owns lifecycle; `WorkbookContext` owns run-level workbook
  state; controller modules own policy; evaluation scripts consume evidence.
- Compatibility: recipe and approval serialization are preserved until focused
  migration proof exists.
- Correctness gates: the hidden-row cache alias, snapshot-only validation,
  preventive byte limits, post-settlement `asyncio.CancelledError`, and the
  formula/data-only `openpyxl` distinction are explicit task-local proof items.
- Current-base fit: the plan uses existing `NormalizedIntent` and
  `AnalysisInputContract` as canonical owners and stops for bounded plan
  reconciliation if the merged base disagrees.
- Scope: Task 7 blocks only on cleanup made necessary by Tasks 4–6; unrelated
  vertical-slice, recipe, persistence, and process cleanup is follow-up work.
- Non-goals: no second store, source registry, generic recovery framework,
  distributed cache, filesystem watcher, new orchestration pattern, or hidden
  parsed-workbook database.
- Execution: tasks are serialized because controller, lifecycle, synthesis,
  workbook, persistence, and receipt changes share contracts.
