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
  - src/foresight_os/persistence/analysis_store.py
  - src/foresight_os/persistence/recovery.py
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
  - tests/test_optimization_measurement.py
  - docs/architecture.md
  - docs/evidence-and-evaluation.md
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

Implementation is authorized in the isolated worktree recorded below. This
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

### Required corrections before execution

- The supplied critique refers to `main@73c0826` and files that are not present
  in this checkout. This plan therefore requires Task 1 to refresh `main` and
  reconcile the owner map immediately before implementation. At the planning
  base verified here, `NormalizedIntent` and `AnalysisInputContract` are not
  current symbols; if the refreshed base contains them, reuse those existing
  owners rather than introducing duplicates.
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

One run-owned workbook context supports multiple immutable source versions,
bounded same-snapshot reuse, multiple-workbook accounting, bounded reads, and
shared deterministic extraction for analyst and validator paths.

### Release D — maintenance reduction

Compatibility owners, duplicate authority probes, CI duplication, and stale
architecture guidance are reduced only after Releases A–C are proven. No new
store, registry, recovery engine, orchestration framework, or persistent parsed
workbook database is introduced.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-plan-document-reviewer`, `skill-executing-plans`, `skill-backend-verification`, `skill-test-driven-development`, `skill-performance-optimization`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: current workspace for planning; create an isolated `codex/` branch or worktree before implementation
- Commit policy: `no commits during execution unless separately approved`
- Preauthorized local actions: inspect declared source/tests/docs, edit declared plan and implementation files during approved execution, run declared local checks, preserve unrelated user files
- User-approval actions: branch/worktree creation, commits, pushes, merges, external provider calls, destructive cleanup, and compatibility-data deletion
- Parallel ownership: none; shared controller, workbook, persistence, and cleanup contracts require serialization
- Sequential fallback: execute Tasks 1–8 in order

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: detached implementation worktree at `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\recommended-implementation-sequence\foresight-OS`
- Base commit: refreshed from `main` at execution start; `bd5abc1335d6454f89703a00243051bd5b2fff40`
- Expected workspace: preserve all unrelated artifacts in the primary checkout and existing worktrees
- Next action: none; implementation is verified in the isolated worktree and remains uncommitted by instruction
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `complete` | isolated implementation workspace | `lead controller` | none | matched baseline receipt | `work/optimization-baseline/receipt.json`, `work/optimization-baseline/owner-inventory.md` |
| Task 2 | `complete` | isolated implementation workspace | `lead controller` | Task 1 | Release A boundary tests | focused source, workflow, portability, and validation tests |
| Task 3 | `complete` | isolated implementation workspace | `lead controller` | Task 2 | lifecycle/publication tests | capability, boundary, committer, and persistence tests |
| Task 4 | `complete` | isolated implementation workspace | `lead controller` | Task 1 | controller/fingerprint tests | controller, stage-input, reuse, approval, and gate tests |
| Task 5 | `complete` | isolated implementation workspace | `lead controller` | Task 4 | synthesis/recovery tests | orchestration, committer, boundary, review, and participant tests |
| Task 6 | `complete` | isolated implementation workspace | `lead controller` | Tasks 2–5 | matched reuse comparison | context tests; `work/optimization-release-final/receipt.json`; `work/optimization-platform-regression/receipt.json` |
| Task 7 | `complete` | isolated implementation workspace | `lead controller` | Task 6 | maintenance/docs/CI checks | consumer search; CI concurrency; maintained docs; compatibility cleanup deferred |
| Task 8 | `complete` | isolated implementation workspace | `lead controller` | Tasks 2–7 | full verification | full suite, compileall, links, diff check, receipt comparison, source-tree fingerprint |

## Task Breakdown

### Task 1: Freeze scope and establish a matched baseline

**Purpose:**
- Convert the verdict into measurable acceptance gates and protect unrelated
  working-tree artifacts before implementation begins.

**Task Function:**
- Reproduce current behavior, map canonical owners, and record baseline
  investigation and workbook measurements.

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
- [ ] Step 1: Refresh `main` immediately before implementation, record the
  actual base SHA, and re-run the owner/symbol inventory. If `NormalizedIntent`,
  `AnalysisInputContract`, or dedicated workbook-input owners exist at that
  base, update Tasks 2 and 4 to consume them rather than adding parallel types.
- [ ] Step 2: Inventory current owners and callers for source identity, workbook
  reads, controller policy, typed synthesis, recovery, persistence, resource
  cleanup, and publication.
- [ ] Step 3: Record fixture hashes, dependency versions, environment,
  implementation identity, dirty paths, and current correctness results.
- [ ] Step 4: Measure cold read, same-view repeat, different selection,
  analyst-to-validator extraction, currentness check, cancellation, multiple
  workbooks, repeated investigation, and end-to-end time to a usable result.
  Prefer external or harness measurement for baseline; if runtime counters are
  added, use equivalent instrumentation for baseline and release and separate
  `capture_hash_count`, `currentness_hash_count`, `xlsx_parse_count`,
  `openpyxl_load_count`, and `cache_hits`.
- [ ] Step 5: Freeze non-goals: no distributed cache, parsed-workbook database,
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
- Exact SHA identity, formula/cache semantics, cell/range provenance, live vs
  pinned reads, immutable approved inputs, explicit mapping/unit failures, and
  exactly one source-capture implementation.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`,
  `skill-code-standards`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/local_toolbelt.py:WorkbookReadCache`,
  `_sha256_file`, `spreadsheet_read`, `SheetSelection`, `AnalysisOperation`,
  `UnitSpec`, `WorkbookReadResult`
- Modify: `src/foresight_os/domain/models.py` and
  `src/foresight_os/domain/validation.py` for the current brief/stage input
  contract; if the refreshed base contains `domain/analysis_inputs.py`, use its
  existing `AnalysisInputContract` owner instead of adding another model
- Modify: `src/foresight_os/analysis/evidence_workflow.py:run_xlsx_finding_workflow`
- Modify: `src/foresight_os/analysis/independent_validation.py` source-read and
  extraction entry points
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
- [x] Step 1: Add exactly one immutable captured-source representation owned by
  the toolbelt; its SHA, byte count, and bytes/file are the inputs to parsing and
  provenance. Do not add a run-level cache/context here.
- [x] Step 2: Make live reads, pinned reads, explicit currentness checks, and
  new captures distinct. Repeated live reads must not silently reuse a pinned
  version, and Task 6 must wrap this primitive rather than reimplement capture.
- [x] Step 3: Check cancellation during capture, hashing, preflight, and parse;
  do not publish a read or trusted result after cancellation or source change.
- [x] Step 4: Harden the existing domain/stage input contract at its canonical
  owner: deep-freeze nested values, validate period syntax, units/currency and
  supported policies, and reject unsupported fields before analysis. If a
  refreshed base has `AnalysisInputContract`, strengthen it; do not create a
  second normalized contract.
- [x] Step 5: Keep explicit column mappings and required tables in analyzer/input
  owners, where missing or ambiguous mappings fail explicitly. Keep generic
  `local_toolbelt.py` validation limited to source, selection, range/table
  bounds, resource limits, formula/cache semantics, parsing, and provenance.
- [x] Step 6: Remove redundant pre-hashes only after capture is authoritative;
  retain currentness hashes where the trust boundary requires a fresh check.

**Verification:**
- [ ] `python -m pytest -q tests/test_local_toolbelt.py tests/test_evidence_workflow.py tests/test_ncc_independent_validation.py tests/test_work_brief_compatibility.py tests/test_portfolio_resilience.py tests/test_supplier_resilience.py tests/test_technology_radar.py tests/test_ev_capacity_investment.py`
- Expected: provenance is exact, invalid contracts fail early, formula/cache
  behavior is unchanged, explicit mappings fail clearly, and cancellation/source
  mutation cannot publish trusted output.

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
  before workbook cleanup, and publication atomicity.

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
  `tests/test_result_committer.py`, `tests/test_persistence.py`

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
- [ ] Step 2: Stop new admission, signal cancellation, settle workers/futures,
  shut down executors, close workbook contexts, then close remaining resources.
- [ ] Step 3: Prevent writes to closed scopes and prevent cleanup failures from
  being reported as accepted publication.
- [ ] Step 4: Preserve atomic pending/accepted transitions through existing
  `AnalysisStore` and result committer; add no parallel store.

**Verification:**
- [ ] `python -m pytest -q tests/test_capabilities.py tests/test_runtime_boundaries.py tests/test_result_committer.py tests/test_persistence.py`
- Expected: setup failures clean up partial resources, workers settle before
  cleanup completes, closed scopes reject publication, and accepted state is
  written only after validation.

**Exit Criteria:**
- Ownership starts before creation, ends after settlement, and publication is
  atomic and failure-aware.

### Task 4: Normalize controller policy and canonicalize stage identity

**Purpose:**
- Implement Release B single policy input, Direct/Sequential default, one
  canonical stage plan, and relevant-only stage fingerprints without breaking
  recipe/approval compatibility.

**Task Function:**
- Make the repository's existing brief-normalization boundary authoritative for
  recipe selection and reuse. If the refreshed base contains
  `domain.analysis_inputs.NormalizedIntent`, consume it directly; otherwise
  promote the existing normalization path without adding a second model.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: policy is centralized but still derives facts from multiple
  structures; this is a controller-owner refactor.

**Validator Profile:**
- Controller-selected: `none`

**Specification Coverage:**
- Existing `NormalizedIntent`/`normalize_work_brief()` when present,
  `RecipeStage` as runtime plan, Direct/Sequential defaults, one stage identity,
  and relevant-only contract fingerprints.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Modify: `src/foresight_os/controller/policy.py:select_recipe`,
  `_recipe_for_patterns`, and normalization boundary
- Modify: `src/foresight_os/controller/recipes.py:StageInput`, `RecipeStage`,
  `ExecutionRecipe`, `make_recipe`
- Modify: `src/foresight_os/controller/proposal.py:build_execution_recipe`,
  `validate_execution_recipe_contract`
- Modify: `src/foresight_os/runtime/execution_gate.py` and the current domain
  normalization owner; if the refreshed base contains
  `src/foresight_os/domain/analysis_inputs.py`, use its existing
  `NormalizedIntent`/`normalize_work_brief()` symbols
- Modify: `src/foresight_os/runtime/workflow.py:_stage_fingerprints`,
  `_stage_cache_key`, and stage context construction
- Verify: `tests/test_controller_selection.py`, `tests/test_stage_inputs.py`,
  `tests/test_selective_reuse.py`, `tests/test_approval_contract.py`,
  `tests/test_execution_approval_fingerprint.py`

**Dependencies:**
- Task 1 owner inventory; Task 3 publication and lifecycle boundaries.

**Authority:**
- Preauthorized local actions: migrate selection and fingerprints to the existing
  normalization path and add narrow compatibility translation while preserving
  serialized recipes, approval fingerprints, explicit overrides, and review-required topology
- Stop for: removing persisted fields, making advanced patterns implicit, or
  changing user-authorized topology without focused compatibility proof

**Steps:**
- [ ] Step 1: Reuse the existing `NormalizedIntent`/`normalize_work_brief()`
  boundary when present and ensure it contains every policy datum recipe
  selection actually needs. Do not introduce another normalization dataclass.
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
- [ ] `python -m pytest -q tests/test_controller_selection.py tests/test_stage_inputs.py tests/test_selective_reuse.py tests/test_approval_contract.py tests/test_execution_approval_fingerprint.py tests/test_execution_gate.py`
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
  conflict preservation, typed recovery codes, and targeted correction.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`,
  `skill-code-standards`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/workflow.py:_synthesize_stage_outputs`,
  correction loop in `run_recipe_async`, and stage context
- Modify: `src/foresight_os/analysis/result_committer.py:normalize_stage_result`
  and canonical reference validation
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
- [ ] Step 3: Add hard bounds for records, relationships, aliases, dependency
  depth, and normalization operations. Use a small fixed failure-code contract:
  `MALFORMED_OUTPUT`, `UNRESOLVED_REFERENCE`, `AMBIGUOUS_ALIAS`,
  `MATERIAL_CONFLICT`, `INVALID_RELATIONSHIP`, `MISSING_INPUT`, `SOURCE_STALE`,
  `PROVIDER_INTERRUPTION`, and `BUDGET_EXHAUSTED`.
- [ ] Step 4: Correct only the affected component: normalize unambiguous IDs,
  correct malformed participant output once, correct/reject invalid
  relationships locally, block missing source/mapping/unit dependents, preserve
  conflicts for review, retry only interrupted provider calls, and preserve
  partial state on budget/source-change failure without publication.
- [ ] Step 5: Pass canonical dependency IDs and matching hashes to participants;
  stop copying full existing evidence into later participant outputs. A
  participant may reference only records in the stage's declared dependency
  closure and authorization scope; host validation must confirm ID existence,
  hash match, non-invalidation, authorization, and allowed dependency.

**Verification:**
- [ ] `python -m pytest -q tests/test_orchestration_patterns.py tests/test_result_committer.py tests/test_runtime_boundaries.py tests/test_review_hardening.py tests/test_participant_scope.py`
- Expected: aliases are deterministic, equal duplicates collapse, conflicts
  remain visible, malformed relationships do not rerun successful work, and all
  bounds terminate safely.

**Exit Criteria:**
- Typed synthesis is one bounded deterministic transformation and recovery
  targets the failing component rather than rerunning the whole stage.

### Task 6: Add one run-owned workbook context and measure reuse

**Purpose:**
- Implement Release C only after Releases A and B establish correct identity,
  ownership, and stage behavior.

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
  analyst/validator extraction sharing, authority lifetime, and measured reuse.
  Level-2 parsed-workbook reuse remains out of scope.

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
- Tasks 2–5. The earlier workbook-session plan is source material only; do not
  adopt its task ledger or assume its older repository model remains valid.

**Authority:**
- Preauthorized local actions: implement bounded sessions, migrate direct
  callers, add matched receipts, and update focused tests
- Stop for: distributed/persistent caches, hidden parsed-workbook reuse,
  unbounded memory, cache-eviction authority loss, or unmeasured performance claims

**Steps:**
- [x] Step 1: Make the final owner model explicit: `CapabilityScope` owns one
  `WorkbookContext`; `WorkbookContext` owns `SourceSnapshot[]`, a derived-result
  cache, an `AuthorityIndex`, and workbook statistics. It wraps Task 2 capture;
  it does not capture or hash sources independently.
- [x] Step 2: Migrate `WorkbookReadCache` into or behind that context, remove
  process-global authority maps after callers migrate, and replace
  `CapabilityScope.workbook_cache` rather than leaving parallel owners.
- [x] Step 3: Account separately for snapshot bytes, retained read-result bytes,
  retained analysis-result bytes, retained authority-record bytes, temporary
  storage, and peak in-flight parser memory. Enforce one aggregate run budget.
- [x] Step 4: Reuse complete results only for identical snapshot/selection/limits.
  One `spreadsheet_read` request may request several required sheets/ranges,
  but a later different selection may parse again in Level 1; do not retain a
  hidden parsed-workbook representation.
- [x] Step 5: Share immutable deterministic extraction with independent
  validation while keeping judgment, checks, and review outcomes independent.
- [x] Step 6: Run matched baseline/release comparison with separate optimization
  and platform-regression receipts. Freeze these acceptance gates: warm identical
  view has zero new captures, zero new capture hashes, zero new XLSX parses, and
  at least one cache hit; analyst-to-validator same view has zero new captures or
  capture hashes and ideally zero new parses; currentness has exactly one
  intentional currentness hash; warm latency improvement must exceed measured
  baseline drift/noise. Do not require parse improvement for different selections
  in Level 1.

**Verification:**
- [x] `python -m pytest -q tests/test_local_toolbelt.py tests/test_capabilities.py tests/test_runtime_boundaries.py tests/test_ncc_independent_validation.py tests/test_optimization_measurement.py`
- Expected: identical views avoid redundant work, different views reuse source
  identity safely, currentness hashes the mutable source, validator extraction
  is shared, and cleanup leaves no run-owned state.

**Exit Criteria:**
- Production-path measurements satisfy the frozen count/noise/resource gates
  without a cold-path regression beyond the agreed baseline budget.

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
  and narrow CI cancellation. Optional vertical-slice, recipe-compatibility,
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
- Task 6 release comparison and no unresolved ownership findings.

**Authority:**
- Preauthorized local actions: remove demonstrably unused duplicate paths,
  update maintained docs, and add narrow CI concurrency cancellation
- Stop for: deleting active compatibility readers, removing unique evidence
  jobs, changing provider/MCP authority, or adding a new store/registry

**Steps:**
- [x] Step 1: Search all consumers before deleting or replacing cache fields,
  process-global authority maps, or `CapabilityScope.workbook_cache`; retain
  compatibility readers until migration is proven.
- [x] Step 2: Add CI cancellation for superseded runs only; do not change
  `push`/`pull_request` trigger structure or remove unique evidence jobs.
- [x] Step 3: Update maintained guidance only where Tasks 2–6 changed behavior;
  leave historical plans as history rather than parallel specifications.
- [x] Step 4: Record deferred vertical-slice, recipe-compatibility, persistence,
  and process-policy cleanup as follow-up work instead of expanding this task.

**Verification:**
- [ ] `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- [ ] `python -m pytest -q tests/test_local_toolbelt.py tests/test_capabilities.py tests/test_markdown_links.py`
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
- [x] Step 1: Run focused backend checks for each changed owner, then the full
  repository suite and compile checks.
