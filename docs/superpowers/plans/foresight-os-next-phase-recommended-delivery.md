---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: foresight-os-next-phase-recommended-delivery
targets:
- src/foresight_os/
- schemas/
- evaluation/
- tests/
- docs/intent/
- README.md
- pyproject.toml
related_features:
- analytical correctness
- canonical relationship state
- rebuildable knowledge view
- real Microsoft Agent Framework execution
- truthful workflow evaluation
- bounded Group Chat challenge recipe
related_stages:
- post-v0.1 correctness and capability expansion
---

# Foresight OS Next Phase: Recommended Delivery

## Goal

Deliver the next Foresight OS increment as five gated capabilities around one
canonical revisioned `AnalysisState`:

1. correctness convergence;
2. a typed, rebuildable relationship view;
3. real async MAF execution of analytical work;
4. truthful comparative evaluation;
5. one bounded Group Chat challenge recipe.

The system remains evidence-aware and human-controlled. Agents propose
structured changes; deterministic/domain validation checks them; one revisioned
writer commits accepted state; MAF owns runtime collaboration; NetworkX owns no
durable truth. Magentic orchestration, a graph database, a scheduler,
distributed locking, CRDTs, multi-writer graph state, and a second durable
state store remain out of scope.

## Decision Review

The supplied verdict is directionally approved. It correctly prioritizes
analytical correctness and measured evaluation before richer orchestration, and
its five-increment sequence is the right dependency order.

Required corrections incorporated into this plan:

- Existing `analysis.json` files and work directories need an explicit
  compatibility/migration test before relationship and revision changes are
  activated.
- Provider credentials must be selected by an explicit configured environment
  variable; scanning the first `API_KEY` or `TOKEN` assignment is not safe.
- Group Chat, Concurrent, and Handoff require executed comparative evidence and
  a declared quality/latency/cost threshold before production admission.
- Pydantic convergence, schema packaging, validator caching, and provider
  lifecycle reuse are included only where they reduce a current boundary risk;
  a wholesale domain rewrite is not admitted as a prerequisite.

## Implementation Outcomes

### Correct analytical state

Workbook-derived values and calculations are deterministic, analytical claims
retain source and calculation provenance, numerical and semantic review are
separate checks, and changed inputs cannot leave an accepted but numerically
false result current.

### One relationship authority

`AnalysisState.relationships` is the canonical dependency representation with a
controlled relation registry. Convenience evidence or dependency lists are
derived views, not independently editable state. Invalidation, graph
projection, provenance, counterevidence, and context retrieval consume the same
validated relationships.

### Real bounded execution

The async runtime executes actual analyst and reviewer work through MAF with
typed structured outputs, one provider/client lifecycle per Run where supported,
actual call/latency/failure metering, durable pending-review state, and
optimistic revision checks on the single analytical writer.

### Measured pattern selection

Evaluation runs the same cases and rubric through Single, Sequential,
Concurrent, and Handoff candidates where applicable. It defines the one
candidate Group Chat opportunity and its threshold but leaves implementation and
execution to Task 6. Metrics are measured from executions rather than
constants, and the Controller admits a pattern only when its quality
improvement exceeds the declared latency/cost or human-effort threshold.

### Bounded challenge workflow

If evaluation justifies it, `CHALLENGE_RECOMMENDATION` uses two participants,
deterministic speaker selection, `max_rounds = 4`, a deterministic termination
predicate, typed proposal output, domain validation, and a single state-writer
commit path.
Conversation history remains runtime context or telemetry, not analytical truth.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-executing-plans`, `skill-backend-verification`, `skill-code-standards`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`; use one explicitly authorized finishing action after fresh final verification
- Preauthorized local actions: edit declared repository files, create or migrate synthetic fixtures, run bounded local and environment-gated provider checks, install only declared dependencies after approval, and update plan evidence
- User-approval actions: provider authentication, external data access, push, merge, publication, destructive migration, discard, cleanup, and changes outside declared targets
- Parallel ownership: none; tasks share domain schemas, persistence, runtime, and evaluation contracts
- Sequential fallback: complete Tasks 1–2 before Task 3; complete Task 3 before Task 4; complete Task 4 before Task 5; activate Task 6 only after Task 5 identifies a justified Group Chat opportunity; complete Task 7 after the applicable Tasks 1–6 evidence exists

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `0d12be38d3d595cae346aae7e95cd6d230209f9d`
- Expected workspace: `implementation changes present; generated work/build artifacts removed`
- Next action: `commit and push the verified implementation from main`
- Blockers: `none; live 9router probe succeeded through the configured repository .env`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | mutation, calculation, validation, migration tests | `pytest tests/test_calculation_revision.py tests/test_analysis_schema.py tests/test_persistence.py` |
| Task 2 | `completed` | current | `codex` | Task 1 | typed relationship and invalidation tests | `pytest tests/test_analysis_schema.py tests/test_invalidation.py` |
| Task 3 | `completed` | current | `codex` | Task 2 | deterministic graph fixture and query tests | `pytest tests/test_graph.py` |
| Task 4 | `completed` | current | `codex` | Tasks 1–3 | async MAF boundary, failure, restart, and writer tests | `pytest tests/test_maf_fit.py tests/test_runtime_boundaries.py tests/test_recovery.py` + live 9router probe |
| Task 5 | `completed` | current | `codex` | Task 4 | measured evaluation report and admission gate | evaluation matrix cases 001–005 and `pytest tests/test_evaluation_contract.py tests/test_controller_selection.py` |
| Task 6 | `completed` | current | `codex` | Task 5 | Group Chat proposal, budget, validation, and non-admission tests | `pytest tests/test_group_chat.py` |
| Task 7 | `completed` | current | `codex` | Tasks 1–6 as applicable | packaging/configuration/targeted performance checks | wheel build/install, packaged schema test, full regression |

