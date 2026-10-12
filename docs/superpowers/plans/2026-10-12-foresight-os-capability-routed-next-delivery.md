---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: foresight-os-capability-routed-next-delivery
targets:
  - src/foresight_os/controller/
  - src/foresight_os/domain/
  - src/foresight_os/graph/
  - src/foresight_os/runtime/
  - src/foresight_os/schemas/
  - evaluation/
  - tests/
  - docs/intent/
  - README.md
  - pyproject.toml
related_features:
  - native pattern execution
  - semantic capability routing
  - evidence-aware tool use
  - relationship-aware context retrieval
  - truthful runtime evaluation
related_stages:
  - post-27c678a capability-routed runtime
---

# Foresight OS Capability-Routed Next Delivery

## Verdict Review

**Decision: approve with architectural refinements.** The supplied verdict is
correct that native MAF pattern support is now substantially present, while
agent construction, capability assignment, runtime enforcement, resource
lifecycle, and evidence ingestion are still fragmented. The next delivery
should implement that missing layer without creating a second orchestration
engine.

The verdict needs these refinements before execution:

- Treat pattern support, runtime availability, Controller selection, and run
  measurement as four separate statuses. Historical benchmark results must not
  make an implemented pattern unavailable.
- Make Wayfinding emit ordered work stages and make review an analytical
  responsibility, not a requirement that the recipe contain Sequential.
- Keep recipes declarative: participants name semantic capability IDs; they do
  not contain MAF, provider, or MCP objects.
- Remove silent API degradation. A known MAF adapter may handle a proven API
  variant, but a broad `TypeError` fallback must not silently drop identity,
  persistence, tools, or profile settings.
- Route every external result through an untrusted `EvidenceCandidate` and
  domain validation before it can influence durable analytical records.
- Keep graph indexes rebuildable and run-scoped retrieval caching bounded. Do
  not add a routing service, general DAG/planner engine, persistent semantic
  cache, or broad external-mutation surface in this delivery.

## Goal

Deliver a small capability-routed runtime in which the Foresight Controller
selects work stages, pattern composition, participants, profiles, semantic
capabilities, context, and limits for a Run; one shared factory constructs all
participants; a small resolver lazily binds only required capabilities; MAF
owns native orchestration; and tool output enters the domain as
provenance-bearing evidence proposals. Runtime limits, failure classes,
cleanup, and metrics must be truthful on success and failure.

Preserve the durable vocabulary:

```text
Investigation → Work Brief → Work Stages → Execution Recipe → Run → Analysis State → Artifact
```

Preserve these ownership boundaries:

- Work Brief and Wayfinding own objective, scope, assumptions, deliverables,
  research needs, and ordered work stages.
- Foresight Controller owns pattern composition, participant configuration,
  profiles, capability requirements, limits, escalation, and rationale.
- Execution Recipe owns the bounded declarative specification of one Run.
- Capability Catalog and Resolver own semantic capability definitions and
  runtime bindings; they are not a service and do not change authority.
- MAF owns agent execution, native workflow mechanics, tool invocation, and
  checkpoint mechanics.
- Domain code owns evidence semantics, calculations, validation, proposal
  acceptance, and durable revision truth.
- NetworkX remains a rebuildable derived view; Persistence remains the single
  revision-safe writer; Human review remains required for consequential
  decisions or external mutation capabilities.

## Implementation Outcomes

### Runtime correctness and lifecycle

`run_recipe_async()` enforces declared limits before dispatch, distinguishes
provider, tool, domain-validation, timeout, cancellation, budget, and cleanup
failures, preserves settled metrics when execution fails, cleans Direct and
native participants consistently, and removes the broad `TypeError` fallback.
Concurrent stages pass an explicit aggregate to later stages, and Handoff
tests prove an observed transfer rather than only a legal topology.

### Declarative participants and capability resolution

Work stages and `ParticipantConfig` keep role, purpose, profile, capabilities,
data scope, limits, and structured-output requirements independent from the
workflow pattern. A shared `AgentFactory` constructs all native participants
with only their assigned capabilities. A small resolver performs native-first,
lazy, run-scoped resolution with bounded parallelism and explicit unavailable
or denied results.

### Evidence, graph, and evaluation integrity

