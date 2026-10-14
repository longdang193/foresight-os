---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: foresight-os-canonical-architecture
targets:
  - src/foresight_os/domain/models.py
  - src/foresight_os/domain/approval.py
  - src/foresight_os/domain/validation.py
  - src/foresight_os/wayfinding.py
  - src/foresight_os/controller/recipes.py
  - src/foresight_os/controller/policy.py
  - src/foresight_os/controller/proposal.py
  - src/foresight_os/persistence/ids.py
  - src/foresight_os/persistence/analysis_store.py
  - src/foresight_os/persistence/invalidation.py
  - src/foresight_os/runtime/execution_gate.py
  - src/foresight_os/runtime/orchestration.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/artifacts/approval.py
  - src/foresight_os/cli.py
  - src/foresight_os/schemas/work_brief.schema.json
  - src/foresight_os/schemas/execution_recipe.schema.json
  - src/foresight_os/schemas/approval_record.schema.json
  - tests/
  - docs/templates/work-brief-template.md
  - docs/templates/approval-package-example.md
  - README.md
  - docs/architecture.md
  - docs/getting-started.md
  - docs/extending.md
  - docs/superpowers/plans/2026-10-14-1542-foresight-os-canonical-architecture-plan.md
---

# ForesightOS Canonical Architecture

## Goal

Implement the recommended human-control architecture without creating a
second analytical state store or a second orchestration engine:

```text
lightweight intake
  -> Wayfinding
  -> WorkBrief
  -> Controller-generated ExecutionRecipe
  -> derived ApprovalPackage
  -> ApprovalRecord
  -> shared execution gate
  -> existing MAF workflow runtime
  -> AnalysisState, review, and reassessment
```

Delivery is split into two independently verifiable milestones. Milestone A
ends when ForesightOS can produce, persist, display, edit, approve, restart,
and safely execute the exact reviewed investigation plan. Milestone B adds
reuse and runtime intervention only after Milestone A is accepted. The first
usable surface is a deterministic library and CLI proposal/approval flow that
emits human-readable Markdown plus machine-readable JSON. A richer browser UI
remains a later product decision and is not introduced by this plan.

## Verdict Review

The supplied consolidated verdict is accepted as the target architecture. Its
strongest decision is the ownership split:

- `WorkBrief` owns decision and investigation truth.
- The existing `ExecutionRecipe` becomes the complete execution truth.
- `ApprovalPackage` is a derived review projection, never another state store.
- `ApprovalRecord` owns human authorization for a specific brief/recipe
  projection.
- `AnalysisState` remains the analytical source of truth.

The repository review adds these implementation constraints:

1. The repository already owns `WorkBrief`, `ExecutionRecipe`, `AnalysisState`,
   `StageReceipt`, capability resolution, invalidation, and the MAF workflow.
   Tasks extend those owners instead of introducing a workflow platform,
   scheduler, graph database, or parallel analytical store.
2. The exact reviewed `ExecutionRecipe` must be persisted as
   `execution-recipe.json`. `ApprovalPackage` remains derived, while
   `execution-approval.json` stores authorization. `AnalysisStore` already owns
   the investigation directory and atomic lock/write boundary, so it will own
   recipe and approval persistence rather than a second approval-persistence
   module.
3. `WorkBrief` currently contains `execution_pattern_override`. The canonical
   model will replace that resolved-configuration field with typed
   `ExecutionIntent` containing required and preferred choices. The validator
   will accept and translate legacy briefs once, preserving an explicit legacy
   pattern as required intent; new writes emit only the canonical shape.
4. The current repository has no browser product surface. Human review is
   therefore implemented as deterministic Markdown/JSON package output and
   typed override APIs/CLI commands. Rich progressive-disclosure UI is a later
   surface, not a reason to duplicate domain state.
5. Existing `AnalysisState` and `StageReceipt` files under work directories
   must remain readable. Compatibility tests and explicit migration behavior
   precede any schema change.
6. The low-level `run_recipe_async` primitive remains an internal runtime
   primitive. Every public or user-facing execution path must call an approved
   execution entrypoint; tests and evaluation probes may bypass only through an
   explicit test-only API or flag.
7. The approved WorkBrief, exact recipe snapshot, and adaptation envelope are
   immutable for a run. Permitted runtime deviations are recorded separately;
   material deviations produce a revised proposal and renewed approval.
8. Approval and execution admission use the existing investigation lock for
   displayed-fingerprint verification, status transitions, and new-dispatch
   admission. Atomic writes alone are not sufficient concurrency control.
9. Local CLI approval is a trusted human-interaction boundary by explicit
   assumption, not authenticated identity. Runtime code, participants, and
   tools cannot invoke the approval transition.
10. The repository currently reports `ed9bcaf6315cbb8ce7ad8a0987304d0262a55a52`
    as `HEAD`; the verdict's `248cc81` bookkeeping value is not present here
    and is not adopted.

## Scope And Non-Goals

### In scope

- Lightweight WorkBrief intake with visible user preferences and progressive
  clarification inputs.
- Complete, rationale-bearing recipe generation from the brief, persisted as
  the exact reviewed `execution-recipe.json` snapshot.
- Validated human overrides for stages, topology, participants, skills,
  capabilities, permissions, budgets, review, reuse, and stop rules.
- Derived primary and detailed approval package rendering.
- Canonical approval projection hashing and durable ApprovalRecord storage.
- Gate enforcement before controller-driven MAF execution.
- Explicit adaptation envelope and material-change reapproval rules.
- Visible selective reuse with a per-stage `Reuse` or `Run Fresh` decision.
- Pause, cancel, and revise-remaining-work controls with invalidation-aware
  reassessment.
- CLI/library proof, migration fixtures, focused regression tests, and owned
  documentation.
- One reusable WorkBrief intake template and one validated generated
  approval-package example.

### Out of scope

- A new orchestration engine, distributed scheduler, queue, or workflow DSL.
- A second durable analytical state model or a copied recipe inside WorkBrief.
- Automatic external writes, provider authentication, or publication.
- A browser UI, hosted approval service, or full observability platform.
- Cross-process pause/resume control without an existing control transport.
- Changing the meaning or ownership of `AnalysisState`, NetworkX projections,
  `FindingView`, review records, or presentation delivery boundaries.
