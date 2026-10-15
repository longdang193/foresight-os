---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: foresight-os-investigation-overhead-optimization
targets:
  - src/foresight_os/controller/policy.py
  - src/foresight_os/controller/recipes.py
  - src/foresight_os/analysis/reviewer.py
  - src/foresight_os/analysis/review_workflow.py
  - src/foresight_os/analysis/independent_validation.py
  - src/foresight_os/domain/challenge.py
  - src/foresight_os/persistence/invalidation.py
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/runtime/capabilities.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/artifacts/report.py
  - src/foresight_os/artifacts/brief.py
  - .agents/skills/foresight-validation/SKILL.md
  - docs/architecture.md
  - docs/extending.md
  - docs/evidence-and-evaluation.md
  - evaluation/probes/run_case_portability_probe.py
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/compare_optimization_receipts.py
  - evaluation/README.md
  - docs/superpowers/plans/2026-10-15-foresight-os-investigation-overhead-optimization-plan.md
---

# ForesightOS Investigation-Overhead Optimization

## Verdict Review

Decision: accept the supplied direction as the next optimization objective,
but revise the execution plan to simplify first, measure second, and add new
mechanisms only when a failing case or measurement justifies them.

The core recommendation is correct: preserve strict trust-boundary invariants
while making assurance minimum-sufficient, deterministic-first, and adaptive.
The current repository already provides several foundations that must be
extended rather than replaced:

- `WorkBrief` and `ExecutionRecipe` are already separate owners. Runtime
  policy must remain in the recipe/controller path; do not add machinery to the
  canonical brief merely to expose execution details.
- Typed review checks and independent validation already exist in
  `controller.policy`, `controller.recipes`, `analysis.independent_validation`,
  and `domain.challenge`. Add applicability and escalation to those owners;
  expose `Explore`, `Assess`, and `Decide` only as optional projections over
  effective policy, not as a new runtime mode, registry, or status hierarchy.
- `CapabilityScope` already owns a run-scoped workbook cache and cleanup. Keep
  source currentness authoritative by recomputing the content hash before each
  cache lookup; optimize reuse at the complete-result level rather than adding
  an unsafe metadata-only identity cache. Any deeper immutable parsed snapshot
  is conditional on material remaining parse overhead; do not add an external
  cache.
- `PENDING_REVIEW`, `PROVISIONAL`, `ReviewSlotStatus`, invalidation, and
  conditional checks already represent most of the proposed state model. Add a
  user-facing projection and selective invalidation where needed; do not
  replace durable states wholesale.
- Repository evidence for this checkout shows that
  `.agents/skills/foresight-validation/SKILL.md` and
  `evaluation/probes/run_case_portability_probe.py` do not yet exist. The plan
  therefore retains their creation, but keeps the host procedure thin and the
  portability harness staged rather than treating either as an existing
  subsystem.
- `analysis.foresight_validator` is an exercise/evaluation validator used by
  tests, not proven NCC-specific runtime logic. Do not delete or move it merely
  because the proposal calls for removing case-specific code. First prove its
  consumers and then keep case semantics in evaluation data/configuration.

The current `main` checkout is at `bd5abc1`, is six commits behind
`origin/main`, and contains substantial pre-existing untracked `work/`, build,
data, and generated outputs. This plan preserves them and does not authorize
cleanup, rebasing, merging, or publication. The active plan
`2026-10-15-02-43-foresight-os-correctness-delivery-plan.md` overlaps the
controller, review, runtime, and schema owners. It blocks conflicting owner
edits until its remaining scope is explicitly reconciled, but it does not
block read-only inspection, baseline measurement, or documentation-only work.

The optimization is staged as three releases: (1) remove duplicate work and
make validation applicability and routing explicit, (2) reduce repeated
workbook identity/read cost with a measured run-scoped optimization, and (3)
patch only demonstrated projection/invalidation gaps and prove portability.
Optional assurance labels may be added over existing policy when they improve
the user path without creating a new durable mode. New investigations must be
represented as brief/source mappings/evaluation configuration whenever the
existing supported capabilities are sufficient.

## Goal

Reduce the latency, cost, configuration burden, and case-specific engineering
required for supported investigations without weakening provenance, review,
human acceptance, invalidation, or failure truthfulness.

The finished change must make a supported investigation normally require zero
production-code changes, minimal user configuration, and human attention only
at meaningful strategic decisions. It must preserve the following hard
invariants:

1. execution is not reported as successful without durable results;
2. arithmetic is not reported as verified without independent evidence;
3. approved evidence scope and source access are not silently changed;
4. known contradictions and missing material inputs remain visible;
5. automated review is never treated as human acceptance; and
6. material conclusions remain reconstructable from provenance.

## Implementation Outcomes

### Policy-driven minimum sufficient assurance

The existing controller resolves the required checks, capabilities, permissions,
and budgets that provide minimum-sufficient assurance. `Explore`, `Assess`, and
`Decide` may be exposed as optional user-facing presets over that effective
policy, but are not required first-release architecture and must not create
workflow engines, persistence types, or new status hierarchies. The default
remains suitable for ordinary recommendations, while consequential or uncertain
work adds only targeted checks. `WorkBrief` remains an intent and scope record,
not a runtime configuration object; derived execution detail may be shown in
the approval view.

