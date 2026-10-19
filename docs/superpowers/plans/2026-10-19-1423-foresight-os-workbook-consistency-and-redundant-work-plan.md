---
layer: change
artifact_type: plan
status: verified
template_id: implementation-plan
contract_version: "1"
name: foresight-os-workbook-consistency-and-redundant-work
targets:
  - src/foresight_os/runtime/execution_gate.py
  - src/foresight_os/runtime/executors.py
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/analysis/workbook_engine.py
  - src/foresight_os/analysis/workbook_inputs.py
  - src/foresight_os/analysis/evidence_workflow.py
  - src/foresight_os/analysis/workbook_runner.py
  - src/foresight_os/analysis/review_workflow.py
  - src/foresight_os/analysis/workbook_registry.py
  - src/foresight_os/persistence/analysis_store.py
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/compare_optimization_receipts.py
  - tests/
  - docs/architecture.md
  - README.md
---

# Workbook Consistency And Redundant Work

## Review Of The Recommendation

The pasted review is directionally correct and implementation-ready after
scoping. Current `origin/main` is
`e6755412fa5e3645332812d03b9df4a3a564f653`, the merge commit for PR #38.
Repository inspection confirms the following root causes:

### [P0] Approved execution can bypass workbook default resolution

`ExecutionGate.execute()` supplies both an `analysis_contracts` map and an
`analysis_contract_resolver`. `DeterministicLocalExecutor` checks the map
first, so a declared partial contract can reach `WorkbookAnalysisEngine.run()`
before `resolve_workbook_contract()` applies domain defaults. Direct and
approved paths can therefore select different tables and fingerprints.

**Plan correction:** make one stage/domain resolver authoritative before engine
dispatch, resolve defaults once, and use the effective contract for layout,
materialization, analyzer input, receipt identity, and fingerprints. Keep
legacy map parsing only at the external compatibility boundary.

### [P0] Admission can combine objects from different persisted versions

`ExecutionGate.admit()` captures the workbook outside the lock, while
`ExecutionGate.execute()` later reloads the brief and constructs another
committer from a fresh store read. The post-capture check validates only the
approval projection fingerprint. A brief or recipe update that does not change
that approval field can combine an old admitted recipe with newly loaded brief
data.

**Plan correction:** carry the admitted brief, normalized intent, recipe,
approval projection, fingerprints, and workbook snapshot together; revalidate
the persisted brief/recipe/approval projection after capture; execute only the
admitted bundle.

### [P1] Materialization and currentness still duplicate immutable work

`materialize_scope=False` replaces scopes with empty values but still rebuilds
every `TypedTable` and re-hashes all rows. Snapshot-authoritative execution
also calls path currentness after capture, adding a second source hash.

**Plan correction:** reuse original immutable tables when no rows are rejected,
and remove the live-path currentness check from snapshot-authoritative analysis.
Retain `WorkbookContext.currentness()` as an explicit API for callers that
need live-path comparison.

### [P1] XLSX preflight is broader than extraction selection

`_preflight_xlsx_archive()` treats an empty `sheet_names` collection as all
sheets selected, even when a selection is expressed only by ranges or tables.
Allocation counters can therefore reject or scan unrelated worksheets.

**Plan correction:** share one selection predicate between preflight and
extraction. Keep archive-wide byte and structural ZIP/XML limits, but scope row,
cell, merged-cell, and selected formula accounting to selected material.

### [P1] Immediate review settlement performs an unnecessary pending rewrite

The synchronous workbook runner saves pending state, then
`review_and_accept_pending_analysis()` attaches the review through another
pending write before `accept_pending_analysis()` commits. The persisted pending
token and revision checks are valuable, but the reviewed-pending intermediate
is not needed when the decision is immediately ACCEPT or REJECT.

**Plan correction:** attach the review in memory and commit directly against the
persisted pending token for terminal decisions; persist reviewed pending only
when the state remains PENDING.

### [P1/P2] Conditional cached-value loading is a separate candidate

The reader always loads both `data_only=False` and `data_only=True` workbooks.
Removing the cached view globally would break formula-bearing workbooks, but a
formula-free selected-material case can skip the second load.

**Plan correction:** implement selection-aware formula detection first, then
benchmark the conditional second-load candidate independently. Do not accept it
without matched correctness, resource, cold, warm, reuse, and history gates.

