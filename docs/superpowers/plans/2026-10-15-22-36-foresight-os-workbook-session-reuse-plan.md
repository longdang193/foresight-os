---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: proposed
layer: change
name: foresight-os-workbook-session-reuse
targets:
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/runtime/capabilities.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/analysis/independent_validation.py
  - src/foresight_os/analysis/evidence_workflow.py
  - src/foresight_os/analysis/portfolio_resilience.py
  - src/foresight_os/analysis/supplier_resilience.py
  - src/foresight_os/analysis/technology_radar.py
  - src/foresight_os/analysis/ev_capacity_investment.py
  - src/foresight_os/analysis/powerbi_strategic_portfolio.py
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/compare_optimization_receipts.py
  - tests/test_local_toolbelt.py
  - tests/test_optimization_measurement.py
  - tests/test_capabilities.py
  - tests/test_runtime_boundaries.py
  - tests/test_ncc_independent_validation.py
  - tests/test_evidence_workflow.py
  - .github/workflows/ci.yml
  - docs/evidence-and-evaluation.md
  - evaluation/README.md
  - docs/superpowers/plans/2026-10-15-22-36-foresight-os-workbook-session-reuse-plan.md
---

# ForesightOS Workbook Session Reuse

## Goal

Reduce repeated workbook identity, read, parse, and deterministic-analysis work within one investigation by making live reads, pinned reads, currentness checks, and new captures explicit. Preserve source provenance, exact SHA-256 identity, cancellation, failure isolation, current-source checks at acceptance/publication boundaries, independent judgment, revision/invalidation, and run cleanup.

This plan is a follow-on to `docs/superpowers/plans/2026-10-15-foresight-os-investigation-overhead-optimization-plan.md`. That plan established bounded cache cleanup and passed its release comparison, but its XLSX benchmark did not exercise the warm run-scoped workload targeted here. Execution starts from merged `main` at `0ed92a491fd743fddcc57180f7da8728bf10d94e` on a new implementation branch. The supplied verdict's reported measurements are treated as supplied evidence; repository facts and current symbols were checked locally.

## Implementation Outcomes

### Explicit live and pinned workbook semantics

Live reads inspect the mutable path now and establish current content identity. Pinned reads consume an explicitly captured immutable `SourceSnapshot` without rehashing the original path. Currentness checks intentionally re-read/hash the mutable original at required acceptance/publication boundaries. New captures create another immutable version and never silently replace an earlier one.

### Explicit workbook reuse with one cleanup owner

`WorkbookContext` owns multiple per-source `WorkbookSession` objects, run-owned authority indexes, a bounded derived-result cache, aggregate resource accounting, and workbook statistics for one `CapabilityScope`. Each `WorkbookSession` owns one immutable snapshot. Same-snapshot same-selection reuse is bounded and complete-result-only. Cleanup leaves no run-owned snapshot, retained workbook result, parsed resource, measurement, calculation, executor, or temporary file behind.

### Correctness and performance evidence that matches the objective

The optimization probe uses the same non-invasive measurement harness for baseline and release. Receipts identify base commit, source-tree fingerprint, dirty paths, benchmark schema, fixture hashes, workload parameters, dependency versions, environment fingerprint, and measurement mode. Workload-specific gates distinguish capture/currentness hashes, parse/load counts, warm hits, timing noise, and resource bounds. Missing or contradictory evidence fails closed.

### Lower hidden execution cost without weakening trust boundaries

