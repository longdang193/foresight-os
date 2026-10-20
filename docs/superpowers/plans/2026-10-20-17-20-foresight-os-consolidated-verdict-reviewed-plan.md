---
layer: change
artifact_type: plan
status: in_progress
template_id: implementation-plan
contract_version: "1"
name: foresight-os-consolidated-verdict-reviewed
targets:
  - src/foresight_os/persistence/analysis_store.py
  - src/foresight_os/domain/analysis_inputs.py
  - src/foresight_os/domain/validation.py
  - src/foresight_os/controller/policy.py
  - src/foresight_os/analysis/workbook_inputs.py
  - src/foresight_os/analysis/workbook_engine.py
  - src/foresight_os/analysis/workbook_runner.py
  - src/foresight_os/runtime/local_toolbelt.py
  - evaluation/probes/optimization_measurement.py
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/compare_optimization_receipts.py
  - evaluation/README.md
  - docs/evidence-and-evaluation.md
  - tests/
  - work/optimization-runs/consolidated-verdict-reviewed/
---

# ForesightOS Consolidated Verdict Reviewed Plan

## Review Of The Recommendation

The consolidated verdict is directionally correct and implementation-ready
after narrowing the work to evidence-backed changes. The PR #35-#41
architecture remains the baseline: do not begin a new workbook parser,
persistence store, cache, journal, provider-plan layer, executor layer, or
second analytical state owner.

The review makes four corrections explicit:

- The P0 recovery defect is the `restore_revision_snapshot()` write path
  recreating a bare pending-token list. Normal settlement is already scoped;
  preserve legacy list reading but never emit the legacy shape.
- The changed-brief workload must vary material workbook scope and expected
  result identity, not only objective or assumption text.
- `changed_brief` aliases `approved_changed_brief`, and
  `public_workflow_context_reuse` aliases `repeated_investigation`; aliases
  cannot count as independent optimization evidence.
- `NormalizedIntent` cleanup is conditional maintenance, not a confirmed
  runtime bug. Inventory consumers before changing its contract or removing
  dependencies.

## Goal

Close the remaining revision-recovery and workbook-binding correctness gaps,
then make the optimization evidence cheaper, durable, and decision-useful.
The implementation must preserve the current contract-authoritative workbook
architecture, local provider-free execution, receipt invalidation semantics,
and the rule that persistence changes are made only after measured evidence
shows a material end-to-end benefit above the workload's noise floor.

## Implementation Outcomes

### Correctness and contract authority

Pending-token snapshots restore into the revision-scoped object format, with
backward-compatible reads for old list files. Approved workbook execution
fails early when stage-specific bindings are missing or ambiguous, while
direct global declarations and whole-contract stage shadowing retain their
existing supported behavior.

### Trustworthy cross-brief evidence

The approved changed-brief workload uses materially different fixture scopes,
proves distinct consumed-domain/result identities, rejects stale receipts, and
confirms unaffected-stage reuse without counting aliases as independent
evidence.

### Measured optimization and durable evidence

The harness has smoke, targeted, and release profiles with explicit workload
selection and lazy external-probe imports. Selected-sheet, cancellation,
history, and stage-receipt measurements use bounded scaling cases and record
reproducible metadata. A compact immutable manifest and maintained evaluation
guidance make the evidence reusable without rerunning discovery.

### Separate maintenance boundary

Contract simplification, `NormalizedIntent` changes, and dependency cleanup
remain outside this delivery. They require a separate plan so later API or
packaging changes cannot make this measurement evidence stale.

## Execution Approach

