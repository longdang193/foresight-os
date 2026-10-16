---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: foresight-os-correctness-deletion-pass
targets:
  - src/foresight_os/domain/models.py
  - src/foresight_os/domain/analysis_inputs.py
  - src/foresight_os/domain/validation.py
  - src/foresight_os/wayfinding.py
  - src/foresight_os/schemas/work_brief.schema.json
  - src/foresight_os/schemas/execution_recipe.schema.json
  - src/foresight_os/controller/recipes.py
  - src/foresight_os/controller/policy.py
  - src/foresight_os/controller/task_shape.py
  - src/foresight_os/runtime/capabilities.py
  - src/foresight_os/runtime/execution_gate.py
  - src/foresight_os/runtime/local_toolbelt.py
  - src/foresight_os/runtime/participants.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/analysis/workbook_inputs.py
  - src/foresight_os/analysis/powerbi_strategic_portfolio.py
  - src/foresight_os/analysis/result_committer.py
  - src/foresight_os/persistence/analysis_store.py
  - evaluation/probes/run_optimization_probe.py
  - evaluation/probes/optimization_measurement.py
  - evaluation/probes/compare_optimization_receipts.py
  - tests/test_analysis_input_contract.py
  - tests/test_brief_portability.py
  - tests/test_case_portability.py
  - tests/test_controller_selection.py
  - tests/test_execution_gate.py
  - tests/test_capabilities.py
  - tests/test_local_toolbelt.py
  - tests/test_runtime_boundaries.py
  - tests/test_orchestration_patterns.py
  - tests/test_result_committer.py
  - tests/test_stage_inputs.py
  - tests/test_selective_reuse.py
  - tests/test_optimization_measurement.py
  - tests/test_supplier_and_ev_resilience.py
  - tests/test_technology_powerbi_validator.py
  - docs/architecture.md
  - docs/evidence-and-evaluation.md
  - docs/extending.md
---

# ForesightOS Correctness and Deletion Pass Plan

## Goal

Close the remaining correctness gaps identified after PR #26 and delete
redundant runtime paths that those corrections make unnecessary. This is a
bounded correctness-closure and deletion pass, not a general controller or
runtime refactor and not a new architecture program.

The implementation starts from merged `origin/main` at
`117ca70f7bc9fcd2c1ca2420e512b6b837716e34`. The primary checkout is dirty and
contains unrelated local artifacts; execution must use a new isolated worktree
created from that remote base and must not mutate the primary checkout.

## Review Of The Verdict

### Adopted conclusions

- Contract identity must remain distinct for stages that share an analysis
  domain. The canonical identity is `(stage_id | GLOBAL_SCOPE, domain)` and
  duplicate keys fail instead of overwriting.
- The authoritative internal representation is an ordered immutable contract
  collection, not a domain-keyed dictionary. Legacy domain-keyed callers may
  translate once at a compatibility boundary.
- Resolution precedence is explicit: a stage-scoped contract replaces the
  global contract for that stage/domain; global scope is fallback only when no
  stage-specific contract exists; duplicate same-scope keys fail; explicit
  no-contract scope receives none; and legacy scope-unavailable remains
  distinct from explicit empty scope.
- `RecipeStage.analysis_domains` becomes the authoritative internal and new
  serialized representation. Legacy recipe metadata is a one-way translation
  boundary, not a second live policy source.
- Explicit mappings are exact-or-fail per intended source table; omitted
  mappings retain compatibility fallback behavior.
- Exact `PeriodSpec` values flow from normalized input into analyzers without a
  second year-only lookup.
- Participant identity travels with output and failure data; targeted recovery
  retries a stable participant ID rather than a filtered-list position.
- Cancellation preserves the caller's `asyncio.CancelledError` after worker
  settlement and cleanup; settlement and cleanup failures remain secondary
  diagnostics.
- Capability preflight is metadata-only. Resource factories run only inside an
  owned `CapabilityScope` that registers resources immediately and closes them
  exactly once.
- Direct and multi-participant execution share one bounded canonical-output
  boundary, while direct execution skips only unnecessary aggregation.
- Synthesis uses one memoized dependency traversal, explicit cycle errors,
  real cancellation checkpoints, and an operation budget that counts material
  work rather than only normalization calls.
