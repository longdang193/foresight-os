---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: foresight-os-closure-identity-performance
targets:
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/runtime/executors.py
  - src/foresight_os/runtime/participants.py
  - src/foresight_os/controller/budgets.py
  - src/foresight_os/controller/skills.py
  - src/foresight_os/analysis/reviewer.py
  - src/foresight_os/runtime/maf_probe.py
  - src/foresight_os/persistence/analysis_store.py
  - evaluation/probes/run_skill_exercise_evaluation.py
  - evaluation/probes/run_full_pipeline_exercise.py
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/compare_optimization_receipts.py
  - evaluation/probes/optimization_measurement.py
  - tests/test_skills.py
  - tests/test_selective_reuse.py
  - tests/test_group_chat.py
  - tests/test_maf_fit.py
  - tests/test_optimization_measurement.py
  - tests/test_skill_exercise_evaluation.py
  - tests/test_evaluation_contract.py
  - tests/test_runtime_boundaries.py
  - .github/workflows/ci.yml
  - .github/workflows/evidence.yml
  - evaluation/README.md
  - README.md
  - docs/superpowers/evidence/closure-identity-performance-receipt.json
  - docs/superpowers/plans/2026-10-13-1608-foresight-os-closure-release-plan.md
  - docs/superpowers/plans/2026-10-14-0021-foresight-os-skill-layer-hardening-plan.md
---

# Foresight OS Closure Identity and Performance Plan

## Goal

Close the remaining acceptance gaps after the three implementation increments
and merged PR #9 without expanding the architecture. Correct the canonical
stage/participant skill identity boundary, make selective reuse invalidate on
the complete effective skill plan, enforce declared Group Chat limits in native
MAF execution and shared budgets, and produce trustworthy frozen p95 evidence.

Keep the existing Controller, `AnalysisState`, `RelationIndex`, capability
resolver, native MAF patterns, deterministic data tools, `PresentationSpec`,
human approval boundary, and Canva ownership unchanged. This plan does not add
new orchestration layers, a second skill metadata source, a design database, or
provider-backed claims to deterministic evidence.

The source verdict is reviewed against merged `origin/main` at
`368f58e4fe2ce77d02023713f76adf2aac6622f1`. Its central conclusion is accepted:
implementation and skill hardening are delivered, but closure acceptance is
still incomplete. The current checkout contains preserved untracked outputs and
is not the execution base; implementation must start from a fresh worktree at
`origin/main`.

## Verdict Review

The following findings are justified and are converted into tasks below:

- **P0 — effective skill resolution:** `run_recipe_async` resolves only stage
  skills, then `dispatch_stage` attaches participant skill IDs to the config
  while passing the stage-only `selected_skills` tuple through the context.
  A participant with both stage and participant skills can therefore receive
  incomplete instructions and capabilities.
- **P0 — reuse identity:** `_stage_fingerprints` and `skill_hashes_by_stage`
  use only `stage.skill_ids`. A participant-only skill change can leave the
  cache key and receipt skill hashes unchanged, so the old result can be reused.
- **P0 — Group Chat budget:** `_run_native_stage` hard-codes
  `GroupChatBuilder(max_rounds=4)`, while stage limits are applied only to the
  shared `BudgetState`. The declared stage limit is not the native execution
  limit and is not proven against observed rounds.
- **P1 — evaluator truthfulness:** the merged evaluator runs real provider
  cases but classifies every exception as `BLOCKED_EXTERNAL`; code defects and
  provider unavailability are not separated. Structural/reference evidence
  must remain distinct from provider runtime and human rubric evidence.
- **P1 — provider configuration:** `load_provider_settings` requires an
  existing `.env` path and does not establish a clear inherited-environment
  path. Missing local files must not prevent an approved inherited provider
  configuration from running.
- **P1 — registry reuse:** production review and workflow paths still create
  `SkillRegistry` instances at multiple boundaries. Reuse the process/run
  registry without introducing global mutable state or removing the existing
  verified resolution cache.
- **P2 — operations:** deterministic PR checks should stay cheap; expensive
  optimization, soak, provider, and rendered-slide evidence belongs in
  scheduled/release tiers. Durable Git evidence should retain compact receipts,
  not raw console dumps.

The verdict is narrowed in two ways. First, the evaluator correction is an
existing-file repair on merged `origin/main`, not a new evaluation subsystem.
Second, Group Chat p95 must be stabilized and measured before any tuning; the
existing `20%` regression threshold is frozen and must not be relaxed. The
existing real XLSX/full-pipeline path remains in the evaluation strategy and
must not be replaced by CSV-only skill fixtures.

Canva remains a boundary, not a task: no connector authentication, publication,
export, or external mutation is part of this PR. A missing external Canva
connection remains an explicit `BLOCKED_EXTERNAL` receipt; local presentation
contracts and evidence are still verified independently.

## Implementation Outcomes

1. Every participant receives one ordered effective skill plan equal to the
   stable union of stage-level and participant-level skill IDs.
2. The same resolved plan drives instructions, required capabilities, semantic
   fingerprints, and `StageReceipt` validation.
3. Any participant-specific skill addition, removal, reorder, version, or
   content-hash change invalidates the prior stage receipt.
4. Native and fallback Group Chat execution honor one effective round limit and
   report observed rounds consistently through `BudgetState` and `RunMetrics`.
5. The evaluator reports `FAILED` for code/contract defects and
   `BLOCKED_EXTERNAL` only for unavailable approved provider boundaries.
6. Provider configuration can inherit approved process environment values when
   the optional env file is absent; secrets remain outside tracked files and
   report output.
