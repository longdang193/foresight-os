---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: foresight-os-closure-release
targets:
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/wayfinding.py
  - src/foresight_os/controller/
  - src/foresight_os/domain/
  - src/foresight_os/persistence/
  - src/foresight_os/analysis/
  - src/foresight_os/runtime/metrics.py
  - evaluation/
  - evaluation/reference/
  - tests/
  - data/exercise/
  - README.md
  - pyproject.toml
---

# Foresight OS Closure Release Plan

## Goal

Close the three previously delivered increments with one bounded release that proves execution correctness, trustworthy analytical review, and real selective reuse. Preserve the existing Microsoft Agent Framework runtime, one Controller, one `AnalysisState`, one capability resolver, deterministic data tools, and NetworkX as a derived projection.

The completed Power BI PBIP/PBIR deliverable is a baseline capability and is outside this plan. This plan does not reopen, redesign, or contradict that completed work.

Governing review input: the user-provided verdict received on 2026-10-13 at `C:\Users\HOANG PHI LONG DANG\.codex\attachments\66ab76ab-d21e-4116-9f35-4d3958bddaec\Pasted text.txt`.

The verdict establishes five ordered gates inside the three increments: (1) Increment A execution integrity, (2) Increment B epistemic integrity, (3) Increment B genuine adversarial integration, (4) Increment C durable selective reuse, and (5) cross-increment evidence of stability and release readiness.

## Implementation Outcomes

### Increment A — Correct, bounded execution

Every `WorkStage` produces exactly one executable stage specification, receives the original stage input unchanged, and executes with capabilities derived from the review or research objective rather than a hard-coded purpose branch. Wayfinding is generic, dependencies and objectives are preserved, specialists are independent from execution topology, and all five native MAF patterns retain deterministic contract coverage.

### Increment B — Trustworthy analytical review

A single canonical material-dependency index supplies review fingerprints, invalidation, graph context, `FindingView`, and selective reassessment. Review validity includes evidence, calculations, assumptions, dependencies, counterevidence, and skill implementation identity. A declared `ReviewPolicy` drives acceptance, and selected analytical skills produce typed objections that become immutable `ReviewRecord` outcomes and a complete derived finding view.

### Increment C — Restartable selective reuse with evidence

Committed `StageReceipt` records persist the minimum provenance needed for fresh-process reuse. Reuse revalidates status, fingerprints, authorization/data scope, referenced records, and provenance; reassessment follows dependency impact instead of caller-provided cache hints. Evaluation reports distinguish model/tool/external work, latency, resources, cache hits, reused stages, reassessed stages, accepted findings, and human corrections.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-plan-document-reviewer`, `skill-executing-plans`, `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `verified per-gate checkpoint commits preauthorized; no push or merge without separate authorization`
- Preauthorized local actions: edit the declared canonical sources and tests, run declared local checks, update the proposed plan ledger, and preserve existing untracked outputs
- User-approval actions: push, merge, publication, external writes, destructive recovery, deletion or cleanup of preserved untracked outputs, and architecture changes beyond the listed owners
- Parallel ownership: none; the shared dependency index and review contracts require sequential integration
- Sequential fallback: Tasks 1–2, Increment A gate; Tasks 3–4, Increment B gate; Task 5, Increment C gate; Task 6, final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `9c4f47f568ddad0780a4e196e0ec04db873ec6b8`
- Expected workspace: `main` with preserved untracked `build/`, `src/foresight_os.egg-info/`, and `work/` outputs; those outputs are not to be modified or deleted
- Next action: completed; preserve the verified work in a local checkpoint commit.
- Blockers: none for the declared local scope; optional external providers remain explicitly unverified boundaries.

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 0 | `completed` | current | `codex` | none | green baseline and toolbelt probe reconciliation | `work/closure-final-20261013/toolbelt`, `work/closure-final-20261013/optimization/baseline.json`, contract/controller outputs |
| Task 1 | `completed` | current | `codex` | Task 0 | input-preservation and generic Wayfinding tests | full `python -m pytest -q` pass; focused workflow/Wayfinding coverage |
| Task 2 | `completed` | current | `codex` | Task 1 | RecipeStage compilation, overrides, routing, and capability tests | full `python -m pytest -q` pass; `work/closure-final-20261013/controller.md` |
| Task 3 | `completed` | current | `codex` | Task 2 | typed relation index and fingerprint invalidation tests | full `python -m pytest -q` pass; review/invalidation test coverage |
| Task 4 | `completed` | current | `codex` | Task 3 | policy-driven typed objections and durable review outcomes | full `python -m pytest -q` pass; policy/review coverage |
| Task 5 | `completed` | current | `codex` | Task 4 | fresh-process receipt reuse and impact-directed reassessment | `work/closure-release-20261013/selective-reuse/fresh-process`, full `python -m pytest -q` pass |
| Task 6 | `completed` | current | `codex` | Task 5 | thresholds, strategic probes, resource stability, and clean packaging | `work/closure-final-20261013/optimization`, `work/closure-release-20261013/strategic`, `work/closure-release-20261013/wheel`, `git diff --check` |
**Execution Evidence:**