## Task Breakdown

### Task 1: Converge calculations, review, and durable pending state

**Purpose:**
- Replace hard-coded analytical conclusions with deterministic workbook
  calculations and explicit numerical provenance.
- Make review distinguish reference integrity, numerical correctness, and
  semantic reasoning.
- Make human approval apply to a specific pending revision rather than a
  caller-supplied boolean.

**Task Function:**
- Correctness-boundary and revision-state implementation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: highest correctness risk and direct ownership of the
  canonical domain contract.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independently challenge numerical mutation, contradiction,
  revision, and backward-compatibility evidence.

**Specification Coverage:**
- Verdict Increment 1: dynamic workbook calculations, numerical review,
  semantic review, pending analytical revisions, and human acceptance tied to a
  revision.
- Agents may propose values, but deterministic extraction/calculation and domain
  validation own numeric truth.
- Existing accepted state remains readable; migration must preserve IDs,
  revisions, evidence locators, and artifact lifecycle.
- Persist a `schema_version` with `analysis.json`; readers must migrate supported
  older versions in memory and write only the current version at an explicit
  persistence boundary.
- The migration contract is explicit: missing `schema_version` means legacy
  v0.1 and migrates to current version `1`; version `1` is a no-op; versions
  greater than `1` are rejected without rewriting the source file.
- Revision state is explicit and independent of assessment/lifecycle:
  `DRAFT → PENDING_REVIEW → ACCEPTED|REJECTED`, with accepted revisions able to
  become `SUPERSEDED` only through a newer accepted revision; stale writers may
  not advance or overwrite the state.

**Required Skills:**
- `skill-backend-verification`
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `src/foresight_os/analysis/workbook.py:WorkbookRow, read_workbook, extract_evidence`
- Inspect: `src/foresight_os/analysis/analyst.py:draft_analysis`
- Inspect: `src/foresight_os/analysis/reviewer.py:review_reasoning`
- Inspect: `src/foresight_os/persistence/analysis_store.py:AnalysisStore`
- Inspect: `src/foresight_os/vertical_slice.py:run_vertical_slice`
- Modify: `src/foresight_os/analysis/` calculation and review helpers; `src/foresight_os/domain/models.py`; `src/foresight_os/domain/validation.py`; `schemas/analysis.schema.json`; `src/foresight_os/persistence/analysis_store.py`; `src/foresight_os/vertical_slice.py`
- Add or modify tests: `tests/test_analysis_schema.py`,
  `tests/test_vertical_slice.py`, `tests/test_persistence.py`,
  `tests/test_invalidation.py`, and `tests/test_calculation_revision.py`
- Verify: `work/` migration fixtures and `evaluation/cases/case-001/`

**Dependencies:**
- Current v0.1 plan is complete at base commit `0d12be3`.
- The frozen workbook/reference case remains synthetic and unchanged until a
  deliberate evaluation rebaseline is recorded.

**Authority:**
- Preauthorized local actions: edit domain, analysis, persistence, schema, and test files named above; create synthetic mutation and legacy-state fixtures; run local checks.
- Stop for: changed decision semantics, destructive migration, customer data, or a requirement to preserve an incompatible public schema without an explicit migration decision.

**Steps:**
- [x] Step 1: Add deterministic lookup and calculation records for workbook
  values, including formula, inputs, output, units, and source locators; refactor
  `draft_analysis` to consume them instead of literal `140`/`115` conclusions.
- [x] Step 2: Add independent reference-integrity, numerical-correctness, and
  semantic-reasoning checks; reject or mark `UNCERTAIN` records whose values do
  not match current workbook evidence.
- [x] Step 3: Add explicit pending-review/accepted-revision state and a domain
  commit boundary that accepts a proposal only when `expected_revision` matches
  the current state; reject stale proposals without overwriting state.