- Mode: `parallel-capable`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `task-specific worktree`; execute from a clean worktree based on `origin/main`, not the dirty current checkout
- Commit policy: `verified per-task checkpoint commits preauthorized`
- Preauthorized local actions: edit owned files in the clean worktree, run declared local tests/compile/link checks, inspect Git history and source, write bounded local measurement artifacts, and create local checkpoint commits after verified boundaries
- User-approval actions: push, merge, publication, external writes, destructive recovery, discard, cleanup, or changes outside the task-owned files
- Parallel ownership: Task 1 and Task 2 own disjoint correctness surfaces; Task 5 and Task 6 own disjoint measurement lanes; Task 7 owns release qualification and manifest generation
- Sequential fallback: run Task 1 then Task 2, converge before Task 3, run Tasks 5 and 6 independently after Task 4, then run Task 7; stop only when a prerequisite materially invalidates the task assumptions

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/foresight-os-consolidated-verdict`
- Base commit: `91aeaca09f7a2f098e18c6dc13e96dc33608201c` (`origin/main`)
- Expected workspace: isolated worktree; preserve the original checkout's unrelated dirty/untracked paths untouched
- Next action: complete final release packaging and repository-wide verification from the accepted checkpoint
- Blockers: none known; remain pinned to the declared base and record upstream movement; stop only if an upstream change materially invalidates the task assumptions or required source paths are absent

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `complete` | isolated worktree | lead controller | none | focused snapshot/replay tests and correctness checkpoint | `5b652e3`; focused recovery/result/evidence tests passed |
| Task 2 | `complete` | isolated worktree | lead controller | none | policy/validation binding tests and correctness checkpoint | existing behavior verified; focused workbook/policy suites passed without production patch |
| Task 3 | `complete` | isolated worktree | lead controller | Tasks 1-2 | changed-brief workload assertions | `8668c2a`; approved changed-brief samples prove distinct contracts, consumed technologies, calculations, result/recommendation identities, stale-receipt rejection, and unaffected-stage reuse |
| Task 4 | `complete` | isolated worktree | lead controller | Task 3 | harness profile, import, and instrumentation checkpoint | `8668c2a`; smoke/targeted profiles, alias/profile tests, and fresh import blocker passed |
| Task 5 | `complete` | isolated worktree | lead controller | Task 4 | selected-sheet scaling receipt | `8668c2a`; `8x128`, `24x512`, and `48x2048` cases verified with selected-sheet controls |
| Task 6 | `complete` | isolated worktree | lead controller | Tasks 1 and 4 | persistence phase measurements and candidate checkpoint if eligible | `8668c2a`; histories `10/100`, receipts `10/50/100`, hashing, snapshot capture/restore, locking, serialization, and I/O verified; no optimization candidate retained because material end-to-end benefit was not established |
| Task 7 | `pending` | clean worktree | `unresolved` | Tasks 5-6 | release qualification and new-namespace manifest | pending |

## Task Breakdown

### Task 1: Restore revision-scoped pending tokens

**Purpose:**
- Make cancellation/recovery preserve the same revision-scoped pending-token format used by normal settlement, without breaking reads of legacy list files.

**Task Function:**
- Repair the persistence write-path invariant and add a replay regression.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded backend correctness change with a clear owner and low ambiguity.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused tests and final backend verification are sufficient.

**Specification Coverage:**
- Consolidated verdict section 1; `AnalysisStore` owns pending-token persistence and revision recovery.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/persistence/analysis_store.py:capture_revision_snapshot`, `restore_revision_snapshot`, `_remember_consumed_pending_token`, and `_load_consumed_pending_tokens`
- Modify: `src/foresight_os/persistence/analysis_store.py` and the focused recovery, result-committer, and evidence-workflow tests
- Verify: `tests/test_recovery.py`, `tests/test_result_committer.py`, `tests/test_evidence_workflow.py`, and the persisted `analysis.pending.tokens.json` shape

**Dependencies:**
- Clean worktree pinned to base commit `91aeaca09f7a2f098e18c6dc13e96dc33608201c`.

**Authority:**
- Preauthorized local actions: edit `AnalysisStore` and focused tests, run their local test subset, inspect temporary JSON fixtures, and create a correctness checkpoint commit after proof passes.
- Stop for: any need to change the persistence schema beyond the scoped token object, alter unrelated recovery behavior, or use destructive cleanup.

