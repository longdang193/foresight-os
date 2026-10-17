---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: foresight-os-correctness-first-deletion-pass
targets:
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/runtime/capabilities.py
  - src/foresight_os/runtime/executors.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/analysis/workbook.py
  - src/foresight_os/analysis/workbook_inputs.py
  - src/foresight_os/analysis/evidence_workflow.py
  - src/foresight_os/analysis/result_committer.py
  - src/foresight_os/domain/models.py
  - src/foresight_os/domain/validation.py
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/optimization_measurement.py
  - evaluation/probes/compare_optimization_receipts.py
  - evaluation/README.md
  - docs/evidence-and-evaluation.md
  - tests/test_local_toolbelt.py
  - tests/test_runtime_boundaries.py
  - tests/test_result_committer.py
  - tests/test_selective_reuse.py
  - tests/test_evidence_workflow.py
  - tests/test_analysis_input_contract.py
  - tests/test_brief_portability.py
  - tests/test_orchestration_patterns.py
  - tests/test_optimization_measurement.py
---

# ForesightOS Correctness-First Deletion Pass Plan

## Goal

Close the remaining correctness and lifecycle gaps identified in the supplied
review, repair the measurement protocol, and only then inspect a bounded,
optional deletion tail. Preserve the existing trust model:

```text
approved brief
→ normalized investigation identity
→ bounded source capture
→ provenance-aware workbook view
→ deterministic analysis
→ canonical validation
→ transactional persistence
→ independent review
→ deliverable and cleanup
```

This is a bounded correctness-and-measurement pass, not a new orchestration
engine, cache layer, provenance model, analysis store, or controller rewrite.
The reviewed activation base is remote `main` at
`14bd69644b7012639c00a65fa94cdd67f52b4c62`; Task 1 must re-check that SHA
before activation. The primary checkout has unrelated tracked and untracked
changes. Preserve it and execute in an isolated worktree; do not require those
unrelated changes to be reconciled into this pass.

## Review Of The Verdict

The supplied verdict is directionally correct and should be adopted with the
following implementation constraints:

- **Adopt the order:** freeze the corrected measurement protocol before
  performance optimization; correctness closure precedes hot-path changes; the
  deletion tail is optional after the core evidence is accepted.
- **Keep one cache owner:** extend the existing `WorkbookContext` in
  `src/foresight_os/runtime/local_toolbelt.py` and do not introduce
  `runtime/workbook_context.py` merely to match an earlier plan.
- **Keep durable reuse canonical:** `StageReceipt` plus canonical result hashes
  remain the durable stage-reuse authority. `stage_cache` may remain only as a
  compatibility boundary until all live consumers and tests migrate.
- **Do not make timing a correctness gate:** the proposed 20% improvement is a
  decision threshold for a substantial structural refactor, not permission to
  weaken immutability, provenance, bounds, cancellation, review invalidation,
  or cleanup when timing is noisy.
- **Resolve current-base drift first:** Task 1 must inventory the current
  `WorkbookContext` and shared workbook-input/mapping owner, including
  `analysis/workbook_inputs.py`, before adding any new type or file.
- **Prepared identity is conditional:** first determine whether the existing
  `NormalizedIntent` owner can hold the needed fingerprints and identity; add a
  separate value type only if it has a distinct lifetime or invariant.
- **Keep optional work optional:** domain-wrapper consolidation, large
  `run_recipe_async()` restructuring, topology-policy changes, and CI/process
  changes cannot block the core pass.
- **Separate evidence classes:** local workbook correctness and reuse are
  mandatory and credential-free; provider/MCP and model-quality evidence remain
  separate optional or release-level evidence.

## Implementation Outcomes

### Transactionally safe, immutable analytical reuse

Cached `AnalysisResult` values are recursively immutable from the cache's
perspective, while serialization and mutable external adapters receive explicit
copies. Read and analysis publication share one run-owned context, enforce
aggregate entry and retained-byte limits, and roll back inserts, evictions and
accounting on cancellation, rejection, or failure. Standalone workbook reads
retain the same byte-boundary behavior as capability-dispatched reads.

### Strict analytical boundaries

Explicit source-column mappings are validated against the table that consumes
them and fail clearly when absent; they never silently fall back to canonical
columns. Single-output and multi-output synthesis share one structural bound,
canonical validation, provenance, conflict, and cancellation boundary.

### Measured core with an optional deletion tail

The mandatory pass ends after correctness closure, measured warm-path
optimization, and truthful matched performance evidence. Repeated brief
normalization, stage-cache removal, domain-wrapper consolidation,
`run_recipe_async()` restructuring, topology-policy changes, and CI/process
changes are follow-ups activated only when consumer inventory and measurement
justify them.

### Measured and truthful optimization evidence

