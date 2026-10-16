---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: foresight-os-brief-portability-execution-simplification
targets:
  - src/foresight_os/domain/analysis_inputs.py
  - src/foresight_os/domain/models.py
  - src/foresight_os/domain/validation.py
  - src/foresight_os/schemas/work_brief.schema.json
  - src/foresight_os/wayfinding.py
  - src/foresight_os/persistence/analysis_store.py
  - src/foresight_os/artifacts/brief.py
  - src/foresight_os/analysis/workbook_inputs.py
  - src/foresight_os/analysis/portfolio_resilience.py
  - src/foresight_os/analysis/supplier_resilience.py
  - src/foresight_os/analysis/ev_capacity_investment.py
  - src/foresight_os/analysis/technology_radar.py
  - src/foresight_os/analysis/powerbi_strategic_portfolio.py
  - src/foresight_os/analysis/foresight_validator.py
  - src/foresight_os/runtime/execution_gate.py
  - src/foresight_os/controller/policy.py
  - src/foresight_os/controller/recipes.py
  - src/foresight_os/runtime/workflow.py
  - src/foresight_os/runtime/capabilities.py
  - tests/test_analysis_input_contract.py
  - tests/test_work_brief_compatibility.py
  - tests/test_portfolio_resilience.py
  - tests/test_supplier_and_ev_resilience.py
  - tests/test_technology_powerbi_validator.py
  - tests/test_brief_portability.py
  - tests/test_controller_selection.py
  - tests/test_stage_inputs.py
  - tests/test_capabilities.py
  - tests/test_runtime_boundaries.py
  - evaluation/probes/run_brief_portability_probe.py
  - evaluation/README.md
  - docs/architecture.md
  - docs/evidence-and-evaluation.md
  - docs/superpowers/plans/2026-10-16-00-52-foresight-os-brief-portability-execution-simplification-plan.md
---

# ForesightOS Brief Portability And Execution Simplification

## Goal

Make the next production workbook investigation portable across materially different briefs without adding another orchestration, cache, provenance, or business-rules subsystem.

The implementation will normalize an approved `WorkBrief` once, resolve a typed `AnalysisInputContract`, pass verified tabular inputs into the existing domain-specific analyses, and generate narrative from computed state. It will also remove measured execution overhead from duplicate stage fingerprinting and repeated capability adapter inspection while preserving the existing trust boundaries: exact source identity, cell/range provenance, deterministic calculation ancestry, independent validation, revision and invalidation semantics, human acceptance, cancellation, and cleanup.

This is Release 2 work after the source/session correctness work represented by PR #21. It does not absorb the remaining Release 1 streaming-capture, cancellable-hash, transactional-publication, warm-session benchmark, or analyst-to-validator reuse follow-ups. It also does not migrate or delete the CSV `vertical_slice` implementation; that remains a compatibility fixture until the later production-portability cleanup.

## Implementation Outcomes

### One normalized brief and one explicit domain-input contract

`WorkBrief` can carry typed analysis-input declarations without breaking legacy brief files. `normalize_work_brief()` produces one immutable `NormalizedIntent` per execution, including stage dependencies, source needs, required capabilities, review checks, explicit topology requirements, resource limits, and domain contracts. The normalized object is an execution view, not a second durable authority; the persisted brief and existing `ExecutionRecipe` remain the owning records.

`AnalysisInputContract` explicitly represents required tables, column mappings, entity scope, baseline and comparison periods, scenarios, units, conversion assumptions, duplicate policy, missing-value policy, required calculations, and required validation checks. Contract serialization, validation, and fingerprinting are deterministic and reject ambiguous or unsupported values before analysis begins. The contract fingerprint is part of stage semantic identity, so a contract-only change cannot reuse a stale stage result.

### Portable domain analysis with preserved semantics

Portfolio, supplier, EV-capacity, technology-radar, and Power BI portfolio analyses consume the resolved contract plus verified tables. Periods, entities, mappings, scenarios, reporting units, and supported conversion rates come from the contract instead of fixture constants. Unknown currency conversion produces an explicit `UNSUPPORTED_CONVERSION` data-quality outcome rather than silently using an identity rate.

Missing, zero, invalid, and not-applicable values remain distinguishable through calculations, issues, findings, and reports. Existing source locators, evidence IDs, calculation inputs, review state, and accepted-result behavior remain intact.

### Outcome-driven reports and focused shared plumbing