### Deferred findings

The per-domain registry factory simplification and dependency isolation are
valid P2 maintenance opportunities, but they are not required to establish
the next correctness or measured cold-path improvement. They are explicit
deferrals here and must not be mixed into the workbook execution change.

## Goal

Make approved workbook execution use one immutable admitted bundle and one
fully resolved stage/domain contract, then remove only redundant transformations,
hashes, scans, writes, and workbook loads that survive correctness and matched
performance evidence. Preserve `AnalysisStore`, `WorkbookContext`,
`WorkbookAnalysisEngine`, `StageReceipt`, review-token checks, provenance, and
the provider-free local execution boundary as the canonical owners.

## Implementation Outcomes

### One admitted execution identity

Approved execution carries the admitted brief, normalized intent, recipe,
approval projection, fingerprints, source path, and immutable workbook snapshot.
After capture, persisted brief/recipe/approval fingerprints are revalidated
before dispatch. Execution never reloads a different brief or recipe for the
same admission.

### One effective stage/domain contract

Each deterministic workbook stage resolves its exact stage contract, then the
unambiguous global fallback, applies workbook defaults once, and uses that
effective contract for layout, materialization, analyzer input, receipt
identity, and parity checks. Missing or ambiguous bindings remain fail-closed.

### Measured redundant-work removal

No-op materialization reuses immutable source tables, snapshot-authoritative
flows avoid a second path hash, and terminal review decisions avoid an
unnecessary reviewed-pending write while preserving revision and token checks.
XLSX preflight counts only selected material for selection-scoped limits.

### Conditional XLSX loading is evidence-gated

Formula-free selected material may use one openpyxl view; formula-bearing
material continues to use both source and cached-value views. The candidate is
accepted only if separate correctness, resource, cold, warm, source-change,
scope-change, reuse, and history gates pass.

### Cross-brief release evidence

One representative workbook fixture covers changed period/entity/scenario,
stage-specific same-domain overrides, and partial contracts relying on domain
defaults. The receipt records effective contract fingerprints, selected data,
canonical output, and correct reuse/non-reuse decisions for each brief.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-test-driven-development`, `skill-backend-verification`, `skill-systematic-debugging`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: new dedicated worktree from `origin/main` at `e6755412fa5e3645332812d03b9df4a3a564f653`; do not modify the dirty primary checkout
- Commit policy: verified per-task checkpoint commits preauthorized; no commit before task-local proof passes
- Preauthorized local actions: inspect source and tests, create the declared worktree, edit named owners, run declared checks and local probes, and retain task-owned evidence under a declared work directory
- User-approval actions: push, merge, publication, external writes, destructive recovery, discard, branch deletion, worktree removal, and cleanup
- Parallel ownership: none; shared runtime, persistence, and reader owners serialize
- Sequential fallback: Tasks 1 through 7 in order; do not begin the conditional second-load candidate before selection-aware preflight proof passes

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/foresight-os-workbook-consistency-and-redundant-work`
- Base commit: `e6755412fa5e3645332812d03b9df4a3a564f653`
- Expected workspace: clean dedicated worktree; dirty primary-checkout changes preserved and excluded
- Next action: hand off the verified branch state to branch-finishing workflow
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `completed` | dedicated worktree | `lead controller` | none | baseline and current defect reproduction | `work/consistency-baseline-output.json`, focused baseline output |
| 2 | `completed` | dedicated worktree | `lead controller` | 1 | admitted bundle and effective contract parity | `tests/test_execution_gate.py`, `tests/test_analysis_input_contract.py` |
| 3 | `completed` | dedicated worktree | `lead controller` | 2 | zero-copy materialization and snapshot hash proof | `tests/test_workbook_engine.py`, `tests/test_evidence_workflow.py`, release receipt |
| 4 | `completed` | dedicated worktree | `lead controller` | 2 | selection-aware preflight limits and scan behavior | `tests/test_local_toolbelt.py`, release receipt |
| 5 | `completed` | dedicated worktree | `lead controller` | 2 | terminal review settlement and revision safety | `tests/test_review_workflow.py`, `tests/test_workbook_runner.py` |
| 6 | `completed` | dedicated worktree | `lead controller` | 3, 4 | conditional cached-load candidate and matched gates | release receipt; formula-free and formula-bearing focused tests |
| 7 | `completed` | dedicated worktree | `lead controller` | 2-6 | cross-brief release evidence, docs, and final verification | full pytest, compileall, Markdown links, diff check, release receipt |