- Warm workbook hits use incremental retained-size accounting, skip authority
  re-registration and transaction setup, and preserve bounded standalone
  capture behavior.
- A warm cached view is valid only while the authority records it depends on
  remain retained. The implementation must either prevent authority eviction
  while dependent views are live or invalidate those views atomically.
- `NormalizedIntent` is the normal controller input; Direct and Sequential are
  the default topology, while Concurrent, Handoff, and Group Chat require an
  explicit normalized request or approved override.
- Benchmark labels must correspond to executed workloads, counters must come
  from runtime metrics, and performance claims must remain narrow to the
  workload actually measured.

### Scoped corrections and explicit non-goals

- Do not introduce a source registry, parsed-workbook database, persistent
  `openpyxl` object cache, generic recovery engine, graph framework, second
  analytical store, filesystem watcher, distributed cache, or new orchestration
  pattern.
- Preserve backward-readable WorkBrief and recipe serialization. Legacy input
  may translate into the canonical representation once, but live logic must not
  consult both representations.
- Retire process-global authoritative measurement/calculation state only after
  the consumer audit proves normal execution no longer depends on it. If a
  standalone compatibility caller remains, isolate and document that adapter;
  do not replace the globals with another registry.
- Do not add a recursive object sizer. Use structural payload gates followed by
  one canonical serialization when hashing or committing is actually required.
- Keep participant correction bounded to one targeted rerun within the existing
  budget. No participant checkpoint database or retry graph is authorized.
- Required invalid relationships are never silently dropped. Removal or
  correction is permitted only when the exact participant/edge is identified
  and policy allows it; otherwise recovery returns an explicit unsupported or
  failed result.
- Replace multi-release ceremony with one final acceptance receipt. Routine
  pytest output, allocation dumps, raw samples, and generated probe state stay
  out of Git unless a focused regression requires a durable fixture.

## Change-set order and control

| Change set | Scope | Depends on | Required gate |
| --- | --- | --- | --- |
| 1. Correctness and identity closure | Contract identity, mappings, periods, cancellation, admission, participant identity, canonical output bounds | Merged PR #26 and current owner map | Focused correctness suite and portability matrix pass |
| 2. Runtime overhead and recovery deletion | Warm-path accounting, cache fast path, bounded capture, synthesis traversal, tolerance removal, fingerprint reuse | Change set 1 | Focused runtime and synthesis suite plus benchmark fixture correctness |
| 3. Migration and proof | Mandatory contract serialization cleanup, optional bounded NormalizedIntent/topology cleanup, compatibility retirement, truthful benchmark, final documentation | Change set 2 | Full suite, final benchmark, receipt, and scope review pass |

All changes are serialized through one lead controller because the three change
sets share `workflow.py`, `local_toolbelt.py`, `recipes.py`, and their tests.
Do not dispatch parallel writers over those files. Each change set must leave a
reviewable commit boundary and pass its focused gate before the next begins.

## Task Ledger

| Task | Change set | Status | Owner | Required proof |
| --- | --- | --- | --- | --- |
| Task 1 | 1 | completed | lead controller | Frozen evidence protocol plus stage-scoped contract, mapping, period, invalidation, and portability regressions |
| Task 2 | 1 | completed | lead controller | Cancellation, admission, participant identity, and canonical-boundary regressions |
| Task 3 | 2 | completed | lead controller | Warm-path, synthesis-bound, strict-recovery, and fingerprint regressions |
| Task 4 | 3 | completed | lead controller | Mandatory contract serialization cleanup; bounded migration decision and controller-policy regressions |
| Task 5 | 3 | completed | lead controller | Truthful benchmark, final receipt, full verification, and plan reconciliation |

## Task Breakdown

### Task 1: Close stage-scoped contract identity and analytical meaning

Purpose:
- Make `(stage_id, domain)` identity stable across the complete chain:
  WorkBrief schema, in-memory WorkBrief, validation, save/load, normalization,
  recipe compilation, execution gate, workflow fingerprints, receipts, and
  invalidation/reuse.
- Correct explicit mapping and exact-period semantics before optimizing the
  runtime around potentially wrong inputs.

Task Function:
- Correctness-first contract and portability implementation.

Required Skills:
- skill-code-standards
- skill-test-driven-development
- skill-backend-verification

Files And Symbols:
- Inspect/modify: `src/foresight_os/domain/models.py:WorkBrief` and
  `src/foresight_os/wayfinding.py` where the brief is constructed or normalized.