The optimization probe measures the real shared-context repeated-investigation
path with distributions and cache/parse/hash counters. Local workbook evidence,
orchestration evidence, and provider/MCP evidence are reported separately.
Missing or unavailable dimensions remain explicitly blocked, deferred, or
`NOT_MEASURED`; they are never converted into a pass.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-plan-document-reviewer`, `skill-using-git-worktrees`, `skill-executing-plans`, `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: isolated worktree from the exact activation SHA; required because the primary checkout is dirty
- Commit policy: `no commits during execution`; identify verified states with a deterministic source-tree digest plus `git diff` evidence unless a later approved execution plan grants checkpoint commits
- Preauthorized local actions: inspect source/tests/docs, create the declared isolated worktree, add or modify declared code/tests/docs/evaluation files, run declared local verification, and write bounded receipts under the task-owned `work/` directory
- User-approval actions: commit, push, merge, PR publication, external/provider writes, destructive cleanup or reset of the current checkout, changing the reviewed base, and broad scope expansion
- Parallel ownership: none; cache, lifecycle, synthesis, and evidence changes share contracts and remain serialized
- Sequential fallback: Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 8; activate Tasks 6–7 only as separately justified follow-ups

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/correctness-first-deletion-pass`
- Base commit: `14bd69644b7012639c00a65fa94cdd67f52b4c62`, revalidated by Task 1 before activation
- Expected workspace: current checkout remains dirty and preserved; implementation uses an isolated worktree where only unexpected, undeclared, or unrelated modifications are blockers
- Next action: none; final verification is recorded and Git disposition remains separate
- Blockers: `none`; Tasks 6–7 are explicitly deferred optional follow-ups

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | isolated | `codex` | none | owner inventory, frozen harness contract, defect reproduction | `work/correctness-first-deletion-20261017/task-1/` |
| Task 2 | `completed` | isolated | `codex` | Task 1 | immutable cache and exact transactional publication tests | `work/correctness-first-deletion-20261017/task-2/` |
| Task 3 | `completed` | isolated | `codex` | Task 2 | exact mappings, bounded synthesis, active cancellation, portability tests | `work/correctness-first-deletion-20261017/task-3/` |
| Task 4 | `completed` | isolated | `codex` | Task 3 | matched-base measurement receipt using the frozen harness | `work/correctness-first-deletion-20261017/task-4/` |
| Task 5 | `completed` | isolated | `codex` | Task 4 | hot-path counters, authority lifetime, retained-accounting and final comparison | `work/correctness-first-deletion-20261017/task-5/` |
| Task 6 | `deferred` | isolated | `unresolved` | Task 5, optional activation | consumer inventory and compatibility proof for any deletion | `work/correctness-first-deletion-20261017/task-6/` |
| Task 7 | `deferred` | isolated | `unresolved` | Task 5, optional activation | independent policy/process evidence if activated | `work/correctness-first-deletion-20261017/task-7/` |
| Task 8 | `completed` | isolated | `codex` | Tasks 1–5; Tasks 6–7 only if activated | final core verification and exact-tree evidence | `work/correctness-first-deletion-20261017/task-8/` |

## Task Breakdown

### Task 1: Reconcile current owners and freeze the baseline

**Purpose:**
- Establish the exact reviewed base, preserve the dirty primary checkout,
  reconcile live owners, and freeze one measurement protocol before any
  performance change.

**Task Function:**
- Source reconciliation and defect reproduction.

**Template Profile:**
- Controller-selected: `<unresolved while task is pending>`
- Selection basis: source ambiguity and current-base risk must be resolved before selecting an implementation profile.

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: lead controller owns the baseline gate.

**Specification Coverage:**
- Review conclusions on cache mutability, rejected publication, direct-path
  bypass, table-local mappings, synthesis bounds, warm-hit overhead, stage
  reuse, and benchmark validity; measurement chronology and evidence classes.

**Required Skills:**
- `skill-plan-document-reviewer`, `skill-using-git-worktrees`, `skill-systematic-debugging`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/local_toolbelt.py:WorkbookContext`, `WorkbookReadCache`, `spreadsheet_read`, `data_analysis`
- Inspect: `src/foresight_os/runtime/workflow.py:_synthesize_stage_outputs`, `_stage_cache_key`, `run_recipe_async`
- Inspect: `src/foresight_os/analysis/workbook_inputs.py` and its shared mapping/normalization owner
- Inspect: `src/foresight_os/analysis/evidence_workflow.py`, `tests/test_analysis_input_contract.py`, `tests/test_brief_portability.py`, and `tests/test_orchestration_patterns.py`
- Inspect: `src/foresight_os/runtime/workflow.py:stage_cache` consumers and `StageReceipt` consumers
- Inspect: `evaluation/probes/run_optimization_probe.py`, `optimization_measurement.py`, `compare_optimization_receipts.py`
- Modify: focused regression tests only where a reviewed defect is reproducible
- Verify: current `git diff`, current plan inventory, and baseline receipt