- Full suite: `python -m pytest -q` passed with all tests green.
- Static hygiene: `python -m compileall -q src evaluation tests` and `git diff --check` passed.
- Contract/controller/toolbelt: contract matrix, controller matrix, and toolbelt probe passed; `powerbi_project_read` is discovered and verified.
- Optimization: baseline/release receipts share schema, each report one accepted finding, and comparison accepted with p95 regression `-0.057%`, peak allocation regression `0.067%`, and no tool-call increase.
- Selective reuse: fresh-process probe passed with two cache hits, zero model calls, and zero reassessed stages.
- Strategic isolation: five exercise workbooks were hashed and the validator was denied to participants.
- Packaging: clean-wheel smoke passed with import path outside the repository.

## Task Breakdown

### Task 0: Reconcile the green baseline

**Purpose:**
- Establish a truthful causal baseline before closure changes begin.
- Fix the Analyst toolbelt probe regression caused by the completed Power BI capability registration without changing Power BI implementation semantics.

**Task Function:**
- Reconcile current local capability discovery with the existing probe contract and record fresh baseline evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: narrow integration-probe repair with known ownership and no architecture change.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independently confirm the baseline failure is isolated to probe capability discovery and that Power BI semantics remain untouched.

**Specification Coverage:**
- The baseline at `9c4f47f` is green for implementation tests, compilation, contract matrix, controller matrix, and Analyst toolbelt probing.
- `powerbi_project_read` is discovered and asserted as a current local capability; PBIP/PBIR implementation is not reopened.
- `evaluation/probes/optimization_measurement.py` is the shared baseline/release measurement harness. It emits one schema for accepted `FindingView` count, RSS/resource metrics, per-stage metrics, model/tool/external calls, latency, cache hits, reused stages, reassessed stages, and failure class; values come from observed execution rather than hard-coded fixtures.
- The same pinned baseline workload, environment, metric definitions, sampling procedure, and harness produce immutable performance/resource receipts before closure implementation changes and again at release.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect and modify `evaluation/probes/run_toolbelt_probe.py` and its tests.
- Add `evaluation/probes/optimization_measurement.py` as the shared baseline/release measurement harness and route both modes through its receipt schema.
- Inspect `src/foresight_os/runtime/participants.py:bind_local_toolbelt` only to confirm the declared capability set.
- Verify the baseline commands and record immutable correctness/performance run IDs in task evidence.

**Dependencies:**
- None; this gate precedes all closure work.

**Authority:**
- Preauthorized local actions: update the toolbelt probe and focused tests, run current CI locally, create the Task 0 checkpoint commit, and record baseline evidence.
- Stop for: any change to Power BI implementation semantics, external provider access, deletion of preserved outputs, push/merge, or unrelated probe redesign.

**Steps:**
- [x] Make the probe discover or enumerate all capabilities returned by `bind_local_toolbelt`, including `powerbi_project_read`, instead of indexing an incomplete static ID list.
- [x] Add a regression assertion that every bound local capability has a probe mapping and that the probe does not silently skip an unknown capability.
- [x] Implement `evaluation/probes/optimization_measurement.py` as the single measurement path for baseline and release receipts; collect observed accepted `FindingView` values, resource snapshots, per-stage metrics, calls, latency, cache/reassessment counts, and failure classes without hard-coded measurement values.
- [x] Run the current implementation tests, compilation checks, contract matrix, controller matrix, and Analyst toolbelt probe.
- [x] Run `python evaluation/probes/run_optimization_probe.py --mode baseline --fixture tests/fixtures/analyst_multisheet.xlsx --output work/closure-final-20261013/optimization/receipt.json`.
- [x] Run `python evaluation/run.py --matrix contract --output-root work/closure-final-20261013/contract` and `python evaluation/run.py --matrix controller`; run `python evaluation/probes/run_toolbelt_probe.py --output-root work/closure-final-20261013/toolbelt`.
- [x] Capture `python --version`, dependency/package version, OS/runtime identity, workload paths, sampling settings, and metric schema beside the receipts.
- [x] Record baseline SHA `9c4f47f`, command results, and correctness/performance run IDs before starting Task 1; never use existing `work/toolbelt-probes` or `work/optimization-*` paths.

**Verification:**
- [x] Run the focused toolbelt probe, current CI-equivalent baseline checks, and the baseline optimization receipt commands above.
- Expected: baseline is green, `powerbi_project_read` is covered, reproducible receipts exist under the unique disposable root, and no Power BI source implementation file changes.

**Exit Criteria:**
- A green baseline checkpoint exists at the known base commit plus the minimal probe fix.
- Later failures can be attributed to closure work rather than this pre-existing probe regression.

### Task 1: Restore stage-input integrity and generic Wayfinding

**Purpose:**
- Eliminate the release-blocking defect where budget-limit values can replace the actual stage input before agent execution.
- Make production Wayfinding normalize explicit planning information rather than inventing capacity or contradiction stages from an evaluation fixture.

