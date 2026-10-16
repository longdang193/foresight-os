---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: foresight-os-runtime-consolidation
targets:
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/runtime/capabilities.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/runtime/participants.py
  - src/foresight_os/controller/policy.py
  - src/foresight_os/controller/recipes.py
  - src/foresight_os/domain/analysis_inputs.py
  - src/foresight_os/analysis/workbook_inputs.py
  - src/foresight_os/analysis/portfolio_resilience.py
  - src/foresight_os/analysis/supplier_resilience.py
  - src/foresight_os/analysis/technology_radar.py
  - src/foresight_os/analysis/ev_capacity_investment.py
  - src/foresight_os/analysis/powerbi_strategic_portfolio.py
  - src/foresight_os/analysis/foresight_validator.py
  - src/foresight_os/runtime/metrics.py
  - tests/test_local_toolbelt.py
  - tests/test_capabilities.py
  - tests/test_runtime_boundaries.py
  - tests/test_analysis_input_contract.py
  - tests/test_brief_portability.py
  - tests/test_case_portability.py
  - tests/test_technology_powerbi_validator.py
  - tests/test_supplier_and_ev_resilience.py
  - tests/test_orchestration_patterns.py
  - tests/test_result_committer.py
  - tests/test_controller_selection.py
  - tests/test_stage_inputs.py
  - tests/test_selective_reuse.py
  - tests/test_execution_gate.py
  - tests/test_skills.py
  - tests/test_optimization_measurement.py
  - evaluation/probes/optimization_measurement.py
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/compare_optimization_receipts.py
  - docs/architecture.md
  - docs/extending.md
  - evaluation/README.md
---

# ForesightOS Runtime Consolidation Plan

## Goal

Deliver the next bounded runtime-consolidation increment after PR #25. Preserve
exact source provenance, formula/cache semantics, immutable analytical identity,
independent validation, canonical persistence, invalidation, human acceptance,
and the existing Microsoft Agent Framework boundary while closing the remaining
trust, cancellation, workbook-reuse, semantic-contract, synthesis, and owner-
duplication gaps identified in the supplied verdict.

The implementation starts from merged origin/main at c8c17db0663fbbcab696215308aa5b7f386bb2b4 and runs in a new isolated worktree. The existing primary checkout contains unrelated untracked artifacts and must remain untouched.

## Review Of The Verdict

### Adopted conclusions

- Caller-controlled material fingerprints cannot authorize analysis-cache hits.
- WorkbookContext is the run-local owner for source snapshots, views, bounded caches, authority state, and retained-resource accounting.
- Cancellation preserves the caller-visible asyncio.CancelledError after worker settlement and cleanup diagnostics.
- Capability admission is metadata-only; resource activation occurs inside an owned cleanup boundary.
- Domain contracts are validated before expensive capture where the required facts are brief-local, and source-dependent mappings fail exact-or-fail after schema discovery.
- Period meaning is represented and validated explicitly rather than reduced to month numbers or silently degraded ranges.
- Synthesis is bounded, indexed, cancellation-aware, typed, and participant-order independent.
- NormalizedIntent is the authoritative input to recipe selection; Direct and Sequential are the ordinary execution paths.
- Performance claims require matched production-path timing and allocation/resource evidence; structural counter evidence is not a latency claim.

### Scoped corrections

- This plan does not introduce a source registry, parsed-workbook database, second durable store, generic recovery engine, new orchestration pattern, filesystem watcher, distributed cache, or another normalization layer.
- AnalysisStore remains the durable analytical authority. CapabilityScope and WorkbookContext remain runtime owners; no parallel ownership model is added.
- Backward-compatible serialized contract fields and recipe fields remain stable while typed internal accessors become authoritative.
- Compatibility behavior remains available only for omitted inputs. Explicit periods, mappings, policies, and conversions execute exactly or fail.
- Routine raw verification logs are not tracked. Each release keeps one concise receipt; CI and local command output remain sufficient for detailed diagnostics.
- Persistent parsed-workbook retention remains deferred until the production benchmark proves that source parsing, rather than orchestration or downstream calculation, is the dominant remaining cost.

### Release order

Release 1: Correctness → Release 2: Workbook reuse → Release 3: Execution simplification → Release 4: Synthesis and consolidation.

No later release starts until its predecessor's focused proof and exit criteria
are satisfied. A failed correctness gate stops the sequence instead of being
converted into an optimization claim.

## Implementation Outcomes

### Trusted identity and lifecycle safety

TypedTable material identity is derived by the host from accepted content and
provenance. Supplied fingerprints, caller IDs, and dataclasses.replace()
retained identities cannot authorize stale analysis-cache hits. Cancellation,
resource activation, cleanup, and publication failures preserve primary failure
semantics and leave no reusable partial state.

### Brief-portable workbook analysis

The six workbook analyzers and the validator can consume one optional
WorkbookContext, validate brief-local semantics before capture, reuse an
unchanged extracted view across briefs, reject missing explicit mappings, and
preserve exact period meaning and provenance.

### Bounded execution and synthesis

Synthesis performs one bounded indexed transformation with typed recovery,
material-conflict preservation, canonical dependency references, participant-
local correction, and cancellation checkpoints. Recipe selection consumes one
immutable NormalizedIntent and defaults routine work to Direct or Sequential.
Stage-to-analysis-contract associations are explicit, and stage identity includes
only direct and declared dependency contracts.

