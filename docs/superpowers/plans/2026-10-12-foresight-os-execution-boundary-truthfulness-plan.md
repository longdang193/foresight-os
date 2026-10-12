---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: foresight-os-execution-boundary-truthfulness
targets:
  - src/foresight_os/runtime/
  - src/foresight_os/controller/
  - src/foresight_os/domain/
  - src/foresight_os/persistence/
  - src/foresight_os/graph/
  - evaluation/probes/
  - tests/
  - .github/workflows/
  - docs/intent/
  - README.md
  - pyproject.toml
related_features:
  - truthful capability binding
  - run-scoped lifecycle ownership
  - policy-enforced tool execution
  - real web and MCP evidence
  - anomaly and soak detection
related_stages:
  - post-846f4ed capability-routed runtime correctness pass
---

# Foresight OS Execution-Boundary Truthfulness

## Verdict Review

**Decision: approve the architecture; narrow the next delivery to runtime
correctness and integration proof.** At commit `846f4ed6f58e095b2294f5f94f075595cdc8fc30`,
the durable architecture is sufficient: Work Briefs produce ordered stages,
the Controller produces declarative recipes, the shared factory constructs
participants, capabilities are semantically named, MAF owns orchestration,
EvidenceCandidate protects the domain boundary, persistence owns revisions, and
NetworkX remains derived.

The verdict correctly identifies two P0 defects and several unproven claims:

- `CapabilityResolver` treats every callable as a factory, so a callable tool
  executes during resolution instead of being passed to MAF.
- Successful Direct execution does not have one unambiguous ownership path for
  all agents, tools, and resources, so cleanup can be skipped or ambiguous.
- Current tool-enabled tests prove assignment, not a real model → tool →
  tool-result → model cycle.
- `data_scope`, `max_parallelism`, Handoff permissions, actual-call budgets,
  run-cache identity, and stage-derived capability assignment are modeled but
  not fully enforced at the invocation boundary.
- Persistence race/restart behavior, exact graph traversal bounds, disposable
  MCP behavior, real read-only web/MCP behavior, live transfer, and resource
  anomalies need direct evidence rather than source-level confidence.

The plan therefore does not add another orchestration layer, routing service,
general DAG engine, persistent semantic cache, broad role catalog, or external
mutation capability. It makes the current boundaries executable and observable.

## Goal

Make the existing capability-routed runtime truthful at execution boundaries:

```text
Work Brief / Work Stages
  → Controller-selected declarative recipe
  → explicit capability binding
  → shared factory
  → MAF model/tool execution
  → instrumented typed result
  → EvidenceCandidate for external factual retrieval, or a typed local
    calculation/context/validation result
  → domain validation and durable persistence
```

The delivery must prove, with fresh evidence, that capabilities are bound
without side effects, authorized at invocation time, limited by real calls and
parallelism, measured where they execute, cleaned up under every terminal
condition, and converted into validated domain inputs before affecting
`AnalysisState`.

## Implementation Outcomes

### Truthful runtime boundaries

Capability binding distinguishes tools, synchronous factories, and
resource-producing factories; one run-owned scope registers and closes every
owned participant, agent, tool, and session exactly once while borrowed
resources remain borrowed. Authorization, hard limits, and cleanup outcomes are
visible at the invocation boundary without masking the primary result.

### Typed execution and durable state

MAF-driven model/tool cycles preserve participant identity, tool provenance, and
typed results. External factual retrieval becomes validated `EvidenceCandidate`
data, while calculations, graph context, and validation remain their native
typed results. Persistence recovery, invalidation, and derived graph context
remain revision-safe and bounded.

### Integration and release proof

Disposable MCP, real read-only MCP, provider-hosted web, live native-pattern,
and anomaly probes report independently sanitized outcomes. Deterministic CI
proves implementation behavior without credentials, while external integration
readiness is reported separately as verified or explicitly blocked.

## Non-goals and approved deferrals

- No new orchestration engine, scheduler, routing service, or general planner.
- No persistent semantic cache; reuse remains run-scoped and authorization-aware.
- No broad role catalog or agent subclasses for web, MCP, or patterns.
- No remote service hosting or autonomous monitoring.
- No external mutation capability without an explicit human approval boundary.
- No live credentials, prompts, raw provider output, or external source payloads
  in tracked files, CI logs, metrics, or reports.

## Invariants

- `TOOL`, `FACTORY`, and `RESOURCE_FACTORY` are explicit binding kinds; Python
  callability never determines lifecycle semantics.
- `TOOL` resolution never invokes the tool; `FACTORY` construction is
  synchronous; `RESOURCE_FACTORY` may acquire a synchronous or asynchronous,
  context-managed resource. An awaitable is rejected only when its declared
  binding kind does not permit one.
- Borrowed resources are never closed by the run; owned resources are always
  registered with the run scope and closed after primary settlement.
- A run creates and owns a `CapabilityScope` when the caller supplies none. A
  supplied scope must declare whether it is run-owned or borrowed; only the
  run-owned scope closes participants, agents, MCP sessions, and run-owned tools.
  `RunScope`/`CapabilityScope` is the sole lifecycle owner; workflow helpers do
  not perform a second cleanup pass.