Redundant pre-hashes in workbook analysis modules are removed after snapshot semantics exist. Direct callers can pass `workbook_session=None` for a safe standalone cold read or an explicit session for reuse; analysis modules never create or own the session. The capability runtime receives an explicit typed workbook context. CI cancellation is an independent, narrow follow-up in this plan, not a repository-wide evidence-inventory exercise.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-performance-optimization`, `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: new implementation branch from `main@0ed92a491fd743fddcc57180f7da8728bf10d94e`; preserve all unrelated untracked `work/`, `build/`, `data/`, generated, and user-created files
- Commit policy: `no commits during execution`; Git disposition is handled only after fresh completion verification and separate user authorization
- Preauthorized local actions: inspect and edit declared source, tests, evaluation probes, CI, and documentation; run declared local checks; write redacted receipts under `work/workbook-session-reuse-20261015/`; create the named implementation branch from merged `main`
- User-approval actions: push, merge, rebase, publication, external writes, destructive recovery, cleanup of pre-existing outputs, or edits outside declared targets
- Parallel ownership: none; the runtime, analysis, tests, probes, and CI changes share the session and counter contracts
- Sequential fallback: complete Tasks 1–2 before Task 3; complete Task 3 before Task 4; complete Task 4 before the CI/documentation task and final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/workbook-session-reuse`
- Base commit: `0ed92a491fd743fddcc57180f7da8728bf10d94e`
- Expected workspace: new branch from merged `main`; preserve all pre-existing unrelated untracked artifacts and do not clean them
- Next action: commit the verified implementation, push the branch, open the pull request, and complete the required review cycles before merge
- Blockers: none for local planning or implementation; provider-backed evidence remains optional and must stay explicitly unavailable when not configured

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1: Freeze evidence and reproduce correctness defects | `complete` | current | `none (lead controller)` | none | matched baseline receipt and focused reproductions | `work/workbook-session-reuse-20261015/baseline/receipt.json`; `tests/test_optimization_measurement.py`; `tests/test_local_toolbelt.py` |
| Task 2: Introduce immutable source capture | `complete` | current | `none (lead controller)` | Task 1 | live/pinned semantics, capture, cancellation, and publication tests | `tests/test_local_toolbelt.py`; `src/foresight_os/runtime/local_toolbelt.py` |
| Task 3: Consolidate multi-workbook reuse ownership | `complete` | current | `none (lead controller)` | Task 2 | identity, aggregate budget, authority-lifetime, and Level 1 reuse tests | `tests/test_local_toolbelt.py`; `work/workbook-session-reuse-20261015/release/receipt.json` |
| Task 4: Integrate consumers and synchronized cleanup | `complete` | current | `none (lead controller)` | Task 3 | direct-caller, validation, currentness, concurrency, and cleanup tests | `tests/test_capabilities.py`; `tests/test_runtime_boundaries.py`; `tests/test_evidence_workflow.py`; `tests/test_ncc_independent_validation.py`; `tests/test_result_committer.py` |
| Task 5: Document the contract and add narrow CI cancellation | `complete` | current | `none (lead controller)` | Task 4 | maintained guidance and CI syntax checks | `.github/workflows/ci.yml`; `docs/evidence-and-evaluation.md`; `evaluation/README.md`; Markdown checker output |
| Task 6: Run matched release comparison and final verification | `complete` | current | `none (lead controller)` | Tasks 1–5 | accepted optimization receipt or explicit blocked result plus full checks | `work/workbook-session-reuse-20261015/comparison.json`; full pytest; compileall; Markdown checker; `git diff --check` |

## Task Breakdown

### Task 1: Freeze evidence and reproduce correctness defects

**Purpose:**
- Establish a trustworthy baseline from merged `main` without changing production code, and reproduce the cache-identity, stale-source, cancellation, and non-publication defects that block reuse work.

**Task Function:**
- Freeze the benchmark contract, implementation identity, environment fingerprint, and correctness evidence baseline.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: the task defines the shared measurement contract used by every later task.

**Validator Profile:**
- Controller-selected: `none`

**Specification Coverage:**
- Covers the verdict's requirement for exact measured source-tree identity, non-invasive baseline instrumentation, cold/warm/fan-out/analyst-to-validator workloads, and reproduced correctness defects before implementation.

**Required Skills:**
- `skill-performance-optimization`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/local_toolbelt.py:WorkbookReadCache`, `spreadsheet_read`, `data_analysis`, `calculation`
- Inspect: `src/foresight_os/runtime/capabilities.py:_instrumented_dispatch`, `CapabilityScope`
- Inspect: `evaluation/probes/run_optimization_probe.py:_measure_workbook`, `_run`, `main`
- Inspect: `evaluation/probes/compare_optimization_receipts.py:compare`, `main`
- Modify: `evaluation/probes/run_optimization_probe.py` workload and receipt generation
- Modify: `evaluation/probes/compare_optimization_receipts.py` schema validation and warm-path acceptance
- Verify: `tests/test_optimization_measurement.py`, `tests/test_local_toolbelt.py`, and the generated baseline receipt

