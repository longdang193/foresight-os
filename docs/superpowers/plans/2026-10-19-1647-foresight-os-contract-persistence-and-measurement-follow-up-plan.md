---
layer: change
artifact_type: plan
status: active
template_id: implementation-plan
contract_version: "1"
name: foresight-os-contract-persistence-and-measurement-follow-up
targets:
  - src/foresight_os/domain/analysis_inputs.py
  - src/foresight_os/domain/validation.py
  - src/foresight_os/analysis/workbook_inputs.py
  - src/foresight_os/analysis/workbook_registry.py
  - src/foresight_os/runtime/capabilities.py
  - src/foresight_os/runtime/external_signals.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/persistence/analysis_store.py
  - src/foresight_os/runtime/local_toolbelt.py
  - evaluation/probes/optimization_measurement.py
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/compare_optimization_receipts.py
  - tests/
  - docs/architecture.md
  - work/
---

# ForesightOS Contract, Persistence, And Measurement Follow-Up

## Review Of The Recommendation

The supplied review is materially correct, but the recommendations need a
dependency-aware scope. Source inspection against `origin/main` at
`2081f6caa78fe771b52014b6ad4d99c2b4118845` confirms:

- **P0, confirmed:** `domain/validation.py:_normalize_work_brief` converts
  sparse declarations through `AnalysisInputContract.to_dict()`. That loses
  field presence before `workbook_inputs.py:resolve_workbook_contract` merges
  domain defaults, so direct and persisted approved execution can resolve
  different effective contracts. The existing `required_tables` exception is
  incomplete; it does not protect units, currencies, conversion rates,
  periods, scenarios, or explicit empty values.
- **P1, confirmed:** `runtime/capabilities.py:prepare_capability_context`
  loads hosted MCP bindings and binds adapters before calling metadata
  admission. `external_signals.py:load_hosted_mcp_bindings` constructs live
  `agent_framework` tool objects, so admission can create resources that are
  not used until runtime.
- **P1, confirmed:** the optimization probe marks `changed_brief` as
  `NOT_MEASURED`, aliases `growing_analysis_history` to the two-run repeated
  investigation workload, and leaves `gate_timing_paths` disabled. Its
  revision metadata also does not record a clean/dirty state, so durable
  baseline/release evidence can be mismatched.
- **P1, confirmed but measurement-gated:** `AnalysisStore.commit_revision`
  loads and validates both current and pending full states under the lock, and
  `_remember_consumed_pending_token` grows an unbounded token list. These are
  credible history-scaling risks, but changes must preserve stale-pending and
  replay protection and should be selected only after a real growing-history
  workload quantifies the cost.
- **P1, confirmed but conditional:** XLSX preflight now scopes selected rows,
  but it still scans each worksheet XML and `openpyxl.load_workbook` still
  materializes the whole workbook. A selected-sheet stress fixture is required
  before introducing a read-only path.
- **P2, confirmed and low-risk:** `workbook_registry.py:DomainWorkbookSpec`
  constructs all five domain defaults whenever one default is requested. A
  per-domain immutable factory/cache is justified, but default-resolution
  ownership must remain unchanged until the sparse declaration fix is proven.

Dependency cleanup is intentionally deferred. `agent-framework` is imported
at module scope by runtime workflow/executor/capability/recovery modules, so
making it optional is a separate packaging and clean-wheel migration. Pandas
removal likewise requires an independent wheel/import proof and should not be
coupled to the correctness and persistence changes below.

## Goal

Preserve sparse analysis-input declarations exactly through durable WorkBrief
normalization, make one immutable effective stage/domain contract authoritative
for direct and approved execution, keep capability admission metadata-only,
make optimization evidence exercise the changed-brief and growing-history
paths, and apply only persistence or XLSX reader optimizations proven safe by
those measurements.

## Implementation Outcomes

### Sparse contract semantics are durable and parity-preserving

Canonical sparse declarations retain field presence and aliases while keeping
explicit empty values meaningful. Domain defaults are merged once at the
workbook input boundary, and direct, persisted, and approved execution produce
identical effective contracts, fingerprints, selected tables, and domain
results.