**Task Function:**
- Correct runtime state handling and separate generic planning from fixture-only strategic scenarios.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: direct, localized correctness fix with clear source ownership; no delegated benefit is required.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independently inspect the changed state flow and fixture boundary for regression or hidden input mutation.

**Specification Coverage:**
- Stage input equals the input received by orchestration for Direct, Sequential, Concurrent, Handoff, and Group Chat.
- Generic Wayfinding normalizes explicit planning information; when no stages are justified it returns `stages = []` and preserves open dependencies/uncertainty for Controller fallback rules.
- `WorkBrief.horizon` is first-class and backward-compatible with the existing `horizon` input.

**Required Skills:**
- `skill-backend-verification`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify `src/foresight_os/runtime/workflow.py:run_recipe_async` and nested `dispatch_stage`.
- Modify `src/foresight_os/wayfinding.py:create_work_brief` and `src/foresight_os/domain/models.py:WorkBrief` for explicit normalization and first-class horizon.
- Extend focused workflow, Wayfinding, and pattern tests under `tests/`.

**Dependencies:**
- Task 0 complete.

**Authority:**
- Preauthorized local actions: edit workflow/Wayfinding sources and focused tests, run the five-pattern deterministic suite, and record results in this plan.
- Stop for: public architecture changes, external provider access, deletion of preserved outputs, or changes to the `AnalysisState` contract.

**Steps:**
- [x] Introduce distinct `stage_input`, `limit_value`, and existing-budget values in the budget-limit loop; never reassign the orchestration input variable.
- [x] Pass unchanged `stage_input` to agent invocation and preserve it in receipts or diagnostics where applicable.
- [x] Make `create_work_brief` normalize `decision_question`, scope, horizon, assumptions, explicit stages, research needs, and desired output.
- [x] Return no invented stages when none are justified; preserve open dependencies/uncertainty and let Controller fallback rules handle simple execution.
- [x] Move capacity/contradiction stages and cost metadata into an explicit evaluation fixture; keep production `create_work_brief` generic.
- [x] Add regression cases for short and long inputs across all five MAF patterns, including input that resembles a budget value.
- [x] Add an insufficient-information Wayfinding case and assert `stages == []`, preserved uncertainty, and Controller fallback behavior.
- [x] Add backward-compatible horizon assertions and prevent missing horizon information from becoming a misleading invented assumption.

**Verification:**
- [x] Run `python -m pytest -q tests/test_orchestration_patterns.py tests/test_runtime_boundaries.py tests/test_controller_selection.py tests/test_analysis_schema.py`.
- Expected: every pattern observes the exact original input; generic Wayfinding returns only explicit stages or `stages == []` with preserved uncertainty; the command exits `0`.

**Exit Criteria:**
- The input-corruption regression is fixed and covered, production Wayfinding is generic, and Increment A cannot proceed with a failing preservation test.

### Task 2: Compile one RecipeStage per WorkStage and separate routing from specialists

**Purpose:**
- Make the Controller-to-runtime handoff auditable and eliminate synthetic stages caused by pattern-count padding.
- Decouple specialist selection from execution topology and derive reviewer capabilities from the actual review objective.

**Task Function:**
- Normalize planning output into one bounded execution specification per stage.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: contract refactor spans controller and participant assembly, but remains within known owners and requires sequential integration.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: verify routing/topology independence and least-privilege reviewer capabilities.

**Specification Coverage:**
- `WorkStage -> RecipeStage` is one-to-one, preserving objective, dependencies, participants, skill IDs, research needs, capabilities, pattern, expected result, and limits.
- Specialist identity and execution topology are independent decisions.
- Review capabilities derive from research needs, selected skills, and review objective while preserving least privilege.

**Required Skills:**
- `skill-backend-verification`
- `skill-code-standards`

**Files And Symbols:**
- Modify `src/foresight_os/controller/policy.py:_recipe_for_patterns` and `select_recipe`.
- Modify `src/foresight_os/controller/recipes.py:RecipeStage` and `make_recipe`.
- Modify `src/foresight_os/controller/task_shape.py:TaskShape`, `src/foresight_os/domain/models.py:WorkStage`, and `src/foresight_os/runtime/participants.py:ParticipantConfig` / `AgentFactory.create`.
- Extend controller, participant, capability, and pattern tests.

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: edit Controller, RecipeStage, task-shape, participant, and test contracts for one-to-one compilation and objective-based capabilities; run local checks and create the Increment A checkpoint after verification.
- Stop for: a second orchestrator, changed MAF pattern semantics, widened default capabilities, external execution, or unrelated persistence-schema changes.