- [x] Step 2: Run `git diff --check`, inspect the tracked diff, and confirm
  unrelated untracked artifacts remain untouched.
- [x] Step 3: Confirm final source-tree fingerprint matches the release receipt
  and baseline/release identities match for workload, fixture, environment,
  dependencies, schema, and harness.
- [x] Step 4: Record deviations, blocked external evidence, deferred Level-2
  reuse, and follow-up work; only the verification skill may mark this plan
  `completed` after returning `verified`.

**Verification:**
- [x] `python -m pytest -q`
- [x] `python -m compileall -q src tests evaluation`
- [x] `git diff --check`
- Expected: deterministic checks pass; unavailable provider, human-quality, or
  performance evidence is labeled truthfully rather than converted to a pass.

**Exit Criteria:**
- `skill-verification-before-completion` returns `verified`; the final tree and
  receipts agree; no required task or scope deviation is unresolved.

**Verification Disposition:**

- `VERIFIED`: focused owner tests, full repository tests, compile checks,
  Markdown links, whitespace, matched optimization comparison, and source-tree
  fingerprint reconciliation.
- `DEFERRED`: removal of process-global authority compatibility readers and the
  `CapabilityScope.workbook_cache` compatibility pointer; direct callers and
  existing tests still consume these compatibility paths, so deletion is not
  justified in this change.
