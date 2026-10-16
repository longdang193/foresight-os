---
layer: change
artifact_type: plan
status: complete
template_id: implementation-plan
contract_version: "1"
name: foresight-os-next-optimization-pass
targets:
  - src/foresight_os/analysis/powerbi_strategic_portfolio.py
  - src/foresight_os/analysis/workbook_inputs.py
  - src/foresight_os/analysis/portfolio_resilience.py
  - src/foresight_os/analysis/supplier_resilience.py
  - src/foresight_os/analysis/technology_radar.py
  - src/foresight_os/analysis/ev_capacity_investment.py
  - src/foresight_os/analysis/evidence_workflow.py
  - src/foresight_os/analysis/independent_validation.py
  - src/foresight_os/domain/analysis_inputs.py
  - src/foresight_os/domain/models.py
  - src/foresight_os/domain/validation.py
  - src/foresight_os/controller/policy.py
  - src/foresight_os/controller/recipes.py
  - src/foresight_os/controller/task_shape.py
  - src/foresight_os/runtime/execution_gate.py
  - src/foresight_os/runtime/capabilities.py
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/schemas/work_brief.schema.json
  - src/foresight_os/schemas/execution_recipe.schema.json
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/optimization_measurement.py
  - evaluation/probes/compare_optimization_receipts.py
  - evaluation/README.md
  - tests/test_analysis_input_contract.py
  - tests/test_brief_portability.py
  - tests/test_stage_inputs.py
  - tests/test_selective_reuse.py
  - tests/test_execution_gate.py
  - tests/test_runtime_boundaries.py
  - tests/test_capabilities.py
  - tests/test_local_toolbelt.py
  - tests/test_orchestration_patterns.py
  - tests/test_result_committer.py
  - tests/test_independent_validation.py
  - tests/test_controller_selection.py
  - tests/test_optimization_measurement.py
  - tests/test_markdown_links.py
  - tests/test_analysis_schema.py
---

# ForesightOS Next Optimization Pass Plan

## Goal

Close the remaining high-impact correctness and lifecycle gaps identified
against `main@0fa7e3b`, then connect the existing run-owned workbook reuse to
the real repeated-investigation path and remove only the duplicated compatibility
work that no longer has a live consumer.

The implementation must preserve the existing trust boundary:

```text
exact-byte SourceSnapshot
→ material workbook-view identity
→ run-owned WorkbookContext
→ provenance / authority
→ deterministic analysis
→ canonical result
→ independent validation
→ AnalysisStore
→ explicit currentness boundary
→ human acceptance
→ settlement / cleanup
```

This plan deliberately does not start another controller, cache, lifecycle,
graph, or orchestration redesign. It uses three bounded patches in dependency
order: correctness and lifecycle closure, real reuse and runtime deletion, and
compatibility/process cleanup with truthful measurement.

## Review Of The Verdict

The verdict is adopted with these decisions:

- **Mandatory:** exact period identity, table-local mappings, global/stage
  contract fallback, dependency-aware invalidation, cancellation settlement,
  metadata-only admission, warm-read cancellation, uniform result bounds, and
  the currently non-executing blocking-cancellation regression.
- **High-value follow-up:** production `WorkbookContext` propagation,
  source-reuse versus analysis-result separation, authority-lifetime safety,
  linear dependency validation, observable synthesis cancellation, one-time
  fingerprinting, and one-time adapter signature inspection.
- **Deferred maintenance:** removal of incidental `TaskShape` topology
  inference, stronger `WorkBrief.analysis_inputs` typing, process-global
  authority fallback, and broad documentation reduction. Task 5 removes only
  duplicate producers whose consumers have already migrated; the other cleanup
  remains optional follow-up work.
- **Explicitly rejected:** persistent parsed-workbook storage, distributed
  caches, filesystem watchers, a second `AnalysisStore`, a generic recovery
  framework, a generic graph engine, a new orchestration pattern, immediate
  reference-counted cache ownership, and a statistics platform.