### Measured consolidation

The production investigation path has matched cold/warm, changed-brief,
different-selection, multi-sheet, cancellation, multi-workbook, repeated-run,
and large-context warm-hit measurements. Wall-clock timing is separate from
allocation profiling, and receipts distinguish PASS, FAILED, NOT_MEASURED,
and DEFERRED outcomes.

## Execution Approach

- Mode: inline sequential
- Coordination: git-tracked
- Required skills: skill-writing-plans, skill-plan-document-reviewer, skill-executing-plans, skill-backend-verification, skill-test-driven-development, skill-performance-optimization, skill-code-standards, skill-verification-before-completion, skill-finishing-a-development-branch
- Isolation: new native worktree from origin/main at the recorded base commit
- Commit policy: no commits during execution unless separately approved
- Preauthorized local actions: inspect declared source/tests/docs, edit declared implementation and test files in the isolated worktree, run declared local checks and probes, write one concise release receipt per release, preserve unrelated primary-checkout files
- User-approval actions: commit, push, pull request creation or update, merge, provider calls, destructive cleanup, deletion of compatibility data, and removal of any worktree or branch
- Parallel ownership: none; identity, lifecycle, workbook, synthesis, and controller changes share runtime contracts and remain serialized
- Sequential fallback: execute Tasks 1 through 8 in dependency order

## Coordination State

- Coordination owner: single lead controller
- Coordination schema: 2
- Branch: codex/foresight-os-runtime-consolidation
- Base commit: c8c17db0663fbbcab696215308aa5b7f386bb2b4 (origin/main)
- Expected workspace: isolated worktree with no unrelated changes; preserve all existing primary-checkout untracked artifacts
- Next action: preserve the verified final tree for the separately authorized Git disposition
- Blockers: none; publication, merge, cleanup, and compatibility deletion remain separately authorized

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | complete | isolated | lead controller | none | base and matched baseline receipt | work/runtime-consolidation-baseline/receipt.md |
| Task 2 | complete | isolated | lead controller | Task 1 | identity and lifecycle boundary tests | work/runtime-consolidation-release-1/receipt.md |
| Task 3 | complete | isolated | lead controller | Tasks 2 | brief portability and exact-mapping tests | work/runtime-consolidation-release-1/receipt.md |
| Task 4 | complete | isolated | lead controller | Tasks 2–3 | workbook-context integration tests | work/runtime-consolidation-release-2/receipt.md |
| Task 5 | complete | isolated | lead controller | Task 4 | matched production-path benchmark | work/runtime-consolidation-release-2/receipt.md |
| Task 6 | complete | isolated | lead controller | Tasks 4–5 structural/correctness gate | normalized-intent, topology, and relevant-contract tests | work/runtime-consolidation-release-3/receipt.md |
| Task 7 | complete | isolated | lead controller | Task 6 | typed synthesis and owner-cleanup tests | work/runtime-consolidation-release-4/receipt.md |
| Task 8 | complete | isolated | lead controller | Task 7 | final verification and plan reconciliation | work/runtime-consolidation-final/receipt.md |

## Task Breakdown

### Task 1: Freeze the current base and establish matched evidence

Purpose:
- Reconcile the verdict with merged origin/main, reproduce the two highest-risk failures, and define release gates without touching unrelated primary-checkout files.

Task Function:
- Bounded baseline and owner-map verification.

Template Profile:
- Controller-selected: none (lead controller)
- Selection basis: current primary checkout is dirty and the plan spans shared runtime owners; one controller must establish the authoritative base and evidence.

Validator Profile:
- Controller-selected: none

Specification Coverage:
- Measurement-first execution, trust-boundary correctness, preserved invariants, explicit non-goals, and primary-checkout protection.

Required Skills:
- skill-using-git-worktrees, skill-performance-optimization, skill-code-standards

Files And Symbols:
- Inspect: src/foresight_os/runtime/local_toolbelt.py:TypedTable, WorkbookReadCache, WorkbookContext, data_analysis
- Inspect: src/foresight_os/runtime/capabilities.py:CapabilityScope, CapabilityResolver, prepare_capability_context
- Inspect: src/foresight_os/runtime/workflow.py:_synthesize_stage_outputs, _stage_fingerprints, _stage_cache_key, run_recipe_async
- Inspect: src/foresight_os/domain/analysis_inputs.py:AnalysisInputContract, NormalizedIntent, normalize_work_brief
- Inspect: src/foresight_os/controller/policy.py:select_recipe
- Verify: origin/main resolves to c8c17db0663fbbcab696215308aa5b7f386bb2b4

Dependencies:
- Approved plan and isolated worktree creation.

Authority:
- Preauthorized local actions: inspect the recorded base, create the named isolated worktree, run focused read-only probes, and write the baseline receipt.
- Stop for: base drift, missing canonical owners, a new failure outside the verdict's stated scope, or any request to mutate the primary checkout.

Steps:
- [x] Step 1: Create codex/foresight-os-runtime-consolidation from origin/main and record the exact base SHA.
- [x] Step 2: Reproduce the stale-cache case using two externally/coerced TypedTable values with the same caller ID and supplied fingerprint but different rows; reproduce dataclasses.replace(rows=...) identity reuse if present.
- [x] Step 3: Execute the existing cancellation scenario in tests/test_runtime_boundaries.py and record whether the worker/settlement failure replaces asyncio.CancelledError.
- [x] Step 4: Reproduce one explicit missing-mapping failure and one explicit period failure (reversed, cross-year, or unsupported granularity) to establish the current brief-validation boundary before Task 3.
- [x] Step 5: Run python -m pytest -q tests/test_optimization_measurement.py tests/test_controller_selection.py tests/test_execution_gate.py tests/test_local_toolbelt.py tests/test_runtime_boundaries.py and record baseline versions and limitations.
- [x] Step 6: Record one concise baseline receipt; do not add raw command logs to Git.

