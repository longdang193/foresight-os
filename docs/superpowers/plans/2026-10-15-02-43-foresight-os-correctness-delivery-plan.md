---
layer: change
artifact_type: plan
contract_version: "1"
status: active
template_id: implementation-plan
name: foresight-os-correctness-and-delivery
targets:
  - src/foresight_os/analysis/result_committer.py
  - src/foresight_os/analysis/reviewer.py
  - src/foresight_os/artifacts/brief.py
  - src/foresight_os/artifacts/presentation.py
  - src/foresight_os/controller/policy.py
  - src/foresight_os/controller/recipes.py
  - src/foresight_os/domain/models.py
  - src/foresight_os/domain/validation.py
  - src/foresight_os/persistence/analysis_store.py
  - src/foresight_os/runtime/capabilities.py
  - src/foresight_os/runtime/execution_gate.py
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/schemas/analysis.schema.json
  - src/foresight_os/schemas/execution_recipe.schema.json
  - src/foresight_os/schemas/work_brief.schema.json
  - tests/test_capabilities.py
  - tests/test_execution_gate.py
  - tests/test_execution_persistence.py
  - tests/test_host_delivery_routing.py
  - tests/test_host_wayfinding_routing.py
  - tests/test_ncc_execution.py
  - tests/test_orchestration_patterns.py
  - tests/test_presentation_spec.py
  - tests/test_research_needs.py
  - tests/test_result_committer.py
  - tests/test_review_hardening.py
  - tests/test_skill_package.py
  - tests/test_stage_inputs.py
  - tests/fixtures/wayfinding/ncc-2022-brief.yaml
  - .agents/skills/foresight-delivery/SKILL.md
  - .agents/skills/foresight-execution/SKILL.md
  - AGENTS.md
  - docs/architecture.md
  - docs/extending.md
  - docs/superpowers/plans/2026-10-15-02-43-foresight-os-correctness-delivery-plan.md
---

# ForesightOS Correctness And Delivery

## Goal

Close the remaining correctness gaps exposed by the NCC review before claiming
business-analysis completion, then add one renderer-neutral
`foresight-delivery` host procedure for turning an accepted `PresentationSpec`
into one explicitly requested local or external delivery. Preserve
`AnalysisState` as the only analytical source of truth, keep participant
outputs provisional, keep review and acceptance separate from persistence, and
leave cross-process pause/cancel deferred.

## Verdict Review

The verdict is accepted with four repository-truth corrections:

1. The one-record `CanonicalStageResult` hash defect is already fixed in the
   merged code. Keep that fix and add one-evidence, one-claim, and
   one-calculation regressions.
2. No runtime path currently creates durable `ReviewRecord` values from generic
   analyst output. Keep review persistence in `analysis.reviewer`; add a
   negative boundary test instead of an unused review registry.
3. `foresight-delivery` is a host procedure under `.agents/skills/`, not a
   participant skill. Do not add PowerPoint or Canva to the packaged manifest.
4. Do not claim a finished PPTX or Canva design without a renderer/adapter that
   writes or durably saves the artifact and returns matching proof.

## Implementation Outcomes

### Correct canonical execution

`analysis-stage-result/v1` has one decoder and one normalizer. Approved
research needs and source hints reach `StageInput`; references resolve only
from an authorized dependency closure; participant records remain `UNASSESSED`
and `CURRENT`; supported calculations are deterministic; model-authored paths
never become durable artifacts.

### Correct multi-participant semantics

Sequential, handoff, group-chat, and concurrent execution use explicit stage
synthesis instead of “last participant output wins.” Concurrent branches
execute independently and commit one aggregated typed result. Runtime and
preflight use the same capability context, and the NCC brief describes
investigation work rather than forcing topology unless a human authored that
requirement.

### Explicit delivery