The plan treats timing as secondary to structural proof. A workload cannot pass
because a status label stayed unchanged; mandatory workloads must exist, run,
prove correctness, and report their exact measured path.

## Implementation Outcomes

### Exact analytical and reuse identity

Power BI calculations retain the selected immutable period specification from
contract parsing through labels, numeric windows, and evidence ranges. Explicit
column mappings are validated against the table that consumes them. Each stage
gets all applicable global contracts plus same-domain overrides, and contract
changes invalidate only the consuming stage and stale declared descendants.

### Uniform bounded lifecycle

Admission validates metadata without constructing execution resources. Runtime
activation creates one run-owned `CapabilityScope` and registers every resource
immediately. Caller cancellation remains `asyncio.CancelledError` while worker,
cleanup, and repeated-cancellation settlement completes. Warm cache hits honor
cancellation, and direct outputs pass the same result bounds as aggregate
outputs.

### Real run-owned workbook reuse

The repeated investigation workflow consumes an existing `WorkbookContext` when
one is supplied. Identical source/view requests reuse the pinned snapshot,
material view, provenance, and authority without recapture, rehash, parse, or
authority re-registration. Changed briefs recompute brief-dependent analysis
without reusing analytical judgment. Cached views cannot outlive the authority
needed to validate their ancestry.

### Deletion and truthful proof

Synthesis uses one memoized dependency pass, counts meaningful bounded work,
and either yields cooperatively or documents an explicit bounded cancellation
latency guarantee. Stage fingerprints and adapter signature metadata are
computed once. New benchmark workloads are mandatory by name, timing paths are
reported separately, small samples use median/p90/max or a meaningful sample
count, and the final acceptance evidence is one concise matrix.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-backend-verification`, `skill-performance-optimization`, `skill-code-standards`, `skill-verification-before-completion`, `skill-using-git-worktrees`
- Isolation: dedicated native Git worktree from `origin/main@0fa7e3b`; preserve the current dirty primary checkout and its unrelated artifacts
- Commit policy: `no commits during execution`; commit, push, pull request, merge, and cleanup require a later explicit Git disposition
- Preauthorized local actions: inspect source and tests, edit declared files, run declared local tests, run declared local benchmarks, and write this Git-tracked plan
- User-approval actions: commits, pushes, pull requests, merges, branch/worktree cleanup, destructive recovery, external writes, and discarded unrelated artifacts
- Parallel ownership: none; tasks intentionally share runtime and contract owners
- Semantic dependencies: Task 2 can be reasoned about independently of Task 1;
  Task 3 depends on the run-owned lifecycle boundary; Task 4 depends only on
  the result-boundary behavior it consumes; Task 5 depends on the evidence
  emitted by the earlier tasks.
- Edit order: keep Tasks 1–2 as Patch A, Tasks 3–4 as Patch B, then Task 5 as
  Patch C because shared files make sequential edits safer than parallel edits.

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/next-optimization-pass`
- Base commit: `origin/main@0fa7e3b776790f9255d78e8e8d07d0e5c484866f`
- Expected workspace: `dedicated clean worktree; current primary checkout retains unrelated untracked artifacts`
- Next action: `none; implementation and verification complete; Git disposition remains separately authorized`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `complete` | dedicated worktree | `codex` | none | analytical contract and invalidation regressions | focused pytest suite and compileall PASS |
| Task 2 | `complete` | dedicated worktree | `codex` | none; execute after Task 1 only when shared-file edit order requires it | lifecycle and bounded-output regressions | focused pytest suite and compileall PASS |
| Task 3 | `complete` | dedicated worktree | `codex` | Task 2 | repeated-workflow and authority-lifetime reuse proof | focused pytest suite and compileall PASS |
| Task 4 | `complete` | dedicated worktree | `codex` | Task 2 for result-boundary behavior; execute after Task 3 only when shared-file edit order requires it | synthesis, fingerprint, and adapter-inspection regressions | focused pytest suite and compileall PASS |
| Task 5 | `complete` | dedicated worktree | `codex` | Tasks 1–4 | mandatory benchmark matrix and full verification | frozen external harness comparator PASS; full pytest, compileall, Markdown links, and diff checks PASS |