### Admission and activation have separate resource boundaries

Capability admission validates definitions, authorization, and availability
metadata without constructing hosted MCP tools or external adapter objects.
Activation constructs each required provider object once, records its existing
fingerprint, and owns its teardown through the runtime capability scope.

### Optimization evidence is honest and actionable

The measurement harness executes a real changed-brief workload, a distinct
10/100/1000-revision history workload, selected-sheet reader stress, and timing
paths. Receipts identify the exact clean source tree and harness pair, and
comparisons gate timing paths instead of allowing aggregate p95 to hide a
material cold or repeated-path regression.

### Persistence and reader changes preserve safety under load

If measurement confirms the expected bottlenecks, persistence avoids redundant
full-state work without weakening locking, revision checks, pending recovery,
or replay rejection. XLSX preflight avoids excluded-sheet XML work and only
uses a read-only selected-sheet path if parity and resource evidence justify
it; the eager path remains the safe fallback otherwise.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `new clean worktree from origin/main`; preserve the current dirty checkout unchanged
- Commit policy: `verified local checkpoint commits are preauthorized; push, PR publication, merge, branch deletion, cleanup, and unrelated workspace mutation still require explicit authorization`
- Preauthorized local actions: `inspect source and tests, edit the listed files, create bounded fixtures/probes/receipts, and run declared local verification`
- User-approval actions: `push, pull-request publication, merge, destructive recovery, cleanup, and any deletion or rewrite of unrelated work artifacts`
- Parallel ownership: `none; contract, measurement, persistence, and reader work share contracts and must remain ordered`
- Sequential fallback: `complete Tasks 1-2 first, run Task 3 measurements, then execute only the measurement-supported portions of Tasks 4-5 before Task 6 and final verification`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/foresight-os-contract-persistence-and-measurement-follow-up` (to be created from the base after approval)
- Base commit: `2081f6caa78fe771b52014b6ad4d99c2b4118845`
- Expected workspace: `current checkout is dirty and preserved; execution uses a clean linked worktree`
- Next action: `execute Task 1: preserve sparse analysis-input declarations`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | new worktree | `lead controller` | none | sparse round-trip and parity tests | focused contract, runner, path-parity, execution-gate, CLI, and approval tests passed |
| Task 2 | `completed` | new worktree | `lead controller` | Task 1 | admission/activation lifecycle tests | capability and hosted-MCP lifecycle tests passed |
| Task 3 | `active` | new worktree | `lead controller` | Tasks 1-2 | changed-brief, history, timing, and receipt tests/probes | in progress |
| Task 4 | `pending` | new worktree | `lead controller` | Task 3 | persistence benchmark plus stale/replay regression tests | pending |
| Task 5 | `pending` | new worktree | `lead controller` | Task 3 | selected-sheet resource evidence and parity tests | pending |
| Task 6 | `pending` | new worktree | `lead controller` | Tasks 1-5, with Tasks 4-5 completed or evidence-deferred | default construction proof and final suite | pending |

## Task Breakdown

### Task 1: Preserve sparse analysis-input declarations

**Purpose:**
- Keep omitted fields omitted through WorkBrief validation and persistence,
  while preserving explicit empty values and canonical aliases.

**Task Function:**
- Repair the durable declaration boundary and prove direct/persisted/approved
  workbook contract parity.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `P0 correctness work with narrow ownership and high contract risk`

**Validator Profile (optional):**
- Controller-selected: `<none>`
- Selection basis: `focused regression tests and backend verification are sufficient`

**Specification Coverage:**
- A canonical sparse declaration remains separate from the fully resolved
  `AnalysisInputContract`:
  `declaration -> durable WorkBrief -> NormalizedIntent lookup ->
  resolve_workbook_contract() -> effective contract`.
- Declaration identity may differ from effective execution identity. Effective
  `AnalysisInputContract.to_dict()` and `fingerprint` continue to describe
  resolved execution semantics only; they do not gain presence metadata.
- Explicit empty values remain explicit overrides and may fail domain/schema
  validation when the domain requires non-empty values; they must not silently
  become a successful empty analysis.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/domain/analysis_inputs.py:AnalysisInputContract`, `NormalizedIntent`, `normalize_work_brief`
