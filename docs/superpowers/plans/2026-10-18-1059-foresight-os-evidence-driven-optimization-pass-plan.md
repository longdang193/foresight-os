---
layer: change
artifact_type: plan
status: in_progress
template_id: implementation-plan
contract_version: "1"
name: foresight-os-evidence-driven-optimization-pass
targets:
  - src/foresight_os/controller/recipes.py
  - src/foresight_os/domain/approval.py
  - src/foresight_os/persistence/analysis_store.py
  - src/foresight_os/runtime/execution_gate.py
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/analysis/evidence_workflow.py
  - src/foresight_os/analysis/technology_radar.py
  - src/foresight_os/analysis/supplier_resilience.py
  - src/foresight_os/analysis/ev_capacity_investment.py
  - src/foresight_os/analysis/portfolio_resilience.py
  - src/foresight_os/analysis/powerbi_strategic_portfolio.py
  - src/foresight_os/analysis/foresight_validator.py
  - src/foresight_os/analysis/review_workflow.py
  - src/foresight_os/controller/policy.py
  - evaluation/probes/optimization_measurement.py
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/compare_optimization_receipts.py
  - tests/test_approval_contract.py
  - tests/test_execution_gate.py
  - tests/test_evidence_workflow.py
  - tests/test_local_toolbelt.py
  - tests/test_optimization_measurement.py
  - tests/test_result_committer.py
  - tests/test_runtime_boundaries.py
  - docs/superpowers/plans/2026-10-18-1059-foresight-os-evidence-driven-optimization-pass-plan.md
---

# ForesightOS Evidence-Driven Optimization Pass

## Goal

Reconcile the still-open legacy-recipe compatibility PR with the current
`main`, centralize its compatibility behavior, and use trustworthy end-to-end
measurements to remove only duplicate ordinary-path work that is proven to be
material. Preserve provenance, approval currentness, cancellation settlement,
transactional publication, bounded resources, canonical result validation,
review/commit boundaries, and source identity.

The pasted optimization recommendation is directionally accepted but is not a
single implementation batch. Its baseline is stale relative to the current
checkout: PR #33 is open, GitHub reports its base as `main` at
`7881831dc7785adb9a17b8b4378fee1f2260c1e`, while the local `origin/main`
ref is behind. Task 1 establishes the authoritative integration base before
any optimization result is treated as valid evidence.

## Implementation Outcomes

### Reconciled compatibility boundary

PR #33 is rebased or otherwise reconciled against the recorded current
`origin/main` base. Legacy `metadata["analysis_contract_domains"]` is handled
by one recipe-boundary transformation with explicit stage fields taking
precedence. Approval history is preserved, material mutations still require
reapproval, and the execution gate does not reread the recipe file solely to
reconstruct a persisted fingerprint.

### Truthful optimization evidence

The existing optimization probe reports separate cold, warm, persistence,
correction, synthesis, cancellation, cleanup, and analytical-correctness
evidence. Correctness, regression-threshold status, and demonstrated
improvement remain separate outcomes. Benchmark artifacts stay outside Git
unless an owning evaluation contract explicitly requires a fixture or schema
change.

Task 2 is a correctness and ownership consolidation, not a measured speedup.
Its proof is the focused recipe-read reduction and compatibility regression
suite. Baseline and release performance receipts apply only to the one
production optimization selected after Task 3.

### Bounded ordinary-path simplification

Only after measurement gates pass, the implementation makes exactly one
evidence-selected ordinary-path production optimization. A workbook-context
reuse change may reuse the existing run-owned `WorkbookContext`, carry
admitted normalized intent forward, and remove duplicate contract/lifecycle
derivation; another measured owner may be selected instead. No global cache,
orchestration framework, recovery engine, new durable intent store, or broad
controller rewrite is introduced.

### Explicit deferrals

