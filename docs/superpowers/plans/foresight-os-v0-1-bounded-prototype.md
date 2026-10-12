---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: proposed
layer: change
name: foresight-os-v0-1-bounded-prototype
targets:
- src/foresight_os/
- schemas/analysis.schema.json
- schemas/work_brief.schema.json
- evaluation/
- tests/
- docs/intent/
- README.md
related_features:
- evidence-aware strategic reasoning
- durable investigation continuity
- bounded Microsoft Agent Framework execution
related_stages:
- v0.1 bounded prototype
---

# Foresight OS v0.1 Bounded Prototype

## Goal

Deliver a small, evidence-aware strategic reasoning prototype that starts from a decision question, analyzes one workbook, persists traceable analytical state, reviews claims and implications, detects stale dependent outputs when evidence or scope changes, and resumes in a fresh Session without relying on prior chat history. Use Microsoft Agent Framework (MAF) directly for execution capabilities that pass evaluation; do not build a custom orchestration platform.

The verdict is adopted with two implementation clarifications:

- `basis`, `assessment`, and `lifecycle` remain independent epistemic dimensions. Reassessment is a separate dependency-invalidation signal, not a replacement state vocabulary.
- The implementation runtime and MAF package surface are pinned during the MAF-fit task. No later task may silently assume a runtime, checkpoint behavior, or client integration that was not proven locally.

## Terminology Boundary

- `Implementation Controller` means the build-time controller governing plan tasks, repository authority, profiles, and verification gates.
- `Foresight Controller` means the product capability being built: it recommends an execution recipe, selects foresight roles and effort profiles, and chooses bounded MAF patterns.
- `Controller-selected` and `Validator Profile` fields in this plan describe build governance only. Foresight runtime configuration uses `purpose: execute | review` and `profile: low | normal | high | xhigh`.
- Project OS concepts reused in the product are right-sized execution, profiles, controller recommendation, evidence before completion, native-first infrastructure, and Git source truth. Coding worktree isolation, repository mutation ownership, branch/commit semantics, and implementation admission gates are not user-facing Foresight OS runtime requirements.

Runtime vocabulary is separate from this `Implementation Plan`:

- `Investigation`: a persistent foresight problem being explored.
- `Work Brief`: the current decision question, scope, deliverables, assumptions, open dependencies, direction, and next useful step for an Investigation.
- `Execution Recipe`: the Foresight Controller's proposed roles, profiles, budgets, and MAF pattern.
- `Run`: one instantiated execution of an Execution Recipe.
- `Session`: one temporary Codex or Claude interaction window.
- `Analysis State`: durable evidence, claims, relationships, reasoning, assessments, revisions, and invalidation metadata.
- `Artifact`: a generated report, workbook, presentation, or other retained result.

The runtime flow is `Investigation → Work Brief → Execution Recipe → Run → Analysis State → Artifact`. The implementation controls in this document govern construction of Foresight OS; they are not mandatory user-facing pre-flight rules for running an Investigation.

## Implementation Outcomes

### Reproducible evaluation contract

The repository contains frozen workbook cases, decision questions, expected traps, reference findings, and a scoring rubric covering supported-claim precision, finding coverage, contradiction detection, traceability, accepted-finding cost, human verification effort, recovery success, and maintainability cost. The benchmark separates three levels: A) a capable single agent with an ordinary prompt, B) the same single agent with Foresight OS schema, evidence requirements, and Wayfinding, and C) Foresight OS with additional coordination. This isolates semantic/governance value from coordination value.

### Evidence-first vertical slice

A decision-anchored Wayfinding function, minimal evidence/claim/implication/recommendation records, workbook locators, bounded analysis and reasoning review, a human decision/review boundary, and report-fidelity checking produce a durable `analysis.json` whose material report statements trace to validated analytical records. The benchmark case explicitly exercises formal human acceptance; the product does not make that ceremony mandatory for every future use.

### Durable continuation and invalidation

Persistent Investigations use `work/<investigation-id>/brief.md`, `analysis.json`, and optional `artifacts/`. `brief.md` is the durable Work Brief, not an execution plan. Analytical continuation loads the Work Brief and Analysis State, then starts a new Run; runtime resumption uses only a compatible MAF checkpoint. Material evidence, assumption, or scope changes mark dependent claims, implications, recommendations, and Artifacts for reassessment or stale output instead of silently reusing them.

### Bounded coordination and client access

The Foresight Controller selects only tested recipes with explicit call, correction, budget, completion, escalation, and partial-result bounds. It may choose a single agent. Concurrent or handoff execution enters the product only if evaluation shows measurable value over the semantic single-agent and sequential-review baselines. One real client integration is required for v0.1; a second client is a stretch gate unless portability is an explicit release objective.

### Documentation and deferral alignment