- Inspect: `src/foresight_os/domain/validation.py:_normalize_work_brief`
- Add or modify: a small immutable `AnalysisInputDeclaration` (or equivalent
  canonical sparse mapping) at the durable boundary; do not overload effective
  `AnalysisInputContract.to_dict()` or `fingerprint`
- Inspect only: `src/foresight_os/domain/analysis_inputs.py:AnalysisInputContract.from_dict`,
  `to_dict`, and `fingerprint` to preserve effective-contract semantics
- Modify: `src/foresight_os/domain/validation.py:_normalize_work_brief`
- Modify: `src/foresight_os/analysis/workbook_inputs.py:resolve_workbook_contract`
- Verify: `tests/test_analysis_input_contract.py`, `tests/test_workbook_runner.py`, `tests/test_workbook_path_parity.py`

**Dependencies:**
- Base source at `2081f6caa78fe771b52014b6ad4d99c2b4118845`.

**Authority:**
- Preauthorized local actions: `edit the contract/validation/workbook-boundary files and add focused tests`
- Stop for: `schema compatibility, legacy brief migration, or public serialization behavior cannot be preserved without a specification decision`

**Steps:**
- [ ] Step 1: Introduce a canonical immutable sparse declaration type or
  mapping that records only fields present in the authored brief. Normalize
  aliases (`tables`, `entities`, `currency`, and `validation_checks`) to
  canonical names without populating omitted fields.
- [ ] Step 2: Make WorkBrief validation and `NormalizedIntent` persist and
  select that sparse declaration. Make `resolve_workbook_contract` merge only
  declared overrides into the immutable domain default, remove the current
  `required_tables`-only special case, and retain explicit empty overrides with
  normal domain validation.
- [ ] Step 3: Preserve the distinction `declaration identity != effective
  execution identity`: approval/brief serialization may include declaration
  presence, while stage reuse and workbook analysis use the resolved contract
  fingerprint.
- [ ] Step 4: Add parity tests for supplier currency/conversion defaults,
  technology units, portfolio periods/baseline/comparison/scenarios, Power BI
  comparable periods, required tables, aliases, explicit empties, and stage
  overrides. Compare effective contract dictionaries, fingerprints, selected
  material, representative domain results, and declaration round trips across
  direct, persisted, and approved paths.

**Verification:**
- [ ] `python -m pytest -q tests/test_analysis_input_contract.py tests/test_workbook_runner.py tests/test_workbook_path_parity.py`
- Expected: sparse round trips retain omission, explicit empties either apply or
  fail validation explicitly, and direct/persisted/approved paths produce equal
  effective contract identity.

**Exit Criteria:**
- No sparse declaration is expanded into a default-overriding full contract
  before resolution, and all focused parity tests pass.

### Task 2: Make capability admission metadata-only

**Purpose:**
- Prevent admission from constructing hosted MCP tools or binding live
  external adapters that activation may never use.

**Task Function:**
- Separate capability metadata discovery/admission from provider activation while
  preserving authorization, availability, fingerprints, and teardown.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `shared runtime boundary with external-resource lifecycle risk`

**Validator Profile (optional):**
- Controller-selected: `<none>`
- Selection basis: `lifecycle tests plus backend boundary verification`

**Specification Coverage:**
- Admission may read configuration metadata but must not instantiate external
  resources; activation instantiates once and owns cleanup.