Persistence-history optimization, participant-local recovery, synchronous
synthesis offload, controller flattening, and compatibility-shim removal are
recorded as follow-ups when they are not the single Task 4 selection. They are
not implemented in this pass. A clean regression result is not reported as an
optimization improvement.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-backend-verification`, `skill-performance-optimization`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: dedicated worktree created from the recorded current `origin/main` commit; preserve the existing dirty checkout unchanged
- Commit policy: verified local commits are permitted in the dedicated worktree after task-local proof; branch disposition is handled only after fresh verification and explicit authorization
- Preauthorized local actions: inspect declared owners, create the named worktree, edit declared plan-lane files, run focused tests/probes, write benchmark artifacts under `work/`, create verified local commits in the dedicated worktree, and run repository verification commands
- User-approval actions: rebase conflict resolution with semantic choices, push, pull-request changes, merge, external provider writes, destructive cleanup, and discarding unrelated work
- Parallel ownership: none; compatibility, measurement, and runtime changes share approval, persistence, and workbook boundaries
- Sequential fallback: Task 1 integration gate, then Task 2 compatibility, then Task 3 measurement, then exactly one evidence-selected production optimization, then final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/foresight-os-evidence-driven-optimization-pass`
- Base commit: `7881831dc7785adb9a17b8b4378fee1f2260c1e`
- Expected workspace: current checkout remains dirty and preserved; implementation worktree starts clean
- Evidence anchors: base `7881831dc7785adb9a17b8b4378fee1f2260c1e`; compatibility `5a6669cea80d8ded049f94c69f460f30bdc41d4f`; prior implementation/final-verification SHA `1d41fcc1dbe6d8c2aa4acf4f5edd6d575f7f6344`; review cycle 1 head `55576decd3bef704b6f072b6a576c3a199c39581`; cross-revision baseline/release receipts under `work/optimization-review-{baseline,release}/`; selected optimization is public workflow `WorkbookContext` reuse
- Next action: commit and push the review corrections, rerun the bounded review cycle, and merge only after review completion
- Blockers: none for implementation; MAF/timing-path latency remains diagnostic-only because repeated runs showed nondeterministic noise beyond the deterministic release gate

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | dedicated worktree | lead controller | none | fetched base, PR ancestry, clean lane inventory | base `7881831`; PR #33 reconciled with commits `615fb95`, `2f2d45a` |
| Task 2 | `completed` | dedicated worktree | lead controller | Task 1 | compatibility and mutation regressions | commit `5a6669c`; focused recipe/gate/persistence tests passed |
| Task 3 | `completed` | dedicated worktree | lead controller | Task 2 | repaired deterministic baseline and scenario evidence | baseline receipt `VERIFIED`; explicit phases/scenarios/retained bytes; comparison harness updated |
| Task 4 | `completed` | dedicated worktree | lead controller | Task 3 | exactly one selected optimization with before/after proof | public workflow context reuse; comparison `PASS`; captures/parses `2 -> 1` |
| Task 5 | `in_progress` | dedicated worktree | lead controller | Tasks 1-4 | full verification and handoff evidence | prior verification passed; review cycle 1 found benchmark revision-identity and collapsed-result gate defects; fixes verified locally, final SHA pending |

## Task Breakdown

### Task 1: Establish the integration base and reconcile PR #33

**Purpose:**
- Make PR #33's verification evidence current before changing runtime behavior.

**Task Function:**
- Integration audit and bounded branch reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: Git state, PR ancestry, and conflict inventory are authority-sensitive and should remain under the lead controller.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: Git ancestry and repository checks are the task-local validator.

**Specification Coverage:**
- Current-base reconciliation precedes optimization; unrelated dirty work is preserved.

**Required Skills:**
- `skill-using-git-worktrees`, `skill-finishing-a-development-branch`