**Dependencies:**
- None. The current primary checkout must remain untouched except for the new
  plan file already being recorded.

**Authority:**
- Preauthorized local actions: create the isolated worktree, inspect declared owners, freeze the measurement contract, add focused reproduction tests, and run the declared baseline probe.
- Stop for: a changed intended-main SHA, unexpected or unrelated modifications in the implementation worktree, destructive workspace operations, or a defect that requires an unapproved product decision.

**Steps:**
- [x] Step 1: Pin the full intended-main SHA
  `14bd69644b7012639c00a65fa94cdd67f52b4c62` or record the replacement SHA
  selected at activation, then capture the source-tree identity and changes
  since the supplied verdict.
- [x] Step 2: Create minimal reproductions for nested cached-result mutation,
  rejected analysis publication, direct workflow bypass, explicit mapping
  fallback, single-output synthesis bypass, and warm-hit authority scanning.
- [x] Step 3: Decide the canonical owners from the live source: extend
  `WorkbookContext` in `local_toolbelt.py`, use `workbook_inputs.py` for shared
  workbook-input/mapping logic when present, and prefer existing
  `NormalizedIntent` before introducing a prepared identity type.
- [x] Step 4: Freeze the measurement protocol before optimization: exact tree
  SHA/tree digest, harness version, fixture hash, workload identity, limits,
  sample count, warm-up policy, aggregation method, environment, counters,
  thresholds, and `FINAL_ONLY`/`not_measured` rules.
- [x] Step 5: Run the focused suite and the frozen baseline protocol without
  claiming an optimization; store bounded receipts under the task-owned
  `work/` directory and keep correctness failures separate from timing.

**Verification:**
- [ ] `python -m pytest -q tests/test_local_toolbelt.py tests/test_runtime_boundaries.py tests/test_result_committer.py tests/test_selective_reuse.py tests/test_evidence_workflow.py tests/test_optimization_measurement.py`
- [ ] `python evaluation/probes/run_optimization_probe.py --mode baseline --fixture tests/fixtures/analyst_multisheet.xlsx --output work/correctness-first-deletion-20261017/task-1/baseline/receipt.json`
- Expected: defects are either reproduced with focused assertions or marked
  `NOT_REPRODUCED` with the source evidence explaining why; baseline output is
  complete enough for the frozen matched protocol, carries exact source and
  harness identity, and does not call provider evidence a local workbook result.

**Exit Criteria:**
- The implementation base and owners are reconciled, the measurement contract
  is frozen, the baseline is recorded, and no task proceeds on an unverified
  architecture or benchmark assumption.

### Task 2: Make workbook and analysis publication immutable and transactional

**Purpose:**
- Establish one run-owned mutation boundary for workbook reads, deterministic
  analysis, retained authority, and aggregate budget accounting; publication
  becomes reusable only after every check succeeds.

**Task Function:**
- Runtime state ownership and failure-safe cache implementation.

**Template Profile:**
- Controller-selected: `<unresolved while task is pending>`
- Selection basis: backend lifecycle risk, shared-state invariants, and cancellation semantics.

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: focused backend proof is owned by the lead controller.