Verification:
- [x] git rev-parse origin/main and git status --short --branch
- Expected: base is c8c17db0663fbbcab696215308aa5b7f386bb2b4; isolated worktree is clean; primary checkout remains unchanged.
- [x] Baseline stale-cache and cancellation probes
- Expected: reproduced stale-cache, cancellation, mapping, and period behavior is recorded as a baseline failure or explicitly marked not reproduced with the exact environment.

Exit Criteria:
- Base, owner map, focused baseline, and preserved-primary-checkout evidence are recorded in work/runtime-consolidation-baseline/receipt.md.

### Task 2: Close material-identity and lifecycle trust boundaries

Purpose:
- Make host-established identity authoritative and correct cancellation, capability admission, activation, cleanup, and the existing failed-attempt publication boundary.

Task Function:
- Correctness-first boundary hardening with regression proof.

Template Profile:
- Controller-selected: none (lead controller)
- Selection basis: shared runtime boundaries have high blast radius and require serialized implementation with direct failure-path proof.

Validator Profile:
- Controller-selected: none

Specification Coverage:
- Release 1: caller-controlled fingerprints cannot authorize cache hits; cancellation remains primary; no resource is created before an owner exists; the existing rollback boundary prevents failed operations from publishing reusable state.

Required Skills:
- skill-backend-verification, skill-test-driven-development, skill-code-standards

Files And Symbols:
- Modify: src/foresight_os/runtime/local_toolbelt.py:TypedTable.__post_init__, _coerce_typed_table, _stable_material_value, WorkbookReadCache.analysis_key, WorkbookContext.read
- Modify: src/foresight_os/runtime/capabilities.py:CapabilityScope, CapabilityResolver, prepare_capability_context
- Modify: src/foresight_os/runtime/workflow.py:_run_native_stage, _close_agents, run_recipe_async
- Verify: tests/test_local_toolbelt.py, tests/test_capabilities.py, tests/test_runtime_boundaries.py

Dependencies:
- Task 1 baseline and exact current-base owner map.

Authority:
- Preauthorized local actions: modify the listed runtime owners and focused tests; run local backend and lifecycle checks; record the Release 1 receipt.
- Stop for: a required schema/persistence change, an external provider dependency, or a failure that requires discarding accepted source/provenance semantics.

Steps:
- [x] Step 1: Make `material_fingerprint` derived and non-init (`field(init=False)` or the equivalent); have `__post_init__()` always compute it from accepted headers, rows, provenance, measurements, range, sheet, hidden state, related provenance, and one fixed parser/schema identity-version constant. Ignore serialized or caller-supplied fingerprints for authorization; `to_dict()` may emit only the derived value diagnostically.
- [x] Step 2: Ensure `_coerce_typed_table()` never trusts a serialized fingerprint and that `dataclasses.replace()` with changed rows, provenance, range, hidden state, or join-table content receives a new identity while trusted cache lookup remains O(1) after construction. Test same ID plus same supplied fingerprint with changed material, changed provenance/range/hidden state, and join-table identity.
- [x] Step 3: Split capability admission from activation so preflight inspects definitions, bindings, policy, authorization, approval, and static configuration without invoking factories or resource factories. Activate only after an owned CapabilityScope exists and register each resource immediately.
- [x] Step 4: Preserve the original asyncio.CancelledError through worker settlement and cleanup; collect secondary worker/cleanup failures as diagnostics; keep cancellation non-retryable.
- [x] Step 5: Preserve and prove the current rollback boundary: retain failed-attempt diagnostics, keep cancellation and setup/cleanup failures from publishing snapshots, cache entries, authority records, or accepted analytical results, and leave replacement of world-copy rollback to Task 4.

Verification:
- [x] python -m pytest -q tests/test_local_toolbelt.py tests/test_capabilities.py tests/test_runtime_boundaries.py
- Expected: supplied-fingerprint, changed-material, join-identity, cancellation, setup-failure, cleanup-failure, closed-scope, and no-publication regressions pass.
- [x] Direct preflight probe with a counting factory and a scope-close probe
- Expected: preflight invokes zero factories; runtime activation registers and closes every owned resource exactly once.

Exit Criteria:
- No caller-supplied table identity can produce a cache hit; cancellation and cleanup preserve primary failure semantics; failed attempts publish no reusable state; Release 1 receipt records PASS/FAILED/NOT_MEASURED per gate.

### Task 3: Make brief semantics exact and portable

Purpose:
- Validate brief-local semantics before workbook I/O, represent period meaning explicitly, and make explicit mappings and policies exact-or-fail.

Task Function:
- Domain-contract and portability hardening.

Template Profile:
- Controller-selected: none (lead controller)
- Selection basis: domain semantics cross all workbook analyzers but remain owned by the existing input-contract and workbook-input modules.

Validator Profile:
- Controller-selected: none

