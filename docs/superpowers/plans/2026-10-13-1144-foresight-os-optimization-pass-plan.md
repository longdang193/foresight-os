---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: foresight-os-resource-xlsx-mcp-optimization
targets:
  - src/foresight_os/runtime/capabilities.py
  - src/foresight_os/runtime/participants.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/runtime/metrics.py
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/runtime/external_signals.py
  - src/foresight_os/runtime/crawl4ai.py
  - src/foresight_os/runtime/page_retrieval.py
  - tests/test_runtime_boundaries.py
  - tests/test_orchestration_patterns.py
  - tests/test_tool_enabled_patterns.py
  - tests/test_local_toolbelt.py
  - tests/test_external_signals.py
  - tests/test_crawl4ai.py
  - tests/fixtures/mcp_streamable_http_server.py
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/run_xlsx_probe.py
  - evaluation/README.md
  - README.md
  - pyproject.toml
---

# Foresight OS Resource, XLSX, and MCP Optimization Pass

## Verdict Review

Decision: adopt the verdict with two required refinements before activation.

The verdict correctly prioritizes run-wide resource ownership, blocking XLSX
execution, analytical correctness, supported MCP instrumentation, selective
provider setup, and bounded browser reuse. It also correctly rejects a new
distributed queue, graph service, external cache, or second orchestration
engine. The current main merge commit is `413cac37c4794fe38b006681dc72a03a9b538463`.

The verdict is a source review, not a performance benchmark or fresh live
provider verification. Therefore the first task must establish cold and warm
baselines before changing behavior. The optimization is accepted only when
the baseline and post-change receipts use the same representative workbook,
four MAF patterns, external-call fixture, cancellation case, and clean-environment
installation procedure.

The second refinement is an explicit safety boundary for caching and
middleware migration:

- Workbook reuse is immutable, run-scoped, keyed by content hash plus selection,
  parsing options, and effective safety limits. Failed, cancelled, or partially
  read results are never cached, and the source workbook is never modified.
- The existing native MCP transport, authentication, lifecycle, provenance,
  policy, and native error meaning remain authoritative. Private object cloning
  is removed only after the pinned `agent-framework==1.21.0` middleware path
  proves that MCP-generated tools are intercepted with the same budget,
  concurrency, telemetry, and failure semantics.
- Cancellation is not considered complete when an awaiting coroutine exits.
  A run retains capacity ownership until the underlying worker operation exits
  and its resources are closed.

XLSX analysis remains mandatory. Sequential, Concurrent, Handoff, and Group
Chat remain available and are selected from the existing recipe; none may be
silently removed or replaced by a benchmark-only path.

## Goal

Improve responsiveness, predictable resource use, and analytical trust without
expanding orchestration infrastructure or weakening the existing Analyst
toolbelt contract. The delivery must prove that:

1. synchronous workbook work no longer stalls the async event loop;
2. concurrency limits are owned by one run scope and hold across all agents;
3. cancellation, cleanup, and capacity accounting remain truthful until real
   underlying work exits;
4. repeated XLSX reads reuse immutable validated results within a run while
   preserving all mandatory inspection and provenance behavior;
5. missing values and untrusted formula caches cannot produce silent numeric
   conclusions;
6. MCP instrumentation uses supported framework middleware when the pinned
   framework exposes the required hook, without changing native MCP lifecycle;
7. unneeded external providers are not initialized; and
8. browser crawling remains optional, bounded, certificate-validating, and
   covered by a real network fixture.

## Implementation Outcomes

### Run-scoped execution ownership

`CapabilityScope` or its existing run-owned extension becomes the single owner
of semaphores, bounded worker capacity, run-scoped workbook cache, and owned
resource cleanup. `AgentFactory` receives references to that scope rather than
creating participant-local mutable copies. Tool telemetry separates queue wait,
underlying execution, cancellation completion, and cleanup time.

### Safe and efficient XLSX execution

`spreadsheet_read` keeps the mandatory XLSX contract: multi-sheet workbooks,
hidden sheets and rows, selected ranges and tables, formulas versus cached
values, dates/types/errors, merged headers, missing values, duplicates,
cross-sheet references, source cell/range provenance, deterministic analysis,
sensitivity/scenario analysis, and proof that the source remains unchanged.
Preflight rejects oversized expanded merged areas before normal workbook
allocation. Successful immutable reads are reused only inside the active run.

### Correct analytical conclusions

`data_analysis` preserves `None` as missing rather than converting it to zero
for comparisons. Numeric table operations inspect formula status and fail closed
with the existing recalculation error classification when a decision-critical
input is stale, absent, or an Excel error. Deterministic result keys and
provenance remain stable across cold and warm reads.

### Supported MCP and provider lifecycle

Budget enforcement, timing, failure accounting, and concurrency are implemented
through the supported `FunctionMiddleware` boundary for the pinned Agent
Framework version, with a thin Foresight adapter carrying capability metadata.
MCP discovery, authentication, native transport, and close behavior remain
unchanged. Hosted providers are selected from required capability IDs and are
created lazily inside the run cleanup scope; an unused provider cannot make a
local XLSX run unavailable.