- Modify: `src/foresight_os/domain/analysis_inputs.py:AnalysisInputContract, NormalizedIntent, normalize_work_brief, contract_for_domain`
- Modify: `src/foresight_os/domain/validation.py` and
  `src/foresight_os/persistence/analysis_store.py` where validation,
  persistence, receipt identity, and reuse/invalidation support are owned.
- Modify/verify: `src/foresight_os/schemas/work_brief.schema.json` and
  `src/foresight_os/schemas/execution_recipe.schema.json` for backward-readable
  wire contracts.
- Modify: `src/foresight_os/controller/recipes.py:StageInput, RecipeStage, ExecutionRecipe.from_dict, ExecutionRecipe.to_dict`
- Modify: `src/foresight_os/controller/policy.py:stage_analysis_domains, recipe compilation`
- Modify: `src/foresight_os/runtime/execution_gate.py` and
  `src/foresight_os/runtime/workflow.py:stage-input preparation,
  _stage_fingerprints, _stage_cache_key` so the execution gate and runtime use
  the same scoped identity.
- Verify affected analyzers, especially
  `src/foresight_os/analysis/workbook_inputs.py` and
  `src/foresight_os/analysis/powerbi_strategic_portfolio.py`, consume exact
  periods and resolved contracts rather than reconstructing them.
- Verify: `tests/test_analysis_input_contract.py`, `tests/test_stage_inputs.py`, `tests/test_selective_reuse.py`, `tests/test_brief_portability.py`, `tests/test_case_portability.py`, `tests/test_supplier_and_ev_resilience.py`, `tests/test_technology_powerbi_validator.py`

Dependencies:
- `origin/main` at `117ca70f7bc9fcd2c1ca2420e512b6b837716e34`.

Steps:
1. Freeze the benchmark protocol before production changes: define fixtures,
   exact workload labels, sample counts, thresholds, environment capture, and
   separate correctness, timing, allocation, and soak evidence. Run that frozen
   harness against the base commit and save the local result as
   `work/foresight-os-correctness-deletion-pass/baseline-optimization.json`.
   Do not change the protocol after observing results; carry only the summary
   into the final receipt.
2. Define one ordered immutable internal contract representation for global and
   stage-scoped contracts. Preserve `stage_id` through WorkBrief construction,
   validation, save/load, normalization, recipe serialization, execution-gate
   input, fingerprints, receipts, invalidation, and reuse. Reject duplicate
   scoped keys and unknown stage-scoped contract IDs with typed validation
   errors.
3. Implement and test precedence explicitly: stage-specific scope replaces the
   global contract for that stage/domain; global scope is fallback only when no
   stage-specific contract exists; explicit no-contract scope receives none; and
   legacy scope-unavailable remains distinct from explicit empty scope. Translate
   legacy domain-keyed callers once at the compatibility boundary rather than
   making a dictionary authoritative internally.
4. Serialize new recipes with explicit `analysis_domains`. Translate legacy
   `analysis_contract_domains` metadata into `RecipeStage.analysis_domains` once
   during deserialization, then make runtime policy and the execution gate read
   only the canonical stage field.
5. Make stage fingerprints and reuse keys consume the canonical scoped contract
   collection. A contract change invalidates its consuming stage and the stale
   downstream dependency closure, while unrelated branches remain reusable. Prove
   that same-domain contracts on different stages never collide.
6. Validate explicit mappings against the intended source table. A missing
   explicit source column raises `MISSING_MAPPED_COLUMN` even when the same
   canonical field exists elsewhere in the workbook. Apply fallback inference
   only when no explicit mapping was supplied.
7. Resolve baseline and comparison periods to exact `PeriodSpec` values during
   normalization and pass those specs directly to analyzers. Reject unsupported
   granularity, unavailable periods, and unsupported cross-year semantics rather
   than reducing them to a year-only compatibility lookup.
8. Extend portability tests to assert selected contract, period, entity, source
   table/range, mapped column, units, expected analytical value, provenance
   hashes/cells, anomaly handling, explicit unsupported/error outcomes, and
   save/load round-trip identity.