Specification Coverage:
- Release 1: strict period semantics, exact explicit mappings, omitted-field compatibility only, and analytical meaning preserved across briefs.

Required Skills:
- skill-backend-verification, skill-test-driven-development, skill-code-standards

Files And Symbols:
- Modify: src/foresight_os/domain/analysis_inputs.py:AnalysisInputContract, NormalizedIntent, normalize_work_brief
- Modify: src/foresight_os/analysis/workbook_inputs.py:apply_column_mappings, require_row_columns
- Modify: src/foresight_os/analysis/portfolio_resilience.py:analyze_portfolio_resilience
- Modify: src/foresight_os/analysis/supplier_resilience.py:analyze_supplier_resilience
- Modify: src/foresight_os/analysis/technology_radar.py:analyze_technology_radar
- Modify: src/foresight_os/analysis/ev_capacity_investment.py:analyze_ev_capacity_investment
- Modify: src/foresight_os/analysis/powerbi_strategic_portfolio.py:analyze_powerbi_strategic_portfolio
- Modify: src/foresight_os/analysis/foresight_validator.py:validate_exercises
- Verify: tests/test_analysis_input_contract.py, tests/test_brief_portability.py, tests/test_case_portability.py, tests/test_technology_powerbi_validator.py, tests/test_supplier_and_ev_resilience.py

Dependencies:
- Task 2 identity and failure-boundary behavior.

Authority:
- Preauthorized local actions: modify the existing domain-contract and workbook-input owners, update focused portability tests, and record the Release 1 semantic receipt.
- Stop for: a breaking serialized contract change without compatibility tests, an unsupported domain period granularity, or a requirement for silent legacy fallback on explicit input.

Steps:
- [x] Step 1: Add one private immutable `PeriodSpec` (or equivalent parser API) while preserving serialized brief compatibility. Support `2026`, `2026-03`, and `2026-03:2026-09`; preserve year, month, granularity, start/end, and cross-year meaning; validate ordering and domain-supported granularity before analytical transformation. Do not add public general-purpose period types unless multiple consumers prove the need.
- [x] Step 2: Make each analyzer consume the typed period meaning rather than deriving independent month-number or hard-coded intervals; reject unsupported cross-year or same-year-only requests explicitly.
- [x] Step 3: Add validate_mapping_targets(headers, mappings) and make explicit source mappings fail with stable MISSING_MAPPED_COLUMN errors before default/compatibility values are applied.
- [x] Step 4: Apply the omitted-versus-explicit rule to periods, entity scope, mappings, units/currency, conversion rates, duplicate policy, missing-value policy, required calculations, and validation checks. Reject brief-local invalidity (syntax/order, empty explicit scope, mapping shape, and policy completeness) before source capture; reject source-dependent invalidity (headers, conversion availability, duplicates, missing values, and source-required calculations) after schema discovery but before analytical transformation.
- [x] Step 5: Add exact portability fixtures for missing mappings, empty scope, reordered columns, equivalent reordered meaning, reversed and cross-year periods, unsupported granularity, missing conversion, duplicate records, missing values, totals, scenario calculations, and provenance.

Verification:
- [x] python -m pytest -q tests/test_analysis_input_contract.py tests/test_brief_portability.py tests/test_case_portability.py tests/test_technology_powerbi_validator.py tests/test_supplier_and_ev_resilience.py
- Expected: explicit invalid inputs fail before expensive analysis; accepted briefs preserve exact selected period, entities, mappings, totals, units, and provenance.

Exit Criteria:
- Brief-local invalidity is rejected before capture; source-dependent invalidity is rejected immediately after schema discovery; no explicit input silently falls back to old-fixture behavior.

### Task 4: Make WorkbookContext the production extraction owner

Purpose:
- Route domain analyzers through the existing run-local context, remove warm-path world copies, and account retained resources incrementally.

Task Function:
- Shared workbook integration and resource-accounting consolidation.

Template Profile:
- Controller-selected: none (lead controller)
- Selection basis: six analyzers, validator, capability middleware, cache, authority index, and metrics share one ownership boundary.

Validator Profile:
- Controller-selected: none

Specification Coverage:
- Release 2: one source snapshot per owned context, trusted workbook views, bounded multi-sheet reads, cheap warm hits, incremental accounting, cumulative work counters, and publish-on-success transactions.

Required Skills:
- skill-backend-verification, skill-performance-optimization, skill-test-driven-development, skill-code-standards

Files And Symbols:
- Modify: src/foresight_os/runtime/local_toolbelt.py:WorkbookContext, WorkbookReadCache, AuthorityIndex, spreadsheet_read, data_analysis
- Modify: src/foresight_os/runtime/capabilities.py:CapabilityScope and instrumented workbook dispatch
- Modify: src/foresight_os/runtime/metrics.py:RunMetrics
- Modify: src/foresight_os/analysis/portfolio_resilience.py:analyze_portfolio_resilience
- Modify: src/foresight_os/analysis/supplier_resilience.py:analyze_supplier_resilience
- Modify: src/foresight_os/analysis/technology_radar.py:analyze_technology_radar
- Modify: src/foresight_os/analysis/ev_capacity_investment.py:analyze_ev_capacity_investment
- Modify: src/foresight_os/analysis/powerbi_strategic_portfolio.py:analyze_powerbi_strategic_portfolio
- Modify: src/foresight_os/analysis/foresight_validator.py:validate_exercises
- Verify: tests/test_local_toolbelt.py, tests/test_runtime_boundaries.py, tests/test_capabilities.py, tests/test_selective_reuse.py