**Steps:**
- [x] Replace `max(len(patterns), len(work_stages))`-style padding with exact iteration over `WorkStage` objects; fail clearly when a stage lacks a valid pattern.
- [x] Reuse and extend `RecipeStage` as the canonical compiled execution contract; do not introduce a parallel `CompiledStage` type.
- [x] Make repeated per-stage patterns legal and define precedence as stage override, global WorkBrief default, Controller structural selection, then safe fallback.
- [x] Define the legacy global override deterministically: a scalar is the WorkBrief default; a list must satisfy `len(pattern_list) == len(work_stages)`, maps positionally, allows repeated values, and never determines stage count.
- [x] Resolve specialist participants separately from pattern selection; do not imply Handoff from dynamic specialist selection.
- [x] Derive source, numerical, and red-team reviewer capabilities from objective, research needs, and skills with least-privilege assertions.
- [x] Preserve dependency order, stage IDs, and expected-result metadata through compilation and dispatch.

**Verification:**
- [x] Run `python -m pytest -q tests/test_controller_selection.py tests/test_research_needs.py tests/test_orchestration_patterns.py tests/test_tool_enabled_patterns.py` and `python evaluation/run.py --matrix controller --write-report work/closure-final-20261013/controller.md`.
- Expected: five WorkStages produce five RecipeStages regardless of pattern distribution; scalar/list override behavior is deterministic; no synthetic stage appears; routing and capability assertions pass; the command exits `0`.

**Exit Criteria:**
- Increment A has one auditable stage specification per WorkStage and independently testable routing, specialist, and reviewer-permission decisions.

### Task 3: Build the canonical material-dependency index and review identity

**Purpose:** Make material closure consistent without conflating fingerprinting, invalidation, graph context, counterevidence, and reassessment semantics; prevent stale review approval when analytical inputs, skill content, or policy identity changes.

**Task Function:**
- Consolidate dependency traversal and immutable review fingerprint construction.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: high-impact domain/persistence contract work requires one coherent source of truth.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: inspect closure completeness, authority boundaries, and stale-review behavior.

**Specification Coverage:**
- One derived typed `RelationIndex` records direct support, analytical support, counterevidence, provenance dependencies, forward/reverse impact, calculation inputs, and assumptions.
- Distinct traversals—`material_closure`, `impact_closure`, `support_context`, and `counterevidence_context`—operate over the same indexed semantics.
- Direct evidence remains authoritative through `AnalyticalRecord.evidence_ids`; analytical support remains canonical `Relationship` data.
- Fingerprints include skill ID/version/content hash and `ReviewPolicyResolver` policy ID/version/hash, but exclude unrelated global `AnalysisState` revision.
- `ReviewRecord` remains immutable and validity is derived from current versus reviewed fingerprint.

**Required Skills:**
- `skill-backend-verification`
- `skill-code-standards`

**Files And Symbols:**
- Modify `src/foresight_os/domain/challenge.py:collect_material_inputs`, `build_material_fingerprint`, `review_validity`, and `select_review_record`.
- Inspect `src/foresight_os/domain/models.py:AnalyticalRecord`, `Relationship`, `AnalysisState`, and evidence/calculation models.
- Modify `src/foresight_os/persistence/invalidation.py` and graph-context helpers to consume the shared index; keep NetworkX derived.
- Extend `tests/test_review_records.py`, `tests/test_invalidation.py`, graph tests, and evidence workflow tests.

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: edit challenge, model, invalidation, graph-context, and focused tests to establish the typed relation index and content-aware fingerprints; create the Increment B checkpoint only after Task 4 verification.
- Stop for: a graph database, a new Finding store, changed direct-evidence authority, numeric probability confidence, or historical-review deletion.

**Steps:**
- [x] Define the derived typed `RelationIndex` and relation direction/type rules for support, counterevidence, provenance, impact, calculations, inputs, assumptions, and dependencies.
- [x] Implement distinct material, impact, support-context, and counterevidence traversals over that index; keep NetworkX as a derived projection.
- [x] Route each consumer through the appropriate typed traversal instead of separate ad hoc walks, preserving its distinct semantics.
- [x] Add skill registry identity fields—skill ID, version, and content hash—to review fingerprints.
- [x] Include `policy_id`, `policy_version`, and optional `policy_hash` in `ReviewRecord` identity and compare them with the current policy at acceptance time.
- [x] Preserve `AnalyticalRecord.evidence_ids` as direct-evidence authority and analytical-to-analytical support in `Relationship`.
- [x] Add transitive evidence and `depends_on` fixtures proving material changes stale the right review while unrelated changes do not.

**Verification:**
- [x] Run `python -m pytest -q tests/test_review_records.py tests/test_invalidation.py tests/test_persistence.py tests/test_evidence_workflow.py`.
- Expected: changed transitive evidence/calculation/dependency/skill resources change the target fingerprint; unrelated `AnalysisState` updates do not; the command exits `0`.

**Exit Criteria:**
- Increment B epistemic integrity passes with one shared material-dependency source and complete, immutable, content-aware review identity.

### Task 4: Integrate skills, typed objections, ReviewPolicy, and FindingView

**Purpose:** Prove that selected analytical skills genuinely govern durable review outcomes and provide one acceptance answer plus a complete decision-facing finding projection.