### Bounded browser and release evidence

Crawl4AI is reused only within a bounded run when browser rendering is required,
with certificate verification enabled by default and native controls for
service workers and WebSockets. A repeatable optimization probe records cold
and warm metrics for all four MAF patterns, local XLSX work, external-call
fixtures, cancellation, cleanup, and provider selection without recording
credentials, raw pages, prompts, or raw provider payloads.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-performance-optimization`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`
- Isolation: `current workspace` with existing untracked `build/`, egg-info, and `work/` artifacts preserved and never staged
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit the listed source, test, probe, documentation, and dependency files; run repository tests, benchmarks, clean-environment checks, and configured read-only fixtures; write receipts only under ignored `work/`
- User-approval actions: push, merge, external publication, provider authentication changes, destructive cleanup, deletion of preserved work artifacts, and dependency major-version changes
- Parallel ownership: `none`; the concurrency, cache, middleware, and cleanup changes share runtime boundaries
- Sequential fallback: complete each task and its proof before starting the next task; stop at any failed safety or compatibility gate

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/external-signal-mcp-integration`
- Base commit: `fe9b03e79c0bdf75690bd7b8cc6b5223c6924e23`
- Expected workspace: current branch with no tracked changes before plan creation; preserve existing untracked `build/`, egg-info, and `work/` artifacts
- Next action: final verification and handoff; all implementation tasks and
  release receipts are complete
- Blockers: none for planning; execution requires a fresh baseline before implementation

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `Codex` | none | baseline receipt and framework compatibility inspection | `work/optimization-baseline/receipt.json`, `work/optimization-baseline/acceptance.json` |
| Task 2 | `completed` | current | `Codex` | Task 1 | run-wide semaphore, event-loop, cancellation, and cleanup tests | `tests/test_runtime_boundaries.py`, full suite |
| Task 3 | `completed` | current | `Codex` | Task 2 | XLSX correctness, formula-trust, and merged-area tests | `tests/test_local_toolbelt.py`, `work/optimization-xlsx/xlsx-probe.json` |
| Task 4 | `completed` | current | `Codex` | Task 3 | run-local cache, index, hashing, and read-only tests | `tests/test_local_toolbelt.py`, `work/optimization-xlsx/xlsx-probe.json` |
| Task 5 | `completed` | current | `Codex` | Task 2 | selective provider setup and run cleanup tests | `tests/test_external_signals.py`, release receipt |
| Task 6 | `completed` | current | `Codex` | Tasks 2 and 5 | supported MCP middleware boundary and four-pattern budget tests | `tests/test_runtime_boundaries.py`, native MCP receipt |
| Task 7 | `completed` | current | `Codex` | Tasks 3–6 | browser fixture, clean install, optimization probe, and final receipts | `work/optimization-release/receipt.json`, `work/optimization-release/clean-receipt-final2.json` |

## Execution Evidence Reconciliation

- Native MCP root cause: the probe looked for tools in the wrong client
  argument and invoked the container instead of the flattened discovered
  function; it now exercises `options["tools"]` through public
  `client_kwargs["middleware"]` and records `tool_calls: 1`.
- Private MCP clone/rebind fallback removed from `capabilities.py`; native
  MCP objects retain their transport and lifecycle, while direct callers use a
  thin public `call_tool` adapter.
- Fresh focused suite: `49 passed`; full suite: `148 passed`.
- Fresh baseline and release receipts are `VERIFIED`; native MCP discovery and
  middleware accounting both report one call; four MAF patterns settle owned
  resources; 100-run soak reports no monotonic growth.
- Fresh clean wheel install passes `pip check`, base imports, MCP import, and
  `[crawl]` import. The clean release receipt is `VERIFIED` with native MCP
  `tool_calls: 1`.
- No credentials, `.env`, raw provider payloads, or source workbook mutations
  were added to the tracked diff.

## Task Breakdown

### Task 1: Establish the optimization baseline and framework gate

**Purpose:**
- Measure the current bottlenecks before changing behavior and prove the
  installed framework API needed for the MCP migration.

**Task Function:**
- Produce a deterministic baseline and a compatibility decision for the
  pinned runtime.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: baseline work is bounded, but the workload spans runtime,
  XLSX, browser, and four orchestration patterns.

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: the lead controller can validate the baseline commands and
  receipts directly.

**Specification Coverage:**
- The verdict is explicitly source-review-only; no optimization may be claimed
  without comparable cold/warm measurements.
- The installed dependency remains `agent-framework==1.21.0` unless a separate
  approved dependency change is made.

**Required Skills:**
- `skill-performance-optimization`
- `skill-systematic-debugging`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/capabilities.py:_instrumented_dispatch`
- Inspect: `src/foresight_os/runtime/capabilities.py:instrument_tool`
- Inspect: `src/foresight_os/runtime/participants.py:AgentFactory.create`
- Inspect: `src/foresight_os/runtime/workflow.py:run_recipe_async`
- Inspect: `src/foresight_os/runtime/local_toolbelt.py:spreadsheet_read`
- Inspect: `src/foresight_os/runtime/external_signals.py:load_hosted_mcp_bindings`
- Inspect: `agent_framework.FunctionMiddleware` and `FunctionInvocationContext`
- Modify: `evaluation/probes/run_optimization_probe.py`
- Verify: `tests/test_runtime_boundaries.py`, `tests/test_orchestration_patterns.py`, `tests/test_local_toolbelt.py`, `tests/test_tool_enabled_patterns.py`