- Primary failure and cleanup failure are recorded separately. Cleanup failure
  never hides the original provider, tool, timeout, cancellation, budget, or
  domain failure.
- Authorization is `participant + capability + data scope + access mode +
  approval state`, and denial occurs before invocation.
- Stage dispatches, participant turns, tool calls, handoffs, group-chat rounds,
  parallelism, and deadlines are hard-enforced when the runtime can observe
  them. Provider-request, token, and similar provider telemetry is observational
  unless a trustworthy provider hook makes it enforceable; unknown values remain
  `unknown` and are never inferred from participant count.
- Controller measurements never change pattern support or capability admission.
- NetworkX is rebuildable derived state; persistence remains the revision-safe
  source of truth.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Executor: `codex`
- Isolation: `current workspace`; do not overwrite preserved `build/`, egg-info,
  or `work/` outputs.
- Required skills: `skill-executing-plans`, `skill-backend-verification`,
  `skill-systematic-debugging` for failed probes, and
  `skill-verification-before-completion`.
- Commit policy: no commits during implementation; commit/push requires a later
  explicit user authorization.
- External boundary policy: disposable MCP and configured real web/MCP probes
  are allowed only through explicit environment-gated commands; absent approved
  configuration is a blocked integration-proof condition, not a passing result.
  Report `implementation_verified` separately from
  `external_integration_verified`/`BLOCKED_EXTERNAL`.
- Parallel ownership: none; runtime, Controller, persistence, graph, probes,
  and CI contracts share telemetry and lifecycle semantics.
- Execution order: Tasks 1–8 sequentially.

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `846f4ed6f58e095b2294f5f94f075595cdc8fc30`
- Expected workspace: `main` at the base commit plus preserved untracked probe
  outputs; do not clean or overwrite them.
- Next action: `implementation verified; offer branch finishing only after explicit Git authorization`
- Blockers: `real MCP and hosted-web provider configuration remain BLOCKED_EXTERNAL`

| Task | State | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- |
| Task 1 | `verified` | `codex` | none | binding-kind, scope, cleanup, and failure-boundary tests | focused runtime tests and full suite passed |
| Task 2 | `verified` | `codex` | Task 1 | authorization, concurrency, cache, budget, and telemetry tests | focused boundary/controller tests and full suite passed |
| Task 3 | `verified` | `codex` | Task 2 | stage-derived capability and explicit Handoff topology tests | Controller matrix accuracy `1.0` |
| Task 4 | `verified` | `codex` | Tasks 1–3 | actual model/tool cycles across native patterns | deterministic tool-cycle suite passed |
| Task 5 | `verified` | `codex` | Tasks 1–4 | persistence race/restart and exact graph fixtures | persistence/recovery/invalidation/graph tests passed |
| Task 6 | `verified-with-external-blockers` | `codex` | Tasks 1–5 | disposable MCP, real MCP, and configured provider-hosted web probes | disposable MCP `verified`; real MCP and hosted web `BLOCKED_EXTERNAL` |
| Task 7 | `verified` | `codex` | Tasks 1–6 | live native patterns and 100-run anomaly/soak probe | all five live patterns passed; Handoff observed `1`; anomaly `verified` |
| Task 8 | `verified` | `codex` | Tasks 1–7 | deterministic CI workflow, package smoke, and final verification | final sweep, wheel/import/schema smoke, and diff check passed |

## Task Breakdown

### Task 1: Make capability bindings and lifecycle ownership explicit

**Purpose:**
- Fix the P0 callable-tool resolution bug and make cleanup ownership
  unambiguous before introducing real MCP or web tools.

**Task Function:**
- Runtime binding and lifecycle convergence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded local runtime change with direct boundary tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused lifecycle and failure-boundary tests are sufficient.

**Specification Coverage:**
- Binding-kind semantics, explicit ownership, one cleanup owner, and primary
  versus cleanup failure separation.

**Required Skills:**
- `skill-backend-verification`

**Dependencies:**
- Base commit `846f4ed6f58e095b2294f5f94f075595cdc8fc30`; preserve current MAF
  and all untracked probe outputs.

**Authority:**
- Preauthorized local actions: edit listed runtime files and focused tests; run focused pytest and compile checks
- Stop for: dependency installation, provider/authentication changes, or modification of preserved untracked outputs

**Files and symbols:**
- Modify `src/foresight_os/runtime/capabilities.py:CapabilityScope`,
  `CapabilityResolver`, and `CapabilityDefinition`.
- Modify `src/foresight_os/runtime/participants.py:AgentFactory`.
- Modify `src/foresight_os/runtime/executors.py:AnalystExecutor` and
  `ReviewerExecutor`.
- Modify `src/foresight_os/runtime/workflow.py:run_recipe_async`,
  `_run_native_stage`; remove direct lifecycle ownership from `_close_agents`,
  or retain it only as a scope-internal helper.