### One validation lifecycle with targeted specialist checks

One repository-local `foresight-validation` host procedure coordinates the
post-execution validation phase. Existing specialist participant skills and
deterministic tools remain owners of their methods. Deterministic source,
range, formula, unit, period, completeness, and arithmetic checks run before
model-based escalation. The default execution path no longer pays for a
reviewer participant when independent post-persistence validation already owns
the assurance; intentionally selected Group Chat, Handoff, or explicit review
patterns retain their reviewer behavior.

### Immutable run-scoped workbook identity and reuse

The source version is checked by recomputing the content hash before each cache
lookup, so metadata-preserving edits cannot reuse stale values or provenance.
Reuse keys include source identity, content hash, selection, parsing options,
and effective limits. If content changes, a new fingerprint and snapshot are
required and affected validation becomes stale. Only complete successful reads
enter the cache; failed, cancelled, partial, or untrusted results do not. A
deeper parsed snapshot is added only if measurement proves read overhead is
still material. Workbook and analysis entries share one bounded memory budget;
the source file is never modified and every reused measurement retains the
original workbook hash and cell/range provenance.

### Selective conclusions and progressive disclosure

Known dependency closure allows the smallest dependent analytical scope to be
invalidated precisely. When dependency coverage is uncertain, the related
scope is conservatively marked for reassessment rather than claiming precision
the graph cannot prove. Missing feasibility inputs produce conditional
recommendations, not blanket investigation failure. Durable review and
human-acceptance states remain truthful, while reports and briefs present
compact user-facing summaries with progressive detail for sources, validation,
and execution. No automated state named `ACCEPTED` is emitted where human
acceptance is still pending.

### Case portability evidence

Existing evaluation cases become a staged portability benchmark. The first
release uses three representative shapes: an existing supported case, a
differently structured workbook requiring mappings only, and missing or
contradictory evidence. Later shapes may expand coverage after the first
release proves useful. The benchmark records production files changed, manual
configuration/actions, approval interruptions, provider/model calls, workbook
hashes/parses, time to first useful finding, escalations, recovery, peak memory,
and case-specific runtime branches, distinguishing automatically measured facts
from recorded engineering observations. New supported cases must target zero
production-code changes; exceptions require a documented new format,
capability, provider, or runtime defect.

### Maintained guidance and ownership boundaries

The host procedure, architecture guidance, extending guidance, and evaluation
documentation describe the thin routing model without duplicating the runtime
contract. Generated adapter surfaces, private credentials, raw provider
payloads, and disposable work outputs remain out of the plan's durable files.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-executing-plans`, `skill-performance-optimization`, `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve all pre-existing untracked outputs and generated files
- Commit policy: `no commits during execution`; request Git disposition only after fresh completion verification
- Preauthorized local actions: inspect declared owners, edit declared source/tests/docs, add the declared portability probe, run declared local checks, and write redacted local measurement receipts under `work/optimization-overhead-20261015/`
- User-approval actions: push, merge, rebase, publication, external writes, destructive recovery, discard, cleanup of pre-existing outputs, and any expansion beyond the declared files
- Parallel ownership: none; controller, validation, workbook, projection, and evaluation owners overlap through recipe and review contracts
- Sequential fallback: run Task 0, then the simplification release (Tasks 1–2 and 5), then the measured workbook release (Task 3), then the usability/portability release (Tasks 4 and 6); if the active correctness plan changes a shared owner, reconcile the plan and rerun the baseline before continuing
- Default executor: `none (lead controller)` until Task 0 resolves a bounded task profile; task-specific profiles override only when the task contract requires it
- Default authority: use the plan-level preauthorized local actions and do not cross a new canonical owner without plan reconciliation
- Default stop conditions: stop for scope/base changes, external or destructive actions, private data exposure, or a shared-owner conflict that cannot be reconciled
- Default verification discipline: focused task proof first; separate local implementation evidence from provider-dependent analytical evidence, recording unavailable dimensions as `BLOCKED_EXTERNAL`
- Target boundary: frontmatter names primary owners; adjacent existing tests/docs may be changed when directly required by a primary-owner change, while a materially new owner requires plan reconciliation

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `bd5abc1`
- Expected workspace: `existing untracked work/, build/, data/, generated files, and active-plan changes preserved; no cleanup`
- Next action: `preserve the verified working state; no Git disposition is authorized by this plan`
- Blockers: `fresh NCC provider execution remains blocked by the overlapping active correctness plan; local implementation, portability, and optimization verification are complete`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 0: reconcile owners and baseline | `completed` | current | `none (lead controller)` | active correctness plan disposition | baseline probe and scope ledger | `work/optimization-overhead-20261015/baseline/receipt.json`; active-plan branch/base mismatch recorded; local-only work allowed |
| Task 1: optional assurance projection | `completed` | current | `none (lead controller)` | Task 0 | focused policy/recipe tests | `13 passed`; optional labels deferred because existing effective policy is authoritative and labels would add no proven value yet |
| Task 2: validation escalation and duplicate review | `completed` | current | `none (lead controller)` | Task 0; Task 1 only if policy changes | review/workflow tests and local boundary probe | `61 passed`; default sequential reviewer removed; explicit reviewer patterns retained |
| Task 3: measured workbook identity/reuse | `completed` | current | `none (lead controller)` | Task 0 | toolbelt/cache/cancellation tests | focused cache tests and release probe; fresh source hashing, metadata-preserving change rejection, bounded cache state, failure/cancellation non-publication |
| Task 4: selective conclusions and UX projection | `completed` | current | `none (lead controller)` | Tasks 0–2 | invalidation, report, and acceptance tests | `19 passed`; derived finding summary added without changing durable status or human acceptance gates |
| Task 5: thin host procedure and guidance | `completed` | current | `none (lead controller)` | Tasks 0–2 | skill/link/package boundary tests | `13 passed`; `.agents/skills/foresight-validation/` added; packaged manifest unchanged |
| Task 6: staged portability benchmark and final proof | `completed` | current | `none (lead controller)` | Tasks 2–5 | three-case matrix, comparison receipt, full suite | portability receipt `VERIFIED`; release comparison `accepted=true`; repository-wide verification `verified` |