Repeated XLSX table lookup, row conversion, required-column checks, and row-provenance construction are owned by one small helper module. Domain reasoning and acceptance workflows remain separate. Specialized reports state analytical conditions only from computed result fields and contract labels; they do not contain fixture-specific claims such as a fixed year, fixed month range, or unconditional growth statement.

### Simpler ordinary execution with bounded hot-path work

One bounded task defaults to `DIRECT`; dependencies or validation default to `SEQUENTIAL`; `CONCURRENT`, `HANDOFF`, and `GROUP_CHAT` remain available only when explicitly requested or structurally required by an explicit intent. `RecipeStage` remains the canonical execution representation. Stage semantic and policy fingerprints are computed once at admission and reused for cache lookup, receipt construction, dependency validation, and invalidation. Capability bindings precompute supported adapter parameters at bind time rather than calling `inspect.signature()` on each invocation.

### Production-path portability evidence

Brief-variation regression cases exercise the real XLSX analysis path and vary periods, baseline years, entities, mapping aliases, units, supported conversions, sheet and column ordering, duplicates, missing values, and narrative conditions. The evidence separates structural portability from model quality, provider availability, and human acceptance. The legacy CSV vertical slice is not used as evidence for production XLSX behavior.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-executing-plans`, `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`, `skill-performance-optimization`, `skill-verification-before-completion`
- Isolation: current workspace for planning; implementation activates from a clean branch based on the merged Release 1 source/session correctness base and preserves unrelated untracked artifacts under `work/`, `build/`, `data/`, and `.agents/skills/`
- Commit policy: `no commits during execution`; Git disposition remains a separate authorized step after fresh completion verification
- Preauthorized local actions: edit only the declared source, schema, test, evaluation, documentation, and plan paths; run the declared local tests, compile checks, Markdown-link checks, and portability probe; preserve unrelated workspace files
- User-approval actions: push, merge, pull-request publication, external provider calls, destructive cleanup, deletion of compatibility paths, and any change to the Release 1 base
- Parallel ownership: none; contract, analysis, controller, and evidence tasks share interfaces and execute sequentially
- Sequential fallback: complete Tasks 1 through 5 in order, then run Task 6 and final verification from the integrated tree

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/foresight-investigation-overhead-optimization` planning snapshot at `51fbe9aa6afef7dd52a1d601136a01d7ab01098a`
- Expected workspace: existing unrelated untracked artifacts are preserved; the plan file is the only new tracked-scope artifact created by this turn
- Lifecycle: the plan was approved, activated, executed on the current implementation branch, and changed to `completed` only after fresh repository-wide verification.
- Next action: commit, push, open the pull request, and complete the authorized review cycles before merge.
- Blockers: none for implementation or verification; Git publication and merge remain separately authorized by the user.

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current implementation branch | `resolved` | Release 1 base confirmed | contract and normalization tests | passed |
| Task 2 | `completed` | current implementation branch | `resolved` | Task 1 | shared-helper and provenance regression tests | passed |
| Task 3 | `completed` | current implementation branch | `resolved` | Tasks 1–2 | five-domain portability and semantic-state tests | passed |
| Task 4 | `completed` | current implementation branch | `resolved` | Task 3 | result-driven report assertions | passed |
| Task 5 | `completed` | current implementation branch | `resolved` | Task 1 | controller, fingerprint, and capability-boundary tests | passed |
| Task 6 | `completed` | current implementation branch | `resolved` | Tasks 1–5 | real-path portability receipt and documentation/link checks | passed |

## Task Breakdown

### Task 1: Add normalized intent and typed analysis-input contracts

**Purpose:**
- Establish one domain-owned contract between a persisted `WorkBrief` and each domain analysis without creating a rules engine or a second durable state store.

**Task Function:**
- Define and validate the normalized execution input boundary.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: cross-cutting domain-model and schema change with compatibility and provenance risk; use the lowest profile that can safely reconcile serialization, migration, and validation.

**Validator Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: independently verify schema compatibility, deterministic fingerprints, legacy loading, and rejection of malformed contracts.