**Dependencies:**
- Current source at `fe9b03e`; the verdict reviewed merged main at
  `413cac37c4794fe38b006681dc72a03a9b538463`.

**Authority:**
- Preauthorized local actions: add the baseline probe and inspect installed APIs without changing runtime behavior
- Stop for: missing representative IEA workbook fixture, unavailable pinned framework middleware API, or a required external write/authentication action

**Steps:**
- [x] Step 1: Define one fixed workload using the repository XLSX fixture plus
  the IEA workbook already used by the preserved local analysis receipts, one
  deterministic external-call fixture, and the existing Sequential,
  Concurrent, Handoff, and Group Chat recipes.
- [x] Step 2: Record cold and warm p50/p95 wall latency, event-loop delay,
  peak Python allocation, workbook parse/load count, crawler/browser starts,
  active worker count, cancellation completion time, cleanup time, tool calls,
  and accepted findings. Keep receipt fields sanitized and write only under
  `work/optimization-baseline/`.
- [x] Step 3: Inspect `FunctionMiddleware` invocation semantics and prove with a
  credential-free disposable Streamable HTTP MCP server, actual
  `MCPStreamableHTTPTool` discovery, and an agent-driven invocation that the
  pinned framework routes discovered functions through middleware. Record tool
  identity, result, native error, cancellation, and cleanup observations.
- [x] Step 4: Freeze the workload manifest, warm-up count, sample count, and
  acceptance thresholds in `work/optimization-baseline/acceptance.json` before
  Task 2 starts: two warm-up runs and ten measured runs per MAF pattern; p95
  end-to-end and event-loop delay may regress by at most 20%, peak allocation by
  at most 15%, tool calls per accepted finding may not increase, and no resource
  count may grow monotonically across the 100-run soak. Threshold changes must
  be recorded as a plan deviation before the affected task, never after release
  results are observed.
- [x] Step 5: Record the baseline and the native middleware boundary result in
  the probe JSON; do not remove the existing instrumentation yet.

**Verification:**
- [x] `python evaluation/probes/run_optimization_probe.py --mode baseline --output work/optimization-baseline/receipt.json`
- [x] `python -c "import agent_framework; print(agent_framework.__file__)"`
- Expected: one sanitized baseline receipt per workload, all four patterns
  execute, XLSX remains readable, the native MCP path is exercised through
  actual discovery and agent invocation, and acceptance thresholds are frozen
  before implementation changes.

**Exit Criteria:**
- Baseline metrics and the installed middleware boundary are reproducible and
  available for comparison by every later task.

### Task 2: Make execution capacity run-scoped and cancellation-truthful

**Purpose:**
- Prevent synchronous tool work from blocking the event loop and ensure one
  run-wide concurrency budget is shared across all participants.

**Task Function:**
- Refactor the existing capability scope into the owner of bounded execution,
  semaphores, cancellation signaling, and resource settlement.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: high-risk backend concurrency change with shared callers and
  cancellation semantics.

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: focused runtime boundary and orchestration tests provide the
  required proof.

**Specification Coverage:**
- Capability definitions classify execution as `ASYNC`, `INLINE`, or
  `BLOCKING`; only `BLOCKING` tools use the bounded worker pool.
- Synchronous workbook parsing and analysis execute through a bounded executor.
- The semaphore is acquired before execution and released only after the
  underlying worker exits, including cancellation of the awaiting coroutine.
- Queue wait and execution time are separately observable.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-code-standards`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/runtime/capabilities.py:CapabilityDefinition`, `CapabilityScope`, `_instrumented_dispatch`, `instrument_tool`
- Inspect/modify: `src/foresight_os/runtime/participants.py:AgentFactory.create`
- Inspect/modify: `src/foresight_os/runtime/workflow.py:run_recipe_async`, `_run_native_stage`
- Inspect/modify: `src/foresight_os/runtime/metrics.py:RunMetrics`
- Verify: `tests/test_runtime_boundaries.py`, `tests/test_orchestration_patterns.py`, `tests/test_tool_enabled_patterns.py`

**Dependencies:**
- Task 1 baseline and middleware gate complete.

**Authority:**
- Preauthorized local actions: change run-scope context propagation, bounded local execution, metrics fields, and focused tests
- Stop for: a cancellation path that releases capacity before the worker exits, a changed budget meaning, or a required Agent Framework API change outside the pinned version