**Specification Coverage:**
- Deep cache immutability, rejected-publication rollback, shared direct and
  dispatched paths, standalone byte limits, authority retention, serialized
  mutation, exact rollback, and cleanup.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/local_toolbelt.py:WorkbookContext`, `WorkbookReadCache`, `AnalysisResult`, `spreadsheet_read`, `data_analysis`, authoritative-record helpers
- Modify: `src/foresight_os/runtime/capabilities.py:CapabilityScope` and deterministic dispatch adapters
- Modify: `src/foresight_os/analysis/evidence_workflow.py` direct workbook path
- Verify: `tests/test_local_toolbelt.py`, `tests/test_runtime_boundaries.py`, and new context-focused tests

**Dependencies:**
- Task 1 complete; the chosen existing owners and frozen measurement protocol
  must be recorded before moving state.

**Authority:**
- Preauthorized local actions: modify the existing runtime owners and focused tests, serialize context mutation, add exact rollback coverage, and run local backend verification.
- Stop for: a need for a second durable cache/store, changed provenance semantics, destructive migration, or an external dependency required to prove the local boundary.

**Steps:**
- [ ] Step 1: Replace mutable nested cache payloads with recursively immutable
  internal values and explicit mutable serialization copies; preserve stable
  deterministic identity and provenance.
- [ ] Step 2: Serialize shared-context mutation and prevent public/direct and
  capability-dispatched adapters from opening nested publication transactions.
- [ ] Step 3: Move read and analysis publication into one context transaction
  that snapshots prior entries, staged inserts, evictions, authority
  registration, and byte accounting; commit only after cancellation and
  aggregate limits pass.
- [ ] Step 4: Make failed, cancelled, oversized, and budget-rejected work leave
  no newly reusable state while preserving earlier valid committed entries;
  restore displaced entries and retained-byte accounting exactly on rollback.
- [ ] Step 5: Inject failures during computation, immediately before
  publication, during aggregate-budget validation, and after intermediate
  structures exist; verify cancellation reaches the real production boundary.
- [ ] Step 6: Route capability-dispatched and direct deterministic analysis
  through the same context method; keep public adapters thin and compatible.
- [ ] Step 7: Ensure standalone `spreadsheet_read` enforces the same source-byte
  and expanded-content boundaries before caching or authority publication.

**Verification:**
- [ ] `python -m pytest -q tests/test_local_toolbelt.py tests/test_runtime_boundaries.py tests/test_evidence_workflow.py`
- Expected: attempted mutation of a returned cached result cannot alter a later
  hit or its identity; rejected/cancelled publication leaves cache size,
  authority state, and retained-byte counters unchanged while earlier valid
  entries survive; direct and dispatched paths produce equivalent bounded
  results and cleanup status.

**Exit Criteria:**
- [x] There is one production mutation owner for workbook and analysis reuse,
  all covered failure paths settle without reusable-state corruption, and
  focused tests prove the boundary.
- Evidence: `work/correctness-first-deletion-20261017/task-2/receipt.json` and
  `work/correctness-first-deletion-20261017/task-2/verification.md`.

### Task 3: Enforce exact mappings and one bounded synthesis boundary

**Purpose:**
- Close the analytical correctness holes that can silently change meaning or
  bypass structural safeguards.

**Task Function:**
- Contract-boundary hardening and cancellation-aware result synthesis.

**Template Profile:**
- Controller-selected: `<unresolved while task is pending>`
- Selection basis: cross-module contract reasoning and material failure-path risk.

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: focused canonical-result and boundary tests are sufficient.

**Specification Coverage:**
- Table-local explicit mappings, independent brief portability, uniform
  single/multi-output limits, conflict detection, canonical provenance, and
  production cancellation.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Modify: `src/foresight_os/analysis/workbook_inputs.py` shared mapping/normalization owner, or the owner confirmed by Task 1
- Modify: `src/foresight_os/analysis/workbook.py:read_workbook`, `calculate_case_metrics` only where the reconciled input contract requires it
- Modify: `src/foresight_os/analysis/evidence_workflow.py` table selection and deterministic analysis call path
- Modify: `src/foresight_os/runtime/workflow.py:_synthesize_stage_outputs`, `run_recipe_async`
- Modify: `src/foresight_os/analysis/result_committer.py:normalize_stage_result`
- Modify if needed: `src/foresight_os/runtime/executors.py:run_agent_with_tool_fallback` and cancellation checkpoints
- Verify: `tests/test_local_toolbelt.py`, `tests/test_evidence_workflow.py`, `tests/test_result_committer.py`, `tests/test_runtime_boundaries.py`, `tests/test_analysis_input_contract.py`, `tests/test_brief_portability.py`, `tests/test_orchestration_patterns.py`

**Dependencies:**
- Task 2 complete so analysis calls cannot bypass the publication boundary.

**Authority:**
- Preauthorized local actions: change the reconciled mapping, synthesis, and cancellation owners and add small independent portability fixtures/tests.
- Stop for: changing canonical record schemas without a separate approved specification, weakening legacy omitted-mapping behavior, or adding a new orchestration framework.

**Steps:**
- [ ] Step 1: Resolve the canonical columns consumed by each target table, then
  validate every explicit source mapping against that table; omitted mappings
  retain compatibility behavior, explicit missing mappings fail closed.
- [ ] Step 2: Send one-output and multi-output results through the same bounded
  normalization/structural validation boundary; enforce record, relationship,
  depth, payload, and normalization-operation limits consistently.
- [ ] Step 3: Preserve canonical references and provenance while detecting
  conflicting duplicate IDs; do not silently drop invalid relationships.
- [ ] Step 4: Pass cancellation through the actual production synthesis
  invocation and add real checkpoints around material pure work; use existing
  worker infrastructure only for materially expensive pure synthesis, not
  durable commits. Cover sequential recovery after validation failure and
  cancellation or corrected output, not only direct helper calls.
- [ ] Step 5: Add small independent fixtures covering different periods, units,
  mappings, sheets, malformed values, hidden rows, duplicate records, and
  same-source/different-brief semantics, wrong-sheet explicit mappings,
  contract-only changes with identical source bytes, conflicting canonical
  records, invalid references, and cancellation after intermediate results
  exist but before publication.

**Verification:**
- [ ] `python -m pytest -q tests/test_local_toolbelt.py tests/test_evidence_workflow.py tests/test_result_committer.py tests/test_runtime_boundaries.py`
- Expected: explicit mappings never fall back silently; single and aggregate
  synthesis enforce identical limits; cancellation settles and remains visible
  to the caller; independent briefs preserve expected values and provenance.

**Exit Criteria:**
- [x] Meaning-changing inputs fail clearly, all production output shapes share
  one bounded validation boundary, and cancellation cannot leave partial
  reusable or durable analytical state.
- Evidence: `work/correctness-first-deletion-20261017/task-3/receipt.json` and
  `work/correctness-first-deletion-20261017/task-3/verification.md`.

### Task 4: Establish the matched performance baseline

**Purpose:**
- Run the frozen harness against the selected original/base tree before any
  hot-path optimization and preserve correctness failures separately from
  timing results.

**Task Function:**
- Matched benchmark execution and evidence validation.

**Template Profile:**
- Controller-selected: `<unresolved while task is pending>`
- Selection basis: performance work is accepted only with identical workload
  and correctness proof.

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: focused counters and resource tests are owned by the lead.

**Specification Coverage:**
- Exact tree/harness/fixture identity, workload and limits, sample counts,
  warm-up and aggregation rules, environment details, counters, thresholds,
  and `FINAL_ONLY`/`not_measured` handling.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Modify: `evaluation/probes/run_optimization_probe.py:_measure_workbook`, `_run`, and receipt construction
- Modify: `evaluation/probes/optimization_measurement.py` receipt schema and metrics
- Modify: `evaluation/probes/compare_optimization_receipts.py:compare`, `compare_repeats`
- Verify: `tests/test_optimization_measurement.py`, `evaluation/README.md`, and `docs/evidence-and-evaluation.md`

**Dependencies:**
- Tasks 2–3 complete; the frozen protocol must be runnable against the selected
  base before Task 5 changes runtime performance behavior.

**Authority:**
- Preauthorized local actions: update the declared benchmark scripts, receipt fields, tests, and maintained evaluation guidance.
- Stop for: changing acceptance thresholds without a documented rationale, changing the workload after base measurement, selecting a favorable rerun, or mixing provider latency into the local workbook gate.

**Steps:**
- [ ] Step 1: Freeze and record the exact source-tree SHA/tree digest, harness
  version, fixture hash, workload identity, limits, sample count, warm-up policy,
  aggregation method, environment, counters, and thresholds.
- [ ] Step 2: Run the same corrected harness against the selected original/base
  tree for shared-context repeated investigations, warm reads, analyst/validator
  reuse, different selections, multi-workbook behavior, retained-context growth,
  and cancellation.
- [ ] Step 3: Record correctness failures independently; unsupported new
  dimensions are `FINAL_ONLY` or `not_measured`, never synthesized into a green
  baseline.
- [ ] Step 4: Preserve the exact baseline receipt and comparison inputs for the
  final post-optimization run.

**Verification:**
- [ ] `python -m pytest -q tests/test_optimization_measurement.py`
- [ ] `python evaluation/probes/run_optimization_probe.py --mode baseline --fixture tests/fixtures/analyst_multisheet.xlsx --output work/correctness-first-deletion-20261017/task-4/base/receipt.json`
- Expected: the receipt carries exact source and harness identity, the workload
  is frozen for comparison, correctness and performance are separate, and
  unavailable dimensions are explicitly labelled.

**Exit Criteria:**
- A matched baseline exists before Task 5 changes hot-path behavior.

### Task 5: Optimize the measured hot path

**Purpose:**
- Remove measured warm-path overhead without adding a cache layer or weakening
  source currentness, provenance, authority lifetime, or cleanup semantics.

**Task Function:**
- Measured hot-path optimization with retained-state invariants.

**Template Profile:**
- Controller-selected: `<unresolved while task is pending>`
- Selection basis: reproducibility, measurement validity, and release evidence risk.

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: measurement tests and receipt comparison provide bounded proof.

**Specification Coverage:**
- O(1) authority validity, construction-time retained weights, bounded memory,
  no monotonic growth, and matched before/after evidence.

**Required Skills:**
- `skill-performance-optimization`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/local_toolbelt.py:WorkbookContext`, `WorkbookReadCache`, authority helpers, `spreadsheet_read`, `data_analysis`
- Modify: `src/foresight_os/runtime/capabilities.py` only where the shared context is dispatched
- Modify: `evaluation/probes/run_optimization_probe.py` only to consume the frozen protocol
- Modify: `evaluation/probes/optimization_measurement.py`, `compare_optimization_receipts.py` only for measured hot-path fields
- Verify: `tests/test_local_toolbelt.py`, `tests/test_runtime_boundaries.py`, `tests/test_optimization_measurement.py`