Deliverable status uses typed predicates. `PresentationSpec` keeps the current
six-slide default and adds bounded case-competition and supplied-template
profiles with readable citations and derived reassessment signals.
`foresight-delivery` validates accepted state and spec freshness, routes to one
requested adapter, preserves external approval, and reports blocked/failed
delivery truthfully.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-executing-plans`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve existing generated and untracked files
- Commit policy: `no commits during execution`; request Git disposition after fresh completion verification
- Preauthorized local actions: inspect listed owners, edit listed files, add focused tests, run declared local checks, and run bounded authorized NCC probes without persisting credentials
- User-approval actions: push, merge, external Canva mutation, publication, destructive cleanup, credential changes, and deliverable submission
- Parallel ownership: none; shared contracts, workflow, presentation, and schemas are serialized owners
- Sequential fallback: complete Tasks 1 through 7 in order in one lead workspace

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/canonical-architecture-20261014` (current authorized checkout)
- Base commit: `3e82069e201796e6f8e6485fba7be15df1a54992` (current checkout HEAD)
- Expected workspace: current checkout with pre-existing untracked `build/`, `data/`, `work/`, and `src/foresight_os.egg-info/` preserved
- Next action: obtain fresh execution-package approval for Task 7 before any NCC provider call
- Blockers: fresh approval is required for the regenerated NCC execution package; live provider and renderer proof remain capability-gated

Before Task 1, record `git status --short --branch`, branch, and HEAD in the
coordination evidence. If the checkout differs from the recorded branch or
commit, stop and reconcile the plan or obtain explicit workspace authority; do
not rebase, create a branch, or silently continue from a different base.

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `complete` | current | `lead controller` | none | focused contract tests | `43 passed` in stage/result/orchestration suites |
| Task 2 | `complete` | current | `lead controller` | Task 1 | reference/review tests | `43 passed`; dependency scope and review ownership covered |
| Task 3 | `complete` | current | `lead controller` | Task 2 | orchestration/gate tests | `31 passed`; typed synthesis and pre-call policy gate covered |
| Task 4 | `complete` | current | `lead controller` | Task 2 | calculation/persistence tests | `61 passed`; trusted workbook calculations, migration, typed deliverables |
| Task 5 | `complete` | current | `lead controller` | Task 3 | capability/NCC tests | `33 passed`; shared capability context and NCC intent boundary covered |
| Task 6 | `complete` | current | `lead controller` | Tasks 4–5 | presentation/routing tests | `18 passed`; profiles, citations, durable receipts, restart/failure proof |
| Task 7 | `active` | current | `lead controller` | Tasks 1–6 | full suite and NCC proof | fresh package approval required; fingerprint `5a27cf0b4c9e140c03d3ec2a61898090cbaa5d3ce75130b5e8580926c5e3f5d9` |

## Task Breakdown

### Task 1: Freeze the stage transport and input contract

**Purpose:** Make `analysis-stage-result/v1` one producer/consumer contract and
ensure approved research needs reach every participant prompt.

**Task Function:** Contract hardening and transport normalization.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared contract and high regression risk.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: focused tests plus final verification.

**Specification Coverage:** Native mappings, typed framework values, and JSON
text are accepted; prose and malformed JSON are rejected; optional lists
normalize consistently; `StageInput` carries `kind`, `query`, and `source_hint`.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `src/foresight_os/analysis/result_committer.py:analysis_stage_result_schema`, `src/foresight_os/analysis/result_committer.py:normalize_stage_result`, `src/foresight_os/runtime/workflow.py:_workflow_output_value`, `src/foresight_os/controller/recipes.py:StageInput`
- Modify: `src/foresight_os/analysis/result_committer.py:analysis_stage_result_schema`, `src/foresight_os/analysis/result_committer.py:normalize_stage_result`, `src/foresight_os/controller/recipes.py:StageInput`, `src/foresight_os/runtime/workflow.py:_workflow_output_value`, `src/foresight_os/runtime/workflow.py:run_recipe_async`
- Verify: `tests/test_result_committer.py`, `tests/test_orchestration_patterns.py`, `tests/test_stage_inputs.py`, `tests/test_research_needs.py`