**Steps:**
- [x] Step 1: Add an execution mode to `CapabilityDefinition` and classify
  `spreadsheet_read`, `data_analysis`, and large `graph_context` as `BLOCKING`,
  `calculation` and `domain_validation` as `INLINE`, and web/page/MCP tools as
  `ASYNC`; keep the classification in the capability registry rather than in
  individual callers.
- [x] Step 2: Add run-owned execution state to the existing `CapabilityScope`,
  including one semaphore map, one bounded executor for synchronous tools,
  cancellation events, and explicit close/shutdown registration.
- [x] Step 3: Pass the same scope and mutable semaphore map from
  `run_recipe_async` through `AgentFactory.create` to every participant;
  eliminate participant-local copies of run-wide controls.
- [x] Step 4: Route `BLOCKING` local tool calls through the bounded executor;
  keep `ASYNC` tools awaited and `INLINE` tools on the event loop; preserve tool
  return values, budget reservation, and failure classes.
- [x] Step 5: On coroutine cancellation, signal the cooperative workbook
  cancellation callback, await the worker future to settlement without releasing
  the semaphore early, then close the executor during run cleanup.
- [x] Step 6: Add queue-wait, execution, cancellation-settlement, and cleanup
  metrics without changing existing metric field meanings.

**Verification:**
- [x] `python -m pytest -q tests/test_runtime_boundaries.py tests/test_orchestration_patterns.py tests/test_tool_enabled_patterns.py`
- Expected: a blocking local tool does not prevent an async heartbeat from
  running; concurrent participants share the declared run-wide maximum; a
  cancelled workbook call eventually exits, releases capacity exactly once, and
  leaves no live owned executor after cleanup.

**Exit Criteria:**
- All four MAF patterns pass run-wide concurrency and cancellation tests with
  unchanged authorization, budgets, outputs, and cleanup semantics.

### Task 3: Harden XLSX correctness and allocation safety

**Purpose:**
- Prevent pathological workbook allocation and incorrect numeric conclusions
  before any cache or read-path optimization is introduced.

**Task Function:**
- Make merged-area limits, missing values, formula trust, and structured numeric
  inputs explicit at the existing XLSX analysis boundary.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: P0 stability and analytical correctness with a clear
  regression boundary.

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: red/green regression tests and the existing mandatory XLSX
  contract suite.

**Specification Coverage:**
- `ToolbeltLimits` exposes `max_merged_cells_per_range` and
  `max_total_merged_cells`; both are enforced during XML preflight before
  `openpyxl.load_workbook()`.
- Missing values remain `None` and compare results use `status=INCOMPLETE_INPUT`
  with `delta=None`, never an implicit zero.
- Untrusted formula inputs produce `BLOCKED_RECALCULATION` in decision-critical
  numeric operations while preserving formula and cached-value inspection data.
- Spreadsheet analysis consumes `TypedMeasurement`, `CalculationRecord`, or
  explicitly structured numeric evidence; prose regex extraction is retained
  only in the isolated legacy Evidence compatibility path.