**Specification Coverage:**
- Add `NormalizedIntent` and `AnalysisInputContract`; interpret legacy `WorkBrief` fields once; preserve existing brief persistence and execution-intent compatibility; keep `ExecutionRecipe` and `AnalysisState` as separate owning records.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `src/foresight_os/domain/models.py:WorkBrief`, `ExecutionIntent`, `WorkStage`
- Inspect: `src/foresight_os/domain/validation.py:validate_work_brief`, `_normalize_work_brief`
- Inspect: `src/foresight_os/persistence/analysis_store.py:save_brief`, `load_brief`
- Modify: `src/foresight_os/domain/analysis_inputs.py:AnalysisInputContract`, `NormalizedIntent`, `normalize_work_brief`, `contract_for_domain`
- Modify: `src/foresight_os/domain/models.py:WorkBrief` to carry an optional typed `analysis_inputs` collection without re-emitting the removed legacy execution override
- Modify: `src/foresight_os/domain/validation.py:validate_work_brief` and `schemas/work_brief.schema.json` for deterministic contract normalization, field validation, legacy omission compatibility, and explicit unsupported-policy errors
- Modify: `src/foresight_os/wayfinding.py:create_work_brief`, `refine_work_brief` to accept and preserve input contracts
- Modify: `src/foresight_os/persistence/analysis_store.py:load_brief` and `artifacts/brief.py:render_work_brief_markdown` to round-trip and display the contract without duplicating it as a separate authority
- Verify: `tests/test_analysis_input_contract.py`, `tests/test_work_brief_compatibility.py`

**Dependencies:**
- Release 1 source/session correctness base must be identified before implementation activation; this task has no dependency on parsed-workbook Level 2 reuse.

**Authority:**
- Preauthorized local actions: edit the Task 1 paths, add focused contract tests, and run their focused test commands.
- Stop for: a requirement to persist a second normalized-intent registry, change the `AnalysisState` schema, or alter Release 1 source/session semantics.

**Steps:**
- [ ] Step 1: Define immutable `AnalysisInputContract` fields for required tables, canonical column mappings, entity scope, baseline/comparison periods, scenarios, units, conversion assumptions, duplicate and missing-value policies, required calculations, and required validation checks.
- [ ] Step 2: Define immutable `NormalizedIntent` as the one execution-time view of decision question, horizon, stages, dependencies, source needs, capabilities, review checks, explicit topology requirements, resource limits, and domain contracts; derive a deterministic fingerprint from canonical JSON.
- [ ] Step 3: Extend `WorkBrief` serialization and `work_brief.schema.json` with backward-compatible optional contracts; reject unknown contract fields, conflicting period declarations, unsupported policies, malformed mappings, and non-positive or non-finite conversion rates.
- [ ] Step 4: Implement `normalize_work_brief()` so controller callers perform the legacy-field interpretation once; keep the normalized object ephemeral and keep the persisted `WorkBrief` as the source of truth. Define the bounded legacy compatibility contract used when `analysis_inputs` is omitted: legacy workbook metadata may use the existing `EUR=1.0`, `USD=0.92`, and `CNY=0.13` FX map, with an explicit compatibility-assumption label in the resulting contract and evidence.
- [ ] Step 5: Add round-trip, legacy-load, fingerprint-stability, malformed-contract, domain-selection, and compatibility-contract tests. Explicit contracts with missing required conversion inputs must not inherit legacy defaults; they must produce the declared missing/unsupported conversion outcome.

**Verification:**
- [ ] `python -m pytest -q tests/test_analysis_input_contract.py tests/test_work_brief_compatibility.py`
- Expected: new contract cases pass; legacy briefs still validate and load; equivalent contracts have identical fingerprints; malformed contracts fail with `ValidationError` before analysis.

**Exit Criteria:**
- A loaded or newly created brief can provide a deterministic `NormalizedIntent` and a domain-specific `AnalysisInputContract`, while briefs without the optional field preserve current behavior and no second durable intent store exists.

### Task 2: Consolidate verified XLSX table and provenance plumbing

**Purpose:**
- Remove repeated mechanics from the five XLSX analyzers and validator without genericizing their reasoning or changing the CSV compatibility fixture.

**Task Function:**
- Extract and adopt the smallest shared table/provenance helpers that have identical semantics.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: bounded refactor across repeated helpers with source-provenance regression risk.

**Validator Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: verify source locators, evidence IDs, required-sheet failures, and row ordering remain unchanged for existing fixtures.

**Specification Coverage:**
- One shared verified-table helper surface; one source-locator/evidence construction path; no inheritance tree, analysis DSL, or second provenance model.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: duplicated `_table`, `_rows`, `_row_evidence`, and digest handling in `portfolio_resilience.py`, `supplier_resilience.py`, `ev_capacity_investment.py`, `technology_radar.py`, `powerbi_strategic_portfolio.py`, and `foresight_validator.py`
- Modify: new `src/foresight_os/analysis/workbook_inputs.py:require_table`, `table_rows`, `require_columns`, `row_range`, `row_evidence`, `brief_metadata`
- Modify: the six XLSX analysis modules to call the shared helpers while retaining domain-specific issue, calculation, finding, and workflow logic
- Verify: `tests/test_portfolio_resilience.py`, `tests/test_supplier_and_ev_resilience.py`, `tests/test_technology_powerbi_validator.py`, `tests/test_runtime_boundaries.py`