**Dependencies:** Current `analysis-stage-result/v1` schema and native MAF
output unwrapping.

**Authority:**
- Preauthorized local actions: edit the listed contract/input owners, add focused tests, and run Task 1 checks.
- Stop for: a contract-version change, an undiscovered persisted consumer, or an external provider call.

**Steps:**
- [ ] Add one decoder at the workflow-to-committer boundary for current MAF
  wrappers, declared JSON text, and typed mappings; reject prose and malformed
  JSON.
- [ ] Derive provider schema requirements and normalizer defaults from the same
  field definition; preserve exact stage IDs and contract values.
- [ ] Add `research_needs` and source hints to `StageInput` serialization and
  stage fingerprints; the persisted recipe remains authoritative.
- [ ] Add regressions for each transport shape, omitted optional lists, prose,
  malformed JSON, and the installed MAF wrapper shape.

**Verification:**
- [ ] `python -m pytest -q tests/test_result_committer.py tests/test_orchestration_patterns.py tests/test_stage_inputs.py tests/test_research_needs.py`
- Expected: one decode path, prose rejection, and research needs in payloads
  and fingerprints.

**Exit Criteria:** Every stage receives the approved typed input and every
provider value reaches normalization through one decoder.

### Task 2: Constrain canonical references and review-owned truth

**Purpose:** Permit evidence-bearing cross-stage relations without exposing
unrelated state, while preventing participants from self-assigning review or
lifecycle authority.

**Task Function:** Dependency-scoped identity and review-boundary hardening.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: identity and acceptance invariants cross persistence and
  review owners and must remain serialized.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: focused normalization and review-boundary regressions.

**Specification Coverage:** Dependency-closure references, canonical-ID
precedence, `UNASSESSED`/`CURRENT` participant records, and no generic
`ReviewRecord` or human acceptance.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/analysis/result_committer.py:CanonicalResultCommitter`, `src/foresight_os/analysis/result_committer.py:normalize_stage_result`, `src/foresight_os/runtime/workflow.py:dispatch_stage`, `src/foresight_os/analysis/reviewer.py:parse_review_objections`
- Modify: `src/foresight_os/analysis/result_committer.py:CanonicalResultCommitter`, `src/foresight_os/analysis/result_committer.py:normalize_stage_result`, `src/foresight_os/runtime/workflow.py:dispatch_stage`, `src/foresight_os/analysis/reviewer.py:parse_review_objections`
- Verify: `tests/test_result_committer.py`, `tests/test_review_hardening.py`, `tests/test_review_records.py`

**Dependencies:** Task 1's decoder and `StageInput` dependency list.

**Authority:**
- Preauthorized local actions: edit the listed identity/review owners, add focused regressions, and run Task 2 checks.
- Stop for: changed human acceptance semantics, a new durable review store, or a provider mutation.

**Steps:**
- [ ] Build the committer's existing-record view from dependency stage receipt
  references and local aliases; never expose all canonical state to a stage.
- [ ] Preserve canonical-ID precedence for evidence, calculations, records,
  artifacts, and relationships; reject same-ID/different-content conflicts.
- [ ] Force participant assessment to `UNASSESSED`, reject lifecycle changes
  away from `CURRENT`, and reject review-only fields from the generic contract.
- [ ] Keep `ReviewRecord` creation in the existing review boundary and prove a
  reviewer-shaped generic result cannot mark a record accepted.
- [ ] Add tests for authorized and undeclared cross-stage references plus
  canonical/provider alias collisions.

**Verification:**
- [ ] `python -m pytest -q tests/test_result_committer.py tests/test_review_hardening.py tests/test_review_records.py`
- Expected: authorized references resolve, undeclared records fail, canonical
  IDs win, and findings remain pending review.

**Exit Criteria:** A stage consumes only its approved dependency closure and
cannot manufacture review acceptance or supersession.

### Task 3: Add explicit stage synthesis and restore safe Concurrent execution

**Purpose:** Replace last-response-wins behavior with one synthesis boundary
for sequential, handoff, group-chat, and concurrent multi-participant stages.

**Task Function:** Multi-participant aggregation and serialized canonical commit.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: workflow semantics and persistence ordering are coupled.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: orchestration-pattern regressions cover all multi-output
  paths.

**Specification Coverage:** Concurrent provider work, one synthesized typed
result, explicit partial branch failure, and pre-call rejection without a
synthesis rule.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/workflow.py:_run_native_stage`, `src/foresight_os/runtime/workflow.py:dispatch_stage`, `src/foresight_os/runtime/metrics.py:ConcurrentAggregate`, `src/foresight_os/runtime/execution_gate.py:_preflight_recipe`, `src/foresight_os/controller/recipes.py:RecipeStage`
- Modify: `src/foresight_os/runtime/workflow.py:_run_native_stage`, `src/foresight_os/runtime/workflow.py:dispatch_stage`, `src/foresight_os/runtime/metrics.py:ConcurrentAggregate`, `src/foresight_os/runtime/execution_gate.py:_preflight_recipe`, `src/foresight_os/controller/recipes.py:RecipeStage`, `src/foresight_os/controller/policy.py:_recipe_for_patterns`, `src/foresight_os/schemas/execution_recipe.schema.json`
- Verify: `tests/test_orchestration_patterns.py`, `tests/test_execution_gate.py`, `tests/test_maf_fit.py`