## Task Breakdown

### Task 1: Establish the post-PR baseline and reproduce remaining issues

**Purpose:** Freeze current behavior and measurement inputs before changing
shared execution, persistence, or XLSX reader owners.

**Task Function:** baseline measurement and defect reproduction.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: source and benchmark baseline are tightly coupled to the lead's coordination state.

**Validator Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: the lead controller owns baseline reproduction.

**Specification Coverage:** current main at the pinned merge commit, preserved
local contracts, source identity, and measured workload separation.

**Required Skills:**
- `skill-executing-plans`
- `skill-backend-verification`
- `skill-performance-optimization`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/execution_gate.py:ExecutionGate.admit`, `ExecutionGate.execute`
- Inspect: `src/foresight_os/runtime/executors.py:DeterministicLocalExecutor.execute`
- Inspect: `src/foresight_os/analysis/workbook_engine.py:WorkbookAnalysisEngine.run`
- Inspect: `src/foresight_os/runtime/local_toolbelt.py:_preflight_xlsx_archive`, `spreadsheet_read`
- Verify: `tests/test_execution_gate.py`, `tests/test_workbook_path_parity.py`, `tests/test_workbook_runner.py`, `evaluation/probes/run_optimization_probe.py`

**Dependencies:** pinned `origin/main` base and the existing representative XLSX fixture.

**Authority:**
- Preauthorized local actions: create the dedicated worktree, inspect source and tests, run baseline commands and probes, and write declared evidence files.
- Stop for: base drift, missing fixture, primary-checkout mutation, or a defect requiring an unapproved behavioral choice.

**Steps:**
- [x] Step 1: Assert `origin/main` equals the pinned base and create the dedicated branch/worktree without copying primary-checkout files.
- [x] Step 2: Run the focused workbook, execution-gate, persistence, review, and local-toolbelt suites plus compile checks.
- [x] Step 3: Add or run reproductions for a partial approved contract, a brief change during capture, a no-op materialization path, range/table-only preflight, immediate settlement, and snapshot currentness hashing.
- [x] Step 4: Record baseline reader-load, currentness-hash, materialization, pending-write, persistence, and selected-material metrics with fixture and environment identifiers.

**Verification:**
- [x] `python -m pytest -q` on the pinned base or equivalent focused baseline suite
- [x] `python -m compileall -q src tests evaluation`
- Expected: existing behavior is captured and each planned defect is reproducible or explicitly marked `not_measured` with a reason.

**Exit Criteria:** baseline receipts and reproductions are retained, no behavior change has been made, and Task 2 has exact failing assertions to fix.

### Task 2: Make admission and stage/domain contract resolution single-source

**Purpose:** Eliminate mixed-version admission and ensure approved execution
uses the same effective workbook contract as direct execution.

**Task Function:** runtime identity and contract-boundary implementation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared admission and executor symbols have high correctness and lifecycle risk.

**Validator Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: focused boundary tests remain with the lead controller.

**Specification Coverage:** source-bound execution identity, exact stage/domain
precedence, default resolution before layout, and fail-closed ambiguity.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-systematic-debugging`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/execution_gate.py:ApprovedExecution`, `ExecutionGate.admit`, `ExecutionGate.execute`
- Modify: `src/foresight_os/runtime/executors.py:DeterministicLocalExecutor.execute`
- Modify: `src/foresight_os/analysis/workbook_engine.py:WorkbookAnalysisEngine.run`
- Modify: `src/foresight_os/analysis/workbook_inputs.py:resolve_workbook_contract`
- Verify: `tests/test_execution_gate.py`, `tests/test_analysis_input_contract.py`, `tests/test_workbook_path_parity.py`, `tests/test_selective_reuse.py`

**Dependencies:** Task 1 reproductions; preserve the existing resolver and
`resolve_workbook_contract()` owners rather than adding a second registry or
executor layer.

**Authority:**
- Preauthorized local actions: edit the named admission, resolver, executor, and engine owners and add focused regression tests.
- Stop for: unresolved precedence semantics, approval schema changes, new persistence identity formats, or any required external provider.

**Steps:**
- [x] Step 1: Extend `ApprovedExecution` with the admitted brief, normalized intent, approval projection/fingerprint, recipe/persisted recipe fingerprint, source identity, and snapshot needed by execution.
- [x] Step 2: After snapshot capture, reacquire the store lock and compare the captured brief, recipe, approval projection, and source-identity fingerprints with the persisted records; reject any mismatch before dispatch, then execute only the captured bundle without reloading persisted objects.
- [x] Step 3: Resolve each deterministic stage through one stage/domain resolver, apply workbook defaults once, and pass the effective contract and effective fingerprints to engine, analyzer, receipt, and commit contexts.
- [x] Step 4: Remove executor preference for a competing contract map; retain only a compatibility normalization boundary before executor construction where serialized callers require it.
- [x] Step 5: Use the admitted brief and normalized intent to construct the committer and run context without reloading a different brief after admission.
- [x] Step 6: Add tests for partial contracts, stage-over-global precedence, ambiguous/missing bindings, brief mutation during capture, recipe mutation during capture, and direct/approved parity.

**Verification:**
- [x] A partial approved contract selects the same default tables and effective contract fingerprint as direct execution.
- [x] Mutating brief or recipe state after capture fails closed and never executes a mixed bundle.
- [x] An unchanged admitted bundle executes without additional brief/recipe reloads and preserves receipt reuse semantics.

**Exit Criteria:** approved and direct execution share one effective contract and one admitted identity bundle, with fail-closed mutation and parity tests passing.

### Task 3: Remove no-op materialization and snapshot currentness re-hashing

**Purpose:** Remove measurable duplicate row allocation, table hashing, and
source hashing without weakening immutable snapshot semantics.

**Task Function:** material-view and snapshot-lifecycle optimization.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: the change spans the canonical workbook context and material owner.

**Validator Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: focused resource and cancellation tests are sufficient.

**Specification Coverage:** immutable source snapshot authority, provenance
preservation, cancellation, and material-only analyzer input.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-performance-optimization`