7. A process/run-scoped `SkillRegistry` is reused at canonical callers while
   manifest/content hash validation remains intact.
8. Frozen baseline/release comparison proves Group Chat p95 at the existing
   threshold, with workload identity and environment recorded.
9. Plan status and evidence records distinguish delivered implementation,
   delivered skill hardening, and completed closure acceptance.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Isolation: fresh task-specific Git worktree created from `origin/main`; do not
  use the current checkout with preserved untracked outputs as the implementation
  workspace
- Required skills: `skill-writing-plans`, `skill-plan-document-reviewer`,
  `skill-using-git-worktrees`, `skill-executing-plans`,
  `skill-code-standards`, `skill-backend-verification`,
  `skill-performance-optimization`, `skill-verification-before-completion`
- Executor: `unresolved` until Planning Dispatch activates the plan; Codex is
  the default controller when no bounded delegated benefit is established
- Commit policy: verified checkpoint commits are allowed; push, PR creation,
  merge, provider calls, Canva writes, and external publication require separate
  authorization
- Parallel ownership: none; workflow identity, budget accounting, evaluator
  contracts, and benchmark evidence share canonical runtime assumptions
- Preserved artifacts: do not delete, clean, stage, or rewrite the current
  checkout's untracked `build/`, `data/`, `src/foresight_os.egg-info/`, or
  `work/` outputs

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Base commit: `368f58e4fe2ce77d02023713f76adf2aac6622f1` (`origin/main`)
- Execution branch: `codex/closure-identity-performance` created from the base
  commit only when execution is authorized
- Current plan state: proposed; when execution begins, the lead first tracks this
  plan on the execution branch and changes it to `active` before activating Task 0
- External boundaries: provider-backed evaluation, native MAF package behavior,
  rendered-slide quality, and Canva delivery require their declared approved
  environment; missing setup is recorded honestly, not simulated
- Stop conditions: changed `origin/main` base, unexpected tracked edits in the
  fresh worktree, a contract conflict with source/tests, a request to widen
  architecture, or any request to discard preserved artifacts

| Task | State | Executor | Depends On | Required Proof | Durable Evidence |
| --- | --- | --- | --- | --- | --- |
| 0. Reconcile merged main | completed | unresolved | none | exact base, source findings, clean isolated worktree | `work/closure-identity-performance/reconciliation/` |
| 1. Canonical effective skill plan | completed | unresolved | 0 | mixed stage/participant instructions and capability test | `work/closure-identity-performance/task-1/` |
| 2. Receipt and fingerprint identity | completed | unresolved | 1 | participant-only skill change misses reuse | `work/closure-identity-performance/task-2/` |
| 3. Group Chat round/budget contract | completed | unresolved | 1 | native/fallback declared-versus-observed round proof | `work/closure-identity-performance/task-3/` |
| 4. Evaluator/provider boundary repair | completed | unresolved | 1 | structural pass plus classified provider outcomes | `work/closure-identity-performance/task-4/` |
| 5. Process-scoped registry reuse | completed | unresolved | 1, 4 | shared registry identity and unchanged hash validation | `work/closure-identity-performance/task-5/` |
| 6. Frozen p95 comparison | completed | unresolved | 2–5 | repeat stability and both ordinal comparisons pass in repeat-6 with enforced revision provenance | `work/closure-identity-performance/task-6/repeat-6/` |
| 7. CI/evidence/status hygiene | completed | unresolved | 4, 6 | deterministic gate remains green; compact evidence | `work/closure-identity-performance/task-7/` |
| 8. Final verification | completed | unresolved | 1–7 | fresh full proof and acceptance disposition | `work/closure-identity-performance/final/` |

## Current Execution Ledger

- Plan status is `completed`; Tasks 0–8 are implemented or verified, and their
  required focused and final verification passed.
- The original Task 6 receipts remain preserved with their stability failure:
  baseline drift `61.458%`, candidate drift `32.162%`, and ordinal run-1
  `CHALLENGE_RECOMMENDATION` regression `46.722%`.
- A fresh `repeat-6` protocol corrected the baseline receipt schema, required
  revision provenance, and used the same relative fixture identity. Stability
  passed and both ordinal comparisons passed: Group Chat p95 deltas `-0.218%`
  and `2.330%`, overall p95 deltas `7.464%` and `8.671%`, with the unchanged
  `20%` gate.
- Tasks 7 and 8 completed with fresh local verification and durable evidence.
  No threshold relaxation, provider authentication, Canva mutation, push, PR,
  or merge is claimed by this plan.

## Task Breakdown

### Task 0: Reconcile merged main and establish the execution lane

**Purpose:**
- Confirm the exact merged source, prior plan statuses, current benchmark
  contracts, and isolated workspace before changing code.

**Task Function:**
- Establish repository truth and durable execution ownership.

**Template Profile:**
- `unresolved`; controller resolves through Planning Dispatch.

**Specification Coverage:**
- Use `origin/main` merge commit `368f58e4fe2ce77d02023713f76adf2aac6622f1`.
- Treat the original closure-release plan and merged skill-layer-hardening plan
  as historical implementation records, not active runtime specifications.

**Required Skills:**
- `skill-using-git-worktrees`, `skill-executing-plans`

**Files And Symbols:**
- Inspect: `git status --short --branch`, `git worktree list --porcelain`,
  `git show origin/main`, and `git diff --name-status`.
- Inspect: `src/foresight_os/runtime/workflow.py:run_recipe_async`,
  `dispatch_stage`, `_run_native_stage`.