- `OUT OF SCOPE`: Level-2 parsed-workbook reuse, persistent/distributed caching,
  broad CI trigger changes, recipe compatibility-field removal, and unrelated
  vertical-slice or persistence cleanup.

## Verification

Final verification is one authoritative pass after task-local checks:

- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- matched baseline/release optimization comparison from Task 6
- final `git status --short --branch` and declared-target diff inspection

Structural proof must be reported separately from provider availability, model
quality, human acceptance, and any performance dimension not measured.

## Completion Criteria

The plan is ready for completion verification when:

1. Source identity, live/pinned semantics, contract validation, cancellation,
   cleanup, and transactional publication are proven by focused tests.
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
7. Workbook reuse is run-owned, bounded, measured on the production path, and
   does not claim parsed-workbook reuse beyond the implemented level; exact
   count/noise/resource gates are satisfied.
8. Required migrated owners are removed, while optional maintenance cleanup is
   recorded as deferred rather than blocking runtime acceptance.
9. Documentation and CI describe actual behavior without trigger restructuring.
10. Full verification passes, the final receipt matches the verified tree, and
    unavailable evidence is labeled explicitly.

The plan may be marked `completed` only after
`skill-verification-before-completion` returns `verified`. A checked box is
progress evidence, not completion proof.

## Self-Review

- Verdict coverage: Releases A–D map to Tasks 2–7; Task 1 adds the required
  baseline gate; Task 8 owns final reconciliation.
- Repository reconciliation: Task 1 refreshes `main` and updates the owner map;
  current checkout facts are not replaced by the supplied critique's unverified
  SHA or file inventory.
- Ownership: `AnalysisState`/`AnalysisStore` remain durable owners;
  `local_toolbelt.py` owns the single source primitive and generic extraction;
  `CapabilityScope` owns lifecycle; `WorkbookContext` owns run-level workbook
  state; controller modules own policy; evaluation scripts consume evidence.
- Compatibility: recipe and approval serialization are preserved until focused
  migration proof exists.
- Scope: Task 7 blocks only on cleanup made necessary by Tasks 2–6; unrelated
  vertical-slice, recipe, persistence, and process cleanup is follow-up work.
- Non-goals: no second store, source registry, generic recovery framework,
  distributed cache, filesystem watcher, new orchestration pattern, or hidden
  parsed-workbook database.
- Execution: tasks are serialized because controller, lifecycle, synthesis,
  workbook, persistence, and receipt changes share contracts.