**Dependencies:** Task 2's provisional-result and reference rules.

**Authority:**
- Preauthorized local actions: edit the listed workflow/recipe/policy/metrics owners, add orchestration regressions, and run Task 3 checks.
- Stop for: a second orchestration engine, cross-process pause/cancel, or an unbounded retry/branch policy.

**Steps:**
- [ ] Add and persist an explicit serialized synthesis policy on `RecipeStage`;
  reject multi-output stages without it before participant calls.
- [ ] Declare the synthesis policy in `execution_recipe.schema.json`, preserve
  backward-compatible defaults for legacy recipes, and include the normalized
  policy in recipe approval and stage-receipt fingerprints.
- [ ] Aggregate compatible `analysis-stage-result/v1` branch outputs
  deterministically, preserve participant IDs, and record branch failures.
- [ ] Route reviewer/challenge objections to the existing review boundary and
  require bounded synthesis for analytical persistence.
- [ ] Remove the unconditional Concurrent admission rejection; keep branch
  execution parallel and canonical commit serialized under the store lock.
- [ ] Add save/load and approval round-trip coverage, plus a regression proving
  a synthesis-policy change invalidates receipt reuse before provider calls.
- [ ] Add success, partial-failure, analyst-plus-reviewer, handoff, group-chat,
  and missing-synthesis regressions.

**Verification:**
- [ ] `python -m pytest -q tests/test_orchestration_patterns.py tests/test_execution_gate.py tests/test_maf_fit.py`
- Expected: concurrent work runs in parallel, one canonical commit is written,
  partial failure is explicit, and unsupported paths fail before calls.

**Exit Criteria:** Every enabled pattern has an output owner and one canonical
commit path; cross-process pause/cancel remains deferred.

### Task 4: Give calculations, artifact requests, and deliverables explicit owners

**Purpose:** Prevent model-invented numerical truth and durable files from
entering `AnalysisState`, then replace fuzzy deliverable matching with typed
evidence predicates.

**Task Function:** Deterministic verification and artifact-boundary design.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: domain persistence and local calculation capabilities share
  the trust boundary.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: calculation, persistence, and deliverable regressions.