- Inspect: `src/foresight_os/controller/skills.py:SkillRegistry` and
  `src/foresight_os/persistence/analysis_store.py:StageReceipt`.
- Inspect: `evaluation/probes/run_optimization_probe.py:_measure_patterns` and
  `evaluation/probes/compare_optimization_receipts.py:compare`.

**Dependencies:**
- None.

**Authority:**
- Preauthorized: read Git/source/plan state and create the declared isolated
  worktree/evidence directory.
- Stop for: changed base SHA, unknown tracked edits in the fresh worktree, or
  any request to clean the current checkout.

**Steps:**
- [x] Fetch `origin/main` and verify it resolves to the recorded merge commit.
- [x] Create the task worktree from `origin/main` without copying current
  untracked outputs.
- [x] Record the source findings above and confirm PR #9 assets are present:
  nine skill manifests/fixtures, the evaluator, and the frozen optimization
  comparator.
- [x] Add this plan to the execution branch as the first tracked coordination
  artifact, create the authorized checkpoint that preserves its front matter and
  task ledger, then change `status` from `proposed` to `active` before activating
  Task 0. The lead remains the sole coordination-state writer.
- [x] Record the two historical plans as delivered implementation records only
  after verifying their own completion contracts and PR-bound evidence; do not
  use this plan to retroactively erase their blockers.

**Verification:**
- `git rev-parse origin/main`
- `git diff --name-status 368f58e4fe2ce77d02023713f76adf2aac6622f1 origin/main`
- `git ls-tree -r --name-only origin/main evaluation src/foresight_os/skills tests | rg "run_skill_exercise|evaluation/skills|test_skill_exercise|manifest.json"`
- Expected: the base matches, the isolated worktree is clean, and merged PR #9
  sources are present.

**Exit Criteria:**
- All later tasks can resume from the worktree and reconciliation receipt
  without relying on chat history.

### Task 1: Implement one canonical effective skill plan per participant

**Purpose:**
- Make stage and participant skill assignments resolve once at the workflow
  boundary and use the same result for every downstream concern.

**Task Function:**
- Correct runtime skill selection without adding a new orchestration layer.

**Template Profile:**
- `unresolved`; controller resolves through Planning Dispatch.

**Specification Coverage:**
- Effective IDs are the ordered de-duplicated union of stage skill IDs followed
  by participant skill IDs.
- Each participant gets its own resolved tuple; stage-only skills remain shared
  where assigned, and participant skills do not leak to other participants or
  stages.
- The resolved tuple feeds instructions, capability requirements, native MAF
  agent construction, fallback executors, and later identity computation.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`, `skill-executing-plans`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/workflow.py:run_recipe_async`,
  `_run_native_stage`, `dispatch_stage`.
- Modify: `src/foresight_os/runtime/participants.py:AgentFactory.create`.
- Verify/update call seams: `src/foresight_os/runtime/executors.py:AnalystExecutor.execute`
  and `ReviewerExecutor.execute`.
- Preserve `src/foresight_os/controller/skills.py:SkillRegistry.resolve`,
  `required_capabilities`, and `instructions` as the manifest/content authority.
- Add focused coverage in `tests/test_skills.py` and
  `tests/test_runtime_boundaries.py`.

**Dependencies:**
- Task 0.

**Authority:**
- Preauthorized: edit the named runtime/test owners and run local deterministic
  checks.
- Stop for: a need to change `RecipeStage` shape, add a second skill manifest,
  or change capability policy outside the named runtime boundary.

**Steps:**
- [x] Add one private, deterministic effective-ID assembly path at the workflow
  dispatch boundary; preserve declaration order and remove duplicates.
- [x] Resolve the effective IDs once for each participant with the run-scoped
  registry and store the result in the stage context keyed by participant ID.
- [x] Make `AgentFactory.create` consume the participant-specific selection;
  only resolve from `ParticipantConfig.skill_ids` when no canonical selection
  was supplied for a standalone caller.
- [x] Compute required capabilities from every effective participant skill plus
  explicit participant capabilities before hosted capability binding.
- [x] Ensure native MAF and fallback Analyst/Reviewer executor paths use the same
  participant-specific selection.
- [x] Add a mixed-skill regression with distinct stage and participant skills,
  asserting both instruction sections and both skill-derived capabilities are
  present only for the intended participant.

**Verification:**
- `python -m pytest -q tests/test_skills.py tests/test_runtime_boundaries.py`
- `python -m pytest -q tests/test_review_records.py tests/test_participant_scope.py`
- Expected: mixed-skill agents receive the ordered union, capability denial
  occurs before agent construction, and adjacent review/scope contracts remain
  green.

**Exit Criteria:**
- There is one observable effective skill plan per participant, and no downstream
  caller reconstructs a different skill tuple.

### Task 2: Bind fingerprints and receipts to the complete effective skill plan

**Purpose:**
- Prevent stale stage reuse when participant-specific skill assignments or skill
  content change.

**Task Function:**
- Repair semantic identity and receipt validation at their canonical owners.

**Template Profile:**
- `unresolved`; controller resolves through Planning Dispatch.

**Specification Coverage:**
- Semantic identity includes participant IDs and each participant's ordered
  effective skill records `(skill_id, version, content_sha256)`, not only
  `stage.skill_ids`.
- `StageReceipt.skill_hashes` contains ordered hashes for all effective skills in
  stable participant/skill order.
- Reuse rejects changed participant assignments, changed skill order, changed
  skill content hashes, changed capability fingerprints, and changed policy.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`, `skill-executing-plans`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/workflow.py:_stage_fingerprints`,
  `_stage_cache_key`, `dispatch_stage`.