**Dependencies:**
- Existing release probe and comparator are the canonical performance evidence entry points; do not create a second benchmark framework.
- Use `tests/fixtures/analyst_multisheet.xlsx` and `evaluation/cases/case-001/workbook.csv` so the baseline remains credential-free and deterministic.

**Authority:**
- Preauthorized local actions: edit the declared probe, comparator, and focused measurement tests; create the implementation branch from merged `main`; run baseline measurements; write only redacted receipts under `work/workbook-session-reuse-20261015/`
- Stop for: correction requiring a changed frozen benchmark criterion, protected contract, external action, or scope expansion

**Steps:**
- [x] Step 1: Make the probe record `base_commit`, `source_tree_fingerprint`, `dirty`, changed paths, `benchmark_schema`, fixture hashes, workload parameters, dependency versions, environment fingerprint, and measurement mode. The comparator must require matching workload/environment/harness identity and different implementation fingerprints, not merely different commits.
- [x] Step 2: Instrument hashing, archive preflight, and workbook loading externally from the probe where practical. Do not add release-only counters to the production baseline; later `WorkbookSessionStats` may supplement, but must not replace, the stable harness.
- [x] Step 3: Run matched cold read, same-selection repeated read/analysis, different and overlapping selections, analyst-to-validator same-view and different-view workloads, plus explicit currentness checks. Record timing, allocations, RSS, temporary bytes, and resource-soak evidence separately.
- [x] Step 4: Reproduce analysis-key collisions, metadata-preserving source mutation, cancellation before warm return/publication, concurrent publication, and scope-close races using focused tests without changing production code. Save `work/workbook-session-reuse-20261015/baseline/receipt.json` from `main@0ed92a491fd743fddcc57180f7da8728bf10d94e`.

**Verification:**
- [x] `python -m pytest -q tests/test_optimization_measurement.py tests/test_local_toolbelt.py`
- Expected: focused measurement and toolbelt tests pass, the baseline receipt contains the workload and identity fields, and reproduced correctness defects are recorded without claiming an optimization.
- [x] `python evaluation/probes/run_optimization_probe.py --mode baseline --fixture tests/fixtures/analyst_multisheet.xlsx --output work/workbook-session-reuse-20261015/baseline/receipt.json`
- Expected: a deterministic, redacted baseline receipt is written from the merged implementation; provider-backed fields remain explicitly unavailable rather than being treated as passing evidence.

**Exit Criteria:**
- The receipt schema, implementation identity, workload parameters, environment fields, and correctness baseline are fixed; later tasks compare only matched receipts.

### Task 2: Introduce immutable source capture

**Purpose:**
- Establish the explicit live-read, pinned-read, currentness-check, and new-capture contract before adding derived-result reuse.

**Task Function:**
- Implement one bounded cancellable byte stream whose SHA describes the exact bytes subsequently parsed.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: the changes affect provenance and cache safety and must be kept in the canonical toolbelt owner.

**Validator Profile:**
- Controller-selected: `none`