**Files And Symbols:**
- Modify: `src/foresight_os/analysis/workbook_inputs.py:build_material_view`
- Modify: `src/foresight_os/analysis/workbook_engine.py:WorkbookAnalysisEngine.run`
- Modify: `src/foresight_os/analysis/evidence_workflow.py:_run_xlsx_finding_workflow`
- Modify: `src/foresight_os/runtime/local_toolbelt.py:WorkbookContext.currentness`, snapshot-authoritative read path
- Verify: `tests/test_local_toolbelt.py`, `tests/test_workbook_engine.py`, `tests/test_workbook_runner.py`, `tests/test_workbook_path_parity.py`

**Dependencies:** Task 2 effective contract and admitted snapshot context.

**Authority:**
- Preauthorized local actions: edit material-view and snapshot-currentness owners, preserve existing provenance fields, and add focused resource/cancellation tests.
- Stop for: changed snapshot semantics, lost provenance, altered scope matching, or a need for a cache or second persistence owner.

**Steps:**
- [x] Step 1: Define the no-effective-scope predicate from the resolved filter contract and required scope dimensions.
- [x] Step 2: Return a material view that reuses immutable `layout.bindings` when no rows can be rejected; when filtering is requested, reuse the original `TypedTable` if every row is retained.
- [x] Step 3: Preserve material fingerprints, source SHA, scope fingerprints, rejected-row semantics, and cancellation behavior for filtered and unfiltered paths.
- [x] Step 4: Remove the normal snapshot-authoritative currentness hash after capture; keep explicit `WorkbookContext.currentness()` behavior for callers that request live-path comparison.
- [x] Step 5: Add tests asserting no extra table reconstruction/hash and exactly one source hash for snapshot-authoritative analysis.

**Verification:**
- [x] Unfiltered approved/direct paths preserve selected rows, provenance, analyzer output, and receipt identity.
- [x] Filtered paths preserve rejection reasons and cancellation behavior.
- [x] Instrumentation shows materialization and currentness hash counts decrease without changing correctness output.

**Exit Criteria:** no-op and all-retained paths reuse immutable tables, snapshot-authoritative execution uses the captured bytes only, and focused resource tests pass.