**Required Skills:**
- `skill-performance-optimization`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/runtime/local_toolbelt.py:ToolbeltLimits`, `_preflight_xlsx_archive`, `_numeric`, `spreadsheet_read`, `TypedTable`, `TypedMeasurement`, `data_analysis`, `calculation`
- Verify: `tests/test_local_toolbelt.py`, `tests/fixtures/analyst_multisheet.xlsx`, `evaluation/probes/run_xlsx_probe.py`, `tests/test_toolbelt_contracts.py`

**Dependencies:**
- Task 2 execution ownership and cancellation semantics are complete.

**Authority:**
- Preauthorized local actions: add merged-area preflight limits, formula/missing-value guards, structured numeric input handling, and focused XLSX regression tests
- Stop for: loss of hidden-sheet/row, formula/cache, merged-header, table, cross-sheet, or provenance data; source hash changes; or a changed public formula-status meaning

**Steps:**
- [x] Step 1: Add `max_merged_cells_per_range` and `max_total_merged_cells` to
  `ToolbeltLimits`, compute each merge’s row-by-column area during XML preflight,
  and reject a pathological merge before normal workbook allocation.
- [x] Step 2: Carry formula status into analysis-ready table rows without
  discarding the original `TypedMeasurement` formula and cached value; expose an
  explicit blocked/sentinel state to numeric table operations.
- [x] Step 3: Change `compare` so any missing operand yields `delta=None` and
  `status=INCOMPLETE_INPUT`; only an explicit Work Brief imputation rule may
  turn missing data into a numeric value.
- [x] Step 4: Gate `aggregate`, `sum`, `mean`, `scenario`, `sensitivity`, and
  `compare` when selected formula inputs are `FORMULA_WITHOUT_CACHE`,
  `FORMULA_STALE_OR_UNKNOWN`, or `ERROR`, and restrict `_numeric()` prose
  parsing to the legacy Evidence compatibility branch rather than spreadsheet
  rows.
- [x] Step 5: Add red tests before implementation for a huge merged area, null
  comparisons, stale and absent formula caches, cached Excel errors, trusted
  cached formulas, structured numeric evidence, legacy prose compatibility, and
  the supported `aggregate`, `sum`, and `mean` aliases.

**Verification:**
- [x] `python -m pytest -q tests/test_local_toolbelt.py tests/test_toolbelt_contracts.py`
- Expected: the new tests fail for the expected pre-fix reason and pass after
  implementation; no numeric output silently treats missing data or untrusted
  formulas as trustworthy zeros or recalculations, and a huge merged range is
  rejected before normal workbook allocation.

**Exit Criteria:**
- XLSX correctness and stability are proven independently of caching, with all
  mandatory inspection and source-integrity assertions preserved.

### Task 4: Add run-local XLSX reuse without semantic shortcuts

**Purpose:**
- Reduce repeated workbook parsing and allocation only after Task 3 has proven
  correct analytical semantics.

**Task Function:**
- Implement bounded immutable run-local reuse, structural indexing, incremental
  hashing, and selective read-only extraction.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: performance-sensitive data path with mandatory XLSX semantics
  already protected by Task 3.

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: cache identity, manifest, parse-count, and source-integrity
  tests.

**Specification Coverage:**
- Cache keys include canonical source identity, workbook SHA-256, sheet/range/table
  selection, hidden content flags, formula/cache options, and effective limits.
- Only successful complete `WorkbookReadResult` snapshots and their indexes are
  cached; cache scope ends with the run and final analytical conclusions are
  never cached.
- Hashing reads bounded chunks instead of allocating all workbook bytes at once.
- A `WorkbookManifest` is built during preflight before any read-only streaming
  change; it records the structural facts needed to preserve hidden sheets/rows,
  tables, merged headers, formulas, cached values, and provenance.
- Read-only iteration is introduced only for paths whose semantics are proven
  equivalent by the manifest and contract tests.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/runtime/local_toolbelt.py:ToolbeltLimits`, `_preflight_xlsx_archive`, `spreadsheet_read`, `WorkbookReadResult`, `TypedMeasurement`
- Inspect/modify: `src/foresight_os/runtime/capabilities.py:CapabilityScope`
- Inspect/modify: `src/foresight_os/runtime/workflow.py:run_recipe_async`
- Verify: `tests/test_local_toolbelt.py`, `tests/test_toolbelt_contracts.py`, `evaluation/probes/run_xlsx_probe.py`

**Dependencies:**
- Task 3 XLSX correctness and allocation guards are complete.

**Authority:**
- Preauthorized local actions: add run-local immutable workbook reuse, chunked hashing, workbook manifest/indexing, selective read-only extraction, and focused performance tests
- Stop for: any changed mandatory XLSX semantics, cross-run cache state, cached final conclusions, or a read-only path that lacks equivalence proof

**Steps:**
- [x] Step 1: Add a bounded `WorkbookReadCache` owned by `CapabilityScope` with
  entry-count and byte limits; make the key deterministic and include every
  read-affecting option, effective safety limit, and canonical source identity.
- [x] Step 2: Reuse successful snapshots through the existing
  `spreadsheet_read` binding so analyst and validator receive the same immutable
  object within one run without changing the direct public function contract.
- [x] Step 3: Replace whole-file hashing with chunked SHA-256 reads and retain
  the same digest value and source-immutability proof.
- [x] Step 4: Build one index for `(sheet, coordinate) -> TypedMeasurement` and
  `(sheet, source_range) -> measurements`, then use it for table construction,
  validation, evidence generation, and cross-sheet resolution.
- [x] Step 5: Use the `WorkbookManifest` to introduce read-only formula and
  cached-value iteration only where merged headers, tables, hidden content,
  calculation metadata, and provenance remain equivalent; close every workbook
  on success, failure, and cancellation.
- [x] Step 6: Add cache-hit, parse-count, chunked-hash, manifest-equivalence,
  cleanup, source-integrity, and two-path-identical-content tests. The same path
  must reuse its snapshot; a byte-identical workbook at a different path must
  retain the second path in `WorkbookReadResult.source`.

**Verification:**
- [x] `python -m pytest -q tests/test_local_toolbelt.py`
- [x] `python -m pytest -q tests/test_toolbelt_contracts.py`
- [x] `python evaluation/probes/run_xlsx_probe.py --fixture tests/fixtures/analyst_multisheet.xlsx --output-root work/optimization-xlsx`
- Expected: identical reads produce one parse/snapshot per run with identical
  deterministic keys and provenance; mandatory XLSX fields remain unchanged;
  cache entries disappear at run cleanup; source hash remains unchanged; the
  probe writes `work/optimization-xlsx/xlsx-probe.json`.