- Modify `src/foresight_os/runtime/metrics.py:RunMetrics`, `RunResult`, and
  failure/cleanup fields.
- Add or extend `tests/test_capabilities.py` and
  `tests/test_runtime_boundaries.py`.

**Steps:**
- [ ] Add `CapabilityBindingKind` with `TOOL`, `FACTORY`, and
  `RESOURCE_FACTORY`, plus a binding record carrying the value, ownership,
  share scope, data scope, max parallelism, and stable configuration
  fingerprint.
- [ ] Make `TOOL` resolution return the callable unchanged without invoking it;
  keep `FACTORY` construction synchronous; allow `RESOURCE_FACTORY` to acquire
  synchronous or asynchronous/context-managed resources. Reject an awaitable
  only when its declared binding kind does not permit one.
- [ ] Extend `CapabilityScope`/`RunScope` to register each owned resource and
  agent once while leaving borrowed resources unregistered. Reuse a supplied
  scope only when its ownership is explicit, create one when absent, and make
  that scope the sole cleanup owner on success and every failure path.
- [ ] Settle primary outcome before cleanup, retain both primary and cleanup
  failure metadata, attempt every owned close operation, and preserve the
  original exception when both primary and cleanup fail.
- [ ] Route Direct, Sequential, Concurrent, Handoff, and Group Chat agents
  through the same factory/scope path; remove any path that can return before
  owned agents or resources are registered for cleanup.

**Verification:**
- [ ] `python -m pytest -q tests/test_capabilities.py tests/test_runtime_boundaries.py tests/test_orchestration_patterns.py`
- [ ] Add tests proving a callable tool is not called during resolution and an
  owned resource closes on success, provider failure, timeout, cancellation,
  budget rejection, domain rejection, and cleanup failure. Cover synchronous
  and asynchronous resource factories, borrowed resources, shared bindings,
  and the invariant that no workflow-level helper closes an owned resource a
  second time.

**Exit criteria:**
- Resolution has no side effects for `TOOL` bindings.
- Every run has one observable ownership scope and cleanup metrics are truthful.

### Task 2: Enforce authorization, concurrency, reuse, budgets, and telemetry

**Purpose:**
- Turn modeled policy fields into invocation-boundary enforcement and make
  metrics reflect actual provider/tool behavior.

**Task Function:**
- Invocation policy and telemetry enforcement.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded policy change with deterministic runtime tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: authorization, budget, semaphore, and metric assertions cover
  the required boundary behavior.

**Specification Coverage:**
- Data scope, access mode, approval, cache identity, hard budgets, and truthful
  provider telemetry.

**Required Skills:**
- `skill-backend-verification`

**Dependencies:**
- Task 1 complete; use its binding and scope contract rather than adding a
  second enforcement path.

**Authority:**
- Preauthorized local actions: edit listed runtime/controller files and focused tests; run deterministic boundary checks
- Stop for: provider API changes, credential/authentication work, or scope expansion beyond invocation policy

**Files and symbols:**
- Modify `src/foresight_os/runtime/capabilities.py` and
  `src/foresight_os/runtime/participants.py`.
- Modify `src/foresight_os/runtime/workflow.py` and
  `src/foresight_os/runtime/metrics.py`.
- Modify `src/foresight_os/controller/recipes.py:RecipeStage` and
  `src/foresight_os/controller/budgets.py:BudgetState`.
- Add or extend `tests/test_tool_enabled_patterns.py` and
  `tests/test_runtime_boundaries.py`.

**Steps:**
- [ ] Apply participant `data_scope`, capability access mode, approval policy,
  and optional trusted-pre-resolved tools through one authorization function;
  reject public-scope participants requesting internal capabilities before
  MAF agent creation or tool invocation.
- [ ] Wrap bound tools at the tool boundary with a run-local semaphore and
  instrumentation. Enforce `CapabilityDefinition.max_parallelism` across
  concurrent participants and record tool calls, failures, latency, and
  capability reuse exactly once per actual call.
- [ ] Replace cache keys based only on capability ID with a deterministic key
  containing capability ID, binding fingerprint, authorization/data scope,
  session identity, and freshness/search policy. Keep all cache state run-local.
- [ ] Make hard-observable stage dispatches, participant turns, tool calls,
  parallelism, handoffs, group-chat rounds, and deadlines consume recipe
  budgets; reject the next dispatch before it would exceed the corresponding
  existing limit fields such as `max_total_agent_calls`, `max_tool_calls`,
  `max_parallelism`, `max_handoffs`, or `max_group_chat_rounds`.
- [ ] Treat provider-request, input-token, and output-token counts as
  observational unless the configured provider exposes a trustworthy request
  hook. Enforce a provider-request budget only with that hook; otherwise record
  `provider_requests=unknown` and never substitute executor or participant
  counts.
- [ ] Keep participant invocation, provider request, tool invocation, retry,
  handoff, round, cleanup, and reuse metrics distinct and settled on failure.