**Steps:**
- [x] Step 1: Trace snapshot capture, restore, acceptance, rejection, and replay paths; identify the legacy list write in `restore_revision_snapshot()`.
- [x] Step 2: Route both restoration and normal consumption through one revision-scoped writer, using the restored accepted-state revision and an explicit fallback when no accepted state exists; retain list-format reads and revision filtering for compatibility.
- [x] Step 3: Add the accepted-revision to cancel/restore to stale-replay scenario, inspect the actual token file, and assert it contains an object such as `{"revision": 7, "tokens": ["..."]}`, never a bare array.
- [x] Step 4: Create a local correctness checkpoint commit only after the focused recovery, result-committer, and evidence-workflow tests pass.

**Verification:**
- [x] `python -m pytest -q tests/test_recovery.py tests/test_result_committer.py tests/test_evidence_workflow.py`
- Expected: the cancellation/replay regression passes, restored token JSON is an object containing the restored accepted revision and tokens, and the ledger never returns to a bare array.

**Exit Criteria:**
- The same writer is used by all token-producing paths, the old list format remains readable, and focused recovery tests prove stale replay is rejected.

### Task 2: Enforce explicit stage-scoped workbook binding

**Purpose:**
- Make approved deterministic execution fail early for missing or ambiguous stage bindings while preserving supported global declarations and whole-contract stage shadowing.

**Task Function:**
- Reconcile policy stage-domain selection, recipe validation, contract resolution, and runner admission around one explicit stage/global binding rule.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: contract behavior spans a small set of existing owners; correctness is more important than parallel speed.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing stage-input, workbook-input, and runner tests cover the boundary directly.