**Exit Criteria:**
- XLSX reuse lowers warm parse/load counts without changing any mandatory field,
  formula status, deterministic result, provenance, or source-integrity assertion.

### Task 5: Make hosted provider setup lazy and selective

**Purpose:**
- Avoid initializing or failing on hosted providers when the selected recipe does
  not require their capability, while preserving native resource ownership.

**Task Function:**
- Derive required capabilities from the recipe and resolve hosted MCP resources
  through the existing `RESOURCE_FACTORY` binding kind inside the run scope.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: P0 lifecycle and configuration isolation with a bounded
  provider-binding change.

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: selective-binding tests and run cleanup assertions.

**Specification Coverage:**
- Required capabilities are the union of participant capability IDs selected by
  the recipe.
- A local XLSX-only run makes zero hosted provider construction attempts.
- A required provider is created lazily through `RESOURCE_FACTORY`, owned by
  `CapabilityScope`, reused within the run, and closed exactly once.
- Missing provider credentials remain `BLOCKED_EXTERNAL` only for the capability
  that requested the resource.

**Required Skills:**
- `skill-backend-verification`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/runtime/workflow.py:run_recipe_async`
- Inspect/modify: `src/foresight_os/runtime/external_signals.py:load_hosted_mcp_bindings`, `create_hosted_mcp_tool`
- Inspect/modify: `src/foresight_os/runtime/capabilities.py:CapabilityResolver`, `CapabilityScope`, `CapabilityBindingKind.RESOURCE_FACTORY`
- Verify: `tests/test_external_signals.py`, `tests/test_tool_enabled_patterns.py`, `tests/test_orchestration_patterns.py`

**Dependencies:**
- Task 2 shared scope and cleanup are complete.

**Authority:**
- Preauthorized local actions: add recipe-derived capability filtering, lazy resource factories, run-scoped reuse, and lifecycle tests
- Stop for: a local-only recipe contacting a hosted endpoint, credentials appearing in receipts, or provider cleanup depending on process-global state

**Steps:**
- [x] Step 1: Compute the required capability union from participant configs
  before loading any hosted bindings and pass only those IDs into resolution.
- [x] Step 2: Represent hosted provider construction as a `RESOURCE_FACTORY`
  binding that creates the native MCP resource on first resolution, registers
  ownership with `CapabilityScope`, and preserves the provider fingerprint.
- [x] Step 3: Reuse the resolved provider for multiple participants in one run
  and ensure a failed factory affects only the requesting capability.
- [x] Step 4: Add local-only, one-provider, multi-provider, missing credential,
  construction failure, reuse, and close-once tests.

**Verification:**
- [x] `python -m pytest -q tests/test_external_signals.py tests/test_tool_enabled_patterns.py tests/test_orchestration_patterns.py`
- Expected: unused providers have zero construction attempts; required missing
  credentials remain `BLOCKED_EXTERNAL`; used resources are reused and closed
  once at run settlement.

**Exit Criteria:**
- Provider initialization is demand-driven, resource ownership is run-scoped,
  and failure scope matches the capability that requested it.

### Task 6: Replace private MCP wrapping with supported middleware

**Purpose:**
- Remove direct dependence on Agent Framework private MCP object fields while
  preserving Foresight budgets, policy, telemetry, failure classes, and limits.

**Task Function:**
- Implement and validate a Foresight function middleware adapter for the pinned
  Agent Framework release.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: framework-integration change with compatibility and lifecycle
  risk.

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: a direct MCP-shaped invocation test must observe the real
  supported hook before private wrapping is removed.

**Specification Coverage:**
- `FunctionMiddleware` owns budget reservation, queue/execution telemetry,
  failure accounting, concurrency, and cancellation observation for supported
  function invocations.
- Native MCP transport, discovery, authentication, lifecycle, and error
  payloads remain untouched.
- Private `_tool`, closure rebinding, and cloned-tool manipulation are removed
  only after the boundary test passes. If MCP calls bypass middleware, retain
  only the thinnest documented adapter and record the compatibility blocker.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/runtime/capabilities.py:instrument_tool`, `_InstrumentedMCPTool`, `_clone_mcp_function`, `_rebind_mcp_callable`
- Inspect/modify: `src/foresight_os/runtime/participants.py:AgentFactory.create`
- Verify: `tests/test_runtime_boundaries.py`, `tests/test_external_signals.py`, `tests/test_tool_enabled_patterns.py`
- Verify dependency: `pyproject.toml` pinned `agent-framework==1.21.0`

**Dependencies:**
- Task 1 middleware compatibility result, Task 2 shared execution controller,
  and Task 5 provider lifecycle.

**Authority:**
- Preauthorized local actions: add the supported middleware adapter, migrate instrumentation, and add direct MCP-shaped boundary tests
- Stop for: MCP-generated tools bypassing middleware, changed native MCP lifecycle, or a required private-framework fallback that cannot be isolated and documented as a blocker