**Task Function:**
- Connect adversarial review execution to typed objections, durable records, and derived acceptance state.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-domain integration must be one coherent vertical slice before reuse depends on it.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: challenge objection validation, policy acceptance, and blocked-research semantics independently.

**Specification Coverage:**
- `src/foresight_os/controller/policy.py:ReviewPolicyResolver` is the sole owner of deterministic policy selection. Its authoritative inputs are target kind, presence of `ResearchNeedKind.QUANTITATIVE_ANALYSIS`, and an explicit backward-compatible `WorkBrief.consequence_level` (`standard` or `high`). It maps to this fixed v1 table: standard recommendation → `source-appraisal` + `red-team-claim`; quantitative recommendation → `quantitative-sanity-check` + `red-team-claim`; high-consequence recommendation → `key-assumptions-check` + `red-team-claim` + `abstain-or-escalate`. Overlap precedence is high-consequence > quantitative > standard; missing/unknown classification falls back to standard and records an unresolved classification issue. Callers do not attach independently editable policies to findings or manually supply skill IDs to decide acceptance.
- Selected skills produce typed `ChallengeObjection` values that become durable `ReviewRecord` outcomes.
- Proof rules are objection-specific: `SOURCE_CONTRADICTION` needs evidence IDs; `CALCULATION_ERROR` needs calculation/input provenance; `UNSUPPORTED_ASSUMPTION` needs target plus rationale; `ALTERNATIVE_HYPOTHESIS` needs a coherent competing explanation; `FAILURE_MODE` is explicitly hypothetical; `INSUFFICIENT_EVIDENCE` records the missing-evidence boundary.
- `FindingView` remains derived and includes counterevidence, confidence rationale, disconfirmation conditions, unresolved issues, implications, and monitoring indicators. `unknowns` comes from `AnalyticalRecord.uncertainty`, `ReviewRecord.unresolved_issues`, and blocked/missing material inputs; monitoring indicators come only from an explicit analytical metadata field, not a scheduler.

**Required Skills:**
- `skill-backend-verification`
- `skill-full-stack-integration`

**Files And Symbols:**
- Modify `src/foresight_os/domain/challenge.py:ReviewRecord`, `ChallengeObjection`, `ChallengeProposal`, `review_validity`, `derive_finding_views`, and `accepted_consequential_recommendation`.
- Add `src/foresight_os/controller/policy.py:ReviewPolicyResolver` as the sole policy-selection owner; `challenge.py` records policy identity and evaluates outcomes but does not own policy definitions or a second mutable policy store.
- Modify `src/foresight_os/analysis/reviewer.py:review_reasoning` and `ReviewResult`.
- Inspect skill delivery in `src/foresight_os/controller/skills.py` and `src/foresight_os/skills/`.
- Update `src/foresight_os/artifacts/report.py` and end-to-end tests in `tests/test_review_records.py` and `tests/test_evidence_workflow.py`.

**Dependencies:**
- Task 3 complete.

**Authority:**
- Preauthorized local actions: edit review, skill, report, and test surfaces for the typed objection-to-ReviewRecord vertical slice and unified acceptance policy; create the Increment B checkpoint after verification.
- Stop for: human-approval substitution, external publication, invented evidence citations, weakened least privilege, or in-place mutation of immutable history.

**Steps:**
- [x] Add backward-compatible `WorkBrief.consequence_level` and implement the fixed v1 policy table above, including policy ID, version, required skill IDs, acceptable outcome set, blocking-objection rules, overlap precedence, and standard fallback; record policy identity on historical reviews.
- [x] Add tests for standard, quantitative, high-consequence, overlapping quantitative/high-consequence, and missing/unknown classification inputs.
- [x] Make selected skill invocation produce typed objections and durable disposition records; keep blocked research distinct from no counterevidence.
- [x] Replace universal evidence requirements with objection-specific validation tests for every objection type. Make `ChallengeObjection` the durable validation contract; retain `ChallengeProposal` only as an aggregation DTO if useful.
- [x] Require current policy reviews, acceptable outcomes, no blocking unresolved objections, and required evidence/calculations for acceptance; define final acceptance as all required reviews `CURRENT` with outcome `ACCEPTED`, while `PROVISIONAL` remains a distinct non-final disposition.
- [x] Expand `FindingView` and reports from the typed index without a second mutable finding authority. Source `unknowns` from uncertainty, unresolved issues, and missing inputs; add `AnalyticalRecord.monitoring_indicators` as metadata only, never as a monitoring service.

**Verification:**
- [x] Run `python -m pytest -q tests/test_review_records.py tests/test_evidence_workflow.py tests/test_group_chat.py tests/test_adversarial_review_integration.py`.
- [x] Exercise the fixed v1 policies with `red-team-claim`, `key-assumptions-check`, a calculation objection, and an insufficient-evidence case.
- Expected: selected skills change durable review outcome; accepted, provisional, rejected, and blocked states are distinct and deterministic; the derived view contains support, counterevidence, rationale, assumptions, unknowns, disconfirmation, implications, and monitoring fields.