**Dependencies:**
- Task 1 contract types and validation are available so helper callers can distinguish required input failures from ordinary missing-cell values.

**Authority:**
- Preauthorized local actions: edit the shared helper and listed XLSX analysis/test paths; run focused analyzer and provenance tests.
- Stop for: a proposal to make `src/foresight_os/analysis/workbook.py` or `src/foresight_os/vertical_slice.py` the production XLSX authority in this release.

**Steps:**
- [ ] Step 1: Implement `workbook_inputs.py` with required-sheet lookup, row conversion, required-column validation, stable row ranges, and evidence construction that preserves the caller-supplied digest, units, transformation, and calculation labels.
- [ ] Step 2: Replace duplicated helper bodies in all five domain analyzers and `foresight_validator.py`; keep domain-specific table selection and evidence IDs stable unless a changed ID is required by a contract parameter.
- [ ] Step 3: Add focused tests for missing sheets, missing columns, row-provenance ranges, units, digest propagation, and existing exercise outputs.
- [ ] Step 4: Confirm the CSV vertical slice remains a compatibility fixture only and is not imported by the production XLSX path or portability probe.

**Verification:**
- [ ] `python -m pytest -q tests/test_portfolio_resilience.py tests/test_supplier_and_ev_resilience.py tests/test_technology_powerbi_validator.py tests/test_runtime_boundaries.py`
- Expected: existing exercise workflows retain their accepted/rejected behavior, evidence locators and calculation ancestry remain source-bound, and required-sheet/column failures remain explicit.

**Exit Criteria:**
- All six XLSX consumers use the one shared helper surface; no duplicated row/provenance helper remains in those consumers; CSV compatibility code remains separate and unclaimed as production portability evidence.

### Task 3: Parameterize domain calculations and explicit data-quality outcomes

**Purpose:**
- Make changed briefs select different periods, entities, mappings, scenarios, units, and supported conversions without copy-pasted analysis code.

**Task Function:**
- Adapt each existing domain algorithm to consume verified tables plus its typed input contract.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: high reasoning depth and cross-domain correctness risk; preserve separate strategy logic while changing shared input semantics.

**Validator Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: independently compare default-fixture results with changed-brief results and inspect failure classifications.

**Specification Coverage:**
- Portfolio economics, supplier resilience, EV capacity, technology radar, and Power BI portfolio analysis remain separate domain methods; only input selection and common table mechanics are shared.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `analyze_portfolio_resilience`, `analyze_supplier_resilience`, `analyze_ev_capacity_investment`, `analyze_technology_radar`, `analyze_powerbi_strategic_portfolio`
- Modify: the five `analyze_*` functions to accept an optional `input_contract` keyword and resolve a compatibility contract from declared workbook brief metadata only when the caller omits it
- Modify: `src/foresight_os/runtime/execution_gate.py:ExecutionGate.execute` and the analyzer workflow entry points in `portfolio_resilience.py`, `supplier_resilience.py`, `ev_capacity_investment.py`, `technology_radar.py`, and `powerbi_strategic_portfolio.py` to forward the normalized contract selected from persisted `WorkBrief.analysis_inputs`
- Modify: portfolio period filtering, entity-scope filtering, `MeasurementKey` periods and labels, and KPI reconciliation in `portfolio_resilience.py`
- Modify: supplier `_fx`, `_unit_cost_eur`, spend aggregation, reporting-unit assumptions, and issue construction in `supplier_resilience.py`
- Modify: EV year/scenario/region selection, capacity calculations, and KPI reconciliation in `ev_capacity_investment.py`
- Modify: technology scope, mapped columns, scenario/signpost selection, and assessment inputs in `technology_radar.py`
- Modify: Power BI baseline/comparison period selection, period labels, deduplication filters, `MeasurementKey` periods, and compatibility aliases in `powerbi_strategic_portfolio.py`
- Modify: `src/foresight_os/analysis/foresight_validator.py:validate_exercises` so checks use contract-selected periods and units rather than fixed `2026` or `Jan–Sep` strings
- Verify: `tests/test_portfolio_resilience.py`, `tests/test_supplier_and_ev_resilience.py`, `tests/test_technology_powerbi_validator.py`, `tests/test_runtime_boundaries.py`, and new `tests/test_brief_portability.py`

