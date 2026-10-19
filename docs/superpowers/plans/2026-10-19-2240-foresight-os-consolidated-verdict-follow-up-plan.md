---
layer: change
artifact_type: plan
status: active
template_id: implementation-plan
contract_version: "1"
name: foresight-os-consolidated-verdict-follow-up
targets:
  - src/foresight_os/domain/analysis_inputs.py
  - src/foresight_os/domain/validation.py
  - src/foresight_os/analysis/workbook_inputs.py
  - src/foresight_os/analysis/workbook_engine.py
  - src/foresight_os/analysis/workbook_runner.py
  - src/foresight_os/analysis/workbook_registry.py
  - src/foresight_os/controller/policy.py
  - src/foresight_os/controller/recipes.py
  - src/foresight_os/runtime/execution_gate.py
  - src/foresight_os/runtime/capabilities.py
  - src/foresight_os/runtime/external_signals.py
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/persistence/analysis_store.py
  - evaluation/probes/optimization_measurement.py
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/compare_optimization_receipts.py
  - tests/
  - docs/architecture.md
  - docs/evidence-and-evaluation.md
  - work/optimization-runs/
---

# ForesightOS Consolidated Verdict Follow-Up

## Review Of The Recommendation

The supplied verdict is directionally correct and has the right delivery
sequence: contract correctness first, trustworthy measurement second, and
persistence optimization only after a clean measured checkpoint. The material
amendment is correct and must be treated as P0 rather than as cleanup.

Source review against `origin/main` at `5ae8069543ad55f82e451f56554ca09b0435c61f` confirms:

- `AnalysisInputDeclaration` preserves sparse values, but `from_dict()` does
  not canonicalize legacy aliases before defaults are merged. `from_dict()` on
  `AnalysisInputContract` accepts aliases, while declaration resolution and
  workbook default merging can still give canonical fields precedence over the
  authored sparse alias.
- `normalize_work_brief()` keeps declarations for persistence but also creates
  generic typed contracts for validation and fingerprinting. This creates two
  possible identity inputs before the domain resolver runs.
- `resolve_workbook_contract()` has an incomplete empty-table compatibility
  exception, and both `WorkbookWorkflowRunner.run()` and
  `WorkbookAnalysisEngine.run()` call the resolver. An explicit empty
  `required_tables` can therefore be treated as omission on a later pass.
- PR #40 already added source-tree identity, mandatory scenario names, and
  timing-path comparison fields. The next change must not recreate those
  surfaces blindly. It must make the `changed_brief` workload exercise the
  approved execution path and make `selected_sheet_stress` a real generated
  unrelated-sheet workload; the current probe aliases it to
  `different_selection` when constructing timing evidence.
- `AnalysisStore` still performs full-state loading, validation, hydration,
  merge, and atomic writes inside commit paths, and pending-token history is a
  credible growth cost. These are optimization candidates, not conclusions;
  history-10 and history-100 evidence must establish the dominant phase first.
- Capability admission is already intended to be lazy. The follow-up should
  preserve and test that boundary, not add a provider-plan abstraction.

The revised plan makes four execution decisions explicit:

- verified local checkpoint commits are allowed so clean baseline/candidate
  provenance is immutable;
- stage-specific declarations shadow global declarations for the same domain;
  there is no field-level overlay, and the global declaration is used only when
  no stage-specific declaration exists;
- semantically equivalent persisted approvals remain compatible through the
  existing compatibility path, while a materially changed effective contract
  requires the existing reapproval/invalidation behavior; and
- persistence instrumentation and history measurement are mandatory, while a
  persistence optimization candidate is conditional on measured benefit.

The local checkout is `main` at `bd5abc1335d6454f89703a00243051bd5b2fff40`,
behind the reviewed `origin/main`, and contains unrelated dirty changes. This
plan therefore assumes execution from a clean worktree based on the reviewed
origin commit; the current workspace must be preserved, not reset.

## Goal