- [x] Step 4: Add a compatible reader/migration path for existing v0.1
  `analysis.json` and `brief.md` fixtures; preserve historical revisions and
  mark newly affected outputs for reassessment rather than deleting history.
- [x] Step 5: Persist the current `schema_version`, define supported migration
  steps from v0.1, and reject unknown future versions without overwriting the
  source state.

**Verification:**
- [x] Mutate the workbook demand value from `140` to `999` and assert the
  derived evidence/calculation/claim changes; no stale accepted artifact remains
  current.
- [x] Submit a proposal against revision `n` after state is at `n+1` and assert
  rejection with unchanged durable state.
- [x] Load a representative v0.1 state and assert IDs, revision history, and
  locators survive migration.
- [x] Assert a migrated state exposes the current `schema_version`, unknown
  future versions fail safely, and migration is not written until explicitly
  saved.
- [x] `python -m pytest tests/test_analysis_schema.py tests/test_vertical_slice.py tests/test_persistence.py tests/test_invalidation.py tests/test_calculation_revision.py`
- Expected: numerical mutations are reflected, invalid reasoning is rejected or
  marked uncertain, stale writes fail safely, and legacy state remains readable.

**Exit Criteria:**
- Input mutations produce corresponding analytical changes; numeric claims are
  source/calculation-backed; approval targets a concrete revision; no affected
  artifact is falsely current; legacy state has a tested migration path.

### Task 2: Make relationships canonical and typed

**Purpose:**
- Establish one authoritative dependency model for invalidation, provenance,
  graph projection, and bounded context.

**Task Function:**
- Domain relationship registry and single-writer dependency implementation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared schema and persistence semantics require one owner.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: verify direction, source/target legality, propagation, and
  compatibility with existing state.

**Specification Coverage:**
- Verdict Increment 1 and 2: `Relationship[]` is the only editable dependency
  authority; convenience `evidence_ids` and `relationship_ids` are either
  derived projections or removed from persisted state.
- Initial relation registry: `SUPPORTS`, `CONTRADICTS`, `DERIVED_FROM`,
  `DEPENDS_ON`, `INFORMS`, `PRODUCES`, `SUPERSEDES`.
- Every relation declares valid source/target kinds, semantic direction, and
  whether invalidation propagates in a separately named impact direction.
- The initial endpoint/impact matrix is fixed before implementation: `SUPPORTS`
  is evidence/analytical-record → analytical-record and impacts forward;
  `CONTRADICTS` is evidence/analytical-record → analytical-record and impacts
  forward; `DERIVED_FROM` is analytical-record → evidence/analytical-record and
  impacts reverse; `DEPENDS_ON` is claim/implication/recommendation/artifact →
  evidence/claim/implication/recommendation and impacts reverse;
  `INFORMS` is evidence/claim/implication → implication/recommendation and
  impacts forward; `PRODUCES` is claim/implication/recommendation → artifact
  and impacts forward; `SUPERSEDES` is same-kind record/artifact → prior
  record/artifact and does not propagate reassessment.

**Required Skills:**
- `skill-backend-verification`
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `src/foresight_os/domain/models.py:Relationship, AnalysisState`
- Inspect: `src/foresight_os/domain/validation.py:validate_analysis`
- Inspect: `src/foresight_os/persistence/invalidation.py:invalidate_dependencies`
- Modify: `src/foresight_os/domain/models.py`, `src/foresight_os/domain/validation.py`, `schemas/analysis.schema.json`, `src/foresight_os/persistence/invalidation.py`, `src/foresight_os/persistence/analysis_store.py`
- Add or modify tests: `tests/test_analysis_schema.py`, `tests/test_invalidation.py`, `tests/test_persistence.py`

**Dependencies:**
- Task 1 defines pending/accepted revision behavior and calculation-backed
  records.

**Authority:**
- Preauthorized local actions: edit relationship models, registry, validators, invalidation, migration, and focused tests; run local checks.
- Stop for: a requirement for independently editable duplicate dependency fields, multi-writer persistence, or a graph database.

**Steps:**
- [x] Step 1: Introduce a controlled relation type and registry with allowed
  source/target record kinds, semantic direction, and impact propagation
  direction/policy.
- [x] Step 2: Make writers construct and validate relationships first; remove
  editable `evidence_ids` and `relationship_ids`, or derive both only at load
  or serialization boundaries from `Relationship[]`.
- [x] Step 3: Update invalidation to traverse only relation types whose registry
  policy propagates reassessment; preserve `SUPERSEDES` semantics and idempotent
  revision history.
- [x] Step 4: Add relationship migration checks for existing lowercase relation
  values and reject unknown or directionally invalid relationships.