- Verify/update: `src/foresight_os/persistence/analysis_store.py:StageReceipt`,
  `StageReceipt.reusable_for`, and `AnalysisStore.save_stage_receipt`.
- Extend: `tests/test_selective_reuse.py` and `tests/test_skills.py`.

**Dependencies:**
- Task 1.

**Authority:**
- Preauthorized: edit fingerprint/receipt producers and tests; preserve receipt
  schema compatibility unless a migration is proven necessary.
- Stop for: a request to invalidate receipts by caller-supplied cache hints or
  to add a second persistence identity format.

**Steps:**
- [x] Pass the Task 1 participant skill plan into `_stage_fingerprints` and make
  each participant's ordered `(skill_id, version, content_sha256)` records part
  of the canonical semantic payload.
- [x] Flatten the resolved content hashes in the same stable order and use that
  tuple for `StageReceipt.skill_hashes` and `reusable_for`; retain the version
  records in the semantic fingerprint so a version-only change invalidates reuse.
- [x] Keep the existing input, execution-policy, capability, model, authorization,
  and canonical-provenance checks unchanged.
- [x] Add separate tests where only a participant skill is added/removed/reordered,
  only a skill version changes while content/hash stays constant, and only a
  content hash changes; prove each old receipt is rejected and an identical plan
  still reuses.
- [x] Confirm receipt serialization remains deterministic and no raw skill content
  or secrets are written to durable evidence.

**Verification:**
- `python -m pytest -q tests/test_selective_reuse.py tests/test_skills.py`
- `python -m pytest -q tests/test_review_records.py`
- Expected: same complete plan reuses; participant-only assignment/content changes
  reassess; canonical result provenance is still required.

**Exit Criteria:**
- A stage receipt cannot be reused when any effective participant skill identity
  differs from the committed receipt.

### Task 3: Enforce one Group Chat round limit across native MAF and budgets

**Purpose:**
- Make declared Group Chat limits control actual native execution and make the
  reported budget/round metrics truthful.

**Task Function:**
- Repair the backend execution contract and prove important success/failure paths.

**Template Profile:**
- `unresolved`; controller resolves through Planning Dispatch.

**Specification Coverage:**
- The effective stage `max_rounds` value is passed to native
  `GroupChatBuilder` instead of hard-coded `4`; when a stage omits the limit,
  preserve the existing default of `4`.
- The same limit is applied to fallback Group Chat dispatch and shared
  `BudgetState`; observed rounds cannot exceed the declared limit.
- `BudgetState.max_rounds` remains `None` when no run-level ceiling is supplied;
  there is no hidden recipe-level round ceiling in the current source. If
  `run_context["max_rounds"]` is supplied, `run_recipe_async` initializes that
  optional cumulative ceiling and each stage uses the lesser of its declared
  limit (or default `4`) and the remaining cumulative allowance.
- Stage limits are positive integers. A non-positive configured value fails as an
  invalid stage configuration; a stage with no remaining explicit run-level
  allowance fails before invocation.
- Each observed native group-chat round or fallback participant exchange is
  charged exactly once. Early stabilization charges rounds already observed;
  reservation must not double-count stream observations.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`,
  `skill-executing-plans`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/workflow.py:_run_native_stage` and
  `dispatch_stage`, and `run_recipe_async` for optional run-level
  `max_rounds` initialization.
- Verify/update: `src/foresight_os/controller/budgets.py:BudgetState.reserve`.
- Preserve: `src/foresight_os/runtime/group_chat.py:run_challenge_recommendation`
  as the domain-level deterministic helper.
- Add coverage in `tests/test_group_chat.py`, `tests/test_maf_fit.py`, and
  `tests/test_runtime_boundaries.py`.

**Dependencies:**
- Task 1.

**Authority:**
- Preauthorized: edit the named runtime/budget owners and deterministic tests.
- Stop for: changes to Microsoft Agent Framework dependency versions, external
  provider invocation, or threshold changes.

**Steps:**
- [x] Derive one validated positive effective limit using the stage declaration
  and optional `run_context["max_rounds"]`; use `4` only when the stage omits a
  limit, and treat an unset run-level ceiling as unbounded.
- [x] Pass that value into native `GroupChatBuilder`, account for stream-observed
  rounds once, and reject a stage with no remaining allowance before constructing
  or invoking another participant.
- [x] Apply the same value to fallback Group Chat behavior. Keep
  `run_challenge_recommendation` as the deterministic domain helper; runtime
  fallback stabilization is limited to the existing analyst/reviewer exchange
  and does not introduce a second consensus algorithm.
- [x] Add direct tests using the installed native builder with a local fake client
  and observed round/model-call counts; cover fallback limits `1`, `2`, and `4`,
  invalid/exhausted limits, an unset run-level ceiling, differing stage limits,
  and a multi-stage run with `run_context["max_rounds"]` where the second stage
  cannot invoke after the cumulative allowance is consumed.

**Verification:**
- `python -m pytest -q tests/test_group_chat.py tests/test_maf_fit.py tests/test_runtime_boundaries.py`
- `python -m pytest -q tests/test_selective_reuse.py`
- Expected: native and fallback paths honor the same limit, successful runs
  report bounded rounds, and failures stop before over-budget execution.

**Exit Criteria:**
- Actual native/fallback rounds never exceed the effective stage/run allowance,
  and early stabilization may finish below the allowance while charging each
  observed round exactly once.

### Task 4: Repair evaluator failure classification and inherited provider configuration