Make sparse workbook declarations semantically exact and durably canonical,
resolve one immutable effective contract exactly once for direct and approved
execution, repair the optimization evidence so it proves the real workflows,
and optimize persistence only when history measurements identify a safe,
material bottleneck. Keep XLSX reader changes and dependency cleanup explicitly
conditional or separate.

## Implementation Outcomes

### One canonical contract boundary

Legacy aliases are normalized before defaults are applied. Conflicting alias
and canonical values fail validation. Explicit empty values remain explicit.
Planning, approval, materialization, analyzer execution, receipt reuse, and
review provenance use the same effective stage/domain contract fingerprint.

### Honest release evidence

The measurement harness records a real approved changed-brief workload, a real
selected-sheet stress workload, distinct history-10 and history-100 workloads,
path-specific timing noise floors, clean source identity, fixture identity,
and bounded manifests that point to raw artifacts without copying them into
the repository.

### Measured persistence improvement or a justified deferral

Persistence phases are separately observable. Any retained optimization keeps
file locking, atomic writes, stale revision rejection, cancellation recovery,
bounded revision-scoped token state, idempotency, and replay protection. If no
material safe improvement is demonstrated, the candidate is deferred with
fresh evidence rather than merged speculatively.

### Explicit non-goals remain protected

No workbook cache, second persistence store, transaction journal, custom XLSX
parser, provider-plan abstraction, executor layer, or dependency migration is
introduced by this plan.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `dedicated clean worktree from origin/main; preserve the current dirty workspace`
- Commit policy: `verified local checkpoint commits are allowed; no push, PR, merge, branch deletion, or cleanup during execution`
- Preauthorized local actions: `edit the declared files, add focused tests and bounded generated measurement fixtures, run declared local checks, and record bounded evidence under work/optimization-runs/`
- User-approval actions: `push, merge, publication, destructive cleanup, resetting the current dirty workspace, or changing dependency declarations`
- Parallel ownership: `none; contract identity, evidence protocol, and persistence optimization are dependency-ordered`
- Sequential fallback: `Task 1 -> Task 2 -> Task 3 verified checkpoint -> Task 4 instrumentation checkpoint and mandatory history measurement -> conditional Task 4 candidate -> conditional Task 5`

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/foresight-os-consolidated-verdict-follow-up`
- Base commit: `5ae8069543ad55f82e451f56554ca09b0435c61f`
- Expected workspace: `clean execution worktree from base; current main dirty changes preserved separately`
- Next action: `Task 4 persistence instrumentation and mandatory history measurement`
- Blockers: `none; current workspace is not a safe execution workspace until isolated`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | dedicated clean worktree | `lead controller` | none | focused contract tests | `tests/test_analysis_input_contract.py`, `tests/test_work_brief_compatibility.py`, `tests/test_analysis_schema.py` pass |
| Task 2 | `completed` | dedicated clean worktree | `lead controller` | Task 1 | identity, approval, and capability boundary proof | focused Task 2 suite passes; persisted alias admission and material-change rejection pass |
| Task 3 | `completed` | dedicated clean worktree | `lead controller` | Task 2 | verified benchmark checkpoint | `20a3503`; clean baseline receipt: `work/optimization-runs/task3-final2/baseline.json` |
| Task 4 | `active` | dedicated clean worktree | `lead controller` | Task 3 | instrumentation checkpoint, history proof, conditional candidate | pending |
| Task 5 | `pending` | dedicated clean worktree | `lead controller` | Task 3 | reader parity and resource evidence, or explicit deferral | pending |

## Task Breakdown

### Task 1: Canonicalize sparse declarations before defaults

**Purpose:**
- Make declaration field presence and alias meaning authoritative before any
  domain defaults or typed contract construction occurs.

**Task Function:**
- Extend the existing declaration boundary without creating a second schema or
  validation framework.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `high correctness risk, bounded source surface, and direct testability`

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: `focused contract and validation tests`

**Specification Coverage:**
- Canonicalize `tables`, `entities`, `currency`, and
  `validation_checks` to `required_tables`, `entity_scope`,
  `reporting_currency`, and `required_validation_checks` before defaults.
- Reject conflicting alias/canonical pairs instead of selecting implicitly.
- Preserve omitted versus explicit empty for all fields that affect workbook
  selection, filtering, units, currency, periods, scenarios, calculations, and
  checks.
- Keep serialized durable WorkBrief input sparse and round-trippable.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/domain/analysis_inputs.py:AnalysisInputDeclaration.from_dict`
- Inspect only unless a failing test proves it necessary: `AnalysisInputContract.from_dict`, `AnalysisInputContract.to_dict`
- Inspect/modify: `src/foresight_os/domain/validation.py:_normalize_work_brief`
- Verify: `tests/test_analysis_input_contract.py`, `tests/test_work_brief_compatibility.py`, `tests/test_analysis_schema.py`