**Dependencies:**
- Task 4 complete; the baseline protocol and receipt are immutable comparison inputs.

**Authority:**
- Preauthorized local actions: optimize existing cache bookkeeping, add counters and focused resource tests, and run the frozen protocol against the final tree.
- Stop for: persistent openpyxl storage, timestamps replacing content hashes, unbounded retention, changing the frozen workload, or an optimization that changes currentness or provenance semantics.

**Steps:**
- [x] Step 1: Make cached views carry authority generations/tokens covering all
  measurement and calculation ancestry; keep required authority alive or
  invalidate dependent views atomically.
- [x] Step 2: Replace `len(repr(...))` scans with deterministic construction-time
  retained weights and update internal accounting incrementally. Describe these
  as retained-memory accounting, not RSS or peak allocation.
- [x] Step 3: Ensure the frozen probe captures source captures, capture/currentness
  hashes, parses, read/analysis-cache hits, and retained read/analysis/authority
  counters for warm and repeated-investigation workloads.
- [x] Step 4: Run the identical protocol against the final tree and compare it
  with Task 4; fail closed on mismatched identity, missing mandatory counters,
  resource growth, or correctness changes.
- [x] Step 5: Prove cancellation, cleanup, and prior-valid-entry preservation
  while retained state remains bounded.