**Specification Coverage:** Supported calculations are recomputed; unsupported
results are `NOT_VERIFIED`; workbook locators are checked; participants emit
transient artifact requests; only system renderers create durable artifacts;
unknown deliverables remain `NOT_VERIFIED`.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/local_toolbelt.py:calculation`, `src/foresight_os/analysis/result_committer.py:StageAnalyticalResult`, `src/foresight_os/domain/models.py:CalculationRecord`, `src/foresight_os/domain/models.py:Artifact`, `src/foresight_os/runtime/workflow.py:_refresh_execution_status`
- Modify: those owners plus `src/foresight_os/artifacts/brief.py`, `src/foresight_os/schemas/analysis.schema.json`, `src/foresight_os/persistence/analysis_store.py`, and `src/foresight_os/domain/validation.py`
- Verify: `tests/test_result_committer.py`, `tests/test_execution_persistence.py`, `tests/test_ncc_execution.py`

**Dependencies:** Tasks 1–2's decoder and dependency-scoped records.

**Authority:**
- Preauthorized local actions: edit the listed calculation/artifact/status owners, add regressions, and run Task 4 checks.
- Stop for: a second analytical store, provider-authored file writes, or external artifact mutation.

**Steps:**
- [ ] Reuse or extract one pure evaluator from `local_toolbelt.calculation`
  and compare operation, inputs, units, and output before commit.
- [ ] Resolve supported numerical inputs from the approved workbook measurement
  identified by trusted hash, sheet, range/cell, and units; treat model excerpts
  as context only. Require trustworthy formula-cache values for formula cells,
  and retain `NOT_VERIFIED` when the workbook value, unit, cache, or coordinate
  cannot be proven.
- [ ] Persist explicit `VERIFIED` versus `NOT_VERIFIED` calculation status and
  preserve it through reload. Assign the `CalculationRecord` field, analysis
  schema, `AnalysisStore` loader/writer, and legacy-state migration default;
  legacy records must default to `NOT_VERIFIED`, never `VERIFIED`.
- [ ] Validate workbook locators against approved workbook hash and actual
  sheet/range and authoritative cell values; record a blocking limitation for
  fabricated locators, false excerpts, changed workbook bytes, unavailable
  formula caches, or unit mismatches.
- [ ] Replace provider artifact paths with transient typed requests containing
  kind, format/profile, title, and source record IDs; only system delivery
  creates `Artifact` values.
- [ ] Add a typed deliverable predicate map for analytical records, verified
  calculations, reports, presentation outlines, verified PPTX, and Canva
  receipts; unknown labels return `NOT_VERIFIED`.
- [ ] Update runtime status refresh and NCC persistence tests so `SETTLED` and
  `PERSISTED` never imply deliverable completion.
- [ ] Include verification metadata in calculation fingerprints and test that
  changing it prevents stale receipt reuse.

**Verification:**
- [ ] `python -m pytest -q tests/test_result_committer.py tests/test_execution_persistence.py tests/test_ncc_execution.py`
- Expected: arithmetic mismatch and invalid locators cannot become verified;
  model paths are not durable; statuses use explicit predicates.

**Exit Criteria:** Numerical truth and durable artifact truth have system-owned
verification paths.

### Task 5: Unify capability preparation and correct NCC execution intent

**Purpose:** Make preflight capability truth equal runtime dispatch truth and
ensure Wayfinding records the investigation rather than forcing topology.

**Task Function:** Capability context consolidation and recipe selection.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared preflight/runtime behavior and NCC admission.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: capability and recipe-selection tests.

**Specification Coverage:** One `prepare_capability_context(...)` path feeds
preflight and runtime; Wayfinding requirements are not human mandates;
topology derives from stage dependencies and task shape; the NCC graph remains
source audit, category screen, channel screen, joint validation, challenge,
and synthesis.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/capabilities.py:CapabilityResolver`, `src/foresight_os/runtime/execution_gate.py:_preflight_recipe`, `src/foresight_os/runtime/workflow.py:run_recipe_async`, `src/foresight_os/controller/policy.py:select_recipe`, `tests/fixtures/wayfinding/ncc-2022-brief.yaml`
- Modify: those owners plus `tests/fixtures/wayfinding/ncc-2022-brief.yaml`
- Verify: `tests/test_capabilities.py`, `tests/test_execution_gate.py`, `tests/test_ncc_wayfinding.py`, `tests/test_controller_selection.py`, `tests/test_host_wayfinding_routing.py`