- Performance optimization not justified by a measured regression.

## Implementation Outcomes

### Canonical decision and execution ownership

`WorkBrief` stores the decision question, scope, assumptions, unknowns,
deliverables, constraints, and uncommitted user preferences. `ExecutionRecipe`
stores the controller's complete, rationale-bearing execution proposal in a
restart-safe file. No approval projection or runtime cache becomes a competing
source of truth.

### Inspectable and editable execution proposal

Every material execution choice is represented in the recipe and exposed in a
primary and detailed approval package. Typed overrides are either applied and
revalidated or rejected with an explicit diagnostic; no request is silently
ignored or normalized away.

### Approval-bound execution

An `ApprovalRecord` binds a canonical approval projection containing material
WorkBrief fields, material recipe fields, and the approved adaptation envelope.
The record binds the fingerprint displayed to the human, and the shared gate
refuses stale, missing, rejected, superseded, or out-of-scope approval before
MAF dispatch.

### Bounded adaptation and visible reuse

Runtime changes are classified as inside or outside a narrow approved envelope.
Retries within approved limits, lower concurrency/resource use, and equivalent
transient scheduling changes are allowed only when explicitly listed. New
providers, participant/reviewer substitution, topology changes, expanded
scope, increased budget, write access, or material deliverable changes require
renewed approval. Reusable stage receipts are shown with provenance and a
deterministic `Run Fresh` override rather than hidden as cache behavior.

### Intervention and reassessment

Milestone B pause stops new stage dispatch, cancel preserves completed evidence
and receipt state, and revise creates a new proposal for unfinished plus
revision-invalidated completed work. Existing dependency-aware invalidation
marks affected analytical outputs stale; unaffected work remains reusable.

### Migration and verification readiness

Legacy `brief.md`, `analysis.json`, and `stage-receipts.json` fixtures remain
loadable, new canonical files validate against packaged schemas, focused
success/failure paths are covered, and the repository-wide required checks
remain runnable.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-executing-plans`, `skill-code-standards`, `skill-backend-verification`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`; create one explicitly authorized finishing checkpoint only after fresh final verification
- Preauthorized local actions: edit declared repository files, add deterministic fixtures under `tests/`, run repository checks, update this plan's ledger/evidence, and preserve unrelated existing workspace outputs
- User-approval actions: provider authentication, external writes, publication, push, merge, destructive migration, deleting existing work outputs, or edits outside the declared targets
- Parallel ownership: `none`; `domain/models.py`, `controller/recipes.py`, `controller/policy.py`, and `runtime/workflow.py` are shared owners and require serialization
- Sequential fallback: execute Tasks 0–8 in dependency order in the current workspace; do not activate a second writer or isolated lane

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `ed9bcaf6315cbb8ce7ad8a0987304d0262a55a52`
- Expected workspace: current workspace with pre-existing untracked `build/`, `data/`, `src/foresight_os.egg-info/`, `work/`, and the untracked README showcase plan preserved; no cleanup or reset is authorized
- Next action: none; Task 8 final reconciliation completed after fresh verification
- Blockers: none known; the current branch is two commits behind `origin/main`, so execution must not rebase or merge without explicit approval

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 0 | `accepted` | current | `codex` | none | baseline inventory and focused baseline tests | baseline focused suite and compileall passed; canonical owners/callers inventoried; pre-existing untracked outputs preserved |
| Task 1 | `accepted` | current | `codex` | Task 0 | schema, migration, and contract tests | focused schema, compatibility, approval-contract, and compile checks passed |
| Task 2 | `accepted` | current | `codex` | Task 1 | proposal, override, capability, and rationale tests | proposal/refinement suites and compile check passed |
| Task 3 | `accepted` | current | `codex` | Tasks 1–2 | package rendering, displayed-fingerprint race, template, and approval persistence tests | exact recipe persistence, package, approval persistence, CLI help, and compile checks passed |
| Task 4 | `accepted` | current | `codex` | Tasks 1–3 | every public execution path passes the gate; restart-safe execution tests | gate, public-path, runtime-boundary, compile, and execute-help checks passed |
| Task 5 | `accepted` | current | `codex` | Tasks 0–4 | Milestone A full suite, migration, trust-boundary, and documentation proof | Milestone A package/gate/race/template suites, compile, and Markdown-link checks passed |
| Task 6 | `accepted` | current | `codex` | Task 5 | visible reuse, fallback policy, and fresh-result reassessment tests | reuse metadata/classification, explicit Run Fresh decisions, descendant reassessment, and compile checks passed |
| Task 7 | `accepted` | current | `codex` | Task 6 | run control/addressability, local or transport-backed pause/cancel, revise, and reapproval tests | run-control, materiality, invalidation, CLI-help, and compile checks passed; cross-process control remains explicitly transport-gated |
| Task 8 | `accepted` | current | `codex` | Tasks 5–7 | final docs, full suite, compile, link, diff, and scope proof | `python -m pytest -q`: PASS; `python -m compileall -q src tests evaluation`: PASS; `python scripts/check_markdown_links.py README.md --tracked-docs`: PASS, 23 paths; `git diff --check`: PASS; CLI help: PASS; live local propose/approve/execute/revise/reapproval probe: PASS; final scope inspection passed; preserved unrelated outputs remain untouched |

## Task Breakdown

### Task 0: Establish baseline ownership and compatibility inventory

**Purpose:**
- Prove the current canonical owners and identify compatibility obligations
  before changing the model boundary.

**Task Function:**
- Repository architecture and migration reconnaissance.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers the verdict's canonical ownership rule, the requirement to preserve
  existing behavior, and the plan's explicit migration constraint.

**Required Skills:**
- `skill-code-standards`.

**Files And Symbols:**
- `src/foresight_os/domain/models.py`: `WorkBrief`, `WorkStage`,
  `AnalysisState`.
- `src/foresight_os/controller/recipes.py`: `RecipeStage`,
  `ExecutionRecipe`, `make_recipe`.
- `src/foresight_os/controller/policy.py`: `select_recipe` and recipe
  selection helpers.