Dependencies:
- Tasks 2–3 establish identity and contract semantics.

Authority:
- Preauthorized local actions: add optional workbook_context integration, refactor cache/authority accounting, update declared analyzers and focused tests, and record Release 2 evidence.
- Stop for: a second cache/store/registry proposal, a requirement to retain live openpyxl objects, or a resource-accounting result that cannot distinguish cumulative counters from retained gauges.

Steps:
- [x] Step 1: Add one shared helper that reads through a supplied WorkbookContext and preserves standalone analyzer behavior when no context is supplied.
- [x] Step 2: Update all six analyzers and the validator to accept workbook_context=None; use the context for source snapshot, bounded selection, formula/cache inspection, provenance, and deterministic extraction.
- [x] Step 3: Replace repr() scans and whole-context rollback copies with per-entry weights and transactional candidate publication on success; apply retained-size deltas only after commit, keep failed-attempt diagnostics, and keep parser peak memory separate from logical retained cache bytes.
- [x] Step 4: Separate cumulative counters (capture_count, hashes, parses, loads, cache hits, failed reads) from retained gauges (snapshot, read-cache, analysis-cache, authority bytes); failed attempts increment work counters but do not increase retained gauges.
- [x] Step 5: Change only workbook-capable participant/tool guidance to request the smallest bounded multi-sheet/range set for one analytical step, retain sheet/row/cell/result limits, and reject blanket full-workbook reads; do not redesign general participant orchestration here.

Verification:
- [x] python -m pytest -q tests/test_local_toolbelt.py tests/test_runtime_boundaries.py tests/test_capabilities.py tests/test_selective_reuse.py
- Expected: same view has zero new capture/hash/parse; changed brief reuses extraction; different selection reuses source but may reparse; failed reads publish nothing; counters and gauges have distinct semantics.
- [x] Inspect src/foresight_os/runtime/participants.py and tests/test_skills.py
- Expected: one-sheet-per-call guidance is replaced by bounded multi-sheet/range guidance and the test asserts the new wording.

Exit Criteria:
- Domain analyzers share one context in investigation runs, standalone APIs remain compatible, warm hits do not copy retained state, and retained accounting is incremental.

### Task 5: Measure the real repeated-investigation path

Purpose:
- Prove structural reuse, latency, allocation, and resource behavior on representative production-path workloads without conflating timing and memory profiling.

Task Function:
- Matched performance and resource evidence.

Template Profile:
- Controller-selected: none (lead controller)
- Selection basis: performance claims require the existing probe harness plus explicit workload and environment controls.

Validator Profile:
- Controller-selected: none

Specification Coverage:
- Release 2 measurement gate and the non-goal of speculative parsed-workbook retention.

Required Skills:
- skill-performance-optimization, skill-backend-verification

Files And Symbols:
- Modify: evaluation/probes/optimization_measurement.py, evaluation/probes/run_optimization_probe.py, evaluation/probes/compare_optimization_receipts.py
- Modify: tests/test_optimization_measurement.py
- Verify: work/runtime-consolidation-release-2/receipt.md

Dependencies:
- Task 4 context integration and accounting proof.

Authority:
- Preauthorized local actions: extend the existing probe harness, run local deterministic workloads, write one concise measurement receipt, and label unavailable dimensions honestly.
- Stop for: missing representative fixtures, unstable environment, unbounded probe cost, or any request to claim a speedup from structural counters alone.

Steps:
- [x] Step 1: Define matched workloads for cold read, same-view repeat, changed brief with same extraction, different selection, bounded multi-sheet read, analyst-to-validator reuse, changed source, cancelled read, multi-workbook run, repeated run, and large-context warm hit.
- [x] Step 2: Run wall-clock p50/p95 in one mode without tracemalloc; record source identity, selection, implementation identity, Python/dependency versions, and correctness checks.
- [x] Step 3: Run allocation/peak-memory diagnostics in a separate mode and run the declared repeated-run resource soak; keep parser peak memory distinct from retained logical bytes.
- [x] Step 4: Update receipt comparison to report PASS, FAILED, NOT_MEASURED, and DEFERRED per workload; do not convert absent latency or soak data into a passing claim.
- [x] Step 5: Use the result to decide only whether Level-2 parsed-workbook retention is justified; default outcome is defer it.

Verification:
- [x] python -m pytest -q tests/test_optimization_measurement.py
- Expected: receipt validation rejects missing metrics and accepts explicit unavailable/deferred dimensions.
- [x] python evaluation/probes/run_optimization_probe.py --help
- Expected: declared workload and output options exist and run without provider credentials for local fixtures.
- [x] Matched release receipt inspection
- Expected: correctness is proven independently from timing; no speedup claim lacks p50/p95 evidence.

Exit Criteria:
- Release 2 receipt records every workload, environment, correctness result, and limitation; its structural/correctness gate must pass, while noisy or unavailable latency may remain NOT_MEASURED or DEFERRED and does not block Task 6. Parsed-workbook retention remains deferred unless the measured gate explicitly warrants a follow-up plan.

### Task 6: Simplify execution policy and stage identity

Purpose:
- Make immutable NormalizedIntent authoritative for recipe selection, use Direct/Sequential for ordinary topology, and scope stage identity to explicit relevant contracts before synthesis changes.

Task Function:
- Controller-policy and stage-input simplification.