## Task Breakdown

### Task 1: Close exact analytical identity and contract invalidation

**Purpose:**
- Make period selection, table mappings, effective contracts, fingerprints, and downstream invalidation obey the same stage-scoped analytical meaning.

**Specification Coverage:**
- Preserve the parsed `_PeriodSpec` selected by baseline/comparison input instead of reducing it to a year and rescanning contract periods.
- For each table, derive the canonical fields that table consumes, select only
  mappings whose canonical keys are in that set, validate those mapped source
  columns against that table, apply the mappings, then validate required
  canonical fields. Never validate every brief mapping against every table.
- Resolve `(stage_id, domain)` overrides over `GLOBAL_SCOPE` independently for every stage.
- Keep domain-only lookup out of stage execution identity.
- When an effective contract changes, the consuming stage is always stale. A
  downstream stage is stale only when the dependency input identity it consumes
  changes; do not stale a branch merely because an ancestor reran.

**Files And Symbols:**
- Inspect: `src/foresight_os/domain/analysis_inputs.py:_PeriodSpec`, `AnalysisInputContract`, `NormalizedIntent.contract_for_domain`, `normalize_work_brief`
- Modify: `src/foresight_os/analysis/powerbi_strategic_portfolio.py:_period_window`, `_period_label`, `analyze_powerbi_strategic_portfolio`
- Modify: `src/foresight_os/analysis/workbook_inputs.py:validate_mapping_targets`, `apply_column_mappings`; add one table-local mapping helper in this owner if the existing pair cannot express exact-or-fail semantics
- Modify: `src/foresight_os/analysis/portfolio_resilience.py:analyze_portfolio_resilience`, `src/foresight_os/analysis/supplier_resilience.py:analyze_supplier_resilience`, `src/foresight_os/analysis/technology_radar.py:analyze_technology_radar`, `src/foresight_os/analysis/ev_capacity_investment.py:analyze_ev_capacity_investment`, `src/foresight_os/analysis/powerbi_strategic_portfolio.py:analyze_powerbi_strategic_portfolio`
- Modify: `src/foresight_os/controller/policy.py:_recipe_for_patterns`, `stage_analysis_domains`
- Inspect and modify: `src/foresight_os/runtime/execution_gate.py:_preflight_recipe`, `ExecutionGate.execute`; `src/foresight_os/runtime/workflow.py:run_recipe_async` stage input construction and reuse/invalidation dispatch
- Verify: `tests/test_analysis_input_contract.py`, `tests/test_brief_portability.py`, `tests/test_stage_inputs.py`, `tests/test_selective_reuse.py`, `tests/test_execution_gate.py`

**Dependencies:**
- Base source is `origin/main@0fa7e3b`; use the existing private `_PeriodSpec` and `AnalysisInputContract` rather than creating a public period hierarchy or new contract schema.

**Steps:**
- [ ] Step 1: Trace each Power BI baseline/comparison value to its current `_period_window` call and change the calculation path to carry the selected `_PeriodSpec` directly; update labels and evidence ranges together.
- [ ] Step 2: Replace union-of-workbook-header validation with a table-local helper in all five production XLSX analyzers: derive consumed canonical keys, select the matching mapping subset, validate source headers on that table, apply mappings, then enforce canonical required columns.
- [ ] Step 3: Add one private effective-contract projection per stage, use it for `analysis_domains` and fingerprints, and remove the branch where the presence of any scoped contract suppresses unrelated global domains.
- [ ] Step 4: Reconcile reuse/invalidation decisions with the effective contract projection and declared dependency graph; always stale the consuming stage, stale descendants only when their consumed dependency identity changes, and preserve unrelated branches and complete overrides.
- [ ] Step 5: Add same-year month, cross-year/range, table-local mapping, global fallback, override replacement, and selective invalidation regressions.