- `src/foresight_os/wayfinding.py`: `create_work_brief`.
- `src/foresight_os/persistence/analysis_store.py`: brief and stage-receipt
  persistence.
- `src/foresight_os/runtime/workflow.py`: `run_recipe_async`, stage cache and
  receipt handling.
- `src/foresight_os/persistence/invalidation.py` and
  `src/foresight_os/domain/relationships.py`: revision/reassessment flow.
- `src/foresight_os/schemas/work_brief.schema.json` and existing tests.

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: read source/tests/history, run focused baseline checks, and record findings in this plan without modifying product files.
- Stop for: an existing approval/proposal owner, a tracked migration generator, or an untracked change that cannot be classified without user direction.

**Steps:**
1. Record `git status --short --branch`, `git rev-parse HEAD`, and the current
   Python version in the execution evidence without resetting existing files.
2. Trace every current caller of `create_work_brief`, `select_recipe`,
   `run_recipe_async`, `AnalysisStore.save_brief`, and `StageReceipt`.
3. Classify `brief.md`, `analysis.json`, `analysis.pending.json`, and
   `stage-receipts.json` as compatibility surfaces; record their current
   versions and required defaults.
4. Confirm that no tracked frontend, approval service, generated schema
   source, or alternate execution engine exists.
5. Run the baseline focused suite before any source edit.

**Verification:**
- `python -m pytest -q tests/test_controller_selection.py tests/test_analysis_schema.py tests/test_persistence.py tests/test_selective_reuse.py tests/test_runtime_boundaries.py`
- `python -m compileall -q src tests evaluation`
- `git status --short --branch` still contains the pre-existing untracked
  outputs and no plan-induced product changes.

**Exit Criteria:**
- Canonical owners, callers, schemas, compatibility files, and baseline test
  results are recorded; no hidden approval implementation or generated source
  is assumed.

### Task 1: Define canonical WorkBrief intent, recipe, and approval contracts

**Purpose:**
- Establish the typed contracts and packaged schemas that separate decision
  truth, execution truth, and human authorization.

**Task Function:**
- Domain model and durable contract implementation.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers the two canonical linked objects, typed required/preferred execution
  intent, derived ApprovalPackage boundary, approval projection fingerprint,
  narrow adaptation envelope, and legacy brief compatibility.

**Required Skills:**
- `skill-code-standards`.
- `skill-test-driven-development`.
- `skill-backend-verification` for durable contract and failure-path proof.

**Files And Symbols:**
- `src/foresight_os/domain/models.py`: add `ExecutionIntent` with required and
  preferred choices; revise `WorkBrief`; preserve `WorkStage` as
  investigation-stage truth; do not place resolved recipe data in the brief.
- `src/foresight_os/controller/recipes.py`: extend `RecipeStage` and
  `ExecutionRecipe` with explicit rationale, capability/access summary,
  review/completion/escalation/reuse policy, and adaptation metadata while
  preserving existing runtime fields.
- `src/foresight_os/domain/approval.py`: add `ApprovalStatus`,
  `AdaptationEnvelope`, `ApprovalProjection`, `ApprovalRecord`,
  `MaterialChange`, and deterministic projection canonicalization. Keep
  proposal states ephemeral as `DRAFT` and `READY_FOR_REVIEW`; an absent
  ApprovalRecord means not approved. Approval statuses are only `APPROVED`,
  `REJECTED`, and `SUPERSEDED`.
- `src/foresight_os/persistence/ids.py`: add the shared canonical JSON hash
  helper used by approval projections; retain `deterministic_id` behavior.
- `src/foresight_os/domain/validation.py`: add validators for the new contracts
  and a legacy loader that translates `execution_pattern_override` into
  required `ExecutionIntent` without silently changing a newly authored brief.
- `src/foresight_os/schemas/work_brief.schema.json`: replace the canonical
  resolved-pattern property with typed required/preferred execution intent and
  preserve all existing required fields.
- `src/foresight_os/schemas/execution_recipe.schema.json`: add the packaged
  recipe contract, including stage dependencies, participant responsibility,
  capabilities, limits, rationale, and stop/review policy.
- `src/foresight_os/schemas/approval_record.schema.json`: add the durable
  authorization contract and allowed statuses.
- `tests/test_analysis_schema.py`, `tests/test_persistence.py`, and new
  `tests/test_approval_contract.py` and `tests/test_work_brief_compatibility.py`.

**Dependencies:**
- Task 0.

**Authority:**
- Preauthorized local actions: modify the listed canonical model, schema, validator, and focused test files; add only the named approval module and schemas.
- Stop for: a required change to `AnalysisState` semantics, a destructive rewrite of existing work directories, or a need to introduce a second analytical state owner.

**Steps:**
1. Add `user_preferences` as uncommitted intake information. Keep scope,
   assumptions, open dependencies, deliverables, horizon, and consequence level
   in `WorkBrief`; keep investigation stages in `WorkStage`.
2. Remove resolved execution configuration from newly serialized briefs. Accept
   legacy `execution_pattern_override` only in the load/validation adapter and
   translate it to a required execution choice with a migration diagnostic.
3. Add recipe fields for rationale and material execution policy without
   changing the existing `run_recipe_async` input contract.
4. Define the approval projection as a canonical payload containing material
   WorkBrief fields, material recipe fields, and the adaptation envelope. Exclude
   transient runtime counters, object addresses, raw provider payloads, and
   secrets before hashing.
5. Validate enum values, stage dependency references, non-negative limits,
   required/preferred intent conflicts, approval status transitions, and the
   narrow adaptation-envelope consistency.
6. Add fixtures for a current brief, a legacy brief with
   `execution_pattern_override`, a current recipe, and each approval status.

**Verification:**
- `python -m pytest -q tests/test_analysis_schema.py tests/test_persistence.py tests/test_approval_contract.py tests/test_work_brief_compatibility.py`
- Current briefs round-trip with the canonical fields and legacy briefs load
  without emitting the legacy field on the next save.
- Equivalent projections hash identically regardless of dictionary insertion
  order; material brief/recipe changes hash differently.
- Invalid stage dependencies, invalid statuses, negative limits, and malformed
  adaptation envelopes fail with typed validation errors.