Verification:
- `python -m pytest -q tests/test_analysis_input_contract.py tests/test_stage_inputs.py tests/test_selective_reuse.py tests/test_brief_portability.py tests/test_case_portability.py tests/test_supplier_and_ev_resilience.py tests/test_technology_powerbi_validator.py`
- Expected: duplicate scoped keys and unknown stage IDs fail, precedence and
  explicit empty scope are distinct, same-domain stages remain independent,
  changed contracts invalidate their consuming stage plus stale downstream
  closure but not unrelated branches, mappings are exact-or-fail per table, and
  March/April in one year remain distinct.
- `python evaluation/probes/run_optimization_probe.py --mode release --fixture tests/fixtures/analyst_multisheet.xlsx --output work/foresight-os-correctness-deletion-pass/baseline-optimization.json --measurement-mode full`
- Expected: the frozen base run records exact implementation identity,
  correctness, workload, environment, distributions, allocation diagnostics,
  and resource-soak evidence; missing mandatory evidence is incomplete rather
  than a pass.

Exit Criteria:
- Contract identity and analytical meaning are correct before Task 2 changes
  runtime or recovery behavior.

### Task 2: Close lifecycle, participant, and canonical-output boundaries

Purpose:
- Preserve cancellation truth, eliminate resource creation during admission,
  carry participant identity through correction, and apply one bounded output
  boundary to every execution topology.

Task Function:
- Backend lifecycle and recovery hardening.

Required Skills:
- skill-backend-verification
- skill-test-driven-development
- skill-code-standards

Files And Symbols:
- Modify: `src/foresight_os/runtime/capabilities.py:CapabilityResolver, CapabilityScope, admit_capabilities, activate_capabilities` or the smallest equivalent split.
- Modify: `src/foresight_os/runtime/execution_gate.py:ExecutionGate._preflight_recipe`
- Modify: `src/foresight_os/runtime/participants.py:participant result envelope and response normalization`
- Modify: `src/foresight_os/runtime/workflow.py:run_recipe_async, participant result collection, _synthesize_stage_outputs, targeted correction`
- Modify: `src/foresight_os/analysis/result_committer.py:normalize_stage_result and typed validation errors`
- Verify: `tests/test_capabilities.py`, `tests/test_execution_gate.py`, `tests/test_runtime_boundaries.py`, `tests/test_orchestration_patterns.py`, `tests/test_result_committer.py`

Steps:
1. Separate metadata-only admission from activation. Preflight may inspect
   definitions, bindings, callable factories, authorization, and human approval,
   but must not invoke a factory or create a resource. Activation creates the
   owned scope, registers each resource immediately, executes the operation, and
   closes the scope on every exit path.
2. Preserve the original `asyncio.CancelledError` across blocking-worker
   settlement. Signal cancellation, await worker settlement, record worker and
   cleanup failures as secondary diagnostics, and re-raise the original
   cancellation even after a worker error, cleanup error, or second cancellation.
   `cleanup_complete` is true only when every owned resource actually closed
   successfully; an attempted `.close()` or partial activation is not success.
3. Carry `participant_id`, output, and failure together from execution through
   synthesis. Report targeted validation failures by stable participant ID, not
   filtered-list position, and rerun at most that participant once within the
   existing correction budget.
4. Remove broad `tolerate_invalid_relationships` and
   `tolerate_conflicting_records` recovery switches. Invalid relationships are
   corrected or removed only when the exact participant/edge is known and
   policy permits it; required invalid relationships otherwise return explicit
   `UNSUPPORTED_RECOVERY` or failure. Material conflicts stop automatic merge
   with `MATERIAL_CONFLICT` rather than silently dropping required edges.
5. Apply payload, record, relationship, alias, dependency, and normalization
   bounds to Direct and single-output results before canonical commit, while
   avoiding unnecessary multi-output aggregation.
6. Add direct boundary tests for partial resource activation, failed close and
   truthful retained-resource accounting, worker settlement failure, cleanup
   failure, second cancellation, malformed participant output,
   participant-targeted correction, unsupported targeted recovery, required
   invalid relationships, direct-output limits, and material conflicts.

Verification:
- `python -m pytest -q tests/test_capabilities.py tests/test_execution_gate.py tests/test_runtime_boundaries.py tests/test_orchestration_patterns.py tests/test_result_committer.py`
- Expected: admission creates no resources, all owned resources settle exactly
  once, `cleanup_complete` reflects actual close success, caller cancellation
  remains `asyncio.CancelledError`, correction targets the named participant,
  required invalid relationships are never silently dropped, direct results
  obey the same safety limits, and participant order never resolves a material
  conflict.