**Steps:**
- [x] Step 1: Define the middleware context-to-capability mapping using public
  function metadata and the existing `CapabilityDefinition`; do not inspect
  private MCP fields.
- [x] Step 2: Move the shared invocation accounting into one controller used by
  ordinary tools and middleware, preserving one budget charge per actual call,
  declared parallelism, failure class, and result identity.
- [x] Step 3: Prove success, provider error, budget exhaustion, cancellation,
  and cleanup through the same credential-free Streamable HTTP MCP fixture and
  native `MCPStreamableHTTPTool` discovery/agent-driven invocation established
  in Task 1; retain the repository’s MCP-shaped fixture only as supplementary
  unit coverage.
- [x] Step 4: Remove the private clone and closure-rebinding path only after the
  direct boundary tests pass; retain native MCP objects and close behavior.

**Verification:**
- [x] `python -m pytest -q tests/test_runtime_boundaries.py tests/test_external_signals.py tests/test_tool_enabled_patterns.py`
- Expected: MCP-shaped calls traverse supported middleware, charge once, obey
  authorization and concurrency, preserve native errors, and leave no private
  wrapper state or unclosed owned resource.

**Exit Criteria:**
- No production path depends on `_tool` cloning or closure rebinding, and the
  supported middleware receipt covers all required invocation outcomes.

### Task 7: Bound browser reuse, add release probes, and reconcile documentation

**Purpose:**
- Complete the optimization proof across Crawl4AI, clean installation, four MAF
  patterns, repeated runs, and final documentation.

**Task Function:**
- Produce end-to-end evidence and release-level verification after the runtime
  changes are stable.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: cross-boundary verification and release evidence.

**Validator Profile:**
- Controller-selected: `<none>`
- Selection basis: final verification is owned by the lead controller using
  fresh local and CI output.

**Specification Coverage:**
- `page_retrieval` is attempted first; Crawl4AI is an escalation capability only
  when retrieval fails or rendering is explicitly required. Browser resources
  are bounded to one run and certificate-validating by default.
- Real browser traffic, not only a manually invoked route callback, proves TLS,
  private destinations, redirects, WebSockets, and service-worker behavior.
- Clean installation creates a fresh environment without
  `--system-site-packages` or `--no-deps`, installs the wheel with declared
  dependencies, and separately checks `[mcp]` and `[crawl]` extras.
- Repeated runs do not steadily grow threads, processes, browser contexts,
  connections, or cache entries.

**Required Skills:**
- `skill-performance-optimization`
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect/modify: `src/foresight_os/runtime/page_retrieval.py:PageRetrievalCapability`, `bind_page_retrieval`
- Inspect/modify: `src/foresight_os/runtime/crawl4ai.py:Crawl4AICapability`, `bind_crawl4ai`
- Modify: `evaluation/probes/run_optimization_probe.py`, `evaluation/README.md`, `README.md`, `pyproject.toml`
- Verify: `tests/test_crawl4ai.py`, `tests/test_local_toolbelt.py`, `tests/test_runtime_boundaries.py`, `tests/test_orchestration_patterns.py`, `tests/test_tool_enabled_patterns.py`

**Dependencies:**
- Tasks 3–6 complete with fresh focused proof.

**Authority:**
- Preauthorized local actions: add bounded browser reuse, real fixture probes, clean-environment checks, sanitized receipts, and documentation updates
- Stop for: certificate verification being disabled by default, private or redirected destinations bypassing validation, browser/service-worker/WebSocket tests lacking real network evidence, or any required external publication

**Steps:**
- [x] Step 1: Make `page_retrieval` the first path and require an explicit
  rendering-needed or retrieval-failed transition before invoking `web_crawl`;
  add the escalation assertion to the capability tests.
- [x] Step 2: Reuse one crawler/browser resource per run only after escalation;
  isolate a fresh browser context per source, close each context, and close the
  run-owned crawler/browser through `CapabilityScope`.
- [x] Step 3: Set `ignore_https_errors=False` by default, use native
  `context.route()`, `context.route_web_socket()`, and
  `service_workers="block"`, and retain destination validation for HTTP,
  redirects, and WebSockets.
- [x] Step 4: Do not add DNS caching unless the browser connection is constrained
  to the validated public addresses or an equivalent verified network boundary.
  Until that proof exists, retain per-request DNS validation; any future
  run/request cache must revalidate redirects, same-host DNS changes, and
  unapproved origins rather than relying on a prior public-host approval.
- [x] Step 5: Add a real local browser fixture that exercises HTTPS/TLS,
  private-target rejection, redirect validation, same-host DNS changing from a
  public address to a private address, WebSocket interception, and service-worker
  blocking through actual browser traffic.
- [x] Step 6: Run the optimization probe for cold/warm XLSX, all four MAF
  patterns, external-call fixtures, cancellation, provider selection, browser
  reuse, cleanup, and repeated-run resource counts.