README owns stable product architecture and the runtime vocabulary. A small `docs/intent/maf-capability-decision.md` record owns the empirical MAF capability decision. This Implementation Plan owns temporary build truth, and evaluation results own empirical comparisons. Group Chat, Magentic, large role catalogs, remote service hosting, graph storage, autonomous monitoring, multi-writer editing, generic A2A, and custom workflow/checkpoint/scheduler/HITL/message-bus systems remain explicitly deferred unless a measured failure proves one necessary.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`; add `skill-full-stack-integration` only for the client contract task if the selected client crosses a service boundary
- Isolation: `current workspace`; activation requires a Git checkout because the current starter-kit path has no `.git` metadata
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit the declared repository files, create local fixtures and disposable test artifacts, run declared local checks, and read configured local documentation or MAF package documentation without sending source or credentials outside the approved boundary
- User-approval actions: install or upgrade dependencies, authenticate to models/MCP/external clients, send data outside the local workspace, publish artifacts, commit, push, merge, discard changes, or destructive cleanup
- Parallel ownership: `none`; evaluation, runtime proof, domain state, workflow, continuity, Controller, and clients share contracts and must advance in order
- Sequential fallback: if any task cannot prove its exit criteria, keep the Implementation Plan proposed or mark the task blocked; do not add the next layer to compensate for missing evidence

## Coordination State

- Coordination owner: `single Implementation Controller`
- Coordination schema: `2`
- Branch: `unresolved — current workspace is not a Git checkout`
- Base commit: `unresolved — no Git metadata is available`
- Expected workspace: `current workspace after Git checkout or attachment is established; no unrelated preserved changes`
- Next action: `establish or attach the intended Git checkout, then begin Task 1`
- Blockers: `Git workspace identity and MAF runtime/dependency availability must be resolved before activation`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | current | `unresolved` | none | `python -m pytest tests/test_evaluation_contract.py` | pending |
| Task 2 | `pending` | current | `unresolved` | Task 1 | `python -m pytest tests/test_maf_fit.py` | pending |
| Task 3 | `pending` | current | `unresolved` | Tasks 1–2 | `python -m pytest tests/test_analysis_schema.py tests/test_persistence.py` | pending |
| Task 4 | `pending` | current | `unresolved` | Tasks 1–3 | `python -m pytest tests/test_vertical_slice.py tests/test_report_fidelity.py` | pending |
| Task 5 | `pending` | current | `unresolved` | Task 4 | `python -m pytest tests/test_recovery.py tests/test_invalidation.py` | pending |
| Task 6 | `pending` | current | `unresolved` | Tasks 1–5 | `python -m pytest tests/test_controller_selection.py` | pending |
| Task 7 | `pending` | current | `unresolved` | Tasks 5–6 | `python -m pytest tests/test_client_continuation.py` | pending |
| Task 8 | `pending` | current | `unresolved` | Tasks 1–7 | `python -m pytest` plus evaluation report | pending |

## Task Breakdown

### Task 1: Freeze the evaluation contract

**Purpose:**
- Make success measurable before Controller logic exists.
- Establish one representative workbook investigation with a decision question, expected traps, human/reference findings, and a fair baseline comparison.

**Task Function:**
- Evaluation contract design and fixture authoring.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded but consequential scope; direct Implementation Controller ownership avoids premature delegation.

**Validator Profile (optional):**
- Controller-selected: `review-1`
- Selection basis: independently check that the rubric does not reward coordination or unstructured prompting instead of evidence quality.

**Specification Coverage:**
- Verdict Phase 0: frozen workbook cases, decision questions, expected traps, scoring rubric, single-agent baseline, and human/reference findings.
- Compare three levels fairly: A) capable single agent plus ordinary prompt, B) the same single agent plus Foresight OS schema/evidence/Wayfinding, and C) Foresight OS plus additional coordination.
- Level A receives the workbook, decision question, ordinary prompt, and source tools, but no Foresight Work Brief, evidence schema, or Wayfinding contract. Level B receives the same workbook, question, and source tools plus the Work Brief, evidence schema, Wayfinding, and evidence requirements. Level C receives exactly level B's inputs and adds only the tested coordination pattern.
- Apply one common scoring rubric and human/reference adjudication to A, B, and C; require the same evidence contract for B and C. This isolates A → B semantic/governance value from B → C coordination value without pretending that level A produced structured evidence.
- Measure decision usefulness and evidence integrity before agent sophistication.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `repo_config/planning_artifact_schema.yaml`, `agents/*.toml`
- Modify: `pyproject.toml`, `evaluation/README.md`, `evaluation/rubric.md`, `evaluation/cases/case-001/decision.md`, `evaluation/cases/case-001/reference.json`, `evaluation/baseline/README.md`, `tests/test_evaluation_contract.py`
- Verify: `evaluation/cases/case-001/`

**Dependencies:**
- Git checkout or attachment is established before activation.
- The representative workbook fixture and any sensitive data handling boundary are agreed locally; do not use customer data as a fixture.

**Authority:**
- Preauthorized local actions: create evaluation documentation, synthetic or approved local fixtures, a minimal project configuration, and contract tests; run local test commands.
- Stop for: missing or unapproved workbook data, external dataset access, a change to the decision question or acceptance rubric, or any request to optimize for coordination metrics.

**Steps:**
- [ ] Step 1: Choose one decision-anchored question with owner, horizon, and materiality criteria; record provisional assumptions and unresolved dependencies.
- [ ] Step 2: Create one frozen workbook case with reproducible source locators, expected traps, reference findings, and a human-verification protocol.
- [ ] Step 3: Define scoring for supported-claim precision, coverage, contradiction precision/recall, traceability, cost per accepted finding, verification effort, recovery success, and maintainability cost.
- [ ] Step 4: Define level A, level B, and level C inputs, common scoring/adjudication, and acceptance gates; level A remains ordinary-prompt only, while levels B/C share the same evidence contract and C differs from B only by coordination.

**Verification:**
- [ ] `python -m pytest tests/test_evaluation_contract.py`
- Expected: the case, rubric, reference findings, three comparison levels, and baseline contracts are present, schema-valid, deterministic, and do not contain hidden customer data.

**Exit Criteria:**
- Evaluation can be rerun by another engineer without inventing the question, traps, reference findings, scoring rules, or baseline constraints.

### Task 2: Prove MAF fit with native capabilities

**Purpose:**
- Pin the supported runtime and MAF package surface before building domain orchestration.
- Prove only the capabilities needed immediately: single agent, sequential review, human input, checkpoint/restart, and structured output.

**Task Function:**
- Runtime spike and capability characterization.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: framework behavior and dependency risk require direct inspection and bounded experiments.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: the tests and captured capability matrix are the validator for this local spike.

**Specification Coverage:**
- Verdict Phase 1: use MAF directly and defer Group Chat, Magentic, and large agent catalogs.
- Map ordered work to sequential execution, human judgment to HITL, and compatible interruption to checkpoints.
- Do not create a custom workflow engine, message bus, checkpoint store, scheduler, or HITL system.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: selected MAF package documentation and local runtime capabilities
- Modify: `pyproject.toml`, `src/foresight_os/runtime/maf_probe.py`, `src/foresight_os/runtime/capabilities.py`, `tests/test_maf_fit.py`, `docs/intent/maf-capability-decision.md`
- Verify: `docs/intent/maf-capability-decision.md`

**Dependencies:**
- Task 1 evaluation contract is frozen.
- The implementation runtime and dependency installation/authentication boundary are explicitly approved before installation.

**Authority:**
- Preauthorized local actions: inspect installed runtime capabilities, write the MAF probe and capability matrix, and run local smoke tests against approved local dependencies.
- Stop for: dependency installation, authentication, network/model access, undocumented checkpoint semantics, or any need for a custom orchestration primitive.

**Steps:**
- [ ] Step 1: Pin the runtime and MAF package versions in `pyproject.toml`; record why the selected runtime is the smallest viable prototype surface.
- [ ] Step 2: Implement a probe for single-agent execution, sequential review, human input, structured output, and compatible checkpoint/restart.
- [ ] Step 3: Record observed success, failure, state, and side-effect behavior, including how a changed topology must start a new workflow instead of resuming an incompatible checkpoint.
- [ ] Step 4: For every tested capability, record exactly one decision: `USE_NATIVE`, `ADAPT_AT_BOUNDARY`, `DEFER`, or `UNSUPPORTED`.
- [ ] Step 5: Record the minimal vertical-slice guardrail contract: `max_agent_steps: 5` per role, `max_correction_rounds: 1`, `max_total_agent_calls: 3`, and exhaustion behavior of no accepted recommendation plus a human decision/review boundary.
- [ ] Step 6: Record only the MAF capability decision, guardrail contract, and implementation boundary in `docs/intent/maf-capability-decision.md`; keep stable product architecture in `README.md`.

**Verification:**
- [ ] `python -m pytest tests/test_maf_fit.py`
- Expected: every required capability has a reproducible pass or a concrete blocker; unsupported capabilities are not represented as implemented.
- [ ] Inspect `docs/intent/maf-capability-decision.md`.
- Expected: every tested capability has one of the four decision values, with evidence and known limits; Group Chat and Magentic are explicitly `DEFER` unless a later benchmark changes scope.
- [ ] Inspect the vertical-slice guardrail contract.
- Expected: the shared preset is explicit and enforceable (`max_agent_steps: 5` per role, `max_correction_rounds: 1`, `max_total_agent_calls: 3`), and Task 4 can consume it without inventing its own correction or call limits.
- [ ] Direct boundary trace from probe input to MAF run/checkpoint output is retained as a disposable or documented local test artifact.
- Expected: failure and restart behavior are observable without relying on chat history.

**Exit Criteria:**
- The supported MAF capability matrix is pinned, the runtime is known, and no downstream task depends on unproven framework behavior.

### Task 3: Define durable evidence and analytical state

**Purpose:**
- Create the smallest reusable domain model and persistence contract for evidence-aware work.
- Preserve evidence relationships and distinguish epistemic dimensions without building a graph database.

**Task Function:**
- Domain contract and durable-state implementation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared schemas are high-blast-radius contracts and should be authored centrally.

**Validator Profile (optional):**
- Controller-selected: `review-1`
- Selection basis: independent review of schema invariants, lineage, and stale-state behavior.

**Specification Coverage:**
- Evidence records require source locator, version/date, excerpt or data reference, and limitations.
- Excel evidence requires `file_version`, `sheet`, `range`, `units`, `transformation`, and `calculation`; a bare filename is not evidence.
- Claims, implications, recommendations, and artifacts use lightweight ID relationships.
- `Work Brief` is a separate runtime contract containing decision question, scope, desired deliverables, assumptions, open dependencies, current direction, and next useful step; it is not an Execution Recipe.
- `basis`: `OBSERVED | DERIVED | ASSUMED`; `assessment`: `UNASSESSED | SUPPORTED | UNCERTAIN | CONTESTED | REFUTED`; `lifecycle`: `CURRENT | SUPERSEDED`.
- Reassessment/staleness is separate dependency metadata.
- For v0.1, the schema contains only `Evidence`, `Claim`, `Implication`, `Recommendation`, `Artifact`, `Revision`, and `Relationship`; new domain records require a concrete workflow that cannot be represented cleanly with these records.
- Persistent work uses `brief.md`, `analysis.json`, and optional `artifacts/`; no `state.json` unless a later proven need exists.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `schemas/analysis.schema.json`, `docs/intent/maf-capability-decision.md`
- Modify: `schemas/analysis.schema.json`, `schemas/work_brief.schema.json`, `src/foresight_os/domain/models.py`, `src/foresight_os/domain/validation.py`, `src/foresight_os/persistence/analysis_store.py`, `src/foresight_os/persistence/ids.py`, `tests/test_analysis_schema.py`, `tests/test_persistence.py`
- Verify: `work/<investigation-id>/brief.md`, `work/<investigation-id>/analysis.json`, `work/<investigation-id>/artifacts/`

**Dependencies:**
- Tasks 1–2 complete.
- The MAF-fit task has confirmed the runtime and structured-output boundary.

**Authority:**
- Preauthorized local actions: create local schemas, domain models, deterministic ID/version helpers, filesystem persistence, validation tests, and disposable work fixtures.
- Stop for: introducing a graph database, adding a second durable state store, storing secrets or customer data, or changing the epistemic vocabulary without updating the evaluation contract.

**Steps:**
- [ ] Step 1: Define the Work Brief schema and typed domain records for evidence, claims, implications, recommendations, artifacts, relationships, revisions, and invalidation metadata; do not add Scenario, Driver, Signal, Indicator, or Trigger records without a demonstrated vertical-slice need.
- [ ] Step 2: Implement validation and deterministic persistence with revision history; preserve source locators and relationship IDs rather than flattening them into report text.
- [ ] Step 3: Add idempotent load/save behavior and duplicate-ID rejection; ensure malformed or incomplete evidence fails at the trust boundary.
- [ ] Step 4: Create a minimal persisted Investigation fixture with a validated Work Brief in `brief.md` and machine-readable Analysis State in `analysis.json`.

**Verification:**
- [ ] `python -m pytest tests/test_analysis_schema.py tests/test_persistence.py`
- Expected: valid records round-trip; invalid locators, missing relationships, duplicate IDs, unsupported states, and malformed revisions fail clearly without partial writes.
- [ ] Inspect a persisted fixture and reconstruct one evidence-to-claim-to-recommendation lineage.
- Expected: every relationship is recoverable from IDs and revision metadata.

**Exit Criteria:**
- Durable analytical state is versioned, validated, reproducible, and small enough to inspect without a graph database.

### Task 4: Build the workbook-to-report vertical slice

**Purpose:**
- Deliver the first useful end-to-end capability: workbook input to decision-anchored analysis, evidence/reasoning review, bounded correction, a human decision/review boundary, and faithful report output.

**Task Function:**
- Vertical-slice implementation and direct boundary verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: the slice crosses ingestion, analysis, review, persistence, and artifact generation; one Implementation Controller owns the build contract.

**Validator Profile (optional):**
- Controller-selected: `review-1`
- Selection basis: independently challenge exact-source support and report fidelity.

**Specification Coverage:**
- Verdict Phase 2 flow: Workbook → Wayfinding → Analyst → draft claims/implications → evidence/reasoning review → bounded correction → human decision/review boundary → report fidelity check.
- Wayfinding and the Foresight Controller are functions in the application initially, not separate agents.
- Review validates reasoning and exact statements, not only numeric source data.
- Review purpose is independent of effort profile; do not use `review` as an agent profile.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `schemas/analysis.schema.json`, `src/foresight_os/domain/models.py`, `src/foresight_os/runtime/maf_probe.py`
- Modify: `src/foresight_os/wayfinding.py`, `src/foresight_os/analysis/workbook.py`, `src/foresight_os/analysis/analyst.py`, `src/foresight_os/analysis/reviewer.py`, `src/foresight_os/artifacts/report.py`, `src/foresight_os/cli.py`, `tests/test_vertical_slice.py`, `tests/test_report_fidelity.py`
- Verify: `work/case-001/analysis.json`, `work/case-001/artifacts/`

**Dependencies:**
- Tasks 1–3 complete.
- The representative workbook case is approved for local use.

**Authority:**
- Preauthorized local actions: implement the local workbook boundary, MAF-backed single-agent/sequential steps, review checks, report rendering, and focused tests using the frozen fixture.
- Stop for: external data access, unbounded agent loops, unsupported workbook formats, report claims without evidence IDs, or the human decision/review boundary being bypassed for consequential recommendations.

**Steps:**
- [ ] Step 1: Have Wayfinding maintain the Work Brief with decision question, owner, horizon, criteria, scope, assumptions, deliverables, unresolved dependencies, and next useful step; allow provisional values without blocking unless materially necessary.
- [ ] Step 2: Extract reproducible workbook evidence locators and create draft claims, implications, and recommendation rationale with explicit basis and assessment.
- [ ] Step 3: Run evidence and reasoning review for period, units, population, calculation, opposing evidence, alternative explanations, assumptions, and recommendation sensitivity.
- [ ] Step 4: Consume the Task 2 vertical-slice guardrail (`max_agent_steps: 5` per role, `max_correction_rounds: 1`, `max_total_agent_calls: 3`), exercise correction and call exhaustion, and then exercise the human decision/review boundary; require acceptance for the benchmark case, persist the accepted revision, and generate a report whose material statements retain source record IDs.

**Verification:**
- [ ] `python -m pytest tests/test_vertical_slice.py tests/test_report_fidelity.py`
- Expected: the frozen case produces a valid analysis, rejected unsupported claims remain rejected or uncertain, accepted benchmark claims retain traceable locators, report wording matches the validated analysis, and assertions prove the shared step, correction, and total-call limits plus the exhaustion outcome and human-boundary routing.
- [ ] Direct boundary test with an invalid workbook locator and a contradictory evidence record.
- Expected: the run returns actionable validation/review results, does not silently accept the finding, and leaves no partial accepted recommendation.
- [ ] Reconstruct one representative operation from run ID, analysis revision, evidence IDs, and artifact metadata.
- Expected: the trace identifies the source, review decision, accepted revision, and generated artifact.

**Exit Criteria:**
- The vertical slice proves decision usefulness, evidence integrity, traceability, uncertainty, the benchmark’s formal acceptance gate, and report fidelity for one workbook case.

### Task 5: Add analytical continuation and dependency invalidation

**Purpose:**
- Make durable investigation continuity independent of the original chat and prevent stale conclusions from being reused silently.

**Task Function:**
- Recovery, revision, and dependency-invalidation implementation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: persistence and invalidation are cross-cutting safety behavior requiring one owner and explicit state transitions.

**Validator Profile (optional):**
- Controller-selected: `review-1`
- Selection basis: independently inspect fresh-session recovery, duplicate prevention, and invalidation propagation.

**Specification Coverage:**
- Analytical continuation loads the Work Brief `brief.md` and Analysis State `analysis.json`, then starts a new Run.
- Runtime resumption loads only a compatible MAF checkpoint.
- Changed workflow topology starts a new execution from analytical state rather than blindly rehydrating an incompatible checkpoint.
- When evidence, assumptions, or scope materially change, dependent outputs become candidates for reassessment; artifacts become stale.
- Fresh-Session checks: no lost evidence, stale recommendation, duplicated analysis objects, or chat-history dependence.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/persistence/analysis_store.py`, `src/foresight_os/runtime/capabilities.py`, `src/foresight_os/domain/models.py`
- Modify: `src/foresight_os/persistence/invalidation.py`, `src/foresight_os/persistence/recovery.py`, `src/foresight_os/cli.py`, `tests/test_invalidation.py`, `tests/test_recovery.py`
- Verify: `work/case-001/analysis.json`, `work/case-001/artifacts/`

**Dependencies:**
- Task 4 produces an accepted persisted investigation and artifact.

**Authority:**
- Preauthorized local actions: implement local revision loading, dependency traversal, invalidation metadata, fresh-process recovery tests, and safe retry/idempotency checks.
- Stop for: deleting historical evidence, silently rewriting prior revisions, resuming after topology change, or introducing a second runtime-state store.

**Steps:**
- [ ] Step 1: Record dependency edges from evidence through claims, implications, recommendations, and artifacts.
- [ ] Step 2: On material evidence, assumption, or scope change, mark dependent outputs for reassessment and artifacts stale while preserving prior revisions.
- [ ] Step 3: Implement separate commands or entry points for analytical continuation and compatible runtime checkpoint resumption.
- [ ] Step 4: Execute the Session-1/Session-2 scenario in a fresh process: analyze, close, load the Work Brief and Analysis State, add evidence, change scope, and start a new Run to regenerate the report.
- [ ] Step 5: Change an upstream assumption without changing supporting evidence; verify semantic reassessment of dependent outputs while the original evidence remains current.

**Verification:**
- [ ] `python -m pytest tests/test_recovery.py tests/test_invalidation.py`
- Expected: changed source evidence invalidates all reachable dependent outputs; unaffected branches remain current; historical revisions remain readable.
- [ ] Run the continuation flow in a fresh Session with no prior chat/session state.
- Expected: evidence and accepted decisions survive, stale outputs are not silently reused, and repeated recovery does not duplicate records.
- [ ] Change an upstream assumption without changing its evidence.
- Expected: dependent implications and recommendations require reassessment, dependent artifacts are stale, and the original evidence remains unchanged/current.
- [ ] Exercise duplicate delivery and interrupted execution.
- Expected: persistence is idempotent and compatible checkpoints resume only when topology and contract match.

**Exit Criteria:**
- The prototype can continue an Investigation across Sessions and can explain why any dependent Recommendation or Artifact must be reassessed.

### Task 6: Add bounded Foresight Controller selection and benchmark one extra pattern

**Purpose:**
- Let the Foresight Controller select the smallest useful execution without inventing arbitrary swarms.
- Add Concurrent or Handoff only if the evaluation proves measurable value over the baseline; otherwise retain single-agent or sequential review.

**Task Function:**
- Recipe policy, budget enforcement, and comparative evaluation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: policy selection is constrained by the evaluation contract and requires direct comparison.

**Validator Profile (optional):**
- Controller-selected: `review-1`
- Selection basis: independently verify recipe bounds and fair baseline comparison.

**Specification Coverage:**
- Foresight Controller owns coordination justification, recipe/profile choice, budgets, stopping/escalation rules, and partial-result behavior.
- Initial recipes are `DIRECT`, `ANALYZE`, and `ANALYZE_REVIEW`; one additional tested pattern may be selected only after benchmark evidence.
- Every recipe declares maximum agent calls, correction rounds, time/token budget, completion, escalation, and partial-result conditions.
- Foresight runtime roles use `purpose: execute | review` and `profile: low | normal | high | xhigh`; the build-time `Validator Profile` field is not runtime configuration.
- Start with coarse profile presets and provider/runtime telemetry; do not build custom token accounting or scheduler infrastructure.
- Native MAF patterns are used: Agent, Sequential, Concurrent, Handoff, HITL, and Checkpoint only where proven.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `evaluation/rubric.md`, `src/foresight_os/runtime/capabilities.py`, `src/foresight_os/analysis/reviewer.py`
- Modify: `src/foresight_os/controller/recipes.py`, `src/foresight_os/controller/policy.py`, `src/foresight_os/controller/profiles.py`, `src/foresight_os/controller/budgets.py`, `evaluation/run.py`, `tests/test_controller_selection.py`, `docs/intent/maf-capability-decision.md`
- Verify: `evaluation/results/`

**Dependencies:**
- Tasks 1–5 complete.
- The single-agent and sequential-review paths already pass the vertical-slice and recovery gates.

**Authority:**
- Preauthorized local actions: implement bounded recipe definitions, budget/stop enforcement, benchmark runners, and local comparative tests using the frozen case.
- Stop for: adding Group Chat or Magentic, unbounded dynamic orchestration, a new recipe without benchmark evidence, or a budget change that invalidates prior comparisons.

**Steps:**
- [ ] Step 1: Have the Foresight Controller read the Work Brief and produce an Execution Recipe, then implement `DIRECT`, `ANALYZE`, and `ANALYZE_REVIEW` with explicit bounds and partial-result contracts.
- [ ] Step 2: Implement only coarse presets such as normal/high/xhigh correction and step limits; consume provider/runtime telemetry where available and do not add custom token accounting.
- [ ] Step 3: Run level A with ordinary-prompt inputs and levels B/C with identical level-B inputs and evidence requirements through capable single-agent, semantic single-agent, bounded sequential-review, and Foresight Controller-selected paths; apply the common rubric and adjudication to all results.
- [ ] Step 4: Run a bounded, evaluation-only candidate probe for both `Concurrent` and `Handoff` using the same level-B inputs and acceptance rubric; compare each candidate against the semantic single-agent and sequential-review baselines without production admission, then admit at most one pattern only if its result passes the acceptance gate for measurable accepted-finding quality or recovery value within the accepted cost/latency budget; otherwise defer both.
- [ ] Step 5: Record the decision and defer unsupported patterns rather than creating speculative abstractions.

**Verification:**
- [ ] `python -m pytest tests/test_controller_selection.py`
- Expected: every run terminates within declared call, correction, and coarse profile bounds and reports completion, escalation, or partial-result state explicitly.
- [ ] `python evaluation/run.py --case evaluation/cases/case-001 --compare ordinary,semantic,sequential,controller`
- Expected: comparative results isolate ordinary-prompt value, Foresight semantic/governance value, sequential-review value, and additional coordination value.
- [ ] `python evaluation/run.py --case evaluation/cases/case-001 --probe-patterns concurrent,handoff --evaluation-only --compare semantic,sequential`
- Expected: both candidate probes run against the same level-B inputs and rubric, neither candidate is production-selectable before the gate, the report records both candidate results and their baseline comparison, at most one candidate is admitted only after passing the gate, and a failed or unsupported probe leaves both candidates deferred.
- [ ] Direct failure tests for budget exhaustion, review rejection, and partial upstream output.
- Expected: no accepted recommendation is emitted when required evidence or review conditions are unmet.

**Exit Criteria:**
- The Foresight Controller can choose one agent and can justify any additional coordination with reproducible evidence; no orchestration feature is included merely because MAF supports it.

### Task 7: Expose one required client and gate the second as stretch

**Purpose:**
- Validate durable continuation through a real user-facing boundary only after the local workflow and recovery contracts are proven.

**Task Function:**
- Client adapter and continuation-flow integration.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: client work must consume the canonical CLI/domain contracts rather than create a second orchestration layer.

**Validator Profile (optional):**
- Controller-selected: `review-1`
- Selection basis: independently exercise continuation, challenge, scope-change, and report commands.

**Specification Coverage:**
- One real client integration is required for v0.1; a second client is a stretch gate unless portability is explicitly accepted as a v0.1 release objective.
- Required flows: continue an investigation, challenge a finding, exclude a region and reassess, and create an executive report.
- Clients must load durable state rather than depend on previous chat history.

**Required Skills:**
- `skill-backend-verification`
- `skill-full-stack-integration` only when the selected client crosses a service/API boundary

**Files And Symbols:**
- Inspect: `src/foresight_os/cli.py`, `src/foresight_os/persistence/recovery.py`, `schemas/analysis.schema.json`
- Modify: `src/foresight_os/clients/first_client_adapter.py`, optional `src/foresight_os/clients/second_client_adapter.py`, `tests/test_client_continuation.py`, `README.md`
- Verify: client-specific command or adapter contract tests and a persisted `work/<investigation-id>/` Investigation fixture

**Dependencies:**
- Tasks 1–6 complete.
- The first client choice and any external authentication boundary are approved; keep the second client out until the first passes and the v0.1 portability objective is explicitly accepted.

**Authority:**
- Preauthorized local actions: add adapters over the canonical local commands and run approved local contract tests with synthetic or approved fixture data.
- Stop for: credentials, external publication, client-specific duplicate schemas, client-specific workflow logic, or a client boundary that cannot preserve evidence IDs and revision semantics.

**Steps:**
- [ ] Step 1: Expose the canonical local commands for continue, challenge, scope-change/reassess, and report generation.
- [ ] Step 2: Integrate one selected client and prove all four flows from a fresh Session.
- [ ] Step 3: If portability is an explicit v0.1 objective, add the second client only after the first client’s evidence and continuation contract is stable; otherwise record it as a v0.2 stretch item.
- [ ] Step 4: Document that all clients consume the same durable state and do not own analytical truth.

**Verification:**
- [ ] `python -m pytest tests/test_client_continuation.py`
- Expected: the required client invokes the canonical state and commands, preserves IDs and revisions, and continues without the original chat transcript; a second client is tested only when the stretch gate is accepted.
- [ ] Direct failure test with stale artifact and unsupported scope change.
- Expected: the client surfaces reassessment rather than presenting stale output as current.

**Exit Criteria:**
- One client is proven through the canonical durable-state contract; a second client is either proven under the explicit portability gate or recorded as a v0.2 stretch item.

### Task 8: Reconcile documentation, deferrals, and final evidence

**Purpose:**
- Produce a truthful handoff that matches implemented behavior, evaluation output, and known limits.

**Task Function:**
- Final artifact reconciliation and acceptance verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance requires one Implementation Controller to reconcile code, tests, documentation, generated artifacts, and Implementation Plan state.

**Validator Profile (optional):**
- Controller-selected: `review-1`
- Selection basis: independent completion check against repository evidence and the verdict’s deferral list.

**Specification Coverage:**
- Final product principle: decision usefulness, evidence integrity, traceability, explicit uncertainty, reasoning quality, right-sized coordination, then agent sophistication.
- No unrecorded scope expansion, stale claims, missing proof, or deferred feature leakage.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: all changed files, `evaluation/results/`, `README.md`, `docs/intent/maf-capability-decision.md`
- Modify: `README.md`, `docs/intent/maf-capability-decision.md`, `docs/superpowers/plans/foresight-os-v0-1-bounded-prototype.md`
- Verify: `schemas/analysis.schema.json`, `tests/`, `evaluation/results/`, `work/`

**Dependencies:**
- Tasks 1–7 complete with fresh task-local evidence.

**Authority:**
- Preauthorized local actions: reconcile documentation and Implementation Plan evidence, run final local checks, and record limitations or deferrals.
- Stop for: failed required checks, missing evaluation results, stale task states, unverified external integrations, or any need to claim production readiness.

**Steps:**
- [ ] Step 1: Compare documentation, schemas, tests, fixtures, and implemented behavior; remove claims not supported by source or fresh evidence.
- [ ] Step 2: Keep `README.md` as stable product architecture, keep `docs/intent/maf-capability-decision.md` limited to the empirical MAF decision record, keep this plan as temporary implementation truth, and keep evaluation results as empirical evidence.
- [ ] Step 3: Record benchmark results, known gaps, selected/deferred MAF patterns, and recovery limitations.
- [ ] Step 4: Run the final verification set and update this Implementation Plan only after evidence exists; do not mark it completed from checked boxes alone.

**Verification:**
- [ ] `python -m pytest`
- Expected: all required tests pass with failures and skips recorded.
- [ ] `python evaluation/run.py --case evaluation/cases/case-001 --compare ordinary,semantic,sequential,controller --write-report evaluation/results/case-001.md`
- Expected: the report contains reproducible A/B/C metrics, comparison inputs, accepted limitations, and recovery results.
- [ ] `python -m compileall src tests`
- Expected: the implemented runtime compiles cleanly.

**Exit Criteria:**
- Every outcome and task is proven, all deviations and deferrals are recorded, documentation matches repository truth, and final verification returns `verified` before the plan status changes to `completed`.

## Verification

Use this section for final artifact-level verification only.

- `python -m pytest`
- `python evaluation/run.py --case evaluation/cases/case-001 --compare ordinary,semantic,sequential,controller --write-report evaluation/results/case-001.md`
- `python -m compileall src tests`
- Fresh-process continuation scenario: create an Investigation → close the process → load `brief.md` and `analysis.json` → add evidence/change scope → reassess dependents → start a new Run → regenerate the report.
- Inspect the final `analysis.json` and report to confirm every material statement has evidence IDs, review status, revision, and no silently current stale artifact.
- Run the repository contract validator available from the project or shared Project OS installation once Git metadata and the validator are available.

## Completion Criteria

The plan is ready for completion verification when:

1. the evaluation contract is frozen before Foresight Controller implementation and separates ordinary-prompt, semantic, and coordination value
2. MAF fit is proven for only the required native capabilities, or blocked limitations are recorded
3. every tested MAF capability has one explicit decision: `USE_NATIVE`, `ADAPT_AT_BOUNDARY`, `DEFER`, or `UNSUPPORTED`
4. the Work Brief schema and `brief.md` contract are distinct from Execution Recipe, Run, Session, Analysis State, and Artifact
5. evidence, claims, implications, recommendations, relationships, revisions, and artifacts validate against one canonical schema, with no new domain record added without a concrete workflow need
6. workbook evidence is reproducible from file version, sheet, range, units, transformation, and calculation
7. the vertical slice validates reasoning and report fidelity through a human decision/review boundary, not only source numbers
8. analytical continuation and runtime resumption are separate, explicit behaviors
9. changed evidence, assumptions, or scope triggers dependency reassessment and stale-artifact handling
10. the Foresight Controller consumes a Work Brief, emits bounded coarse recipes, and may correctly select one agent
11. any Concurrent or Handoff addition is justified by comparative evaluation, not framework availability
12. one required client passes through the canonical durable-state contract; a second is either proven under an explicit portability gate or recorded as a v0.2 stretch item
13. README, the MAF decision record, the Implementation Plan, and evaluation results each have one clear ownership role without duplicated architectural truth
14. deferred features remain absent unless a recorded evaluation failure proves necessity
15. every required task and task-local verification item is complete
16. plan deviations, substitutions, blockers, and deferrals are recorded
17. changed code, configuration, tests, validators, documentation, and generated outputs are reconciled with current repository truth
18. final verification commands are identified and runnable

The plan may be marked `completed` only when `skill-verification-before-completion`:

1. runs fresh final verification
2. confirms completion criteria against repository evidence
3. finds no unresolved required task, failed required check, stale status, or unrecorded scope deviation
4. returns `verified`; the Implementation Controller then updates Implementation Plan status

A checked box records progress; it is not proof by itself.