- Reuse the existing lazy factory/resource-factory `CapabilityBinding` and
  `CapabilityScope` semantics rather than introducing a second provider-binding
  plan abstraction.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/capabilities.py:prepare_capability_context`, `admit_capability_context`, `CapabilityResolver.admit`
- Inspect: `src/foresight_os/runtime/external_signals.py:load_hosted_mcp_bindings`, `create_hosted_mcp_tool`
- Inspect: `src/foresight_os/runtime/workflow.py:prepare_capability_context` call site and `src/foresight_os/runtime/execution_gate.py`
- Modify: the capability preparation and hosted binding boundary; represent
  admitted hosted providers with existing lazy `CapabilityBinding` factories,
  keep provider construction in activation only, and preserve caller-owned
  bindings
- Verify: `tests/test_capabilities.py`, `tests/test_external_signals.py`, `tests/test_execution_gate.py`

**Dependencies:**
- Task 1 must establish stable effective contract fingerprints before admission
  and activation fingerprints are compared.

**Authority:**
- Preauthorized local actions: `edit capability/runtime binding code and use fake provider factories in focused tests`
- Stop for: `a provider requires a live network/authentication call to determine metadata availability or an existing adapter contract would change`

**Steps:**
- [ ] Step 1: Split hosted-provider metadata discovery from live tool creation.
  Admission may validate credential presence, provider policy, requested
  capability, and a stable redacted fingerprint, then retain an existing
  lazy `CapabilityBinding` whose factory captures the admitted configuration;
  it must not call the factory or create an `agent_framework` MCP object.
- [ ] Step 2: Ensure activation invokes each required lazy factory once, reuses
  caller-owned bindings without replacing them, and keeps
  `CapabilityScope.close()` responsible for owned resources.
- [ ] Step 3: Add tests proving zero factory calls during admission, exactly one
  creation during activation, stable fingerprints, missing-credential and
  unavailable-capability failures, and single teardown on success, cancellation,
  and failure.

**Verification:**
- [ ] `python -m pytest -q tests/test_capabilities.py tests/test_external_signals.py tests/test_execution_gate.py`
- Expected: admission has no live provider objects; activation and cleanup are
  deterministic and existing capability failure classifications remain intact.

**Exit Criteria:**
- Hosted MCP and external adapter constructors are reachable only from runtime
  activation paths, with no duplicate creation or leaked owned resource.

### Task 3: Make release evidence cover changed briefs and history

**Purpose:**
- Replace nominal scenario labels with workloads that detect the correctness and
  persistence regressions this follow-up is intended to address.

**Task Function:**
- Extend the deterministic measurement harness and comparator without changing
  analytical truth or silently rewriting historical evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `measurement contract and receipt provenance are shared by later optimization tasks`

**Validator Profile (optional):**
- Controller-selected: `<none>`
- Selection basis: `harness tests plus reproducible receipt inspection`

**Specification Coverage:**
- A release cannot claim optimization while changed-brief correctness,
  history scaling, required timing paths, or baseline/release provenance remain
  unmeasured or mismatched.

**Required Skills:**
- `skill-performance-optimization`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `evaluation/probes/optimization_measurement.py:_revision_metadata`
- Inspect/modify: `evaluation/probes/run_optimization_probe.py` workload assembly,
  scenario workload fields, timing paths, and thresholds
- Inspect/modify: `evaluation/probes/compare_optimization_receipts.py` required
  evidence and acceptance gates
- Verify: `tests/test_optimization_measurement.py` and generated artifacts under
  `work/`

**Dependencies:**
- Tasks 1 and 2 must provide a brief-aware fixture, stable sparse/effective
  contract parity assertions, and a stable admission/activation boundary.

**Authority:**
- Preauthorized local actions: `edit probes/tests and create new source-specific baseline/release receipts under work/`
- Stop for: `a probe requires credentials, network mutation, or rewriting an existing historical receipt rather than creating a new pair`

**Steps:**
- [ ] Step 1: Add a real same-workbook changed-brief workload that changes
  scope or a stage override and asserts one correct reassessment, preserved
  source identity, expected reuse/invalidation, and distinct analytical output.
- [ ] Step 2: Replace the two-run history alias with configurable workloads in
  which `history-10` is the mandatory fast scaling check, `history-100` is the
  mandatory release gate, and `history-1000` is bounded stress/manual evidence
  promoted only if the smaller workloads cannot characterize growth. Record
  compact aggregate measurements, endpoint state/token hashes, sizes,
  load/validation counts, wall time, and sampled milestones; do not persist
  hundreds or thousands of full snapshots.
- [ ] Step 3: Record `dirty` state, exact baseline/candidate commit, source-tree
  hash, harness hash, fixture identity, workload parameters, and relevant
  environment in receipts. Baseline and candidate source identities must differ,
  while both worktrees remain clean and share the same harness, fixture,
  workload, and relevant environment identities. Each receipt's source-tree
  hash must match its own clean commit. Reject mismatched comparisons and retain
  old artifacts as historical evidence.
- [ ] Step 4: Enable timing-path gates with repeated samples for at least the
  cold-workbook, repeated-investigation, changed-brief, `history-10`,
  `history-100`, and selected-sheet stress paths. Apply each path's own
  absolute noise floor plus the existing relative threshold; do not let an
  aggregate p95 hide a path-specific regression. Add comparator tests proving
  that missing changed-brief/history/timing evidence yields `NOT_MEASURED`, not
  a pass.
- [ ] Step 5: After Tasks 1-3 pass, create a verified local checkpoint commit.
  Use that checkpoint as the optimization baseline for Tasks 4-5. Do not use
  `2081f6caa78fe771b52014b6ad4d99c2b4118845` as the candidate acceptance
  baseline; it remains informational context only.

**Verification:**
- [ ] `python -m pytest -q tests/test_optimization_measurement.py`
- [ ] Run baseline and release probe modes from clean worktrees and compare the
  resulting immutable receipt pair.
- Expected: changed-brief, `history-10`, and `history-100` are `VERIFIED`,
  required timing paths are gated, and the comparator refuses dirty or mismatched
  pairs before Tasks 4-5 begin.

**Exit Criteria:**
- Task 3 produces trustworthy evidence that can select or reject the persistence
  and XLSX optimizations in Tasks 4-5.

### Task 4: Optimize persistence only where history evidence justifies it

**Purpose:**
- Reduce repeated full-state work and bound pending-token metadata without
  weakening concurrency, recovery, idempotency, or replay protection.

**Task Function:**
- Apply the smallest persistence change supported by Task 3 measurements.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `stateful backend optimization with stale-write and recovery risk`

**Validator Profile (optional):**
- Controller-selected: `<none>`
- Selection basis: `focused persistence regression tests and representative history trace`

**Specification Coverage:**
- Pending publication and terminal settlement remain atomic under the existing
  file lock; stale revisions/tokens are rejected; recovery restores valid state;
  history growth is bounded or explicitly justified.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`