## Task Breakdown

### Task 0: Reconcile active owners and establish the measurement baseline

**Purpose:**
- Prevent overlapping plans from editing the same controller, review, runtime,
  and schema contracts without an agreed handoff.
- Capture a cold/warm baseline before changing the optimization objective.

**Task Function:**
- repository-truth reconciliation and performance baseline measurement

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: repository ownership and measurement setup are authority-
  sensitive and do not benefit from delegation.

**Validator Profile (optional):**
- Controller-selected: `<none>`
- Selection basis: baseline validity is checked by the controller against the
  declared workload and current Git state.

**Specification Coverage:**
- Preserve existing correctness work and make the optimization measurable.
- Treat the current active correctness-and-delivery plan as an upstream
  dependency rather than silently forking its changes.

**Required Skills:**
- `skill-performance-optimization`

**Files And Symbols:**
- Inspect: `docs/superpowers/plans/2026-10-15-02-43-foresight-os-correctness-delivery-plan.md`
- Inspect: `src/foresight_os/controller/policy.py`, `src/foresight_os/analysis/reviewer.py`, `src/foresight_os/runtime/local_toolbelt.py`, `src/foresight_os/runtime/capabilities.py`
- Inspect: `evaluation/probes/run_optimization_probe.py`, `evaluation/probes/compare_optimization_receipts.py`, and existing `evaluation/cases/`
- Verify: `git status --short --branch`, `git log -1 --oneline`, and the baseline receipt path

**Dependencies:**
- None for inspection; implementation Tasks 1–6 depend on this reconciliation.

**Authority:**
- Preauthorized local actions: inspect repository state and run the declared baseline probe without modifying pre-existing outputs.
- Stop for: any request to clean, rebase, merge, publish, or overwrite existing untracked evidence, or an unresolved shared-owner conflict with the active plan.

**Steps:**
- [x] Step 1: Record the active plan's terminal/remaining tasks and identify shared symbols that must be sequenced; allow read-only measurement and documentation work unless a probe itself mutates a conflicting owner.
- [x] Step 2: Run the existing optimization baseline on `tests/fixtures/analyst_multisheet.xlsx` and record cold/warm workbook reads, five native patterns, resource soak, and cleanup evidence under `work/optimization-overhead-20261015/baseline/`.
- [x] Step 3: Freeze the workload, environment, thresholds, and comparison inputs for the release receipt; record absolute baseline values and deltas, and calculate percentages only where a meaningful denominator exists. Mark provider-backed dimensions `BLOCKED_EXTERNAL` when configuration is absent.

**Verification:**
- [x] `python evaluation/probes/run_optimization_probe.py --mode baseline --fixture tests/fixtures/analyst_multisheet.xlsx --output work/optimization-overhead-20261015/baseline/receipt.json`
- Expected: one redacted, schema-valid baseline receipt with absolute values, explicit unavailable dimensions, unchanged source hash, and no cleanup of existing workspace outputs; zero-valued dimensions are recorded rather than rejected solely because a percentage denominator is unavailable.

**Exit Criteria:**
- Shared-owner sequencing is written into the coordination evidence and a
  comparable baseline receipt exists, or the task is explicitly `blocked` with
  the concrete dependency recorded.

**Execution Evidence (2026-10-15):**
- Local baseline completed at `work/optimization-overhead-20261015/baseline/receipt.json` with `VERIFIED` status, fixture SHA-256 `3f381b148ab6f2d0942061964b3851b26e4a66c224dd0866d431cc3c9d52d123`, `accepted_finding_count=1`, XLSX p95 `39.572 ms`, peak allocation `1,097,437 bytes`, and `80` model calls.
- The active correctness plan remains `active` at Task 7 with recorded branch/base metadata that differs from this checkout (`main` at `bd5abc1`). Its current Task 7 authority blocks fresh NCC provider execution, not this local baseline or the non-provider owners below; no NCC provider call was made.

### Task 1: Optionally project assurance presets through existing controller policy

**Purpose:**
- First determine whether `Explore`, `Assess`, and `Decide` can be exposed as
  understandable labels over existing effective policy without adding a new
  durable mode. Defer the labels if they would require new architecture.