**Files And Symbols:**
- Inspect: PR #33 metadata, `git rev-parse origin/main`, `git merge-base`, `git diff`
- Modify: no source files; branch/worktree metadata only after explicit authorization
- Verify: repository status, worktree inventory, PR base/head ancestry

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: fetch refs, inspect ancestry, create the dedicated worktree, and record immutable base/head evidence.
- Stop for: semantic conflict resolution, dirty lane content, changed PR scope, or any need to discard unrelated files.

**Steps:**
- [x] Step 1: Fetch `origin`, record the fetched `origin/main` SHA, PR #33 base/head SHAs, and the merge base.
- [x] Step 2: Create `codex/foresight-os-evidence-driven-optimization-pass` from the fetched base without copying the current checkout's dirty files.
- [x] Step 3: Apply the PR #33 reconciliation in the dedicated lane only if the PR remains the selected compatibility vehicle; otherwise record the immutable replacement decision and preserve the PR branch.

**Verification:**
- [x] `git status --short --branch`, `git worktree list --porcelain`, `git merge-base --is-ancestor`, and `gh pr view 33 --json baseRefOid,headRefOid,state,mergedAt`
- Expected: clean implementation worktree, recorded base/head identity, and no unrelated file enters the lane.

**Exit Criteria:**
- The lane has a clean, current base and an explicit PR integration decision; no source optimization begins before this evidence exists.

### Task 2: Centralize legacy recipe compatibility and remove the duplicate recipe read

**Purpose:**
- Preserve old approved recipe admission while giving recipe serialization one compatibility owner and one file read.

**Task Function:**
- Compatibility-boundary consolidation with approval-currentness preservation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: approval identity and persistence semantics require a single owner and direct review.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused approval and gate tests cover the direct boundary and mutation failures.