**Dependencies:** Task 3's synthesis policy and Task 4's typed capability
requirements.

**Authority:**
- Preauthorized local actions: edit capability/controller/fixture/routing owners, add focused tests, and run Task 5 checks.
- Stop for: new credentials, a provider connection, a topology requirement not explicitly authored by a human, or cross-process pause/cancel changes.

**Steps:**
- [x] Extract `prepare_capability_context` with local, hosted/MCP, adapter,
  approval, scope, and fingerprint inputs.
- [x] Call it from `_preflight_recipe` and `run_recipe_async`; unavailable and
  unauthorized capabilities fail before provider calls.
- [x] Remove NCC fixture hard `sequential`/`spreadsheet_read` intent unless a
  test identifies it as human-authored; retain source/data needs in stages.
- [x] Add the NCC dependencies and synthesis stage without encoding vendor or
  topology requirements in the brief.
- [x] Distinguish host procedures from the packaged participant manifest in
  routing tests.

**Verification:**
- [x] `python -m pytest -q tests/test_capabilities.py tests/test_execution_gate.py tests/test_ncc_wayfinding.py tests/test_controller_selection.py tests/test_host_wayfinding_routing.py`
- Expected: preflight and runtime resolve the same capabilities, the NCC recipe
  remains valid without Wayfinding forcing topology, and host procedures stay
  outside the participant manifest.

**Exit Criteria:** Runtime and preflight share one capability-context builder,
and the controller owns execution-pattern selection.

### Task 6: Add the presentation contract and `foresight-delivery` boundary

**Purpose:** Prepare an accepted revision for one explicitly requested renderer
or destination without coupling vendor procedures to participant skills.

**Task Function:** Renderer-neutral presentation contract and host delivery.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: artifact ownership, external approval, and provenance share
  one canonical boundary.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: presentation/routing regressions and artifact verification.

**Specification Coverage:** `executive-six` remains default; `case-competition`
is capped at 20 slides; `user-template` requires a supplied structure; notes
resolve readable workbook/web citations; reassessment derives monitoring,
disconfirmation, and kill signals; Canva and PPTX receipts prove durable
delivery.

**Required Skills:** `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/artifacts/presentation.py:PresentationSpec`, `src/foresight_os/artifacts/presentation.py:compile_presentation`, `src/foresight_os/artifacts/presentation.py:publish_to_canva`, `.agents/skills/foresight-execution/SKILL.md`, `AGENTS.md`
- Modify: those presentation/host owners plus `src/foresight_os/domain/models.py:Artifact`, `src/foresight_os/persistence/analysis_store.py`, `.agents/skills/foresight-delivery/SKILL.md`, `docs/architecture.md`, and `docs/extending.md`
- Verify: `tests/test_presentation_spec.py`, `tests/test_host_delivery_routing.py`, `tests/test_skill_package.py`

**Dependencies:** Tasks 4–5's system-owned artifact requests, typed
deliverables, and host routing.

**Authority:**
- Preauthorized local actions: edit presentation owner, create host procedure, add static routing/receipt tests, and run Task 6 checks.
- Stop for: Canva mutation, external publication, vendor skills in the manifest, or a new PPTX dependency without an approved runtime decision.

**Steps:**
- [x] Add bounded presentation profiles while preserving deterministic default
  six-slide output.