Exit Criteria:
- Lifecycle and correction behavior is typed, bounded, participant-identity
  safe, and independent of execution topology.

### Task 3: Delete runtime overhead and make synthesis genuinely bounded

Purpose:
- Remove repeated work from warm workbook reads and stage dispatch while making
  dependency traversal, cancellation, and operation limits match the actual
  amount of work performed.

Task Function:
- Runtime simplification and measured overhead reduction.

Required Skills:
- skill-performance-optimization
- skill-backend-verification
- skill-test-driven-development

Files And Symbols:
- Modify: `src/foresight_os/runtime/local_toolbelt.py:WorkbookContext, WorkbookReadCache, AuthorityIndex, spreadsheet_read, data_analysis`
- Modify: `src/foresight_os/analysis/workbook_inputs.py:read_workbook`
- Modify: `src/foresight_os/runtime/workflow.py:_synthesize_stage_outputs, _stage_fingerprints, _stage_cache_key, run_recipe_async`
- Modify: `src/foresight_os/runtime/capabilities.py:instrumented dispatch metadata`
- Inspect and remove only after consumer proof: `_AUTHORITATIVE_MEASUREMENTS`, `_AUTHORITATIVE_CALCULATIONS`, and their standalone callers in `src/foresight_os/runtime/local_toolbelt.py`.
- Verify: `tests/test_local_toolbelt.py`, `tests/test_stage_inputs.py`, `tests/test_runtime_boundaries.py`, `tests/test_orchestration_patterns.py`, `tests/test_result_committer.py`

Steps:
1. Add incremental byte counters for read-cache, analysis-cache, measurement,
   calculation, and snapshot retention. Update counters on insert, replace,
   eviction, rollback, and cleanup; make retained-size properties read the
   counters rather than scan retained dictionaries.
2. Tie cached views to the authority records they depend on. Prevent authority
   eviction while a dependent view is live, or atomically invalidate every
   dependent view before eviction. Test cache-hit validity after eviction,
   rollback, failed first reads, and cleanup with zero leaked snapshots or
   authority records.
3. Add the same-context cache-hit fast path before opening a mutation
   transaction. A committed hit increments the hit metric and returns without
   capture, source/table-content hashing, parsing, authority re-registration,
   authority traversal, or transaction journal work.
4. Route standalone workbook reads through the existing bounded capture path so
   `ToolbeltLimits.max_bytes` is enforced consistently. Do not create a second
   snapshot path or retain parsed workbook objects.
5. Replace per-record dependency walks with one memoized DFS/topological pass
   using `UNSEEN`, `VISITING`, and `DONE` states. Calculate dependency order and
   depth in one pass, keep domain relationships outside the calculation graph,
   and raise typed `DEPENDENCY_CYCLE` errors.
6. Thread the real cancellation predicate through synthesis preflight,
   dependency traversal, normalization, and merge. Check it at bounded work
   units during substantial traversal/normalization, not only at entry or
   between awaits. Count inspected records, traversed references, validated
   relationships, resolved aliases, and required canonical hashes against one
   operation budget; preserve the caller's `asyncio.CancelledError` while
   worker/cleanup failures remain secondary diagnostics.
7. Use structural payload gates before serialization; serialize once only when
   hashing or committing requires canonical bytes. Keep the implementation
   shallow and bounded instead of adding a recursive object-size framework.
8. Compute semantic and execution fingerprints once per stage and pass both
   values through cache lookup, receipt creation, reuse validation, invalidation,
   and result commit. Reuse precomputed accepted adapter-parameter metadata in
   blocking and inline tool dispatch.
9. Search all repository consumers of the process-global authority maps. Delete
   the globals when no normal caller remains; otherwise isolate the remaining
   low-level compatibility adapter, mark it deprecated, and keep it outside the
   orchestrated `WorkbookContext` path.

Verification:
- `python -m pytest -q tests/test_local_toolbelt.py tests/test_stage_inputs.py tests/test_runtime_boundaries.py tests/test_orchestration_patterns.py tests/test_result_committer.py`
- Expected: same-context warm hits perform no new capture/hash/parse or
  authority publication or traversal; dependent cache views never outlive
  required authority; failed first reads leak no snapshots; retained-size
  checks remain constant-cost as records grow; standalone reads enforce byte
  limits; dependency cycles are typed; substantial synthesis work observes
  cancellation; and stage fingerprints are computed once.