**Specification Coverage:**
- Explicit `analysis_domains` wins over legacy metadata, malformed metadata is deterministic, old fingerprints remain valid only for the historical representation difference, and material changes remain denied.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/controller/recipes.py:ExecutionRecipe.from_dict`, `RecipeStage.from_dict`
- Inspect/modify: `src/foresight_os/domain/approval.py:ApprovalProjection`
- Inspect/modify: `src/foresight_os/persistence/analysis_store.py:load_recipe`
- Inspect/modify: `src/foresight_os/runtime/execution_gate.py:ExecutionGate.admit`, `ApprovedExecution`
- Verify: `tests/test_approval_contract.py`, `tests/test_execution_gate.py`, `tests/test_approval_persistence.py`

**Dependencies:**
- Task 1 complete and the PR/base diff is immutable.

**Authority:**
- Preauthorized local actions: edit only the named compatibility/persistence/gate owners and their focused tests; run the named test modules.
- Stop for: a need to rewrite approval records, broaden accepted fingerprint alternatives, change recipe schema semantics, or alter unrelated persistence contracts.

**Steps:**
- [x] Step 1: Extract one pure `normalize_legacy_recipe_dict(raw_dict)` transformation at the recipe boundary; reuse it from canonical loading and approval projection normalization.
- [x] Step 2: Ensure explicit `analysis_domains=[]` is preserved, legacy values use the canonical string coercion, malformed metadata yields the documented deterministic empty result, and new serialization does not emit legacy metadata.
- [x] Step 3: Extend `AnalysisStore` with one load result that retains the raw persisted dictionary/fingerprint alongside the canonical `ExecutionRecipe`; update `ExecutionGate` to use that result and retain the immediate approval-currentness reread before dispatch only where it establishes a new race boundary.
- [x] Step 4: Add regressions for empty/no metadata, nonempty metadata, explicit empty override, malformed metadata, coercion, material mutation denial, and canonical serialization.

**Verification:**
- [x] `python -m pytest -q tests/test_approval_contract.py tests/test_execution_gate.py tests/test_approval_persistence.py`
- Expected: legacy admission passes, material mutations fail, approval fingerprints remain stable, and the recipe file read count falls from 2 to 1 per admission path as shown by focused instrumentation or a mock. Do not claim a performance improvement from this task.

**Exit Criteria:**
- One compatibility transformation owns the historical representation, the gate has no redundant recipe reread, and all approval/security regressions pass.

### Task 3: Repair the optimization probe and capture the baseline

**Purpose:**
- Produce reproducible end-to-end evidence that distinguishes correctness, regression thresholds, and actual improvement.

**Task Function:**
- Benchmark instrumentation and evidence-contract hardening.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve after Task 1 based on benchmark scope, measurement complexity, and local profile availability.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic receipt comparison and focused probe tests are sufficient.

**Specification Coverage:**
- Separate cold/warm runs, workbook capture/parse/currentness/cache counters, persistence cost, model/correction cost, synthesis/cancellation latency, cleanup, and analytical correctness.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `evaluation/probes/optimization_measurement.py:_metric_snapshot`, `_summarize_samples`, `observed_xlsx_state`
- Inspect/modify: `evaluation/probes/run_optimization_probe.py:_run`, `_measure_workbook`, `_measure_patterns`, `_soak_receipt`
- Inspect/modify: `evaluation/probes/compare_optimization_receipts.py`
- Verify: `tests/test_optimization_measurement.py`, `evaluation/README.md`

**Dependencies:**
- Task 2 complete; baseline and release use the same fixture, environment metadata, sample count, and receipt schema.

**Authority:**
- Preauthorized local actions: edit probe/instrumentation files and focused measurement tests; write outputs only under `work/`.
- Stop for: missing representative workload, unstable fixture identity, unavailable required counter, or a benchmark that measures only a proxy rather than the end-to-end path.

**Steps:**
- [x] Step 1: Add explicit cold, warm-1, and warm-2-plus workload labels instead of combining repeated elapsed time.
- [x] Step 2: Capture persistence duration/bytes, peak retained memory/bytes, workbook capture and parse counts, currentness hashes, cache hits, model/tool/correction counts, synthesis duration, cancellation latency, cleanup status, and analytical result fingerprints before context cleanup.
- [x] Step 3: Use deterministic provider-free fixture workloads for the release gate. Keep changed briefs, changed selection, growing analysis history, correction, cancellation during workbook work, and cancellation during synthesis as separately labeled scenario probes; they are mandatory release gates only when the selected Task 4 optimization touches those paths.
- [x] Step 4: Update comparison logic so `correctness`, `regression_threshold`, and `improvement_demonstrated` are separate fields with explicit sample/threshold provenance.

**Verification:**
- [x] `python -m pytest -q tests/test_optimization_measurement.py`
- [x] `python evaluation/probes/run_optimization_probe.py --mode baseline --fixture tests/fixtures/analyst_multisheet.xlsx --output work/optimization-baseline/receipt.json`
- Expected: deterministic receipt schema, analytical correctness remains valid, and correctness, regression-threshold status, and improvement-detected outcomes remain separate. Live provider latency is not part of the deterministic release gate, and improvement is not claimed when only non-regression is shown.

**Exit Criteria:**
- The probe can identify a measured bottleneck and produce comparable baseline/release receipts without changing production behavior.

### Task 4: Implement exactly one evidence-selected ordinary-path optimization

**Purpose:**
- Remove exactly one material repeated operation identified by Task 3 without introducing a new cache or durable intent layer.

**Task Function:**
- Narrow owner-local performance refactor with ownership-preserving reuse.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: choose the single largest eligible ordinary-path bottleneck after Task 3; record rejected opportunities as follow-ups.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct workflow, context-ownership, and cross-brief portability tests.

**Specification Coverage:**
- The selected owner retains source identity, approval currentness, cancellation, cleanup, and publication semantics. If workbook reuse is selected, source-derived material may be reused, brief-dependent conclusions must be recomputed, and caller-provided contexts remain borrowed and are never closed by the callee.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-systematic-debugging`