**Exit Criteria:**
- The domain and schema layer has one canonical brief/intent shape, one
  complete recipe shape, one minimal approval-record shape, deterministic
  fingerprints, and explicit compatibility behavior for existing work
  directories.

### Task 2: Generate and validate the complete execution proposal

**Purpose:**
- Make Wayfinding produce bounded investigative intent and make the Controller
  resolve a complete, explainable `ExecutionRecipe` from it.

**Task Function:**
- Controller policy and proposal construction.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers lightweight intake, progressive clarification, complete recipe
  generation, rationale, typed intent, editable overrides,
  capability/permission checks, dependency recalculation, enforceable limits,
  and explicit unsupported-change diagnostics.

**Required Skills:**
- `skill-code-standards`.
- `skill-backend-verification` for capability, permission, and failure-boundary
  proof.
- `skill-test-driven-development`.

**Files And Symbols:**
- `src/foresight_os/wayfinding.py`: preserve `create_work_brief`; add the
  bounded refinement function that records decision, scope, inputs,
  assumptions, unknowns, outcome, deliverables, constraints, and preferences.
- `src/foresight_os/controller/proposal.py`: add `build_execution_recipe`,
  `apply_execution_overrides`, `validate_execution_recipe`, and typed
  `OverrideDiagnostic`/`ProposalResult` contracts.
- `src/foresight_os/controller/policy.py`: retain `select_recipe`; make pattern,
  role, skill, capability, budget, review, completion, escalation, and reuse
  choices explicit and rationale-bearing.
- `src/foresight_os/controller/recipes.py`: preserve direct, sequential,
  concurrent, handoff, and group-chat runtime patterns while populating the
  enriched recipe fields. The persisted contract must expose work inputs and
  outputs, coordination rationale, participant responsibilities, skill
  versions, capability/data/read-write scope, provider/model/profile, supported
  reasoning controls, enforced limits, review independence/checkpoints,
  completion, escalation, partial-result, reuse, and adaptation policy.
- `src/foresight_os/controller/skills.py`, `src/foresight_os/controller/profiles.py`,
  `src/foresight_os/controller/budgets.py`, and
  `src/foresight_os/runtime/capabilities.py`: use existing registries/resolvers
  for hashes, availability, scope, permission policy, and limits.
- `tests/test_controller_selection.py`, new `tests/test_wayfinding.py`, and
  new `tests/test_execution_proposal.py`.

**Dependencies:**
- Task 1.

**Authority:**
- Preauthorized local actions: modify the listed Wayfinding/controller/resolver adapters and add deterministic proposal tests using existing capability fixtures.
- Stop for: a requested provider authentication, an unavailable capability that requires external setup, or an override that changes analytical scope without an explicit material-change result.

**Steps:**
1. Make the lightweight intake path require only a decision question and
   investigation identity, while preserving explicit defaults for deliverables,
   horizon, and consequence level.
2. Add progressive refinement inputs without making the user select agent
   topology during intake. Parse human text into typed required/preferred
   `ExecutionIntent`; never execute free-form preference text directly. Show the
   resolved interpretation in the generated proposal.
3. Generate one complete recipe from the refined brief. Every stage must carry
   objective, dependencies, pattern, participants, skills, capabilities,
   limits, rationale, expected output, review checks, completion rule,
   escalation rule, partial-result rule, and reuse policy.
   Display only limits and reasoning controls that the selected runtime can
   enforce; label estimates as estimates rather than presenting them as hard
   limits.
4. Parse typed override requests and apply them to a recipe copy. Revalidate
   topology compatibility, dependency order, participant count, skill hashes,
   capability availability, authorization scope, budgets, and stop rules.
5. Controller defaults may complete a system-generated proposal and explain
   the addition, but an explicit human override is applied exactly or rejected.
   Never silently add a participant, reviewer, skill, provider, or capability
   back after a human removed it.
6. Return diagnostics for rejected changes. Cover the explicit examples:
   group chat with one participant is rejected; an unavailable FRED capability
   returns unavailable status plus the configured alternatives; no override is
   silently ignored.
7. Keep `select_recipe` deterministic for existing callers and route new
   proposal generation through the enriched path.

**Verification:**
- `python -m pytest -q tests/test_controller_selection.py tests/test_wayfinding.py tests/test_execution_proposal.py tests/test_capabilities.py tests/test_skills.py`
- The same brief and resolver state produce byte-equivalent recipe projections.
- Each selected pattern has a human-readable rationale and complete stage
  fields; unresolved capabilities remain explicit rather than becoming success;
  displayed hard limits are backed by enforcement and unsupported controls are
  labelled non-enforced estimates.
- Valid overrides update the proposal and invalidate dependent budget/rationale
  fields; invalid overrides return diagnostics and leave the original recipe
  unchanged.

**Exit Criteria:**
- A user can start with a lightweight question, receive a complete inspectable
  recipe, edit it through typed overrides, and receive explicit validation
  results without configuring agent mechanics manually.

### Task 3: Persist the reviewed recipe and render the approval package

**Purpose:**
- Persist the exact recipe that the human reviews, then render the brief plus
  recipe into a human-reviewable package with a displayed fingerprint.

**Task Function:**
- Exact recipe persistence, approval projection, and trusted review boundary.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers restart-safe recipe persistence, primary/detail progressive disclosure,
  editable proposal review, displayed-fingerprint approval, minimal approval
  lifecycle, and the WorkBrief → recipe → approval boundary.

**Required Skills:**
- `skill-backend-verification`.
- `skill-code-standards`.
- `skill-test-driven-development`.

**Files And Symbols:**
- `src/foresight_os/artifacts/approval.py`: add deterministic primary and
  detailed Markdown renderers plus JSON serialization for `ApprovalPackage` as
  a derived view only.
- `src/foresight_os/persistence/analysis_store.py`: add atomic
  `save_recipe`, `load_recipe`, `save_execution_approval`, and
  `load_execution_approval` methods beside the existing work-directory lock;
  persist `execution-recipe.json` and `execution-approval.json` without
  embedding either in `AnalysisState`.
