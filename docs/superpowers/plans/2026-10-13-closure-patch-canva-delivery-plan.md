---
layer: change
artifact_type: plan
contract_version: "1"
status: active
template_id: implementation-plan
name: foresight-os-closure-patch-canva-delivery
targets:
  - src/foresight_os/domain/models.py
  - src/foresight_os/controller/recipes.py
  - src/foresight_os/controller/policy.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/runtime/participants.py
  - src/foresight_os/domain/relationships.py
  - src/foresight_os/domain/challenge.py
  - src/foresight_os/analysis/reviewer.py
  - src/foresight_os/analysis/evidence_workflow.py
  - src/foresight_os/persistence/analysis_store.py
  - src/foresight_os/persistence/invalidation.py
  - src/foresight_os/artifacts/report.py
  - src/foresight_os/artifacts/presentation.py
  - src/foresight_os/runtime/capabilities.py
  - src/foresight_os/runtime/executors.py
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/controller/skills.py
  - src/foresight_os/domain/validation.py
  - src/foresight_os/runtime/metrics.py
  - evaluation/probes/run_selective_reuse_probe.py
  - evaluation/probes/optimization_measurement.py
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/compare_optimization_receipts.py
  - tests/
  - .github/workflows/ci.yml
  - README.md
---

# Foresight OS Closure Patch + Canva Delivery Plan

## Goal

Deliver one bounded closure patch on top of `origin/main` commit
`2fe7b4280d989f254647ba2acc142a271e2813f8`. Make declared stage objectives,
dependencies, specialists, and semantic inputs control execution; make
material dependency traversal, adversarial review, accepted-output
qualifications, and restartable reuse truthful; and add a vendor-neutral
presentation boundary that can feed an optional, human-approved Canva write.

This plan reconciles the user-provided verdict at
`C:\Users\HOANG PHI LONG DANG\.codex\attachments\7074a2fc-3278-4a0b-8116-065668830108\Pasted text.txt`
with current source. The verdict is directionally correct: the contracts are
present, but several are not yet runtime-controlling end to end. Task 0 must
first verify `origin/main` and recreate the closure branch from `2fe7b428`
before implementation claims are accepted.

Preserve the existing Controller, `RecipeStage` boundary, canonical
`AnalysisState`, typed `RelationIndex`, `StageReceipt`, five native MAF
patterns, deterministic workbook logic, and existing untracked workspace
outputs. Do not add another orchestration layer, a second dependency graph, a
`CompiledStage`, a presentation database, or a custom Canva server.

## Verdict Reconciliation

- **Accepted:** the P0 gaps are real in current source. `run_recipe_async`
  passes the caller's rolling `current` value in some pattern paths instead of
  assembling declared dependency outputs; `_stage_cache_key` omits objective,
  dependencies, expected result, research needs, limits, and model semantics;
  `_recipe_for_patterns` builds participants from generic recipe roles instead
  of preserving `WorkStage.participants`; `depends_on` maps material traversal
  in the wrong direction; `collect_material_inputs` gathers evidence and
  assumptions only from original targets; runtime execution does not persist
  successful `StageReceipt` records; and the selective-reuse probe seeds cache
  and receipts manually.
- **Accepted with bounded interpretation:** deterministic checks in
  `review_reasoning` remain valuable validators, but text heuristics must not
  be presented as proof that selected analytical skills ran. Record selected
  skill execution and typed objections while retaining deterministic structural
  validation as a separate layer.
- **Accepted:** accepted reports must retain uncertainty, confidence rationale,
  disconfirmation conditions, monitoring indicators, counterevidence, and
  unresolved non-blocking issues rather than hiding them after acceptance.
- **Accepted with external-boundary guard:** implement and validate the local
  `PresentationSpec` compiler and artifact dependency metadata. Canva remains
  optional; no local task may authenticate, publish, update, or export an
  external design without explicit human approval and a connected adapter.
- **Deferred:** P2 partial-slide Canva updates and arbitrary deck layouts. The
  first delivery uses one six-slide strategic decision template and full-spec
  regeneration.
- **Accepted operational correction:** execute on a dedicated closure branch
  with verified per-task checkpoint commits; keep push and merge approval-
  controlled. Task 0 captures any legacy performance reference, but the first
  apples-to-apples performance baseline is captured after Task 5's corrected
  measurement schema and before Task 6 optimizations.

## Implementation Outcomes

### Executable stage truth

Every declared `WorkStage` compiles to exactly one `RecipeStage` that preserves
requested specialist IDs, objective, dependencies, expected result, research
needs, skills, limits, and selected pattern. Runtime builds a deterministic
bounded `StageInput` from decision question, horizon, objective, expected
result, relevant constraints, and exactly the declared dependency outputs;
large canonical outputs travel as references plus bounded summaries/extracts.
Semantic, model, capability, authorization, and execution-policy identities
remain separately inspectable.

### Trustworthy material review

One typed `RelationIndex` exposes material, impact, support, and counterevidence
traversals with explicit direction. Material fingerprints include the complete
recursive analytical closure, evidence, assumptions, calculations, missing
inputs, counterevidence, skill identity, and review policy identity. Selected
skills produce recorded typed objections; deterministic validation remains
separate; `FindingView` and accepted reports preserve analytical qualifications.