**Dependencies:**
- Tasks 1 and 2 complete; all analyzers receive validated contracts and shared verified-table primitives.

**Authority:**
- Preauthorized local actions: edit the five domain modules, validator, and declared focused tests/fixtures; run deterministic local analysis and review workflows.
- Stop for: a need to invent a generic strategy DSL, alter `AnalysisState` ownership, or silently coerce unsupported currency or missing values to valid numeric results.

**Steps:**
- [ ] Step 1: Define per-domain contract defaults from the existing workbook `Brief` metadata for backward-compatible direct callers. The omitted-contract legacy path uses exactly one documented compatibility contract, including the existing FX map and compatibility-assumption label; an explicitly supplied but incomplete contract never falls back to that map and instead reports missing/unsupported conversion inputs.
- [ ] Step 1a: Thread `WorkBrief.analysis_inputs` through `ExecutionGate.execute` into each analyzer workflow entry point and `validate_exercises`, and add an end-to-end regression proving that changing only the persisted contract changes the accepted analysis scope or result.
- [ ] Step 2: Replace hard-coded portfolio baseline/comparison years and entity selection with contract periods and scope; carry contract periods and units into evidence calculations and reconciliation messages.
- [ ] Step 3: Replace supplier identity FX fallback with the explicit supported conversion map from the resolved contract. For omitted contracts using legacy workbook metadata, use only the bounded compatibility map (`EUR=1.0`, `USD=0.92`, `CNY=0.13`) and label the assumption; for explicit contracts missing a required rate, classify the conversion as missing/unsupported rather than silently applying a legacy rate. Classify unknown currencies as `UNSUPPORTED_CONVERSION`, exclude them from converted aggregates according to the declared policy, and retain source evidence and issue references.
- [ ] Step 4: Parameterize EV and technology selections without changing their distinct observed/projected or source-independence reasoning.
- [ ] Step 5: Replace Power BI January–September filters with contract-selected comparable periods and preserve default-fixture compatibility aliases only for existing public result fields.
- [ ] Step 6: Preserve `0.0` as zero, use `None` or explicit issue/status for missing and invalid numeric inputs, and keep not-applicable outcomes separate from missing values in calculations and findings.
- [ ] Step 7: Add changed-brief workbooks and assertions for alternate periods, baseline years, regions/segments, mapping aliases, units, supported/unsupported currencies, duplicate rows, missing values, and zero-valued rows.

**Verification:**
- [ ] `python -m pytest -q tests/test_portfolio_resilience.py tests/test_supplier_and_ev_resilience.py tests/test_technology_powerbi_validator.py tests/test_brief_portability.py`
- Expected: default fixtures preserve existing findings and review outcomes; changed briefs change selected inputs and calculations; unsupported conversion is explicit; zero, missing, invalid, and not-applicable cases remain distinguishable.

**Exit Criteria:**
- Each production XLSX analyzer accepts a typed contract, uses contract-selected inputs and units, preserves evidence/calculation ancestry, and passes changed-brief regression cases without copied domain implementations.

### Task 4: Generate reports from computed outcomes

**Purpose:**
- Remove fixture-specific analytical prose from specialized reports while retaining domain-specific explanatory structure and accepted-finding gates.

**Task Function:**
- Bind narrative sentences to computed result fields, statuses, contract labels, and evidence-backed issue state.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: material analytical-output correctness and semantic-state coverage across five report renderers.

**Validator Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: inspect rendered output for positive, negative, zero, missing, invalid, and not-applicable cases and verify every conditional sentence has a computed source.

**Specification Coverage:**
- Reports must not claim positive growth, missing denominators, segment leadership, or fixed comparison periods unless those conditions were computed for the supplied contract and current state.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Modify: `render_portfolio_report`, `render_supplier_report`, `render_ev_report`, `render_technology_report`, and `render_powerbi_report` in their owning analysis modules
- Inspect: `src/foresight_os/artifacts/report.py:render_report` for the existing accepted-state and evidence rendering contract; do not create a second report authority
- Verify: `tests/test_report_fidelity.py`, `tests/test_portfolio_resilience.py`, `tests/test_supplier_and_ev_resilience.py`, `tests/test_technology_powerbi_validator.py`, `tests/test_brief_portability.py`

**Dependencies:**
- Task 3 exposes computed period labels, status distinctions, issue classifications, and outcome fields needed by report renderers.