**Task Function:**
- controller policy design and approval-fingerprint compatibility

**Template Profile:**
- Uses the plan default; resolve a bounded executor after Task 0 confirms the
  active plan's recipe and schema changes.

**Validator Profile (optional):**
- Uses the plan default; assign only if recipe serialization or approval
  fingerprint behavior needs an independent check.

**Specification Coverage:**
- Presets are optional policy projections only; the resolved required checks,
  capabilities, permissions, and budgets remain authoritative.
- `WorkBrief` remains intent, scope, assumptions, and research need truth.
- `ExecutionRecipe`/`ReviewPolicy` remains the runtime configuration owner.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/controller/policy.py:ReviewPolicy`, `ReviewPolicyResolver`, `select_recipe`, `_recipe_for_patterns`
- Inspect/modify: `src/foresight_os/controller/recipes.py:ExecutionRecipe`, `RecipeStage`, `ReviewCheckKind`, serialization methods
- Verify/modify if required by the existing contract: `src/foresight_os/schemas/execution_recipe.schema.json`
- Verify: `tests/test_review_policy.py`, `tests/test_execution_approval_fingerprint.py`, `tests/test_stage_inputs.py`

**Dependencies:**
- Task 0 complete and the active correctness plan no longer has an unresolved
  edit in these symbols.

**Authority:**
- Preauthorized local actions: edit existing policy/recipe owners and focused tests while preserving WorkBrief shape and approval-fingerprint semantics.
- Stop for: a need for a new durable profile store, WorkBrief runtime fields, new status enum, or a schema migration not covered by approved scope.

**Steps:**
- [x] Step 1: Map the existing `ReviewPolicyResolver` outputs to the proposed
  labels and make consequence, quantitative need, material source, and
  uncertainty inputs explicit.
- [x] Step 2: If the mapping is sufficient, expose the selected label through
  existing recipe/approval projection surfaces without making it an input to
  the canonical brief; otherwise record the preset as deferred.
- [x] Step 3: Ensure any material required-check change alters the approval
  projection and stale-reuse fingerprints, while retries and non-material
  adaptation remain inside the existing adaptation envelope.
- [x] Step 4: Keep policy resolution deterministic and explainable; overrides
  must be bounded and cannot silently widen evidence or authority.

**Verification:**
- [x] `python -m pytest -q tests/test_review_policy.py tests/test_execution_approval_fingerprint.py tests/test_stage_inputs.py`
- Expected: effective required checks remain authoritative, any optional labels
  are derived and explainable, material coverage changes affect fingerprints,
  and WorkBrief serialization remains unchanged. A deferred label is acceptable
  when exposing it would create a new durable mode.

**Exit Criteria:**
- Any preset projection is recipe-bound, serialized only through existing runtime
  ownership, fingerprinted when material, and covered by focused tests; no new
  profile store or runtime mode is introduced.

**Execution Evidence (2026-10-15):**
- Existing `ReviewPolicyResolver` and `ExecutionRecipe` already determine the
  effective checks, capabilities, and runtime ownership. Focused policy,
  approval-fingerprint, and stage-input tests passed (`13 passed`). The optional
  labels are deferred until a user-facing need or measurement justifies adding
  them; no source or schema change was required for this release.

### Task 2: Make validation deterministic-first, escalation-driven, and non-duplicative

**Purpose:**
- Run only the checks justified by actual evidence, risk, and uncertainty.
- Remove default reviewer duplication while preserving intentionally selected
  deliberation patterns.

**Task Function:**
- validation lifecycle integration and execution-policy simplification

**Template Profile:**
- Uses the plan default; resolve a bounded executor because shared
  runtime/review behavior has material correctness risk.

**Validator Profile (optional):**
- Uses the plan default; assign only to validate independent derivation and
  preservation of required contradictions.

**Specification Coverage:**
- One `foresight-validation` host lifecycle coordinator.
- Existing specialist skills remain reasoning methods.
- Deterministic checks precede model-based escalation.
- Reviewer-in-execution is opt-in by pattern or explicit policy, not automatic
  whenever post-persistence validation will run.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/analysis/independent_validation.py:run_independent_validation`, `read_validation_source`, check helpers
- Inspect/modify: `src/foresight_os/analysis/reviewer.py:execute_review_skills`, `review_reasoning_with_skills`
- Inspect/modify: `src/foresight_os/analysis/review_workflow.py:run_review_phase`, `accept_pending_analysis`
- Inspect/modify: `src/foresight_os/controller/policy.py:stage_roles`, review policy resolution
- Inspect/modify: `src/foresight_os/runtime/workflow.py:_run_native_stage`, participant dispatch and synthesis
- Verify: `tests/test_review_workflow.py`, `tests/test_review_hardening.py`, `tests/test_review_policy.py`, `tests/test_orchestration_patterns.py`

**Dependencies:**
- Task 0 complete; incorporate Task 1 only if its optional policy projection is
  adopted.

**Authority:**
- Preauthorized local actions: edit the existing review, independent-validation, and workflow owners plus focused tests using local stubs for provider/model boundaries.
- Stop for: any change that turns automated review into human acceptance, drops unresolved objections, removes Group Chat/Handoff behavior, or requires a second review registry.