**Specification Coverage:**
- Consolidated verdict sections 3 and 12; `AnalysisInputContract` and workbook resolver remain the single contract authorities.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/controller/policy.py:stage_analysis_domains`, `src/foresight_os/domain/validation.py:validate_execution_recipe`, `src/foresight_os/domain/analysis_inputs.py:AnalysisInputContract`, `src/foresight_os/analysis/workbook_inputs.py:resolve_workbook_contract`, and `src/foresight_os/analysis/workbook_runner.py:WorkbookWorkflowRunner`
- Modify: policy/recipe compilation and validation owners; keep `resolve_workbook_contract()` narrow; update `tests/test_controller_selection.py`, `tests/test_stage_inputs.py`, `tests/test_approval_contract.py`, `tests/test_execution_gate.py`, `tests/test_workbook_runner.py`, and directly affected contract tests
- Verify: direct global declaration behavior, stage-specific resolution, whole-contract shadowing, deterministic recipe validation, and approved execution admission

**Dependencies:**
- Independent of Task 1; both correctness lanes converge before Task 3, and no contract simplification is allowed to obscure either fix.

**Authority:**
- Preauthorized local actions: edit policy/validation/contract owners and focused tests, then run deterministic local execution tests and create a correctness checkpoint commit after proof passes.
- Stop for: a proposed second registry, provider-plan layer, silent fallback, or a behavior change that removes supported global declarations without an explicit contract decision.

**Steps:**
- [x] Step 1: Map how global declarations, stage-specific declarations, defaults, fingerprints, and runner inputs are selected in direct and approved paths.
- [x] Step 2: Keep the workbook resolver responsible for declaration meaning only; make policy/recipe compilation and `validate_execution_recipe()` fail early when an approved deterministic stage lacks exactly one intended domain binding.
- [x] Step 3: Preserve direct global declarations and whole-contract stage shadowing without promoting every global declaration into every stage; assert the effective contract is used for layout, materialization, analyzer input, receipt identity, and fingerprints.
- [x] Step 4: Create a local correctness checkpoint commit only after policy, validation, approval, gate, stage-input, and runner tests pass.

**Verification:**
- [x] `python -m pytest -q tests/test_controller_selection.py tests/test_stage_inputs.py tests/test_approval_contract.py tests/test_execution_gate.py tests/test_workbook_engine.py tests/test_workbook_runner.py`
- Expected: valid global and stage-shadowing cases remain green, while missing/ambiguous approved stage bindings raise the intended deterministic error before workbook execution.

**Exit Criteria:**
- Direct and approved paths resolve the same effective contract, stage binding failures are explicit, and focused contract/workbook tests cover both supported and rejected forms.

### Task 3: Make changed-brief evidence materially different

**Purpose:**
- Upgrade the approved changed-brief workload so it proves different domain-consumed rows and analytical results rather than only different text fingerprints.

**Task Function:**
- Strengthen the optimization probe and its assertions around cross-brief consumed-domain/result identity, stale receipt rejection, and selective reuse.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded measurement-fixture change with moderate contract ambiguity and no production API redesign.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: probe tests and receipt comparison tests provide independent structural proof.

**Specification Coverage:**
- Consolidated verdict section 2; changed briefs must use different entity/material scopes and preserve source provenance.

**Required Skills:**
- `skill-backend-verification`, `skill-performance-optimization`

**Files And Symbols:**
- Inspect: `evaluation/probes/run_optimization_probe.py` changed-brief workload, `evaluation/probes/optimization_measurement.py` workload/result identity, `evaluation/probes/compare_optimization_receipts.py`, and `tests/test_optimization_measurement.py`
- Modify: the changed-brief fixture and assertions plus focused measurement tests
- Verify: same source SHA, different effective contract fingerprints, different consumed technology sets/calculation identities/result fingerprints, stale receipt rejection, and unaffected-stage reuse

**Dependencies:**
- Task 2 complete so the workload exercises the final stage/global binding semantics.

**Authority:**
- Preauthorized local actions: edit optimization fixtures/probes/tests and run bounded local measurements without changing production analytical ownership.
- Stop for: a fixture that cannot demonstrate distinct records/results, an alias being counted as a new workload, or any need to weaken stale-receipt checks.

**Steps:**
- [x] Step 1: Assert at startup that both `SiC Power Electronics` and `Zonal Architecture` exist in the fixture, then use those scopes with valid Technology Radar scenarios such as `Acceleration`, `Base`, or `Delay`; do not add an unused period dimension.
- [x] Step 2: Assert source SHA stability alongside distinct effective contract fingerprints, consumed technology sets, calculation IDs/values or hashes, recommendation/result fingerprints, and accepted result references/hashes; retain stale receipt rejection and unaffected-stage reuse assertions.
- [x] Step 3: Deduplicate `changed_brief`/`approved_changed_brief` and equivalent aliases in the evidence accounting, then update the comparison expectations.

**Verification:**
- [x] `python -m pytest -q tests/test_optimization_measurement.py`
- Expected: the changed-brief workload proves material divergence and the receipt comparison reports aliases once without lowering correctness checks.

**Exit Criteria:**
- Cross-brief evidence is materially distinct, reproducible on the unchanged fixture, and cannot pass by changing only objective/assumption text.

### Task 4: Split and decouple the optimization harness

**Purpose:**
- Provide smoke, targeted, and release profiles with explicit workload selection, stable harness identity, profile-specific validation, and lazy external-probe imports.

**Task Function:**
- Reduce investigation overhead and remove misleading duplicate evidence without changing analytical results.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: harness refactor is bounded but touches shared measurement contracts and needs sequential integration after the workload fix.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: harness tests, CLI help, and a smoke run are sufficient before release measurements.

**Specification Coverage:**
- Consolidated verdict sections 4-6 and 14; local workbook profiling must not import agent/MCP-only dependencies unless the selected workload needs them.

**Required Skills:**
- `skill-performance-optimization`

**Files And Symbols:**
- Inspect: `evaluation/probes/optimization_measurement.py`, `evaluation/probes/run_optimization_probe.py`, `evaluation/probes/compare_optimization_receipts.py`, probe imports, and measurement serialization
- Modify: profile/workload dispatch, profile evidence matrix, receipt validation, alias normalization, and lazy imports; update `tests/test_optimization_measurement.py` and `evaluation/README.md` when the changed harness contract requires it
- Verify: `--profile smoke|targeted|release`, `--workloads`, profile/workload/profile-schema/harness identity, baseline/candidate profile matching, release eligibility, and transitive provider-free importability

**Dependencies:**
- Task 3 complete; changed-brief names and identity semantics are now canonical.

**Authority:**
- Preauthorized local actions: edit evaluation harness/probe code, measurement tests, and maintained evaluation guidance; run smoke and targeted local profiles and create an instrumentation checkpoint commit after proof passes.
- Stop for: changing production runtime contracts merely to satisfy the harness, eager imports of optional providers, or publishing a release result before the manifest task.

**Steps:**
- [x] Step 1: Define one profile evidence matrix consumed by dispatch, receipt validation, and comparison: smoke proves correctness only, targeted proves explicitly selected paths, and release alone can produce a release-qualified verdict with required workbook, pattern, soak, and policy evidence.
- [x] Step 2: Record profile, canonical workload set, profile schema/version, harness digest, repository revision, and environment facts in every receipt; reject baseline/candidate profile mismatches and deduplicate aliases before aggregation.
- [x] Step 3: Move direct and transitive agent/MCP/provider imports behind selected-workload boundaries; prove in a fresh subprocess with an import blocker that the workbook-only smoke profile neither imports nor initializes those runtimes.
- [x] Step 4: Create a local instrumentation checkpoint commit only after profile-specific validation, transitive import checks, and smoke/targeted tests pass; do not label either profile release-qualified.

**Verification:**
- [x] `python -m pytest -q tests/test_optimization_measurement.py` plus harness help, smoke, targeted, and fresh-subprocess import-blocker commands
- Expected: profiles select only their declared workloads, receipts carry stable identity metadata, mismatched profiles are rejected, smoke/targeted results are not release-qualified, aliases count once, and the smoke path imports without external runtime dependencies.

**Exit Criteria:**
- The harness is faster for local iteration, explicit about what ran, structurally incapable of double-counting aliases or requiring unavailable providers for workbook-only work, and only release receipts can satisfy release acceptance.

### Task 5: Measure selected-sheet scaling

**Purpose:**
- Replace the single fixed XLSX stress point with a bounded scaling experiment that distinguishes selected-sheet work from unrelated workbook size.

**Task Function:**
- Generate representative workbook cases and capture parsing, allocation, memory, timing, result, and provenance evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: measurement design is explicit and bounded; no parser rewrite is justified before data exists.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic generated fixtures and workbook-engine tests provide reproducible validation.

**Specification Coverage:**
- Consolidated verdict section 7; preserve the existing XLSX reader and test selected extraction boundaries rather than inventing a custom parser.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/local_toolbelt.py:_preflight_xlsx_archive`, `spreadsheet_read`, `WorkbookContext`, and `WorkbookStats`; also inspect higher-level material construction in `src/foresight_os/analysis/workbook_inputs.py` and `src/foresight_os/analysis/workbook_engine.py`
- Modify: generated workload construction, measurement serialization, and focused workbook/measurement tests
- Verify: cases `8x128`, `24x512`, and `48x2048`, with selected-sheet versus unselected-sheet controls