Template Profile:
- Controller-selected: none (lead controller)
- Selection basis: execution policy and stage identity are shared inputs to cache, approval, receipts, and metrics; they must be settled before synthesis consumes them.

Validator Profile:
- Controller-selected: none

Specification Coverage:
- Release 3: one immutable normalized intent, ordinary Direct/Sequential defaults, one stage fingerprint bundle, and explicit relevant-contract routing.

Required Skills:
- skill-backend-verification, skill-test-driven-development, skill-code-standards

Files And Symbols:
- Modify: src/foresight_os/domain/analysis_inputs.py:normalize_work_brief, NormalizedIntent
- Modify: src/foresight_os/controller/policy.py:select_recipe, _recipe_for_patterns
- Modify: src/foresight_os/controller/recipes.py:ExecutionRecipe
- Modify: src/foresight_os/runtime/workflow.py:stage-input preparation, _stage_fingerprints, _stage_cache_key
- Verify: tests/test_analysis_input_contract.py, tests/test_controller_selection.py, tests/test_stage_inputs.py, tests/test_selective_reuse.py, tests/test_execution_gate.py

Dependencies:
- Tasks 2–4 accepted identity/lifecycle and workbook structural/correctness boundaries. Task 5 latency comparison may be NOT_MEASURED or noisy; only its structural/correctness gate is required here.

Authority:
- Preauthorized local actions: modify the listed intent, controller, recipe, and stage-input owners; preserve serialized recipe compatibility; update focused tests and record the Release 3 receipt.
- Stop for: a required recipe-schema rewrite, inferred contract routing, a second normalization layer, or a need to add a new execution pattern.

Steps:
- [x] Step 1: Populate NormalizedIntent.resource_limits and other policy fields from actual brief/runtime constraints. Deep-freeze nested stage/source-need mappings, resource limits, and nested policy structures; derive a stable fingerprint from immutable content so mutation fails or requires a new intent.
- [x] Step 2: Make select_recipe consume one normalized intent and stop reinterpreting raw WorkBrief plus independent TaskShape policy. Default one bounded independent stage to Direct and ordered work/review to Sequential; retain Concurrent, Handoff, and Group Chat only for explicit normalized intent or approved topology.
- [x] Step 3: Add an internal `RecipeStage.analysis_domains` projection, populated from WorkBrief/NormalizedIntent during recipe compilation, and resolve those domains to direct analysis-contract IDs plus declared dependency IDs. If serialized recipe compatibility forbids a wire-field change, carry the projection in existing compatibility-safe internal metadata. Never infer it from prompt text, participant names, stage IDs, or skill names.
- [x] Step 4: Compute one stage fingerprint bundle containing semantic, execution-policy, and relevant-contract fingerprints; pass it to cache, receipts, approval, and metrics without recomputation or overwrite.
- [x] Step 5: Prove an unrelated domain-contract change does not invalidate the stage, while a direct or declared dependency change does; preserve serialized compatibility and add focused routing/reuse assertions.

Verification:
- [x] python -m pytest -q tests/test_analysis_input_contract.py tests/test_controller_selection.py tests/test_stage_inputs.py tests/test_selective_reuse.py tests/test_execution_gate.py
- Expected: immutable normalized policy is authoritative, ordinary topology is Direct/Sequential, explicit relevant-only routing preserves reuse, and mutation attempts cannot alter intent semantics.

Exit Criteria:
- Recipe selection and stage identity have one source of truth; NormalizedIntent is immutable after construction; contract routing is explicit and relevant-only; synthesis can consume the settled execution inputs.

### Task 7: Consolidate synthesis and obsolete runtime owners

Purpose:
- Replace fixed-point normalization and message-substring recovery with one bounded indexed synthesis pass, then remove only proven duplicate owners and compatibility paths.

Task Function:
- Bounded synthesis, recovery, and ownership consolidation.

Template Profile:
- Controller-selected: none (lead controller)
- Selection basis: synthesis and result commitment share canonical-record ownership, while compatibility cleanup must follow consumer proof rather than defer the same refactor across tasks.

Validator Profile:
- Controller-selected: none

Specification Coverage:
- Release 4: bounded preflight, participant-local correction, typed recovery, material conflicts, canonical dependency references, cancellation checkpoints, and one run-local workbook owner.

Required Skills:
- skill-backend-verification, skill-test-driven-development, skill-code-standards

Files And Symbols:
- Modify: src/foresight_os/runtime/workflow.py:_synthesize_stage_outputs, _expand_dependency_records, run_recipe_async
- Modify: src/foresight_os/runtime/participants.py:participant_instructions
- Modify: src/foresight_os/analysis/result_committer.py
- Modify: src/foresight_os/runtime/capabilities.py:CapabilityScope and workbook middleware only for proven owner cleanup
- Modify: src/foresight_os/domain/models.py and src/foresight_os/domain/validation.py only where existing typed result/error owners require extension
- Verify: tests/test_orchestration_patterns.py, tests/test_result_committer.py, tests/test_review_hardening.py, tests/test_participant_scope.py, tests/test_runtime_boundaries.py

Dependencies:
- Task 6 execution simplification and Tasks 2–5 accepted boundaries and evidence.