**Verification:**
- [x] Assert each initial relation type accepts only its declared source/target
  kinds and direction.
- [x] Assert an evidence change reaches claims, implications, recommendations,
  and produced artifacts through canonical relationships, without traversing a
  non-propagating `SUPERSEDES` edge.
- [x] Assert semantic relationship direction is preserved independently from
  impact traversal direction, and that any convenience lists equal the
  relationship-derived view and cannot introduce an unrepresented dependency.
- [x] Assert reverse-impact `DEPENDS_ON` and `DERIVED_FROM` fixtures reach every
  expected dependent while non-propagating `SUPERSEDES` does not.
- [x] `python -m pytest tests/test_analysis_schema.py tests/test_invalidation.py tests/test_persistence.py`

**Exit Criteria:**
- Relationship validation, invalidation, migration, graph inputs, and context
  inputs all consume one canonical relationship representation.

### Task 3: Add a deterministic NetworkX knowledge view

**Purpose:**
- Provide provenance, counterevidence, impact, and bounded-context queries
  without creating a second durable store.

**Task Function:**
- Rebuildable graph projection and query surface.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded deterministic adapter with no autonomous policy.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: compare exact fixture ancestors, dependents, and context to
  canonical relationships.

**Specification Coverage:**
- Verdict Increment 2: `AnalysisState → validated relationships →
  NetworkX.MultiDiGraph`.
- NetworkX owns no persistence and is rebuilt from the selected analytical
  revision.
- NetworkX is an optional derived optimization; runtime correctness and
  recovery must not depend on its installation or internal ordering.
- Initial query surface: `trace_provenance`, `get_impacted_records`,
  `get_evidence`, `get_counterevidence`, `get_context`; assumptions and
  dependents are deferred until those record kinds exist.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Modify: `pyproject.toml`; add `src/foresight_os/graph/projection.py` and
  `src/foresight_os/graph/queries.py`; update `src/foresight_os/domain/__init__.py`
  only if exports are required.
- Add tests: `tests/test_graph.py` with a small canonical fixture and exact
  expected paths/neighborhoods.
- Verify: `docs/intent/` decision record or README architecture note if the
  derived-view contract changes.

**Dependencies:**
- Task 2 canonical typed relationships.

**Authority:**
- Preauthorized local actions: add the minimal NetworkX dependency and derived projection/query modules plus deterministic fixtures and tests.
- Stop for: graph persistence, a graph synchronization service, unbounded traversal, or a query API without a bounded result/context limit.

**Steps:**
- [x] Step 1: Pin the smallest supported NetworkX dependency and build a graph
  only from validated current `AnalysisState` relationships.
- [x] Step 2: Implement deterministic node/edge ordering and bounded traversal
  limits; sort every public query result by explicit stable keys rather than
  relying on NetworkX insertion or iteration order, and include relation type
  and provenance metadata in query results.
- [x] Step 3: Implement the initial five query functions and a bounded context
  packet suitable for a reviewer without serializing the full analysis state.

**Verification:**
- [x] Rebuild the graph twice from the same state and assert identical nodes,
  edges, ordering, and query results.
- [x] Assert known fixture provenance, counterevidence, impact, and context
  results exactly; assert traversal bounds are enforced.
- [x] `python -m pytest tests/test_graph.py tests/test_analysis_schema.py`

**Exit Criteria:**
- Known graph fixtures return exact expected ancestors, dependents, and context;
  rebuilding is deterministic; no graph-only state is required to recover an
  investigation.

### Task 4: Replace stage markers with real async MAF execution

**Purpose:**
- Make MAF execute analyst/reviewer work while deterministic extraction,
  calculations, validation, graph queries, and persistence remain domain-owned.

**Task Function:**
- Async runtime boundary, typed MAF executors, and provider lifecycle.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: material backend behavior, provider boundaries, and restart
  semantics require direct integration control.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: independently inspect success, provider failure, timeout,
  interruption/restart, and stale-writer behavior.

**Specification Coverage:**
- Verdict Increment 3: async-first runtime, actual Analyst and Reviewer
  executors, typed structured outputs, metering, durable HITL pause, and one
  provider/client lifecycle per Run where MAF permits.
- Runtime metering is exposed through a typed `RunMetrics` contract containing
  `run_id`, `recipe`, `pattern`, `model_calls`, `retries`, `correction_rounds`,
  `wall_time_ms`, `provider_failures`, and optional reliable token counts.
- Canonical API is `async def run_recipe(...)`; synchronous CLI adapters call it
  only at the outer boundary.
- Provider configuration uses explicit `credential_env` and the configured
  custom provider/base URL; never scan the first key/token assignment.