**Dependencies:**
- Task 4 complete so the scaling workload can be selected independently and receipt metadata is stable.

**Authority:**
- Preauthorized local actions: edit bounded measurement fixtures/probes/tests and write ephemeral profiling outputs under the new run namespace.
- Stop for: evidence that requires a custom XLSX parser, a new cache, unbounded generated files, or changing production parsing limits without an approved threshold.

**Steps:**
- [x] Step 1: Generate deterministic small, medium, and large workbook cases with the same selected logical sheet and controlled unrelated sheets/ranges.
- [x] Step 2: Run each generated workbook size in a fresh subprocess with a fixed warm-up/sample policy; record parse time, allocation counters, peak RSS or equivalent memory evidence, result identity, provenance identity, fixture parameters, and environment metadata.
- [x] Step 3: Compare scaling and selected/unselected controls; defer parser or cache work unless a reproducible regression crosses an explicitly recorded decision threshold.

**Verification:**
- [x] Run the selected-sheet scaling workload through the targeted profile and `python -m pytest -q tests/test_workbook_engine.py tests/test_optimization_measurement.py`
- Expected: all three cases complete deterministically, selected data remains correct, provenance remains intact, and resource measurements are comparable across cases.

**Exit Criteria:**
- The repository contains reproducible selected-sheet scaling evidence and a documented decision to optimize or defer the XLSX path based on measured behavior.