Authority:
- Preauthorized local actions: modify the listed synthesis, participant, commit, typed-validation, and proven compatibility owners; add focused regression tests; record the Release 4 receipt. Task 7 consumes the stage fingerprint bundle settled by Task 6 and does not redesign its ownership.
- Stop for: a new generic recovery framework, a second dependency store, participant-order-dependent conflict resolution, loss of conflict visibility, or an unproven owner deletion.

Steps:
- [x] Step 1: Add cheap aggregate preflight for participants, records, calculations, relationships, aliases, payload bytes, dependency depth, and normalization operations before materializing full normalized output.
- [x] Step 2: Build participant-local namespaces and one record index; memoize canonical hashes once; resolve aliases and dependency DAGs; validate relationships after endpoints; dedupe identical records; emit MATERIAL_CONFLICT for differing content under one canonical identity.
- [x] Step 3: Add bounded cancellation checkpoints during indexing, dependency traversal, and relationship validation; preserve asyncio.CancelledError as non-retryable.
- [x] Step 4: Replace validation-message parsing and tolerance toggles with typed codes: MALFORMED_OUTPUT, UNRESOLVED_REFERENCE, AMBIGUOUS_ALIAS, INVALID_RELATIONSHIP, MATERIAL_CONFLICT, MISSING_INPUT, SOURCE_STALE, PROVIDER_INTERRUPTION, and BUDGET_EXHAUSTED.
- [x] Step 5: Preserve valid participant outputs while correcting only the failed participant or affected relationship once through existing participant result boundaries and invocation code; do not add participant checkpoint persistence or a generic resumable workflow engine. For relationship-only failures, prefer deterministic local correction/removal; if the active execution pattern cannot expose safe participant-level state, return a typed unsupported/recovery failure instead of creating another orchestration subsystem. Assert successful participants, source tools, and deterministic calculations are not repeated.
- [x] Step 6: Pass dependency content for reasoning but accept references to existing canonical IDs; validate ID existence, hash, invalidation state, dependency closure, and participant authorization without requiring copied dependency records.
- [x] Step 7: Migrate remaining consumers from CapabilityScope.workbook_cache and process-global authority fallbacks; retire aliases only after consumer search and focused tests prove no active runtime dependency remains.

Verification:
- [x] python -m pytest -q tests/test_orchestration_patterns.py tests/test_result_committer.py tests/test_review_hardening.py tests/test_participant_scope.py tests/test_runtime_boundaries.py
- Expected: bounded synthesis, typed recovery, canonical references, material conflicts, cancellation checkpoints, participant-local correction, and exact owner-cleanup call-count assertions pass.
- [x] git grep -n -E "workbook_cache|_AUTHORITATIVE_MEASUREMENTS|_AUTHORITATIVE_CALCULATIONS" -- src tests
- Expected: only explicitly documented standalone compatibility paths remain, or all active consumers have been migrated and the aliases are removed.

Exit Criteria:
- Synthesis is one bounded indexed transformation, recovery decisions are typed, valid outputs survive a sibling failure, dependency references are canonical, and runtime ownership has one proven run-local owner.

### Task 8: Reduce evidence noise and complete final verification

Purpose:
- Align maintained documentation and evidence with actual behavior, rerun the production benchmark on the exact final tree, remove only proven obsolete compatibility/process guidance, and produce fresh completion proof.

Task Function:
- Final reconciliation, verification, and handoff.

Template Profile:
- Controller-selected: none (lead controller)
- Selection basis: final reconciliation must be performed by the lead controller after all implementation lanes are settled.

Validator Profile:
- Controller-selected: none

Specification Coverage:
- Final Release 4 consolidation, final-tree performance evidence, truthful evidence, maintained guidance, plan completion gates, and preservation of unrelated user work.

Required Skills:
- skill-performance-optimization, skill-backend-verification, skill-verification-before-completion, skill-plan-document-reviewer, skill-finishing-a-development-branch

Files And Symbols:
- Modify: docs/architecture.md, docs/extending.md, evaluation/README.md, and the plan receipt only where implementation changed behavior
- Reuse/modify if needed: evaluation/probes/optimization_measurement.py, evaluation/probes/run_optimization_probe.py, evaluation/probes/compare_optimization_receipts.py, tests/test_optimization_measurement.py
- Inspect: .github/workflows/ci.yml and all declared consumers before any CI or compatibility cleanup
- Verify: final changed-file diff, receipts, source-tree fingerprint, and worktree state

Dependencies:
- Tasks 1–7 complete with no unresolved required proof.

Authority:
- Preauthorized local actions: run final checks, update maintained documentation and the plan receipt, and preserve or explicitly defer unmeasured evidence.
- Stop for: failed required proof, stale base, unresolved dirty in-scope files, destructive cleanup, publication, merge, or branch/worktree removal.

Steps:
- [x] Step 1: Remove only compatibility/process paths proven unused by the consumer search; retain deferred owners and record their reason in the receipt.
- [x] Step 2: Replace one-sheet-per-call and copied-dependency guidance with the implemented bounded multi-sheet and canonical-reference contracts; run the Markdown-link checker.
- [x] Step 3: Rerun the matched end-to-end benchmark after Tasks 6–7 on the exact final source tree, including cold investigation, warm repeated investigation, changed brief with the same workbook, analyst-validator reuse, large-context warm hit, cancellation, and resource soak. Record implementation identity, workload, environment, correctness result, p50/p95 timing, allocation/peak-memory diagnostics, retained-resource gauges, and named limitations; do not treat the Release 2 receipt as final-tree proof.
- [x] Step 4: Keep one concise release/final receipt with requirement, proof, result, and limitation columns; reference both the Release 2 workbook benchmark and the final-tree end-to-end benchmark; do not commit routine raw logs or generated probe dumps.
- [x] Step 5: Run fresh focused checks, the full suite, compileall, Markdown links, diff check, and source-tree scope inspection. Completion requires all declared evidence gates to pass on the exact final tree; the verification workflow records that result.