**Steps:**
- [x] Step 1: Define a deterministic check inventory and escalation predicate
  using existing `ReviewCheckResult`, `ReviewSlotStatus`, and policy inputs.
- [x] Step 2: Make `run_independent_validation` accept the selected check set
  and distinguish applicability using existing review coverage/status semantics:
  checks not required by resolved policy are absent and do not affect
  completion; required checks that cannot run remain pending/unresolved; a
  required failure blocks the affected conclusion. Do not add another durable
  `NOT_RUN` hierarchy.
- [x] Step 3: Update reviewer role selection so default sequential/direct
  execution does not inject a second reviewer when independent validation owns
  the post-persistence assurance; retain reviewer interaction for explicit
  challenge, Group Chat, Handoff, or an approved recipe requirement.
- [x] Step 4: Keep conflict, missing-input, and contradiction evidence visible
  in review coverage and ensure a passing check cannot erase a blocking issue
  from another required category.
- [x] Step 5: Allow independent validators to share the immutable run-scoped
  source state while deriving their own checks; they must not reuse analyst
  output, denominator choices, or interpretations. Add local success/failure
  tests for no-calculation, ambiguous
  mapping, conflicting evidence, high-impact recommendation, unavailable
  specialist capability, and explicit reviewer-pattern cases.

**Verification:**
- [x] `python -m pytest -q tests/test_review_workflow.py tests/test_review_hardening.py tests/test_review_policy.py tests/test_orchestration_patterns.py`
- Expected: deterministic checks run first; non-required checks do not affect
  completion; required-but-unavailable checks remain visibly unresolved;
  required failures block only affected conclusions; targeted escalation is
  recorded; default reviewer calls decrease; intentional reviewer patterns and
  all blocking objections remain intact.

**Exit Criteria:**
- One validation lifecycle owns post-persistence assurance, default duplicate
  review is removed, and focused tests prove success, failure, missing-input,
  conflict, and intentional-review paths.

**Execution Evidence (2026-10-15):**
- Default sequential recipes retain typed review coverage for post-persistence
  assurance but no longer inject a reviewer participant; explicit reviewer
  requirements, Handoff, and Group Chat remain multi-participant.
- `run_independent_validation` now accepts a selected check set, omits checks
  that resolved policy does not require, preserves required-but-unavailable
  checks as `PENDING`, and supports sharing the run-scoped raw source cache
  without sharing analyst outputs.
- Focused review, controller, orchestration, fingerprint, and independent
  validation tests passed (`61 passed`).

### Task 3: Measure and reduce run-scoped workbook identity/read cost

**Purpose:**
- Stop proven repeated workbook parsing/opening/closing while preserving
  cancellation, limits, formula-cache trust, and provenance. Recompute source
  content hashes for currentness; add a deeper parsed snapshot only if
  measurement shows it is still needed.

**Task Function:**
- run-scoped deterministic resource optimization and boundary verification

**Template Profile:**
- Uses the plan default; resolve a bounded executor because resource behavior
  has measurable latency and cleanup impact.

**Validator Profile (optional):**
- Uses the plan default; assign only for an independent cache, immutability, or
  cancellation-settlement check.

**Specification Coverage:**
- Capture a source version once per run and tie all run-local reads to that exact
  version; if the file changes, require a new fingerprint and mark affected
  validation stale.
- Recompute source identity/hash before each cache lookup; do not use metadata-
  only currentness to authorize reuse.
- Cache key includes source identity, content hash, selection, parsing options,
  and effective limits.
- Only complete successful results are cached; cancellation and failure never
  publish a reusable result.