**Verification:**
- [x] `python -m pytest -q tests/test_optimization_measurement.py`
- [x] `python -m pytest -q tests/test_local_toolbelt.py tests/test_runtime_boundaries.py tests/test_optimization_measurement.py`
- [x] `python evaluation/probes/run_optimization_probe.py --mode release --fixture tests/fixtures/analyst_multisheet.xlsx --output work/correctness-first-deletion-20261017/task-5/final/receipt.json`
- [x] `python evaluation/probes/compare_optimization_receipts.py --baseline work/correctness-first-deletion-20261017/task-4/base/receipt.json --release work/correctness-first-deletion-20261017/task-5/final/receipt.json --output work/correctness-first-deletion-20261017/task-5/comparison.json`
- Expected: the comparison uses identical workload identity and reports
  correctness, resource, economics, and timing dimensions separately; no
  unmeasured dimension is treated as a pass.

**Exit Criteria:**
- The measured hot path has a matched final comparison, or the exact failed or
  blocked gate is recorded without weakening correctness requirements.

### Task 6: Consolidate prepared identity and durable stage reuse

**Purpose:**
- Optional deletion tail: remove repeated brief normalization, duplicate
  deterministic lifecycle wrappers, or competing normal stage-reuse paths only
  after consumer inventory and the core pass justify each change. This task is
  not required to declare the correctness-and-measurement pass successful.

**Task Function:**
- Runtime deletion and canonical-owner consolidation.

**Template Profile:**
- Controller-selected: `<unresolved while task is pending>`
- Selection basis: broad cross-module change with compatibility and migration risk.

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: focused reuse and persistence tests are required before final review.

**Specification Coverage:**
- One prepared investigation identity, one normal durable reuse authority,
  generic deterministic-analysis hosting, static schema reuse, and bounded
  workflow responsibilities, only where each deletion has a distinct owner,
  compatibility proof, and expected reduction.

**Required Skills:**
- `skill-executing-plans`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect first: the existing `NormalizedIntent`/analysis-input owner,
  `stage_cache` consumers, `StageReceipt` consumers, and repeated domain
  lifecycle callers.
- Modify only proven owners: the existing intent/input owner,
  `src/foresight_os/runtime/workflow.py`, `src/foresight_os/persistence/analysis_store.py`,
  or domain wrappers as consumer inventory requires.
- Verify: `tests/test_selective_reuse.py`, `tests/test_result_committer.py`,
  `tests/test_evidence_workflow.py`, `tests/test_analysis_input_contract.py`,
  `tests/test_brief_portability.py`

**Dependencies:**
- Task 5 complete; Tasks 2–3 preserve publication and output contracts.

**Authority:**
- Preauthorized local actions: inventory consumers and, only if separately activated, migrate declared deterministic callers or remove a proven duplicate while retaining compatibility adapters until tests pass.
- Stop for: deleting a live consumer without migration proof, changing durable receipt semantics without a focused migration test, or broad controller/runtime redesign.

**Steps:**
- [ ] Step 1: Inventory existing `NormalizedIntent`/analysis-input identity and
  determine whether it can safely hold the needed fingerprints; add another
  value type only if its lifetime/invariant is demonstrably distinct.
- [ ] Step 2: Inventory `stage_cache` and `StageReceipt` consumers; remove or
  consolidate only a path proven to duplicate durable reuse rather than serve a
  distinct same-run purpose.
- [ ] Step 3: Compare repeated domain lifecycle code and migrate only identical
  consumers with compatibility tests; do not require all five workflows to move.
- [ ] Step 4: Delete redundant normal-path work from `run_recipe_async`
  opportunistically; a large decomposition is explicitly out of scope unless
  measurement and consumer proof justify it.