### Task 4: Make XLSX preflight selection-aware

**Purpose:** Prevent unrelated worksheets from consuming selected-material
allocation budgets or cold-read work for range/table-focused selections.

**Task Function:** bounded XLSX archive preflight correction.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: archive safety and extraction semantics are tightly coupled.

**Validator Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: fixture-based boundary tests provide direct proof.

**Specification Coverage:** archive-wide byte safety, selection-scoped allocation
limits, cancellation, hidden-sheet behavior, and extraction/preflight symmetry.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-performance-optimization`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/local_toolbelt.py:_preflight_xlsx_archive`, selection helpers, `spreadsheet_read`
- Verify: `tests/test_local_toolbelt.py`, `tests/test_workbook_path_parity.py`, `tests/fixtures/`

**Dependencies:** Task 1 baseline and the existing `SheetSelection` contract.

**Authority:**
- Preauthorized local actions: edit the preflight and shared selection predicate, add synthetic workbook fixtures/tests, and run local resource probes.
- Stop for: weakened archive-wide byte/ZIP/XML safety, hidden-row/merged-cell provenance regressions, or unsupported selection semantics.

**Steps:**
- [x] Step 1: Extract one predicate that answers whether a sheet can contribute to the requested sheet, range, or table selection.
- [x] Step 2: Use that predicate in both preflight counting and extraction; keep compressed/expanded archive limits global.
- [x] Step 3: Scope row, cell, merged-cell, and selected formula counts to contributing material; skip irrelevant worksheet XML parsing unless required for archive safety.
- [x] Step 4: Add a fixture with an unrelated oversized sheet and a small range/table selection; assert the selected case succeeds while a genuinely oversized selected case fails.
- [x] Step 5: Verify cancellation, hidden-sheet, table, range, and no-selection behavior remain symmetric.

**Verification:**
- [x] Range/table-only selection does not fail because of unrelated worksheet rows/cells.
- [x] Selected oversized material still fails with the existing safety error class.
- [x] Archive-wide byte and structural checks remain enforced.

**Exit Criteria:** preflight and extraction use the same selection semantics, with focused resource and parity proof passing.

### Task 5: Avoid the immediate reviewed-pending rewrite

**Purpose:** Remove one redundant persistence round trip for terminal review
decisions while preserving pending-state recovery and revision/token safety.

**Task Function:** persistence settlement optimization.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: review and persistence lifecycle changes require one owner and serialized proof.

**Validator Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: existing persistence and review tests cover the contract.

**Specification Coverage:** pending/committed lifecycle, review validity,
revision checks, idempotency, and failure recovery.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `src/foresight_os/analysis/review_workflow.py:review_and_accept_pending_analysis`, `accept_pending_analysis`
- Inspect: `src/foresight_os/persistence/analysis_store.py:save_pending_if_unchanged`, `commit_revision`; modify these helpers only if focused tests prove the existing commit path cannot accept the in-memory reviewed state without changing the pending-token or revision protocol.
- Verify: `tests/test_review_workflow.py`, `tests/test_persistence.py`, `tests/test_workbook_runner.py`

**Dependencies:** Task 2 admitted identity; do not change the pending token or
revision protocol.

**Authority:**
- Preauthorized local actions: edit review settlement and focused persistence tests while preserving store ownership and existing failure statuses.
- Stop for: weakened stale-review checks, altered committed-state semantics, non-idempotent retries, or a required schema migration.

**Steps:**
- [x] Step 1: Distinguish terminal ACCEPT/REJECT from remaining PENDING after review attachment.
- [x] Step 2: For terminal decisions, attach review in memory and call the existing commit path against the persisted pending token/revision without rewriting reviewed pending.
- [x] Step 3: For PENDING, retain the reviewed-pending write and existing resume behavior.
- [x] Step 4: Add write-count and stale-token tests for terminal, pending, retry, and failure paths.

**Verification:**
- [x] Terminal review performs one pending read/token validation and one committed write, with no redundant reviewed-pending rewrite.
- [x] Pending review remains recoverable and resumable.
- [x] Stale revision/token and commit failures remain fail-closed.

**Exit Criteria:** terminal settlement removes only the redundant write; all lifecycle and idempotency tests pass.

### Task 6: Benchmark the conditional cached-value load candidate