- Workbook and analysis cache entries share one bounded memory budget.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/runtime/local_toolbelt.py:WorkbookReadCache`, `_sha256_file`, `spreadsheet_read`, `WorkbookReadResult`
- Inspect/modify: `src/foresight_os/runtime/capabilities.py:CapabilityScope`, instrumented local dispatch, executor cleanup
- Inspect/modify: `src/foresight_os/analysis/independent_validation.py:read_validation_source`
- Verify: `tests/test_local_toolbelt.py`, `tests/test_runtime_boundaries.py`, `tests/test_ncc_independent_validation.py`, and optimization receipts

**Dependencies:**
- Task 0 baseline complete. Coordinate with Task 2 so validation reads use the
  same snapshot without weakening independent derivation.

**Authority:**
- Preauthorized local actions: edit the run-scoped toolbelt/cache and capability boundary, add focused local tests, and write redacted benchmark receipts.
- Stop for: external cache/storage, source-file mutation, weakened formula-cache trust, metadata-only currentness assumptions, incomplete cancellation settlement, or a cache entry published from a partial/failed read.

**Steps:**
- [x] Step 1: Separate one-time source identity acquisition from equivalent
  selection lookups under `CapabilityScope`; include selection, parsing options,
  and limits in the reuse key without re-hashing unchanged content for every
  lookup.
- [x] Step 2: Prove currentness/version binding: reads against changed content
  produce a new fingerprint and cannot reuse the old run-local result.
- [x] Step 3: Ensure reused measurements keep workbook SHA-256, sheet,
  coordinate, range, formula status, trusted flag, and related provenance.
- [x] Step 4: Enforce one bounded memory budget across workbook and analysis
  entries, and prove failed, cancelled, over-limit, and untrusted reads are not
  cached; prove the underlying worker and owned resources settle before the run
  releases capacity.
- [x] Step 5: Only if the baseline/release evidence shows material remaining
  parse overhead, introduce the smallest immutable parsed snapshot compatible
  with the existing `WorkbookReadResult` API; otherwise record the deferral.

**Verification:**
- [x] `python -m pytest -q tests/test_local_toolbelt.py tests/test_runtime_boundaries.py tests/test_ncc_independent_validation.py`
- Expected: equivalent reads avoid duplicate identity/hash work, distinct
  selections do not collide, changed content cannot reuse stale data, source
  hashes and provenance remain unchanged, cancelled/failed reads do not become
  cache hits, the shared memory bound holds, and cleanup completes after the
  worker exits.

**Exit Criteria:**
- The release probe shows lower duplicate workbook identity/read work without
  resource growth, provenance loss, or changed failure semantics; any deeper
  parsed snapshot is either justified by that evidence or explicitly deferred.

**Execution Evidence (2026-10-15):**
- Focused local toolbelt, runtime boundary, and independent validation tests
  cover fresh source hashing, metadata-preserving changed-content rejection,
  bounded cache state, and failed/cancelled read settlement.
- Release receipt: `work/optimization-overhead-20261015/release/receipt.json`.
  The same fixture hash and accepted-finding count were preserved; XLSX p95 was
  `39.133 ms` versus baseline `39.572 ms`, peak allocation was `1,097,285`
  bytes versus `1,097,437`, and RSS did not grow.
- Parsed snapshot work was deferred: focused tests and the release probe did
  not justify a second immutable parsed representation.

### Task 4: Make partial results, conditional recommendations, and selective invalidation visible

**Purpose:**
- Block only conclusions that depend on failed or missing evidence instead of
  failing the whole investigation.
- Present compact result states without collapsing automated review and human
  acceptance into one status.

**Task Function:**
- analytical dependency projection and truthful result presentation

**Template Profile:**
- Uses the plan default; resolve a bounded executor because domain semantics and
  acceptance boundaries require source-first reconciliation.

**Validator Profile (optional):**
- Uses the plan default; assign only to verify dependency closure and
  stale-review behavior independently.

**Specification Coverage:**
- Known dependency closure allows precise selective invalidation; uncertain
  dependency coverage causes a conservative related-scope reassessment rather
  than an unsupported precision claim.
- Missing feasibility inputs yield conditional recommendations.
- Durable `ReviewOutcome`, `ReviewSlotStatus`, and human decision states remain
  unchanged unless current source proves a missing state is necessary.
- User-facing output uses progressive disclosure.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/persistence/invalidation.py:invalidate_dependencies`
- Inspect/modify: `src/foresight_os/domain/challenge.py:derive_finding_views`, `review_category_statuses`, `accepted_consequential_recommendation`
- Inspect/modify: `src/foresight_os/analysis/review_workflow.py:accept_pending_analysis`
- Inspect/modify: `src/foresight_os/artifacts/report.py:render_report`, `src/foresight_os/artifacts/brief.py:deliverable_status`, `render_work_brief_markdown`
- Verify: `tests/test_invalidation.py`, `tests/test_finding_view.py`, `tests/test_review_workflow.py`, `tests/test_report_fidelity.py`, `tests/test_cli.py`

**Dependencies:**
- Task 2 complete; incorporate Task 1 only if its optional projection is adopted.
  Coordinate with the active correctness plan before
  touching `AnalysisState` or artifact status owners.

**Authority:**
- Preauthorized local actions: extend existing dependency, review, report, and brief projections with focused regressions for partial and conditional outcomes.
- Stop for: a new global status hierarchy, blanket failure on non-critical missing inputs, silent recommendation changes, or loss of human-acceptance gating.

**Steps:**
- [x] Step 1: First exercise the existing limitations, unresolved issues, review
  status, counterevidence, and reassessment projections against partial-result
  examples; add a focused projection test before changing domain semantics.
- [x] Step 2: Map each validation result and missing input to dependent record
  IDs through existing relationships and invalidation rules. Use precise
  invalidation only where the dependency closure is known; otherwise mark the
  related scope for conservative reassessment.
- [x] Step 3: Preserve unaffected findings as current/provisional while marking
  dependent findings stale, pending, conflicted, or conditionally usable.
- [x] Step 4: Add a user-facing summary projection such as supported,
  uncertain, correction-needed, and human-review-pending, with expandable
  source/validation/execution detail.
- [x] Step 5: Only when a focused failing test shows the existing durable state
  is insufficient, patch the owning invalidation/domain semantics. Prove reports
  do not say accepted before human acceptance and that
  renderer or optional-provider failure does not erase accepted analytical
  state.

**Verification:**
- [x] `python -m pytest -q tests/test_invalidation.py tests/test_finding_view.py tests/test_review_workflow.py tests/test_report_fidelity.py tests/test_cli.py`
- Expected: missing margin invalidates only dependent profitability conclusions,
  category growth remains available, conditional recommendations retain the
  missing-input trigger, and presentation/report failure leaves analytical
  state truthful.