**Specification Coverage:**
- Covers immutable source identity, multiple source versions, live versus pinned semantics, cancellation-safe capture/publication, and no silent refresh.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/local_toolbelt.py:spreadsheet_read`, `_sha256_file`, `_check_cancel`, `WorkbookReadResult`
- Modify: `src/foresight_os/runtime/local_toolbelt.py` with `SourceSnapshot`, source handles, live/pinned read paths, and cancellation-safe publication
- Modify: `src/foresight_os/analysis/independent_validation.py:read_validation_source`, `run_independent_validation` for explicit pinned-source inputs
- Verify: `tests/test_local_toolbelt.py`, `tests/test_ncc_independent_validation.py`, and stale-source workflow tests

**Dependencies:**
- Task 1 freezes the receipt contract and reproduces the current correctness defects.
- Existing `workbook_sha256` remains authoritative for the exact bytes read; this task adds an immutable handle rather than a second identity registry.

**Authority:**
- Preauthorized local actions: add the declared capture and pinned-read owner plus focused tests; run deterministic boundary checks; preserve current invalidation and provenance contracts
- Stop for: metadata/mtime-only identity, persistent source registry, silent refresh, changed trust status, or correction requiring scope, protected-contract, external, or frozen-criterion changes

**Steps:**
- [x] Step 1: Add `SourceSnapshot` with `snapshot_id`, original source locator, SHA-256, byte size, capture version, and immutable captured bytes/file. Capture through one bounded cancellable stream and make the captured SHA the identity of all subsequent parsing.
- [x] Step 2: Define live reads against mutable paths, pinned reads against a source handle, explicit currentness checks against the original path, and new capture as a distinct operation. Repeated `spreadsheet_read(path)` remains a live read; it must not silently reuse a pinned snapshot.
- [x] Step 3: Check cancellation during capture/hash/preflight/parse, before returning a pinned cached result, and immediately before publishing. Failed or cancelled work must publish no read, analysis, authority, stage, or accepted result.
- [x] Step 4: Add direct-caller support for `workbook_session=None` as a safe standalone cold read and an explicit pinned session for reuse. The analysis modules do not create or own sessions; their provenance digest comes from the actual read/captured result.

**Verification:**
- [x] `python -m pytest -q tests/test_local_toolbelt.py tests/test_evidence_workflow.py tests/test_portfolio_resilience.py tests/test_supplier_and_ev_resilience.py tests/test_technology_powerbi_validator.py`
- Expected: live and pinned semantics are distinguishable, captured bytes and SHA agree, changed/missing/unreadable originals produce truthful stale/blocked/invalidation outcomes, and cancellation/failure publishes nothing.
- [x] `python -m compileall -q src tests evaluation`
- Expected: all modified Python files compile without warnings or generated-file edits.

**Exit Criteria:**
- Immutable source capture and pinned-read semantics are implemented and tested without introducing derived-result caching or silent currentness changes.

### Task 3: Consolidate multi-workbook reuse ownership

**Purpose:**
- Add one run-owned `WorkbookContext` that can contain several per-source sessions while keeping source versions immutable and derived results disposable.

**Task Function:**
- Consolidate identity, derived-result reuse, authority retention, aggregate budgets, and workbook statistics without adding a scheduler or persistence layer.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: this is a cross-cutting runtime contract but remains owned by the existing local toolbelt module.

**Validator Profile:**
- Controller-selected: `none`

**Specification Coverage:**
- Covers multiple workbooks per run, O(1)-ish table identity, Level 1 same-snapshot same-selection reuse, separate authority lifetime, aggregate retained-resource budgets, provenance preservation, and cleanup.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/local_toolbelt.py` with `WorkbookSession`, `WorkbookContext`, derived cache, authority indexes, and `WorkbookSessionStats`
- Modify: `src/foresight_os/runtime/local_toolbelt.py:TypedTable`, `WorkbookReadCache.analysis_key`, `spreadsheet_read`, `data_analysis`, and `calculation`
- Verify: `tests/test_local_toolbelt.py`, `tests/test_optimization_measurement.py`, and cross-workbook calculation tests

**Dependencies:**
- Task 2 provides immutable source handles and pinned reads.
- Reuse existing `ToolbeltLimits`, `SheetSelection`, `WorkbookReadResult`, `AnalysisResult`, `TypedMeasurement`, and `CalculationRecord`; do not introduce a second schema or provenance graph.

**Authority:**
- Preauthorized local actions: add `WorkbookContext`, per-source sessions, the derived cache, authority indexes, stats, and focused lifecycle/identity tests
- Stop for: persistent/distributed storage, a second identity registry, a mutable long-lived `openpyxl` workbook, new cache lifecycle statuses, or a budget that omits snapshots, retained values, temporary bytes, or in-flight parse memory

