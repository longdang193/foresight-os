---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: foresight-os-three-delivery-increments
targets:
  - src/foresight_os/domain/
  - src/foresight_os/controller/
  - src/foresight_os/runtime/
  - src/foresight_os/analysis/
  - src/foresight_os/graph/
  - src/foresight_os/persistence/
  - src/foresight_os/artifacts/
  - src/foresight_os/schemas/
  - src/foresight_os/skills/
  - evaluation/
  - tests/
  - pyproject.toml
  - README.md
---

# Foresight OS Three Delivery Increments

## Goal

Deliver the approved three-increment architecture from repository baseline
`38e1596d23b1e9c0c548b1dcd82d2f0538113d21` without reimplementing runtime and
XLSX optimization already present on `main`. Preserve Microsoft Agent
Framework, Controller, CapabilityResolver, AnalysisState, deterministic data
tools, and NetworkX as a derived projection.

The existing untracked `build/`, `src/foresight_os.egg-info/`, and `work/`
outputs are preserved generated or investigation outputs. They are not
canonical implementation sources.

**Review disposition:** `review-1` completed the maximum two review turns.
The three final findings are resolved in Tasks 5, 8, and the Verification
section before execution may begin.

## Implementation Outcomes

### Increment A — execution and correctness
WorkBrief and WorkStage are generic and independently executable. Controller
routing is stage-first, specialist selection is independent, override
precedence is explicit, and graph queries are bounded and relation-aware.
Existing runtime and XLSX safeguards remain true through the new path.

### Increment B — analytical capability
A small local skill package contains real `SKILL.md` method content and injects
selected content deterministically. AnalyticalRecord remains canonical with
minimal uncertainty and assumption fields. Direct evidence support and
analytical support use separate authorities. Immutable ReviewRecord values bind
review to material inputs, and FindingView is derived.

### Increment C — selective efficiency
Unchanged material inputs and valid reviews are reused; only affected
stage-descendants are reassessed. Metrics prove correctness and efficiency.
Monitoring is optional and on-demand. Packaging and documentation agree with
canonical source ownership.