**Dependencies:**
- Base `origin/main` commit recorded in Coordination State.

**Authority:**
- Preauthorized local actions: `edit declaration normalization and focused contract-validation tests`
- Stop for: `changing public WorkBrief schema names, losing sparse field presence, or introducing a parallel contract representation`

**Steps:**
- [x] Step 1: Enumerate every accepted alias, including the existing
  `name -> domain` compatibility fallback, and define one canonical mapping at
  the sparse declaration boundary. If `name` is deprecated instead, add an
  explicit compatibility test and documented removal decision.
- [x] Step 2: Add conflict detection for alias/canonical pairs, including
  unequal values and explicit empty versus non-empty values.
- [x] Step 3: Ensure declaration serialization does not materialize domain
  defaults and that validation can inspect fields without changing them.
- [x] Step 4: Add tests for omission, explicit empty, alias-only, canonical-only,
  equivalent duplicate forms, conflicting forms, canonical persisted
  declaration output, and equal effective contract fingerprints for equivalent
  declarations. Do not add a separate declaration fingerprint unless a
  source-backed requirement appears.

**Verification:**
- [x] `python -m pytest -q tests/test_analysis_input_contract.py tests/test_work_brief_compatibility.py tests/test_analysis_schema.py`
- Expected: sparse declarations remain sparse, conflicts fail closed, and
  canonical fingerprints are stable across equivalent input forms.

**Exit Criteria:**
- There is one tested sparse declaration normalization boundary and no alias
  ambiguity remains before domain defaults are merged.

### Task 2: Resolve one effective contract and identity

**Purpose:**
- Remove repeated inference from the runner and engine and make one immutable
  effective contract authoritative for the whole workbook path.

**Task Function:**
- Reconcile declaration, planning, approval, materialization, analyzer, and
  receipt identity around the existing resolver and stage/domain ownership.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `cross-layer correctness change with receipt and approval impact`

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: `direct/approved parity and stale-reuse tests`

**Specification Coverage:**
- Compatibility/public callers may supply mappings or declarations once.
- `resolve_workbook_contract()` produces the immutable effective contract.
- `WorkbookWorkflowRunner` and `WorkbookAnalysisEngine` consume the effective
  contract without re-resolving it.
- A stage-specific declaration shadows the global declaration for the same
  domain; there is no field-level overlay. The global declaration is used only
  when no stage-specific declaration exists. An explicit empty `required_tables`
  remains empty and does not fall back to domain defaults.
- The effective contract fingerprint is the identity used by execution,
  material selection, analyzer output, stage receipts, and review provenance.
- Recipe construction uses the same effective contract identity rather than a
  separate generic contract fingerprint.
- Existing valid persisted approvals remain compatible when canonicalization is
  semantically equivalent. A materially changed effective contract follows the
  existing invalidation/reapproval path; it must not silently execute under an
  old approval.