**Exit Criteria:**
- Selective invalidation and progressive summaries are proven without changing
  the durable source-of-truth or human-acceptance contract.

**Execution Evidence (2026-10-15):**
- `19 passed` across invalidation, finding-view, review workflow, report
  fidelity, and CLI tests.
- Added the derived `supported`, `uncertain`, `correction-needed`, and
  `human-review-pending` projection to the existing finding/report path; no
  durable state hierarchy or acceptance rule was replaced.

### Task 5: Add one thin validation host procedure and update maintained guidance

**Purpose:**
- Make the routing contract discoverable while reducing duplicated procedural
  explanation and keeping the packaged skill registry unchanged.

**Task Function:**
- host-procedure consolidation and documentation ownership

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: host routing and documentation ownership are repository
  contract changes, not independent implementation lanes.

**Validator Profile (optional):**
- Controller-selected: `<none>`
- Selection basis: link and package-boundary checks are deterministic.

**Specification Coverage:**
- Add one `.agents/skills/foresight-validation/SKILL.md` containing only when
  to use, required inputs, owner calls, critical invariants, and stop condition.
- Keep `source-appraisal`, `quantitative-sanity-check`,
  `key-assumptions-check`, `red-team-claim`, and `abstain-or-escalate` as
  specialist methods.
- Keep the host procedure out of `src/foresight_os/skills/manifest.json`.
- Put detailed examples and the zero-production-change rule in maintained docs,
  not in the host skill.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Modify: `.agents/skills/foresight-validation/SKILL.md`
- Modify: `docs/architecture.md`, `docs/extending.md`, `docs/evidence-and-evaluation.md`
- Verify: `src/foresight_os/skills/manifest.json`, `src/foresight_os/controller/skills.py`, `tests/test_skill_package.py`, `tests/test_markdown_links.py`

**Dependencies:**
- Task 2 defines the validation ownership vocabulary; incorporate Task 1 only if
  its optional policy projection is adopted.

**Authority:**
- Preauthorized local actions: add the thin host procedure and update maintained documentation/link tests without editing generated adapter files or the packaged manifest.
- Stop for: a request to expose private governance, credentials, raw provider payloads, or to duplicate runtime contracts in the skill text.

**Steps:**
- [x] Step 1: Write the host procedure around the existing controller,
  `AnalysisStore`, review workflow, deterministic toolbelt, and acceptance
  boundary.
- [x] Step 2: Move long examples and user-facing explanation to the owning
  documentation pages; state the case-portability rule and complexity budget.
- [x] Step 3: Add routing/link/package-boundary checks and confirm the host
  procedure is not loaded as a participant skill.

**Verification:**
- [x] `python -m pytest -q tests/test_skill_package.py tests/test_markdown_links.py`
- Expected: the host procedure is discoverable, specialist skills remain
  registered, links pass, and no new packaged capability or vendor skill is
  required.

**Exit Criteria:**
- The validation lifecycle is documented once at the host boundary, with
  maintained docs owning detail and no generated/private surface changed.

**Execution Evidence (2026-10-15):**
- `13 passed` for skill package and Markdown link checks.
- Added `.agents/skills/foresight-validation/SKILL.md`; the packaged skill
  manifest and generated adapter surfaces were not changed.

### Task 6: Add the staged portability benchmark and complete optimization proof

**Purpose:**
- Measure whether supported business cases can run without production-code
  changes and compare the optimized path against the Task 0 baseline.

**Task Function:**
- evaluation harness design and final artifact verification

**Template Profile:**
- Uses the plan default; resolve a bounded executor because cross-case
  evaluation combines performance, correctness, and effort evidence.

**Validator Profile (optional):**
- Uses the plan default; assign only to inspect workload matching, denominator
  safety, and receipt completeness independently.

**Specification Coverage:**
- First benchmark three representative supported case shapes: an existing
  supported case, a differently structured workbook requiring mappings only,
  and missing or contradictory evidence. Expand to five only after the first
  release proves the harness is useful.
- Track production-file changes, manual setup/actions, approval interruptions,
  latency/cost, validation escalations, recovery, workbook hash/parse work,
  peak memory, and case-specific runtime branches.
- Keep analytical quality and infrastructure measurements separate.
- Distinguish automatically measured facts from recorded engineering
  observations.

**Required Skills:**
- `skill-performance-optimization`, `skill-verification-before-completion`, `skill-backend-verification`

**Files And Symbols:**
- Add: `evaluation/probes/run_case_portability_probe.py`
- Add: `tests/test_case_portability.py`
- Modify: `evaluation/README.md`, `docs/evidence-and-evaluation.md`,
  `evaluation/probes/compare_optimization_receipts.py`
- Verify: `evaluation/cases/case-001` through `case-003`,
  `evaluation/probes/compare_optimization_receipts.py`,
  `tests/test_optimization_measurement.py`

**Dependencies:**
- Tasks 0–5 complete and all shared owners reconciled.

**Authority:**
- Preauthorized local actions: add deterministic evaluation code/tests and write redacted baseline/release receipts under the declared work directory.
- Stop for: missing fixture/input, provider authentication, external delivery, or any result that would require claiming model quality or human acceptance without its separate proof.