**Purpose:**
- Make skill-quality evidence distinguish code defects from unavailable external
  providers while retaining the real XLSX evaluation path.

**Task Function:**
- Correct the existing provider probe and configuration boundary; do not add a
  second evaluator or infer human quality from structural scores.

**Template Profile:**
- `unresolved`; controller resolves through Planning Dispatch.

**Specification Coverage:**
- Structural/reference results remain deterministic and separate from provider
  runtime and human rubric classes.
- `BLOCKED_EXTERNAL` is used only for missing/invalid approved provider
  configuration, unavailable provider dependency, or provider transport/runtime
  boundary explicitly identified in the report.
- Unexpected evaluator/code/contract exceptions are `FAILED` and include a
  sanitized error type/message; they are not relabeled as external blocks.
- Missing `.env` does not prevent inherited `os.environ` configuration from
  being used, and secrets never enter reports.
- `run_full_pipeline_exercise.py` remains the real XLSX/full-pipeline evidence
  path; skill fixtures do not replace it.

**Required Skills:**
- `skill-backend-verification`, `skill-code-standards`, `skill-executing-plans`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/maf_probe.py:load_provider_settings`.
- Modify: `evaluation/probes/run_skill_exercise_evaluation.py:ALLOWED_STATUSES`,
  `_run_provider_cases`, `run_provider`, `validate_report_contract`.
- Modify: `evaluation/probes/run_full_pipeline_exercise.py:run` and `main` only
  to return an explicit `BLOCKED_INPUT` report when the approved input pack is
  absent; preserve a non-blocked failure when the pack exists but the pipeline
  fails.
- Extend: `tests/test_skill_exercise_evaluation.py`,
  `tests/test_evaluation_contract.py`, and focused provider-setting tests in
  `tests/test_maf_fit.py`.
- Update only explanatory boundaries in `evaluation/README.md` and `README.md`.

**Dependencies:**
- Task 1; Task 0 confirms the approved provider boundary.

**Authority:**
- Preauthorized: deterministic structural runs, fake/local provider test seams,
  and inherited-environment configuration tests.
- Stop for: real provider invocation without explicit approval, secret capture,
  external writes, or claiming provider quality from structural/reference checks.

**Steps:**
- [x] Make the env file optional and merge approved process environment values
  with file values using an explicit precedence rule; retain the existing config
  file as the provider/model/base URL source.
- [x] Add a report status for unexpected evaluator failure and classify only
  known setup/transport/dependency boundaries as `BLOCKED_EXTERNAL`.
- [x] Preserve structural report output when provider mode is blocked or failed;
  keep provider and human metric classes explicit and independent.
- [x] Add tests for missing optional env file with inherited settings, absent
  provider configuration, provider boundary failure, and an injected code defect.
- [x] Define the approved input-pack classifications in
  `run_full_pipeline_exercise.py`: absent root, absent validator, or zero
  participant workbooks produce `BLOCKED_INPUT`; one through four participant
  workbooks produce `BLOCKED_INPUT` as an incomplete pack; exactly five
  participant workbooks run the existing validator-isolated pipeline; more than
  five is also `BLOCKED_INPUT` as an unexpected pack shape. When the complete
  pack exists, preserve any real pipeline failure as `FAILED` and preserve the
  existing five-participant acceptance count.
- [x] Make `main` exit `0` for `VERIFIED` and `BLOCKED_INPUT`, and nonzero for
  `FAILED`; write the same status/report shape for every branch.
- [x] Add these five input-shape cases to `tests/test_evaluation_contract.py` and
  keep validator isolation and the existing participant acceptance checks intact.

**Verification:**
- `python -m pytest -q tests/test_skill_exercise_evaluation.py tests/test_maf_fit.py`
- `python evaluation/probes/run_skill_exercise_evaluation.py --mode structural --exercise-root evaluation/cases --skill-fixture-root evaluation/skills --output-root work/closure-identity-performance/task-4/structural`
- `python evaluation/probes/run_full_pipeline_exercise.py --exercise-root data/exercise --output-root work/closure-identity-performance/task-4/full-pipeline`
- Expected: structural five-case evidence remains `VERIFIED`; provider setup is
  either genuinely verified or explicitly `BLOCKED_EXTERNAL`; code defects are
  `FAILED`; absent optional XLSX inputs produce `BLOCKED_INPUT` without treating
  a real available-input pipeline failure as an input block.

**Exit Criteria:**
- The evaluation report no longer conflates implementation failures with
  unavailable external providers, and real XLSX evidence remains available.

### Task 5: Reuse the process/run-scoped SkillRegistry at canonical callers

**Purpose:**
- Remove repeated manifest/file/hash setup without weakening content validation
  or introducing global mutable state.

**Task Function:**
- Consolidate registry ownership at the existing run/review context boundary.

**Template Profile:**
- `unresolved`; controller resolves through Planning Dispatch.

**Specification Coverage:**
- `run_recipe_async` and review execution use the supplied context registry or
  create one once per run/process boundary.
- `SkillRegistry.resolve` keeps its current verified cache and hash mismatch
  failure behavior.
- Standalone tests and callers remain compatible when they explicitly supply a
  registry.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`, `skill-executing-plans`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/workflow.py:run_recipe_async` and
  `_run_native_stage` only where construction is duplicated.
- Modify: `src/foresight_os/analysis/reviewer.py:execute_review_skills` and
  `review_reasoning_with_skills`/`review_reasoning` registry seams.
- Modify: `evaluation/probes/run_skill_exercise_evaluation.py:run_structural`,
  `run_provider`, and `_run_provider_cases` so both evaluator modes reuse the
  caller-owned registry.
- Preserve: `src/foresight_os/controller/skills.py:SkillRegistry` cache and
  manifest validation.
- Extend: `tests/test_skills.py` and `tests/test_review_records.py`.

**Dependencies:**
- Tasks 1 and 4.

**Authority:**
- Preauthorized: edit named registry callers and tests.
- Stop for: a global singleton, cross-process persistence, or a second metadata
  cache outside `SkillRegistry`.

**Steps:**
- [x] Thread the existing context registry through native stage and review
  execution instead of constructing a replacement at each nested call.
- [x] Use one registry for each evaluator run and pass it through structural and
  provider paths where the caller already owns the run context; do not construct
  the second registry currently created independently by `run_structural` and
  `run_provider`.
- [x] Add identity/counting tests proving repeated resolution reuses the same
  registry/cache result and content hash mismatch still raises.

**Verification:**
- `python -m pytest -q tests/test_skills.py tests/test_review_records.py tests/test_skill_package.py`
- Expected: registry identity is reused at the intended boundary, all manifest
  hashes remain validated, and no global state leaks between tests.

**Exit Criteria:**
- Repeated skill setup is bounded by the existing registry cache and the owning
  run/review context, with no behavior change to skill contracts.

### Task 6: Stabilize and rerun the frozen Group Chat p95 comparator

**Purpose:**
- Produce trustworthy performance evidence after correctness fixes without
  changing the acceptance threshold.

**Task Function:**
- Establish a repeatable before/after measurement and decide the existing gate.

**Template Profile:**
- `unresolved`; controller resolves through Planning Dispatch.

**Specification Coverage:**
- Baseline and release use the same fixture, case, sample protocol, Python/
  dependency environment, and workload identity.
- `CHALLENGE_RECOMMENDATION`/Group Chat p95 is explicitly present in the
  comparison and is measured after Task 3.
- The existing `p95_regression_pct: 20` threshold remains unchanged; no tuning
  is accepted before benchmark stability is established.
- Correctness, resource, and economics checks remain part of the comparator.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`,
  `skill-executing-plans`