- `src/foresight_os/domain/approval.py`: include the displayed package
  fingerprint, `approval_source`, optional `approver_label`, and approval
  timestamp in `ApprovalRecord`.
- `src/foresight_os/cli.py`: add local `propose` and `approve` commands that
  emit package JSON/Markdown and require the displayed fingerprint on approval.
- New `tests/test_approval_package.py`, `tests/test_approval_persistence.py`,
  and updates to `tests/test_persistence.py`.
- New `docs/templates/work-brief-template.md` and
  `docs/templates/approval-package-example.md`; both must be generated from
  and validated against the supported contracts.

**Dependencies:**
- Tasks 1–2.

**Authority:**
- Preauthorized local actions: add exact-recipe persistence, derived package rendering, local approval recording, templates, CLI commands, and focused local boundary tests named above.
- Stop for: any request to call an external provider or mutate an external destination, a stale/missing approval that would otherwise be treated as approved, or a request to persist a third recipe copy inside the package.

**Steps:**
1. Persist the controller-generated or human-edited `ExecutionRecipe` as
   `execution-recipe.json` before rendering. Reloading the work directory must
   recover the exact stage order, override choices, required/preferred intent,
   limits, capabilities, and adaptation policy.
2. Build `ApprovalPackage` from the persisted `WorkBrief` and exact recipe at
   render time. The primary view exposes decision, scope, inputs, unknowns,
   stages, deliverables, external access, and limits. The detailed view exposes
   dependencies, patterns and rationale, participants, skills, capabilities,
   models, budgets, review, reuse, and stop rules.
3. Persist only the `ApprovalRecord` and its canonical projection/fingerprint,
   displayed package fingerprint, local approval source, optional label,
   timestamp, and status in `execution-approval.json`. Store no raw provider
   response, credential, authorization header, or third recipe copy.
4. Make `approve` accept the displayed package fingerprint, acquire the
   investigation lock, reload the current brief and recipe, recompute the
   package fingerprint, and reject approval when it differs. This closes the
   display-A/mutate-to-B race.
5. Treat local CLI approval as an explicit trusted human-interaction boundary,
   not authenticated identity. Runtime code, participants, and tools cannot
   call the approval transition.
6. Keep proposal states ephemeral as `DRAFT` and `READY_FOR_REVIEW`; an absent
   ApprovalRecord means not approved. Keep durable approval statuses limited to
   `APPROVED`, `REJECTED`, and `SUPERSEDED`.
7. Keep the CLI deterministic and local. It must not authenticate, publish, or
   perform external writes.

**Verification:**
- `python -m pytest -q tests/test_approval_package.py tests/test_approval_persistence.py tests/test_persistence.py`
- Rendered primary and detailed packages contain all material review fields and
  are stable for equivalent inputs.
- The exact human-edited recipe persists and reloads after process restart.
- Display A → mutate recipe → approve A rejects without creating an approval.
- Approval records truthfully identify `local_cli` as the source and do not
  claim authenticated identity.
- `python -m foresight_os.cli propose --help` and
  `python -m foresight_os.cli approve --help` succeed.

**Exit Criteria:**
- The repository has a restart-safe exact recipe, one human-readable derived
  approval surface, a displayed-fingerprint race check, and an explicit local
  human-approval boundary; the package remains a derived view over canonical
  owners.

### Task 4: Enforce approval admission on every public execution path

**Purpose:**
- Establish the architectural boundary that every real user-facing execution
  path crosses before calling the existing MAF workflow.

**Task Function:**
- Execution admission and public/internal/test boundary enforcement.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers the shared execution gate, immutable approved baseline, restart-safe
  execution, locking, explicit test bypass, and public-path protection.

**Required Skills:**
- `skill-backend-verification`.
- `skill-code-standards`.
- `skill-test-driven-development`.

**Files And Symbols:**
- `src/foresight_os/runtime/execution_gate.py`: add `ExecutionGate` and
  `execute_approved_investigation` that load the persisted recipe and approval
  under the investigation lock before dispatch.
- `src/foresight_os/runtime/orchestration.py`: expose the approved entrypoint
  and retain `run_recipe_async` only as an internal primitive.
- `src/foresight_os/cli.py` and `src/foresight_os/clients/first_client_adapter.py`:
  route every user-facing execute path through the gate.
- `src/foresight_os/runtime/workflow.py`: accept an immutable approved recipe
  snapshot and record permitted runtime deviations separately.
- `tests/test_execution_gate.py`, `tests/test_public_execution_paths.py`, and
  updates to `tests/test_runtime_boundaries.py`.

**Dependencies:**
- Tasks 1–3.

**Authority:**
- Preauthorized local actions: add the gate and approved entrypoint, route listed public callers, and add explicit internal/test bypass coverage.
- Stop for: a public caller that cannot be classified, an execution path that bypasses the gate implicitly, or a mutation of an approved recipe during runtime.

**Steps:**
1. Inventory and classify every `run_recipe_async`/`run_recipe` caller as
   `PUBLIC / USER-FACING`, `INTERNAL PRIMITIVE`, or `TEST / EVALUATION PROBE`.
2. Make public/client/CLI execution call
   `execute_approved_investigation(...) -> ExecutionGate -> run_recipe_async(...)`.
3. Permit test/evaluation bypass only through an explicit named test API or
   flag; do not make the low-level primitive look like an approved execution.
4. Under the existing investigation lock, reload `brief.md`,
   `execution-recipe.json`, and `execution-approval.json`; verify status,
   projection fingerprint, recipe snapshot identity, and adaptation envelope
   before marking a new dispatch admitted.
5. Treat the approved baseline as immutable. Allowed deviations are recorded as
   runtime events; a material deviation creates a revised proposal rather than
   mutating the approved recipe.
6. Ensure rejection, revocation, or supersession prevents new dispatch while
   already-running owned work follows explicit cancellation/adaptation rules.

**Verification:**
- `python -m pytest -q tests/test_execution_gate.py tests/test_public_execution_paths.py tests/test_runtime_boundaries.py`
- Every user-facing execution command reaches the gate.
- Missing, stale, rejected, superseded, mismatched, or out-of-envelope
  approvals are denied before any MAF call.