Tool results normalize into `EvidenceCandidate` with source and retrieval
provenance, remain untrusted until validated, and cannot alter instructions,
budgets, permissions, or durable claims. Graph projection derives
relation-aware indexes once per revision; correctness-critical invalidation
remains complete, while agent-facing context is bounded and reports
per-channel truncation. Evaluation records runtime behavior without using
measurements to disable supported capabilities.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit tracked source, tests, schemas, documentation, evaluation fixtures, and this plan; run declared deterministic checks and sanitized configured live probes without recording secrets, prompts, raw provider output, or external artifacts; install the newly built local wheel with `--no-deps` into a temporary verification target
- User-approval actions: install or upgrade external dependencies, authenticate, send data outside the workspace, publish, push, merge, commit, discard changes, destructive recovery, and unrelated cleanup
- Parallel ownership: none; shared recipe, runtime, domain, and evaluation contracts require one writer
- Sequential fallback: execute Tasks 1 through 6 in dependency order

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `27c678a7faf8ecce3788f1af630fadeb30eb7bee`
- Expected workspace: `tracked tree at base commit plus preserved untracked build/, src/foresight_os.egg-info/, and work/ probe outputs; do not clean or overwrite those outputs`
- Next action: `none; plan verified and complete`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | focused runtime boundary and failure tests | `python -m pytest -q tests/test_orchestration_patterns.py tests/test_runtime_boundaries.py tests/test_controller_selection.py` — 14 passed; `git diff --check` passed |
| Task 2 | `completed` | current | `codex` | Task 1 | recipe, work-stage, profile, and factory tests | focused controller/schema/runtime suite passed |
| Task 3 | `completed` | current | `codex` | Task 2 | capability resolution, denial, lifecycle, and reuse tests | capability, evidence, and runtime suites passed |
| Task 4 | `completed` | current | `codex` | Tasks 1–3 | four tool-enabled pattern proofs and denied-tool proof | tool-enabled and native pattern suites passed |
| Task 5 | `completed` | current | `codex` | Tasks 2–4 | evidence validation and graph query/invalidation tests | evidence, graph, and invalidation suites passed |
| Task 6 | `completed` | current | `codex` | Tasks 1–5 | evaluation matrices, package smoke, and sanitized live probes | 66 tests; compileall; matrices passed; case evaluation passed; wheel/import/schema smoke passed; preserved hashes unchanged; four sanitized provider smokes passed; diff check passed |

## Task Breakdown

### Task 1: Converge runtime limits, failures, and cleanup

**Purpose:**
- Make the existing runtime contract enforceable and observable before adding
  participant tools or new capability sources.

**Task Function:**
- Runtime correctness convergence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded local runtime change with clear source and test
  contracts; no delegated benefit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused automated boundary tests are sufficient; final
  verification remains independent.