**Exit Criteria:**
- Increment B is complete only when the genuine skill-driven adversarial path is proven end to end and acceptance has one policy-defined answer.

### Task 5: Persist trustworthy StageReceipts and implement impact-directed reuse

**Purpose:** Replace caller-provided ad hoc cache entries with restartable, persisted, provenance-complete stage receipts and make selective reassessment real.

**Task Function:**
- Implement receipt lifecycle, reuse eligibility, authorization revalidation, and dependency-directed descendant reassessment.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: persistence and runtime lifecycle are tightly coupled and require one owner for commit semantics.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: inspect fresh-process reuse, authorization boundaries, incomplete provenance, and unrelated-record reuse.

**Specification Coverage:**
- Persist minimal `StageReceipt` records beside `AnalysisState` through the existing `AnalysisStore`; do not add them to `AnalysisState`, Redis, or another database.
- Receipt contains stage ID, input fingerprint, skill hashes, capability fingerprints, model-config fingerprint, semantic authorization-scope fingerprint, canonical result references, result fingerprints/content hashes, and committed status.
- Cross-process reuse is allowed only for committed stages whose outputs were materialized into canonical durable records; it also requires matching fingerprints, current records, semantic authorization revalidation, and complete provenance.
- Reuse canonical record IDs and reassess only affected descendants.

**Required Skills:**
- `skill-backend-verification`
- `skill-performance-optimization`

**Files And Symbols:**
- Modify `src/foresight_os/persistence/analysis_store.py` for a sidecar `stage-receipts.json` lifecycle using the existing file-lock and atomic temp-write/fsync/replace pattern; keep `AnalysisState` analytical truth only.
- Modify `src/foresight_os/persistence/invalidation.py` for shared impact-directed invalidation.
- Integrate receipt production/consumption in `src/foresight_os/runtime/workflow.py` and controller execution paths.
- Add `evaluation/probes/run_selective_reuse_probe.py` as the named fresh-process acceptance entry point and extend `tests/test_selective_reuse.py`, persistence/authorization tests, and probe coverage.

**Dependencies:**
- Tasks 3 and 4 complete.

**Authority:**
- Preauthorized local actions: edit AnalysisStore, invalidation, runtime receipt integration, and reuse tests/probes using existing local persistence only; create the Increment C checkpoint after verification.
- Stop for: a new database/cache service, bypassed authorization, deleted receipts/records, external writes, or reuse with incomplete provenance.

**Steps:**
- [x] Define the minimal sidecar receipt schema and committed transition; interrupted or incomplete stages are ineligible.
- [x] Mark arbitrary conversational text, intermediate objects, and aggregates without canonical record IDs as non-reusable; do not add a second payload cache.
- [x] Record canonical result references plus result fingerprints/content hashes and input, skill, capability, model, and semantic authorization fingerprints. Never persist API keys, OAuth tokens, or raw credentials.
- [x] Revalidate fingerprints, result content hashes, record currency, authorization scope, and provenance on load, including in a fresh process; resolve capabilities again against current semantic scope.
- [x] Use the canonical dependency index to compute affected descendants and leave unrelated receipts reusable.
- [x] Add restart and mutation scenarios proving affected descendants rerun and invalid receipts are rejected rather than silently refreshed.

**Verification:**
- [x] Run `python -m pytest -q tests/test_selective_reuse.py tests/test_persistence.py` with reports under `work/closure-final-20261013/selective-reuse/`.
- [x] Run `python evaluation/probes/run_selective_reuse_probe.py --output-root work/closure-final-20261013/selective-reuse/fresh-process` from a fresh interpreter process.
- Expected: only canonicalized unchanged stages reuse; arbitrary conversational stages do not; affected descendants reassess; unrelated stages remain reusable; stale, unauthorized, incomplete, and non-committed receipts do not reuse; the probe writes a machine-readable report and exits `0` only when all assertions pass.

**Exit Criteria:**
- Increment C is complete only when reuse survives restart and dependency/authorization changes with measurable reassessment savings.

### Task 6: Produce release-grade performance, probe, stability, and packaging evidence

**Purpose:** Replace weak optimization gates with evidence that can reject a materially unhealthy release and cover the bounded closure.

**Task Function:**
- Build corrected evaluation receipts, systematic probes, strategic fixtures, resource measurements, and final package/documentation reconciliation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final evidence spans evaluation and packaging but is verification-owned, not a new product architecture.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: inspect comparator thresholds, resource evidence, probe failure handling, and clean-wheel claims independently.

**Specification Coverage:**
- Metrics separate model calls, tool calls, external requests, tokens, total latency, per-pattern latency, tool time, queue wait, RSS, active tasks, threads, processes, handles, cache hits, reused/reassessed stages, accepted findings, and human corrections; mixed workflows also capture per-stage metrics with stage ID, pattern, wall time, calls, reuse, and failure class.
- Accepted finding count comes from actual accepted `FindingView` values, never a hard-coded one.
- Required probe failures fail comparison; unavailable optional providers are explicit deferrals, not passes.
- Direct, Sequential, Concurrent, Handoff, and Group Chat remain first-class.
- Strategic XLSX cases, resource soak, clean-wheel verification, and systematic contract/integration/stability probes are present.