**Required Skills:**
- `skill-backend-verification`
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/workflow.py:run_sequential_steps`,
  `src/foresight_os/runtime/maf_probe.py`, `src/foresight_os/vertical_slice.py:run_vertical_slice`
- Modify: `src/foresight_os/runtime/workflow.py`, `src/foresight_os/runtime/maf_probe.py`, `src/foresight_os/vertical_slice.py`, `src/foresight_os/controller/recipes.py`, `src/foresight_os/controller/budgets.py`, `src/foresight_os/persistence/recovery.py`
- Add: `src/foresight_os/runtime/executors.py:AnalystExecutor,ReviewerExecutor`,
  `src/foresight_os/runtime/metrics.py:RunMetrics`,
  `src/foresight_os/runtime/provider_config.py:load_provider_settings`, and
  `src/foresight_os/domain/proposals.py` for typed proposal/review contracts.
- Add or modify tests: `tests/test_maf_fit.py`, `tests/test_vertical_slice.py`,
  `tests/test_recovery.py`, `tests/test_runtime_boundaries.py`, and
  `tests/test_provider_config.py`.

**Dependencies:**
- Tasks 1–2 define typed proposals, revision commit rules, and relationship
  validation.
- Task 3 provides bounded context packets for review; the runtime must still
  operate without graph state when a query is not needed.

**Authority:**
- Preauthorized local actions: edit runtime/controller/persistence files named above; run bounded local MAF checks and explicitly configured provider probes; record sanitized evidence.
- Stop for: unbounded model loops, provider authentication changes, external data transmission not covered by the configured endpoint, custom scheduler/orchestration infrastructure, or a workflow that bypasses the single writer.

**Steps:**
- [x] Step 1: Introduce async recipe execution and retain a thin synchronous
  adapter for existing CLI/tests; remove stage-marker-only success as proof of
  analytical execution.
- [x] Step 2: Implement AnalystExecutor and ReviewerExecutor around deterministic
  domain services and typed structured outputs; keep calculations and persistence
  outside the model call.
- [x] Step 3: Add actual metering at model-call, retry, correction, branch, and
  provider-failure boundaries; emit the typed `RunMetrics` object; enforce
  budgets before work rather than trusting caller-supplied counters.
- [x] Step 4: Persist `PENDING_REVIEW` before human acceptance, resume from a
  compatible checkpoint or start a new Run from durable Analysis State, and
  reject stale proposals through the single writer.
- [x] Step 5: Implement `load_provider_settings` with explicit
  `credential_env`, custom provider/base URL, and missing/ambiguous-credential
  rejection; reuse the provider/client for the Run where supported and add an
  environment-gated live probe. Keep this Run-lifecycle and credential
  ownership here so later packaging work only verifies the contract.

**Verification:**
- [x] Direct boundary test proves analyst → reviewer → domain validation →
  pending revision → human acceptance → artifact.
- [x] Failure tests cover provider failure, timeout, correction-budget
  exhaustion, incompatible checkpoint topology, and stale expected revision;
  durable state remains valid and no false-current artifact is produced.
- [x] With configured credentials, run one bounded provider probe and record
  provider/model/endpoint/package/status/latency only; do not log secrets,
  prompts, responses, headers, or bodies.
- [x] `python -m pytest tests/test_maf_fit.py tests/test_vertical_slice.py tests/test_recovery.py tests/test_runtime_boundaries.py tests/test_provider_config.py`

**Exit Criteria:**
- Sequential execution performs real analytical work through MAF, survives
  controlled interruption/restart, meters actual work, and commits only through
  the validated revision writer.

### Task 5: Replace fixture metrics with truthful comparative evaluation

**Purpose:**
- Measure pattern value from executed behavior and make Controller admission
  evidence-based.

**Task Function:**
- Comparative evaluation runner, cases, rubric, and admission gate.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: evaluation owns the production-admission evidence and must
  remain independent from pattern implementation.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: check equal inputs, reproducible scoring, and absence of
  constant or post-hoc metrics.

**Specification Coverage:**
- Verdict Increment 4: execute Single, Sequential, Concurrent, and Handoff
  candidates only where the task shape warrants them through an evaluation-only
  candidate harness; include graph traversal measures and preserve the A/B/C
  semantic-versus-coordination comparison.
- Add cases A–E: simple workbook, independent scanning, specialist ambiguity,
  conflicting interpretation, and dependency change.
- Metrics include accepted-claim precision, finding coverage, contradiction
  handling, traceability, model calls, retries, wall time, provider failures,
  human correction effort, and invalidation precision/recall where applicable;
  runtime measurements consume the typed `RunMetrics` contract from Task 4.
- This task defines the single Group Chat opportunity, baseline, scoring rubric,
  and admission threshold only. It does not implement or execute Group Chat;
  Task 6 owns that candidate.

**Required Skills:**
- `skill-test-driven-development`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `evaluation/run.py`, `evaluation/rubric.md`,
  `evaluation/cases/case-001/`, `tests/test_evaluation_contract.py`
- Modify: `evaluation/run.py`, `evaluation/rubric.md`, `evaluation/README.md`,
  `evaluation/baseline/README.md`, `src/foresight_os/controller/policy.py`,
  `tests/test_evaluation_contract.py`, `tests/test_controller_selection.py`
- Add: `evaluation/cases/case-002/` through `case-005/` and measured result
  artifacts with execution metadata; add
  `evaluation/candidate_harness.py:run_candidate` as the evaluation-only
  candidate harness for Single, Sequential, Concurrent, and Handoff without
  changing production recipe selection.
- Verify: `src/foresight_os/controller/policy.py` and recipe tests only after
  measured reports exist.

**Dependencies:**
- Task 4 must expose actual execution metrics and stable recipe boundaries.
- Tasks 1–3 must provide calculation-backed state and graph query metrics.

**Authority:**
- Preauthorized local actions: create synthetic evaluation cases, run bounded experiments, update rubrics/reports/tests, and revise Controller admission logic from recorded results.
- Stop for: changing the rubric after seeing results, unequal inputs, hidden provider calls, customer data, or admitting a pattern without a declared threshold and reproducible report.

**Steps:**
- [x] Step 1: Define the metrics, equal-input case contracts, reference answers,
  adjudication rubric, and expected result sets before any candidate execution.
- [x] Step 2: Author cases A–E with expected opportunity, reference findings,
  contradiction/dependency traps, common scoring/adjudication, and dependency
  fixtures carrying `changed_ids`, `expected_reassessment`, and
  `expected_stale_artifacts`.
- [x] Step 3: Freeze explicit admission thresholds for quality gain versus
  latency, calls, cost, and human effort, including the Group Chat opportunity
  threshold; record the frozen contract before collecting candidate results.
- [x] Step 4: Implement the evaluation-only candidate harness for
  Single/Sequential and the warranted Concurrent/Handoff cases, collecting
  actual `RunMetrics` and keeping production selection unchanged.
- [x] Step 5: Execute equivalent-input comparisons, then measure quality,
  graph impact precision/recall, latency, calls, cost, failures, and human
  effort; keep unsupported patterns deferred when evidence is insufficient.
- [x] Step 6: Update `select_recipe` only from the recorded admission results
  and small task-shape signals, not a giant rules engine or framework
  availability; leave Group Chat implementation to Task 6.

**Verification:**
- [x] Two runs with identical inputs produce reproducible reference/scoring
  metadata while live-run metrics may vary within a documented tolerance.
- [x] Reports contain actual calls, latency, failures, quality, and human-effort
  measurements; no result is a hard-coded constant.
- [x] Candidate runs execute through the evaluation-only harness, and the
  report proves thresholds were frozen before candidate results were observed.
- [x] Dependency-change reports compare exact expected impact sets from each
  fixture and record false positives, false negatives, and stale artifacts.
- [x] `python -m pytest tests/test_evaluation_contract.py tests/test_controller_selection.py`
- [x] `python evaluation/run.py --case evaluation/cases/case-001 --compare ordinary,semantic,sequential,controller --write-report evaluation/results/case-001.md`

**Exit Criteria:**
- Controller pattern admission is based on executed metrics; no richer pattern
  is admitted merely because MAF exposes it.

### Task 6: Add one bounded Group Chat challenge recipe

**Purpose:**
- Test Group Chat only where independent challenge can improve a recommendation
  enough to justify additional latency/cost/human review complexity.

**Task Function:**
- Bounded MAF collaboration recipe and proposal validation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: recipe is admitted only after Task 5 demonstrates a case where
  deliberation has measurable value.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: verify deterministic termination, unsupported-consensus
  rejection, and single-writer persistence.

**Specification Coverage:**
- Verdict Increment 5: `CHALLENGE_RECOMMENDATION` with Analyst and Skeptic,
  deterministic speaker selection, `max_rounds = 4`, a deterministic
  termination predicate, hard turn budget, structured proposal output, domain
  validation, and one state writer.
- Group Chat history is runtime context/telemetry only. Persist only accepted
  evidence relationships, objections, changed assessments, or unresolved
  dependencies.
- Consensus is not evidence; a proposal cannot become `SUPPORTED` without
  evidence and domain validation.

**Required Skills:**
- `skill-backend-verification`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `src/foresight_os/controller/recipes.py`, `src/foresight_os/controller/policy.py`,
  `src/foresight_os/runtime/workflow.py`, `src/foresight_os/domain/validation.py`
- Modify: `src/foresight_os/controller/recipes.py`, `src/foresight_os/controller/policy.py`,
  `src/foresight_os/runtime/workflow.py`, `src/foresight_os/persistence/analysis_store.py`
- Add: `src/foresight_os/domain/challenge.py:ChallengeProposal`,
  `src/foresight_os/runtime/group_chat.py:run_challenge_recommendation`, and
  `tests/test_group_chat.py`.
- Verify: `evaluation/cases/case-004/` conflicting-interpretation case and the
  runtime telemetry boundary in `tests/test_group_chat.py`.

**Dependencies:**
- Task 5 must show a justified Group Chat opportunity and define the threshold;
  Task 6 supplies the execution evidence needed for final admission.
- Tasks 1–4 provide typed state, domain validation, bounded context, runtime
  budgets, and single-writer commits.

**Authority:**
- Preauthorized local actions: add the single named recipe, bounded participant/turn logic, proposal validation, telemetry handling, and focused tests.
- Stop for: global Group Chat mode, unbounded turns, transcript persistence as domain state, unsupported consensus, or a result below the Task 5 admission threshold.

**Steps:**
- [x] Step 1: Define the typed proposal with agreements, disagreements,
  counterevidence, unsupported assumptions, proposed changes, and unresolved
  questions.
- [x] Step 2: Build the two-participant bounded recipe with deterministic turn
  selection, `max_rounds = 4`, and a deterministic termination predicate that
  can stop after a useful shorter exchange.
- [x] Step 3: Feed each participant a bounded graph/evidence context packet;
  never rebroadcast the entire investigation by default.
- [x] Step 4: Validate proposals through the domain boundary and route accepted
  changes through the expected-revision single writer; keep transcript data out
  of `analysis.json`.
- [x] Step 5: Execute the frozen Task 5 Group Chat case against its declared
  baseline and threshold, collect `RunMetrics`, and admit the recipe only when
  the threshold is met; otherwise record explicit deferral evidence.

**Verification:**
- [x] Assert turn count, speaker order, timeout, and budget termination.
- [x] Assert unsupported consensus and missing/counterfeit evidence are rejected
  without changing durable state.
- [x] Assert accepted changes create a revision and preserve human authority.
- [x] Compare contradiction resolution, unsupported consensus, human correction
  effort, latency, and calls against Sequential.
- [x] `python -m pytest tests/test_group_chat.py tests/test_controller_selection.py`
- [x] `python evaluation/run.py --case evaluation/cases/case-004 --compare sequential,group_chat --write-report evaluation/results/case-004.md`

**Exit Criteria:**
- Group Chat is either admitted with measured benefit and bounded behavior or
  remains explicitly deferred with the failed/insufficient evidence recorded.

### Task 7: Package and harden the supported boundary

**Purpose:**
- Make the validated runtime distributable and apply only final low-risk
  optimizations after the admission evidence exists.

**Task Function:**
- Release-boundary and measured-overhead hardening.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: small cross-cutting changes with direct packaging and
  verification ownership.

**Validator Profile:**
- Controller-selected: `review-1`
- Selection basis: verify package-installed behavior and that optimization does
  not change analytical results.

**Specification Coverage:**
- Verdict Sections 16–18: cached schema validators, dependency-safe bounded
  concurrency, dependency-valid artifact reuse, package schemas as resources,
  and verification of explicit credential resolution. Task 4 owns provider
  configuration, client lifecycle, and metering required for realistic
  execution; Task 7 must not redefine them.

**Required Skills:**
- `skill-code-standards`
- `skill-verification-before-completion`

**Files And Symbols:**
- Modify: `pyproject.toml`, `src/foresight_os/domain/validation.py`,
  `src/foresight_os/persistence/analysis_store.py`, package layout under
  `src/foresight_os/schemas/`, and relevant documentation; verify rather than
  reimplement `src/foresight_os/runtime/provider_config.py` and
  `src/foresight_os/runtime/maf_probe.py`.
- Add or modify tests: `tests/test_package_resources.py` for installation and
  `tests/test_provider_config.py` remains owned by Task 4 for credential
  selection with multiple env assignments.
- Verify: built wheel in a clean temporary environment and the existing report,
  invalidation, recovery, and live-probe contracts.

**Dependencies:**
- Tasks 1–6 identify the supported schemas, provider settings, and actual
  workload. Task 4's no-regret lifecycle changes occur before Task 5
  benchmarking; Task 7 performs only final packaging/hardening and reruns the
  admission benchmark after any optimization that could affect its result.

**Authority:**
- Preauthorized local actions: move/copy canonical schemas into package resources, update packaging metadata, cache safe immutable validators, and run local build/install checks against the Task 4 configuration contract.
- Stop for: secret material in package or logs, unmeasured performance claims, a second durable state store, or a change that alters analytical results.

**Steps:**
- [x] Step 1: Verify the Task 4 provider credential contract from the installed
  package; do not add a second configuration path or credential-selection rule.
- [x] Step 2: Package schemas as `foresight_os` resources and validate from a
  built wheel installed into a clean temporary environment.
- [x] Step 3: Cache immutable schema validators, preserve dependency-safe
  artifact reuse, and keep bounded concurrency under the runtime budget without
  changing the Task 4 provider lifecycle contract.
- [x] Step 4: Re-run representative workload measurements and, when a change
  can affect admission, rerun the frozen Task 5/Task 6 benchmark before
  confirming outputs, invalidation, and recovery remain unchanged.

**Verification:**
- [x] `python -m pytest tests/test_package_resources.py tests/test_provider_config.py`
- [x] `python -m compileall src tests`
- [x] `python -m build --wheel --outdir dist`
- [x] `$wheel = (Get-ChildItem dist/*.whl | Select-Object -First 1).FullName; python -m pip install --target .tmp/package-install $wheel`
- [x] `tests/test_package_resources.py` installs the wheel outside the checkout
  and validates a `brief.md` and `analysis.json` fixture through packaged
  resources; no source-tree fallback is allowed.
- [x] Run the configured live probe with sanitized metadata only.
- [x] Compare before/after workload outputs and confirm no false-current artifact
  or credential leakage.

**Exit Criteria:**
- Foresight OS installs and validates outside the repository layout, resolves
  exactly the configured provider credential, and shows no correctness
  regression from the measured low-cost optimizations.

## Verification

Use this section for final artifact-level verification only.

- `python -m pytest`
- `python -m compileall src tests`
- `python evaluation/run.py --case evaluation/cases/case-001 --compare ordinary,semantic,sequential,controller --write-report evaluation/results/case-001.md`
- `python evaluation/run.py --case evaluation/cases/case-001 --compare ordinary,semantic,sequential,controller,concurrent,handoff --write-report evaluation/results/case-001-expanded.md`
- `python evaluation/run.py --case evaluation/cases/case-002 --compare ordinary,semantic,sequential,controller,concurrent,handoff --write-report evaluation/results/case-002.md`
- `python evaluation/run.py --case evaluation/cases/case-003 --compare ordinary,semantic,sequential,controller,concurrent,handoff --write-report evaluation/results/case-003.md`
- `python evaluation/run.py --case evaluation/cases/case-004 --compare ordinary,semantic,sequential,controller,concurrent,handoff,group_chat --write-report evaluation/results/case-004.md`
- `python evaluation/run.py --case evaluation/cases/case-005 --compare ordinary,semantic,sequential,controller,concurrent,handoff --write-report evaluation/results/case-005.md`
- Expected: every report uses equal inputs and frozen rubric/threshold metadata;
  each admitted pattern has measured quality, latency, calls, failures, and
  human-effort evidence, while unsupported patterns remain deferred.
- Run a fresh-process scenario: load a legacy v0.1 state, mutate workbook
  evidence, produce a pending revision, reject a stale proposal, resume from a
  compatible checkpoint, accept the current revision, and render an artifact.
- Rebuild the NetworkX view twice and compare exact serialized query results.
- Run the environment-gated provider probe with explicit credential selection;
  record only provider/model/endpoint/package/status/latency.
- `python -m build --wheel --outdir dist`
- `$wheel = (Get-ChildItem dist/*.whl | Select-Object -First 1).FullName; python -m pip install --target .tmp/final-package-install $wheel`
- `python -m pytest tests/test_package_resources.py tests/test_provider_config.py`
- Inspect final `analysis.json`, pending/accepted revision state, relationships,
  invalidation metadata, graph query results, evaluation report, and generated
  artifact for evidence traceability and stale-output protection.

## Completion Criteria

The plan is ready for completion verification when:

1. dynamic workbook calculations, numerical validation, semantic review,
   canonical relationships, typed propagation, pending revisions, stale-writer
   rejection, and artifact invalidation are proven;
2. legacy v0.1 state remains readable through a tested migration path;
3. NetworkX is a deterministic rebuildable view with exact bounded query tests
   and no durable graph-only truth;
4. the async MAF runtime executes real analyst/reviewer work with typed outputs,
   bounded metering, provider lifecycle reuse, and controlled restart/HITL
   behavior;
5. provider credentials are explicitly configured and no secret appears in
   tracked files, logs, telemetry, or reports;
6. evaluation metrics are measured from executions rather than constants, use
   equal-input comparisons, and record quality, cost/latency, failures, and
   human effort;
7. Controller admission follows declared thresholds and keeps unsupported
   patterns deferred;
8. Group Chat is either admitted as the single bounded challenge recipe with
   measured value or remains explicitly deferred;
9. schemas validate from a built package outside the repository layout;
10. all required task-local checks and final verification commands pass, with
    deviations, blockers, and deferrals recorded;
11. `skill-verification-before-completion` returns `verified` before the plan
    status changes from `proposed` to `completed`.