**Specification Coverage:**
- Verdict sections 16–18, 21–23, and the first recommended increment.
- Runtime limits are checked before dispatch; failure categories remain
  distinct; settled metrics survive failure; resources close on success,
  failure, timeout, and cancellation.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/workflow.py:_run_native_stage`, `run_recipe_async`, `_close_agents`
- Inspect: `src/foresight_os/runtime/metrics.py:RunMetrics`, `RunResult`
- Inspect: `src/foresight_os/controller/budgets.py:BudgetState`, `src/foresight_os/controller/recipes.py:RecipeStage`
- Inspect: `src/foresight_os/runtime/executors.py:AnalystExecutor`, `ReviewerExecutor`
- Modify: `src/foresight_os/runtime/workflow.py`, `src/foresight_os/runtime/metrics.py`, `src/foresight_os/controller/budgets.py`, and the smallest required recipe limit declarations
- Modify: `src/foresight_os/runtime/executors.py` for Direct resource cleanup; Task 2 later converges this owner onto the shared factory
- Verify: `tests/test_orchestration_patterns.py`, `tests/test_runtime_boundaries.py`, and a focused runtime-limits test module if needed

**Dependencies:**
- Base commit `27c678a`; preserve the native MAF 1.21.0 boundary.
- Do not introduce tools or provider integrations in this task.

**Authority:**
- Preauthorized local actions: edit the listed runtime/controller/executor files and focused tests; run focused pytest and compile checks
- Stop for: a MAF API change requiring dependency installation, a provider/authentication change, or any modification to preserved untracked probe outputs

**Steps:**
- [x] Step 1: Normalize recipe/stage limits into one runtime budget view and reject a dispatch before it exceeds agent-call, step, correction, branch, handoff, round, tool, or configured timeout bounds.
- [x] Step 2: Add explicit failure classification and settled metrics access for budget, timeout, cancellation, provider, tool, domain-validation, and cleanup failures; do not collapse them into `provider_failures`.
- [x] Step 3: Make Direct and native paths share cleanup accounting, and remove the broad `except TypeError` constructor fallback in favor of one proven MAF adapter contract.
- [x] Step 4: Replace last-output composition with an explicit concurrent aggregate containing branch results and failures; preserve typed stage boundaries.
- [x] Step 5: Add a deterministic Handoff fixture that emits a real transfer event and assert metrics report the observed transfer count.

**Verification:**
- [x] `python -m pytest -q tests/test_orchestration_patterns.py tests/test_runtime_boundaries.py tests/test_controller_selection.py`
- Expected: limits stop dispatch before the next call; failure metrics remain inspectable; cleanup attempts every resource; Handoff transfer count is event-derived.

**Exit Criteria:**
- No broad constructor fallback remains in production runtime code.
- Direct, native, and composed runs enforce declared limits and expose settled
  failure metrics without claiming unobserved transfers.

### Task 2: Add ordered work stages, declarative participants, and one agent factory

**Purpose:**
- Separate work intent, pattern topology, role responsibility, profile, and
  capability assignment while making every participant use one construction
  and lifecycle path.

**Task Function:**
- Controller and participant-contract convergence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-layer contract change with one canonical recipe path;
  controller authority and acceptance stay local.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: controller/schema/factory tests plus final package
  verification cover the contract.

**Specification Coverage:**
- Verdict sections 2, 13–15, and 28.
- Review responsibility must not imply Sequential; profiles must affect known
  agent construction settings; no pattern-specific participant subclasses.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/domain/models.py:WorkBrief`, `src/foresight_os/wayfinding.py:create_work_brief`
- Inspect: `src/foresight_os/controller/task_shape.py:TaskShape`, `src/foresight_os/controller/policy.py:select_recipe`, `_recipe_for_patterns`
- Inspect: `src/foresight_os/controller/recipes.py:RecipeStage`, `ExecutionRecipe`, `make_recipe`; `src/foresight_os/controller/profiles.py:Profile`, `PRESETS`
- Inspect: `src/foresight_os/runtime/executors.py:AnalystExecutor`, `ReviewerExecutor`; `src/foresight_os/runtime/workflow.py:run_recipe_async`
- Modify: `src/foresight_os/domain/models.py`, `src/foresight_os/domain/validation.py`, `src/foresight_os/controller/task_shape.py`, `src/foresight_os/controller/recipes.py`, `src/foresight_os/controller/policy.py`, `src/foresight_os/controller/profiles.py`, `src/foresight_os/wayfinding.py`
- Modify: `src/foresight_os/runtime/executors.py`, `src/foresight_os/runtime/workflow.py`
- Add: `src/foresight_os/runtime/participants.py` with `ParticipantConfig` and `AgentFactory`, unless an existing runtime module can own the same contract without duplication
- Verify: `src/foresight_os/schemas/work_brief.schema.json`, `tests/test_controller_selection.py`, `tests/test_analysis_schema.py`, and focused participant/factory tests

**Dependencies:**
- Task 1 supplies the runtime budget and cleanup contract.
- Keep Work Brief migration backward-compatible by defaulting absent stages.

**Authority:**
- Preauthorized local actions: edit controller/domain/runtime contract files, the editable packaged Work Brief schema, focused tests, and documentation needed to explain the new vocabulary
- Stop for: a second schema source, a required public migration outside the existing Work Brief/Analysis State boundary, or a model configuration API not proven by the local MAF package