- The internal primitive and evaluation probe bypass are explicit and cannot be
  reached through the normal CLI/client path.
- Approved recipe changes after approval are denied rather than silently
  rewritten or accepted.

**Exit Criteria:**
- Restarting a process and executing through the public path runs the exact
  persisted approved recipe, and no public path can bypass the shared gate.

### Task 5: Accept Milestone A and publish the foundation artifacts

**Purpose:**
- Independently verify the restart-safe approval foundation before adding reuse
  or live runtime intervention.

**Task Function:**
- Milestone acceptance, contract examples, and foundation reconciliation.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers the first milestone's intake, proposal, exact persistence, review,
  edit, approval, trust boundary, gate, migration, and restart requirements.

**Required Skills:**
- `skill-verification-before-completion`.
- `skill-backend-verification`.
- `skill-code-standards`.

**Files And Symbols:**
- `docs/templates/work-brief-template.md`.
- `docs/templates/approval-package-example.md`.
- `docs/architecture.md`, `docs/getting-started.md`, and `docs/extending.md`.
- Tasks 1–4 implementation and focused tests.

**Dependencies:**
- Tasks 0–4.

**Authority:**
- Preauthorized local actions: validate the foundation artifacts, run Milestone A checks, update the named documentation, and record acceptance evidence in this plan.
- Stop for: any missing restart proof, approval race, self-approval path, public gate bypass, or unresolved legacy-intent semantics.

**Steps:**
1. Validate the WorkBrief intake template against the canonical WorkBrief and
   typed `ExecutionIntent` schema.
2. Generate and validate one complete approval-package example against the
   exact recipe and approval contracts.
3. Run the Milestone A acceptance matrix: display race, self-approval,
   override/restart, public gate, internal bypass, legacy explicit override,
   equivalent fingerprint ordering, secret exclusion, and approval supersession.
4. Document the persisted work-directory layout:
   `brief.md`, `execution-recipe.json`, `execution-approval.json`,
   `analysis.json`, `stage-receipts.json`, and `artifacts/`.
5. Record Milestone A as accepted only after the fresh verification workflow
   returns `verified`; otherwise stop before Task 6.

**Verification:**
- `python -m pytest -q tests/test_approval_package.py tests/test_approval_persistence.py tests/test_approval_contract.py tests/test_work_brief_compatibility.py tests/test_execution_gate.py tests/test_public_execution_paths.py`
- `python -m compileall -q src tests evaluation`
- `python scripts/check_markdown_links.py README.md docs --tracked-docs`
- Display A → mutate recipe → approve A is rejected.
- Agent/runtime approval attempts are rejected by the trust boundary.
- Human override → save → restart → execute preserves the exact override.
- Secret/provider-token changes never enter the approval projection.
- Approval superseded during new dispatch denies that dispatch.

**Exit Criteria:**
- Milestone A is independently accepted: question → propose → inspect → edit
  → approve → restart → execute exact approved plan works without adding
  runtime intervention or reuse complexity.

### Task 6: Make selective reuse visible and explicitly overridable

**Purpose:**
- Expose existing receipt-based reuse as a reviewable proposal decision while
  preserving provenance and deterministic cache safety.

**Task Function:**
- Reuse policy, receipt metadata, and fresh-execution control.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers visible reuse, `Run Fresh`, provenance display, and the verdict's
  requirement that caching never become invisible execution behavior. This is
  the first Milestone B capability and starts only after Milestone A acceptance.

**Required Skills:**
- `skill-code-standards`.
- `skill-backend-verification`.
- `skill-test-driven-development`.

**Files And Symbols:**
- `src/foresight_os/persistence/analysis_store.py`: extend `StageReceipt`
  only with durable provenance needed to explain reuse, such as source revision,
  creation timestamp, and reuse decision metadata; preserve `reusable_for`.
- `src/foresight_os/runtime/workflow.py`: keep semantic/policy fingerprint
  separation and accept a run-local fresh-stage set without weakening receipt
  validation.
- `src/foresight_os/controller/proposal.py` and
  `src/foresight_os/artifacts/approval.py`: add per-stage reuse candidates,
  source revision, age, fingerprint checks, and `Reuse`/`Run Fresh` choices.
- `src/foresight_os/persistence/analysis_store.py`: record selected fresh
  stages in the approved execution decision or its explicit run-local decision,
  not in the WorkBrief and not in a second approval store.
- `tests/test_selective_reuse.py`, `tests/test_stage_inputs.py`, and updates
  to `tests/test_approval_package.py`.

**Dependencies:**
- Task 5; reuse is not admitted until Milestone A is accepted.

**Authority:**
- Preauthorized local actions: modify receipt/reuse code and named tests while preserving existing committed/provenance checks and source immutability.
- Stop for: a proposal to reuse incomplete, uncommitted, mismatched, or provenance-incomplete output, or a need for a cross-investigation cache.

**Steps:**
1. Add only the metadata required to explain why a receipt is reusable; do not
   change the existing fingerprint predicates or allow incomplete receipts.
2. Have proposal generation classify each stage as reusable, fresh, blocked, or
   unavailable with the exact failing fingerprint/provenance reason.
3. Let the human select `Run Fresh` for individual reusable stages. Bind that
   choice to the approved execution request and pass it as run-local workflow
   context.
4. Ensure a fresh run creates a new committed receipt and does not mutate the
   prior receipt or source workbook.
5. Reassess dependent descendants when `Run Fresh` changes an upstream result;
   do not silently reuse descendants whose inputs now differ.
6. Render reuse provenance in both primary summary and detailed stage views.

**Verification:**
- `python -m pytest -q tests/test_selective_reuse.py tests/test_stage_inputs.py tests/test_approval_package.py`
- A valid committed receipt is offered for reuse with source revision, age,
  unchanged inputs, unchanged skill hash, unchanged capability fingerprint, and
  reusable status.
- A pending, incomplete, stale, or provenance-incomplete receipt is never
  offered as reusable.
- `Run Fresh` bypasses only the selected stage cache, preserves the old receipt,
  and writes a fresh receipt after successful execution.
- A fresh upstream result invalidates or reruns affected descendants according
  to the existing dependency rules; unaffected descendants remain reusable.