Non-goals: second orchestrator, graph database, Finding store, entity/SPO
ontology, runtime skill downloads, continuous monitoring scheduler, or numeric
probability confidence.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-executing-plans`, `skill-backend-verification`, `skill-plan-document-reviewer`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit canonical files named by the active task, run declared local checks, and preserve existing untracked outputs
- User-approval actions: push, merge, publication, external writes, destructive recovery, deletion or cleanup of existing untracked outputs, and architecture-boundary changes
- Parallel ownership: none
- Sequential fallback: Tasks 1–8 in order, with an increment gate after Tasks 3 and 6

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `38e1596d23b1e9c0c548b1dcd82d2f0538113d21`
- Expected workspace: current tracked state plus preserved untracked `build/`, `src/foresight_os.egg-info/`, and `work/`
- Next action: none; execution complete
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
|---|---|---|---|---|---|---|
| Task 1 | `completed` | current | `unresolved` | none | baseline classification | focused baseline suite passed; classification recorded |
| Task 2 | `completed` | current | `unresolved` | Task 1 | WorkBrief/WorkStage and Controller tests | focused research-needs, persistence, Controller, orchestration, Group Chat, and tool-pattern suite passed |
| Task 3 | `completed` | current | `unresolved` | Tasks 1–2 | graph and runtime/XLSX regression proof | relation-aware graph/runtime suite passed; baseline/release receipts compared within p95/allocation/tool-call gates |
| Task 4 | `completed` | current | `unresolved` | Tasks 1–3 | skill package and stage transport proof | six hashed skills packaged; stage-local transport and capability denial tests passed |
| Task 5 | `completed` | current | `unresolved` | Tasks 2–4 | analytical schema and authority proof | exact analytical fields, migration, deterministic material fingerprints, and persistence tests passed |
| Task 6 | `completed` | current | `unresolved` | Tasks 4–5 | review, FindingView, vertical slice | immutable reviews, derived FindingView, recommendation gate, and recovery tests passed |
| Task 7 | `completed` | current | `unresolved` | Task 6 | selective reuse and recovery proof | committed cache hits skip new calls; pending entries reassess; full suite passed |
| Task 8 | `completed` | current | `unresolved` | Task 7 | metrics, package, docs, final proof | contract/controller matrices, disposable MCP invocation and cleanup, optimization comparison, selective-reuse evaluation, disposable wheel resource inspection, full suite, diff check, and final status passed |

## Task Breakdown

## Increment A — Execution and correctness

### Task 1: Reconcile the current baseline

**Purpose:** Remove duplicate implementation work and establish the exact delta from `38e1596`.

**Task Function:** Inspect, classify, and record repository truth.

**Template Profile:** Controller-selected: `unresolved while task is pending`.

**Validator Profile:** Controller-selected: `unresolved while task is pending`.

**Specification Coverage:** Classify every planned area as `OPEN`, `PARTIALLY SATISFIED`, or `ALREADY SATISFIED`; verify existing runtime/XLSX optimization instead of reimplementing it.

**Required Skills:** `skill-plan-document-reviewer`; `skill-backend-verification`.

**Files And Symbols:** Inspect `src/foresight_os/runtime/capabilities.py:CapabilityScope`, `CapabilityResolver`, `src/foresight_os/runtime/workflow.py:run_recipe_async`, `src/foresight_os/runtime/participants.py:AgentFactory`, `src/foresight_os/analysis/workbook.py`, `src/foresight_os/graph/projection.py:GraphView`, `src/foresight_os/domain/relationships.py:relationship_rule`, `src/foresight_os/persistence/invalidation.py:invalidate_dependencies`, `tests/test_runtime_boundaries.py`, `tests/test_tool_enabled_patterns.py`, `tests/test_local_toolbelt.py`, `tests/test_graph.py`, `pyproject.toml`.

**Dependencies:** None.

**Authority:**
- Preauthorized local actions: read source/tests/configuration and run focused baseline commands without editing implementation files.
- Stop for: conflicting repository truth, architecture-boundary change, or deletion of preserved outputs.

**Steps:**
- [x] Record `git status --short --branch` and `git rev-parse HEAD`.
- [x] Map former runtime, XLSX, graph, persistence, and package requirements to current sources and tests.
- [x] Run `python -m pytest -q tests/test_runtime_boundaries.py tests/test_tool_enabled_patterns.py tests/test_local_toolbelt.py tests/test_graph.py tests/test_package_resources.py`.
- [x] Record the classification and convert satisfied work into regression proof in Tasks 3 and 8.

**Verification:**
- [x] HEAD is `38e1596d23b1e9c0c548b1dcd82d2f0538113d21`.
- [x] Focused baseline tests exit `0`.
- [x] Preserved untracked outputs are unchanged.

**Baseline Classification:**
- `ALREADY SATISFIED`: run-owned capability scope, semaphores, bounded blocking execution, cancellation settlement, MCP middleware, provider cleanup, runtime metrics, XLSX formula blocking, missing-value status, and package dependency; focused baseline suite passed.
- `PARTIALLY SATISFIED`: GraphView identity, relationship direction rules, cycle-safe traversal, and bounded context exist; query behavior still needs relation-specific indexes/truncation proof.
- `OPEN`: generic Wayfinding, stage-first routing, stage-local skill transport, packaged method content, analytical extensions, ReviewRecord/FindingView, and selective stage reuse.

**Exit Criteria:** The lead accepts the classification and no later task duplicates satisfied work.

### Task 2: Make WorkBrief and WorkStage generic and route stages first

**Purpose:** Replace case-specific Wayfinding assumptions and positional routing with executable stage contracts.

**Task Function:** Update domain, schema, Controller, and compatibility owners together.

**Template Profile:** Controller-selected: `unresolved while task is pending`.

**Validator Profile:** Controller-selected: `unresolved while task is pending`.

**Specification Coverage:** WorkBrief is generic; WorkStage owns objective, dependencies, participants, research needs, expected result, `skill_ids`, pattern, and limits; stages execute once in dependency order; specialist and pattern selection are independent; precedence is stage override, global override, then Controller selection; Group Chat remains first-class; Handoff cannot consume downstream stages.

**Required Skills:** `skill-code-standards`; `skill-backend-verification`.

**Files And Symbols:** Update `src/foresight_os/domain/models.py:WorkBrief`, `WorkStage`, `src/foresight_os/wayfinding.py:create_work_brief`, `src/foresight_os/controller/recipes.py:RecipeStage`, `ExecutionRecipe`, `make_recipe`, `src/foresight_os/controller/policy.py`, `src/foresight_os/domain/validation.py:validate_work_brief`, `_normalize_work_brief`, `src/foresight_os/schemas/work_brief.schema.json`, and `src/foresight_os/persistence/analysis_store.py:load_brief`. Do not use `migrate_analysis_dict` for brief compatibility. Extend `tests/test_research_needs.py`, `tests/test_persistence.py`, `tests/test_controller_selection.py`, `tests/test_orchestration_patterns.py`, and `tests/test_group_chat.py`.

**Dependencies:** Task 1 confirms the contract is `OPEN` or `PARTIALLY SATISFIED`.

**Authority:**
- Preauthorized local actions: edit the named domain, Controller, validation, persistence, schema, and test files.
- Stop for: a second workflow engine, changed Agent Framework boundary, or incompatible legacy brief migration.

**Steps:**
- [x] Remove hard-coded geography/horizon values from generic brief construction.
- [x] Add `skill_ids`, pattern, and limits to WorkStage and normalize old briefs through `_normalize_work_brief` and `validate_work_brief` defaults.
- [x] Update `load_brief` to reconstruct every new stage field explicitly.
- [x] Route recipes by stage ID and enforce override/topology rules.

**Verification:**
- [x] Legacy `brief.md` and a new brief with skills/pattern/limits both round-trip through `validate_work_brief` and `AnalysisStore.load_brief`.
- [x] Reordered stages execute once by dependency order.
- [x] Focused Controller, persistence, orchestration, Group Chat, and research-needs tests exit `0`.

**Exit Criteria:** Generic brief/stage contracts and stage-first routing are deterministic and backward-compatible.

### Task 3: Make graph queries relation-aware and preserve runtime/XLSX guarantees

**Purpose:** Complete graph-query correctness while proving the existing optimization pass remains true.

**Task Function:** Update bounded graph queries and add regression proof, not duplicate low-level runtime/XLSX implementation.

**Template Profile:** Controller-selected: `unresolved while task is pending`.

**Validator Profile:** Controller-selected: `unresolved while task is pending`.

**Specification Coverage:** GraphView remains derived with investigation/revision identity. Relationship rules own semantic, provenance, and impact direction. Queries are deterministic, cycle-safe, bounded, and report truncation. Missing operands remain `delta=None`/`INCOMPLETE_INPUT`; formula/error/stale-cache inputs remain blocked.

**Required Skills:** `skill-backend-verification`; `skill-performance-optimization`.

**Files And Symbols:** Update `src/foresight_os/graph/queries.py:get_impacted_records`, `get_impacted_records_complete`, `trace_provenance`, `get_evidence`, `get_counterevidence`, `get_context`; inspect `src/foresight_os/graph/projection.py:GraphView`, `src/foresight_os/domain/relationships.py:relationship_rule`, `src/foresight_os/runtime/capabilities.py:CapabilityScope`, `src/foresight_os/runtime/workflow.py:run_recipe_async`, `src/foresight_os/analysis/workbook.py`; extend `tests/test_graph.py`, `tests/test_runtime_boundaries.py`, `tests/test_tool_enabled_patterns.py`, `tests/test_local_toolbelt.py`, and `tests/test_calculation_revision.py`.

**Dependencies:** Tasks 1–2.

**Authority:**
- Preauthorized local actions: edit graph query/projection and focused regression tests; run the named identical-workload probe.
- Stop for: second graph authority, changed runtime limits, or trusted treatment of missing/stale formula data.

**Steps:**
- [x] Map each query to allowed relationship-rule direction and define bound, cycle, ordering, and truncation behavior.
- [x] Implement provenance, evidence, counterevidence, context, and impact queries.
- [x] Add runtime/XLSX regression assertions through the new stage-to-analysis path.
- [x] Run the exact baseline/release probe commands below with the same interpreter and fixture.

**Verification:**
- [x] `python -m pytest -q tests/test_graph.py tests/test_runtime_boundaries.py tests/test_tool_enabled_patterns.py tests/test_local_toolbelt.py tests/test_calculation_revision.py` exits `0`.
- [x] Run `python evaluation/probes/run_optimization_probe.py --mode baseline --fixture tests/fixtures/analyst_multisheet.xlsx --output work/optimization-plan/baseline/receipt.json` and the same command with `--mode release --output work/optimization-plan/release/receipt.json`.
- [x] Both receipts report the same workload (`2` warmups, `10` measured runs, `100` soak runs), use the same Python interpreter and fixture, and report native MCP status separately from performance comparisons.
- [x] A comparison script or test calculates p95 latency, peak allocation, and tool calls per finding from both receipts; the acceptance gate is p95 regression ≤20%, peak allocation regression ≤15%, and tool calls per finding not increased.

**Exit Criteria:** Increment A passes when stage semantics and relation-aware queries do not regress the existing execution/data substrate.

## Increment B — Analytical capability

### Task 4: Package real skill content and transport it stage-locally

**Purpose:** Make `skill_ids` executable method content rather than decorative metadata.

**Task Function:** Build a local registry and carry selected skills from WorkStage through recipe dispatch to AgentFactory.

**Template Profile:** Controller-selected: `unresolved while task is pending`.

**Validator Profile:** Controller-selected: `unresolved while task is pending`.

**Specification Coverage:** The manifest contains ID, version, content path/hash, capability requirements, output contract, and provenance. Six bundled `SKILL.md` files define inputs, use conditions, steps, output, and abstention. `WorkStage.skill_ids` → `RecipeStage.skill_ids` → `ParticipantConfig.skill_ids` → stage-local `selected_skills` context → `AgentFactory` injection. No downloads or per-skill agents.

**Required Skills:** `skill-code-standards`; `skill-backend-verification`.

**Files And Symbols:** Add `src/foresight_os/controller/skills.py:SkillManifest`, `ResolvedSkill`, `SkillRegistry`; add `src/foresight_os/skills/manifest.json` and six `SKILL.md` files for `source-appraisal`, `key-assumptions-check`, `quantitative-sanity-check`, `red-team-claim`, `abstain-or-escalate`, and `scenario-planning`; update `src/foresight_os/controller/recipes.py:RecipeStage`, `src/foresight_os/runtime/participants.py:ParticipantConfig`, `AgentFactory.create`, `src/foresight_os/runtime/workflow.py:dispatch_stage`, `pyproject.toml`; add `tests/test_skills.py` and extend package/runtime/controller tests.

**Dependencies:** Tasks 1–3.

**Authority:**
- Preauthorized local actions: add bundled skill files, registry, stage transport, AgentFactory integration, package metadata, and tests.
- Stop for: runtime downloads, unverified external content, or capability permission expansion.

**Steps:**
- [x] Define concrete manifest/resolved-skill values and hash verification.
- [x] Write six method files and package them as resources.
- [x] Add `skill_ids` fields to recipe and participant contracts.
- [x] Pass only each stage’s selected skills through `dispatch_stage` and inject them in AgentFactory.
- [x] Test two stages with different skill selections and no cross-stage leakage.

**Verification:**
- [x] Skill, runtime, controller, and package-resource tests exit `0`.
- [x] Unknown skills and unavailable required capabilities fail before agent construction.
- [x] Six content hashes match the manifest and all six resources appear in the package build.

**Exit Criteria:** A stage selects and executes real bundled method content deterministically.

### Task 5: Define the minimal analytical contract and evidence authority

**Purpose:** Remove implementation-time ambiguity from AnalyticalRecord and material-input selection.

**Task Function:** Update models, schemas, migration, validation, persistence, projection, and report serialization as one contract.

**Template Profile:** Controller-selected: `unresolved while task is pending`.

**Validator Profile:** Controller-selected: `unresolved while task is pending`.

**Specification Coverage:** AnalyticalRecord adds exactly these fields with defaults: `assumptions: tuple[str, ...] = ()`, `uncertainty: tuple[str, ...] = ()`, `confidence_rationale: str = ""`, and `disconfirmation_conditions: tuple[str, ...] = ()`. Existing `statement`, `basis`, `assessment`, `evidence_ids`, and `relationship_ids` remain canonical. No SPO/entity fields.

Direct evidence support is `Evidence -> AnalyticalRecord`, derived only from target `evidence_ids`. Analytical support is `AnalyticalRecord -> AnalyticalRecord`, stored as canonical Relationship. Calculation dependencies are selected from `CalculationRecord.input_ids` reachable from target evidence IDs; include the target calculation and its transitive inputs, stop at missing IDs, sort IDs, and record missing inputs as limitations. Assumptions and counterevidence are selected from the target record and relationship closure following provenance direction; cycles use a visited set and do not duplicate IDs.

**Required Skills:** `skill-code-standards`; `skill-backend-verification`.

**Files And Symbols:** Update `src/foresight_os/domain/models.py:AnalyticalRecord`, `AnalysisState`, `src/foresight_os/domain/validation.py:validate_analysis`, `migrate_analysis_dict`, `src/foresight_os/schemas/analysis.schema.json`, `src/foresight_os/persistence/analysis_store.py`, `src/foresight_os/graph/projection.py:build_graph`, and `src/foresight_os/artifacts/report.py:render_report`; extend `tests/test_analysis_schema.py`, `tests/test_persistence.py`, `tests/test_graph.py`, and `tests/test_report_fidelity.py`.

**Dependencies:** Tasks 2–4.

**Authority:**
- Preauthorized local actions: edit the named analytical sources, schemas, persistence, projection, report, and tests.
- Stop for: a second assertion store, numeric probability confidence, or entity/SPO modeling.

**Steps:**
- [x] Add the exact fields/defaults above and preserve legacy state.
- [x] Update schema, `migrate_analysis_dict`, validation, persistence, graph projection, and report rendering.
- [x] Implement deterministic material-input selection with the stated traversal and missing-input rules.
- [x] Validate direct evidence support separately from analytical support.

**Verification:**
- [x] Legacy state migrates with empty defaults and no invented certainty.
- [x] Direct evidence edges disagreeing with `evidence_ids` fail; analytical support relationships are checked independently.
- [x] Calculation, assumption, counterevidence, and missing-input fixtures produce the specified material sets and limitations.
- [x] Analytical schema, persistence, graph, and report tests exit `0`.

**Exit Criteria:** Increment B has a minimal, backward-compatible analytical contract with deterministic material-input selection.

### Task 6: Add immutable ReviewRecord, derived FindingView, and one adversarial slice

**Purpose:** Bind challenge outcomes to exact material inputs and keep FindingView derived.

**Task Function:** Implement typed review persistence, validity comparison, finding projection, and one end-to-end adversarial case.

**Template Profile:** Controller-selected: `unresolved while task is pending`.

**Validator Profile:** Controller-selected: `unresolved while task is pending`.

**Specification Coverage:** In `src/foresight_os/domain/challenge.py`, define `ChallengeObjection(kind, target_id, statement, evidence_ids, disposition)`, with dispositions `ACCEPTED`, `REJECTED`, `UNRESOLVED`; `ReviewOutcome` values `ACCEPTED`, `PROVISIONAL`, `REJECTED`; and immutable `ReviewRecord(review_id, target_ids, reviewed_state_revision, input_fingerprint, skill_ids, skill_versions, objections, outcome, limitations, unresolved_issues)`. Add `AnalysisState.review_records` with an empty default. FindingView is never persisted.

`build_material_fingerprint(state, target_ids, skill_ids)` hashes canonical sorted target IDs/content, direct evidence IDs plus versions/hashes, calculations selected by Task 5 rules including formulas/results, target assumptions/dependencies, counterevidence, and skill IDs/versions/content hashes. It excludes global AnalysisState.revision. `review_validity` returns `CURRENT` only on exact equality. `select_review_record` chooses valid review with greatest reviewed revision, then smallest review ID; no valid review yields `PENDING_REVIEW`. Accepted consequential recommendations require selected valid `ACCEPTED` review and no unresolved objection. Provisional reports preserve limitations and unknowns.

**Required Skills:** `skill-backend-verification`; `skill-test-driven-development`.

**Files And Symbols:** Add/update `src/foresight_os/domain/challenge.py`, `src/foresight_os/domain/models.py:AnalysisState`, `src/foresight_os/domain/validation.py:validate_analysis`, `migrate_analysis_dict`, `src/foresight_os/schemas/analysis.schema.json`, `src/foresight_os/persistence/analysis_store.py`, `src/foresight_os/persistence/invalidation.py:invalidate_dependencies`, `src/foresight_os/analysis/reviewer.py:ReviewResult`, `src/foresight_os/artifacts/report.py:render_report`, `src/foresight_os/vertical_slice.py`; add `tests/test_review_records.py`, `tests/test_finding_view.py`, and `evaluation/cases/case-006/`.

**Dependencies:** Tasks 4–5.

**Authority:**
- Preauthorized local actions: add the named review/finding domain, schema, migration, persistence, report, evaluation, and tests.
- Stop for: persisted Finding lifecycle, mutable ReviewRecord staleness, global revision in fingerprints, or hidden unresolved limitations.

**Steps:**
- [x] Add concrete types, `AnalysisState.review_records`, schema entries, legacy migration defaults, validation, and persistence reconstruction; keep FindingView out of persisted state.
- [x] Implement fingerprint, validity, and review-selection helpers with deterministic tests for every material input category and unrelated-input preservation.
- [x] Derive FindingView and gate accepted consequential recommendations.
- [x] Run the adversarial Brief → Skills → Evidence → Analysis → Challenge → Review → FindingView → Report slice.

**Verification:**
- [x] Legacy analysis without reviews round-trips with empty reviews; a ReviewRecord round-trips through `analysis.json` in a fresh process.
- [x] Unrelated input leaves review `CURRENT`; each fingerprinted input makes it `STALE`.
- [x] Missing/stale formula produces provisional/blocked output and cannot authorize acceptance.
- [x] Review, schema, persistence, vertical-slice, invalidation, and report tests exit `0`.

**Exit Criteria:** Increment B preserves traceability and uncertainty through the complete analytical path.

## Increment C — Efficiency and refinement

### Task 7: Reuse valid material and reassess only affected descendants

**Purpose:** Reduce repeated operations without weakening provenance, review validity, invalidation, or recovery.

**Task Function:** Add content-keyed reuse and cache-aware stage dispatch.

**Template Profile:** Controller-selected: `unresolved while task is pending`.

**Validator Profile:** Controller-selected: `unresolved while task is pending`.

**Specification Coverage:** A complete cache hit counts as ordered stage completion, supplies typed dependency output, emits a cache-hit metric, and consumes zero new model/tool calls. Only committed entries with complete provenance are reusable after restart; pending/partial entries rerun. Changed material invalidates only impact-directed descendants and affected review fingerprints.

**Required Skills:** `skill-backend-verification`; `skill-performance-optimization`.

**Files And Symbols:** Update `src/foresight_os/persistence/invalidation.py:invalidate_dependencies`, `src/foresight_os/persistence/analysis_store.py:AnalysisStore`, `src/foresight_os/graph/queries.py:get_impacted_records`, `src/foresight_os/analysis/evidence_workflow.py`, `src/foresight_os/analysis/workbook.py:calculate_case_metrics`, `src/foresight_os/controller/skills.py:SkillRegistry`, `src/foresight_os/controller/recipes.py:ExecutionRecipe`, `src/foresight_os/runtime/workflow.py:run_recipe_async`, `dispatch_stage`, and `src/foresight_os/runtime/metrics.py`; extend invalidation, calculation, recovery, evidence, graph, and review tests.

**Dependencies:** Task 6.

**Authority:**
- Preauthorized local actions: edit reuse, invalidation, dispatch, metrics, evaluation, and focused tests named above.
- Stop for: provenance bypass, ignored impact direction, lost revision, or hidden recovery conflict.

**Steps:**
- [x] Define material cache keys from content/version identity, not global revision.
- [x] Reuse only after provenance, capability, formula-status, and fingerprint checks.
- [x] Let `run_recipe_async` treat complete cache hits as stage completion and dispatch only affected stages in dependency order.
- [x] Test unrelated updates, affected updates, repeated runs, fresh-process recovery, and writer conflicts.

**Verification:**
- [x] Unchanged stage makes zero new model/tool calls and supplies downstream output; affected stage runs in cold-run order.
- [x] `python evaluation/run.py --case evaluation/cases/case-001 --compare ordinary,semantic,sequential,controller --output-root work/selective-reuse-plan` records cold/warm calls, reuse, reassessment, and recovery.
- [x] Unrelated-input acceptance requires zero new calls for unaffected stages; affected-input acceptance requires only impacted descendants to recompute.
- [x] Focused reuse/recovery tests exit `0`.

**Exit Criteria:** Selective updates reduce repeated operations without correctness or recovery regression.

### Task 8: Measure, package, document, and finish verification

**Purpose:** Close delivery with executable quality, package, and boundary proof.

**Task Function:** Reconcile metrics, optional monitoring, resources, documentation, and final verification.

**Template Profile:** Controller-selected: `unresolved while task is pending`.

**Validator Profile:** Controller-selected: `unresolved while task is pending`.

**Specification Coverage:** Metrics cover quality, traceability, stale review, recovery, calls, latency, reuse, reassessment, and correction effort where measurable. MonitoringIndicator is optional and on-demand over ordinary Evidence. Deterministic all-pattern tests are mandatory. Live provider/MCP checks are optional only when configured and must prove invocation/cleanup; unavailable configuration is an explicit deferral.

**Required Skills:** `skill-backend-verification`; `skill-performance-optimization`; `skill-verification-before-completion`.

**Files And Symbols:** Update `evaluation/run.py`, `evaluation/rubric.md`, `evaluation/README.md`, `README.md`, `pyproject.toml`, `src/foresight_os/artifacts/report.py`, and optional `src/foresight_os/domain/models.py:MonitoringIndicator`; extend evaluation, report, package, runtime, and pattern tests. Update `evaluation/probes/run_mcp_probe.py:_real_mcp` and its tests to perform a real configured invocation and report `VERIFIED` only after invocation and cleanup evidence; retain `BLOCKED_EXTERNAL` only for absent configuration.

**Dependencies:** Task 7 and Increment A/B gates.

**Authority:**
- Preauthorized local actions: update metrics, optional indicators, package metadata, evaluation probes, docs, tests, and final checks.
- Stop for: credentials/external writes, continuous monitoring infrastructure, generated-source edits, or final status change before verification.

**Steps:**
- [x] Add metrics and deterministic reports for quality and selective reuse.
- [x] Record the explicit late-C deferral of a continuous `MonitoringIndicator` scheduler; scenario signposts remain reportable skill output only.
- [x] Reconcile docs, package data, schemas, skill resources, and evaluation.
- [x] Run `python evaluation/run.py --matrix contract`, `python evaluation/run.py --matrix controller`, and `python evaluation/probes/run_mcp_probe.py --mode disposable --output-root work/live-smoke/mcp`.
- [x] Configured live-provider/MCP execution is optional; this run records the disposable MCP invocation and cleanup proof, with no configured real-MCP boundary to execute.
- [x] Build from a disposable source copy outside preserved outputs, inspect wheel resources, and remove only the verified task-owned temporary directory.

**Verification:**
- [x] `python -m pytest -q` exits `0`.
- [x] Deterministic contract/controller matrices report `passed: true` for all native patterns.
- [x] Configured live-provider/MCP receipts prove invocation and cleanup; missing configuration is recorded as an explicit optional-boundary deferral.
- [x] Disposable-copy wheel contains schemas, manifest, and six skill resources without changing preserved outputs.
- [x] `git diff --check` exits `0`; `git status --short --branch` shows only in-scope changes plus preserved outputs.

**Exit Criteria:** Final proof is fresh, selective reuse is measured, optional monitoring is implemented or explicitly deferred, and completion verification can run.

## Verification

Final verification is owned by `skill-verification-before-completion` after
all task-local proof passes:

- `python -m pytest -q`
- `python evaluation/run.py --matrix contract`
- `python evaluation/run.py --matrix controller`
- the Task 3 baseline/release optimization receipts and comparison output
- the Task 7 selective-reuse report
- disposable-copy wheel/resource inspection
- configured live-provider and real-MCP receipts, or explicit unavailable-boundary deferrals
- `git diff --check`
- `git status --short --branch`

## Completion Criteria

1. Every WorkStage is generic, stage-first, dependency-ordered, and backward-compatible.
2. Graph queries are bounded, relation-aware, deterministic, and cycle-safe.
3. Existing runtime/XLSX safeguards remain true through the new path.
4. Six packaged skills resolve, hash-verify, and inject through stage-local transport.
5. AnalyticalRecord has the exact minimal contract and deterministic material-input selection.
6. Direct evidence support and analytical support use separate canonical authorities.
7. ReviewRecord is immutable; validity is content-based; FindingView is pure derived state.
8. Selective reuse treats complete cache hits as stage completion and reassesses only affected descendants.
9. Performance receipts compare identical workloads and enforce explicit thresholds including measurable calls-per-finding.
10. Real-MCP verification proves invocation and cleanup; unavailable configuration is not reported as a pass.
11. Packaging, tests, evaluation, docs, and preserved workspace outputs agree with canonical ownership.
12. `skill-verification-before-completion` returns `verified` before status changes from `proposed` or `active`.