### Automatic selective reuse

Successful stages that produce canonical records automatically persist atomic,
validated `StageReceipt` records. Raw conversational output is not reusable.
One fresh-process probe proves cold execution, automatic receipt creation,
restart reuse with zero new calls, dependency mutation, and impact-directed
reassessment of only affected descendants.

### Presentation boundary

`AnalysisState` and `FindingView` compile into a validated six-slide
`PresentationSpec` without introducing new analytical claims. The spec is
represented through the existing `Artifact` and relationship model, carries
revision and source fingerprints, and can be handed to a connected Canva
adapter only after local validation and human approval at the external-write
boundary.

### Evidence and efficiency

Performance receipts split model calls, local/tool calls, external requests,
and token/resource dimensions per accepted finding; compare workflow p95 by
pattern and mixed workflow; measure real resource snapshots during soak; and
cache immutable skill, schema-validator, relation-index, and workbook-derived
work where current owners already exist. CI tiers run inexpensive contract and
spec checks on PRs and reserve heavy closure evidence for nightly/release runs.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-plan-document-reviewer`, `skill-executing-plans`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `current workspace` on the dedicated closure branch; preserve existing untracked outputs
- Commit policy: `verified per-task checkpoint commits preauthorized; no push or merge without separate authorization`
- Preauthorized local actions: verify `origin/main`, create or recreate the declared closure branch, edit declared canonical sources and tests, create checkpoint commits after task-local proof, add the declared local presentation compiler and probes, run declared local checks, and preserve all existing untracked outputs
- User-approval actions: external Canva authentication or writes, publication, push, merge, dependency installation or major upgrades, destructive cleanup, deletion of preserved workspace outputs, and scope changes beyond this plan
- Parallel ownership: none; stage semantics, relation semantics, receipts, presentation provenance, and evidence schemas share canonical contracts and are serialized
- Sequential fallback: execute Tasks 0–7 in order, with Task 4 dependency-ready after Task 2 and Task 3 independent of Task 4; if a connector or real external boundary is unavailable, complete the local spec and record the external smoke as blocked rather than inventing success

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/closure-patch-canva-delivery`
- Base commit: `2fe7b4280d989f254647ba2acc142a271e2813f8` (`origin/main`)
- Expected workspace: tracked files clean after branch recreation from `origin/main`; preserve existing untracked `build/`, `data/`, `src/foresight_os.egg-info/`, and every existing `work/` output without staging, deletion, or cleanup
- Next action: correct performance/resource measurement semantics in Task 5, preserving Task 0–4 evidence
- Blockers: none known; Canva connector availability is an external-boundary condition, not a reason to block local compiler work

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 0 | `completed` | current | `unresolved` | none | baseline commands and verdict matrix | `work/closure-patch-canva-20261013/baseline/` |
| Task 1 | `completed` | current | `unresolved` | Task 0 | stage execution/fingerprint tests | focused suites passed |
| Task 2 | `completed` | current | `unresolved` | Task 0 | relation/review/finding tests | required suite passed; Task 2 checkpoint |
| Task 3 | `completed` | current | `unresolved` | Tasks 1–2 | fresh-process receipt lifecycle probe | automatic receipt/reuse probe passed; Task 3 checkpoint |
| Task 4 | `completed` | current | `unresolved` | Task 2 | presentation compiler/spec validation | focused suites passed; local Canva boundary remains disconnected by design |
| Task 5 | `active` | current | `unresolved` | Tasks 3–4 | performance/resource receipt comparison | pending |
| Task 6 | `pending` | current | `unresolved` | Tasks 2–5 | cache and CI/documentation checks | pending |
| Task 7 | `pending` | current | `unresolved` | Tasks 0–6 | final verification and acceptance evidence | pending |

## Task Breakdown

### Task 0: Reconcile the verdict against current main

**Purpose:**
- Establish a reproducible baseline on current `origin/main` `2fe7b428`, recreate the dedicated closure branch from that commit, distinguish already-fixed behavior from remaining gaps, and reserve a new disposable evidence root without touching preserved outputs.

**Task Function:**
- source/probe reconciliation and baseline evidence capture

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: lead controller retains authority until baseline scope is confirmed

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: baseline is validated by declared probes and source assertions

**Specification Coverage:**
- Current-main reconciliation, preservation of existing workspace outputs, and the verdict's P0/P1 priority order.