**Exit Criteria:**
- Reuse is visible, explainable, provenance-bound, and overridable per stage
  without weakening the existing receipt contract.

### Task 7: Add bounded runtime intervention and material reapproval

**Purpose:**
- Let humans intervene in an identified run without turning every runtime
  adjustment into an approval prompt or silently changing authorized scope.
  Cross-process pause/resume is implemented only when an existing control
  transport can address the run; otherwise it remains an explicit deferred
  boundary rather than a newly invented transport.

**Task Function:**
- Runtime control, materiality classification, and dependency-aware revision.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers the explicit adaptation envelope, materiality-based reapproval,
  observable progress, same-process or transport-backed pause/cancel,
  revise-remaining-work, and reassessment.

**Required Skills:**
- `skill-backend-verification`.
- `skill-code-standards`.
- `skill-test-driven-development`.

**Files And Symbols:**
- `src/foresight_os/runtime/execution_gate.py`: classify runtime changes as
  inside-envelope or reapproval-required.
- `src/foresight_os/runtime/orchestration.py` and
  `src/foresight_os/runtime/workflow.py`: add typed run controls/events for
  explicit run ID, current stage, participants, pattern, capability calls,
  reuse, elapsed time, resource counts, blockers, and remaining stages; pause
  before starting new work and settle cancellation.
- `src/foresight_os/controller/proposal.py`: add projection diff and
  `requires_reapproval` for budget, provider, scope, deliverable, stage,
  pattern, and permission changes.
- `src/foresight_os/persistence/invalidation.py` and existing domain
  invalidation helpers: reuse dependency-aware invalidation/reassessment for
  revised remaining work.
- `src/foresight_os/cli.py`: add `pause`, `cancel`, and `revise` commands with
  explicit status output.
- New `tests/test_execution_intervention.py` plus updates to
  `tests/test_invalidation.py`, `tests/test_runtime_boundaries.py`, and
  `tests/test_approval_contract.py`.

**Dependencies:**
- Tasks 5–6; runtime intervention is Milestone B follow-on work.

**Authority:**
- Preauthorized local actions: add run-scoped control state/events, materiality
  classification, revision proposal generation, and deterministic boundary
  tests. Add CLI controls only against an existing local or transport-backed
  run-control boundary.
- Stop for: a revision that expands external access, scope, budget, deliverables,
  or write capability without a new ApprovalRecord; a CLI command that cannot
  identify and address the intended run; an invented cross-process transport;
  or any cancellation path that loses completed evidence/receipts.

**Steps:**
1. Encode the approved adaptation envelope with allowed operations such as
   bounded retry, compatible participant substitution, reduced concurrency,
   dependency-safe topology adjustment, and verified evidence reuse.
2. Classify retries, participant-instance changes, lower limits, and approved
   topology reductions as non-material only when the envelope permits them.
3. Classify increased budget, new provider, expanded geography, write access,
   changed decision question, material stage changes, new deliverable, and
   external research added to a no-external plan as reapproval-required.
4. Implement pause so no new stage starts after the control is observed; finish
   or settle current owned work according to the existing cancellation contract.
   If the process is separate from the controller, require the existing control
   transport and explicit run ID; do not imply that a CLI flag can signal an
   unrelated process.
5. Implement cancel so completed results/receipts remain durable and the run
   ends with an explicit canceled status rather than success.
6. Implement revise so completed work is checked for material validity, affected
   outputs are invalidated through existing dependency logic, and a new recipe
   is generated only for remaining work.
7. Surface the runtime event stream through the local API/CLI only where the
   run-control boundary can prove ownership and addressability; do not claim an
   observability platform or cross-process control that is not implemented.

**Verification:**
- `python -m pytest -q tests/test_execution_intervention.py tests/test_invalidation.py tests/test_runtime_boundaries.py tests/test_approval_contract.py`
- Pause prevents new stage dispatch and preserves completed stage receipts.
- Cancel settles owned resources and records canceled status without claiming
  analytical acceptance.
- Revise preserves unaffected completed analysis, invalidates affected records,
  and produces a new approval requirement when the boundary changes.
- A retry inside the approved envelope requires no reapproval, while a
  participant/topology change outside the envelope requires reapproval.
- Materiality classification matches the approved table: retry and compatible
  substitution do not reapprove inside policy; provider, scope, budget, write,
  question, stage, deliverable, and external-access changes do.

**Exit Criteria:**
- Humans can observe and intervene within a clearly bounded execution envelope;
  material changes stop at the approval boundary and revised analysis preserves
  existing invalidation/reassessment semantics.

### Task 8: Align documentation and complete repository verification

**Purpose:**
- Make the canonical ownership model discoverable and prove the implementation
  remains compatible, deterministic, and within scope.

**Task Function:**
- Maintained documentation and final verification/reconciliation.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers maintained guidance, acceptance evidence, compatibility, and final
  scope reconciliation.

**Required Skills:**
- `skill-verification-before-completion`.
- `skill-code-standards`.

**Files And Symbols:**
- `docs/architecture.md`: update the flow and canonical-owner sections.
- `docs/getting-started.md`: document local propose/approve/execute/revise
  commands and explicit blocked external-provider behavior.
- `docs/extending.md`: document where proposal policy, approval rendering,
  capability boundaries, and analytical state changes belong.
- `README.md`: update only the affected command/architecture references.
- All files declared in Tasks 0–7 and the final Git diff.

**Dependencies:**
- Tasks 0–7, with Milestones A and B accepted independently before final
  reconciliation.

**Authority:**
- Preauthorized local actions: update the named maintained docs, run all repository verification commands, inspect the final diff, and record immutable local evidence in this plan.
- Stop for: broken local links, failed required checks, untracked product changes outside the declared targets, or any need to delete/reset pre-existing workspace outputs.

**Steps:**
1. Document that `WorkBrief`, `ExecutionRecipe`, `ApprovalRecord`, and
   `AnalysisState` are distinct owners and that `ApprovalPackage` is derived.
2. Document the local Markdown/JSON review surface and the absence of a browser
   UI in this increment.