- `git grep -n -E "_AUTHORITATIVE_MEASUREMENTS|_AUTHORITATIVE_CALCULATIONS|tolerate_invalid_relationships|tolerate_conflicting_records" -- src tests`
- Expected: no normal runtime path depends on removed global state or broad
  tolerance flags; any retained compatibility adapter is named in the receipt.

Exit Criteria:
- Warm-path and synthesis overhead are reduced by deleting repeated work, not by
  adding persistent caches or new ownership layers.

### Task 4: Complete mandatory contract cleanup and bounded controller migration

Purpose:
- Make contract serialization/scoping cleanup complete and independently
  deliverable. If the remaining `NormalizedIntent` and topology migration is
  bounded and demonstrably removes duplicate policy, complete it here; if it
  would delay workbook/correctness closure, record it as an explicit deferral
  rather than making it critical-path.

Task Function:
- Controller simplification and compatibility translation cleanup.

Required Skills:
- skill-code-standards
- skill-test-driven-development

Files And Symbols:
- Modify: `src/foresight_os/domain/analysis_inputs.py:NormalizedIntent`
- Modify: `src/foresight_os/controller/policy.py:select_recipe, _recipe_for_patterns, stage policy projection`
- Modify: `src/foresight_os/controller/recipes.py:recipe compilation and stage serialization`
- Inspect: `src/foresight_os/controller/task_shape.py` and `src/foresight_os/controller/proposal.py` for raw policy re-interpretation and compatibility translation boundaries.
- Verify: `tests/test_controller_selection.py`, `tests/test_execution_gate.py`, `tests/test_stage_inputs.py`, `tests/test_orchestration_patterns.py`, `tests/test_skills.py`

Steps:
1. Complete the mandatory contract serialization and scoping cleanup left by
   Tasks 1–3, including one-way legacy translation and tests proving that no
   second live contract policy source remains.
2. If bounded, populate immutable `NormalizedIntent` with the policy fields required by
   recipe selection, including resource limits, normalized topology, stage
   contracts, review policy, and compatibility decisions. Deep-freeze nested
   structures and derive one stable intent fingerprint.
3. If the bounded migration is selected, make the recipe compiler consume
   `NormalizedIntent` rather than re-reading
   raw WorkBrief execution overrides, task-shape booleans, desired deliverables,
   or participant names after normalization.
4. If the bounded migration is selected, default one bounded stage to Direct and ordered multi-stage or validation
   work to Sequential. Require an explicit normalized request or approved
   override for Concurrent, Handoff, and Group Chat.
5. If the bounded migration is selected, build one local per-stage policy projection containing capabilities, roles,
   review requirements, budgets, analysis domains, and unavailable decisions;
   construct `RecipeStage` from that projection without repeated derivation.
6. Preserve legacy deserialization by translating old fields at one boundary and
   add tests proving old serialized recipes retain behavior while new recipes
   round-trip explicit `analysis_domains`.

Verification:
- `python -m pytest -q tests/test_controller_selection.py tests/test_execution_gate.py tests/test_stage_inputs.py tests/test_orchestration_patterns.py tests/test_skills.py`
- Expected: policy decisions depend on one immutable intent, routine work uses
  Direct/Sequential, advanced patterns require explicit intent when the
  optional migration is delivered, stage policy is derived once, and legacy
  serialized recipes translate without a second live policy source. A deferred
  broader migration is named with its reason and does not weaken mandatory
  contract correctness.

Exit Criteria:
- Mandatory contract/scoping behavior has one authoritative serialized input.
  If the optional controller migration is delivered, normal execution also has
  one authoritative normalized intent and no implicit escalation caused by
  generic task-shape flags.

### Task 5: Make benchmark evidence truthful and complete final verification

Purpose:
- Replace nominal benchmark labels and repeated release ceremony with one
  representative final benchmark and one concise acceptance receipt.

Task Function:
- Production-path evidence, documentation, and completion reconciliation.

Required Skills:
- skill-performance-optimization
- skill-backend-verification
- skill-plan-document-reviewer
- skill-verification-before-completion
- skill-finishing-a-development-branch