**Required Skills:**
- `skill-backend-verification`
- `skill-performance-optimization`
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify `src/foresight_os/runtime/metrics.py` and related runtime receipt structures.
- Update `evaluation/run.py`, `evaluation/rubric.md`, `evaluation/README.md`, `evaluation/probes/`, and optimization receipt comparison code; preserve `evaluation/probes/optimization_measurement.py` as the shared baseline/release measurement owner.
- Add `evaluation/probes/run_strategic_exercise.py` as the named exercise-pack acceptance entry point and `evaluation/probes/run_clean_wheel_smoke.py` as the named clean-wheel acceptance entry point.
- Stage approved participant inputs into a disposable per-case root under `data/exercise/` with an immutable SHA-256 manifest; keep the existing `data/exercise/06_ForesightOS_Validator_Key.xlsx` outside that root and expose it only through `evaluation/reference/`/harness handles, never through participant document, filesystem, or tool scope.
- Enforce isolation in `evaluation/participant_scope.py:ParticipantScope` and `evaluation/run.py:run_candidate`: all participant paths resolve against the allowlisted case root, validator paths are denied before `local_toolbelt` receives them, and direct absolute-path access is denied.
- Extend `tests/test_tool_enabled_patterns.py`, `tests/test_anomaly_probe.py`, `tests/test_mcp_probe_contract.py`, and selective-reuse/performance coverage.
- Reconcile `src/foresight_os/artifacts/report.py`, `README.md`, `pyproject.toml`, package resources, schemas, and manifests without reopening completed Power BI PBIP/PBIR sources. Any Power BI implementation defect discovered after Task 0 is a stop-and-report condition requiring separate approval.

**Dependencies:**
- Tasks 1–5 complete.
- Approved exercise pack and validator isolation are staged before release measurements.

**Authority:**
- Preauthorized local actions: update metrics, evaluators, probes, fixtures, package metadata, documentation, tests, and declared local release checks while preserving untracked outputs; create the release-evidence checkpoint after final verification.
- Stop for: credentials or external writes, continuous monitoring infrastructure, deletion/cleanup of preserved outputs, generated-source edits outside canonical owners, or plan-status changes before final verification.

**Steps:**
- [x] Instrument required counters and resource snapshots across all five patterns and distinguish cache/reassessment outcomes at run, pattern, and stage levels.
- [x] Freeze quantitative thresholds before release measurement: critical probes 100% pass; missing required probe is release FAIL; p95 end-to-end regression ≤20% versus pinned baseline; peak RSS/allocation regression ≤15% unless justified; resource soak has no monotonic task/thread/process/handle growth; fully reusable stages make zero new model/tool calls; affected-input cases rerun only impact-directed descendants; denominator is actual accepted `FindingView` values.
- [x] Correct the optimization comparator so missing or failed required probes fail comparison and accepted findings use actual `FindingView` counts.
- [x] Route release measurement through `evaluation/probes/optimization_measurement.py` with the same receipt schema and workload contract used by Task 0; reject receipts missing accepted-finding, resource, per-stage, call, latency, cache, or reassessment observations.
- [x] Add contract, integration, stability, strategic XLSX, fresh-process reuse, fault-injection, and resource-soak probe layers; keep configured live-provider checks optional but truthful.
- [x] Add or stage the approved participant exercise pack under `data/exercise/` and record immutable SHA-256 hashes in a manifest; do not copy the validator key into the participant-visible set.
- [x] Implement `ParticipantScope`/`run_candidate` enforcement and add `tests/test_evaluation_scope.py`: an allowed workbook read succeeds, validator basename/path access fails, direct absolute-path access fails, and the evaluation harness can still read the validator out of band.
- [x] Run exercise workbooks as participant inputs while denying the validator/reference artifact to participant tools and filesystem scope; record workbook and case identity in receipts.
- [x] Route every artifact-producing command to `work/closure-release-20261013/...` or another new disposable root; never use default `work/toolbelt-probes`, `work/optimization-*`, or existing receipt paths.
- [x] Repair wheel smoke to use a genuinely clean environment, install only the newly built wheel, launch outside the repository tree, and assert the imported package path belongs to that environment.
- [x] Reconcile package resources, docs, schemas, and evaluation instructions; record unavailable external-boundary evidence explicitly.