**Authority:**
- Preauthorized local actions: edit specialized report renderers and focused report tests; run accepted-state report generation and failure-path assertions.
- Stop for: a proposal to make report text an independent source of analytical truth or to weaken the current accepted-finding gate.

**Steps:**
- [ ] Step 1: Replace fixed period and month-range labels with contract labels in headings, table definitions, calculation descriptions, and filter-context checks.
- [ ] Step 2: Build conditional narrative from computed growth, ranking, denominator, data-quality, and recommendation fields; render explicit `UNSUPPORTED_CONVERSION`, missing, invalid, zero, and not-applicable states without converting them to zero or silence.
- [ ] Step 3: Keep domain-specific report sections and citations intact; ensure every conditionally rendered sentence can be traced to a result field, issue, calculation, or accepted analytical record.
- [ ] Step 4: Add report-fidelity assertions for changed briefs and semantic edge cases.

**Verification:**
- [ ] `python -m pytest -q tests/test_report_fidelity.py tests/test_portfolio_resilience.py tests/test_supplier_and_ev_resilience.py tests/test_technology_powerbi_validator.py tests/test_brief_portability.py`
- Expected: accepted reports render only current accepted findings; period labels follow the contract; condition-dependent sentences change when inputs change; status distinctions are visible and source-cited.

**Exit Criteria:**
- Specialized reports are deterministic projections of accepted analytical state and computed contract metadata, with no fixture-only condition asserted as universal fact.

### Task 5: Simplify controller defaults and runtime hot paths

**Purpose:**
- Make ordinary execution predictable and remove repeated stage fingerprint and capability-adapter discovery work without adding execution modes or a new orchestration layer.

**Task Function:**
- Centralize normalized intent consumption and reuse one resolved execution bundle at stage admission.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: cross-module runtime behavior with compatibility, reuse, and cleanup implications.

**Validator Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: verify explicit advanced-pattern behavior, receipt/cache identity, cancellation, and capability instrumentation across direct and sequential paths.

**Specification Coverage:**
- `DIRECT` and `SEQUENTIAL` are ordinary defaults; advanced patterns remain supported only when explicit; `RecipeStage` is canonical; stage fingerprints are computed once; capability binding precomputes adapter support.

**Required Skills:**
- `skill-performance-optimization`, `skill-backend-verification`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `src/foresight_os/controller/policy.py:select_recipe`, `_recipe_for_patterns`, `_explicit_reviewer_requested`
- Inspect: `src/foresight_os/controller/recipes.py:RecipeStage`, `ExecutionRecipe`
- Modify: `src/foresight_os/controller/policy.py` so one normalized intent is consumed during recipe selection and advanced patterns are not inferred from incidental task-shape flags
- Modify: `src/foresight_os/runtime/workflow.py:run_recipe_async`, `_stage_fingerprints`, `_stage_cache_key` so one stage fingerprint bundle is computed at admission and reused for cache lookup, `StageReceipt` construction, dependency validation, and invalidation
- Modify: `src/foresight_os/runtime/capabilities.py:CapabilityBinding`, `prepare_capability_context`, `_instrumented_dispatch`, `instrument_tool` so adapter support for cancellation, workbook context, authority, and execution mode is resolved when a binding is prepared
- Verify: `tests/test_controller_selection.py`, `tests/test_stage_inputs.py`, `tests/test_capabilities.py`, `tests/test_runtime_boundaries.py`

**Dependencies:**
- Task 1 provides the normalized intent boundary; Tasks 2–4 must not change execution receipt semantics while this task is active.

**Authority:**
- Preauthorized local actions: edit controller/runtime files and their focused tests; run direct/sequential workflow, receipt reuse, cancellation, and capability instrumentation checks.
- Stop for: any request to add a new orchestration mode, persistent capability registry, cache lifecycle state machine, or second execution representation.