- Capability admission remains metadata-only; activation creates each resource
  once and settlement closes it once across success, failure, cancellation, and
  retry.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/analysis/workbook_inputs.py:resolve_workbook_contract`
- Inspect/modify: `src/foresight_os/analysis/workbook_runner.py:WorkbookWorkflowRunner.run`
- Inspect/modify: `src/foresight_os/analysis/workbook_engine.py:WorkbookAnalysisEngine.run`
- Inspect/modify: `src/foresight_os/runtime/execution_gate.py:effective contract construction`
- Inspect/modify: `src/foresight_os/domain/analysis_inputs.py:NormalizedIntent`, `src/foresight_os/controller/policy.py`, `src/foresight_os/controller/recipes.py`
- Inspect: `src/foresight_os/runtime/capabilities.py:prepare_capability_context`, `src/foresight_os/runtime/external_signals.py:load_hosted_mcp_bindings`
- Verify: `tests/test_analysis_input_contract.py`, `tests/test_workbook_runner.py`, `tests/test_workbook_engine.py`, `tests/test_execution_gate.py`, `tests/test_brief_portability.py`, `tests/test_stage_inputs.py`, `tests/test_approval_persistence.py`, `tests/test_capabilities.py`, `tests/test_external_signals.py`, `tests/test_runtime_boundaries.py`

**Dependencies:**
- Task 1 complete and focused tests passing.

**Authority:**
- Preauthorized local actions: `edit the existing resolver boundary, policy/recipe identity plumbing, approval compatibility tests, capability guardrail tests, and focused parity tests`
- Stop for: `changing persisted approval compatibility policy, receipt schema, or public contract shape without recording the explicit migration decision in this plan`

**Steps:**
- [x] Step 1: Make `NormalizedIntent` retain declarations as the authoritative
  input while deriving effective contracts by stage/domain.
- [x] Step 2: Move compatibility resolution to one boundary and remove
  internal second-pass resolution, retaining only a narrow public compatibility
  helper where required by existing callers.
- [x] Step 3: Update controller policy and recipe construction so planning,
  recipe-stage identity, approved execution, materialization, analyzer output,
  stage receipts, and review provenance use the same effective fingerprint.
- [x] Step 4: Preserve the explicit shadow rule for stage/global declarations,
  including empty stage-specific values.
- [x] Step 5: Verify direct, persisted, and approved execution produce the same
  effective fingerprint, selected material, source identity, and result identity.
- [x] Step 6: Test approval compatibility: equivalent canonicalization keeps a
  valid persisted approval usable, while a material effective-contract change
  requires invalidation or reapproval.
- [x] Step 7: Add capability admission/activation lifecycle tests covering
  metadata-only admission, one activation, one settlement, unavailable
  resources, failure, cancellation, and retry.

**Verification:**
- [x] `python -m pytest -q tests/test_analysis_input_contract.py tests/test_workbook_runner.py tests/test_workbook_engine.py tests/test_execution_gate.py tests/test_brief_portability.py tests/test_stage_inputs.py tests/test_approval_persistence.py tests/test_capabilities.py tests/test_external_signals.py tests/test_runtime_boundaries.py`
- Expected: one effective contract reaches materialization and analysis; direct
  and approved paths agree; invalidated receipts are not reused; approval
  compatibility and lazy capability lifecycle behavior are proven.

**Exit Criteria:**
- The code has one internal effective-contract boundary and tests prove that
  explicit empties, stage shadowing, approval compatibility, and capability
  lifecycle behavior cannot be changed by later layers.

### Task 3: Repair benchmark truth and establish a clean checkpoint

**Purpose:**
- Make release evidence represent the actual approved workflow and the actual
  selected-sheet stress case before any persistence candidate is evaluated.

**Task Function:**
- Extend the existing measurement protocol, receipt schema, and comparator with
  bounded, source-identifiable scenarios and path-specific gates.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `high measurement risk and explicit performance evidence requirement`

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: `receipt contract tests and clean baseline/release comparison`

**Specification Coverage:**
- `approved_changed_brief` executes Brief A through WorkBrief persistence,
  recipe selection, approval, execution admission, stage receipt/result, then
  Brief B with material scope/stage change on the same workbook.
- The workload proves source identity stability, changed effective contract
  fingerprints, stale receipt rejection, valid unaffected-stage reuse, stage
  override precedence, and sparse-default parity.
- `selected_sheet_stress` generates many large unrelated sheets and one small
  selected sheet, measures archive sheets enumerated, worksheet XML parsed,
  selected rows/cells, openpyxl loads, cold latency, allocation/RSS, and result
  fingerprint, and asserts parsed worksheet XML equals selected-sheet count.
- `history-10` and `history-100` are distinct generated workloads; history-1000
  is bounded stress evidence, not a mandatory release gate.
- Every timing path has repeated samples and its own empirical absolute noise
  floor in addition to relative regression thresholds. Before any candidate
  run, freeze the estimator as `max(0, p95(baseline_samples) -
  median(baseline_samples))` using at least ten baseline samples per path;
  candidate variance is recorded separately and cannot raise the threshold.
- One compact manifest binds baseline/candidate commits, harness digest,
  fixture/workload hashes, environment identity, clean state, and raw artifact
  references.

**Required Skills:**
- `skill-performance-optimization`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `evaluation/probes/run_optimization_probe.py:_changed_brief_workload`, history workloads, selected-sheet stress workload, receipt assembly
- Inspect/modify: `evaluation/probes/optimization_measurement.py:workload/status/manifest schema`
- Inspect/modify: `evaluation/probes/compare_optimization_receipts.py:required paths, noise floors, gate comparison`
- Verify: `tests/test_optimization_measurement.py`, `docs/evidence-and-evaluation.md`, `evaluation/README.md`
- Record bounded evidence: `work/optimization-runs/<checkpoint>/manifest.json` and summary/comparison files; do not commit giant raw timing samples

**Dependencies:**
- Task 2 complete and the effective contract identity is stable.

**Authority:**
- Preauthorized local actions: `edit local probes, comparator tests, maintained evidence guidance, and bounded generated manifests`
- Stop for: `using a dirty tree, mismatched fixture/harness identities, aliasing selected-sheet stress to another workload, or claiming an optimization from NOT_MEASURED evidence`

**Steps:**
- [ ] Step 1: Freeze the workload definitions and receipt schema before running
  baseline/candidate comparisons.
- [ ] Step 2: Replace the direct changed-contract probe with the full approved
  changed-brief path while keeping the existing context-reuse workload distinct.
- [ ] Step 3: Generate the selected-sheet stress fixture at runtime and record
  archive-wide safety counters separately from selected worksheet parsing.
- [ ] Step 4: Add at least ten baseline samples per timing path and freeze the
  baseline-derived estimator `max(0, p95 - median)` before any candidate run;
  keep candidate variance diagnostic-only.
- [ ] Step 5: Require the core scenarios to be `VERIFIED`, not merely limited:
  `approved_changed_brief`, `history-10`, `history-100`, and
  `selected_sheet_stress`.
- [ ] Step 6: Create a verified local checkpoint commit containing the repaired
  workload/comparator protocol and use that commit for the persistence phase.

**Verification:**
- [ ] `python -m pytest -q tests/test_optimization_measurement.py`
- [ ] Run baseline and release probes from clean source-identified worktrees
  using `tests/fixtures/analyst_multisheet.xlsx` and compare their receipts.
- Expected: `approved_changed_brief`, `history-10`, `history-100`, and the real
  selected-sheet stress workload are all `VERIFIED`; a precise limitation is a
  recorded blocked outcome and cannot authorize persistence optimization. No
  receipt can pass with mismatched source or harness identity.

**Exit Criteria:**
- A fresh verified checkpoint commit exists with reproducible workload
  definitions, baseline-derived path-specific gates, all core scenarios
  verified, and no unresolved evidence mismatch.

### Task 4: Instrument, measure, and conditionally optimize full-state persistence

**Purpose:**
- Reduce measured history-size cost without weakening durable analysis lifecycle
  or rollback semantics.

**Task Function:**
- Always instrument and measure first; apply the smallest safe optimization to
  the dominant phase only when the measured benefit gate opens, otherwise record
  a justified deferral.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `material persistence behavior with high correctness and recovery risk`

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: `persistence boundary, cancellation, replay, and history evidence`

**Specification Coverage:**
- Measure lock wait, raw read, JSON decode, schema/domain validation, hydration,
  merge, serialization, write, and fsync separately.
- Prefer one read per persisted JSON, early stale rejection from raw identity,
  one hydration/merge, one final validation, and the existing atomic write.
- Preserve revision-scoped bounded pending-token state through cancellation and
  snapshot restoration; never restore the legacy bare token-array form.
- Preserve stale pending rejection, replay protection, idempotency, rollback,
  failure classification, and lock ownership.
- Do not add a database, append journal, metadata index, background compactor,
  or second persistence owner.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/persistence/analysis_store.py:commit_revision`, `_load_path`, `save_pending_if_unchanged`, `capture_revision_snapshot`, `restore_revision_snapshot`, consumed-token helpers