### Task 6: Gate persistence optimization on phase measurements

**Purpose:**
- Measure cancellation snapshot cost, history growth, and stage-receipt persistence before making at most one narrowly justified persistence optimization.

**Task Function:**
- Instrument and compare dominant persistence phases while preserving atomic writes, recovery, invalidation, and receipt semantics.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: high-risk backend/persistence measurement with a strict no-rewrite guardrail.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct store tests plus end-to-end receipt/recovery probes cover side effects and rollback behavior.

**Specification Coverage:**
- Consolidated verdict sections 8-10; retain PR #41's revert-on-regression rule and make a candidate eligible only when its projected end-to-end benefit is distinguishable from noise on the relevant history workload.

**Required Skills:**
- `skill-backend-verification`, `skill-performance-optimization`

**Files And Symbols:**
- Inspect: `src/foresight_os/persistence/analysis_store.py` snapshot/commit/receipt methods, `tests/test_recovery.py`, result-committer tests, and persistence measurement helpers
- Modify: phase instrumentation, bounded workload generation, and at most one evidence-backed store optimization
- Verify: histories `10/100`, receipts `10/50/100`, cancellation snapshots, accepted/rejected revisions, and stale receipt rejection

**Dependencies:**
- Tasks 1 and 4 complete; token recovery and measurement identity must be stable before comparing persistence phases. Task 5 is an independent measurement lane.

**Authority:**
- Preauthorized local actions: add bounded instrumentation and tests, run persistence measurements, create an instrumentation-baseline checkpoint, and implement at most one reversible optimization only when the material-impact gate passes.
- Stop for: a general persistence rewrite, a second state owner, failed atomicity/recovery proof, an improvement indistinguishable from noise, or a candidate that is not relevant to the real history workload.

**Steps:**
- [x] Step 1: Measure serialization, file I/O, locking, hashing, snapshot capture/restore, and receipt handling separately at histories `10/100` and receipts `10/50/100`, including cancellation, final state, invalidation, rollback/idempotency, and representative operation traces.
- [x] Step 2: Create an instrumentation-only checkpoint, repeat the baseline from that exact immutable commit, freeze the baseline receipt and manifest metadata, and state the targeted path's noise floor and minimum retained end-to-end improvement.
- [x] Step 3: Apply no optimization when no phase is statistically distinguishable or no plausible reduction projects to material end-to-end benefit; otherwise create one candidate checkpoint, measure it against the frozen baseline, and retain the candidate only if correctness and the material-impact gate pass.

**Verification:**
- [x] Run focused persistence/recovery tests and the targeted persistence workload; compare baseline and candidate receipts from their immutable checkpoint commits against the measured noise floor and projected end-to-end benefit.
- Expected: correctness and provenance are unchanged; any optimization is supported by a material measured benefit on the relevant path, otherwise the plan records a measured deferral.

**Exit Criteria:**
- Persistence evidence identifies a bounded optimization target or proves that no change is justified, with recovery, invalidation, and receipt behavior still green.

### Task 7: Qualify release and publish immutable measurement evidence

**Purpose:**
- Run the complete release profile after both measurement lanes, then make optimization results reusable and auditable without confusing mutable worktree state with evidence.

**Task Function:**
- Produce the release-qualified manifest and reconcile maintained evaluation guidance with the actual harness and measurement contracts.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final release qualification and evidence packaging after both measured producer lanes are complete.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: JSON/schema checks, link checks, and manifest hash inspection provide direct proof.

**Specification Coverage:**
- Consolidated verdict section 11; release evidence must retain immutable revision, profile, workload, command, environment, status, and output identity facts.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `evaluation/README.md`, `docs/evidence-and-evaluation.md`, probe receipt schemas, and existing optimization evidence conventions
- Modify: `work/optimization-runs/consolidated-verdict-reviewed/manifest.json` plus the two maintained guidance files and any manifest validation test
- Verify: the complete release profile, final accepted/reverted head, manifest completeness, deterministic ordering, output hashes, durable references, blocked/failed statuses, and absence of secrets or raw provider payloads