**Verification:**
- [x] Run `python -m pytest -q tests/test_evaluation_scope.py tests/test_tool_enabled_patterns.py tests/test_anomaly_probe.py tests/test_mcp_probe_contract.py tests/test_selective_reuse.py` and then `python -m pytest -q`, with any generated reports routed to the disposable root.
- [x] Run `python evaluation/run.py --matrix contract --output-root work/closure-release-20261013/contract` and `python evaluation/run.py --matrix controller --write-report work/closure-release-20261013/controller.md`.
- [x] Run `python evaluation/probes/run_toolbelt_probe.py --output-root work/closure-release-20261013/toolbelt`, `python evaluation/probes/run_optimization_probe.py --mode release --fixture tests/fixtures/analyst_multisheet.xlsx --output work/closure-release-20261013/optimization/release.json`, and `python evaluation/probes/compare_optimization_receipts.py --baseline work/closure-final-20261013/optimization/receipt.json --release work/closure-release-20261013/optimization/release.json --output work/closure-release-20261013/optimization/comparison.json`.
- [x] Run `python evaluation/probes/run_strategic_exercise.py --exercise-root data/exercise --output-root work/closure-release-20261013/strategic`; require an exit code of `0`, a machine-readable report, immutable case/workbook hashes, and participant-scope assertions that validator path access is denied.
- [x] Run `python evaluation/probes/run_clean_wheel_smoke.py --output-root work/closure-release-20261013/wheel`; the probe creates its own disposable source copy, and requires an exit code of `0`, a wheel installed into a clean environment, and an imported package path outside the repository tree.
- Expected: required probes pass, missing required evidence fails comparison, all five patterns remain covered, resource measurements are non-placeholder, validator direct-path access fails, strategic fixtures are identified, and clean-wheel smoke imports from the disposable environment.

**Exit Criteria:**
- Release evidence can reject unhealthy execution, review, reuse, or packaging behavior; docs and package surfaces agree with source truth.

## Verification

Final verification is owned by `skill-verification-before-completion` after all task-local proof passes:

- `python -m pytest -q`
- Focused closure suites for workflow input preservation, Wayfinding, controller compilation, review records, invalidation, skills, all MAF patterns, and selective reuse
- `python evaluation/run.py --matrix contract`
- `python evaluation/run.py --matrix controller`
- `python evaluation/probes/run_selective_reuse_probe.py --output-root work/closure-final-20261013/selective-reuse/fresh-process`
- `python evaluation/probes/run_optimization_probe.py --mode baseline --fixture tests/fixtures/analyst_multisheet.xlsx --output work/closure-final-20261013/optimization/baseline.json`
- `python evaluation/probes/run_optimization_probe.py --mode release --fixture tests/fixtures/analyst_multisheet.xlsx --output work/closure-final-20261013/optimization/release.json`
- `python evaluation/probes/compare_optimization_receipts.py --baseline work/closure-final-20261013/optimization/baseline.json --release work/closure-final-20261013/optimization/release.json --output work/closure-final-20261013/optimization/comparison.json`
- `python evaluation/probes/run_strategic_exercise.py --exercise-root data/exercise --output-root work/closure-final-20261013/strategic`
- `python evaluation/probes/run_clean_wheel_smoke.py --output-root work/closure-final-20261013/wheel`
- Expected: each named probe exits `0`, receipts use the identical measurement schema, required evidence and threshold failures exit non-zero, strategic scope assertions pass, and clean-wheel imports resolve outside the repository tree.
- `git diff --check`
- `git status --short --branch`, confirming preserved untracked outputs remain untouched and only in-scope tracked changes are present

The final verifier must return `verified` before this plan status changes from `proposed` to `completed`.

## Completion Criteria

1. Task 0 establishes a green baseline at `9c4f47f` with the toolbelt probe covering `powerbi_project_read` and no Power BI implementation changes.
2. Increment A passes input preservation, generic Wayfinding, one-to-one `WorkStage -> RecipeStage` compilation, override semantics, specialist/topology, reviewer-capability, and all-pattern gates.
3. Increment B uses one typed `RelationIndex` with distinct material, impact, support, and counterevidence traversals while preserving direct evidence versus analytical support authority.
4. Review fingerprints include target material inputs, skill implementation identity, and policy identity without global unrelated revision invalidation.
5. `ReviewPolicyResolver` provides one deterministic acceptance answer and selected skills produce typed objections and durable `ReviewRecord` outcomes.
6. `FindingView` is pure derived state with complete support, counterevidence, rationale, assumptions, unknowns sourced from canonical uncertainty/issues/missing inputs, disconfirmation, implications, and explicit analytical monitoring metadata.
7. Increment C persists minimal sidecar committed `StageReceipt` records with output fingerprints and semantic authorization fingerprints; only canonicalized durable outputs are reusable.
8. Fresh-process reuse recomputes only affected descendants and leaves unrelated stages reusable; arbitrary conversational outputs are not reused.
9. Performance and stability evidence separates required work/resource dimensions, captures per-stage metrics for mixed workflows, covers all five MAF patterns, and meets frozen thresholds.
10. Strategic cases are staged with immutable hashes, the validator is inaccessible to participants, package checks and documentation reconcile with canonical ownership, and preserved workspace outputs remain untouched.
11. `skill-verification-before-completion` returns `verified`; only then may the lead controller change plan status to `completed` or perform separately authorized Git disposition.
