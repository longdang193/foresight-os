---
layer: change
artifact_type: plan
contract_version: "1"
status: active
template_id: implementation-plan
name: foresight-os-recommended-next-delivery
targets:
  - src/foresight_os/analysis/
  - src/foresight_os/artifacts/
  - src/foresight_os/controller/
  - src/foresight_os/domain/
  - src/foresight_os/graph/
  - src/foresight_os/persistence/
  - src/foresight_os/runtime/
  - src/foresight_os/schemas/
  - evaluation/
  - tests/
  - docs/intent/
  - README.md
  - pyproject.toml
---

# Foresight OS Recommended Next Delivery

## Goal

Converge the current v0.1 prototype into a trustworthy pattern-capable runtime
without creating a second orchestration engine. The delivery makes analytical
correctness and durable revision integrity prerequisites, routes every declared
execution pattern through one native Microsoft Agent Framework entry point,
lets the Controller select and compose patterns from task shape, keeps
NetworkX as a rebuildable view, and evaluates behavior without using benchmark
results to decide whether a supported capability is allowed to exist.

The durable runtime vocabulary remains:

```text
Investigation → Work Brief → Execution Recipe → Run → Analysis State → Artifact
```

The implementation must preserve these ownership boundaries:

- Work Brief owns the definition of the work.
- Foresight Controller owns purpose, pattern, roles, limits, and selection rationale.
- Microsoft Agent Framework owns agent/workflow orchestration mechanics.
- Domain code owns deterministic calculations, evidence validity, and proposal validation.
- One persistence writer owns durable revision commits.
- NetworkX owns only a derived traversal/context view.
- Clients and generated artifacts never become analytical sources of truth.

## Implementation Outcomes

### Trustworthy analytical state

Workbook calculations, evidence, revisions, review transitions, invalidation,
and report rendering preserve identity and acceptance state across migration,
restart, and concurrent writers. Verification includes deterministic domain
tests, save/load round trips, race tests, and fresh-process recovery.

### Native pattern-capable runtime

One bounded `run_recipe_async()` entry point executes native MAF Direct,
Sequential, Concurrent, Handoff, Group Chat, and validated compositions while
preserving typed stage contracts, provider boundaries, settled metrics, and
checkpoint restart behavior. Verification includes native builder tests and
sanitized `9router` live probes.

### Converged Controller, evaluation, and documentation