**Dependencies:**
- Tasks 5-6 complete; the release run must use the final accepted/reverted head represented by the candidate comparison and must describe actual measured outputs, not planned commands.

**Authority:**
- Preauthorized local actions: create the final release checkpoint commit after verified candidate acceptance or reversion, run the complete release profile, write the compact manifest, update maintained evaluation documentation, and run JSON/link/whitespace checks.
- Stop for: external publication, replacing source-of-truth receipts with prose, or adding mutable claims that cannot be tied to an immutable run identity.

**Steps:**
- [ ] Step 1: Run the full release profile from the final accepted/reverted checkpoint and reject any smoke/targeted receipt as release-qualified evidence.
- [ ] Step 2: Define and populate manifest fields for base/head revision, harness digest, profile/schema, canonical workload set, commands, environment, status, and output hashes; reference only committed bounded artifacts, retained CI artifacts with IDs and hashes, durable repository-relative files, or truthful unavailable outcomes.
- [ ] Step 3: Update `evaluation/README.md` and `docs/evidence-and-evaluation.md` to explain release eligibility, baseline/candidate provenance, and reproduction without duplicating runtime contracts.

**Verification:**
- [ ] Run the complete release profile, the manifest/schema checks, `python scripts/check_markdown_links.py README.md AGENTS.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`, and `git diff --check`
- Expected: release eligibility passes only for the release profile, maintained links pass, the manifest parses and references only durable artifacts or truthful unavailable outcomes, and no credentials/raw payloads are persisted.

**Exit Criteria:**
- The final release profile and compact immutable manifest identify exactly what ran, what was measured, what was deferred, and how the results were verified against immutable checkpoint commits.

## Execution Ledger

- `5b652e3` is the Task 1 correctness checkpoint for revision-scoped pending-token restoration.
- `8668c2a` is the instrumentation checkpoint for Tasks 3-6. It includes the changed-brief identity assertions, profile-aware harness, lazy optional imports, selected-sheet scaling, and persistence phase probe.
- Smoke and targeted receipts are iteration evidence only. The release receipt from `8668c2a` passed the complete release workload set; a final release rerun after documentation/manifest changes remains required for Task 7.
- The persistence candidate is deferred: receipt writes and snapshot restore are measurable, but no implementation candidate was tested because the plan's material end-to-end benefit gate was not met by evidence available before release packaging.
- The requested `tests/test_technology_radar.py` path does not exist in this repository; the actual technology/workbook coverage is `tests/test_technology_powerbi_validator.py` plus the workbook and analysis-contract suites.
- The release probe emitted non-fatal Agent Framework handoff warnings for the synthetic `participant-2` path; the receipt still completed with `VERIFIED` status and no provider payload was persisted.

## Separate Maintenance Follow-Up

`NormalizedIntent` consumer cleanup, `pandas` removal proof, optional
`agent-framework` packaging, and clean-wheel compatibility are intentionally
outside this delivery. They require a separate maintenance plan and their own
baseline, candidate, and packaging evidence so they cannot make this
measurement manifest stale.

## Verification

- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- `git diff --check`
- Targeted smoke, selected-sheet scaling, cancellation, and persistence workloads with their manifest entries

## Completion Criteria

The plan is ready for completion verification when:

1. all seven task-local outcomes and proofs are complete or explicitly recorded as measured deferrals
2. revision-scoped token restoration and stage/global workbook binding are covered by focused regression tests
3. changed-brief evidence proves distinct material workbook behavior and alias accounting is deduplicated
4. optimization profiles, scaling measurements, persistence phase evidence, and the immutable manifest are reproducible
5. at most one persistence candidate is retained, or its measured deferral is recorded, and the final release profile runs from the final accepted/reverted checkpoint
6. full tests, compile checks, Markdown-link checks, and whitespace validation pass from the clean worktree
7. deviations, blockers, deferrals, base revision, checkpoint commits, and durable evidence references are recorded in this plan and the manifest

The plan remains `proposed` until a human authorizes execution. It must not be
marked completed merely because the document is saved; completion requires
fresh implementation evidence and `skill-verification-before-completion`.