**Files And Symbols:**
- Inspect: `src/foresight_os/persistence/analysis_store.py:commit_revision`, `_save_pending_unlocked`, `_load_path`, `_remember_consumed_pending_token`, `_merge_states`
- Modify: only the measured full-state load/validation path and consumed-token retention mechanism
- Verify: `tests/test_persistence.py`, `tests/test_execution_persistence.py`, `tests/test_approval_persistence.py`, `tests/test_invalidation.py`

**Dependencies:**
- Task 3 must provide the verified checkpoint baseline and show persistence cost
  or metadata growth that exceeds the agreed measurement noise floor. If it does
  not, record the optimization as deferred and retain the current implementation.

**Authority:**
- Preauthorized local actions: `edit AnalysisStore and focused persistence tests only after Task 3 identifies a measurable bottleneck`
- Stop for: `any stale-write, pending-recovery, replay, rollback, or schema-migration ambiguity`

**Steps:**
- [ ] Step 1: Do not introduce a metadata sidecar, persistence index, journal,
  or new store. Reuse raw JSON already read under the existing lock. If a
  metadata-first parse is justified, read each JSON file once, inspect its
  revision/token/base identity, fail stale cases early, and hydrate/validate
  only when settlement proceeds; do not reopen the same file.
- [ ] Step 2: Replace the unbounded consumed-token set with a revision-aware
  tombstone representation that retains every token needed for the current
  accepted base and live pending revision, prunes older entries only when the
  revision guard makes replay impossible, and migrates the existing list format.