- [x] Resolve evidence IDs to readable source citations and derive the
  reassessment slide from canonical monitoring/disconfirmation fields.
- [x] Harden Canva receipts with provider, successful state, design ID,
  revision, spec hash, and parseable verification timestamp; define a typed
  PPTX renderer receipt without claiming an absent implementation.
- [x] Persist the verified delivery receipt atomically through the existing
  `AnalysisState.artifacts`/`AnalysisStore` owner and bind it to the artifact
  ID, accepted presentation-spec hash, destination, and provider receipt. A
  provider success without local persistence remains failed or blocked, and
  restart reconstruction must reject missing, stale, or mismatched proof.
- [x] Create `.agents/skills/foresight-delivery/SKILL.md` to require accepted
  state, current spec, one requested destination, verified receipt, and an
  explicit blocked status when the adapter is unavailable.
- [x] Route execution and delivery through the generated host-procedure guidance
  and maintained architecture/extending docs; add
  `tests/test_host_delivery_routing.py`; keep both host procedures out of the
  participant manifest.
- [x] Add regressions for restart reconstruction, missing/mismatched receipts,
  and successful provider call followed by local persistence failure; do not
  introduce a second analytical store.

**Verification:**
- [x] `python -m pytest -q tests/test_presentation_spec.py tests/test_host_delivery_routing.py tests/test_skill_package.py`
- Expected: default output remains deterministic, bounded profiles validate,
  stale/provisional specs cannot deliver, invalid receipts fail, and routing
  does not change the participant registry.

**Exit Criteria:** An accepted `PresentationSpec` has one explicit verified
delivery boundary; unavailable adapters cannot be reported complete.

### Task 7: Execute and verify the real NCC closure path

**Purpose:** Prove the corrected pipeline against the approved workbook without
upgrading infrastructure evidence into unsupported business conclusions.

**Task Function:** Live boundary verification and evidence reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final integration and truthful status acceptance.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: final verification owns fresh evidence after local checks.

**Specification Coverage:** Actual workbook locators, verified calculations,
cross-stage traceability, reload/replay, pending review, and delivery status
that remains `NOT_STARTED` or `BLOCKED_EXTERNAL` without accepted state and a
matching adapter receipt.