**Verification:**
- [ ] `python -m pytest -q tests/test_analysis_input_contract.py tests/test_brief_portability.py tests/test_stage_inputs.py tests/test_selective_reuse.py tests/test_execution_gate.py`
- Expected: same-year periods retain distinct labels/months/numeric results/evidence ranges; unrelated mapped tables fail closed; global and stage contracts resolve independently; only consuming and dependent stages become stale.

**Exit Criteria:**
- All five analyzers enforce exact table-local mappings, Power BI same-year periods cannot alias, and stage contract fingerprints represent the effective contract set used by each stage.

### Task 2: Close cancellation, admission, and direct-output lifecycle boundaries

**Purpose:**
- Make admission metadata-only and make worker settlement, warm reads, and direct output paths obey the same lifecycle and safety guarantees.

**Specification Coverage:**
- Preflight checks definitions, bindings, configuration, authorization, and factory callability without creating resources or scopes that execution will discard.
- Runtime creates one run-owned scope and registers activated resources immediately.
- Original caller cancellation survives worker errors, cleanup errors, and repeated cancellation during settlement.
- The blocking worker uses a thread-safe cancellation signal. The tool wrapper
  settles the worker only; `CapabilityScope` and run cleanup own resource
  cleanup separately.
- `WorkbookContext.read()` checks open state and cancellation before returning a warm cache hit.
- Single-output Direct execution passes payload, record, relationship, alias, dependency, depth, and structural bounds before returning.
- The blocking cancellation regression executes its async scenario exactly once and verifies the production worker-error path.

**Files And Symbols:**
- Inspect and modify: `src/foresight_os/runtime/execution_gate.py:_preflight_recipe`, `ExecutionGate.admit`
- Inspect and modify: `src/foresight_os/runtime/capabilities.py:prepare_capability_context`, `CapabilityResolver`, `_instrumented_dispatch`, `CapabilityScope`
- Inspect and modify: `src/foresight_os/runtime/local_toolbelt.py:WorkbookContext.read`, `_check_cancel`
- Inspect and modify: `src/foresight_os/runtime/workflow.py:_synthesize_stage_outputs`, `dispatch_stage`, `_run_native_stage`
- Verify: `tests/test_runtime_boundaries.py:test_blocking_capability_runs_off_event_loop_and_settles_cancellation`, `tests/test_capabilities.py`, `tests/test_local_toolbelt.py`, `tests/test_orchestration_patterns.py`

**Steps:**
- [ ] Step 1: Split metadata admission from activation in the existing capability path; make `_preflight_recipe` call admission-only resolution and make `run_recipe_async` perform the sole activation.
- [ ] Step 2: Use a thread-safe `threading.Event` for the blocking worker's cancellation signal. Let the tool wrapper settle the worker only; keep `CapabilityScope` and run cleanup responsible for resource cleanup. Absorb repeated cancellation until worker settlement completes, retain secondary failures diagnostically, and re-raise the original `CancelledError`.
- [ ] Step 3: Add `ensure_open()` and `_check_cancel()` before `WorkbookContext` warm-cache lookup and retain transactional rollback behavior on cancellation.
- [ ] Step 4: Factor structural and budget preflight from multi-output merge, run that common validation once, then return one validated output or merge multiple validated outputs; preserve Direct topology without bypassing safety limits.
- [ ] Step 5: Fix the named cancellation test so it calls `asyncio.run(scenario())` once, remove the duplicate scenario execution from the adjacent test, and add repeated-cancel plus worker/cleanup-failure cases.

**Verification:**
- [ ] `python -m pytest -q tests/test_runtime_boundaries.py tests/test_capabilities.py tests/test_local_toolbelt.py tests/test_orchestration_patterns.py tests/test_result_committer.py`
- Expected: admission resource-factory counters remain zero; execution creates one resource and one scope owner; cancelled callers receive `asyncio.CancelledError`; warm reads reject cancellation; Direct oversize output fails with the typed boundary error.

**Exit Criteria:**
- No resource is created during admission, cancellation remains caller-owned through settlement, warm reads are cancellation-consistent, and every topology crosses one bounded canonical-result boundary.