- Verify: `tests/test_persistence.py`, `tests/test_recovery.py`, `tests/test_invalidation.py`, `tests/test_approval_persistence.py`, `tests/test_execution_gate.py`
- Extend measurement: `evaluation/probes/run_optimization_probe.py:history-10/history-100`, `evaluation/probes/optimization_measurement.py`

**Dependencies:**
- Task 3 core scenarios are verified and its local checkpoint commit is clean.

**Authority:**
- Preauthorized local actions: `instrument persistence, create a verified local instrumentation checkpoint, add focused recovery tests, and implement one measured candidate within the existing store`
- Stop for: `missing phase evidence, changed rollback/replay semantics, introducing a second store/journal, or a candidate without material improvement`

**Steps:**
- [ ] Step 1: Add phase metrics without changing persistence semantics and
  verify lock wait, raw read, JSON decode, validation, hydration, merge,
  serialization, write, and fsync measurements.
- [ ] Step 2: Run focused persistence/recovery tests and create a verified local
  instrumentation-only checkpoint commit. Measure history-10/history-100 and
  cancellation snapshot cost from that same instrumented commit.
- [ ] Step 3: Identify the dominant phase and define the candidate's expected
  invariant and minimum measurable improvement before editing it. Instrumented
  baseline and candidate must share the same harness and schema.