**Verification:**
- [ ] `python -m pytest -q tests/test_tool_enabled_patterns.py tests/test_runtime_boundaries.py tests/test_controller_selection.py`
- [ ] Add deterministic tests for data-scope denial, denied participant tools,
  semaphore limits, cache identity changes, and every forbidden next dispatch.
  Include assertions that hard budgets stop before forbidden dispatch and that
  unsupported provider telemetry is reported as `unknown`.

**Exit criteria:**
- No hard-observable authorization, concurrency, or call limit is prompt-only;
  unsupported provider telemetry is explicitly observational.
- Metrics report actual execution events rather than topology estimates.

### Task 3: Make Controller capability assignment and stage order real

**Purpose:**
- Complete the Work Stage → Controller path without creating hard-coded agent
  subclasses or a second planner.

**Task Function:**
- Declarative Controller policy convergence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: local recipe and policy edits with existing matrix coverage.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: Controller and schema tests prove ordered capability and
  topology contracts.

**Specification Coverage:**
- Stage-derived capability assignment, ordered dependencies, independent review,
  bounded Handoff destinations, and removal of obsolete admission vocabulary.

**Required Skills:**
- `skill-backend-verification`

**Dependencies:**
- Task 2 complete; retain Work Brief compatibility and the declarative recipe
  boundary.

**Authority:**
- Preauthorized local actions: edit listed Controller/domain/evaluation files and focused tests; run matrix checks
- Stop for: new orchestration/planner architecture, provider integration, or changes to preserved probe outputs

**Files and symbols:**
- Modify `src/foresight_os/wayfinding.py:create_work_brief` and
  `src/foresight_os/domain/models.py:WorkStage`.
- Reuse `src/foresight_os/runtime/participants.py:ParticipantConfig` as the
  runtime participant contract; do not move it into the domain model.
- Modify `src/foresight_os/controller/policy.py:select_recipe` and
  `_recipe_for_patterns`.
- Modify `src/foresight_os/controller/recipes.py:RecipeStage` and
  `ExecutionRecipe`.
- Modify `evaluation/task_shapes.json`, `evaluation/run.py`, and
  `tests/test_controller_selection.py`.

**Steps:**
- [ ] Define the supported research-need to capability mapping in one small
  Controller policy table, including `web_search`, `page_retrieval`,
  `graph_context`, `calculation`, and `domain_validation`; unknown needs must
  produce an explicit unresolved capability decision rather than a guessed
  tool.
- [ ] Derive participant capability IDs, data scope, and limits from each
  WorkStage objective, research need, and participant role. Keep recipe data
  declarative and free of provider, MAF, MCP, or credential objects.
- [ ] Preserve WorkStage list order and dependency validation when creating
  recipe stages. Use TaskShape only as structural input; do not reorder stages
  by a fixed pattern list.
- [ ] Represent review responsibility separately from topology and enforce
  review participants on the stage that owns review, regardless of whether the
  selected topology is Sequential, Concurrent, Handoff, or Group Chat.
- [ ] Add explicit Handoff destination constraints to the recipe and reject
  sender-only capability inheritance, all-to-all destinations, and handoff
  loops before native builder creation.
- [ ] Remove or rewrite the obsolete `production_admitted`, `admitted_pattern`,
  and `probe_optional_patterns` vocabulary in Controller/evaluation outputs;
  update their consumers and tests while preserving supported-pattern
  availability. Expose only support, availability, selection, measurement,
  contract-pass, and quality-pass states.

**Verification:**
- [ ] `python -m pytest -q tests/test_controller_selection.py tests/test_analysis_schema.py`
- [ ] Add tests for research-need capability assignment, ordered mixed stages,
  non-Sequential review, bounded Handoff destinations, unknown needs, and
  legacy Work Brief compatibility.

**Exit criteria:**
- A Work Brief demonstrably determines stage order and minimum capabilities.
- Role, profile, capability, data scope, and pattern remain independent.

### Task 4: Prove real model → tool → result → model cycles

**Purpose:**
- Replace assignment-only tests with deterministic execution-boundary proof.

**Task Function:**
- MAF tool-cycle contract verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: focused fake-boundary integration tests with no live service.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: exact event assertions and pattern coverage provide the proof.

**Specification Coverage:**
- Actual model-request/tool-dispatch/result/model cycles, typed result
  normalization, authority-injection rejection, and cleanup.

**Required Skills:**
- `skill-backend-verification`

**Dependencies:**
- Tasks 1–3 complete; use the real runtime/MAF tool-call path and its scope.

**Authority:**
- Preauthorized local actions: add or edit focused runtime/domain test fixtures and run deterministic cycle checks
- Stop for: live credentials, protocol emulation outside the configured MAF boundary, or mutation-capable tools

**Files and symbols:**
- Modify `src/foresight_os/runtime/participants.py`,
  `src/foresight_os/runtime/workflow.py`,
  `src/foresight_os/domain/evidence.py`, and
  `src/foresight_os/domain/models.py:CalculationRecord`.
- Add `tests/test_tool_cycles.py` and extend
  `tests/test_tool_enabled_patterns.py`.