**Required Skills:**
- `skill-plan-document-reviewer`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/workflow.py:_stage_cache_key`, `run_recipe_async`
- Inspect: `src/foresight_os/controller/policy.py:_recipe_for_patterns`
- Inspect: `src/foresight_os/domain/relationships.py:RelationIndex`
- Inspect: `src/foresight_os/domain/challenge.py:collect_material_inputs`
- Inspect: `src/foresight_os/persistence/analysis_store.py:StageReceipt`
- Verify: `tests/`, `evaluation/probes/`, `git status --short --branch`

**Dependencies:**
- Verified `origin/main` at `2fe7b4280d989f254647ba2acc142a271e2813f8`; the pasted verdict is advisory evidence, not a replacement for source or tests.

**Authority:**
- Preauthorized local actions: fetch and verify `origin/main`, recreate `codex/closure-patch-canva-delivery` from the verified base, read source and tests, create only the new disposable evidence root, and run the listed baseline commands
- Stop for: tracked changes outside the declared branch workflow, deletion or mutation of existing untracked outputs, external access, or a base revision different from `2fe7b428`

**Steps:**
- [x] Step 1: Record `git status --short --branch`, `git fetch`, `git rev-parse origin/main`, and the existing untracked-output inventory; recreate the closure branch from `origin/main` only after preserving the inventory.
- [x] Step 2: Run `python -m pytest -q tests/test_controller_selection.py tests/test_research_needs.py tests/test_selective_reuse.py tests/test_finding_view.py tests/test_review_records.py`.
- [x] Step 3: Run the disputed selective-reuse probe into `work/closure-patch-canva-20261013/baseline/selective-reuse` and capture the legacy optimization receipt into `work/closure-patch-canva-20261013/baseline/optimization-legacy.json`; treat the latter as historical reference only, not as the baseline for Task 6 comparison.
- [x] Step 4: Write a machine-readable verdict matrix with each finding marked `confirmed`, `already fixed`, `not reproducible`, or `blocked`, including exact source/test evidence; delete no planned work unless the current source and tests prove it already satisfied.

**Verification:**
- [x] Baseline commands complete and outputs are stored only under `work/closure-patch-canva-20261013/baseline/`.
- Expected: the matrix identifies remaining closure work without treating a green historical plan status as proof of current runtime behavior.

**Exit Criteria:**
- The baseline is reproducible, preserved outputs are untouched, and Tasks 1–6 have no unresolved scope decision hidden inside them.

### Task 1: Make stage semantics executable and fingerprints complete

**Purpose:**
- Make `RecipeStage` the sole executable boundary while preserving requested specialist IDs and passing bounded objective/dependency semantics into every pattern path.

**Task Function:**
- runtime contract correction with compatibility-preserving test expansion

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: implementation requires source-level contract and runtime reasoning; resolve before activation

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: focused unit and runtime tests are sufficient for this lane

**Specification Coverage:**
- Verdict P0.1, P0.2, and P0.4; one `RecipeStage` per `WorkStage`; declared dependency outputs; specialist preservation; complete semantic cache identity.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/domain/models.py:WorkStage`
- Modify: `src/foresight_os/controller/recipes.py:RecipeStage`, `make_recipe`
- Modify: `src/foresight_os/controller/policy.py:_recipe_for_patterns`
- Modify: `src/foresight_os/runtime/workflow.py:_stage_cache_key`, `run_recipe_async`, `dispatch_stage`
- Inspect/modify as required: `src/foresight_os/runtime/participants.py:ParticipantConfig`
- Verify: `tests/test_controller_selection.py`, `tests/test_research_needs.py`, `tests/test_runtime_boundaries.py`, new stage-input/fingerprint tests

**Dependencies:**
- Task 0 baseline matrix.

**Authority:**
- Preauthorized local actions: edit only the declared stage/controller/runtime owners and focused tests; run local Python tests
- Stop for: adding a second compiled-stage abstraction, changing MAF topology semantics, changing public limits without an explicit compatibility test, or modifying unrelated exercises

**Steps:**
- [x] Step 1: Preserve `WorkStage.participants` as specialist IDs and compile those entries into `RecipeStage.participants` as derived `ParticipantConfig` values through the existing participant/factory path; add topology-generated roles only when the selected pattern requires a missing collaboration role.
- [x] Step 2: Add one deterministic bounded stage-input envelope containing decision question, horizon, objective, expected result, relevant constraints, and `dependency_outputs` keyed by declared dependency ID; pass record references plus bounded summaries/extracts for large canonical outputs rather than the full prompt or accumulated history, and use the same envelope for direct, sequential, concurrent, handoff, and group-chat execution.
- [x] Step 3: Maintain `outputs_by_stage` in `run_recipe_async`; reject missing dependency outputs before dispatch; ensure concurrent branches receive the stage envelope rather than the outer-loop `current` value.
- [x] Step 4: Split stage identity into a semantic input fingerprint and an execution-policy fingerprint. The semantic fingerprint covers decision context, objective, expected result, research needs, specialist IDs, selected skills, dependency result hashes, and relevant constraints; retain separate model, capability, and authorization fingerprints; keep timeouts, round/branch limits, and budgets in execution-policy identity rather than collapsing all values into one giant SHA.
- [x] Step 5: Add focused tests proving objective changes, dependency-output changes, specialist changes, and skill/capability/model/authorization changes invalidate semantic reuse while unchanged stage inputs reuse deterministically; prove timeout, round, branch, and budget changes update execution-policy identity without falsely invalidating an otherwise valid canonical analytical result.