**Files And Symbols:**
- Inspect/modify when workbook reuse is selected: `src/foresight_os/analysis/technology_radar.py:run_technology_radar_workflow`, `src/foresight_os/analysis/supplier_resilience.py:run_supplier_resilience_workflow`, `src/foresight_os/analysis/ev_capacity_investment.py:run_ev_capacity_investment_workflow`, `src/foresight_os/analysis/portfolio_resilience.py:run_portfolio_resilience_workflow`, `src/foresight_os/analysis/powerbi_strategic_portfolio.py:run_powerbi_strategic_portfolio_workflow`, and `src/foresight_os/analysis/foresight_validator.py:run_validator_workflow`
- Keep `src/foresight_os/analysis/evidence_workflow.py` out of the change unless Task 3 identifies an additional duplicate there that is part of the single selected optimization.
- If another ordinary-path bottleneck wins the Task 3 selection, modify only its canonical owner: `src/foresight_os/runtime/local_toolbelt.py:WorkbookContext.read`, `WorkbookContext.analyze`, `_analyze_in_transaction`; `src/foresight_os/runtime/workflow.py:_stage_cache_key`, `_synthesize_stage_outputs`; or `src/foresight_os/controller/policy.py:_recipe_for_patterns`.
- Inspect/modify: `src/foresight_os/runtime/local_toolbelt.py:WorkbookContext`, `SourceSnapshot`
- Inspect/modify: `src/foresight_os/runtime/execution_gate.py:ApprovedExecution`, `ExecutionGate.execute`
- Inspect/modify: `src/foresight_os/runtime/workflow.py:run_recipe_async`
- Verify: `tests/test_evidence_workflow.py`, `tests/test_local_toolbelt.py`, `tests/test_runtime_boundaries.py`, `tests/test_technology_powerbi_validator.py`, `tests/test_supplier_and_ev_resilience.py`, and `tests/test_portfolio_resilience.py` as selected by the changed owner

**Dependencies:**
- Task 3 must identify one material repeated operation, its exact call path, and its canonical owner.

**Authority:**
- Preauthorized local actions: modify only the named workflow/gate/context owners and focused tests; preserve current cancellation, cleanup, authority, and snapshot contracts.
- Stop for: a global cache, cross-run mutable state, changed source identity semantics, or a brief-dependent result becoming reusable by source hash alone.

**Steps:**
- [x] Step 1: Record the selected duplicate operation, baseline count/latency/memory, target metric, canonical owner, and rejected follow-ups before editing.
- [x] Step 2: Implement the smallest owner-local change. If workbook reuse is selected, thread one caller-owned `WorkbookContext` through the six public domain workflows above rather than changing only the already-supported evidence workflow boundary.
- [x] Step 3: Add focused regression proof for the selected owner. For workbook reuse, invoke one public domain workflow twice with one caller-owned context and different contracts, proving one capture, one parse/material view, reuse on the second run, distinct contract fingerprints, distinct results when brief semantics differ, and an open caller-owned context after both calls.

**Verification:**
- [x] `python -m pytest -q tests/test_evidence_workflow.py tests/test_local_toolbelt.py tests/test_runtime_boundaries.py tests/test_technology_powerbi_validator.py tests/test_supplier_and_ev_resilience.py tests/test_portfolio_resilience.py tests/test_result_committer.py tests/test_controller_selection.py`
- [x] Rerun the Task 3 receipt comparison on the same fixture and workload matrix.
- Expected: the selected metric improves past its configured threshold without changed provenance, result, cancellation, or cleanup outcomes. If no eligible metric clears the threshold, record deferral and do not change production code.

**Exit Criteria:**
- Exactly one measured duplicate path is removed with unchanged ownership and analytical semantics, or the single optimization task is recorded as deferred with the measurement evidence.