**Steps:**
- [x] Step 1: Define the three-case matrix over an existing supported case, a
  mappings-only workbook variation, and missing/contradictory evidence; record
  the later two case shapes as deferred expansion candidates.
- [x] Step 2: Run each case from configuration/fixtures only and record
  production-file changes, new code/tests, manual actions, approval
  interruptions, hash/parse count, model calls, time to first useful finding,
  escalation count, recovery, peak memory, and runtime branch count.
- [x] Step 3: Run the release optimization probe with the same fixture,
  patterns, resource soak, and comparison inputs as Task 0; update the
  comparator to record absolute values and deltas, calculate percentages only
  for meaningful denominators, and fail closed on missing/incomparable inputs,
  resource growth, or quality regressions rather than on every zero baseline.
- [x] Step 4: Run the full repository verification and record all blocked or
  unavailable external dimensions separately from local verification.

**Verification:**
- [x] `python evaluation/probes/run_case_portability_probe.py --cases evaluation/cases --output work/optimization-overhead-20261015/portability/receipt.json`
- [x] `python evaluation/probes/run_optimization_probe.py --mode release --fixture tests/fixtures/analyst_multisheet.xlsx --output work/optimization-overhead-20261015/release/receipt.json`
- [x] `python evaluation/probes/compare_optimization_receipts.py --baseline work/optimization-overhead-20261015/baseline/receipt.json --release work/optimization-overhead-20261015/release/receipt.json`
- Expected: the three initial cases complete without production-code changes
  unless an explicitly documented capability/format/defect exception exists;
  measured and observed dimensions are separated; zero-valued baselines are
  represented with absolute values/deltas; and the release comparison is
  accepted or reports a truthful blocked/failed reason.

**Execution Evidence (2026-10-15):**
- Portability receipt `work/optimization-overhead-20261015/portability/receipt.json`
  is `VERIFIED` for three local case shapes; recovery and source-integrity
  checks passed with no production-file changes.
- Release comparison `work/optimization-overhead-20261015/release/comparison.json`
  is `accepted=true`, with absolute values and deltas recorded and zero-valued
  denominators treated as `0%` only when both sides are zero.
- Final repository verification passed: `python -m pytest -q`,
  `python -m compileall -q src tests evaluation`, Markdown link coverage for
  33 paths, final portability receipt `work/optimization-overhead-20261015/portability/final-receipt.json`, and `git diff --check`.
- The final portability run verified three distinct local fixtures and
  preserved source hashes, recovery, and production-file-change checks.
  Model-call and manual-action dimensions remain `not_measured`; all fixtures
  retain the required CSV columns, while `case-002` varies row coverage and
  mapping status and `case-003` varies values to exercise contradictory
  evidence.

**Exit Criteria:**
- Portability and optimization receipts are comparable, redacted, and
  reconciled with code/tests/docs. No claim of model quality, external
  delivery, or human acceptance is made without its own evidence.

## Verification

Final artifact-level verification is owned by `skill-verification-before-completion`
after all task-local proof passes:

- [x] `python -m pytest -q`
- [x] `python -m compileall -q src tests evaluation`
- [x] `python scripts/check_markdown_links.py README.md AGENTS.md .agents/skills/foresight-validation/SKILL.md --tracked-docs` (the plan's original `docs/` directory argument is unsupported by this checker; `--tracked-docs` provides the intended coverage)
- [x] `python evaluation/probes/run_case_portability_probe.py --cases evaluation/cases --output work/optimization-overhead-20261015/portability/final-receipt.json`
- [x] `python evaluation/probes/compare_optimization_receipts.py --baseline work/optimization-overhead-20261015/baseline/receipt.json --release work/optimization-overhead-20261015/release/receipt.json`
- [x] `git diff --check`
- [x] `git status --short --branch`, confirming all pre-existing untracked outputs
  remain untouched and only declared changes are in scope

Completion verification result: `verified`. A blocked external provider,
missing case input, or pending human acceptance remains explicitly blocked or
pending; it is not converted into a passing local result.

## Completion Criteria

The plan is ready for completion verification when:

1. Default execution no longer performs duplicate assurance work, while
   intentional Group Chat, Handoff, explicit challenge, and human-acceptance
   boundaries remain intact.
2. Only checks required by resolved policy affect completion; required but
   unavailable checks remain visible as unresolved, and failed checks block the
   conclusions they support without adding a parallel status hierarchy.
3. Repeated workbook analysis performs less redundant identity/hash/read work
   without weakening source versioning, provenance, cancellation, cleanup, or
   shared memory bounds; deeper parsed snapshots are added only when measured
   overhead justifies them.
4. Known dependency closures receive precise invalidation, uncertain coverage
   triggers conservative reassessment, and missing evidence blocks dependent
   conclusions without unnecessarily destroying unrelated useful analysis.
5. The normal user path requires only meaningful approvals, exposes technical
   details progressively, and any `Explore`/`Assess`/`Decide` labels remain
   optional projections rather than required runtime modes.
6. At least three materially different supported investigations complete without
   production-code changes or record explicit justified exceptions, with
   measured infrastructure facts separated from model-quality and human-
   acceptance claims.
7. `skill-verification-before-completion` returns `verified`; only then may the
   lead controller update plan status or pursue separately authorized Git
   disposition.