**Steps:**
- [ ] Build a deterministic fake MAF client/model that emits a tool-call event,
  requests the assigned tool through the actual MAF tool-call protocol, lets
  MAF/runtime invoke the bound instrumented callable, receives the normalized
  typed result, and then emits a final typed model result. The test harness
  must never invoke the tool directly or bypass the factory.
- [ ] Run the cycle through Direct, Sequential, Concurrent, Handoff, and Group
  Chat recipes with distinct participant capability sets. Assert the actual tool
  invocation order, participant identity, result handoff, and final output.
- [ ] Normalize external factual retrieval (web, page, MCP, database, or
  document retrieval) into `EvidenceCandidate` with source, capability ID,
  request, retrieval timestamp, query/context, limitations, and raw payload
  retained only in transient test memory. Keep deterministic calculation,
  graph-context, and domain-validation results as the existing
  `CalculationRecord` or other typed context/validation/proposal results
  instead of manufacturing evidence.
- [ ] Assert candidate validation rejects instruction, permission, budget,
  capability, and external-mutation authority injection before durable domain
  acceptance.
- [ ] Prove sender-only tools are unavailable after Handoff and that Group Chat
  shared context contains normalized evidence or typed local results rather than
  raw tool payloads.

**Verification:**
- [ ] `python -m pytest -q tests/test_tool_cycles.py tests/test_tool_enabled_patterns.py tests/test_evidence_candidates.py`
- [ ] Require exact event assertions for model requests, tool calls, tool
  failures, normalized candidates, and cleanup.

**Exit criteria:**
- At least one test for each native pattern executes a real callable tool during
  the model interaction rather than merely inspecting assigned tools.

### Task 5: Prove persistence races, restart recovery, and graph correctness

**Purpose:**
- Confirm that truthful runtime output reaches revision-safe durable state and
  bounded derived context without stale or duplicate records.

**Task Function:**
- Persistence, recovery, invalidation, and graph-boundary verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded local race/restart fixtures and exact-set graph tests.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: fresh-process and bounded-work probes provide independent
  evidence for the durable boundary.

**Specification Coverage:**
- Revision conflicts, fresh-process `AnalysisState` recovery, compatible
  checkpoint resumption, complete invalidation, and bounded graph work.

**Required Skills:**
- `skill-backend-verification`

**Dependencies:**
- Tasks 1–4 complete; persistence remains the source of truth and NetworkX
  remains derived.

**Authority:**
- Preauthorized local actions: edit listed persistence/graph files and focused tests; run process and graph probes
- Stop for: destructive data migration, deletion of preserved outputs, or new persistent cache/state architecture

**Files and symbols:**
- Modify `src/foresight_os/persistence/analysis_store.py`,
  `src/foresight_os/persistence/recovery.py:continue_investigation`,
  `resume_checkpoint`, and
  `src/foresight_os/persistence/invalidation.py` only where current contracts
  fail the probes.
- Modify `src/foresight_os/graph/projection.py` and
  `src/foresight_os/graph/queries.py` for exact index/bound behavior.
- Add or extend `tests/test_persistence.py`, `tests/test_recovery.py`,
  `tests/test_invalidation.py`, and `tests/test_graph.py`.

**Steps:**
- [ ] Run two independent processes against the same revision and assert
  exactly one commit succeeds, the loser receives a revision conflict, and no
  duplicate durable records or artifacts are created.
- [ ] Terminate a `PENDING_REVIEW` flow before acceptance, restart in a fresh
  process from persisted `AnalysisState` without requiring a runtime
  checkpoint, and assert the same draft, revision, evidence IDs, and pending
  status are restored. Separately resume a compatible interrupted execution
  from an MAF checkpoint and prove that checkpoint recovery is not required for
  durable human-review recovery.
- [ ] Update one evidence record and assert the exact reassessment set and exact
  stale-artifact set, including reverse and cyclic dependency paths.
- [ ] Build hand-authored SUPPORTS, CONTRADICTS, DERIVED_FROM, and DEPENDS_ON
  fixtures with cycles and large fan-out. Compare full invalidation against
  bounded `get_context` results and assert every truncation channel. Measure
  edge visits/query work, or make complete traversal unavailable in the bounded
  test, so bounded context cannot secretly build the full graph first; require
  work proportional to the requested neighborhood.
- [ ] Verify graph indexes rebuild from durable relationships at a revision and
  are never required as the persistence source of truth.

**Verification:**
- [ ] `python -m pytest -q tests/test_persistence.py tests/test_recovery.py tests/test_invalidation.py tests/test_graph.py`
- [ ] Add exact-set assertions for race outcome, restored draft, invalidation,
  provenance, counterevidence, and bounded context.

**Exit criteria:**
- Persistence and graph probes show no duplicate commit, stale recovery, or
  incomplete correctness-critical invalidation, and bounded context work is
  proportional to the requested neighborhood rather than the full graph.

### Task 6: Add disposable MCP, real MCP, and hosted-web probes