**Steps:**
- [ ] Step 1: Have `select_recipe()` normalize the brief once and choose `DIRECT` for one bounded task, `SEQUENTIAL` for dependencies or validation, and advanced patterns only for explicit override or explicit normalized intent.
- [ ] Step 2: Preserve positional stage mapping, review requirements, capability requirements, and existing explicit-pattern validation while removing incidental topology selection.
- [ ] Step 3: Replace the separate `_stage_cache_key()` and `_stage_fingerprints()` work with one admission result whose semantic and execution-policy fingerprints are passed to all later consumers. Include the applicable `AnalysisInputContract` fingerprint in `StageInput` or the equivalent stage semantic payload, and require `_stage_fingerprints`, cache keys, `StageReceipt` matching, dependency validation, and invalidation checks to include it. A contract-only change must force fresh execution; reuse is allowed only when analytical inputs and contract identity both match.
- [ ] Step 4: Extend `CapabilityBinding` with a precomputed adapter contract or equivalent immutable bound metadata; move supported-parameter inspection out of every instrumented invocation while preserving workbook-cache injection, cancellation, budget, metrics, and ownership behavior.
- [ ] Step 5: Add regressions proving explicit concurrent/handoff/group-chat requests still work, ordinary task shapes select direct/sequential, fingerprint values remain stable, stale receipts remain rejected, capability invocation/cleanup behavior is unchanged, and a contract-only change is rejected as stale under both `fallback_on_stale_reuse="stop"` and `fallback_on_stale_reuse="run_fresh"`.

**Verification:**
- [ ] `python -m pytest -q tests/test_controller_selection.py tests/test_stage_inputs.py tests/test_capabilities.py tests/test_runtime_boundaries.py`
- Expected: ordinary briefs use direct/sequential defaults; explicit advanced patterns remain available; stage fingerprints are computed once per admission; capability wrappers preserve cancellation, workbook context, authority, metrics, and cleanup behavior.

**Exit Criteria:**
- Controller and runtime consumers share one normalized intent and one stage-fingerprint bundle per stage; no repeated adapter signature discovery occurs on the invocation hot path; existing explicit topology and trust behavior remains covered.

### Task 6: Add real-path portability evidence and update maintained guidance

**Purpose:**
- Prove the changed-brief objective through the production XLSX path and document the final ownership boundaries without presenting CSV compatibility code or provider/model quality as equivalent evidence.

**Task Function:**
- Produce reproducible structural portability evidence and reconcile architecture/evaluation guidance.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: evidence design, fixture generation, and cross-domain verification.

**Validator Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: independently inspect receipt scope, production-path usage, changed-brief outcomes, and documentation links.

**Specification Coverage:**
- Real XLSX brief-variation cases cover periods, baseline years, entities, mappings, units, conversions, ordering, duplicates, missing values, and narrative outcomes; structural proof is separated from model quality, provider availability, and human acceptance.

**Required Skills:**
- `skill-backend-verification`, `skill-performance-optimization`, `skill-verification-before-completion`

**Files And Symbols:**
- Add: `evaluation/probes/run_brief_portability_probe.py:run` with deterministic temp-workbook generation and a receipt schema containing contract fingerprint, fixture hash, selected inputs, outcome assertions, and status classification
- Add: `tests/test_brief_portability.py` coverage for the probe and direct analyzer regressions
- Modify: `evaluation/README.md` and `docs/evidence-and-evaluation.md` to distinguish workbook portability, system regression, provider availability, and human acceptance evidence
- Modify: `docs/architecture.md` to document `WorkBrief → NormalizedIntent → AnalysisInputContract → verified tables → domain analysis → independent validation → AnalysisState` and the single ownership boundaries
- Verify: `tests/test_markdown_links.py`, all repository tests, compileall, and the portability probe

**Dependencies:**
- Tasks 1–5 complete and integrated; the probe must call the five production XLSX analyzers or their accepted workflow entry points, not `src/foresight_os/vertical_slice.py`.

**Authority:**
- Preauthorized local actions: add the probe/tests and update maintained documentation; run local evidence generation and link checks; write only redacted deterministic receipts under the ignored `work/` area.
- Stop for: provider authentication, external publication, deletion of CSV compatibility code, or a claim that model quality or human acceptance was measured by the structural probe.

**Steps:**
- [ ] Step 1: Generate deterministic brief-variation workbooks from existing exercise shapes, changing one contract dimension at a time and recording source hashes and contract fingerprints.
- [ ] Step 2: Run the production XLSX analyzers, assert changed period/entity/mapping/unit/convertibility outcomes, and classify missing provider or human-acceptance evidence as `not_measured` or `BLOCKED_EXTERNAL` rather than failing open.
- [ ] Step 3: Separate workbook portability assertions from controller/system-regression assertions in the receipt and documentation.
- [ ] Step 4: Run the Markdown-link checker and reconcile every changed path, deferred Release 3 item, and preserved invariant in the maintained docs.