Verification:
- [x] python -m pytest -q
- Expected: repository suite passes with only documented expected skips.
- [x] python -m compileall -q src tests evaluation
- Expected: no compile errors.
- [x] python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs
- Expected: all tracked Markdown paths pass.
- [x] Final-tree optimization probe and receipt comparison
- Expected: final implementation identity is recorded; correctness, p50/p95, allocation, soak, and retained-resource evidence are independently labeled PASS, FAILED, NOT_MEASURED, or DEFERRED with limitations.
- [x] git diff --check and git status --short --branch
- Expected: no whitespace errors; only declared in-scope changes remain; unrelated primary-checkout artifacts are untouched.

Exit Criteria:
- Final-tree benchmark and verification evidence reconcile with the implementation; unavailable latency/resource evidence is labeled rather than overstated; publication remains a separate Git disposition.

## Verification

Final verification is performed only after Task 8 implementation work completes:

- python -m pytest -q
- python -m compileall -q src tests evaluation
- python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs
- git diff --check
- git status --short --branch
- Review the final compact receipts and confirm each claim is PASS, FAILED, NOT_MEASURED, or DEFERRED with a named limitation.
- Run the verification workflow and record its result; the required tests, receipts, exact source tree, invariants, and declared diff remain the completion authority.

## Completion Criteria

The plan is ready for completion verification when:

1. External or reconstructed TypedTable values cannot authorize cache hits with caller-supplied identity.
2. Changed rows, provenance, range, hidden semantics, and join-table content always produce new material identity.
3. Cancellation remains asyncio.CancelledError after worker settlement and cleanup, and secondary failures are diagnostic only.
4. Capability preflight creates no owned resource; activation occurs inside a cleanup owner and all owned resources settle exactly once.
5. Invalid brief-local semantics fail before expensive capture; explicit source mappings fail exact-or-fail; typed period meaning is preserved across supported analyzers.
6. All six analyzers and the validator can share one WorkbookContext; standalone compatibility remains covered.
7. Warm hits do not copy whole retained context; retained sizes update incrementally; cumulative counters remain truthful.
8. Production-path evidence separates structural reuse, wall-clock timing, allocation diagnostics, and resource soak; unmeasured dimensions remain explicit.
9. Synthesis is bounded, cancellation-aware, typed, participant-order independent, and preserves MATERIAL_CONFLICT.
10. Valid participant outputs and canonical dependency references survive isolated correction without repeating successful work.
11. NormalizedIntent is authoritative for recipe selection; Direct/Sequential are ordinary defaults; stage fingerprints use relevant contracts only.
12. CapabilityScope has one run-local workbook owner and obsolete compatibility owners are removed only after consumer proof.
13. Maintained docs, participant instructions, tests, receipts, and CI behavior describe the implemented contracts without duplicate specifications.
14. No persistent parsed-workbook cache or other non-goal is introduced.
15. NormalizedIntent is immutable after construction; changing policy semantics requires a new intent and fingerprint.
16. Stage-to-analysis-contract association is explicit and never inferred from prompt text, participant names, or stage IDs.
17. Final-tree benchmark evidence records implementation identity, workload, environment, correctness, p50/p95, allocation, soak, retained-resource limits, and named limitations; Release 2 evidence is not reused as final proof.
18. No task modifies the same architectural owner merely because the previous task deferred part of the same refactor; rollback/accounting, identity, topology, and synthesis ownership are singular.
19. Final focused and broad verification passes, the plan evidence matches the exact verified tree, and no unrelated primary-checkout artifact is modified.

Completion requires all declared evidence gates to pass on the exact final tree; the verification workflow records that result. A checked box is progress evidence, not completion proof.

## Self-Review

- Verdict coverage: the justified verdict changes map to Tasks 1–8; the four releases are Correctness, Workbook reuse, Execution simplification, and Synthesis/consolidation.
- Ownership: TypedTable/WorkbookContext remain in local_toolbelt.py; capability lifecycle remains in capabilities.py; contracts remain in analysis_inputs.py; synthesis remains in workflow.py; durable analytical state remains in AnalysisStore.
- Compatibility: serialized brief and recipe fields remain stable; typed period access is internal until compatibility tests prove a wire-format migration is safe.
- Correctness gates: stale caller fingerprints, dataclasses.replace(), cancellation settlement, resource activation, exact mapping, period semantics, immutable intent, explicit contract routing, participant-order conflicts, and no-publication failures have explicit tests.
- Performance gates: Release 2 structural reuse, final-tree p50/p95 timing, allocation diagnostics, and resource soak are separate measurements; no parsed-workbook retention is justified by counters alone.
- Ownership gates: identity, rollback/accounting, topology, and synthesis have singular task ownership; no deferred sub-refactor is duplicated across tasks.
- Scope: no new registry, store, recovery engine, orchestration pattern, distributed cache, filesystem watcher, or second normalization layer is authorized.
- Handoff: execution and verification are complete; branch disposition remains a separate authorized Git workflow.