### Task 3: Connect run-owned workbook reuse to repeated investigations

**Purpose:**
- Make the existing bounded `WorkbookContext` the source-reuse boundary for repeated high-level analyses without caching brief-dependent analytical judgments.

**Specification Coverage:**
- `run_xlsx_finding_workflow` accepts an existing `WorkbookContext` and does not recapture, rehash, or reparse an identical source/view in that context.
- Material extraction/provenance reuse remains separate from entity filters, period selection, mappings, assumptions, calculations, and recommendations.
- Acceptance/currentness checks remain explicit at the acceptance boundary; analysis does not continuously rehash the live path.
- A cached material view cannot remain trusted while its required authority is unavailable; eviction either preserves authority or invalidates/rematerializes the view.
- Analyst and independent validator share deterministic extraction but not analytical judgment.
- Supplying both `snapshot=` and `workbook_context=` at the generic XLSX
  workflow boundary is rejected; the context's pinned snapshot is the only
  accepted source when a context is supplied.

**Files And Symbols:**
- Inspect and modify: `src/foresight_os/analysis/evidence_workflow.py:run_xlsx_finding_workflow`
- Inspect and modify: `src/foresight_os/analysis/independent_validation.py:read_validation_source`, `run_independent_validation`
- Inspect and modify: `src/foresight_os/runtime/local_toolbelt.py:WorkbookContext`, `WorkbookReadCache`, `AuthorityIndex`
- Inspect and modify only where context propagation requires it: `src/foresight_os/analysis/portfolio_resilience.py:run_portfolio_resilience_workflow`, `src/foresight_os/analysis/supplier_resilience.py:run_supplier_resilience_workflow`, `src/foresight_os/analysis/technology_radar.py:run_technology_radar_workflow`, `src/foresight_os/analysis/ev_capacity_investment.py:run_ev_capacity_investment_workflow`, `src/foresight_os/analysis/powerbi_strategic_portfolio.py:run_powerbi_strategic_portfolio_workflow`
- Verify: `tests/test_brief_portability.py`, `tests/test_local_toolbelt.py`, `tests/test_runtime_boundaries.py`, `evaluation/probes/run_optimization_probe.py`

**Steps:**
- [ ] Step 1: Add an optional `WorkbookContext` parameter at the generic XLSX workflow boundary and thread it through source read, deterministic analysis, and independent validation. Reject supplying both `snapshot=` and `workbook_context=`; require callers to use the context's pinned snapshot instead.
- [ ] Step 2: Ensure the workflow reuses material extraction while recomputing changed brief semantics; add a two-brief same-source test and an analyst/validator same-view test.
- [ ] Step 3: Add an authority-eviction pressure regression that proves a warm trusted calculation either succeeds with retained authority or rematerializes safely.
- [ ] Step 4: Keep currentness as an explicit acceptance/publication check and record stale-source behavior without invalidating the historical pinned snapshot.
- [ ] Step 5: Prove zero new capture/hash/parse/load and zero authority re-registration for identical warm views with monkeypatched capture/hash/parse/load/registration functions and existing cache/authority stats; do not add production metrics solely for this proof. Prove changed-brief reuse through at least one real domain analysis contract.

**Verification:**
- [ ] `python -m pytest -q tests/test_brief_portability.py tests/test_local_toolbelt.py tests/test_runtime_boundaries.py tests/test_independent_validation.py`
- Expected: repeated same-view analysis reports one capture, one source hash, one parse, and at least one cache hit; changed briefs recompute analysis; validator reuse preserves independent review; authority eviction never permits an untrusted cache hit.

**Exit Criteria:**
- The production repeated-investigation path uses one run-owned context and demonstrates structural reuse without conflating material source reuse with analytical-result reuse.

### Task 4: Delete duplicated synthesis and dispatch work

**Purpose:**
- Make synthesis complexity and runtime metadata work predictable without adding a new graph or identity framework.