**Steps:**
- [x] Step 1: Make each `TypedTable` carry one immutable material fingerprint derived at construction from source snapshot identity, sheet/range, hidden-row semantics, headers, normalized material rows, and relevant provenance. Multi-table analysis keys include every participating table/source fingerprint; lookups must not rewalk or reserialize full tables.
- [x] Step 2: Implement `WorkbookContext` with multiple `WorkbookSession` instances, a bounded derived cache, run-owned authority indexes, aggregate retained-resource accounting, peak in-flight parse observation, and `WorkbookSessionStats`. Separate eviction: derived results may evict; authority records remain valid for their required lifetime; snapshots stay pinned while dependent state is active.
- [x] Step 3: Define the aggregate budget over captured snapshot bytes, normalized retained values, read views, analysis results, authority records, and temporary storage. Use a conservative retained-size estimator validated against RSS/allocation evidence; do not use `len(repr(result))` or entry/cell count alone.
- [x] Step 4: Add a session-level lock or equivalent small synchronization primitive. Publish cache/authority entries atomically only after successful computation while the context is open and the operation remains admissible. Test simultaneous identical reads, cancellation during publication, concurrent read plus eviction pressure, and authority survival after derived-cache eviction.

**Verification:**
- [x] `python -m pytest -q tests/test_local_toolbelt.py`
- Expected: context tests prove multiple source versions per run, safe Level 1 reuse, O(1)-ish identity lookup, aggregate budgets, synchronized publication, authority lifetime, and no retained state after close.
- [x] `python -m compileall -q src tests evaluation`
- Expected: the new runtime classes and all consumers compile cleanly.

**Exit Criteria:**
- The toolbelt has one explicit run-owned multi-workbook context with per-source immutable sessions, Level 1 reuse, separate authority lifetime, synchronized publication, and no process-wide authoritative workbook state.

### Task 4: Integrate explicit session ownership, validation sharing, and currentness boundaries

**Purpose:**
- Make the multi-workbook context lifecycle real for production execution, direct callers, and independent validation while preserving current-source checks at the existing trust boundary.

**Task Function:**
- Wire the context through capability ownership and cleanup without making generic workflow orchestration responsible for workbook caching unless a failing lifecycle test proves the boundary insufficient.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: runtime integration spans capability dispatch, workflow settlement, validation, cancellation, and cleanup.

**Validator Profile:**
- Controller-selected: `none`