**Steps:**
- [x] Step 1: Add ordered `WorkStage` data with objective, participants/subtasks, dependencies, expected result, and research needs; preserve legacy briefs through migration defaults.
- [x] Step 2: Add declarative `ParticipantConfig` with `id`, `role`, `purpose`, `profile`, `capability_ids`, `data_scope`, `limits`, and `structured_output`.
- [x] Step 3: Make Controller selection consume ordered stages and validate review responsibility rather than requiring Sequential specifically; preserve override safety and bounded composition.
- [x] Step 4: Implement `AgentFactory.create(participant_config, run_context)` for identity, instructions, supported profile/model settings, structured output, assigned tools, context, history, and cleanup registration.
- [x] Step 5: Route Direct and all native builders through the factory; unsupported options must produce explicit unavailable results rather than silently dropping them.

**Verification:**
- [x] `python -m pytest -q tests/test_controller_selection.py tests/test_analysis_schema.py tests/test_maf_fit.py tests/test_orchestration_patterns.py tests/test_runtime_boundaries.py`
- Expected: task-shape composition is ordered and deterministic; review can be fulfilled by a non-Sequential topology; legacy Work Briefs validate; profile settings reach the factory boundary.

**Exit Criteria:**
- No production path constructs a participant outside the shared factory.
- Recipes contain semantic participant configuration, not concrete MAF/provider/
  MCP objects.
### Task 3: Implement the small semantic capability catalog and resolver

**Purpose:**
- Resolve only the capabilities a Run actually needs, with least privilege,
  run-local reuse, bounded concurrency, and explicit lifecycle ownership.

**Task Function:**
- Capability boundary and resource-lifecycle implementation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded local adapter work with security and lifecycle
  implications; controller retains authority.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic fake capabilities and direct lifecycle tests
  provide the required proof without external access.

**Specification Coverage:**
- Verdict sections 3–12, 22–24, and the third recommended increment.
- Resolution order is local deterministic, native/provider, configured MCP,
  thin adapter, then demonstrated custom gap; missing capability is explicit,
  not silently substituted.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/capabilities.py:CapabilityDecision`, `CapabilityResult`, `PatternCapability`
- Inspect: `src/foresight_os/runtime/provider_config.py`, `src/foresight_os/runtime/participants.py:AgentFactory`
- Inspect: `src/foresight_os/domain/models.py:EvidenceCandidate` and `src/foresight_os/domain/validation.py` after the boundary is added
- Modify: `src/foresight_os/runtime/capabilities.py`, `src/foresight_os/runtime/participants.py`, `src/foresight_os/runtime/workflow.py`, `src/foresight_os/domain/models.py`, `src/foresight_os/domain/validation.py`, `src/foresight_os/schemas/analysis.schema.json`
- Add only if needed: one small runtime capability adapter module; do not create a routing service or provider registry
- Verify: focused capability tests plus `tests/test_maf_fit.py` and runtime-boundary tests

**Dependencies:**
- Task 2 defines participant capability IDs and the shared factory boundary.
- Existing provider configuration remains the only configured credential source;
  no secret may enter recipes, logs, reports, or tests.

**Authority:**
- Preauthorized local actions: edit the listed runtime capability/factory/domain/schema files and deterministic tests; use only already configured local provider/MCP boundaries for optional sanitized probes
- Stop for: installing tools, authenticating, adding a new external service, sending source data outside the workspace, or changing project MCP configuration

**Steps:**
- [x] Step 1: Define `CapabilityDefinition` with semantic ID, class (`local_deterministic`, `external_read`, `external_mutation`), access, share scope, max parallelism, and approval policy; retain pattern status separately.
- [x] Step 2: Implement `CapabilityResolver.resolve(required_capabilities, run_context)` with lazy initialization, native-first resolution, explicit availability/denial reasons, and one run-owned resource scope.
- [x] Step 3: Bind first local capabilities (`graph_context`, deterministic calculation/domain validation) and provider/MCP adapters only behind explicit configured boundaries; external mutation remains unavailable without human authority.
- [x] Step 4: Enforce participant-scoped tool lists and destination-scoped Handoff capabilities; a handoff transfers task/context/evidence/rationale, never sender permissions or credentials.
- [x] Step 5: Add run-local retrieval deduplication keyed by capability ID, normalized request, and freshness scope; share only when the definition permits safe reuse.
- [x] Step 6: Define the minimal untrusted `EvidenceCandidate` and raw-result normalizer before any tool-enabled pattern proof; keep durable acceptance and graph indexing in Task 5.

**Verification:**
- [x] Focused pytest covering lazy resolution, unavailable capability status, participant denial, Handoff non-inheritance, run reuse, max parallelism, cleanup on failure, and duplicate retrieval suppression.
- Expected: a participant cannot invoke an unassigned capability; compatible requests reuse one run resource; resources close after success and failure; no fallback changes authority.

**Exit Criteria:**
- The resolver is a small in-process component with no independent service,
  scheduler, or generic provider catalog.
- Agent construction receives only resolved tools assigned to that participant
  and reports missing capabilities explicitly.

### Task 4: Prove tool-enabled native pattern behavior

**Purpose:**
- Demonstrate that capability assignment works through each supported native
  topology, including asymmetric permissions and real Handoff transfer.

**Task Function:**
- Pattern contract and boundary verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: representative operation proof across four native patterns;
  no production redesign unless a contract failure is found.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic fake tool clients prove policy; configured live
  probes remain sanitized and optional when the environment is available.

**Specification Coverage:**
- Verdict sections 8–11 and the fourth recommended increment.
- Prove Sequential + tool, Concurrent + different participant tools, Handoff +
  destination-specific tool, and Group Chat + asymmetric tools; denied calls
  cannot escape participant policy.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/workflow.py:run_recipe_async`, `_run_native_stage`