- [ ] Step 3: Add regression tests for concurrent mutation, stale pending
  settlement, rejected pending recovery, repeated replacement, restored
  snapshots, old-token replay after pruning, and legacy token-file migration.
- [ ] Step 4: Re-run at least the mandatory `history-10` and `history-100`
  workloads against the Task 3 checkpoint baseline and compare wall time, state
  size, token metadata size, load/validation counts, and final state hashes.
  Use `history-1000` only as bounded stress when applicable.

**Verification:**
- [ ] `python -m pytest -q tests/test_persistence.py tests/test_execution_persistence.py tests/test_approval_persistence.py tests/test_invalidation.py`
- [ ] Re-run the growing-history probe and inspect final state/recovery receipts.
- Expected: all stale/recovery/replay tests pass and the measured history cost
  improves without changing accepted or rejected state semantics.

**Exit Criteria:**
- Persistence is changed only if the evidence shows a material bottleneck, and
  the new implementation has explicit replay and recovery proof.

### Task 5: Measure and narrow XLSX selected-sheet work

**Purpose:**
- Avoid XML work for excluded sheets and determine whether whole-workbook
  `openpyxl` materialization is a material resource bottleneck before changing
  reader semantics.

**Task Function:**
- Improve the safe selected-sheet path and conditionally prototype a read-only
  path with parity evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `reader optimization with formula/provenance/format compatibility risk`

**Validator Profile (optional):**
- Controller-selected: `<none>`
- Selection basis: `reader parity tests and resource measurements`

**Specification Coverage:**
- Selection, hidden rows, merged cells, formulas, cached formula values,
  provenance, limits, cancellation, and error classifications remain stable.