- [ ] Step 4: Implement only the smallest candidate justified by the phase data.
- [ ] Step 5: Add pending -> cancellation -> restoration -> new pending ->
  acceptance -> old-token replay regression coverage across revisions.
- [ ] Step 6: Re-run the exact frozen checkpoint workloads and retain the
  candidate only if correctness, recovery, and path-specific performance gates
  all pass. Otherwise keep instrumentation and record the candidate as deferred.

**Verification:**
- [ ] `python -m pytest -q tests/test_persistence.py tests/test_recovery.py tests/test_invalidation.py tests/test_approval_persistence.py tests/test_execution_gate.py`
- [ ] Run matching history-10/history-100 baseline and candidate probes.
- Expected: all lifecycle tests pass; token state remains bounded and
  revision-scoped; any accepted candidate improves a measured phase without
  regressions, otherwise the candidate is explicitly deferred.

**Exit Criteria:**
- Persistence measurement is always complete and reproducible. The optimization
  candidate is retained only when a dominant phase and minimum benefit are
  demonstrated; otherwise the instrumented store remains unchanged and the
  candidate is explicitly deferred.

### Task 5: Make XLSX reader work conditional on real stress evidence

**Purpose:**
- Prevent a speculative reader rewrite while keeping a safe path open if the
  real selected-sheet workload proves material scaling.

**Task Function:**
- Evaluate the existing selected-sheet preflight and eager reader against the
  Task 3 workload; implement a read-only candidate only if all gates open.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: `conditional performance work with high semantic parity risk`

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: `formula/cache, hidden-row, merged-cell, provenance, limit,
  cancellation, and selected-material parity`

**Specification Coverage:**
- Archive-wide safety checks remain intact even when excluded worksheets are
  not opened.
- A read-only path is not retained unless it materially improves cold latency,
  allocation, or RSS on the generated stress fixture.
- Formula and cached-value semantics, hidden rows, merged cells, provenance,
  limits, cancellation, and result fingerprints remain unchanged.