**Specification Coverage:**
- Dependency validation uses `UNSEEN`/`VISITING`/`DONE` memoized traversal for cycle detection and depth in O(V+E) over computational/reference dependencies. Topological ordering is computed only if the existing synthesis path consumes it.
- Cycles fail with typed `DEPENDENCY_CYCLE`; analytical/domain relationships are not misclassified as computational dependencies.
- The synthesis-work limit counts record inspection, edge traversal, relationship validation, alias resolution, and canonical hashing.
- Long synthesis either yields after bounded batches and observes cancellation or explicitly reports a bounded non-interruptible cancellation guarantee.
- Production dispatch computes semantic and execution fingerprints once and reuses them for cache lookup, receipts, invalidation, and metrics.
- Adapter parameter support is inspected once at binding/instrumentation, not with `inspect.signature` on every inline invocation.

**Files And Symbols:**
- Inspect and modify: `src/foresight_os/runtime/workflow.py:_synthesize_stage_outputs`, `_expand_dependency_records`, `_stage_cache_key`, `_stage_fingerprints`, `run_recipe_async`, dispatch capability injection
- Inspect and modify: `src/foresight_os/runtime/capabilities.py:_instrumented_dispatch`, `instrument_tool`, binding metadata creation
- Verify: `tests/test_orchestration_patterns.py`, `tests/test_stage_inputs.py`, `tests/test_selective_reuse.py`, `tests/test_runtime_boundaries.py`

**Steps:**
- [ ] Step 1: Build one memoized dependency graph from canonical record IDs and computational/reference edges only. Explicitly exclude `relationship_ids`, `from_id`, and `to_id` from computational cycle/depth traversal; compute topological order only if the existing synthesis path consumes it. Enforce depth and typed cycle errors in that pass.
- [ ] Step 2: Rename or reinterpret the existing normalization-operation limit as synthesis work and increment it at meaningful inspection, traversal, validation, alias, and hash checkpoints.
- [ ] Step 3: Keep bounded synchronous synthesis as the default and measure worst-case cancellation latency. Add cooperative async batching only if that measured latency justifies it; otherwise document and test the explicit bounded cancellation-delay guarantee instead of claiming interruptibility.
- [ ] Step 4: Remove the production `_stage_cache_key` plus `_stage_fingerprints` duplicate call and pass the computed fingerprint bundle through all consumers.
- [ ] Step 5: Cache adapter parameter acceptance in the existing binding/instrumentation path and remove per-call reflection where metadata is already available.

**Verification:**
- [ ] `python -m pytest -q tests/test_orchestration_patterns.py tests/test_stage_inputs.py tests/test_selective_reuse.py tests/test_runtime_boundaries.py`
- Expected: shared dependency graphs scale linearly, cycles produce `DEPENDENCY_CYCLE`, work budgets fail closed, cancellation behavior matches the documented guarantee, fingerprint call counts are one per stage, and signature inspection is one per binding.

**Exit Criteria:**
- Synthesis, fingerprinting, and adapter dispatch no longer repeat avoidable graph/reflection work, and their bounded behavior is proven by focused tests rather than inferred from timing alone.

### Task 5: Evidence and safe compatibility deletion

**Purpose:**
- Complete only the compatibility cleanup that has migrated consumers, then make benchmark acceptance mandatory by workload and honest about measured paths.

**Specification Coverage:**
- New recipes write only `RecipeStage.analysis_domains`; `metadata["analysis_contract_domains"]` remains read-only load compatibility until no consumers remain.
- Remove duplicate producers only after a consumer search proves that the canonical representation is the sole normal path. Do not make `TaskShape` migration, `WorkBrief.analysis_inputs` retyping, or global-authority retirement completion gates.
- Mandatory workloads are named, executed, correctness-checked, and rejected when missing or failed.
- Cancellation benchmark reproduces a worker-raised secondary error while caller receives `CancelledError`.
- Timing reports distinguish direct cold parse, same-view warm read, repeated investigation, and analyst-validator reuse; small samples report median/p90/max or use a meaningful sample count.
- Timing, allocation, correctness, and soak evidence remain separate, and one concise acceptance matrix records limitations.