**Recorded Selection:**
- Selected owner: public domain workflow wrappers forwarding a caller-owned `WorkbookContext` to their existing analyzers.
- Before/after evidence: `public_workflow_context_reuse` reduced capture and XLSX parse counts from `2` to `1`; focused regression preserved distinct contract fingerprints, distinct brief-scoped results, and an open borrowed context.
- Rejected follow-ups: global or cross-run caches, persistence-history optimization, participant recovery, synchronous synthesis offload, controller flattening, and compatibility-shim removal remain deferred because they were not the measured duplicate owner for this pass.

### Task 5: Final verification and handoff

**Purpose:**
- Produce a fresh, complete verification record for the implemented subset and all recorded deferrals.

**Task Function:**
- Cross-task verification and readiness handoff.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance and plan state are lead-controller responsibilities.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: repository-required commands and fresh receipt comparison.

**Specification Coverage:**
- All mandatory outcomes, task-local proofs, scope deviations, deferrals, and generated/documentation surfaces are reconciled.

**Required Skills:**
- `skill-verification-before-completion`, `skill-plan-document-reviewer`

**Files And Symbols:**
- Verify: all changed files, task ledger, benchmark receipts under `work/`, and PR/rebase evidence from Task 1

**Dependencies:**
- Tasks 1-4 complete or explicitly deferred.

**Authority:**
- Preauthorized local actions: run final verification, inspect diff, update the plan ledger with evidence, and report blockers.
- Stop for: any stale proof, unrecorded scope, failed required command, unresolved plan task, or dirty lane state that affects the implementation.

**Steps:**
- [x] Step 1: Run focused tests for each changed owner and the optimization receipt comparison.
- [x] Step 2: Run `python -m pytest -q` and `python -m compileall -q src tests evaluation`.
- [x] Step 3: Run deterministic repository checks and inspect `git diff --check` plus the final changed-file inventory.
- [x] Step 4: Record verification status, residual risks, deferred tasks, and the exact Git disposition needed next, anchored to the integration-base, compatibility-consolidation, baseline, selected-optimization, and final-verification SHAs.

**Verification:**
- [x] `python -m pytest -q`
- [x] `python -m compileall -q src tests evaluation`
- [x] repository deterministic check defined by the current project contract
- Expected: all required checks pass, or each failure is explicitly classified as unrelated, blocked external, or a plan defect with no false completion claim.

**Exit Criteria:**
- `skill-verification-before-completion` can evaluate the plan as `verified`, `incomplete`, or `blocked` from fresh evidence; the plan is not marked completed by checkbox state alone.

## Verification

- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `python evaluation/probes/run_optimization_probe.py --mode baseline --fixture tests/fixtures/analyst_multisheet.xlsx --output work/optimization-baseline/receipt.json`
- `python evaluation/probes/run_optimization_probe.py --mode release --fixture tests/fixtures/analyst_multisheet.xlsx --output work/optimization-release/receipt.json`
- `python evaluation/probes/compare_optimization_receipts.py --baseline work/optimization-baseline/receipt.json --release work/optimization-release/receipt.json`
- `git diff --check`
- Current repository deterministic checks identified during Task 1 and recorded with immutable command output

## Completion Criteria

The plan is ready for completion verification when:

1. PR #33 integration evidence uses the fetched current base rather than the stale local ref or pasted baseline alone.
2. Legacy recipe compatibility has one transformation owner, preserves explicit values, and has focused mutation/security regressions.
3. The execution gate no longer rereads the same recipe file for a second fingerprint parse unless a separately documented currentness boundary requires it.
4. The optimization probe distinguishes correctness, regression-threshold status, and demonstrated improvement across representative workloads.
5. The single production change selected in Task 4 has a measured baseline, focused regression proof, and before/after receipt; Task 2 has the separate recipe-read and compatibility proof without a speedup claim.
6. All deferred recommendations have an evidence-based reason and no speculative replacement architecture was added.
7. Required tests, compile checks, deterministic checks, plan ledger, and final diff are fresh and reconciled.

The plan may be marked `completed` only after
`skill-verification-before-completion` returns `verified`.