**Verification:**
- [x] `python -m pytest -q tests/test_stage_inputs.py tests/test_controller_selection.py tests/test_research_needs.py tests/test_runtime_boundaries.py tests/test_tool_enabled_patterns.py tests/test_orchestration_patterns.py`
- [x] `python -m pytest -q tests/test_selective_reuse.py tests/test_review_hardening.py tests/test_persistence.py`
- Expected: all five patterns preserve topology contracts, requested specialist IDs/purposes survive compilation, dependency envelopes are exact, semantic changes produce different semantic fingerprints, and policy-only changes remain distinguishable.

**Exit Criteria:**
- No runtime path executes a declared multi-stage recipe from incidental prior output; bounded semantic inputs and separate policy identities are represented in the cache/receipt contract; focused tests pass.

### Task 2: Correct material closure and make review skills authoritative

**Purpose:**
- Fix recursive material provenance and separate deterministic validation from actual selected-skill review evidence.

**Task Function:**
- analytical contract correction and typed review integration

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: shared dependency semantics and review acceptance require sequential source-first implementation

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: typed domain tests and persisted-record round trips provide the required proof

**Specification Coverage:**
- Verdict P0.3, P0.7, and P0.8; canonical relation traversals; `ChallengeObjection` as challenge contract; complete `FindingView` and accepted-report qualifications.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `src/foresight_os/domain/relationships.py:RelationIndex`, `RELATIONSHIP_RULES`
- Modify: `src/foresight_os/domain/challenge.py:collect_material_inputs`, `build_material_fingerprint`, `derive_finding_views`
- Modify: `src/foresight_os/analysis/reviewer.py:review_reasoning`, `ReviewResult`
- Reuse: `src/foresight_os/runtime/executors.py:ReviewerExecutor`, `AgentFactory`, `ParticipantConfig`, and `src/foresight_os/controller/skills.py:SkillRegistry`; do not add a second review runtime
- Modify: `src/foresight_os/analysis/evidence_workflow.py:attach_review_record`
- Inspect/modify: `src/foresight_os/controller/skills.py:SkillRegistry`
- Verify: `src/foresight_os/persistence/analysis_store.py` review serialization
- Verify: `tests/test_finding_view.py`, `tests/test_review_records.py`, `tests/test_vertical_slice.py`, new relation/review-skill tests

**Dependencies:**
- Task 0 baseline; Task 1 only if the review path consumes stage metadata.

**Authority:**
- Preauthorized local actions: edit relation/review/report-domain owners and focused tests; add only the smallest typed skill-review seam required to record execution
- Stop for: introducing a second graph, accepting unsupported claims from an LLM without typed provenance, deleting `ReviewPolicy`, or converting raw skill text into acceptance without validation

**Steps:**
- [x] Step 1: Make material traversal direction explicit per relation type: `depends_on` and `derived_from` follow source-to-target for provenance, while support/contradiction relationships retain target-to-source context; expose `material_closure`, `impact_closure`, `support_context`, and `counterevidence_context` without collapsing semantics.
- [x] Step 2: Change `collect_material_inputs` to aggregate evidence IDs, assumptions, uncertainty, calculations, counterevidence, and missing inputs from every reached analytical record, recursively include calculation inputs, and retain direct-vs-derived provenance in the returned structure.
- [x] Step 3: Add only a thin typed adapter over the existing `ReviewPolicy` → `SkillRegistry` → `ParticipantConfig`/`AgentFactory` → `ReviewerExecutor` path; convert structured executor output into validated `ChallengeObjection` records, retain deterministic missing-reference, formula, and structural checks as a separate validator layer, and record skill IDs, versions, and hashes in `ReviewRecord`.
- [x] Step 4: Make objection validation kind-specific: only objections whose contract requires provenance must require evidence/calculation IDs; keep `ChallengeProposal` as an aggregation/transport compatibility object rather than the acceptance authority.
- [x] Step 5: Ensure `FindingView` and normal report rendering retain evidence, counterevidence, assumptions, confidence rationale, uncertainty, disconfirmation conditions, monitoring indicators, and unresolved non-blocking issues for accepted findings.
- [x] Step 6: Add a reproduced recommendation→claim→evidence regression test proving a supporting claim's evidence changes the material fingerprint and invalidates the review; stage-receipt mapping remains owned and proven by Task 3.

**Verification:**
- [x] `python -m pytest -q tests/test_finding_view.py tests/test_review_records.py tests/test_vertical_slice.py tests/test_persistence.py tests/test_supplier_and_ev_resilience.py tests/test_evidence_workflow.py`
- Expected: recursive material changes invalidate reviews, selected skills are represented in durable review records, objection validation rejects only contract-invalid objections, and accepted reports preserve qualifications.

**Exit Criteria:**
- One `RelationIndex` supplies all named traversals; no material fingerprint depends only on original target records; analytical skill execution and deterministic validation are distinguishable in persisted review evidence.

### Task 3: Close the automatic receipt lifecycle

**Purpose:**
- Make successful canonical stage execution automatically produce and persist reusable receipts, while refusing to reuse temporary conversational output.

**Task Function:**
- persistence lifecycle and fresh-process boundary verification

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: stateful cross-process behavior and atomic persistence require backend-focused execution

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: fresh-process probe is the acceptance validator