**Files And Symbols:**
- Inspect and modify: `src/foresight_os/controller/recipes.py:ExecutionRecipe.from_dict`, `RecipeStage.to_dict`, `src/foresight_os/controller/policy.py:_recipe_for_patterns`, `select_recipe`
- Optional follow-up only: `src/foresight_os/controller/task_shape.py:TaskShape`, `src/foresight_os/runtime/local_toolbelt.py:AuthorityIndex` and global authority compatibility paths
- Optional follow-up only: `src/foresight_os/domain/models.py:WorkBrief`, `src/foresight_os/domain/validation.py:validate_work_brief`, `src/foresight_os/domain/analysis_inputs.py:normalize_work_brief`
- Inspect and modify: `evaluation/probes/run_optimization_probe.py:_cancelled_read_workload`, `_repeated_workflow`, `_retained_context_workloads`, `_multi_workbook_soak`, `_measure_workbook`
- Inspect and modify: `evaluation/probes/optimization_measurement.py` receipt schema/builders and `evaluation/probes/compare_optimization_receipts.py:_validate_measurement_receipt`, `compare`
- Verify: `tests/test_stage_inputs.py`, `tests/test_controller_selection.py`, `tests/test_analysis_input_contract.py`, `tests/test_optimization_measurement.py`, `evaluation/README.md`

**Steps:**
- [x] Step 1: Remove duplicate legacy metadata from new recipe serialization only where a consumer-migration search proves that `RecipeStage.analysis_domains` is the sole normal producer/consumer path; preserve one-time load translation for legacy persisted recipes.
- [x] Step 2: Add the named mandatory workload set: `cold_workbook`, `same_view_repeat`, `different_selection`, `analyst_validator_reuse`, `repeated_investigation`, `large_retained_context`, `multi_workbook`, and `blocking_cancellation`.
- [x] Step 3: Make missing, unexecuted, incorrect, or failed workloads fail comparator acceptance; make the cancellation workload use the production worker-error semantics.
- [x] Step 4: Separate direct-read, warm-read, repeated-investigation, and validator-reuse timing fields; replace the small-sample maximum masquerading as p95 with median/p90/max or a meaningful sample count.
- [x] Step 5: Freeze one benchmark harness and protocol before comparison, including fixture, limits, warmups, measured runs, environment, and host conditions. Run that exact harness against both base and release; do not run the base tree's old probe against a modified release probe.
- [x] Step 6: Write one final acceptance matrix with executable evidence, result, and limitation; keep raw JSON, logs, and measurement state in an external temporary directory, never in a Git worktree.

**Optional follow-up, not completion-critical:**
- Migrate incidental `TaskShape` topology inference.
- Retype `WorkBrief.analysis_inputs` and update its schemas and round-trip tests.
- Retire process-global authority fallback after explicit-context migration is complete.

**Verification:**
- [x] Materialize the frozen harness outside both Git worktrees and run the same measurement implementation, fixture, limits, warmups, measured runs, environment, and host conditions against `origin/main@0fa7e3b` and the final source tree.
- [x] `python -m pytest -q tests/test_stage_inputs.py tests/test_controller_selection.py tests/test_analysis_input_contract.py tests/test_optimization_measurement.py`
- [x] Run the frozen harness with external outputs such as `$TEMP_DIR/foresight-os-next-optimization/baseline.json` and `$TEMP_DIR/foresight-os-next-optimization/release.json`; compare those receipts with the repository comparator without writing raw artifacts under `work/`.
- Expected: all mandatory workloads execute and pass correctness; unavailable/noisy timing is `NOT_MEASURED`, failed workloads reject the comparison, and no compatibility path remains a new-output producer after its consumers migrate.

**Exit Criteria:**
- Canonical representations are the only normal producers, safe compatibility reads are bounded, mandatory benchmark evidence is truthful, and the final receipt does not claim more than the measured path proves.

## Verification

Final artifact-level verification must run from the clean implementation worktree
after Tasks 1–5 and before any branch disposition:

- [x] `python -m pytest -q`
- [x] `python -m compileall -q src tests evaluation`
- [x] `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- [x] `python -m pytest -q tests/test_markdown_links.py`
- [x] Materialize the frozen benchmark harness outside both Git worktrees and run
  that same measurement implementation against `origin/main@0fa7e3b` and the
  final source tree, with the same fixture, environment, limits, warmups,
  measured runs, and host conditions.
- [x] Write raw JSON, logs, and measurement state beneath an external temporary
  directory such as `$TEMP_DIR/foresight-os-next-optimization/`; do not use
  `work/next-optimization/` for benchmark artifacts.
- [x] Compare the two external receipts with
  `evaluation/probes/compare_optimization_receipts.py` after both runs finish.
- [x] `git diff --check`
- [x] Final diff inspection against `origin/main@0fa7e3b`, including confirmation that raw benchmark samples, generated measurement state, credentials, and unrelated primary-checkout artifacts are absent from the patch

Expected final evidence:

| Requirement | Executable evidence | Result | Limitation |
| --- | --- | --- | --- |
| Exact same-year periods | Power BI regression | `PASS` | none |
| Table-local mappings | five analyzer portability/mapping tests | `PASS` | none |
| Global/stage fallback and selective invalidation | recipe/reuse regressions | `PASS` | none |
| Blocking cancellation | real worker-error boundary test | `PASS` | none |
| Metadata-only admission | resource-factory counter | `PASS` | none |
| Direct output bounds | single-output oversize test | `PASS` | none |
| Warm reuse | context counters | `PASS` | none |
| Repeated workflow reuse | production workflow workload | `PASS` | none |
| Authority eviction safety | retained-authority regression | `PASS` | none |
| Synthesis cancellation | cooperative-yield or bounded-delay proof | `PASS` | documented guarantee |
| Warm/repeated timing | labeled benchmark fields | `VERIFIED` or `NOT_MEASURED` | noisy host permitted |

## Completion Criteria

The plan is ready for completion verification when:

1. Every mandatory evidence gate passes against the exact final source tree; task-local verification items are recorded as supporting evidence.
2. Exact periods, table-local mappings, effective contract fallback, and selective invalidation are proven by focused tests.
3. Admission creates no execution resource, one run owns activated resources, and caller cancellation survives worker and cleanup settlement.
4. Direct outputs, synthesis dependencies, and cancellation behavior are uniformly bounded.
5. Repeated investigations reuse one `WorkbookContext` for identical material views while recomputing changed analytical meaning.
6. Authority lifetime, currentness, provenance, and independent validation remain explicit and truthful.
7. Fingerprints and capability signature metadata are computed once per stage/binding.
8. Normal recipe production has one analysis-domain representation; any remaining `TaskShape`, `WorkBrief.analysis_inputs`, or process-global-authority cleanup is explicitly recorded as deferred rather than silently required.
9. All mandatory benchmark workloads execute and pass correctness gates; timing claims use exact path labels and honest limitations.
10. Full verification passes, the final acceptance matrix is recorded, plan deviations and deferrals are reconciled, and no unrelated dirty artifacts are staged.

The plan is complete when every mandatory evidence gate passes against the exact
final source tree. A verification workflow or skill may execute and record
those checks, but it is not the source of truth. Branch commit, push, pull
request, merge, and cleanup remain separate Git disposition actions.

## Approved Deferrals

- No persistent parsed-workbook database, distributed cache, filesystem watcher,
  source-version registry, second `AnalysisStore`, generic recovery framework,
  generic graph engine, new orchestration pattern, or reference-counting cache
  architecture unless a future structural regression proves the current
  capacity/lifetime policy insufficient.
- No `repr()` weight-estimator rewrite without measured evidence that it affects
  the warm path or retained-state budget.
- No broad controller rewrite in Patch A or Patch B; topology simplification is
  restricted to the migrated compatibility cleanup in Patch C.
- No performance claim is required when the host cannot measure the path
  reliably; the result must be `NOT_MEASURED`, not a fabricated speedup.