- [x] Step 7: Create a clean virtual environment, build the wheel, install the
  wheel without `--system-site-packages` or `--no-deps`, import the package and
  schemas, inspect a tiny XLSX fixture, then run separate dependency-resolved
  checks for `.[mcp]` and `.[crawl]`.
- [x] Step 8: Run a 100-run soak and apply only metric-backed P2 tuning after
  the P0/P1 acceptance gates pass; record any threshold change as a plan
  deviation rather than hiding it in the probe.
- [x] Step 9: Update README and evaluation documentation with the measured
  baseline, target thresholds, cache scope, cancellation contract, middleware
  boundary, provider-selection behavior, and exact verification commands.

**Verification:**
- [x] `python -m pytest -q`
- [x] `python -m compileall -q src evaluation`
- [x] `git diff --check`
- [x] `python evaluation/probes/run_optimization_probe.py --mode release --output work/optimization-release/receipt.json`
- [x] clean-environment wheel install, `[mcp]` extra check, and `[crawl]` extra check recorded by the probe
- [x] 100-run soak receipt recorded under `work/optimization-release/`
- Expected: cold/warm comparisons show no regression against Task 1 beyond
  declared thresholds; all four MAF patterns remain available; mandatory XLSX
  behavior and source immutability pass; browser and provider receipts are
  explicit `VERIFIED`, `BLOCKED_EXTERNAL`, or `FAILED`; repeated runs settle
  all owned resources; page retrieval precedes browser crawling; native browser
  controls observe real WebSocket and service-worker traffic.

**Exit Criteria:**
- The release receipt contains fresh measurements, all required boundary and
  failure evidence, no unresolved required task, and no unrecorded scope
  deviation. The plan is `active` during execution and changes to `completed`
  only after final verification succeeds.

## Verification

Final artifact verification after all tasks:

- `python -m pytest -q`
- `python -m compileall -q src evaluation`
- `git diff --check`
- `python evaluation/probes/run_optimization_probe.py --mode release --output work/optimization-release/receipt.json`
- clean wheel installation without `--system-site-packages` or `--no-deps`,
  followed by credential-free base, `[mcp]`, and `[crawl]` checks
- 100-run soak receipt under `work/optimization-release/`
- Inspect the receipt for cold/warm p50/p95 latency, event-loop delay, peak
  allocation, parse/load count, queue wait, execution time, cancellation
  settlement, cleanup, provider construction, browser starts, parse cache hits,
  and repeated-run resource deltas.
- Confirm the tracked diff contains no `.env`, credential, raw page, prompt, or
  raw provider payload and that the source workbook hash is unchanged.

## Completion Criteria

The plan is ready for completion verification when:

1. Tasks 1–7 have completed with their task-local proof recorded in the plan
   ledger and receipts stored under ignored `work/` paths.
2. The measured optimization compares the same workload before and after the
   change and records thresholds, environment, and any accepted deviation.
3. All four MAF patterns still execute with the same capability authorization,
   budget, evidence, persistence, and cleanup contracts.
4. XLSX mandatory inspection, provenance, deterministic analysis, formula
   trust, missing-value status, structured numeric inputs,
   sensitivity/scenario behavior, and source immutability remain proven.
5. MCP middleware proof covers success, native provider error, budget,
   cancellation, concurrency, and cleanup paths without private object access.
6. Hosted provider setup is selective, credentials remain external to tracked
   files, and missing providers are truthfully classified.
7. Page retrieval precedes Crawl4AI escalation; browser boundaries are proven
   by real traffic, native controls, redirect revalidation, and same-host DNS
   rebinding rejection; no DNS cache is accepted without connection-level proof.
8. Clean wheel installation, optional dependency checks, the 100-run soak, and
   the full deterministic test suite pass.
9. `skill-verification-before-completion` returns `verified` before the plan
   status is changed from `active` to `completed`.

## Self-Review

- **Coverage:** Every verdict recommendation maps to a task: execution modes,
  ownership, and cancellation (Task 2), XLSX correctness and merged-area safety
  (Task 3), run-local reuse, indexing, hashing, and selective read-only paths
  (Task 4), selective lazy provider setup (Task 5), supported MCP middleware
  (Task 6), browser escalation/reuse, clean packaging, soak, and measurement
  (Task 7), with the baseline gate in Task 1.
- **Ownership:** Runtime behavior remains canonical in `src/foresight_os`; tests
  and probes consume those contracts; receipts remain ignored under `work/`.
- **Ordering:** Baseline precedes changes; run scope precedes resource
  consumers; correctness precedes caching claims; selective provider setup
  precedes middleware migration; release probes and P2 tuning run only after
  all P0/P1 runtime gates.
- **Safety:** No task adds a second orchestration engine, distributed queue,
  graph service, cross-run cache, or hidden credential loader.
- **Consistency:** The same names are used throughout: `CapabilityScope`,
  `AgentFactory.create`, `run_recipe_async`, `spreadsheet_read`,
  `ToolbeltLimits`, `data_analysis`, `FunctionMiddleware`, and
  `load_hosted_mcp_bindings`.