**Verification:**
- [ ] `python -m pytest -q tests/test_selective_reuse.py tests/test_result_committer.py tests/test_evidence_workflow.py tests/test_controller_selection.py`
- Expected: prepared identity is created once, receipt reuse is provenance and
  fingerprint safe, migrated workflows preserve accepted/rejected/pending
  semantics, and no duplicate normal path can publish conflicting state.

**Exit Criteria:**
- Any activated deletion is consumer-proven and does not weaken review or
  persistence ownership; otherwise the task remains explicitly deferred and
  does not block core completion.

### Task 7: Make advanced execution topology explicit and verification proportional

**Purpose:**
- Optional policy/process follow-up: make `DIRECT` and `SEQUENTIAL` cover
  ordinary cases only if measurements show material cost from current topology
  selection. This task is not required for core completion.

**Task Function:**
- Conservative policy simplification and verification-surface alignment.

**Template Profile:**
- Controller-selected: `<unresolved while task is pending>`
- Selection basis: policy compatibility, explicit intent, and regression risk.

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: controller-selection tests and maintained guidance are the proof boundary.

**Specification Coverage:**
- Explicit pattern selection, stable legacy overrides, ordinary direct and
  sequential defaults, and separation of routine merge gates from release-level
  performance/provider evidence.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-performance-optimization`

**Files And Symbols:**
- Inspect first: `src/foresight_os/controller/task_shape.py:TaskShape`,
  `src/foresight_os/controller/policy.py:select_recipe`, and
  `src/foresight_os/controller/proposal.py:build_execution_recipe`.
- Modify only if separately activated: controller policy, approval/recipe
  compatibility tests, and an existing executable CI/release evidence surface.
- Verify: `tests/test_controller_selection.py`, `tests/test_execution_gate.py`,
  and the actual evidence workflow when one is changed.

**Dependencies:**
- Task 5 complete; benchmark evidence shows topology selection is a material
  bottleneck and approval/recipe semantics are understood.

**Authority:**
- Preauthorized local actions: inspect policy cost and, only if separately activated, change declared defaults or maintained verification guidance while preserving serialized compatibility and explicit overrides.
- Stop for: no material measured benefit, removing supported execution patterns, changing approval semantics, or changing CI gates without an executable replacement workflow explicitly in scope.

**Steps:**
- [ ] Step 1: If activated, measure the current topology-selection cost on
  ordinary investigations before changing behavior.
- [ ] Step 2: Select `DIRECT` for one bounded deterministic task with no
  independent participant requirement; select `SEQUENTIAL` for dependencies,
  review, or independent validation.
- [ ] Step 3: Require explicit structural justification for `CONCURRENT`,
  `HANDOFF`, and `GROUP_CHAT`; do not infer advanced topology from weak boolean
  combinations alone.
- [ ] Step 4: Preserve legacy overrides and approval serialization at the
  compatibility boundary, with diagnostics for unsupported or contradictory
  requests.
- [ ] Step 5: Keep fast deterministic correctness and representative integration
  checks in the routine gate; place distributions, soak, clean-environment or
  wheel proof, and provider evidence in the existing release/scheduled surface
  only if that surface exists, is executable, and is explicitly added to scope.

**Verification:**
- [ ] `python -m pytest -q tests/test_controller_selection.py tests/test_execution_gate.py`
- Expected: ordinary briefs choose direct/sequential behavior, advanced patterns
  remain available when explicitly required, and no approval or compatibility
  contract regresses.

**Exit Criteria:**
- If activated, the controller pays for advanced coordination only when
  structurally needed and verification guidance matches actual runnable evidence
  surfaces; otherwise this follow-up remains non-blocking.

### Task 8: Reconcile, verify, and prepare the handoff

**Purpose:**
- Confirm the complete implementation against the exact verified tree and leave
  a truthful plan/evidence handoff without performing Git disposition.

**Task Function:**
- Final verification and scope reconciliation.

**Template Profile:**
- Controller-selected: `<none (lead controller)>`
- Selection basis: final acceptance requires controller authority and fresh evidence.

**Validator Profile:**
- Controller-selected: `<unresolved until activation>`
- Selection basis: select independently if an authorized review lane is assigned.

**Specification Coverage:**
- All implementation outcomes, non-goals, failure statuses, cleanup, docs, and
  verification requirements in this plan.

**Required Skills:**
- `skill-verification-before-completion`, `skill-backend-verification`

**Files And Symbols:**
- Verify: all declared targets, focused tests, full test suite, compile output,
  Markdown links, benchmark receipts, and final diff
- Modify: this plan only for accepted deviations, blockers, evidence paths, and
  task ledger state

**Dependencies:**
- Tasks 1–5 complete and all core task-local proof accepted; Tasks 6–7 are
  included only if separately activated.

**Authority:**
- Preauthorized local actions: run fresh local verification, inspect the final diff, update this plan with immutable evidence paths, and record truthful blockers or deferrals.
- Stop for: any failed required check, stale receipt, unreviewed scope change,
  unexpected/undeclared/unrelated implementation-worktree modification, or
  request for commit/push/merge/cleanup.

**Steps:**
- [x] Step 1: Run the complete verification set below from the exact
  implementation worktree.
- [x] Step 2: Reconcile plan task states, evidence paths, source/docs/tests,
  and any deviations; do not mark a checked item as proof without output.
- [x] Step 3: Run `skill-verification-before-completion`; retain its result as
  the acceptance gate and leave Git disposition separate.

**Verification:**
- [x] `python -m pytest -q`
- [x] `python -m compileall -q src tests evaluation`
- [x] `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- [x] matched base/final optimization comparison from Tasks 4–5
- [x] `git diff --check`
- [x] source-tree digest capture, `git status --short --branch`, and declared-target diff inspection
- Expected: required checks pass from one exact final tree; structural
  correctness, lifecycle, portability, and cleanup evidence are separate from
  unavailable provider/model-quality evidence; no unexpected or unrelated files
  are included.