3. Document legacy brief migration, approval fingerprint behavior, reuse/fresh
   choices, material reapproval, pause/cancel/revise semantics, and blocked
   external boundaries.
4. Run the focused suites from Tasks 1–7, then the required full suite and
   compile check.
5. Run the Markdown-link checker, `git diff --check`, and final status/diff
   inspection. Confirm unrelated `build/`, `data/`, `egg-info/`, and `work/`
   outputs remain untouched.
6. Record exact command results and any explicit blocked external evidence in
   the plan ledger. Change plan status only through the completion workflow
   after fresh verification returns `verified`.

**Verification:**
- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `python scripts/check_markdown_links.py README.md --tracked-docs`
- `git diff --check`
- `git status --short --branch`
- `git diff --stat`
- `python -m foresight_os.cli --help`

**Exit Criteria:**
- Documentation matches the implemented owners, all required checks pass, the
  final diff contains only declared implementation/docs/tests plus this plan,
  and no external delivery is claimed without a durable receipt.

### Post-completion live probe and defect correction

The local CLI probe found one in-scope defect after Task 8 completion:

- **Reproduction:** `revise` changed `max_total_agent_calls` from `3` to `4`,
  then a second `propose` silently rewrote the persisted recipe back to `3`.
- **Root cause:** `src/foresight_os/cli.py` always called
  `build_execution_recipe(brief)` and overwrote `execution-recipe.json`, even
  when a human-edited exact recipe already existed.
- **Patch:** `propose` now validates and re-renders an existing persisted
  recipe; it generates and saves a recipe only when one does not exist. An
  invalid persisted recipe returns visible `DRAFT` diagnostics instead of
  being replaced.
- **Regression proof:**
  `tests/test_approval_package.py::test_propose_rerenders_persisted_recipe_without_dropping_revision`
  fails before the patch and passes after it.
- **Live evidence:** a fresh local CLI run preserved the revised budget as
  `4` through reproposal, approval, and execution; execution returned two
  outputs with `settled=true`. Stale approval and superseded-recipe execution
  were rejected with exit code `2`. Separate-process pause/cancel correctly
  returned `BLOCKED_EXTERNAL` because no control transport exists.
- **External boundary:** no provider authentication, external call, or write
  was performed; those remain explicitly transport- and credential-gated.

## Verification

Task-local proof must be accepted before the next dependent task starts. The
final verification set is:

- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `python scripts/check_markdown_links.py README.md --tracked-docs`
- `python -m foresight_os.cli --help`
- `git diff --check`
- `git status --short --branch`
- `git diff --stat`

The implementation is not verified by package rendering alone. Fresh proof
must include:

- direct gate success and rejection for missing/stale/rejected approval;
- every public execution command and library entrypoint reaches the shared gate;
  only an explicit internal/test or evaluation-probe bypass can reach the
  low-level runtime primitive directly;
- display A → mutate the recipe → approve A is rejected, and a superseded
  approval blocks a new dispatch under the investigation lock;
- runtime, participant, or agent self-approval attempts are rejected by the
  approval trust boundary;
- an override survives save, restart, and execution without being normalized
  away, and legacy `execution_pattern_override` remains a mandatory required
  intent after migration;
- invalid override, unavailable capability, insufficient participant, and
  budget failure paths;
- atomic approval persistence and legacy brief migration;
- reuse, `Run Fresh`, source immutability, and provenance-completeness paths;
- stale reuse follows the approved fallback (`stop` or `run_fresh`), while
  `Run Fresh` reassesses affected descendants;
- pause, cancel, material reapproval, revision, invalidation, and resource
  settlement paths;
- retry inside the approved envelope requires no reapproval, while participant
  or topology changes outside the envelope require reapproval;
- deterministic ordering-independent equivalent-input fingerprints, stable
  package output, and proof that secrets/provider tokens are never serialized.

No provider authentication, external web call, external write, publication,
or credential-bearing fixture is required for this plan's verified state.

## Completion Criteria

The plan is ready for completion verification when:

1. Tasks 0–8 have completed with accepted task-local proof recorded in the
   ledger and no unresolved blocker; Milestone A is accepted before Milestone B
   begins, and Milestone B is accepted before final reconciliation.
2. WorkBrief no longer serializes resolved execution configuration, while
   legacy briefs remain readable through explicit migration.
3. ExecutionRecipe is complete, explainable, validated, and deterministic for
   the same brief/capability state.
4. ApprovalPackage is derived, ApprovalRecord is durable, the projection hash
   binds material brief/recipe/envelope fields, and the shared gate blocks stale
   or unauthorized execution.
5. Reuse is visible and selectively overridable without weakening receipt,
   provenance, fingerprint, or source-immutability checks.
6. Pause, cancel, and revise preserve completed evidence, settle resources,
   invalidate affected analytical outputs, and require reapproval for material
   boundary changes without inventing cross-process control transport.
7. Existing analytical state, review validity, report truthfulness, optional
   provider boundaries, and low-level runtime tests remain intact.
8. The full test, compile, Markdown-link, diff, and scope checks pass.
9. `skill-verification-before-completion` returns `verified` before this plan
   changes from `proposed`/`active` to `completed`.

## Self-Review

- **Spec coverage:** The verdict's canonical ownership, progressive intake,
  complete proposal, inspection, editing, fingerprinted approval, adaptation
  envelope, material reapproval, visible reuse, execution visibility,
  pause/cancel/revise, and reassessment requirements map to Tasks 1–8, with
  Milestone A and Milestone B acceptance separated.
- **Repository fit:** Existing WorkBrief, recipe, capability, receipt,
  invalidation, MAF, and AnalysisState owners are extended; no second runtime
  or analytical store is introduced.
- **Ordering:** Compatibility baseline precedes contracts; contracts precede
  proposal generation; proposal generation precedes approval; approval
  precedes Milestone A acceptance; reuse and intervention follow Milestone A;
  documentation and full verification follow all producers.
- **Shared writes:** The plan is inline sequential because model, controller,
  persistence, and runtime owners overlap. No parallel lane is justified.
- **Scope control:** Rich UI, external mutation, provider setup, and unrelated
  workspace cleanup are explicit non-goals and stop conditions.