**Specification Coverage:**
- Verdict P0.5 and P0.6; canonicalized results only; automatic receipt persistence; restart reuse and selective reassessment.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `src/foresight_os/runtime/workflow.py:run_recipe_async`, `dispatch_stage`
- Modify: `src/foresight_os/persistence/analysis_store.py:StageReceipt`, `AnalysisStore.save_stage_receipt`
- Inspect/modify: `src/foresight_os/domain/models.py:AnalysisState` canonical record references
- Modify: `evaluation/probes/run_selective_reuse_probe.py`
- Verify: `tests/test_selective_reuse.py`, `tests/test_persistence.py`, new execute-receipt-reuse integration test

**Dependencies:**
- Tasks 1 and 2; canonical result IDs and hashes must be available before a receipt is committed.

**Authority:**
- Preauthorized local actions: edit runtime/persistence/probe owners and create disposable receipt-store fixtures; run fresh local subprocesses
- Stop for: persisting raw prompts or chat text as canonical output, weakening `StageReceipt.reusable_for`, bypassing atomic store locking, or silently refreshing an invalid receipt

**Steps:**
- [x] Step 1: Define an explicit `CanonicalResultCommitter(stage, output, context) -> CanonicalStageResult | None` boundary owned by the caller/domain workflow. `CanonicalStageResult` contains `result_references`, `result_hashes`, and a reloadable canonical output; return `None` when the result is only temporary conversational text.
- [x] Step 2: After successful dispatch, let runtime consume only the committer result, construct `StageReceipt` with the stage semantic/execution-policy identities, skill/capability/model/authorization fingerprints, canonical references/hashes, committed status, and complete provenance, then persist through `AnalysisStore.save_stage_receipt` atomically.
- [x] Step 3: Load state, receipts, and canonical outputs on the next process; validate receipt identity before reuse and map changed analytical records through `RelationIndex.impacted_descendants()` to affected record IDs, intersect those IDs with `StageReceipt.result_references`, walk the stage dependency DAG, and recompute only the resulting affected stage set after a material dependency mutation.
- [x] Step 4: Replace manual cache/receipt seeding in the selective-reuse probe with cold execution → automatic persistence → process exit → new process reuse → dependency mutation → selective reassessment.
- [x] Step 5: Add failure-path tests for incomplete provenance, changed authorization, changed capability/model fingerprint, stale canonical hashes, and missing canonical outputs.

**Verification:**
- [x] `python -m pytest -q tests/test_selective_reuse.py tests/test_persistence.py`
- [x] `python evaluation/probes/run_selective_reuse_probe.py --output-root work/closure-patch-canva-20261013/selective-reuse-task3-r2`
- Expected: the probe proves automatic receipt creation, zero new model/tool calls for unchanged stages in a fresh process, and only affected descendants rerun after dependency change.

**Exit Criteria:**
- Runtime, not the probe, owns the successful-stage receipt lifecycle; raw output is never treated as durable reuse; the fresh-process lifecycle is green.

### Task 4: Add the vendor-neutral presentation compiler and Canva boundary

**Purpose:**
- Produce a validated six-slide decision artifact from canonical findings without adding analytical claims or a second artifact state model.

**Task Function:**
- derived artifact compilation and external-boundary preparation

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: local compiler is deterministic; external adapter work requires controller authority and explicit approval

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: spec validation and artifact provenance assertions are local and deterministic

**Specification Coverage:**
- Verdict P0.9, P2 deferral, and the target architecture `AnalysisState → FindingView → PresentationSpec → approval → Canva`.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Add: `src/foresight_os/artifacts/presentation.py:SlideSpec`, `PresentationSpec`, compiler, validator, fingerprint helper
- Modify: `src/foresight_os/domain/models.py:Artifact` usage and relationship construction only; do not add `PresentationState` or `CanvaState`
- Modify: `src/foresight_os/runtime/capabilities.py:artifact_generation` adapter registration while keeping the default disconnected state truthful
- Verify: `src/foresight_os/artifacts/report.py` qualification rendering
- Add: `tests/test_presentation_spec.py`
- Update: `README.md` artifact boundary and optional Canva connection documentation

**Dependencies:**
- Task 2 for complete `FindingView` and canonical source revision/provenance data already present in `AnalysisState`; Task 3 is not a dependency of local presentation compilation.

**Authority:**
- Preauthorized local actions: add and test the local `PresentationSpec` compiler, validation, artifact metadata, and adapter protocol; update local documentation
- Stop for: Canva authentication, external design mutation, export, publication, arbitrary deck generation, or a new presentation state/database model