**Files And Symbols:**
- Inspect/modify only as measured: `evaluation/probes/run_optimization_probe.py:_measure_patterns`,
  `_run`; `evaluation/probes/compare_optimization_receipts.py:compare`;
  `evaluation/probes/compare_optimization_receipts.py:validate_stability`;
  `evaluation/probes/optimization_measurement.py:build_receipt`.
- Extend regression coverage in `tests/test_optimization_measurement.py`.
- Preserve `evaluation/baseline/README.md` workload contracts.

**Dependencies:**
- Tasks 2–5; all runtime, evaluator, and registry changes must be complete before
  performance tuning or interpretation.

**Authority:**
- Preauthorized: local baseline/release measurement, comparator tests, and
  disposable evidence output.
- Stop for: threshold changes, changing the fixture to improve the result,
  provider-backed calls, external publication, or interpreting a noisy run as
  acceptance without a repeatable protocol.

**Steps:**
- [x] Create these exact sibling detached worktrees before measurement:
  `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-baseline\foresight-OS`
  at `origin/main`, and
  `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-candidate\foresight-OS`
  at `refs/heads/codex/closure-identity-performance`. Run each probe from its
  own worktree with the same fixture
  `tests/fixtures/analyst_multisheet.xlsx`, the same Python executable and
  installed dependency set, and separate output directories. The `--mode` flag
  labels a receipt only; it does not select a revision.
- [x] Record `git rev-parse HEAD`, `python --version`, `python -m pip freeze`,
  fixture SHA, warm-up count, measured-run count, platform, and the resolved
  `foresight_os.__file__` path beside each receipt. Assert that the resolved
  package path is under the worktree being measured; do not import candidate
  source into the baseline worktree.
- [x] Repeat the full probe twice at each pinned SHA, preserving four distinct
  receipts: `baseline/run-1/receipt.json`, `baseline/run-2/receipt.json`,
  `candidate/run-1/receipt.json`, and `candidate/run-2/receipt.json`. Run the
  comparator's `validate_stability` path and accept the protocol only when the
  two Group Chat p95 values at each SHA differ by no more than `10%` and the
  per-pattern workload/fixture/environment metadata matches exactly; otherwise
  retain the performance blocker.
- [x] Compare ordinally paired receipts (`baseline/run-1` to `candidate/run-1`
  and `baseline/run-2` to `candidate/run-2`); both comparisons must pass. Use
  the saved baseline receipts from the baseline worktree and the saved candidate
  receipts from the candidate worktree; never regenerate the baseline from the
  final candidate worktree during final verification.
- [x] Compare receipts and inspect Group Chat p95, overall p95, peak allocation,
  RSS, per-finding economics, and 100-run soak results.
- [x] If the comparator still fails, record the exact metric and keep the plan
  active; do not relax the threshold or claim closure.