Files And Symbols:
- Modify: `evaluation/probes/run_optimization_probe.py:workload execution, _measure_workbook, _soak_receipt`
- Modify: `evaluation/probes/optimization_measurement.py:sample aggregation, distribution summary, evidence status`
- Modify: `evaluation/probes/compare_optimization_receipts.py:required evidence validation`
- Modify: `tests/test_optimization_measurement.py`
- Modify: `docs/architecture.md`, `docs/evidence-and-evaluation.md`, and
  `docs/extending.md` only where their claims or examples contradict the new
  canonical contracts.
- Create: `work/foresight-os-correctness-deletion-pass/final-receipt.md`
- Do not commit raw benchmark samples, allocation dumps, or generated probe
  state.

Steps:
1. Reuse the frozen protocol and exact base workload for every comparable final
   run. Make `changed_selection` execute an alternate selection and assert unchanged
   snapshot/capture counts, allowed parsing, and the expected alternate value.
   Make `repeated_run` execute the real workbook/investigation path instead of
   assigning a verified status. Derive `local_tool_calls` from runtime counters.
2. Add small, medium, and large retained-context workloads and assert a warm hit
   has zero new capture, hash, parse, or authority publication while latency and
   retained bytes remain bounded.
3. Add a multi-workbook soak using independent sources in one `WorkbookContext`;
   assert one snapshot per source, no cross-source authority aliasing, bounded
   aggregate retention, deterministic eviction, and zero owned resources after
   cleanup. Treat failed close as failed cleanup, not as a completed cleanup
   attempt.
4. Add a real cancellation workload using a blocking spreadsheet read; assert
   worker observation, worker failure settlement, caller `CancelledError`, no
   failed cache/authority publication, scope settlement, and truthful cleanup
   success/failure.
5. Predeclare five process-level runs with ten samples per run. Report median
   p50, median p95, maximum p95, observed range, threshold violations, correctness
   status, allocation diagnostics, and resource-soak status. Compare only
   workloads with a valid base measurement; label newly added workloads
   `FINAL_ONLY`. Missing mandatory evidence is incomplete, while optional
   performance dimensions may be `NOT_MEASURED`. Do not select a passing rerun
   after observing the results.
6. Keep performance language limited to the executed fixture/workload, for
   example `analyst_multisheet.xlsx warm-read p95`, and do not claim arbitrary
   investigation speedups without a full investigation workload.
7. Replace release-specific raw logs with one final acceptance table containing
   requirement, proof command, result, and named limitation. Record whether
   process-global compatibility was deleted or explicitly deferred.
8. Run the final verification commands on the exact final tree, reconcile every
   task and approved deferral in this plan, and mark the implementation complete
   only when all mandatory evidence gates pass. A verification skill may
   summarize the evidence but is not itself the truth condition.

Verification:
- `python evaluation/probes/run_optimization_probe.py --mode release --fixture tests/fixtures/analyst_multisheet.xlsx --output work/foresight-os-correctness-deletion-pass/final-optimization.json --measurement-mode full`
- `python evaluation/probes/compare_optimization_receipts.py --baseline work/foresight-os-correctness-deletion-pass/baseline-optimization.json --release work/foresight-os-correctness-deletion-pass/final-optimization.json`
- `python -m pytest -q tests/test_optimization_measurement.py tests/test_local_toolbelt.py tests/test_runtime_boundaries.py tests/test_orchestration_patterns.py`
- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `python scripts/check_markdown_links.py README.md AGENTS.md docs/architecture.md docs/evidence-and-evaluation.md evaluation/README.md --tracked-docs`
- `git diff --check`
- `git status --short --branch`
- Expected: every labeled workload executes, evidence statuses are truthful,
  comparable workloads use exactly the same protocol on base and final,
  new workloads are labeled `FINAL_ONLY`, missing mandatory evidence is not a
  pass, distributions are reported without cherry-picking, all required tests
  pass, and no unrelated tracked files were modified.

Exit Criteria:
- The final receipt proves the exact verified source tree; unmeasured evidence
  is labeled `NOT_MEASURED` or `DEFERRED`; no persistent parsed-workbook cache
  or second ownership layer is introduced; and branch publication remains a
  separate authorized Git disposition.

## Completion Criteria