- Inspect: `evaluation/candidate_harness.py:run_candidate`, `evaluation/run.py:run_live_smoke`
- Modify: `tests/test_orchestration_patterns.py`, `tests/test_runtime_boundaries.py`, `evaluation/task_shapes.json`, `evaluation/candidate_harness.py`, `evaluation/README.md`
- Verify: `docs/intent/maf-capability-decision.md`, a fresh disposable evaluation output root, and preserved `work/` probe outputs without rewriting historical evidence

**Dependencies:**
- Tasks 1–3 complete; capability resolver and factory contracts must be stable.

**Authority:**
- Preauthorized local actions: edit pattern/evaluation tests and contract docs; run deterministic fake-tool proofs and configured live probes that emit metadata only
- Stop for: missing provider credentials, raw model/tool output exposure, unapproved external data, or a pattern failure requiring a change to the approved native MAF contract

**Steps:**
- [x] Step 1: Add an explicit disposable `output_root` parameter to `run_candidate()` and `evaluation/run.py`; never default verification runs to repository `work/` outputs. Capture hashes of preserved `work/case-001/` and `work/case-005/` before and after the proof.
- [x] Step 2: Build deterministic fake capabilities that record invocations, arguments, participant identity, and close events without returning executable instructions.
- [x] Step 3: Prove Sequential uses its assigned tool and passes normalized output to the next participant.
- [x] Step 4: Prove Concurrent participants receive different tool sets, aggregate all branch results/failures, and preserve parallelism and deduplication metrics.
- [x] Step 5: Prove Handoff causes an observed transfer and destination-only capability access; sender-only invocation is denied after transfer.
- [x] Step 6: Prove Group Chat uses asymmetric capabilities and only normalized evidence/context enters the shared conversation.
- [x] Step 7: Run sanitized provider smokes for each applicable pattern and record provider, model, endpoint, status, latency, counters, and cleanup only.

**Verification:**
- [x] `python -m pytest -q tests/test_orchestration_patterns.py tests/test_runtime_boundaries.py`
- [x] Run the contract matrix with a newly allocated temporary `--output-root`, then assert preserved `work/` hashes are unchanged.
- Expected: all four tool-enabled pattern contracts pass offline; live probes are either successful with sanitized metadata or explicitly unavailable without weakening deterministic proof.

**Exit Criteria:**
- Capability policy is enforced at runtime, not only described in prompts or
  tests.
- Pattern support remains `supported/available`; measured quality and latency
  are recorded separately.

### Task 5: Normalize evidence and finish graph-query convergence

**Purpose:**
- Make external and local tool results safe analytical inputs and make graph
  context relationship-correct and bounded.

**Task Function:**
- Evidence-boundary and derived-view convergence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: domain and derived-view correctness with existing tests and
  schemas as the authority.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: domain validation and graph regression tests cover the
  boundary; final verification checks packaged schema ownership.