**Specification Coverage:**
- Covers explicit context ownership, direct-caller migration, shared deterministic extraction but independent interpretation, synchronized cancellation/publication, cleanup ordering, same-run currentness, and explicit resumed-acceptance behavior.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/capabilities.py:CapabilityScope.close`, `prepare_capability_context`, `_instrumented_dispatch`
- Modify: `src/foresight_os/runtime/workflow.py:run_recipe_async`, `dispatch_stage`, and the existing stage settlement/committer boundary
- Modify: `src/foresight_os/analysis/independent_validation.py:read_validation_source`, `run_independent_validation`
- Modify: `src/foresight_os/analysis/evidence_workflow.py:run_xlsx_finding_workflow`, `accept_pending_evidence`
- Verify: `tests/test_capabilities.py`, `tests/test_runtime_boundaries.py`, `tests/test_ncc_independent_validation.py`, `tests/test_evidence_workflow.py`, and `tests/test_result_committer.py`

**Dependencies:**
- Task 3 provides the only `SourceSnapshot`/`WorkbookSession`/`WorkbookContext` contract.
- `CapabilityScope` remains the cleanup boundary; `AnalysisState`, `AnalysisStore`, existing review records, and invalidation remain authoritative for durable analytical state.

**Authority:**
- Preauthorized local actions: wire one `WorkbookContext` into `CapabilityScope`, migrate direct and instrumented callers, update validation and evidence workflows, and add direct boundary tests
- Stop for: changing `AnalysisState` ownership, weakening human acceptance, replacing source currentness with metadata checks, publishing on cancellation/failure, changing external provider contracts, or changing resumed-acceptance policy

**Steps:**
- [x] Step 1: Add an explicit `WorkbookContext` field to `CapabilityScope`. On shutdown, stop admission of new work, signal cancellation, wait for running workers/futures to settle, shut down the workbook/tool executor, close contexts and remove snapshots, then close remaining owned resources. No worker may publish into a closed context.
- [x] Step 2: Replace lazy `_cache` construction in `_instrumented_dispatch` with typed context/session delivery to local deterministic functions. Preserve public JSON signatures exposed by `bind_local_toolbelt()` and strip only the internal context/session parameters at the provider boundary.
- [x] Step 3: Update analysis modules to accept `workbook_session=None` for safe standalone cold reads or an explicit pinned session for reuse. Update `run_independent_validation()` to consume the same immutable extraction/arithmetic while keeping review interpretation and required-check selection independent.
- [x] Step 4: Inventory acceptance boundaries. Same-run acceptance may compare the mutable original against the captured SHA. Resumed acceptance accepts durable captured evidence as that version unless the caller explicitly supplies `current_source`; missing, deleted, unreadable, or changed originals produce explicit stale/blocked/invalidation outcomes.
- [x] Step 5: Add direct concurrency tests for two identical reads, cancellation during publication, scope close during an active operation, concurrent read plus eviction pressure, and no publication after close. Add currentness tests for same-run and resumed acceptance.

**Verification:**
- [x] `python -m pytest -q tests/test_capabilities.py tests/test_runtime_boundaries.py tests/test_ncc_independent_validation.py tests/test_evidence_workflow.py tests/test_result_committer.py`
- Expected: all direct boundary tests pass; shutdown ordering settles workers before deleting snapshots; cancelled or failed runs publish no partial trusted result; same-run and resumed currentness outcomes remain explicit.
- [x] `python -m pytest -q tests/test_local_toolbelt.py tests/test_capabilities.py tests/test_runtime_boundaries.py`
- Expected: direct Python callers and production instrumented callers exercise the same context-owned behavior.

**Exit Criteria:**
- Production execution, direct validation, resumed acceptance, and cleanup all use the same explicit multi-workbook context without changing durable analytical ownership or trust-boundary semantics.

### Task 5: Document the contract and add narrow CI cancellation

**Purpose:**
- Document the explicit workbook contract and add only the independent CI concurrency safeguard.

**Task Function:**
- Maintain the delivery boundary after the runtime contract is proven.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: CI and documentation changes are downstream of the verified runtime/receipt contract.

**Validator Profile:**
- Controller-selected: `none`

**Specification Coverage:**
- Covers superseded-run cancellation and one current explanation of live reads, pinned reads, currentness, multi-workbook ownership, cleanup, and Level 1 reuse.

**Required Skills:**
- `skill-code-standards`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `.github/workflows/ci.yml` jobs and `.github/workflows/evidence.yml` release measurement step
- Modify: `.github/workflows/ci.yml` workflow-level concurrency configuration
- Modify: `docs/evidence-and-evaluation.md` performance evidence section and `evaluation/README.md` optimization probe guidance
- Verify: `.github/workflows/ci.yml`, `.github/workflows/evidence.yml`, and Markdown-link coverage

**Dependencies:**
- Task 4 must establish the final counter/receipt names before documentation is edited.
- Keep wheel smoke tests, provider/MCP boundary checks, deterministic tests, and the matched optimization receipt because each proves a distinct boundary unless a fresh inventory proves otherwise.

**Authority:**
- Preauthorized local actions: add CI concurrency cancellation and update maintained performance/session guidance
- Stop for: deleting or reclassifying CI evidence, changing provider-evidence policy, editing generated agent surfaces directly, or adding a second current specification

**Steps:**
- [x] Step 1: Add workflow-level concurrency to `.github/workflows/ci.yml` using the PR number when available and the branch ref otherwise, with `cancel-in-progress: true`; do not change job permissions or provider-evidence boundaries.
- [x] Step 2: Document live reads, pinned reads, explicit currentness checks, new captures, multiple source versions per run, separate authority/derived lifetimes, cleanup ordering, the Level 1 reuse boundary, and the warm-path acceptance rule. Do not document Level 2 normalized parsed-workbook reuse as implemented.
- [x] Step 3: Run the repository Markdown-link checker over the maintained documentation changed by this task.

**Verification:**
- [x] `python scripts/check_markdown_links.py README.md AGENTS.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- Expected: all checked links resolve and no generated-surface instruction is edited directly.
- [x] Inspect `.github/workflows/ci.yml` and `.github/workflows/evidence.yml` for valid YAML structure and retained distinct-evidence jobs.
- Expected: superseded runs cancel within the same concurrency group; retained checks and protected provider boundaries remain unchanged. Duplicate push/PR trigger design remains out of scope.

**Exit Criteria:**
- CI and documentation describe the explicit context contract without creating a parallel policy, cache, evidence registry, or repository-wide CI cleanup.