**Exit Criteria:**
- `skill-verification-before-completion` returns `verified`, all required task
  proof is accepted, deviations and deferred work are recorded, and no branch
  publication or cleanup is claimed.

## Verification

Final artifact-level verification is one fresh pass after all task-local checks:

- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- matched base/final receipts from `evaluation/probes/run_optimization_probe.py` and `compare_optimization_receipts.py`
- `git diff --check`
- source-tree digest, final declared-target diff, and status inspection

The final report must distinguish `VERIFIED`, `FAILED`, `BLOCKED_INPUT`,
`BLOCKED_EXTERNAL`, `NOT_MEASURED`, and `DEFERRED` evidence. A green test suite
does not by itself prove immutability, rollback, warm-path reuse, portability,
or performance improvement.

## Completion Criteria

The plan is ready for completion verification when:

1. Cached analytical material is recursively immutable, rejected computations
   publish nothing reusable, prior valid committed state survives a later
   failed transaction, and read/analysis/authority accounting rolls back
   exactly on failure or cancellation.
2. Direct and capability-dispatched deterministic workbook analysis share one
   run-owned publication boundary; standalone reads enforce the same limits.
3. Explicit mappings are exact-or-fail per consuming table, periods and other
   brief semantics remain independent across shared source bytes, and canonical
   provenance is preserved.
4. Single-output and multi-output synthesis share structural limits,
   conflict/reference validation, and production cancellation behavior during
   substantial active work, including sequential correction/recovery.
5. Warm hits avoid authority reconstruction and whole-object `repr()` sizing;
   retained state remains bounded and dependent views cannot outlive authority.
6. The frozen benchmark exercises shared-context production reuse with repeated
   samples, exact workload identity, counters, distributions, and separated
   local/provider evidence; unsupported dimensions are `FINAL_ONLY` or
   `not_measured` rather than synthesized into a pass.
7. Warm-path optimization is compared against the pre-change baseline without
   weakening correctness, currentness, provenance, authority lifetime, or
   cleanup semantics.
8. Optional deletion or policy tasks, if activated, have consumer evidence,
   compatibility proof, measured benefit, and explicit scope; otherwise they are
   recorded as deferred and do not block core completion.
9. Focused and broad verification passes, documentation links, receipts, and
   final diff reconciliation are complete on the exact reviewed tree.

The plan may be marked `completed` only after
`skill-verification-before-completion` returns `verified`. A checked box is
progress evidence, not completion proof. Git commit, publication, merge, and
worktree cleanup remain separate authorized actions.

## Self-Review

- Verdict coverage: Tasks 2–3 close correctness; Task 4 freezes and executes
  the matched baseline; Task 5 performs measured hot-path optimization; Tasks
  6–7 are optional evidence-backed follow-ups; Task 8 owns final reconciliation.
- Current-base fit: the plan pins remote `main` to
  `14bd69644b7012639c00a65fa94cdd67f52b4c62` pending activation revalidation,
  extends existing `local_toolbelt.py` ownership, and requires source
  reconciliation before adding any new identity type or file.
- Ownership: local toolbelt/context owns bounded workbook reuse;
  `workbook_inputs.py` or the Task 1-confirmed owner owns mappings; existing
  normalized-intent owners are preferred for identity; workflow/committer own
  canonical synthesis; evaluation probes own measurement truth.
- Non-goals: no second cache, persistent parsed workbook store, second analysis
  store, provenance representation, generic recovery framework, new orchestration
  engine, or broad controller rewrite.
- Safety: the current dirty checkout is preserved; unexpected, undeclared, or
  unrelated implementation-worktree changes block; no task authorizes reset,
  discard, external writes, branch publication, or final Git disposition.
- Performance: the frozen harness measures retained-memory accounting separately
  from RSS/peak allocation and timing remains secondary to correctness,
  provenance, rollback, cancellation, and cleanup proof.