**Specification Coverage:**
- Verdict sections 12, 18–20, 25, and the fifth recommended increment.
- External output is untrusted evidence content and cannot alter policy;
  invalidation is complete while agent-facing context is bounded with explicit
  per-channel truncation.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/domain/models.py:Evidence`, `AnalysisState`; `src/foresight_os/domain/validation.py`
- Inspect: `src/foresight_os/graph/projection.py:build_graph`, `src/foresight_os/graph/queries.py:get_context`, `get_impacted_records_complete`, `trace_provenance`
- Inspect: `src/foresight_os/persistence/invalidation.py:invalidate_dependencies`
- Modify: `src/foresight_os/domain/models.py`, `src/foresight_os/domain/validation.py`, `src/foresight_os/schemas/analysis.schema.json`, `src/foresight_os/runtime/capabilities.py`, `src/foresight_os/graph/projection.py`, `src/foresight_os/graph/queries.py`
- Add only if needed: `src/foresight_os/domain/evidence.py` for normalization/acceptance helpers, keeping durable validation in the domain layer
- Verify: `tests/test_analysis_schema.py`, `tests/test_graph.py`, `tests/test_invalidation.py`, and focused EvidenceCandidate tests

**Dependencies:**
- Tasks 2–4 provide participant context and normalized tool-result boundaries.
- `src/foresight_os/schemas/` remains the sole editable schema tree.

**Authority:**
- Preauthorized local actions: edit domain, schema, graph, runtime adapter, and focused tests; use synthetic evidence only for deterministic proof
- Stop for: treating provider output as canonical truth, adding a second schema location, or changing persistence revision semantics without an explicit scope update

**Steps:**
- [x] Step 1: Extend the Task 3 `EvidenceCandidate` boundary with acquisition kind, source identity, retrieved timestamp, excerpt/content, source version/date when available, query/context, and limitations; raw tool payloads are not durable by default.
- [x] Step 2: Normalize local/provider/MCP results into candidates, validate provenance and content shape, and require domain acceptance before creating durable `Evidence` or analytical records.
- [x] Step 3: Reject candidate content that attempts to change instructions, capabilities, budgets, permissions, or mutation authority.
- [x] Step 4: Build revision-scoped adjacency indexes for forward/reverse impact, provenance, support, and counterevidence; keep full traversal for invalidation.
- [x] Step 5: Make `get_context(record_id, depth, limit)` bounded from the selected index and return items/paths plus `truncated_provenance`, `truncated_evidence`, `truncated_counterevidence`, and `truncated_impact`.
- [x] Step 6: Add cyclic-graph, relationship-direction, depth-bound, limit-bound, and candidate-rejection regressions.

**Verification:**
- [x] `python -m pytest -q tests/test_analysis_schema.py tests/test_graph.py tests/test_invalidation.py`
- Expected: invalid candidates never become durable evidence; complete invalidation reaches every dependent; bounded context reports each truncation channel accurately.

**Exit Criteria:**
- Tool acquisition mechanism is independent from evidence semantics.
- NetworkX remains rebuildable from durable relationships and is never the
  source of truth.
### Task 6: Add truthful telemetry, evaluation measurements, and documentation convergence

**Purpose:**
- Measure the new runtime without turning measurements into capability policy,
  and align maintained documentation and evaluation records with source truth.

**Task Function:**
- Evaluation, telemetry, and release-readiness convergence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final cross-surface reconciliation and acceptance evidence;
  controller authority is required.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification is the independent validator for this
  plan; no parallel validator is assigned.

**Specification Coverage:**
- Verdict sections 21–22, 26–28, and the sixth recommended increment.
- Metrics distinguish participant invocations, model requests/retries, tool
  calls/failures/latency, branches/parallelism, handoffs, rounds, domain
  failures, provider failures, timeouts, cancellations, cleanup, reuse, and
  human correction.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/metrics.py:RunMetrics`, `src/foresight_os/controller/policy.py:probe_optional_patterns`
- Inspect: `evaluation/run.py`, `evaluation/candidate_harness.py`, `evaluation/README.md`
- Modify: `src/foresight_os/runtime/metrics.py`, `src/foresight_os/controller/policy.py`, `evaluation/run.py`, `evaluation/candidate_harness.py`, `evaluation/task_shapes.json`, `evaluation/README.md`, `docs/intent/maf-capability-decision.md`, `README.md`
- Verify: `tests/test_evaluation_contract.py`, `pyproject.toml`, packaged schemas, current source tree, and all changed tests