**Steps:**
- [x] Step 1: Define immutable `SlideSpec` and `PresentationSpec` with investigation ID, analysis revision, audience, decision question, horizon, title, six ordered slides, and source finding IDs; include finding/evidence/calculation IDs, uncertainty, disconfirmation conditions, and speaker notes per slide.
- [x] Step 2: Compile the fixed template: decision/scope, evidence/signals, scenarios, strategic options, recommendation, and reassessment. Select, shorten, and arrange canonical findings only; reject slide content whose claim/evidence IDs are not present in `AnalysisState`.
- [x] Step 3: Validate deterministic completeness, source revision, accepted/rejected status, stale artifacts, provenance subsets, and spec hash. Normal compilation requires the current accepted state; `compile_presentation(state, provisional=True)` is the only provisional path and must mark the spec `DRAFT / UNVALIDATED`. Represent local output as `Artifact(kind="presentation_spec")` with `produces` relationships from source findings.
- [x] Step 4: Define an optional adapter/receipt shape containing only durable Canva identifiers and verification state: `provider`, `design_id`, `source_revision`, `presentation_spec_hash`, `confirmed_state`, and `last_verified_at`. Preview/export URLs remain transient adapter outputs. Keep `artifact_generation` unavailable until a connected adapter is supplied, reject provisional specs for external writes unless a human explicitly approves the draft, and preserve human approval at the first external mutation.
- [x] Step 5: Add tests for accepted and provisional findings, stale revisions, unsupported new claims, counterevidence/uncertainty retention, deterministic spec hashing, no-connector behavior, and the integration chain evidence change → stale finding → stale `presentation_spec` artifact → normal Canva publish/update rejection → regenerated spec.

**Verification:**
- [x] `python -m pytest -q tests/test_presentation_spec.py tests/test_finding_view.py tests/test_client_continuation.py`
- [x] `python -m pytest -q tests/test_toolbelt_contracts.py`
- Expected: local presentation compilation is deterministic and provenance-safe; a disconnected Canva boundary reports unavailable rather than pretending to publish.

**Exit Criteria:**
- A validated six-slide `PresentationSpec` can be generated from canonical state, linked through existing artifacts/relationships, and handed to a connected Canva adapter only after explicit approval.

### Task 5: Correct performance economics and resource evidence

**Purpose:**
- Make optimization evidence measure workflow behavior and real resource stability rather than aggregate or Boolean proxies.

**Task Function:**
- benchmark contract correction and performance verification

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: measured regression analysis and resource instrumentation require specialized performance review

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: comparator and receipt schema provide deterministic validation