**Purpose:** Test the only remaining reader optimization after selection-aware
preflight is correct, without accepting an unsupported formula behavior.

**Task Function:** bounded performance candidate implementation and measurement.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: performance acceptance requires one measurement owner and matched workload evidence.

**Validator Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: correctness and resource gates are part of the same candidate proof.

**Specification Coverage:** formula/cached-value semantics, reader resource
limits, cold/warm performance, and explicit optimization deferral.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-performance-optimization`

**Files And Symbols:**
- Modify only if evidence supports it: `src/foresight_os/runtime/local_toolbelt.py:spreadsheet_read`, formula detection/preflight helpers
- Verify: `evaluation/probes/run_optimization_probe.py`, `evaluation/probes/compare_optimization_receipts.py`, `tests/test_local_toolbelt.py`, `tests/test_optimization_measurement.py`

**Dependencies:** Tasks 3 and 4; formula-free and formula-bearing fixtures.

**Authority:**
- Preauthorized local actions: add bounded formula-presence instrumentation, run matched baseline/release probes, and retain receipts under the declared work directory.
- Stop for: differing fixture/environment/sample definitions, formula correctness changes, resource regressions, or an unmeasurable cold noise floor.

**Steps:**
- [x] Step 1: Record selected-material formula presence during preflight without changing formula/cached-value interpretation.
- [x] Step 2: Run formula-free and formula-bearing correctness/resource fixtures; retain dual views for formulas.
- [x] Step 3: Compare process-cold, warm, source-change, scope-change, reuse, and growing-history workloads with identical fixture SHA and environment.
- [x] Step 4: Keep the candidate only if all workload-specific gates pass; otherwise revert the candidate and record `deferred` evidence.

**Verification:**
- [x] Formula-bearing output and provenance remain unchanged.
- [x] Formula-free selected material uses one workbook load only when the measured gate justifies it.
- [x] Comparator records accepted or deferred truthfully; no aggregate latency claim hides a cold regression.

**Exit Criteria:** conditional loading is either accepted with matched evidence or explicitly deferred without changing the correctness path.

### Task 7: Add cross-brief release evidence and reconcile documentation

**Purpose:** Prove the corrected identity boundaries across distinct briefs and
leave a recoverable final plan state.

**Task Function:** integration evidence, documentation, and final verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final reconciliation and acceptance remain lead-controller responsibilities.

**Validator Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final verification is performed by the lead controller.

**Specification Coverage:** cross-brief stability, source/contract/analyzer
receipt identity, maintained guidance, explicit deferrals, and final evidence.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `tests/test_workbook_path_parity.py`, `docs/architecture.md`, `README.md`
- Verify: all focused suites, full repository checks, and retained optimization receipts

**Dependencies:** Tasks 2-6.

**Authority:**
- Preauthorized local actions: add the representative cross-brief fixture, update maintained guidance, run final checks and probes, and reconcile the plan ledger.
- Stop for: missing cross-brief evidence, stale base/head state, failed required checks, copied disposable artifacts, or any unresolved required deferral.

**Steps:**
- [x] Step 1: Run one workbook through brief A (period/entity/scenario), brief B (different scope), brief C (stage-specific same-domain override), and brief D (partial contract using defaults).
- [x] Step 2: Assert effective contract fingerprints, selected tables/rows, canonical outputs, and reuse/non-reuse decisions for every brief.
- [x] Step 3: Update architecture and maintained README guidance only for behavior proven by source and tests; document any deferred candidate.
- [x] Step 4: Inspect final diff, generated surfaces, staged/unstaged/untracked state, and exact base/head SHAs.

**Verification:**
- [x] `python -m pytest -q`
- [x] `python -m compileall -q src tests evaluation`
- [x] `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/getting-started.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- [x] `git diff --check`
- Expected: all required checks pass, cross-brief evidence is fresh, and every deferred item is explicitly recorded.

**Exit Criteria:** a fresh controller can recover the completed task ledger,
proof, deferrals, base, head, and next Git action from this plan plus Git alone.

## Execution Evidence