**Purpose:**
- Prove three independent boundaries: a deterministic disposable MCP fixture,
  one approved real read-only MCP query, and one provider-hosted web query when
  the configured provider supports hosted search.

**Task Function:**
- External integration boundary verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: disposable proof is local; live proofs are isolated and
  environment-gated.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: sanitized probe reports and contract tests provide the
  required boundary evidence.

**Specification Coverage:**
- MCP lifecycle, read-only authorization, hosted-web event truthfulness,
  evidence provenance, persistence handoff, and cleanup.

**Required Skills:**
- `skill-backend-verification`

**Dependencies:**
- Tasks 1–5 complete; retrieved evidence must pass the durable persistence and
  derived-graph boundary before this task is complete.

**Authority:**
- Preauthorized local actions: add disposable fixtures and run explicitly configured read-only probes
- Stop for: credential or endpoint changes, missing approved external configuration, mutation-capable tools, or raw payload exposure

**Files and symbols:**
- Add `evaluation/probes/disposable_mcp_server.py` with deterministic tools,
  delay, connection-loss, and close behavior.
- Add `evaluation/probes/run_mcp_probe.py` with independently reported
  `--mode disposable` and `--mode real-mcp` results.
- Add `evaluation/probes/real_read_probe.py` using the existing provider/config
  boundary and the explicit MCP adapter contract.
- Add `evaluation/probes/real_web_probe.py` using the existing provider boundary
  and hosted-search event/result contract.
- Modify `src/foresight_os/runtime/capabilities.py` and
  `src/foresight_os/domain/evidence.py` only for the adapter/binding path.
- Add `tests/test_mcp_probe_contract.py`.

**Steps:**
- [ ] Implement the disposable MCP server with the official MCP SDK or a
  MAF-supported server utility when available; add an optional test/MCP
  dependency only if the repository has no supported utility. Cover
  deterministic timeout, connection-loss, malformed-result, and close cases
  without making Foresight OS own a second wire-protocol implementation.
- [ ] Bind MCP tools as explicit `TOOL` or `RESOURCE_FACTORY` capabilities;
  discover tools without invoking them, invoke only after authorization, and
  close owned sessions through `CapabilityScope`.
- [ ] **6A — Disposable MCP:** run the local fixture and assert source
  identity, discovery, actual invocation through the runtime, normalized
  `EvidenceCandidate`, timeout and connection-loss classifications, cleanup,
  and no raw payload in the report.
- [ ] **6B — Real MCP:** define the boundary with
  `FORESIGHT_REAL_MCP_URL`, `FORESIGHT_REAL_MCP_TOKEN`, and
  `FORESIGHT_REAL_MCP_QUERY`. Read the token only from the environment, redact
  it from output, refuse mutation-capable tools, and record only endpoint host,
  source identity, retrieval timestamp, candidate metadata, tool metrics,
  cleanup, and sanitized status. Missing configuration is `BLOCKED_EXTERNAL`,
  not a successful real probe.
- [ ] **6C — Provider-hosted web:** use the existing provider configuration and
  `FORESIGHT_REAL_WEB_QUERY` only when that provider advertises hosted search.
  Require an actual hosted-search event/result and `EvidenceCandidate`
  provenance; an MCP success cannot satisfy this proof. Unsupported provider
  capability is `BLOCKED_EXTERNAL`, not a fake pass.
- [ ] Exercise each retrieved candidate through the Task 5 persistence and
  derived-graph boundary before reporting the corresponding proof complete.

**Verification:**
- [ ] `python evaluation/probes/run_mcp_probe.py --mode disposable`
- [ ] `python -m pytest -q tests/test_mcp_probe_contract.py tests/test_evidence_candidates.py`
- [ ] `python evaluation/probes/run_mcp_probe.py --mode real-mcp` with approved
  environment configuration; assert no token, prompt, header, or raw result is
  emitted.
- [ ] `python evaluation/probes/real_web_probe.py` with a provider that supports
  hosted search; assert the actual hosted-search event/result and sanitized
  provenance, or record `BLOCKED_EXTERNAL` with the provider limitation.

**Exit criteria:**
- Disposable MCP proof is deterministic and green.
- Real MCP and hosted-web proofs are reported independently, each with an
  actual invocation and validated evidence, or each remains explicitly
  `BLOCKED_EXTERNAL` with its exact missing environment boundary recorded.

### Task 7: Prove live native patterns and detect resource anomalies

**Purpose:**
- Confirm the runtime behaves under configured provider execution and repeated
  fault-injected runs without leaks, drift, or false metrics.

**Task Function:**
- Live-pattern and anomaly-probe verification.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic local soak plus environment-gated provider
  smoke checks.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: fixed-seed measurements and sanitized live event reports are
  the required validation evidence.

**Specification Coverage:**
- Native-pattern execution truthfulness, observed Handoff transfer, resource
  stability, metric stability, and platform-aware anomaly classification.

**Required Skills:**
- `skill-backend-verification`

**Dependencies:**
- Tasks 1–6 complete; keep live-provider failures separate from deterministic
  implementation results.