**Verification:**
- `python -m pytest -q tests/test_optimization_measurement.py`
- `git -C "C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-baseline\foresight-OS" rev-parse HEAD`
- `git -C "C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-candidate\foresight-OS" rev-parse HEAD`
- `python -c "import foresight_os; print(foresight_os.__file__)"` with `PYTHONPATH` set to the baseline `src` directory, then repeat with `PYTHONPATH` set to the candidate `src` directory; each path must be inside its named worktree.
- `python "C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-baseline\foresight-OS\evaluation\probes\run_optimization_probe.py" --mode baseline --fixture "C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-baseline\foresight-OS\tests\fixtures\analyst_multisheet.xlsx" --output "C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-baseline\foresight-OS\work\closure-identity-performance\task-6\baseline\run-1\receipt.json"`
- Repeat the preceding baseline command with `run-2`, then run the same two commands from the candidate worktree with `--mode release` and candidate paths.
- `python evaluation/probes/compare_optimization_receipts.py --baseline-repeat "C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-baseline\foresight-OS\work\closure-identity-performance\task-6\baseline\run-1\receipt.json" "C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-baseline\foresight-OS\work\closure-identity-performance\task-6\baseline\run-2\receipt.json" --release-repeat "C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-candidate\foresight-OS\work\closure-identity-performance\task-6\candidate\run-1\receipt.json" "C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-candidate\foresight-OS\work\closure-identity-performance\task-6\candidate\run-2\receipt.json" --output "C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-candidate\foresight-OS\work\closure-identity-performance\task-6\comparison.json"`
- Expected: the comparator accepts only when the existing ≤20% p95 gate and
  other frozen thresholds pass after the explicit two-run stability rule;
  otherwise the exact failed gate remains recorded.

**Exit Criteria:**
- Fresh evidence either proves the frozen Group Chat p95 gate or leaves a
  precise, reproducible blocker without relabeling it as verified.

### Task 7: Tier CI, compact durable evidence, and reconcile plan status

**Purpose:**
- Reduce operational noise while preserving the evidence needed for review and
  future recovery.

**Task Function:**
- Align CI and Git-tracked records with the actual acceptance boundary.

**Template Profile:**
- `unresolved`; controller resolves through Planning Dispatch.

**Specification Coverage:**
- Keep cheap deterministic PR checks in the existing CI job.
- Keep optimization comparison, 100-run soak, and provider-backed evaluation
  out of the cheap PR gate. Add a named `scheduled-evidence` workflow triggered
  by weekly schedule and manual dispatch; the scheduled path runs only the exact
  structural evaluator, clean-wheel smoke, and release optimization probe. The
  provider evaluator is a separate manual opt-in job with `run_provider: false`
  by default and a protected `provider-evidence` environment requiring explicit
  approval. Connected rendered-slide/Canva smoke is explicitly outside this PR
  and remains a separately authorized external boundary.
- Keep compact accepted receipts with commit, commands, statuses, skill IDs/
  versions/hashes, case counts, provider status, and blocked boundaries; move
  raw console dumps to disposable work outputs.
- Mark the original closure-release and skill-layer-hardening plans completed
  only when their already-delivered scopes are reconciled; keep this closure
  plan active until Tasks 1–6 and final verification settle.

**Required Skills:**
- `skill-code-standards`, `skill-executing-plans`

**Files And Symbols:**
- Verify: `.github/workflows/ci.yml` retains the existing deterministic PR job
  and required checks; do not change its required-check behavior in this PR.
- Add: `.github/workflows/evidence.yml:scheduled-evidence` with weekly
  `schedule` and `workflow_dispatch` triggers, a boolean `run_provider` input
  defaulting to `false`, exact local-only commands for structural skill
  evaluation, clean-wheel smoke, and release optimization measurement, plus a
  manually approved `provider-evidence` job that runs the provider command only
  when `run_provider == true`; upload JSON/Markdown reports as workflow
  artifacts.
- Update: `README.md`, `evaluation/README.md` for commands and evidence classes.
- Update: `docs/superpowers/plans/2026-10-13-1608-foresight-os-closure-release-plan.md`
  and `docs/superpowers/plans/2026-10-14-0021-foresight-os-skill-layer-hardening-plan.md`
  status/ledger reconciliation.
- Add compact receipt only under the existing durable evidence convention; do
  not add an evidence database.
- Write the sanitized durable summary to
  `docs/superpowers/evidence/closure-identity-performance-receipt.json` with
  commit, commands, statuses, skill IDs/versions/hashes, case counts, provider
  status, and blocked boundaries; keep raw logs in workflow artifacts or
  disposable `work/` output.

**Dependencies:**
- Tasks 4 and 6.

**Authority:**
- Preauthorized: documentation, CI tiering, compact receipt, and plan-ledger
  updates.
- Stop for: deleting preserved logs, changing PR acceptance thresholds, exposing
  secrets/provider payloads, or modifying Canva/publication behavior.

**Steps:**
- [x] Keep `pytest`, compile, contract/controller matrices, toolbelt/disposable
  MCP, wheel smoke, and whitespace checks in the cheap deterministic PR job.
- [x] Keep the current `.github/workflows/ci.yml` deterministic PR job unchanged
  in required checks, and add the named `scheduled-evidence` workflow with
  explicit local-only commands. Keep `run_provider` false by default, require
  the protected `provider-evidence` environment for the manual provider job,
  and do not add a connected Canva/rendered smoke job to this PR.
- [x] Create one compact accepted receipt for the PR with sanitized facts and
  references to disposable raw outputs.
- [x] Reconcile historical plan status text and this plan's completed acceptance
  boundary; do not mark this plan completed from a checked box alone.

**Verification:**
- `python -m pytest -q`
- `python -m compileall -q src tests`
- `python evaluation/run.py --matrix contract --output-root work/closure-identity-performance/task-7/contract`
- `python evaluation/run.py --matrix controller`
- `gh pr view 9 --json number,baseRefName,headRefName,headRefOid,statusCheckRollup`
- `gh pr checks 9`
- `git diff --check`
- Expected: deterministic PR checks stay green and documentation distinguishes
  verified local evidence from blocked external evidence; the historical
  hardening plan is marked completed only after its own PR-head CI evidence is
  verified.