**Verification:**
- [ ] `python evaluation/probes/run_brief_portability_probe.py --output-root work/brief-portability-20261016/final`
- [ ] `python -m pytest -q tests/test_brief_portability.py tests/test_markdown_links.py`
- Expected: the probe exits successfully with `VERIFIED` for structural portability, records the exact fixture and contract identities, uses the real XLSX path, and does not claim provider/model/human-quality proof.

**Exit Criteria:**
- A fresh reviewer can reproduce the changed-brief evidence, identify which outcomes are structural versus not measured, and follow maintained documentation to the single canonical owner for each contract and state.

## Verification

Use the following final artifact-level checks after all tasks are integrated:

- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `python evaluation/probes/run_brief_portability_probe.py --output-root work/brief-portability-20261016/final`
- `python -m pytest -q tests/test_markdown_links.py`
- `git diff --check`
- `git status --short --branch`

The final review must confirm that the portability receipt uses the production XLSX path, includes the exact contract and fixture identities, distinguishes `VERIFIED`, `FAILED`, `BLOCKED_INPUT`, `BLOCKED_EXTERNAL`, and `not_measured` truthfully, and contains no credentials, raw provider payloads, or customer data. It must confirm that the existing source/session plan remains a separate Release 1 boundary and that no deferred distributed cache, parsed-workbook database, file watcher, source registry, generic rules language, plugin framework, new orchestration mode, second provenance model, or CSV-authority migration was hidden inside this work.

## Completion Criteria

The plan is ready for completion verification when:

1. `WorkBrief` round-trips optional typed analysis-input declarations and legacy briefs remain valid.
2. One `NormalizedIntent` is derived per execution and provides a deterministic domain contract without becoming a second durable authority.
3. All five production XLSX analyzers consume contract-selected periods, entities, mappings, scenarios, units, and supported conversions while retaining domain-specific reasoning.
4. Unsupported currency, missing, invalid, zero, and not-applicable states remain explicit through evidence, calculations, findings, and reports.
5. Shared XLSX table/provenance plumbing has one owner and preserves source locators, evidence IDs, calculation inputs, independent validation, review, invalidation, and acceptance semantics.
6. Specialized reports are computed projections of accepted state and contract metadata, not fixture-specific analytical assertions.
7. Ordinary controller execution uses direct/sequential defaults; explicit advanced patterns remain supported; stage fingerprints and capability adapter support are not recomputed in hot loops.
8. Real-path changed-brief regression evidence covers periods, baseline years, entities, mappings, units, conversions, ordering, duplicates, missing values, and narrative conditions.
9. Maintained architecture/evaluation documentation identifies canonical owners and deferred Release 3 work without duplicating a second specification.
10. `skill-verification-before-completion` returns `verified`; the lead controller changes the plan from `active` to `completed` only after that evidence is fresh. The plan remains `proposed` while awaiting approval and must be changed to `active` before Task 1 begins; any separately authorized Git disposition is pursued only after completion verification.

## Self-Review

- Verdict coverage: Release 2 brief normalization, explicit domain input contracts, parameterized periods/entities/mappings/units, explicit currency failure, result-driven reporting, shared table/provenance helpers, Direct/Sequential defaults, one-time stage fingerprints, one-time capability adapter inspection, and realistic brief-variation evidence map to Tasks 1–6. PR #21 Release 1 follow-ups and Release 3 CSV-authority retirement remain explicit boundaries.
- Repository reconciliation: every named existing symbol was checked locally; new files are limited to the domain contract, shared XLSX helper, portability tests, portability probe, and this plan; `src/foresight_os/analysis/workbook.py` and `src/foresight_os/vertical_slice.py` remain compatibility surfaces rather than new owners.
- Placeholder scan: no unresolved path, symbol, command, task owner, or template token remains in the plan; pending profile values are explicitly controller-resolved plan metadata, not implementation placeholders.
- Cross-task consistency: `AnalysisInputContract`, `NormalizedIntent`, `workbook_inputs.py`, contract-selected period labels, `UNSUPPORTED_CONVERSION`, production XLSX evidence, `RecipeStage`, `_stage_fingerprints`, `CapabilityBinding`, and final verification commands are used consistently across tasks and completion criteria.
- Ownership: `WorkBrief` and domain normalization remain under `src/foresight_os/domain/`; `AnalysisState` and `AnalysisStore` remain durable analytical owners; five analyzers retain domain reasoning; runtime owns execution; probes consume evidence; no parallel registry or provenance model is introduced.
- Task sizing: contract, shared plumbing, domain parameterization, reporting, runtime simplification, and evidence/documentation are sequentially bounded with task-local proof and no overlapping parallel write lanes.