**Authority:**
- Preauthorized local actions: add anomaly probes, edit probe documentation, and run fixed-seed checks
- Stop for: credential/authentication changes, external mutation, or unbounded load/resource collection

**Files and symbols:**
- Add `evaluation/probes/run_anomaly_probe.py`.
- Add or extend `tests/test_anomaly_probe.py` and
  `tests/test_orchestration_patterns.py`.
- Update `evaluation/README.md` and `docs/intent/maf-capability-decision.md`
  with sanitized probe-tier rules and residual limits.

**Steps:**
- [ ] Run one bounded live integration for Direct, Sequential, Concurrent,
  Handoff, and Group Chat through the configured provider. Require an observed
  Handoff transfer event rather than treating a successful topology as transfer
  proof.
- [ ] Record exact participant invocations, provider requests when observable,
  tool calls/failures/latency, handoffs, chat rounds, parallelism, reuse,
  execution time, primary failure, and cleanup outcome.
- [ ] Run `100` deterministic/fault-injected repetitions with a fixed seed and
  state hash after a fixed warmup of `10` runs. Sample at explicit checkpoints
  before and after each measured run: owned-resource count, open files/sockets,
  child process count, unfinished asyncio tasks, memory trend, metric drift,
  and failure classification using the platform resource adapter. Force
  collection before memory samples where supported.
- [ ] Fail the probe on monotonic resource accumulation, unexplained state/hash
  divergence, orphaned tasks, or metric drift; keep environment-gated provider
  failures distinct from deterministic test failures. Unavailable OS counters
  are reported as unavailable rather than zero or automatic failures, and
  memory acceptance detects unbounded trend beyond a documented tolerance rather
  than requiring identical allocator values.

**Verification:**
- [ ] `python evaluation/probes/run_anomaly_probe.py --runs 100 --seed 846f4ed`
- [ ] `python evaluation/run.py --live-smoke --pattern direct`
- [ ] `python evaluation/run.py --live-smoke --pattern sequential`
- [ ] `python evaluation/run.py --live-smoke --pattern concurrent`
- [ ] `python evaluation/run.py --live-smoke --pattern handoff`
- [ ] `python evaluation/run.py --live-smoke --pattern group_chat`

**Exit criteria:**
- Live provider outcomes are sanitized and truthful, and the 100-run probe
  shows no monotonic resource or state anomaly.

### Task 8: Add deterministic CI and complete release verification

**Purpose:**
- Make the deterministic contract repeatable on GitHub without requiring live
  credentials, while keeping expensive probes environment-gated.

**Task Function:**
- Release verification and CI contract completion.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic packaging and repository-integrity checks.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification skill owns the completion decision.

**Specification Coverage:**
- Credential-free CI, clean wheel installation, package resources, sanitized
  evidence, implementation/external status separation, and repository hygiene.

**Required Skills:**
- `skill-verification-before-completion`

**Dependencies:**
- Tasks 1–7 complete; all required proof must be fresh or explicitly blocked.

**Authority:**
- Preauthorized local actions: add CI/docs/package-test configuration and run deterministic release checks
- Stop for: commit/push, publication, secret handling, destructive cleanup, or unresolved scope changes

**Files and symbols:**
- Add `.github/workflows/ci.yml`.
- Modify `README.md`, `evaluation/README.md`, and
  `docs/intent/maf-capability-decision.md`.
- Modify `pyproject.toml` only for explicitly required probe/test extras; keep
  live credentials and endpoints out of package metadata.

**Steps:**
- [ ] Add one deterministic GitHub Actions workflow that runs `pytest`,
  `compileall`, wheel build, clean wheel-install package/schema smoke, contract
  matrix, Controller matrix, and `git diff --check` without external provider
  credentials.
- [ ] Document probe tiers: deterministic PR checks, nightly disposable-MCP
  and anomaly checks, and environment-gated real web/MCP/live-pattern checks.
- [ ] Verify package resources include both schemas and that a clean wheel
  import does not rely on the source checkout.
- [ ] Reconcile tracked changes and preserved untracked outputs; never stage
  credentials, temporary probe logs, build products, or raw external payloads.
- [ ] Run the full verification set against the exact current workspace and
  record the result in this plan. Only `skill-verification-before-completion`
  may change this plan to `status: completed`.
- [ ] Run `git status --porcelain` after deterministic probes and clean-install
  verification; unexpected tracked-file changes fail the check and preserved
  untracked outputs remain untouched.

**Verification:**
- [ ] `python -m pytest -q`
- [ ] `python -m compileall -q src tests`
- [ ] `$evaluation_root = Join-Path ([IO.Path]::GetTempPath()) ("foresight-boundary-eval-" + [guid]::NewGuid()); python evaluation/run.py --matrix contract --output-root $evaluation_root`
- [ ] `python evaluation/run.py --matrix controller`
- [ ] Build a source snapshot wheel, install with `--no-deps` into a fresh target,
  import `foresight_os`, import all native builders, load both packaged schemas,
  and run `git diff --check`.