**Dependencies:**
- Tasks 1–5 complete; telemetry field names must match runtime behavior and
  evaluation output.

**Authority:**
- Preauthorized local actions: edit evaluation, telemetry, policy, and documentation surfaces; run the full deterministic suite, package smoke, evaluation matrices, and sanitized provider probes
- Stop for: changing capability admission based only on benchmark uplift, recording secrets/raw model content, or modifying unrelated generated outputs

**Steps:**
- [x] Step 1: Remove or rewrite `probe_optional_patterns()` so it reports historical measurements rather than contradicting `PATTERN_CAPABILITIES`; expose support, availability, selection, and measurement separately.
- [x] Step 2: Extend evaluation records with pattern selection, capability selection, tool calls, duplicate retrievals, model calls, latency, parallelism, MCP/resource reuse, human correction, quality, and cleanup; make `run_candidate()` score the selected recipe typed analytical output rather than the earlier vertical-slice state.
- [x] Step 3: Make contract and controller matrices assert expected selections and required support/availability outcomes, and return a nonzero exit code on mismatches; preserve separate support, availability, selection, and measurement statuses.
- [x] Step 4: Run the matrices and representative cases with a fresh disposable `--output-root`; preserve the frozen quality rubric and synthetic fixtures, and fail closed if recipe output cannot be scored instead of silently reusing baseline state.
- [x] Step 5: Update README, capability decision, and evaluation documentation so they describe the same runtime contract and accurately label live-provider limits.
- [x] Step 6: Reconcile tracked, untracked, generated, and preserved probe outputs; do not mark the plan complete until verification evidence matches current `HEAD` and exact workspace state.

**Verification:**
- [x] `python -m pytest -q`
- [x] `python -m compileall -q src tests`
- [x] Run `evaluation/run.py` contract/controller matrices and the case comparison with a newly allocated temporary `--output-root`; assert preserved `work/` hashes are unchanged afterward.
- Expected: deterministic tests and evaluation contracts pass; reports contain no credentials, prompts, raw provider output, or capability-policy contradictions.

**Exit Criteria:**
- Evaluation tunes defaults and budgets but cannot mark a supported pattern
  unsupported.
- Maintained docs, tests, schemas, runtime telemetry, and controller policy
  agree with the implemented contract.

## Verification

Use task-local checks during execution, then run these final artifact checks
before changing this plan from `proposed` to `completed`:

```powershell
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "pytest failed" }
python -m compileall -q src tests
if ($LASTEXITCODE -ne 0) { throw "compileall failed" }
$evaluation_root = Join-Path ([IO.Path]::GetTempPath()) ("foresight-os-evaluation-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $evaluation_root | Out-Null
$preserved_before = @(Get-ChildItem work/case-001,work/case-005 -File -Recurse | Get-FileHash | ForEach-Object { "$($_.Path)=$($_.Hash)" })
python evaluation/run.py --matrix contract --output-root "$evaluation_root"
if ($LASTEXITCODE -ne 0) { throw "contract matrix failed" }
python evaluation/run.py --matrix controller --output-root "$evaluation_root"
if ($LASTEXITCODE -ne 0) { throw "controller matrix failed" }
python evaluation/run.py --case evaluation/cases/case-001 --compare ordinary,semantic,sequential,controller --output-root "$evaluation_root"
if ($LASTEXITCODE -ne 0) { throw "case evaluation failed" }
$preserved_after = @(Get-ChildItem work/case-001,work/case-005 -File -Recurse | Get-FileHash | ForEach-Object { "$($_.Path)=$($_.Hash)" })
if ((Compare-Object $preserved_before $preserved_after)) { throw "preserved probe outputs changed" }
$verify_root = Join-Path ([IO.Path]::GetTempPath()) ("foresight-os-capability-wheel-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $verify_root | Out-Null
$snapshot_root = Join-Path ([IO.Path]::GetTempPath()) ("foresight-os-source-snapshot-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $snapshot_root | Out-Null
robocopy . "$snapshot_root" /E /XD .git build work .pytest_cache .serena .tmp-tests src\foresight_os.egg-info /XF .env | Out-Null
if ($LASTEXITCODE -gt 7) { throw "source snapshot failed" }
Push-Location $snapshot_root
python -m build --no-isolation --wheel --outdir "$verify_root/wheel"
if ($LASTEXITCODE -ne 0) { throw "wheel build failed" }
$wheels = @(Get-ChildItem "$verify_root/wheel/*.whl")
if ($wheels.Count -ne 1) { throw "expected exactly one newly built wheel" }
Pop-Location
python -m pip install --no-deps --target "$verify_root/install" $wheels[0].FullName
if ($LASTEXITCODE -ne 0) { throw "wheel install failed" }
Push-Location "$verify_root/install"
python -c "import json, importlib.resources as r, foresight_os; from agent_framework.orchestrations import SequentialBuilder, ConcurrentBuilder, HandoffBuilder, GroupChatBuilder; from foresight_os.runtime.orchestration import run_recipe_async; assert str(foresight_os.__file__).startswith(str(__import__('pathlib').Path.cwd())); json.loads(r.files(foresight_os).joinpath('schemas/analysis.schema.json').read_text()); json.loads(r.files(foresight_os).joinpath('schemas/work_brief.schema.json').read_text()); print(foresight_os.__file__)"
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "installed-package smoke failed" }
Pop-Location
Remove-Item -LiteralPath $evaluation_root -Recurse -Force
Remove-Item -LiteralPath $snapshot_root -Recurse -Force
Remove-Item -LiteralPath $verify_root -Recurse -Force
git diff --check
if ($LASTEXITCODE -ne 0) { throw "git diff --check failed" }
```

Also inspect one accepted report, one provisional report, one fresh-process
pending-review recovery, one cross-process writer race, one cyclic graph with
bounded context, one deterministic task-shaped evaluation report, and one
sanitized live-provider smoke per native tool-enabled pattern when the
configured provider boundary is available. Record only sanitized metadata.

`skill-backend-verification` must prove the runtime through direct boundaries,
important failure paths, final metrics/resource state, and cleanup behavior;
fake tools may prove policy but do not replace configured real-dependency proof
when a live provider or MCP capability is part of the claimed outcome.

`skill-verification-before-completion` must return `verified` against current
`HEAD` and exact staged, unstaged, and untracked in-scope state, with no
unexplained out-of-scope changes, before the lead controller changes plan
status. Existing untracked `build/`, `src/foresight_os.egg-info/`, and `work/`
probe outputs remain preserved unless separately authorized for cleanup.

## Completion Criteria

The plan is ready for completion verification when:

1. Runtime limits are enforced before dispatch and failure metrics remain
   observable for provider, tool, domain, timeout, cancellation, budget, and
   cleanup outcomes.
2. Direct and native participants use one factory, profiles affect supported
   construction settings, and broad compatibility fallbacks are removed.
3. Work stages express ordering and review responsibility independently from
   pattern topology; recipes remain declarative and bounded.
4. Semantic capabilities resolve lazily with native-first order, participant
   scoping, Handoff non-inheritance, run-local reuse, and explicit unavailable
   or denied results.
5. Sequential, Concurrent, Handoff, and Group Chat tool-enabled contracts are
   proven, including real Handoff transfer and denied-tool enforcement.
6. Tool results pass through validated, provenance-bearing `EvidenceCandidate`
   objects and cannot change policy, permissions, budgets, or durable claims.
7. Graph indexes are revision-scoped and relationship-aware; invalidation is
   complete, context is bounded, and truncation metadata is per channel.
8. Evaluation distinguishes support, availability, selection, and measurement
   and records requested quality, cost, latency, reuse, correction, and cleanup
   dimensions without changing capability admission.
9. Documentation, schemas, tests, package resources, and evaluation reports
   agree with source; `src/foresight_os/schemas/` is the sole editable schema
   tree.
10. Final verification returns `verified`; approved deferrals and residual
    risks are recorded, and no required task or blocker remains open.

Approved deferrals for this delivery are a generic routing service, a general
DAG/planner engine, persistent semantic caching, broad role catalogs, remote
service hosting, autonomous monitoring, and external mutation capabilities
without an explicit human-authorized boundary.