**Exit Criteria:**
- CI and evidence storage reflect the same acceptance boundary without adding
  operational infrastructure or deleting preserved artifacts.

### Task 8: Perform final verification and acceptance disposition

**Purpose:**
- Re-run the complete required proof from the final implementation state and
  settle the plan status honestly.

**Task Function:**
- Final controller verification and cross-task integration review.

**Template Profile:**
- `unresolved`; controller resolves through Planning Dispatch.

**Specification Coverage:**
- Verify all nine implementation outcomes and every task exit criterion.
- Preserve `BLOCKED_EXTERNAL`, `BLOCKED_INPUT`, `FAILED`, and `not_measured`
  distinctions in final evidence.

**Required Skills:**
- `skill-verification-before-completion`, `skill-backend-verification`,
  `skill-performance-optimization`

**Files And Symbols:**
- Verify all Task 1–7 owners and the final compact evidence receipt.
- Review `git diff --stat`, `git diff --check`, focused test output, full test
  output, comparator output, and the two historical plan ledgers.

**Dependencies:**
- Tasks 1–7.

**Authority:**
- Preauthorized: local verification and plan status update only after fresh
  proof.
- Stop for: any failed mandatory test, unresolved identity mismatch, failed
  frozen p95 gate, unclassified provider result, or missing required evidence.

**Steps:**
- [x] Run the focused tests for skills, reuse, Group Chat, evaluator, MAF
  boundaries, and optimization measurement.
- [x] Run `python -m pytest -q`, compile, contract/controller matrices, and the
  clean-wheel smoke from the final worktree.
- [x] Review the p95 comparison and provider/full-pipeline evidence; record
  exact blocked boundaries without fabricating success.
- [x] Run `skill-verification-before-completion`; set this plan to `completed`
  only if it returns `verified` for all mandatory outcomes, otherwise leave it
  `active` with the exact failed or blocked acceptance gate.

**Verification:**
- `python -m pytest -q`
- `python -m compileall -q src tests`
- `python evaluation/probes/run_clean_wheel_smoke.py --output-root work/closure-identity-performance/final/clean-wheel`
- `git diff --check`
- `git status --short --branch`
- Expected: all deterministic checks pass; mandatory identity and Group Chat
  gates are either verified or explicitly remain the active blocker.

**Exit Criteria:**
- The final plan status, Git evidence, and user-facing disposition agree. No
  merge or external delivery claim is made by this plan.

## Completion Criteria

The next PR is ready for completion verification only when:

1. Mixed stage/participant skill selection is correct in native and fallback
   paths, with least-privilege capability resolution.
2. Participant-specific skill identity is present in fingerprints and receipts,
   and focused reuse tests prove invalidation and same-plan reuse.
3. Native and fallback Group Chat execution honor declared round limits and
   budget/metrics accounting is consistent.
4. The evaluator preserves structural five-case evidence, classifies code
   defects separately from `BLOCKED_EXTERNAL`, supports inherited configuration,
   and keeps real XLSX evidence in scope.
5. Registry construction is reused at the process/run boundary without a global
   singleton or weakened content-hash validation.
6. Fresh baseline/release measurements use identical workloads and environments;
   the existing Group Chat p95 threshold is passed or the exact blocker remains
   active. No threshold is changed.
7. Cheap PR CI, release evidence, compact receipts, and historical plan status
   all describe the same verified/blocked state.
8. Canva remains unchanged; absent connector authentication or publication
   capability is recorded as `BLOCKED_EXTERNAL`, not treated as a local code
   failure and not silently claimed complete.

## Final Verification Commands

Run these fresh from the final isolated worktree:

- `python -m pytest -q`
- `python -m compileall -q src tests`
- `python evaluation/run.py --matrix contract --output-root work/closure-identity-performance/final/contract`
- `python evaluation/run.py --matrix controller`
- `python evaluation/probes/run_clean_wheel_smoke.py --output-root work/closure-identity-performance/final/clean-wheel`
- `git diff --check`
- `git status --short --branch`

Run these only when the declared inputs and approved environments are available.
The provider command requires the manual `run_provider: true` dispatch and the
protected `provider-evidence` approval; the weekly scheduled workflow never
invokes it:

- `python evaluation/probes/run_skill_exercise_evaluation.py --mode provider --exercise-root evaluation/cases --skill-fixture-root evaluation/skills --extended-exercise-root data/exercise --output-root work/closure-identity-performance/final/provider`
- `python evaluation/probes/run_full_pipeline_exercise.py --exercise-root data/exercise --output-root work/closure-identity-performance/final/full-pipeline`
- `python evaluation/probes/compare_optimization_receipts.py --baseline-repeat "C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-baseline\foresight-OS\work\closure-identity-performance\task-6\baseline\run-1\receipt.json" "C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-baseline\foresight-OS\work\closure-identity-performance\task-6\baseline\run-2\receipt.json" --release-repeat "C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-candidate\foresight-OS\work\closure-identity-performance\task-6\candidate\run-1\receipt.json" "C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-candidate\foresight-OS\work\closure-identity-performance\task-6\candidate\run-2\receipt.json" --output "C:\Users\HOANG PHI LONG DANG\.codex\worktrees\closure-identity-candidate\foresight-OS\work\closure-identity-performance\final\optimization-comparison.json"

No command in this plan authenticates to Canva, publishes externally, exports
through a connector, or merges a branch. Those actions remain separately
authorized delivery steps after code and acceptance verification.