**Specification Coverage:**
- Verdict P1.1 and P1.2; separate model/tool/external economics, workflow p95 by pattern, queue/tool/event-loop latency, and real resource soak measurements.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/runtime/metrics.py:RunMetrics`
- Modify: `evaluation/probes/optimization_measurement.py`
- Modify: `evaluation/probes/run_optimization_probe.py:_soak_receipt` and pattern measurement
- Modify: `evaluation/probes/compare_optimization_receipts.py:compare`, `_tool_calls`, `_validate_measurement_receipt`
- Verify: `tests/test_anomaly_probe.py`, `tests/test_runtime_boundaries.py`, new measurement-schema tests

**Dependencies:**
- Tasks 1–4 so receipts can distinguish reused/reassessed stages and accepted `FindingView` denominators; Task 5 itself must first establish the corrected-schema baseline before Task 6 optimization changes.

**Authority:**
- Preauthorized local actions: edit benchmark schema/probes and runtime counters, run bounded local measurements into the new disposable root
- Stop for: changing frozen thresholds without evidence, disabling a MAF pattern because it benchmarks slower, or using inaccessible production-only telemetry as a required local gate

**Steps:**
- [ ] Step 1: Split receipt counters into non-additive dimensions: `model_calls`, `tool_calls_total`, `local_tool_calls`, `mcp_tool_calls`, `external_http_requests`, `input_tokens`, and `output_tokens`, plus per-accepted-finding values; do not count model calls as tool calls, and preserve backward-readable schema migration where needed.
- [ ] Step 2: Record p95 and latency components for Direct, Sequential, Concurrent, Handoff, Group Chat, and mixed workflows, including queue wait, tool latency, and event-loop lag when available.
- [ ] Step 3: Replace Boolean soak samples with bounded snapshots of portable RSS, active Python tasks, threads, child processes, owned capability resources, MCP/session count, and event-loop lag; record open file descriptors or Windows handles only as optional platform-specific evidence, and report plateau/monotonic-growth evidence.
- [ ] Step 4: Make the comparator fail closed for missing required evidence and compare the same workload, deterministic keys, accepted-finding denominator, and thresholds: p95 ≤20%, allocation/RSS ≤15%, no monotonic resource growth, and no new calls for fully reusable stages.
- [ ] Step 5: Without optimization changes, capture a new post-correctness/pre-optimization baseline using the corrected schema under `work/closure-patch-canva-20261013/baseline/optimization-corrected.json`; add tests for missing receipts, zero accepted findings, pattern-specific regressions, resource drift, and reused-stage economics.

**Verification:**
- [ ] `python -m pytest -q tests/test_anomaly_probe.py tests/test_runtime_boundaries.py`
- [ ] `python evaluation/probes/run_optimization_probe.py --mode baseline --fixture tests/fixtures/analyst_multisheet.xlsx --output work/closure-patch-canva-20261013/baseline/optimization-corrected.json`
 - Expected: the corrected-schema baseline is captured before Task 6 cache optimizations; the legacy Task 0 receipt is not used for apples-to-apples comparison.
- Expected: required observations are present, resource soak is based on actual measurements, and comparator acceptance is false when evidence is missing or thresholds regress.

**Exit Criteria:**
- Performance claims are attributable to workflow and accepted findings, not only XLSX latency or a Boolean cleanup flag; all five patterns remain first-class; the corrected-schema baseline exists before Task 6 begins.

### Task 6: Cache immutable work and align CI/documentation

**Purpose:**
- Reduce repeated immutable work and make closure evidence reviewable without making every pull request run the full release suite.

**Task Function:**
- bounded optimization and delivery-surface alignment

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: low-risk cache changes follow canonical owners established by Tasks 1–5

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: focused cache tests and CI configuration inspection

**Specification Coverage:**
- Verdict P1.3, P1.4, and P1.5; immutable-work caching, shared workbook-derived inputs, three CI evidence tiers, and receipt artifact publication.

**Required Skills:**
- `skill-performance-optimization`

**Files And Symbols:**
- Modify: `src/foresight_os/controller/skills.py:SkillRegistry`
- Inspect/modify: `src/foresight_os/domain/validation.py` schema validator construction
- Inspect/modify: `src/foresight_os/domain/relationships.py:RelationIndex` cache owner
- Inspect/modify: `src/foresight_os/analysis/` workbook parse/calculation owners
- Reuse: `src/foresight_os/runtime/local_toolbelt.py:WorkbookReadCache` as the canonical workbook read cache; do not add parallel workbook caches
- Modify: `.github/workflows/ci.yml` only if the existing workflow owns the relevant gates
- Update: `evaluation/README.md`, `README.md`, and package/evaluation documentation
- Verify: focused cache tests and package resource checks

**Dependencies:**
- Tasks 1–5; do not cache before semantic fingerprints and revision scope are stable.

**Authority:**
- Preauthorized local actions: add process-local caches keyed by verified immutable identity/revision, update existing CI commands and documentation, and run local checks
- Stop for: cross-process mutable caches, global cache invalidation without an identity owner, workflow-provider changes, dependency upgrades, or cleanup of existing `work/` artifacts

**Steps:**
- [ ] Step 1: Cache resolved skill content and verified manifest identity for the process lifetime; preserve hash mismatch failure behavior.
- [ ] Step 2: Cache compiled JSON schema validators by schema identity and cache `RelationIndex` projections by `(investigation_id, revision, relationship_fingerprint)` or an equivalent immutable-state scope; retain explicit invalidation only where the canonical owner requires it.
- [ ] Step 3: Reuse parsed workbook and deterministic calculation results across analysis, review, report, and presentation compilation through the existing `WorkbookReadCache`, keyed by source identity, SHA-256, selection, and effective limits; pass bounded extracts to agents.
- [ ] Step 4: Keep one CI workflow with conditional `deterministic`, `nightly-evidence`, and `release-evidence` jobs where practical, upload machine-readable receipts as SHA-associated artifacts, and document that optional Canva smoke is only run when a connected approved adapter exists.
- [ ] Step 5: Repair the clean-wheel smoke if still applicable so it uses a genuinely empty virtual environment, installs only the newly built wheel, runs outside the repository tree, and verifies `foresight_os.__file__` points inside that environment.
- [ ] Step 6: After the cache changes, capture the optimized release receipt and compare it only with Task 5's corrected-schema baseline; do not compare it with Task 0's legacy receipt.

**Verification:**
- [ ] `python -m pytest -q tests/test_skills.py tests/test_analysis_schema.py tests/test_persistence.py`
- [ ] `python evaluation/probes/run_optimization_probe.py --mode release --fixture tests/fixtures/analyst_multisheet.xlsx --output work/closure-patch-canva-20261013/optimization/release.json`
- [ ] `python evaluation/probes/compare_optimization_receipts.py --baseline work/closure-patch-canva-20261013/baseline/optimization-corrected.json --release work/closure-patch-canva-20261013/optimization/release.json --output work/closure-patch-canva-20261013/optimization/comparison.json`
- [ ] `git diff --check`
- Expected: cache identities are deterministic and scoped, package resources still resolve, CI documentation matches canonical commands, and no preserved output is modified.

**Exit Criteria:**
- Immutable work is not repeatedly reparsed or rehashed within a valid scope; PR gates remain bounded; heavy closure evidence is available for nightly/release execution; the optimized release receipt is comparable only to Task 5's corrected-schema baseline.

### Task 7: Run final verification and reconcile the plan

**Purpose:**
- Prove the complete delivery against current source and record any blocked external-boundary evidence without overstating closure.

**Task Function:**
- final acceptance and evidence reconciliation

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: final verification requires lead-controller authority and fresh evidence

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve independently through the verification skill before activation

**Specification Coverage:**
- All implementation outcomes and completion criteria in this plan; external Canva status must be truthful.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: all Task 0–6 owners and focused tests
- Verify: `docs/superpowers/plans/2026-10-13-closure-patch-canva-delivery-plan.md`
- Verify: `git status --short --branch`, `git diff --check`

**Dependencies:**
- Tasks 0–6 complete with accepted task-local proof.

**Authority:**
- Preauthorized local actions: run final local verification, reconcile plan checklists and evidence paths, and record blocked/unavailable external-boundary results
- Stop for: marking the plan completed without fresh verification, external Canva mutation without explicit approval, or any unrecorded scope deviation

**Steps:**
- [ ] Step 1: Run focused regression tests for controller, workflow, relation/review, receipts, presentation, capabilities, and evaluation scope.
- [ ] Step 2: Run `python -m pytest -q` with generated output routed to the new disposable root where applicable.
- [ ] Step 3: Run the controller/contract matrices, selective-reuse probe, presentation validation, optimization comparison, and clean-wheel smoke using only new disposable output paths.
- [ ] Step 4: If a Canva adapter is connected and the user explicitly approves the external write, run a smoke that creates or updates one editable presentation from `PresentationSpec`; otherwise record `BLOCKED_EXTERNAL: connector unavailable or approval not granted` and do not claim Canva delivery success.
- [ ] Step 5: Reconcile every task state, deviation, evidence path, and completion criterion, then report two independent verdicts: `Core three-increment closure: VERIFIED` or `FAILED`; `Canva external delivery: VERIFIED`, `BLOCKED_EXTERNAL`, or `FAILED`. Only `skill-verification-before-completion` may authorize a terminal `completed` status.

**Verification:**
- [ ] `python -m pytest -q`
- [ ] `python evaluation/run.py --matrix contract --output-root work/closure-patch-canva-20261013/final/contract`
- [ ] `python evaluation/run.py --matrix controller --write-report work/closure-patch-canva-20261013/final/controller.md`
- [ ] `python evaluation/probes/run_selective_reuse_probe.py --output-root work/closure-patch-canva-20261013/final/selective-reuse`
- [ ] `python evaluation/probes/run_optimization_probe.py --mode release --fixture tests/fixtures/analyst_multisheet.xlsx --output work/closure-patch-canva-20261013/final/optimization/release.json`
- [ ] `git diff --check`
- [ ] `git status --short --branch`
- Expected: all required local gates pass, no preserved untracked output changes, evidence is fresh and machine-readable, and external Canva status is either verified through an approved connector or explicitly blocked.

**Exit Criteria:**
- The plan has fresh proof for every required outcome, all deviations and unavailable boundaries are recorded, and completion status remains `proposed` or becomes `completed` only after the verification skill returns `verified`.

## Verification

Final artifact-level verification must be run fresh after all implementation tasks:

- `python -m pytest -q`
- `python evaluation/run.py --matrix contract --output-root work/closure-patch-canva-20261013/final/contract`
- `python evaluation/run.py --matrix controller --write-report work/closure-patch-canva-20261013/final/controller.md`
- `python evaluation/probes/run_selective_reuse_probe.py --output-root work/closure-patch-canva-20261013/final/selective-reuse`
- `python evaluation/probes/run_optimization_probe.py --mode release --fixture tests/fixtures/analyst_multisheet.xlsx --output work/closure-patch-canva-20261013/final/optimization/release.json`
- `python evaluation/probes/compare_optimization_receipts.py --baseline work/closure-patch-canva-20261013/baseline/optimization-corrected.json --release work/closure-patch-canva-20261013/final/optimization/release.json --output work/closure-patch-canva-20261013/final/optimization/comparison.json`
- `git diff --check`
- `git status --short --branch`

Required evidence includes: exact current base, stage-input and semantic-fingerprint regression output, recursive material-invalidation output, typed skill-objection and qualification-preservation output, fresh-process automatic receipt lifecycle output, validated `PresentationSpec` hash/provenance output, split performance/resource receipts, and an explicit Canva connector/approval status.

## Completion Criteria

The plan is ready for completion verification when:

1. Task 0 confirms the verdict's remaining gaps against current `origin/main` `2fe7b428` and preserves all pre-existing untracked outputs.
2. Every `WorkStage` compiles to one executable `RecipeStage` whose objective, declared dependency outputs, requested specialists, capabilities, skills, expected result, and limits control execution.
3. Stage semantic fingerprints include all material inputs, and policy-only execution changes remain distinguishable from analytical changes.
4. `RelationIndex` exposes distinct material, impact, support, and counterevidence traversals; recursive material closure includes evidence and assumptions of every reached analytical record.
5. Selected review skills produce validated typed objections recorded in `ReviewRecord`; deterministic validation remains separate; `FindingView` and accepted reports retain analytical qualifications.
6. Successful canonical stages automatically persist valid `StageReceipt` records; raw conversational output is not reusable; fresh-process reuse and selective reassessment pass.
7. A six-slide, vendor-neutral `PresentationSpec` compiles deterministically from canonical findings, cannot introduce unsupported claims, and uses existing `Artifact` relationships.
8. Canva remains a truthful optional external boundary with human approval at the first external mutation; unavailable connector evidence is recorded rather than simulated.
9. Performance receipts split economics, gate workflow p95 and resource stability, preserve all five MAF patterns, and fail closed on missing evidence.
10. Immutable-work caches, CI tiers, documentation, package resources, and clean-wheel evidence reconcile with canonical ownership.
11. `skill-verification-before-completion` returns `verified`, and Task 7 records separate verdicts for core three-increment closure (`VERIFIED`/`FAILED`) and Canva external delivery (`VERIFIED`/`BLOCKED_EXTERNAL`/`FAILED`); only then may the plan status change from `proposed` to `completed` or any separately authorized Git disposition occur.