- No custom XLSX parser is introduced.

**Required Skills:**
- `skill-performance-optimization`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify only if evidence opens the gate: `src/foresight_os/runtime/local_toolbelt.py:_preflight_xlsx_archive`, selected reader path
- Verify: `tests/test_local_toolbelt.py`, `tests/test_workbook_engine.py`, `tests/test_workbook_path_parity.py`

**Dependencies:**
- Task 3 selected-sheet stress receipt.

**Authority:**
- Preauthorized local actions: `run the reader comparison and add parity tests; implement a bounded reader candidate only after the stated evidence gate`
- Stop for: `formula/cache, provenance, hidden-row, merged-cell, cancellation, or selected-result parity failure`

**Steps:**
- [ ] Step 1: Confirm `archive_sheet_xml_scanned == selected_sheet_count` for
  selected-sheet workloads while preserving archive-wide safety checks.
- [ ] Step 2: Compare eager and read-only candidates only if excluded-data
  growth materially affects measured resource or latency metrics.
- [ ] Step 3: Keep the eager reader and record the candidate as deferred when
  the benefit is not material or parity is incomplete.

**Verification:**
- [ ] `python -m pytest -q tests/test_local_toolbelt.py tests/test_workbook_engine.py tests/test_workbook_path_parity.py`
- Expected: selected material and provenance remain identical; reader work is
  reduced only when the evidence and parity gates justify it.

**Exit Criteria:**
- The reader decision is evidence-backed and documented; speculative parser
  work is not merged.

## Verification

Run from the clean execution worktree after selected tasks complete:

- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/getting-started.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- `git diff --check`
- Confirm both verified local checkpoint commits are present and
  source-identifiable: the Task 3 benchmark-protocol checkpoint and the Task 4
  instrumentation-only persistence checkpoint.
- baseline/release optimization probes and receipt comparison from clean,
  source-identified worktrees with matching fixture, harness, environment, and
  workload identities
- focused backend boundary traces for declaration resolution, approved
  execution, capability admission/activation, persistence settlement, snapshot
  restoration, and selected-sheet reads
- final inspection of changed paths, generated evidence, dirty-state flags,
  exact base/head SHAs, and explicit deferrals

## Completion Criteria

The plan is ready for completion verification when:

1. aliases are canonicalized before defaults and conflicting forms fail closed;
2. direct, persisted, and approved workbook execution share one effective
   contract identity and preserve explicit empties;
3. capability admission remains metadata-only and activation/settlement is
   run-owned and deterministic;
4. `approved_changed_brief`, `history-10`, `history-100`, and
   `selected_sheet_stress` each have fresh, source-identifiable evidence with
   status `VERIFIED`; a precise limitation blocks persistence optimization
   rather than satisfying this criterion;
5. persistence changes, if retained, preserve locking, rollback, recovery,
   idempotency, stale checks, and bounded revision-scoped token state;
6. XLSX reader changes are retained only with material resource benefit and
   complete semantic parity, otherwise explicitly deferred;
7. dependency cleanup remains outside this plan and has not been mixed into the
   correctness or persistence change set; and
8. all final verification commands pass with no unrecorded scope deviation.

The plan remains `proposed` until `skill-verification-before-completion`
returns `verified` for an executed implementation. Dependency cleanup remains
a separate maintenance plan covering clean-wheel installation, optional
agent-framework behavior, pandas consumer proof, and package import tests.

## Explicit Deferrals

- Do not add a workbook cache, reuse database, transaction journal, custom XLSX
  parser, provider-plan abstraction, executor layer, or second persistence owner.
- Do not make `agent-framework` optional or remove pandas in this change set.
- Do not claim a latency improvement from a comparison with mismatched source,
  fixture, harness, environment, or dirty-state identity.
- Do not make history-1000 a mandatory release gate; retain it only as bounded
  stress evidence when affordable.
- Do not optimize the XLSX reader until the real selected-sheet stress workload
  demonstrates material scaling and all parity tests are available.