### Task 6: Run the matched release comparison and final verification

**Purpose:**
- Prove the implementation against the stated optimization objective and repository-wide correctness contract.

**Task Function:**
- Reconcile performance, correctness, cleanup, and documentation evidence into one truthful completion decision.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final verification must remain under one controller and use fresh evidence.

**Validator Profile:**
- Controller-selected: `none`

**Specification Coverage:**
- Covers reproducible warm improvement, cold non-regression, no stale reuse, exact provenance SHA, no partial publication, bounded resources, cleanup, and full repository verification.

**Required Skills:**
- `skill-verification-before-completion`, `skill-performance-optimization`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: all declared targets and `docs/superpowers/plans/2026-10-15-22-36-foresight-os-workbook-session-reuse-plan.md`
- Verify: `evaluation/probes/run_optimization_probe.py`, `evaluation/probes/compare_optimization_receipts.py`, focused tests, full suite, compileall, Markdown links, and `git diff --check`

**Dependencies:**
- Tasks 1–5 complete with no unresolved required task-local proof.
- Use new output paths under `work/workbook-session-reuse-20261015/`; do not overwrite historical receipts or delete unrelated untracked artifacts.

**Authority:**
- Preauthorized local actions: run fresh local verification, generate redacted receipts, inspect the final diff, and record truthful pass/failed/blocked outcomes in the plan
- Investigate and correct failed checks within the approved scope. Stop or escalate only for a scope change, a protected-contract or owner change, an external action/provider dependency, or a request to change a frozen benchmark criterion.

**Steps:**
- [x] Step 1: After all implementation and documentation edits, run the release probe against the same fixture, workload schema, dependency set, environment contract, and harness identity used for Task 1. The release receipt must record the final `source_tree_fingerprint`, base commit, dirty paths, and implementation fingerprint; do not change declared source files after this receipt is produced.
- [x] Step 2: Compare baseline and release receipts with the updated comparator. It must require matching fixture, workload, dependency, environment, benchmark-schema, and harness identity plus different implementation fingerprints. Apply workload-specific gates: cold runs perform one capture/hash with bounded overhead; warm identical selections add no capture, currentness hash, or parse/load; different selections on the same snapshot add no source hash while Level 1 may still parse; analyst-to-validator same-view work shares deterministic extraction; explicit currentness checks are expected to hash the mutable source. Distinguish `capture_hash_count` from `currentness_hash_count` and `xlsx_parse_count` from `openpyxl_load_count`. Accept only when cold performance stays within the agreed non-regression budget, warm latency exceeds the measured baseline noise floor by a reproducible margin, correctness checks pass, and aggregate resource soak remains bounded; use absolute count gates when the baseline count is zero rather than ratios.
- [x] Step 3: Run focused backend boundary tests, then the complete repository suite and compile checks. Preserve `BLOCKED_EXTERNAL` or `not_measured` for provider/model/human-quality dimensions that local execution cannot prove.
- [x] Step 4: Inspect `git diff --check`, the tracked diff, and `git status --short --branch`; confirm the release receipt's final `source_tree_fingerprint` matches the tree verified after all edits, unrelated untracked artifacts are untouched, and only declared files changed.
- [x] Step 5: If the selection-fan-out workload still shows material repeated XLSX parse cost after Level 1 reuse, record the measured result as a follow-up gate. Do not implement a normalized parsed-workbook representation in this plan; draft a separate plan with its own memory budget and owner.

**Verification:**
- [x] Apply the single authoritative command set in the `Verification` section below after Steps 1–5.
- Expected: the release receipt and comparison are generated from the final verified source-tree fingerprint, and the recorded outcome is accepted, failed, or blocked without weakening the trust model.

**Exit Criteria:**
- Fresh verification either returns a truthful accepted optimization result with all required correctness and cleanup proof, or records the exact failed/blocked gate for follow-up without weakening the trust model.

## Verification

Final artifact-level verification is owned by `skill-verification-before-completion` after every task-local proof passes. This is the single authoritative command set; task sections must not duplicate it:

- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `python scripts/check_markdown_links.py README.md AGENTS.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- `python evaluation/probes/run_optimization_probe.py --mode release --fixture tests/fixtures/analyst_multisheet.xlsx --output work/workbook-session-reuse-20261015/release/receipt.json`
- `python evaluation/probes/compare_optimization_receipts.py --baseline work/workbook-session-reuse-20261015/baseline/receipt.json --release work/workbook-session-reuse-20261015/release/receipt.json --output work/workbook-session-reuse-20261015/comparison.json`
- `git diff --check`
- `git status --short --branch`

The final review must confirm that the release receipt's `source_tree_fingerprint` is the exact fingerprint of the final tree under review and that the comparator matched workload, environment, dependency, fixture, schema, and harness identities while comparing different implementation fingerprints. It must distinguish structural proof from model quality, provider availability, and human acceptance. It must not claim that Level 2 normalized parsed-workbook reuse, vertical-slice retirement, risk-driven review policy, or provider-backed performance has been implemented unless a separately approved plan and fresh evidence exist.

## Completion Criteria

The plan is ready for completion verification when:

1. One run-owned `WorkbookContext` can retain multiple immutable source versions, each represented by a per-source `WorkbookSession` whose SHA and bytes are the exact inputs used by downstream reads, provenance, analysis, and validation.
2. Live reads, pinned reads, explicit currentness checks, and new captures are distinct operations; resumed acceptance uses durable captured evidence unless `current_source` is supplied, and missing, deleted, unreadable, or changed originals produce explicit stale, blocked, or invalidation outcomes rather than silent refresh.
3. Same-snapshot same-selection reuse is bounded, complete-result-only, and keyed by full material input identity; no stale source can be reused after a new capture, and authority records cannot disappear because a disposable derived cache evicted an entry.
4. Cancellation and failure publish no trusted cache, authority record, partial stage result, or accepted analytical result; synchronized admission, publication, eviction, and close prevent writes into a closed context.
5. Independent validation shares immutable deterministic extraction but retains independent interpretation, review decisions, and required-check selection.
6. `CapabilityScope.close()` follows the required order: stop admission, signal cancellation, wait for workers/futures, shut down workbook/tool executors, close contexts and remove snapshots, then close remaining resources, retained measurement/calculation state, and temporary files.
7. Aggregate resource accounting covers snapshots, normalized retained values, read views, analysis results, authority records, temporary bytes, and peak in-flight parse memory; memory, threads, handles, and temporary files remain bounded.
8. The matched benchmark distinguishes `capture_hash_count` from `currentness_hash_count` and `xlsx_parse_count` from `openpyxl_load_count`; cold, warm-identical, same-snapshot different-selection, analyst-to-validator, and explicit-currentness gates are evaluated against the measured baseline noise floor and zero-safe absolute counts.
9. CI cancellation and maintained documentation preserve unique packaging, deterministic, provider/MCP, integration, and release-evidence boundaries without a repository-wide evidence-inventory rewrite.
10. `skill-verification-before-completion` returns `verified`, the final `source_tree_fingerprint` matches the release receipt, and only then may the plan status be changed from `proposed` and any separately authorized Git disposition be pursued.

## Self-Review

- Verdict coverage: explicit live/pinned/currentness semantics, multi-workbook ownership, receipt identity, synchronized cleanup, and workload-specific gates map to Tasks 1–4; narrow CI/documentation changes map to Task 5; Level 2 normalized parsed-workbook reuse remains explicitly deferred rather than hidden inside an unresolved task.
- Template scan: every task uses concrete paths, named owners, executable steps, and resolved dependencies.
- Cross-task consistency: `SourceSnapshot`, `WorkbookSession`, `WorkbookContext`, `CapabilityScope`, live/pinned/currentness semantics, `run_independent_validation`, `capture_hash_count`, `currentness_hash_count`, `xlsx_parse_count`, `openpyxl_load_count`, receipt fingerprints, receipt paths, and the single authoritative verification command set are used consistently.
- Ownership: `local_toolbelt.py` remains the canonical source-capture/session owner; `CapabilityScope` remains the cleanup owner; `AnalysisState` and `AnalysisStore` remain durable analytical owners; evaluation probes remain evidence consumers.
- Task sizing: correctness, session construction, runtime integration, CI/documentation, and final verification are separated by dependency and proof; no parallel write lane is declared because the contracts overlap.