- [ ] Inspect sanitized disposable-MCP, real-MCP, hosted-web, live-pattern, anomaly,
  persistence, graph, and package reports for secrets, raw payloads, and
  unexplained failures; inspect real-MCP and hosted-web reports separately.

**Exit criteria:**
- Deterministic CI is available and credential-free.
- Implementation verification is complete independently of external providers.
- Every external integration proof has fresh evidence or is explicitly
  `BLOCKED_EXTERNAL` with its exact blocker; this does not become a passing
  release state or silently change the plan from `proposed` to `completed`.

## Verification Evidence

- Workspace: `C:\Users\HOANG PHI LONG DANG\repos\foresight-OS`, branch `main`,
  verified `HEAD` `846f4ed6f58e095b2294f5f94f075595cdc8fc30`; no staged changes.
- Fresh deterministic proof: `pytest` passed at `100%`; `compileall` passed;
  contract matrix passed for Direct, Sequential, Concurrent, Handoff, and Group
  Chat; Controller matrix passed with accuracy `1.0`; `git diff --check` passed.
- Fresh live proof against configured `9router` / `combo-high`: Direct,
  Sequential, Concurrent, Handoff, and Group Chat all returned `success` with
  `cleanup_complete: true`; Handoff recorded `handoffs: 1`, and Group Chat
  recorded four rounds.
- Fresh disposable MCP proof: read-only tool discovery and invocation passed,
  mutation tool was refused, the result normalized to an `EvidenceCandidate`,
  raw payload was not retained, and scope-owned cleanup completed.
- Fresh anomaly proof: `100` runs with seed `846f4ed`, stable state hash, no
  failures, and no monotonic handle accumulation.
- Fresh package proof: source wheel built, clean system-site-packages venv
  imported `foresight_os` and native runtime modules, and packaged
  `analysis.schema.json` plus `work_brief.schema.json` loaded successfully.
- External release gates remain separate and blocked: real MCP is
  `BLOCKED_EXTERNAL` because `FORESIGHT_REAL_MCP_URL/TOKEN/QUERY` are not fully
  configured; hosted web is `BLOCKED_EXTERNAL` because
  `FORESIGHT_REAL_WEB_QUERY` is not configured.
- Preserved unrelated untracked outputs: `build/`, `src/foresight_os.egg-info/`,
  `work/case-001/*`, and `work/case-005/`.

## Verification

- [x] Run the final deterministic test, compile, contract-matrix,
  Controller-matrix, wheel-install, schema-load, and `git diff --check` commands
  from Task 8 against the exact workspace.
- [x] Inspect the sanitized disposable-MCP, real-MCP, hosted-web, live-pattern,
  anomaly, persistence, graph, and package reports; classify implementation and
  external integration evidence independently.
- Expected: implementation verification is either `verified` or has a recorded
  required blocker; external proofs are independently `verified` or
  `BLOCKED_EXTERNAL`; no secrets, raw payloads, unexplained failures, or
  unexpected tracked changes remain.

Plan lifecycle: `completed` means the implementation verification is complete;
it does not mean external integration is release-approved. If implementation
verification is not complete, the plan remains `proposed`/`active`. A
`BLOCKED_EXTERNAL` result is never treated as a verified external pass.

## Completion Criteria

1. Callable tools are never executed during capability resolution.
2. Owned and borrowed resources are explicit and all terminal paths settle
   primary and cleanup outcomes without leaks or masked failures.
3. Data scope, access mode, approval, max parallelism, run-cache identity, and
   hard-observable call budgets are enforced before forbidden dispatch; provider
   request budgets are enforced only when a trustworthy provider hook exists.
4. Work Stages determine ordering and minimum capabilities; review and Handoff
   topology are explicit and pattern-independent.
5. Each native pattern has an actual model/tool/result/model regression proof.
6. Persistence race/restart/invalidation and graph exact-set/bounded-context
   probes pass.
7. Disposable MCP, approved real MCP, and provider-hosted web proofs are
   independently exercised; each produces validated evidence with sanitized
   telemetry and cleanup proof, or is explicitly `BLOCKED_EXTERNAL`.
8. Live native patterns and the 100-run anomaly probe pass without unexplained
   resource, state, or metric drift, or remain explicitly `BLOCKED_EXTERNAL`
   when the provider boundary is unavailable.
9. Deterministic CI covers all non-live checks and no private material is
   committed.
10. Final verification returns `verified` for implementation work; only then
    may the plan status become `completed`, and external integration remains a
    separately reported release gate when it is `BLOCKED_EXTERNAL`.

## Residual Risks

- Provider APIs may expose incomplete request/tool event telemetry; such fields
  remain explicitly `unknown` rather than inferred from participant counts.
- A real provider may complete Handoff without selecting a transfer; the live
  proof must report that outcome and fail the transfer-specific acceptance
  criterion rather than relabeling it as success.
- External web/MCP availability, rate limits, and endpoint policy remain
  environment-gated. They cannot be replaced by a fake probe when claiming
  real integration readiness.