- Base reconciliation: `origin/main` and `HEAD` both resolve to `e6755412fa5e3645332812d03b9df4a3a564f653`; work ran only in the dedicated worktree.
- Focused proof: workbook, execution-gate, persistence, review, local-toolbelt, runner, engine, parity, and runtime-boundary suites pass; `tests/test_workbook_path_parity.py` covers distinct entity scopes, stage-specific identity, and defaulted contracts on one workbook.
- Full proof: `python -m pytest -q` passes; `python -m compileall -q src tests evaluation` passes; the Markdown-link checker reports 45 checked paths; `git diff --check` passes.
- Release probe: `work/optimization-release/receipt.json` is `VERIFIED`; mandatory workbook workloads, correctness, allocation, and soak are verified. Expected handoff-configuration, group-chat max-round, and optional MCP teardown warnings are probe-framework/external-fixture diagnostics, not workbook defects; the receipt's native MCP boundary remains `VERIFIED`.
- Measured effects: snapshot-authoritative repeated investigation reports `currentness_hash_count=0`, formula-free selected material uses one openpyxl load, formula-bearing material retains two loads, and terminal review uses one pending write plus one committed write. Explicit live-path `WorkbookContext.currentness()` remains available and is separately measured.
- Timing claim: process-cold/pattern timing gates remain not accepted because the probe's timing gate is intentionally disabled/noise-gated; no latency improvement is claimed. The conditional load change is retained because correctness, resource, warm/reuse, and cold-noise-floor gates pass.

## Verification

Structural, backend, resource, and performance proof remain separate:

- Focused correctness proof covers partial/defaulted contracts, stage/global
  precedence, admission mutation, direct/approved parity, no-op materialization,
  snapshot hash count, selection-aware preflight, review settlement, and retry.
- Backend boundary proof covers admission, snapshot capture, workbook read,
  materialization, canonical commit/review, receipt reuse, and failure/blocked
  paths.
- Resource proof covers archive-wide safety, selected-material limits, formulas,
  cached values, hidden rows, merged ranges, provenance, and cancellation.
- Performance proof uses identical fixture SHA, environment, sample counts, and
  workload definitions. Cold, warm, source-change, scope-change, reuse, and
  growth gates are reported independently; a candidate is deferred when the
  empirical cold noise floor is not measurable.
- Final repository proof runs the full test suite, compile check, Markdown-link
  checker, diff check, and dedicated-worktree scope inspection.

## Completion Criteria

The plan is ready for completion verification when:

1. approved execution uses one admitted immutable bundle and one effective
   stage/domain workbook contract;
2. direct and approved paths agree on defaults, selected material, fingerprints,
   canonical output, and reuse/non-reuse behavior;
3. no-op materialization, snapshot currentness re-hashing, and terminal review
   pending rewrites are removed without weakening lifecycle or provenance rules;
4. XLSX preflight is selection-aware and archive-wide safety remains intact;
5. conditional cached-value loading is accepted only with matched formula,
   resource, cold, warm, reuse, and history evidence, or is explicitly deferred;
6. cross-brief evidence covers changed scope, stage overrides, and partial
   defaulted contracts; and
7. final verification reports exact base/head SHAs, required command results,
   documentation reconciliation, retained evidence, and no unrelated changes.

The plan remains `proposed` until `skill-verification-before-completion`
returns `verified`.

## Explicit Deferrals

- Do not add a workbook cache, reuse database, provenance model, parser
  abstraction, executor layer, or second persistence owner.
- Do not remove the dual openpyxl load globally; only accept a formula-aware
  conditional candidate with matched evidence.
- Defer per-domain registry factory simplification to a separate maintenance
  pass unless Task 2 proves it is required for single-source contract resolution.
- Defer `agent-framework` optional packaging and `pandas` removal to a separate
  packaging plan with isolated install/import and dynamic-consumer proof.
- Do not claim latency improvement from PR #38's rejected base-vs-instrumented
  comparison; this plan must produce a new matched comparison.

## Self-Review

- P0 findings are addressed before optimization work and share the existing
  admission, resolver, engine, and persistence owners.
- Every P1 optimization has an independent correctness/resource gate and an
  explicit deferral path.
- Snapshot, review, and receipt semantics remain authoritative; no new cache,
  store, or orchestration layer is introduced.
- Selection-aware preflight is separated from conditional cached-value loading
  so a reader optimization cannot mask a selection bug.
- Cross-brief release evidence is a required gate rather than an unmeasured
  benchmark scenario.