Controller selection, evaluation records, relationship/query behavior, schema
ownership, tests, and current documentation describe one supported-pattern
contract without treating benchmark measurements as capability admission.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-executing-plans`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit tracked source, tests, schemas, documentation, and plan-local verification outputs within the repository; run declared deterministic checks and configured live probes without recording secrets or model content
- User-approval actions: push, merge, publication, destructive recovery, discard, and unrelated cleanup
- Parallel ownership: none
- Sequential fallback: execute tasks 1 through 7 in dependency order

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `5bf8031c9941f3cbdce2bbd7887eb59620a6259a`
- Expected workspace: `clean except this proposed untracked plan`
- Next action: `finish remaining Task 3 native-builder execution and then reconcile Tasks 4–7`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
|---|---|---|---|---|---|---|
| Task 1 | `completed` | current | `codex` | none | persistence, migration, and calculation tests | `40 passed`; live probe pending final reconciliation |
| Task 2 | `completed` | current | `codex` | Task 1 | vocabulary and capability contract tests | `tests/test_controller_selection.py tests/test_analysis_schema.py` passed |
| Task 3 | `active` | current | `codex` | Tasks 1–2 | native builder and runtime-boundary tests | runtime boundary tests pass; native builder execution still open |
| Task 4 | `pending` | current | `codex` | Tasks 2–3 | controller selection and composition tests | pending |
| Task 5 | `pending` | current | `codex` | Tasks 1–3 | relationship, invalidation, and graph tests | pending |
| Task 6 | `pending` | current | `codex` | Tasks 3–5 | contract, controller, quality, and live-probe matrices | pending |
| Task 7 | `pending` | current | `codex` | Tasks 1–6 | source-truth and documentation consistency checks | pending |

## Decision Review

The supplied verdict is accepted with these justified refinements:

1. **Capability, selection, and measurement are separate scoped records.**
   `PatternCapability` owns static support/availability, `PatternSelection`
   owns one Controller decision, and `PatternMeasurement` owns one run's
   provider/case/revision metrics. A performance result can tune Controller
   defaults or explain a selection; it must not turn an implemented pattern
   into an unsupported one.
2. **Native MAF is the only orchestration path.** The existing callable-based
   Group Chat loop may remain as a domain proposal test double, but runtime
   execution must dispatch to native MAF builders and participants.
3. **No generic `AGENTIC` engine is added.** Composition is represented by
   bounded recipe stages whose transitions are explicit; no scheduler, message
   bus, generic DAG runtime, or pattern-specific role classes are introduced.
4. **Correctness precedes richer orchestration.** Workbook identity, report
   acceptance, pending revisions, and the single-writer boundary are fixed
   before native Concurrent, Handoff, or Group Chat execution is enabled.
5. **NetworkX remains derived and lightweight.** Query-specific adjacency
   indexes are allowed; graph persistence, graph synchronization, and a second
   graph truth model are not.
6. **Historical documents are not rewritten to erase prior decisions.** The
   v0.1 plan and its evidence remain historical; current README, capability
   records, tests, and evaluation terminology are reconciled after behavior
   changes land.
7. **The current file-backed writer is cross-process safe without becoming a
   distributed lock service.** A filesystem lock, expected revision, and atomic
   replacement protect the commit boundary; SQLite remains a later storage
   decision, not part of this delivery.
8. **Replanning occurs only at macro-stage boundaries.** A running MAF
   workflow is finished or stopped before a new recipe is produced; its active
   topology is never mutated in place.

## Current Gaps To Close

The committed implementation has these bounded gaps:

- `RecipeName` mixes work purpose with execution pattern.
- `run_recipe_async()` runs Analyst then Reviewer for every multi-role recipe,
  even when the recipe declares Concurrent, Handoff, or Group Chat.
- Workbook calculations and `draft_analysis()` still rely on partial identity
  matching and case-specific record lookup.
- `render_report()` blocks stale artifacts but does not require an accepted
  revision or explicitly label provisional output.
- `AnalysisStore.commit_revision()` checks an expected revision but does not
  allocate the next revision under a cross-process commit boundary.
- Relationship rules primarily describe endpoint validity and invalidation;
  provenance, evidence meaning, and query direction are not first-class.
- Graph context and correctness-critical invalidation do not yet expose
  separate complete-versus-bounded query contracts.
- Capability and evaluation records still use `production_admitted` and
  `DEFERRED` as if measurement determined support.
- The evaluation harness mostly exercises deterministic domain behavior rather
  than proving each native MAF pattern's execution semantics.

## Invariants

- Agents return validated proposals or typed runtime results; arbitrary model
  prose never enters `analysis.json` directly.
- Agents and participants do not write `analysis.json`; only the commit owner
  may do so.
- Every accepted artifact identifies the revision and inputs it represents.
- Invalidation computes the complete affected set or fails explicitly; bounded
  truncation is permitted only for AI context retrieval and must be reported.
- Provider credentials are selected from the explicitly configured environment
  variable in Codex `config.toml`; no key scanning or credential logging is
  permitted.
- Every pattern has a bounded contract, a common `RunMetrics` surface, and
  explicit success, failure, timeout, and cancellation cleanup behavior.
- Existing v0.1 state remains readable through migration tests.

## Task Breakdown

The tasks are intentionally sequential because they share domain schemas,
persistence, runtime, and evaluation contracts.

| Task | Scope | Depends on | Owner | State |
|---|---|---|---|---|
| 1 | Correctness and revision integrity | none | `codex` | `proposed` |
| 2 | Runtime contract and capability vocabulary | 1 | `codex` | `proposed` |
| 3 | Native MAF pattern dispatch | 1–2 | `codex` | `proposed` |
| 4 | Structural Controller selection and bounded composition | 2–3 | `codex` | `proposed` |
| 5 | Relationship/query convergence | 1–3 | `codex` | `proposed` |
| 6 | Behavioral evaluation and runtime hardening | 3–5 | `codex` | `proposed` |
| 7 | Documentation and source-truth convergence | 1–6 | `codex` | `proposed` |

No task is parallelized: the shared contracts make overlapping writes unsafe.

## Task 1: Correctness and Revision Integrity

**Purpose:** prevent deterministic analytical errors and unaccepted state from
becoming durable or externally visible.

**Files and symbols:**

- `src/foresight_os/domain/models.py`: add immutable `MeasurementKey(region,
  measure, period, units, scenario, version)` and `CalculationRecord`; add
  durable calculation records to `AnalysisState` and its migration/schema
  representation. Preserve the current six-column fixture format by defaulting
  `scenario` to `default` and using the existing file version when optional
  fields are absent.
- `src/foresight_os/analysis/workbook.py`: make `WorkbookRow` expose the full
  `MeasurementKey`; preserve that identity through workbook parsing and
  calculation creation.
- `src/foresight_os/analysis/workbook.py`: change
  `calculate_case_metrics(rows: list[WorkbookRow])` to index by the full
  `MeasurementKey`, reject duplicate keys, and calculate typed facts from
  numeric values rather than parsing evidence prose.
- `src/foresight_os/analysis/analyst.py` and
  `src/foresight_os/analysis/workbook.py`: make `draft_analysis()` and
  `extract_evidence()` consume and emit durable `CalculationRecord` identities;
  evidence/calculation IDs must preserve the complete
  region/measure/period/units/scenario/version identity.
- `src/foresight_os/analysis/analyst.py`: make `draft_analysis()` consume the
  typed calculation records and generate statements from those records; remove
  the Northern Europe-only `next()` and substring lookup assumptions.
- `src/foresight_os/vertical_slice.py`: pass workbook rows/calculations into
  drafting and retain the current human acceptance boundary.
- `src/foresight_os/domain/validation.py` and
  `src/foresight_os/schemas/analysis.schema.json`: validate calculation-backed
  records, revision status, and migration defaults without invalidating legacy
  v0.1 files.
- `src/foresight_os/artifacts/report.py`: change the public entry point to
  `render_report(state, *, provisional=False)`. Normal reports require
  `RevisionStatus.ACCEPTED`, no stale artifacts, no reassessment-required
  referenced records, and inputs matching the current revision. Provisional
  reports must carry a `DRAFT / UNVALIDATED` label.
- `src/foresight_os/persistence/analysis_store.py`: protect the read/check/
  allocate/write sequence with a cross-process filesystem lock scoped to the
  investigation directory, allocate the next contiguous revision from the
  current durable state, retain `expected_revision` stale-writer rejection,
  and keep atomic replacement. `save_analysis()` is initialization/import-only;
  every durable mutation uses the same lock/check/allocate/validate/write
  boundary. Use `filelock>=3,<4` from `pyproject.toml` and store only the
  transient lock file beside the investigation state. Do not add a distributed
  lock service or a remote store.
- `src/foresight_os/persistence/analysis_store.py` and
  `src/foresight_os/persistence/recovery.py`:
  define pending-to-accepted/rejected transitions and preserve proposal IDs;
  continuation must commit through the same writer boundary and load the exact
  pending revision after a process restart rather than regenerate the analysis.
- `src/foresight_os/clients/first_client_adapter.py`: route `challenge()` and
  `scope_change()` through the writer boundary; they must not allocate
  revisions directly.
- `src/foresight_os/persistence/invalidation.py`: compute affected records only;
  remove revision allocation from `invalidate_dependencies()` and let the
  persistence writer commit the resulting state.

**Tests:**

- Extend `tests/test_calculation_revision.py` with multi-region, multi-period,
  unit, scenario, version, duplicate-key, contradictory-calculation, and
  calculation save/load round-trip cases.
- Extend `tests/test_vertical_slice.py` and `tests/test_report_fidelity.py` to
  reject pending/rejected/unassessed normal reports and accept explicitly
  labeled provisional reports.
- Extend `tests/test_persistence.py`, `tests/test_recovery.py`, and the client
  adapter tests with revision allocation, cross-process stale-writer rejection,
  pending-write/continuation races, legacy migration, and a fresh-process
  pending-review acceptance without regeneration. Verify accepted/rejected
  transitions preserve the original proposal IDs.
- Keep `tests/test_analysis_schema.py` authoritative for schema and endpoint
  validation.

**Exit criteria:**

- No calculation or claim depends on the first matching region/period/measure.
- The synthetic contradictory workbook is rejected or corrected before review
  acceptance.
- A pending revision cannot render an accepted executive report.
- Two separate processes using the same expected revision cannot both commit,
  and the durable revision history remains contiguous.
- Initialization/import is the only direct `save_analysis()` path; pending,
  accepted, rejected, continuation, challenge, scope-change, and invalidation
  writes all pass through one locked writer boundary.
- A fresh process can load a v0.1 state, migrate it, and continue safely.
- A fresh process can load an exact `PENDING_REVIEW` revision, accept or reject
  it, and preserve the original proposal IDs.

## Task 2: Runtime Contract and Capability Vocabulary

**Purpose:** make recipe purpose, execution pattern, capability state, and
pattern limits explicit before native orchestration is expanded.

**Files and symbols:**

- `src/foresight_os/controller/recipes.py`: introduce
  `ExecutionPattern` with `DIRECT`, `SEQUENTIAL`, `CONCURRENT`, `HANDOFF`, and
  `GROUP_CHAT`; introduce a purpose field independent of pattern; replace the
  current mixed `RecipeName`/`pattern` model with reusable participant role
  records and pattern-specific limits.
- `src/foresight_os/controller/recipes.py`: define one bounded limit contract
  per pattern: direct call/deadline, sequential stages/context policy,
  concurrent branch count/parallelism/failure policy, handoff destinations/
  hops/loop detection, and group-chat rounds/calls/termination.
- `src/foresight_os/controller/recipes.py`: define the shared immutable
  `RecipeStage(stage_id, pattern, participants, input_type, output_type,
  limits)` and `ExecutionRecipe.stages` ordered tuple. Simple recipes are
  one-stage tuples; runtime and evaluation consume this same representation.
- `src/foresight_os/runtime/capabilities.py`: replace the meaning of
  `DEFERRED_CAPABILITIES` with `PatternCapability(supported, available, reason)`
  for static product/runtime facts. Keep provider availability distinct from
  product support.
- `src/foresight_os/controller/policy.py`: remove `production_admitted` from
  `CandidateProbe`; add `PatternSelection(selected_patterns,
  selection_source, rationale, run_id)` for one ordered Controller decision.
  A simple recipe contains one selected pattern; a composed recipe contains
  the complete ordered stage sequence.
- `src/foresight_os/runtime/metrics.py`: add
  `PatternMeasurement(run_id, pattern, provider, model, endpoint, case_id,
  revision, metrics)` plus pattern-specific counters for branches,
  parallelism, handoffs, chat rounds, retries, failures, and cleanup. An
  aggregate view may combine capability, selection, and measurement records for
  reports, but no single mutable status object owns all three scopes.
- `tests/test_controller_selection.py` and `tests/test_maf_fit.py`: replace
  deferred/admitted assertions with support/availability/selection/measurement
  assertions.

**Exit criteria:**

- A recipe can express `CHALLENGE_RECOMMENDATION` as purpose plus
  `GROUP_CHAT` pattern without creating a `GroupChatSkeptic` role type.
- Pattern support is not turned off merely because one provider is unavailable
  or one measurement is poor.
- Capability records, per-run selections, and run measurements cannot be
  mistaken for one another or queried without their scope identifiers.
- Every recipe exposes limits that the runtime can enforce and metrics that the
  evaluator can report.

## Task 3: Native MAF Pattern Dispatch

**Purpose:** make the declared pattern determine actual runtime behavior using
native MAF APIs through one thin asynchronous entry point.

**Discovery and version gate:** before implementation, inspect the installed
`agent-framework==1.21.0` public APIs for sequential chaining, concurrent
fan-out/fan-in, handoff, group chat, typed response formats, checkpointing,
timeouts, and cancellation. The confirmed native orchestration surface is
`agent_framework.orchestrations.SequentialBuilder`,
`ConcurrentBuilder`, `HandoffBuilder`, and `GroupChatBuilder`; verify their
installed signatures and exact package/orchestration versions before coding.
Record those versions and only confirmed APIs in
`docs/intent/maf-capability-decision.md`.

Sequential, Concurrent, Handoff, and Group Chat are essential product
capabilities for this delivery. If a required native API is absent from
`1.21.0`, test the smallest compatible MAF upgrade, update the bounded version
pin in `pyproject.toml`, and rerun the capability probe. If no supported MAF
version provides the required native API, stop the task with an architecture
blocker; do not mark the pattern supported and do not build a Foresight-specific
compatibility orchestration engine merely to preserve `1.21.0`.

**Files and symbols:**

- `src/foresight_os/runtime/orchestration.py`: create the single
  `run_recipe_async(recipe, prompt, client=None, run_id=None)` dispatcher. It
  iterates the ordered `ExecutionRecipe.stages`, selects a thin native-MAF
  adapter from each `RecipeStage.pattern`, validates the stage input/output
  contract, passes the typed output to the next stage, applies stage limits,
  returns the final typed output plus one `RunMetrics`, and settles resources
  in success, failure, timeout, and cancellation paths.
- `src/foresight_os/runtime/executors.py`: define typed boundary results for
  analyst proposals, reviews, concurrent branch results, handoff decisions,
  and challenge proposals. Validate provider responses with the existing MAF
  response-format mechanism and then apply domain validation before producing a
  `ProposedChange`.
- `src/foresight_os/runtime/workflow.py`: retain only compatibility helpers or
  delegate to `orchestration.py`; remove the current unconditional
  Analyst-then-Reviewer behavior from the production path.
- `src/foresight_os/runtime/group_chat.py`: retain `ChallengeProposal` domain
  validation and deterministic test doubles, but remove the production
  Analyst/Skeptic alternation loop once the native Group Chat adapter is
  available.
- `src/foresight_os/runtime/provider_config.py` and
  `src/foresight_os/runtime/maf_probe.py`: reuse explicit custom-provider
  credential selection and add capability probes for each native pattern
  without printing keys, prompts, responses, headers, or request bodies.
- `pyproject.toml`: add a direct structured-output dependency only if the
  installed MAF package does not expose the required public schema dependency;
  keep the version bounded and justify it in the capability decision record.

**Tests:**

- Add `tests/test_orchestration_patterns.py` using the real native
  `SequentialBuilder`, `ConcurrentBuilder`, `HandoffBuilder`, and
  `GroupChatBuilder` with deterministic fake participants/clients. Prove
  Sequential passes upstream output, Concurrent overlaps and aggregates,
  Handoff transfers only to allowed destinations, Group Chat shares context and
  terminates, and composed stages pass typed output forward. Use fake workflows
  only for adapter error-path tests.
- Extend `tests/test_runtime_boundaries.py` for metrics, timeout, cancellation,
  provider failure, cleanup, and a fresh-process native checkpoint restart:
  checkpoint after an observable completed stage, terminate the process,
  restore through native MAF storage, run only remaining stages, and assert the
  completed stage is not duplicated.
- Keep `tests/test_maf_fit.py` as the import/API boundary test and add an
  explicit environment-gated live test command for the configured `9router`
  provider; the default test suite must remain deterministic.

**Exit criteria:**

- The same `run_recipe_async()` entry point executes all five patterns.
- No production pattern path silently falls back to Analyst → Reviewer.
- Unsupported provider/runtime APIs are reported as unavailable; they do not
  masquerade as successful execution.
- The supported installation has native MAF support for every essential
  pattern; provider-specific availability may still vary at runtime.
- Native builder tests exercise the installed MAF orchestration surface, and
  checkpoint restart proves resume behavior across a process boundary rather
  than only round-tripping an in-memory checkpoint object.
- A bounded live `9router` run returns validated structured output and sanitized
  metrics.

## Task 4: Structural Controller Selection and Bounded Composition

**Purpose:** choose patterns from work structure and explicit user intent while
keeping composition small, inspectable, and bounded.

**Files and symbols:**

- Add `src/foresight_os/controller/task_shape.py` with immutable
  `TaskShape(ordered_dependencies, independent_subtasks,
  dynamic_specialist_routing, interactive_deliberation, review_required)`.
  Validate only malformed or logically impossible values. Multiple true
  signals are valid and describe composition, for example independent
  subtasks plus review means Concurrent followed by Sequential review, while
  independent subtasks plus interactive deliberation means Concurrent followed
  by Group Chat.
- `src/foresight_os/domain/models.py` and
  `src/foresight_os/schemas/work_brief.schema.json`: add an optional validated
  execution-pattern override and preserve migration defaults for existing
  Work Briefs.
- `src/foresight_os/controller/policy.py`: change
  `select_recipe(brief, task_shape, override=None)` to apply precedence
  `valid explicit override → structural task shape → Controller default`.
  Return the recipe plus `PatternSelection` containing its ordered
  `selected_patterns`, selection source, rationale, and Run identifier.
- `src/foresight_os/controller/recipes.py`: consume the `RecipeStage` contract
  established in Task 2; only transitions declared by the recipe are valid.
  Replanning is allowed only after a stage completes or is stopped at a
  checkpoint boundary; produce a new `ExecutionRecipe`/Run rather than
  mutating an active MAF topology. Do not add a generic scheduler or
  `AGENTIC` pattern.
- `src/foresight_os/controller/policy.py`: define override semantics: a
  one-element override may replace a simple recipe; a multi-element override
  replaces the complete composition only after stage-contract validation, with
  `review_required` never silently removed. Map signals in this canonical
  order: `independent_subtasks → CONCURRENT`,
  `dynamic_specialist_routing → HANDOFF`,
  `interactive_deliberation → GROUP_CHAT`, and one final `SEQUENTIAL` stage
  for ordered synthesis and/or required review. A `SEQUENTIAL` stage carries
  both synthesis and review when both are true, so the composition never
  exceeds four stages. Record the rejected override reason when validation
  fails.
- `src/foresight_os/controller/budgets.py`: replace the single global call
  guard with pattern-specific limits while preserving one common metering
  implementation.
- Keep roles reusable (`Scout`, `Analyst`, `Validator`, `Strategist`, `Skeptic`)
  and independent of patterns; configure purpose, profile, tools, and pattern
  in the recipe.

**Tests:**

- Extend `tests/test_controller_selection.py` with one representative Work
  Brief for each default mapping: direct operation, ordered synthesis,
  independent branches, specialist routing, and interactive challenge.
- Test valid and invalid user overrides, selection rationale, deterministic
  multi-signal mapping, composed `CONCURRENT → GROUP_CHAT → SEQUENTIAL`
  stages, loop prevention, the four-stage maximum, and each pattern's budget
  exhaustion behavior.

**Exit criteria:**

- Controller selection is explainable from Work Brief/task shape and does not
  depend on a benchmark admission flag.
- Explicit user intent can override a default only when the pattern is
  supported and available; the decision records why an override was rejected.
- Composition stays bounded by stage count, per-pattern limits, and one Run
  metrics record.
- Runtime and evaluation consume the same ordered `RecipeStage` contracts;
  override validation cannot remove a required review stage.
- Findings can trigger a new recipe only at a settled stage boundary, with the
  prior checkpoint and reason preserved for recovery and observability.

## Task 5: Relationship and Query Convergence

**Purpose:** make relationship semantics authoritative for invalidation,
provenance, evidence interpretation, graph traversal, and bounded AI context.

**Files and symbols:**

- `src/foresight_os/domain/relationships.py`: expand `RelationshipRule` with
  semantic direction, impact direction, provenance direction, and evidence role
  for `supports`, `contradicts`, `derived_from`, `depends_on`, `informs`,
  `produces`, and `supersedes`.
- `src/foresight_os/domain/validation.py`: validate endpoint kinds against the
  expanded registry and reject relationship metadata that conflicts with the
  canonical rule.
- `src/foresight_os/persistence/invalidation.py`: use the registry's impact
  direction to compute the complete affected set without depth/record limits;
  fail explicitly if the complete traversal cannot finish.
- `src/foresight_os/graph/projection.py`: keep `AnalysisState` as the source
  of truth and build one derived `networkx.MultiDiGraph` plus lightweight
  adjacency views for `impact_forward`, `impact_reverse`, `provenance`,
  `support`, and `counterevidence`. Return a `GraphView` carrying the graph,
  investigation ID, and analysis revision.
- `src/foresight_os/graph/queries.py`: expose a complete impact query and a
  bounded context query. The bounded result must include investigation ID,
  analysis revision, selected items, depth, limit, and `truncated` metadata.
  Every traversal uses a visited set, excludes the starting node from its own
  result, deduplicates paths, and terminates on cycles such as `A → B → C → A`.
- `src/foresight_os/runtime/orchestration.py`: seed each participant with the
  relevant graph slice rather than the entire investigation history.

**Tests:**

- Extend `tests/test_invalidation.py` for forward and reverse impact semantics,
  counterevidence, provenance, and complete traversal.
- Extend `tests/test_graph.py` for deterministic rebuilds, each adjacency view,
  direction-sensitive queries, bounded context metadata, revision-scoped
  `GraphView` results, cycle protection, starting-node exclusion, path
  deduplication, and no durable graph state.
- Add a regression showing that a bounded context result is never reused as a
  complete invalidation result.

**Exit criteria:**

- Every consumer uses `AnalysisState.relationships` and the registry rather
  than maintaining an independent dependency interpretation.
- Invalidation never returns a silently truncated affected set.
- AI context is bounded and tells the agent when the neighborhood is partial.
- NetworkX remains rebuildable from durable state and has no persistence API.

## Task 6: Behavioral Evaluation and Runtime Hardening

**Purpose:** prove execution behavior and tune defaults without confusing
quality measurement with capability support.

**Files and symbols:**

- `evaluation/run.py` and `evaluation/candidate_harness.py`: split evaluation
  into pattern contract runs and Controller selection runs. The candidate Run
  must produce the `AnalysisState` and typed artifact consumed by its scorer;
  remove the disconnected `run_vertical_slice()` scoring path. Add explicit
  `supported`, `available`, `selected`, and `measured` fields; retain quality,
  latency, model calls, tokens, retries, failures, parallelism, handoffs, chat
  rounds, and human-correction metrics.
- Add `evaluation/pattern_contracts.py` for deterministic fake-client contract
  scenarios covering Sequential, Concurrent, Handoff, Group Chat, and one
  composed workflow. Keep the frozen workbook cases for analytical quality.
- Add `evaluation/task_shapes.json` containing five fixed Work Brief shapes,
  participant input contracts, expected ordered `RecipeStage` pattern
  sequences, and applicable quality cases; use it for Controller selection
  accuracy. Do not infer specialist-routing or deliberation requirements from
  the current decision text.
- `evaluation/README.md` and `evaluation/rubric.md`: distinguish contract
  correctness, runtime/provider availability, Controller selection, and
  measured performance. Do not call a pattern unsupported because it is slower.
- `src/foresight_os/runtime/metrics.py`: ensure metrics settle on all terminal
  paths and distinguish provider failures from domain validation failures.
- `src/foresight_os/persistence/recovery.py`: exercise checkpoint restart,
  pending review, stale writer rejection, and artifact regeneration after
  invalidation.
- Add three evaluation matrices with explicit scopes: pattern contracts run
  every supported pattern on minimal deterministic fixtures; Controller
  selection runs all five fixed Work Brief shapes; performance/quality compares
  only patterns materially relevant to each shape. Use the existing cases as
  follows: `case-001` for direct/sequential baseline, `case-002` for
  independent-branch sequential/concurrent comparison, `case-003` for
  specialist-routing sequential/handoff comparison, `case-004` for
  conflicting-interpretation sequential/group-chat comparison, and `case-005`
  for the selected composed workflow plus recovery. An all-pattern run is
  diagnostic only, never the standard matrix.
- Add a regression that mutating the candidate Run's analytical output changes
  its quality score, proving the scorer is attached to the execution it reports.

**Verification commands:**

```text
python -m pytest -q
python -m compileall -q src tests
python evaluation/run.py --matrix contract
python evaluation/run.py --matrix controller --task-shapes evaluation/task_shapes.json
python evaluation/run.py --case evaluation/cases/case-001 --compare direct,sequential --write-report evaluation/results/case-001-patterns.md
python evaluation/run.py --case evaluation/cases/case-002 --compare sequential,concurrent --write-report evaluation/results/case-002-patterns.md
python evaluation/run.py --case evaluation/cases/case-003 --compare sequential,handoff --write-report evaluation/results/case-003-patterns.md
python evaluation/run.py --case evaluation/cases/case-004 --compare sequential,group_chat --write-report evaluation/results/case-004-patterns.md
python evaluation/run.py --case evaluation/cases/case-005 --compare composed --write-report evaluation/results/case-005-composed.md
python -m build --wheel --outdir dist
```

Run the environment-gated live proof separately with the repository `.env` and
active Codex provider configuration:

```text
python -m foresight_os.runtime.maf_probe --env-file .env --config-file "$HOME/.codex/config.toml"
python evaluation/run.py --live-smoke --pattern sequential --env-file .env --config-file "$HOME/.codex/config.toml"
python evaluation/run.py --live-smoke --pattern concurrent --env-file .env --config-file "$HOME/.codex/config.toml"
python evaluation/run.py --live-smoke --pattern handoff --env-file .env --config-file "$HOME/.codex/config.toml"
python evaluation/run.py --live-smoke --pattern group_chat --env-file .env --config-file "$HOME/.codex/config.toml"
```

The live commands must report provider/model/endpoint/package/status/latency
and sanitized metrics only. They must not write credentials or model content
to tracked reports.

**Exit criteria:**

- Each pattern has a passing behavioral contract test or an explicit
  unavailable-runtime result.
- Controller selection accuracy is measured independently from pattern support.
- Live provider runs exercise the native runtime rather than the deterministic
  vertical slice.
- Each live smoke targets one native pattern with a minimal bounded workflow;
  full analytical cases are reserved for patterns relevant to their task shape.
- Success, failure, timeout, cancellation, checkpoint restart, and cleanup
  leave settled metrics and no leaked client/workflow resources.
- Measurement results tune defaults and budgets; they do not change the
  `supported` contract field.

## Task 7: Documentation and Source-Truth Convergence

**Purpose:** remove contradictory current statements while preserving history.

**Files:**

- `README.md`: state that Foresight OS supports Direct, Sequential, Concurrent,
  Handoff, and Group Chat as bounded capabilities; explain that the Controller
  selects patterns structurally and measurements tune defaults.
- `docs/intent/maf-capability-decision.md`: record confirmed native MAF builder
  imports (`SequentialBuilder`, `ConcurrentBuilder`, `HandoffBuilder`, and
  `GroupChatBuilder`), exact installed package/orchestration versions, provider
  availability, structured-output behavior, checkpoint behavior, and explicit
  limits for the installed `agent-framework==1.21.0` or approved upgrade.
- `evaluation/README.md` and `evaluation/rubric.md`: use separate capability,
  selection, and measurement records and remove old `production_admitted`
  wording.
- `src/foresight_os/schemas/`: establish this directory as the only manually
  editable schema source. Remove any root-level `schemas/` copies, or mark
  them explicitly historical if a migration fixture requires them; never keep
  two editable schema trees.
- `tests/test_maf_fit.py`, `tests/test_controller_selection.py`, and runtime
  capability tests: make test names and assertions match current terminology.
- `docs/superpowers/plans/foresight-os-next-phase-recommended-delivery.md`:
  retain as the completed historical delivery record; add no retroactive
  claims. The new plan becomes completed only after final verification.

**Exit criteria:**

- README, capability decision, Controller policy, runtime status, tests, and
  evaluation reports describe the same supported-pattern contract.
- No current document says a supported pattern is disallowed solely because
  benchmark uplift was not measured.
- Historical v0.1 decisions remain attributable and are not rewritten.

## Verification

Before changing this plan's status from `proposed` to `completed`, run:

```text
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "pytest failed" }
python -m compileall -q src tests
if ($LASTEXITCODE -ne 0) { throw "compileall failed" }
$verify_root = Join-Path ([IO.Path]::GetTempPath()) ("foresight-os-wheel-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $verify_root | Out-Null
python -m build --wheel --outdir "$verify_root/wheel"
if ($LASTEXITCODE -ne 0) { throw "wheel build failed" }
$wheels = @(Get-ChildItem "$verify_root/wheel/*.whl")
if ($wheels.Count -ne 1) { throw "expected exactly one newly built wheel" }
python -m pip install --target "$verify_root/install" $wheels[0].FullName
if ($LASTEXITCODE -ne 0) { throw "wheel install failed" }
Push-Location "$verify_root/install"
python -c "import json, importlib.resources as r, foresight_os; from agent_framework.orchestrations import SequentialBuilder, ConcurrentBuilder, HandoffBuilder, GroupChatBuilder; from foresight_os.runtime.orchestration import run_recipe_async; assert str(foresight_os.__file__).startswith(str(__import__('pathlib').Path.cwd())); json.loads(r.files(foresight_os).joinpath('schemas/analysis.schema.json').read_text()); json.loads(r.files(foresight_os).joinpath('schemas/work_brief.schema.json').read_text()); print(foresight_os.__file__)"
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "installed-package smoke failed" }
Pop-Location
Remove-Item -Recurse -Force $verify_root
git diff --check
if ($LASTEXITCODE -ne 0) { throw "git diff --check failed" }
```

The package checks must use a newly allocated temporary directory outside the
checkout, require exactly one wheel from that build, and run from its fresh
install target with that target first on `sys.path`; otherwise
`pyproject.toml`'s source-tree test path can silently import `src/foresight_os`
or a stale wheel. Parse both packaged schemas and explicitly import all four
native builders alongside the installed `run_recipe_async`; keep normal
source-tree tests as a separate command.

Also inspect a migrated analysis, an accepted report, a provisional report,
an exact fresh-process `PENDING_REVIEW` recovery, cross-process commit-lock
behavior, the relationship/query metadata including a cyclic graph, one
task-shaped deterministic evaluation report, and one sanitized live-provider
pattern smoke per native pattern. Run the configured live probe with explicit
provider selection and record only its sanitized result. Confirm that
`src/foresight_os/schemas/` is the sole editable schema location.

`skill-verification-before-completion` must return `verified` against the
current HEAD plus the exact staged, unstaged, and untracked in-scope changes,
record their content identity, report no unexplained out-of-scope changes, and
include test output, approved deferrals, and residual risks before this plan is
marked completed. A commit is not required before this verification; commit and
branch disposition remain separately authorized actions.

## Completion Criteria

1. Calculation-backed facts are identity-keyed, deterministic, and reject the
   known contradictory case.
2. Normal artifacts require accepted current revisions; provisional artifacts
   are visibly labeled and never masquerade as accepted output.
3. Single-writer revision commits are atomic, contiguous, and stale-writer
   safe across processes through a filesystem lock, without a distributed lock
   service.
4. Recipe purpose is separate from `ExecutionPattern`, and all five patterns
   have explicit bounded contracts.
5. One async runtime entry point dispatches to native MAF behavior for every
   available pattern; no production path silently uses Analyst → Reviewer.
6. Controller selection follows explicit override, task shape, then default,
   and bounded compositions pass typed stage outputs forward.
7. Relationship semantics drive invalidation, provenance, graph traversal, and
   AI context; invalidation is complete and context retrieval is bounded with
   truncation metadata.
8. Evaluation separately reports static capability, per-run selection, and
   scoped measurement records, and includes actual pattern contract and
   live-provider evidence.
9. Provider credentials and model content do not appear in tracked files,
   logs, telemetry, or reports.
10. `src/foresight_os/schemas/` is the only editable schema tree.
11. Documentation and tests agree with the implemented capability contract,
    while the prior plan remains a historical record.