**Required Skills:** `foresight-execution`, `foresight-delivery`, `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `tests/test_ncc_execution.py`, `tests/fixtures/wayfinding/ncc-2022-brief.yaml`, `README.md`, `.env` through the approved local runtime only
- Modify: `tests/test_ncc_execution.py`, `docs/architecture.md`, `README.md` only for verified behavior and commands
- Verify: `work/ncc-2022-cosluxe-vietnam/`, `src/foresight_os/persistence/analysis_store.py:AnalysisStore`, `src/foresight_os/runtime/workflow.py:run_recipe_async`

**Dependencies:** Tasks 1–6 completed with focused proof.

**Authority:**
- Preauthorized local actions: run the approved local NCC command, load existing `.env` credentials without printing/persisting them, inspect receipts/state, and update docs with verified behavior.
- Stop for: missing credentials, unavailable provider/renderer, analytical acceptance, external mutation, or a mismatch requiring brief changes.

**Steps:**
- [ ] Regenerate the NCC execution proposal after the Task 5 brief/recipe change,
  display the bounded package and its new fingerprint, and stop for fresh human
  execution approval. Plan approval alone does not approve the changed execution
  package; the old approval must be rejected.
- [ ] After fresh approval, run the bounded NCC command through the shared gate
  and record only redacted status, stage, receipt, and hash evidence. The exact
  command, input path, output directory, and approval fingerprint must be
  written into the task evidence without credentials or raw provider payloads.
- [ ] Confirm research needs/source hints reach every stage and receipt
  references reload with matching hashes.
- [ ] Confirm calculation verification resolves authoritative workbook values,
  formula-cache trust, units, and locators; false excerpts, changed workbook
  bytes, fabricated coordinates, and unavailable cache values remain
  `NOT_VERIFIED`. Also confirm dependency references, synthesis behavior, and
  truthful `PENDING_REVIEW` status.
- [ ] Run the newly approved NCC execution and fresh-process reload/idempotent
  replay; prove no false receipt or
  deliverable completion after restart.
- [ ] Invoke one delivery adapter only after review and human acceptance;
  otherwise retain `NOT_STARTED` or `BLOCKED_EXTERNAL` and do not generate a
  deck.

**Execution Evidence (2026-10-15):**
- Provider smoke through `.env` passed for the configured read-only MAF
  boundary; credentials and payloads were not printed or persisted.
- A bounded live control probe reproduced the provider/tool-loop defect: a
  no-tool structured call returned a typed value, while a one-tool call ended
  with an empty final assistant message. Replaying without tools and with the
  transient local tool result returned a typed value.
- The runtime now owns that bounded retry in the shared executor/native path;
  parser exceptions remain transient and canonical validation still decides
  whether a result is admissible. Exact duplicate relationship edges are
  canonicalized once; conflicting references remain rejected. Focused
  regressions cover both behaviors.
- The approved NCC command was run with `.env` and redacted evidence only.
  Tool calls completed, but the provider-generated stage payload remained
  invalid after the single approved correction round because it referenced an
  undeclared evidence record. The command therefore returned `FAILED`; no
  recommendation or artifact delivery was claimed.
- Fresh-process store inspection reloaded five committed stage receipts,
  provisional `PENDING_REVIEW` analytical state, workbook locators, and zero
  artifacts. This proves persistence/reload integrity, not analytical
  acceptance or deliverable completion.

**Task 7 Status:** `FAILED` at the provider-backed analytical boundary; local
contract, persistence, reload, and truthful-status checks are verified, while
full fresh NCC analytical closure remains unverified until the provider emits a
self-contained admissible stage result.

**Verification:**
- [x] `python -m pytest -q tests/test_ncc_execution.py tests/test_execution_persistence.py`
- [x] `python -m compileall -q src tests evaluation`
- [x] `python scripts/check_markdown_links.py README.md AGENTS.md .agents/skills/foresight-delivery/SKILL.md --tracked-docs` (`31` Markdown paths)
- [x] `python -m pytest -q` (passed)
- Expected: the live probe records complete redacted evidence or an explicit
  blocked/failed capability result; no limitation is silently upgraded.

**Exit Criteria:** Fresh proof covers local/live boundaries, truthful NCC
status, and delivery readiness. No recommendation or deck is claimed without
review, acceptance, and its own artifact proof.

## Verification

- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `python scripts/check_markdown_links.py README.md AGENTS.md docs .agents/skills/foresight-delivery/SKILL.md`
- `git diff --check`
- `git status --short --branch`

## Completion Criteria

The plan is ready for completion verification when:

1. Tasks 1–7 have task-local proof recorded in this plan.
2. Provider decoding, research inputs, dependency references, review ownership,
   synthesis, calculations, artifact requests, capabilities, and deliverables
   agree across code, schemas, tests, and docs.
3. Concurrent execution uses explicit synthesis and serialized commit; missing
   synthesis fails before provider calls.
4. `foresight-delivery` is routed as a host procedure and no vendor skill is
   added to the packaged manifest.
5. Presentation profiles, citations, reassessment, Canva receipts, and PPTX
   proof rules are tested without claiming unavailable adapters.
6. NCC evidence is redacted, reloadable, and labeled as infrastructure,
   analytical, review, acceptance, and delivery proof separately.
7. Cross-process pause/cancel is unchanged and deferred.
8. Coordination transitions from `proposed` to `active` only after approval and
   workspace reconciliation, then to `completed` only after
   `skill-verification-before-completion` returns `verified`.

A checked task box records progress only; it is not completion evidence.