## Approved Deferrals

- Broader NormalizedIntent and topology migration remains deferred. The
  mandatory serialized contract/scoping cleanup is complete; expanding the
  controller migration would widen this correctness pass without reducing the
  verified workbook, lifecycle, or receipt risk addressed here.
- The standalone process-global authority fallback remains as an isolated
  compatibility adapter for direct callers. Normal scoped execution uses the
  run-owned AuthorityIndex; removing the adapter is deferred until standalone
  caller migration has an explicit compatibility plan.

1. Two stages using the same domain cannot overwrite each other's contracts;
   ordered immutable representation, precedence, unknown IDs, explicit empty
   scope, and legacy unknown scope are all tested.
2. Contract identity remains stable through schema, normalization, stage input,
   execution gate, fingerprint, receipt, invalidation, and selective reuse.
3. Contract changes invalidate the consuming stage and stale downstream
   dependencies, but not unrelated branches.
4. WorkBrief save/load and recipe serialization round-trip same-domain
   stage-specific contracts with one canonical representation.
5. Explicit missing mappings fail per intended table, and omitted mappings alone
   trigger compatibility fallback; exact periods remain exact through analyzers.
6. Portability tests prove expected values, source ranges, units, provenance,
   anomalies, and unsupported outcomes.
7. Caller cancellation remains `asyncio.CancelledError` after worker settlement
   and cleanup, including secondary worker/cleanup failures and repeated
   cancellation.
8. Admission never invokes a resource factory; owned resources settle exactly
   once on partial and normal activation paths; `cleanup_complete` reflects
   actual close success.
9. Participant correction uses stable IDs and never filtered-list positions;
   unsupported targeted recovery stops explicitly.
10. Required invalid relationships are never silently dropped, and direct and
    synthesized outputs share payload and record safety bounds.
11. Synthesis detects dependency cycles, observes cancellation during substantial
    work, and limits actual traversal without treating domain relationships as
    calculation edges.
12. Warm hits avoid capture, hashing, parsing, authority re-registration, and
    authority traversal; dependent views cannot outlive required authority;
    failed first reads leak no snapshots; retained accounting is O(1).
13. Standalone workbook reads enforce `max_bytes` through the same bounded path.
14. Stage fingerprints are computed once and reused through cache/reuse/receipt
    logic.
15. Mandatory controller contract/scoping cleanup is complete. Broader
    `NormalizedIntent`/topology migration is either delivered as a bounded
    reduction of duplicate policy or explicitly deferred with a reason.
16. Normal execution has no process-global analytical authority dependency, or
    any retained standalone adapter is isolated, documented, and explicitly
    deferred.
17. Comparable benchmark metrics use exactly the same frozen protocol on base
    and final; new workloads are labeled `FINAL_ONLY`; labels match executed
    workloads; counters are measured.
18. Timing, allocation, soak, and correctness remain separate evidence classes;
    missing mandatory evidence is incomplete, optional dimensions may be
    `NOT_MEASURED`, and no passing rerun is selected after observation.
19. Final focused and broad verification passes, Markdown links, diff hygiene,
    receipts, exact source-tree identity, and unrelated-file isolation reconcile.

## Self-Review

- Verdict coverage: the justified revisions are mapped to Tasks 1–5; the
  recommended three change sets remain correctness/identity,
  overhead/recovery deletion, and migration/proof, with benchmark freezing
  before production changes and Task 4 independently deliverable.
- Ownership: `AnalysisInputContract` and `NormalizedIntent` remain under
  `domain/analysis_inputs.py`; recipe policy remains under `controller`; runtime
  ownership remains `CapabilityScope` → `WorkbookContext`; durable state remains
  `AnalysisStore`; benchmark truth remains under `evaluation/probes`.
- Compatibility: legacy WorkBrief and recipe inputs translate once into
  canonical fields; no second live policy source is retained.
- Recovery: correction remains one bounded participant-local rerun; material
  conflicts stop rather than enabling broad tolerance.
- Performance: structural reuse, wall-clock distributions, allocation, retained
  resources, and correctness are separate evidence classes.
- Scope: no new registry, persistent parsed workbook cache, recovery engine,
  graph framework, analytical store, or orchestration pattern is authorized.
- Handoff: plan status is `proposed`; plan-document review and explicit human
  approval are required before execution.