**Required Skills:**
- `skill-performance-optimization`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/runtime/local_toolbelt.py:_preflight_xlsx_archive`, `_in_selection`, XLSX reader path
- Verify: `tests/test_local_toolbelt.py`, `tests/test_workbook_engine.py`,
  `tests/test_workbook_path_parity.py`, and a generated stress fixture/probe

**Dependencies:**
- Task 3 must provide the verified checkpoint baseline, stable reader metrics,
  and a changed-brief fixture so selected material can be compared independently
  of persistence cost.

**Authority:**
- Preauthorized local actions: `edit selected-sheet preflight/reader code and create bounded synthetic workbook fixtures`
- Stop for: `read-only parity fails for formulas, cached values, hidden rows, merged cells, provenance, or cancellation`

**Steps:**
- [ ] Step 1: Make archive preflight skip opening excluded worksheet XML while
  retaining archive-wide expanded-byte, workbook-structure, and cancellation
  checks. Add counters proving excluded sheets are not parsed.
- [ ] Step 2: Generate the stress fixture deterministically at probe/test runtime
  with many large unrelated worksheets and one small selected worksheet; do not
  commit a giant XLSX binary. Measure cold time, peak RSS/allocation, archive
  scan work, and selected result identity as unrelated sheet size grows.
- [ ] Step 3: If whole-workbook allocation scales materially, prototype a
  `read_only=True` selected-sheet source view behind the existing reader
  contract. Keep the eager path available until all parity tests and formula
  cached-value cases pass; otherwise record the read-only change as deferred.

**Verification:**
- [ ] `python -m pytest -q tests/test_local_toolbelt.py tests/test_workbook_engine.py tests/test_workbook_path_parity.py`
- [ ] Run the selected-sheet stress probe with formula-free and formula-bearing
  selections.
- Expected: excluded-sheet XML work is absent, selected results are unchanged,
  the runtime-generated fixture is reproducible, and any read-only path is
  adopted only with measured resource improvement and complete parity.

**Exit Criteria:**
- The selected-sheet path has evidence-backed resource behavior and no reader
  semantic regression; unsafe reader experiments remain unmerged and documented.

### Task 6: Reduce redundant domain-default construction and reconcile guidance

**Purpose:**
- Remove safe repeated default construction after declaration semantics are
  correct and document the final resolution boundary.

**Task Function:**
- Make each domain own one immutable default factory/cache and align maintained
  architecture guidance with the resulting contract flow.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `small low-risk cleanup after correctness and measurement gates`

**Validator Profile (optional):**
- Controller-selected: `<none>`
- Selection basis: `registry tests and final architecture review`

**Specification Coverage:**
- Requesting one domain default does not construct unrelated domain contracts;
  the engine retains defensive resolution until Task 1 parity is complete, and
  only one effective contract is used for identity/materialization/calculation.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Modify: `src/foresight_os/analysis/workbook_registry.py:DomainWorkbookSpec`,
  `_SPECS`, `default_workbook_contract_for`
- Inspect/modify: `src/foresight_os/analysis/workbook_inputs.py` and
  `src/foresight_os/analysis/workbook_engine.py` resolution boundary
- Verify: `tests/test_workbook_registry.py`, `tests/test_workbook_runner.py`,
  `docs/architecture.md`

**Dependencies:**
- Tasks 1-3 complete, with Tasks 4-5 either completed or explicitly deferred by
  evidence; no unresolved contract or reader parity defect remains.

**Authority:**
- Preauthorized local actions: `edit registry/default factories, focused tests, and owning architecture guidance`
- Stop for: `moving resolution across public compatibility boundaries or changing analyzer fingerprints without an explicit migration decision`

**Steps:**
- [ ] Step 1: Replace the all-domains dictionary construction with one
  per-domain factory or cached immutable default contract; preserve existing
  `DomainWorkbookSpec` lookup and analyzer metadata APIs.
- [ ] Step 2: Measure construction count or use a focused factory test to prove
  an individual request does not instantiate unrelated defaults.
- [ ] Step 3: Document sparse declaration -> effective contract -> admitted
  bundle -> snapshot -> selected material -> calculation flow and record any
  deferred persistence/reader/dependency work.

**Verification:**
- [ ] `python -m pytest -q tests/test_workbook_registry.py tests/test_workbook_runner.py`
- Expected: all domains retain the same effective defaults and analyzer
  fingerprints, with no unrelated default construction.

**Exit Criteria:**
- Registry construction is bounded and architecture guidance matches the
  tested ownership boundary.

## Verification

Run from the clean execution worktree after all selected tasks are complete:

- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- repository Markdown-link checker, because architecture and plan guidance may change
- `git diff --check`
- baseline/release optimization probes and the receipt comparator from clean,
  source-identified worktrees
- use the post-Task-3 verified checkpoint as the optimization baseline; ensure
  the candidate source commit differs from it, both worktrees are clean, the
  harness/fixture/workload/environment identities match, and each receipt's
  source-tree hash matches its respective commit
- focused backend boundary traces for sparse contract resolution, capability
  admission/activation, pending recovery/replay, and selected XLSX reads
- inspect the final diff, generated receipt lineage, dirty-state flags, and
  source-tree/harness hashes before any publication decision

## Completion Criteria

The plan is ready for completion verification when:

1. sparse declaration semantics are preserved through validation and persistence
2. direct, persisted, and approved execution share effective contract identity
3. capability admission creates no hosted/external resource and activation
   creates each required resource once with deterministic cleanup
4. `changed_brief = VERIFIED`, `history-10 = VERIFIED`, and
   `history-100 = VERIFIED`; required timing paths are gated with repeated
   samples. Only `history-1000` stress, persistence optimization with no
   material bottleneck, a read-only XLSX path with no measured resource benefit,
   and dependency cleanup may be recorded as justified deferrals.
5. persistence changes, if any, preserve locking, stale checks, recovery,
   idempotency, and replay protection under focused tests
6. reader changes, if any, preserve formula/cached-value/provenance/selection
   semantics and demonstrate resource benefit
7. domain default construction is per-domain and architecture guidance is
   reconciled with source behavior
8. dependency cleanup remains a separate follow-up unless a new approved scope
   explicitly adds clean-wheel packaging work
9. all final verification commands pass and fresh verification returns
   `verified`

