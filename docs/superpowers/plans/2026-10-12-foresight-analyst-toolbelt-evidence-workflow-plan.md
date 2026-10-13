---
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
layer: change
name: foresight-analyst-toolbelt-evidence-workflow
targets:
  - src/foresight_os/domain/
  - src/foresight_os/wayfinding.py
  - src/foresight_os/controller/
  - src/foresight_os/runtime/
  - src/foresight_os/analysis/
  - src/foresight_os/persistence/
  - src/foresight_os/graph/
  - evaluation/probes/
  - evaluation/cases/
  - tests/
  - pyproject.toml
  - README.md
  - evaluation/README.md
  - docs/intent/
---

# Foresight Analyst Toolbelt and Evidence Workflow

## Verdict Review

Decision: adopt the verdict with a narrower first activation boundary. The
architecture is ready for a semantic Analyst toolbelt, but the next delivery
must prove one useful capability chain before adding a broad integration catalog.

Keep these decisions:

- Work Briefs and ordered Work Stages own the decision question, scope, research
  needs, expected outputs, and review points.
- The Controller selects collaboration pattern, role, profile, semantic
  capability IDs, and budgets. It must not infer a tool from arbitrary text
  substrings.
- Capability IDs remain vendor-neutral. Concrete local, native, or MCP bindings
  resolve only at the Foresight runtime boundary.
- A search snippet is a discovery candidate, not durable evidence. A material
  claim requires retrieval of the cited source, source identity, retrieval time,
  and sanitized provenance before normalization and persistence.
- Existing MAF execution, CapabilityResolver, instrument_tool, AnalysisStore,
  domain validation, and bounded graph queries remain the owning boundaries.
  This plan adds no second orchestration engine, protocol registry, semantic
  cache, or connector-owned analytical state.

The first activation includes these semantic IDs and truthful availability states:

    web_search
    page_retrieval
    document_read
    spreadsheet_read
    data_analysis
    calculation
    graph_context
    domain_validation
    internal_knowledge
    artifact_generation

The runnable IDs are web_search, page_retrieval, web_crawl, spreadsheet_read,
data_analysis, calculation, graph_context, and domain_validation. document_read,
internal_knowledge, and artifact_generation are registered as explicit
unavailable follow-up capabilities so typed requirements never emit undocumented
IDs or silently fall through to a guessed tool.

The first runnable path is web_search -> page_retrieval -> validated
EvidenceCandidate -> Evidence -> claim -> revision-safe commit. Local
spreadsheet, analysis, calculation, graph, and validation bindings are added as
deterministic toolbelt surfaces. document_read, real enterprise MCP, SQL,
and the unavailable internal-knowledge/artifact-generation adapters remain
explicit follow-up lanes unless their adapters can be implemented without
widening this acceptance boundary.

## Goal

Deliver a small, stable Foresight Analyst toolbelt whose semantic capabilities
are selected from typed Work Stage requirements, bound through the existing
run-scoped resolver, and proven through one complete evidence workflow:

    Work Brief
      -> typed EXTERNAL_FACT / SOURCE_DETAIL requirements
      -> Controller recipe with web_search + page_retrieval
      -> participant invokes web_search
      -> selected source is retrieved through page_retrieval
      -> sanitized EvidenceCandidate with retrieval proof
      -> domain Evidence and AnalyticalRecord
      -> pending revision
      -> accepted revision after review boundary

The delivery must also produce deterministic capability probes, adversarial
failure probes, an environment-gated external probe contract, and a bounded
soak/anomaly receipt without retaining credentials, raw pages, prompts, or raw
provider payloads.

## Implementation Outcomes

### Typed capability routing
WorkStage.research_needs becomes a typed, schema-validated requirement surface.
Known requirement kinds map deterministically to semantic capability IDs. Unknown
requirements produce UNRESOLVED_CAPABILITY and remain visible in recipe metadata;
they never silently fall through to a guessed tool.

### Compact Analyst toolbelt
The existing resolver and instrumentation layer expose the eleven semantic IDs
listed above. Runnable first-party bindings cover web search, page retrieval,
CSV/XLSX reading, deterministic table analysis, reproducible calculation, bounded
graph context, and domain validation. document_read, internal_knowledge, and
artifact_generation have explicit deterministic unavailable results until their
adapters are activated; no fake success is added. spreadsheet_read must support
real CSV and XLSX workbooks before the toolbelt can be marked complete.

### Complete evidence workflow
A deterministic fixture/provider proves that a participant can discover a source,
retrieve the actual source, convert only sanitized retrieved content into an
Evidence record, create an evidence-linked claim, and commit an accepted
revision through AnalysisStore. Search-only claims, malformed sources,
authority-altering retrieved content, stale revisions, and provider failures are
rejected or classified without corrupting state.

### Reliability evidence
Every runnable capability has a contract probe for success and an important
failure path. The vertical slice has a sanitized receipt. A fixed-seed soak runs
10 warmup and 100 measured workflows across success, timeout, cancellation, MCP
failure, invalid input, budget exhaustion, and concurrent execution, and fails
on unexplained result, state, metric, task, or resource drift.

### Documentation and dependency truth
README, evaluation guidance, the MAF capability decision, package extras, and
CI commands describe the same semantic IDs, provider contracts, evidence gate,
probe tiers, and external-blocker behavior.

## Execution Approach

- Mode: inline sequential
- Coordination: git-tracked
- Required skills: skill-writing-plans, skill-backend-verification, skill-test-driven-development, skill-code-standards, skill-executing-plans, skill-plan-document-reviewer, skill-verification-before-completion
- Isolation: optional worktree; use a feature worktree when preserved untracked build, egg-info, or work outputs make the current workspace ambiguous
- Commit policy: no commits during execution; the lead creates one verified checkpoint after the plan is reconciled, unless the user separately authorizes branch disposition
- Preauthorized local actions: edit tracked source, tests, schemas, fixtures, documentation, package configuration, and plan-local probe outputs; run declared deterministic checks and environment-gated probes without recording secrets or raw provider content
- User-approval actions: push, merge, publication, credential configuration, external writes, destructive cleanup, discard, and real-provider or real-MCP calls requiring new access
- Parallel ownership: none; capabilities.py, workflow.py, policy.py, and shared schemas force serialization
- Sequential fallback: execute Tasks 1–7 in order in one lead workspace, accepting each task only after its task-local proof passes

## Coordination State

- Coordination owner: single lead controller
- Coordination schema: 2
- Branch: main
- Base commit: 5260bd67734622a9945e9bb180614bb6adeb9843
- Expected workspace: main at the base commit with generated build, src/foresight_os.egg-info, and work outputs preserved as untracked
- Next action: none; execution and final verification are complete
- Blockers: no implementation blocker; direct provider configuration remains environment-gated, while the public-web bridge probe has supplied a separate verified real-web receipt

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | complete | current workspace | lead | none | typed routing tests | focused routing/schema tests pass |
| Task 2 | complete | same workspace | lead | Task 1 | capability contract tests | semantic registry/unavailable-state tests pass |
| Task 3 | complete | same workspace | lead | Task 2 | retrieval boundary tests | retrieval and evidence-gate tests pass |
| Task 4 | complete | same workspace | lead | Task 3 | end-to-end evidence workflow | evidence workflow, persistence, and restart tests pass |
| Task 5 | complete | same workspace | lead | Task 2 | local toolbelt probes | mandatory multi-sheet XLSX contract tests pass |
| Task 6 | complete | same workspace | lead | Tasks 3–5 | failure, MCP, and soak probes | local toolbelt, evidence, XLSX, MCP, and anomaly receipts pass |
| Task 7 | complete | same workspace | lead | Tasks 1–6 | docs, CI, final verification | final deterministic and package checks pass; direct external probes remain classified BLOCKED_EXTERNAL and the public-web bridge is separately VERIFIED |

## Task Breakdown

### Task 1: Replace substring routing with typed Work Stage requirements

Purpose:
- Make Controller capability admission deterministic, explicit, and backward-compatible without silently guessing from free text.

Task Function:
- Define and migrate typed research requirements at the Work Brief boundary.

Template Profile:
- Controller-selected: unresolved
- Selection basis: resolve at activation from ambiguity and schema-migration risk; the task is bounded but touches the canonical Work Brief contract.

Validator Profile:
- Controller-selected: none
- Selection basis: focused schema and controller tests are sufficient.

Specification Coverage:
- Typed vocabulary EXTERNAL_FACT, SOURCE_DETAIL, DOCUMENT_REVIEW, STRUCTURED_DATA, QUANTITATIVE_ANALYSIS, EXISTING_EVIDENCE, INTERNAL_KNOWLEDGE, VALIDATION, and ARTIFACT_OUTPUT. INTERNAL_KNOWLEDGE and ARTIFACT_OUTPUT map to the registered but unavailable internal_knowledge and artifact_generation capabilities until their adapters exist.
- Exact mapping: EXTERNAL_FACT -> web_search; SOURCE_DETAIL -> page_retrieval; DOCUMENT_REVIEW -> document_read; STRUCTURED_DATA -> spreadsheet_read; QUANTITATIVE_ANALYSIS -> data_analysis and calculation; EXISTING_EVIDENCE -> graph_context; INTERNAL_KNOWLEDGE -> internal_knowledge; VALIDATION -> domain_validation; ARTIFACT_OUTPUT -> artifact_generation.
- Unknown requirements produce UNRESOLVED_CAPABILITY.
- UNRESOLVED_CAPABILITY is a resolution outcome that preserves the original kind and query; it is not a runnable capability ID.
- Controller policy maps typed requirements to semantic IDs, not vendor names or substrings.

Required Skills:
- skill-code-standards
- skill-test-driven-development
- skill-backend-verification

Files And Symbols:
- Inspect: src/foresight_os/domain/models.py:WorkStage, src/foresight_os/wayfinding.py:create_work_brief, src/foresight_os/controller/policy.py:select_recipe, src/foresight_os/controller/policy.py:_recipe_for_patterns, src/foresight_os/schemas/work_brief.schema.json
- Modify: src/foresight_os/domain/models.py:ResearchNeedKind, src/foresight_os/domain/models.py:ResearchNeed, src/foresight_os/domain/models.py:WorkStage, src/foresight_os/domain/validation.py:validate_work_brief, src/foresight_os/wayfinding.py:create_work_brief, src/foresight_os/controller/policy.py:stage_capabilities
- Verify: tests/test_controller_selection.py, new tests/test_research_needs.py

Dependencies:
- Current WorkStage.research_needs is a list of untyped strings and Controller routing uses substring matching.
- Preserve existing saved briefs by normalizing legacy strings to an explicit unresolved requirement rather than inferring a capability.

Authority:
- Preauthorized local actions: edit the Work Brief model, schema, validation, wayfinding, Controller policy, and focused tests; run schema and controller tests.
- Stop for: changing persisted analysis schema, deleting legacy brief compatibility, or adding a new routing layer.

Steps:
- [x] Step 1: Add ResearchNeedKind and ResearchNeed with kind, query, and optional source hint; make WorkStage serialize typed requirements through the existing to_dict path.
- [x] Step 2: Update work_brief.schema.json and validate_work_brief to accept typed requirements and normalize legacy strings as UNRESOLVED_CAPABILITY with the original query preserved.
- [x] Step 3: Replace stage_capabilities substring matching with a deterministic kind-to-capability table, including explicit unavailable mappings for INTERNAL_KNOWLEDGE and ARTIFACT_OUTPUT, and emit unresolved requirement names in recipe metadata.
- [x] Step 4: Update the synthetic Work Brief to express capacity expansion cost as EXTERNAL_FACT with a source-detail follow-up, then add positive, unknown, legacy, mixed-stage, registry-target, and saved-brief round-trip tests.

Verification:
- [x] python -m pytest -q tests/test_controller_selection.py tests/test_research_needs.py
- Expected: known kinds produce only declared semantic IDs; unknown and legacy strings produce UNRESOLVED_CAPABILITY; no vendor-specific identifier appears in recipe capability IDs.

Exit Criteria:
- Controller routing is typed, schema-validated, deterministic, and covered by focused tests without breaking existing saved brief loading.

### Task 2: Establish the semantic toolbelt registry and binding contracts

Purpose:
- Make the Analyst toolbelt discoverable through one capability-definition source and preserve the existing run-scoped authorization, budget, scope, concurrency, cache, telemetry, and cleanup contracts.

Task Function:
- Extend the existing resolver with semantic definitions and explicit binding factories for local, native, and MCP-backed implementations.

Template Profile:
- Controller-selected: unresolved
- Selection basis: resolve at activation from the number of boundary contracts and optional-dependency decisions.

Validator Profile:
- Controller-selected: none
- Selection basis: contract tests and existing runtime-boundary tests cover the resolver and instrumentation directly.

Specification Coverage:
- Semantic IDs are web_search, page_retrieval, web_crawl, document_read, spreadsheet_read, data_analysis, calculation, graph_context, domain_validation, internal_knowledge, and artifact_generation.
- Unavailable bindings return an explicit unavailable decision; they never execute during resolution.
- openpyxl and pandas are normal core analytical dependencies for spreadsheet_read and data_analysis; MCP remains an explicit optional probe dependency, not an accidental transitive import.

Required Skills:
- skill-code-standards
- skill-test-driven-development
- skill-backend-verification

Files And Symbols:
- Inspect: src/foresight_os/runtime/capabilities.py:CapabilityDefinition, src/foresight_os/runtime/capabilities.py:CapabilityResolver, src/foresight_os/runtime/capabilities.py:DEFAULT_CAPABILITIES, src/foresight_os/runtime/workflow.py:run_recipe_async, src/foresight_os/runtime/web_search.py:WebSearchCapability, src/foresight_os/runtime/crawl4ai.py:Crawl4AICapability
- Modify: src/foresight_os/runtime/capabilities.py:DEFAULT_CAPABILITIES, src/foresight_os/runtime/capabilities.py:CapabilityResolver, src/foresight_os/runtime/workflow.py:run_recipe_async, src/foresight_os/runtime/web_search.py:bind_web_search, pyproject.toml:project.dependencies, pyproject.toml:project.optional-dependencies
- Verify: tests/test_capabilities.py, tests/test_runtime_boundaries.py, tests/test_web_search_capability.py, new tests/test_toolbelt_contracts.py

Dependencies:
- Task 1 provides the semantic IDs required by recipes.
- Reuse CapabilityBinding, CapabilityScope, instrument_tool, and RunMetrics; do not create a second resolver or lifecycle owner.

Authority:
- Preauthorized local actions: edit the existing capability registry, run-context wiring, package extras, and focused tests; use only local fixture bindings during proof.
- Stop for: installing unapproved integrations, changing provider credentials, adding mutation capabilities, or widening participant data scope.

Steps:
- [x] Step 1: Add one canonical semantic-definition table with access, scope, approval, budget, parallelism, and binding-kind metadata for all ten IDs.
- [x] Step 2: Add explicit binding constructors for each implemented local capability and deterministic unavailable results for document_read, internal_knowledge, and artifact_generation until their adapters are activated. Do not add document-parser, knowledge-store, or artifact-generator dependencies in this delivery.
- [x] Step 3: Ensure every run-scoped binding is instrumented and registered with the existing scope; assert resolution has no provider side effects.
- [x] Step 4: Add openpyxl and pandas as pinned/constrained core runtime dependencies for the accepted CSV/XLSX analytical surface. Add an MCP dependency group only for the disposable fixture. Keep the base install credential-free and leave document-parser, knowledge-store, and artifact-generator dependencies deferred.

Verification:
- [x] python -m pytest -q tests/test_capabilities.py tests/test_runtime_boundaries.py tests/test_web_search_capability.py tests/test_toolbelt_contracts.py
- Expected: all ten semantic IDs resolve to truthful available, unavailable, or unresolved decisions; no tool call occurs during resolution; authorization, budget, scope, and cleanup invariants remain green.

Exit Criteria:
- The resolver has one authoritative toolbelt contract and every declared capability has a truthful binding or explicit unavailable state.

### Task 3: Add page retrieval and source-verification boundaries

Purpose:
- Close the search-to-source gap with a bounded read-only HTTP capability that produces candidates carrying retrieval proof without retaining raw page payloads.

Task Function:
- Implement and verify page_retrieval as the second half of the external evidence boundary.

Template Profile:
- Controller-selected: unresolved
- Selection basis: resolve from network-boundary and content-sanitization risk.

Validator Profile:
- Controller-selected: none
- Selection basis: direct local HTTP fixture tests provide success and failure proof.

Specification Coverage:
- page_retrieval accepts only HTTP(S) URLs, rejects URL credentials, file URLs, loopback/private/link-local/metadata targets, and unsafe redirect targets, re-checking every redirect. Loopback is allowed only for an explicitly configured disposable fixture endpoint. It enforces timeout and byte limits, records original/final/canonical URL, retrieval time, and content hash, and returns sanitized text metadata.
- Retrieved page text is untrusted data. Phrases such as "ignore instructions" are not by themselves invalid; content that attempts to alter runtime authority, capabilities, permissions, or budgets is quarantined or rejected without changing execution policy.
- 404, timeout, oversized content, malformed content, invalid URL, blocked network target, and authority-altering content are explicit failures or rejected candidates.
- Search candidates cannot be normalized as material evidence until a page-retrieval result verifies the source.

Required Skills:
- skill-backend-verification
- skill-test-driven-development
- skill-code-standards

Files And Symbols:
- Inspect: src/foresight_os/runtime/web_search.py:ConfiguredWebSearchProvider, src/foresight_os/domain/validation.py:validate_evidence_candidate, src/foresight_os/domain/evidence.py:normalize_evidence_candidate
- Modify: new src/foresight_os/runtime/page_retrieval.py, src/foresight_os/domain/models.py:EvidenceCandidate, src/foresight_os/domain/validation.py:validate_evidence_candidate, src/foresight_os/domain/evidence.py:normalize_evidence_candidate
- Verify: new tests/test_page_retrieval.py, tests/test_evidence_candidates.py

Dependencies:
- Task 2 provides the capability definition, binding, and instrumentation contract.
- Preserve existing web-search candidate behavior; add an explicit verification marker rather than treating every search result as durable evidence.

Authority:
- Preauthorized local actions: edit the page retrieval adapter, candidate validation, and focused local HTTP fixture tests; use loopback fixtures only.
- Stop for: crawling, authentication, robots-policy expansion, private-network access, raw payload persistence, or external mutation.

Steps:
- [x] Step 1: Implement bounded URL fetch, redirect handling, content-size limit, content-type check, HTML text extraction, canonical metadata, content hashing, and typed failure mapping using the standard library. Resolve each hostname, reject non-global destinations including IPv4-mapped IPv6, bind the connection to the approved resolved address while preserving HTTPS hostname verification, and re-apply the rule to every redirect. Disable ambient proxy routing unless it enforces the same destination policy. The fixture exception is limited to an explicitly configured fixture endpoint.
- [x] Step 2: Replace the forgeable source_verified boolean with a retrieval-only SourceRetrievalProof containing original URL, final/canonical URL, retrieval timestamp, and content hash. Only page_retrieval may construct it; it proves retrieval integrity, not source trust.
- [x] Step 3: Keep discovery on validate_evidence_candidate, but require adapter-issued retrieval proof for external web candidates at the public durable-normalization entry point; callers cannot disable that requirement. Local evidence retains its existing provenance contract. Do not treat retrieval proof as independent source-trust approval, and add a regression test rejecting search-only external candidates through the public normalization path.
- [x] Step 4: Cover success, redirect, 404, timeout, oversized response, malformed markup, empty source, URL-credential, private-address, hostname-to-private-address, changed-resolution, mapped-IPv6, proxy-bypass, unsafe-redirect, public-to-private-redirect, benign instruction-like text, fabricated-proof metadata, and authority-altering-content cases with an explicitly configured fixture endpoint.

Verification:
- [x] python -m pytest -q tests/test_page_retrieval.py tests/test_evidence_candidates.py
- Expected: only bounded retrieval results carrying the adapter-issued proof enter durable evidence conversion; failures carry stable failure classes and no raw body is present in returned objects.

Exit Criteria:
- page_retrieval is a run-scoped, instrumented, read-only capability with direct boundary proof and a hard gate against search-only evidence.

### Task 4: Complete the end-to-end evidence workflow

Purpose:
- Prove one useful Analyst workflow from typed Work Brief through participant tool calls to an accepted, evidence-linked revision.

Task Function:
- Compose the existing recipe runtime, retrieval capabilities, domain normalization, review boundary, and AnalysisStore into one deterministic workflow.

Template Profile:
- Controller-selected: unresolved
- Selection basis: resolve from cross-layer integration depth and state-transition risk.

Validator Profile:
- Controller-selected: unresolved
- Selection basis: assign an independent validator at activation if the execution path changes persistence or acceptance semantics.

Specification Coverage:
- Search result is discovered, the actual source is retrieved, retrieval-only proof records source identity, retrieval timestamp, and content hash, raw payload is excluded, claim references Evidence.id, and accepted state is committed with revision history.
- Search-only claims, invalid source content, review rejection, stale revision, provider timeout, and cleanup error do not produce a misleading accepted state.

Required Skills:
- skill-backend-verification
- skill-test-driven-development

Files And Symbols:
- Inspect: src/foresight_os/runtime/workflow.py:run_recipe_async, src/foresight_os/runtime/capabilities.py:instrument_tool, src/foresight_os/domain/evidence.py:normalize_evidence_candidate, src/foresight_os/persistence/analysis_store.py:AnalysisStore.commit_revision, src/foresight_os/analysis/reviewer.py:review_reasoning
- Modify: new src/foresight_os/analysis/evidence_workflow.py:run_evidence_workflow, src/foresight_os/vertical_slice.py only when the shared entry point can be reused without changing the existing workbook contract
- Verify: new tests/test_evidence_workflow.py, tests/test_vertical_slice.py, tests/test_persistence.py

Dependencies:
- Tasks 1–3 complete.
- Use a deterministic fixture provider and scripted local participant client; real provider readiness is not a prerequisite for deterministic acceptance.

Authority:
- Preauthorized local actions: add the evidence workflow entry point, deterministic fixtures, state assertions, and focused integration tests; write only under temporary test directories.
- Stop for: changing AnalysisState revision semantics without a migration, bypassing review or human acceptance, or persisting raw external content.

Steps:
- [x] Step 1: Build a typed workflow result containing discovery candidates, selected source identity, retrieval proof, retrieved candidate metadata, normalized Evidence, claim records, and committed revision metadata without raw provider payloads. Keep evidence_workflow.py as a thin application service; it must not own scheduling, retries, tool resolution, or agent lifecycle.
- [x] Step 2: Keep EXTERNAL_FACT and SOURCE_DETAIL routing in the typed controller registry, and use the thin evidence application service with participant-scoped web_search and page_retrieval adapters so scheduling and lifecycle remain owned by run_recipe_async rather than duplicated in the workflow.
- [x] Step 3: Convert only the retrieval-proof-bearing result into Evidence, create an evidence-linked AnalyticalRecord, run automated review, persist PENDING_REVIEW, and require an explicit simulated human_decision=ACCEPT before committing with AnalysisStore.commit_revision using the expected revision. Human acceptance must assess source identity, relevance, credibility, and limitations separately from retrieval integrity; retrieval proof and automated review never imply source-trust approval. review_reasoning() must never implicitly transition PENDING_REVIEW to ACCEPTED.
- [x] Step 4: Add rejection and recovery paths for search-only evidence, malformed source, timeout, review rejection, source-trust rejection after successful retrieval, fabricated proof metadata, stale revision, and cleanup error; add a restart test between PENDING_REVIEW and acceptance and assert no web_search or page_retrieval call occurs after restart; assert primary failures are not hidden by cleanup failures.
- [x] Step 5: Add one deterministic XLSX-to-finding workflow using STRUCTURED_DATA and QUANTITATIVE_ANALYSIS requirements. Promote material SpreadsheetCell/TypedMeasurement values to canonical Evidence with workbook SHA256, sheet, cell/range, and source-locator provenance; make CalculationRecord.input_ids reference those Evidence IDs or prior CalculationRecord IDs; pass the result through domain_validation and explicit human acceptance. Missing provenance and BLOCKED_RECALCULATION inputs must produce no accepted revision.

Verification:
- [x] python -m pytest -q tests/test_evidence_workflow.py tests/test_vertical_slice.py tests/test_persistence.py
- Expected: the web fixture query produces exactly one retrieved source with retrieval proof, one Evidence record, one evidence-linked claim, one accepted revision after explicit human_decision=ACCEPT, and complete cleanup; the XLSX fixture produces an evidence-linked, domain-validated finding with cell/range provenance and an accepted revision only when formula status is trustworthy; negative and restart paths produce no accidental accepted revision, preserve the prior state hash, and perform no duplicate web/page or workbook analysis.

Exit Criteria:
- One end-to-end workflow proves participant -> web search -> page retrieval -> Evidence -> claim -> revision-safe persistence with sanitized evidence and truthful failure behavior.

### Task 5: Add deterministic local Analyst tool bindings

Purpose:
- Make the compact toolbelt useful beyond external retrieval by exposing existing local analytical behavior through explicit, instrumented capability contracts.

Task Function:
- Wrap existing workbook, calculation, graph, and validation owners without duplicating domain logic.

Template Profile:
- Controller-selected: unresolved
- Selection basis: resolve from local adapter breadth and deterministic data-contract risk.

Validator Profile:
- Controller-selected: none
- Selection basis: fixture-based contract tests and existing domain tests provide direct proof.

Specification Coverage:
- spreadsheet_read returns Workbook/Sheet/Table/Cell models and TypedTable/TypedMeasurement values with workbook hash, sheet/range/cell provenance and never mutates source files. It must inspect sheet names, visible/hidden state, dimensions, tables, named ranges where practical, selected sheets/ranges/tables, numbers, strings, booleans, blanks, dates, merged or multi-row headers, hidden rows, nulls, duplicates, mixed types, cross-sheet references, and Excel error values.
- Formula cells preserve formula expression separately from cached value with calculation status VALUE, FORMULA_WITH_CACHE, FORMULA_WITHOUT_CACHE, FORMULA_RECALCULATED, FORMULA_STALE_OR_UNKNOWN, or ERROR. Untrusted cached values never masquerade as freshly recalculated output; decision-critical metrics with unusable formula caches return BLOCKED_RECALCULATION. Do not add a homemade Excel formula engine.
- The stale-cache fixture changes an input after writing a cached formula result and must classify the dependent formula as FORMULA_STALE_OR_UNKNOWN; absent cache is FORMULA_WITHOUT_CACHE, cached Excel error is ERROR, and only an explicitly supported recalculation boundary may produce FORMULA_RECALCULATED. Uncertainty propagates through data_analysis and calculation to BLOCKED_RECALCULATION for decision-critical outputs.
- data_analysis consumes typed tables and performs bounded aggregate, compare, join/filter, scenario, duplicate, and null operations deterministically. Strategic/evidentiary contradiction handling belongs to domain_validation or analysis, not this table-operation adapter.
- calculation returns CalculationRecord with formula, input IDs, units, and output; divide-by-zero and unit mismatch are explicit failures.
- graph_context returns bounded provenance, support/counterevidence, and impact context. get_impacted_records_complete() remains for correctness/invalidation only; agent context uses indexed traversal with explicit visited-node and visited-edge counters and stops at declared limits.
- domain_validation wraps candidate and analysis validation before persistence.

Contract owned by `src/foresight_os/runtime/local_toolbelt.py`:

| Binding | Required signature/result | Fixed semantics |
| --- | --- | --- |
| `spreadsheet_read` | `spreadsheet_read(source: Path, selection: SheetSelectionOrNone, limits: ToolbeltLimits) -> WorkbookReadResult` | Explicit table selection wins over range, range over sheet used-range; hidden sheets/rows are excluded by default and included only by explicit selection; merged headers remain ordered header tuples; dates use ISO-8601 values; blanks become `None`; Excel errors become typed `ExcelError`; unsupported external links fail explicitly. |
| `data_analysis` | `data_analysis(table: TypedTable, operation: AnalysisOperation, limits: ToolbeltLimits) -> AnalysisResult` | Nulls are reported, not silently dropped; duplicate join keys reject unless the operation declares `many_to_many`; cross-sheet provenance is the union of contributing cell/range locators; scenario/sensitivity inputs and ordering are explicit and deterministic. |
| `calculation` | `calculation(inputs: Sequence[EvidenceOrCalculationRecord], formula: FormulaSpec, units: UnitSpec) -> CalculationRecord` | Inputs are canonical IDs, not prose; formula uncertainty propagates to `BLOCKED_RECALCULATION`; floating-point comparisons use relative tolerance `1e-9`; output preserves formula, units, input IDs, and provenance. |
The contract must define `TypedTable`, `TypedMeasurement`, `WorkbookReadResult`,
`AnalysisResult`, and `CalculationRecord` field types before implementation.
The XLSX fixture tests must assert concrete values and coordinates for selection,
headers, dates, errors, joins, scenario ordering, sensitivity outputs, and
provenance rather than only checking that calls succeed.

Required Skills:
- skill-backend-verification
- skill-test-driven-development
- skill-code-standards

Files And Symbols:
- Inspect: src/foresight_os/analysis/workbook.py:read_workbook, src/foresight_os/analysis/workbook.py:calculate_case_metrics, src/foresight_os/graph/queries.py:get_impacted_records_complete, src/foresight_os/graph/queries.py:trace_provenance, src/foresight_os/domain/validation.py:validate_analysis
- Modify: new src/foresight_os/runtime/local_toolbelt.py, src/foresight_os/analysis/workbook.py only for reusable typed table/workbook helpers, src/foresight_os/graph/queries.py only for adapter-safe result contracts, src/foresight_os/runtime/capabilities.py for bindings, tests/fixtures/analyst_multisheet.xlsx, tests/fixtures/analyst_large.xlsx
- Verify: new tests/test_local_toolbelt.py, tests/test_xlsx_probe.py, tests/test_graph.py, tests/test_calculation_revision.py, tests/test_analysis_schema.py

Dependencies:
- Task 2 defines semantic IDs and the scope/telemetry contract.
- Add a real multi-sheet XLSX fixture and a larger synthetic XLSX fixture; CSV and XLSX are both mandatory release inputs. The fixtures include visible/hidden sheets, hidden rows, tables, merged headers, dates, numbers, strings, blanks, duplicates, mixed types, formula cells with and without cached results, Excel errors, cross-sheet references, scenarios, periods, units, and one deliberate contradiction.

Authority:
- Preauthorized local actions: add local read-only adapters, core analytical dependencies, deterministic CSV/XLSX fixtures, and focused tests; never write into source workbooks during probes.
- Stop for: introducing a new analytical engine, unbounded graph traversal, arbitrary code execution, SQL mutation, or hidden global caches.

Steps:
- [x] Step 1: Define the typed pipeline spreadsheet_read -> Workbook/Sheet/Table/Cell -> TypedTable/TypedMeasurement -> data_analysis -> AnalysisResult -> calculation -> CalculationRecord, with provenance and failure classes at each boundary. Make ToolbeltLimits in src/foresight_os/runtime/local_toolbelt.py the single limits owner with defaults/hard maxima of input bytes 5 MiB/20 MiB, expanded workbook XML bytes 20 MiB/100 MiB, total cells 100,000/1,000,000, rows 10,000/100,000, columns 100/256, join work 100,000/1,000,000 pairs, output rows 10,000/50,000, graph nodes 256/2,048, graph edges 1,024/10,000, returned items 100/1,000, and a per-operation deadline of 10/60 seconds. Enforce limits before allocation and during workbook scanning, formula/cache loading, table conversion, graph traversal, and analysis.
- [x] Step 2: Adapt current CSV reading and real XLSX inspection with openpyxl into spreadsheet_read, loading formulas and cached values separately, preserving workbook hash, sheet visibility, dimensions, tables, ranges, cell coordinates, and source-locator semantics. Preserve Evidence and CalculationRecord semantics without parsing numeric values from Evidence.excerpt regexes. TypedTable names fields for columns, rows, join keys, null/duplicate semantics, and provenance; TypedMeasurement names value, unit, period/scenario, and source locator; AnalysisResult names operation, inputs, outputs, assumptions, truncation, applied limits, and provenance.
- [x] Step 3: Adapt pandas-backed bounded transformations into data_analysis and current calculation owners into calculation. Support filter, join, aggregate, compare, profile, scenario, and sensitivity operations over typed values. Reject input/work-limit exceedance; only returned-item limits may truncate, and truncation must set an explicit flag, applied limit, and preserved provenance. Route decision-critical formula uncertainty to BLOCKED_RECALCULATION and domain_validation rather than inventing recalculated values.
- [x] Step 4: Adapt bounded graph and domain validation functions into graph_context and domain_validation bindings with explicit limits, visited-node/visited-edge telemetry, and no full-graph pre-scan. Add CSV, real multi-sheet XLSX, stale-cache XLSX, and larger synthetic XLSX fixtures containing multiple periods, scenarios, missing values, duplicate rows, units, formulas, absent caches, stale cached results after changed inputs, cached errors, cross-sheet references, one contradiction, a high-fan-out graph, and a many-to-many join. Preserve both formula expressions and cached values without adding an Excel formula engine; classify stale/unknown caches and propagate `BLOCKED_RECALCULATION` to decision-critical analysis. Enforce `asyncio.CancelledError` and deadline checks before workbook allocation, after each sheet, during row/cell conversion, before/after formula/cache loads, and before/after each analysis operation. Assert hand-calculated outputs, source locations, formula statuses, source hash unchanged before/after, and cancellation at parsing, table conversion, and analysis checkpoints with stable failure classification, settled workers, closed handles, no retained workbook lock, and no temporary-resource leaks.

Verification:
- [x] python -m pytest -q tests/test_local_toolbelt.py tests/test_xlsx_probe.py tests/test_graph.py tests/test_calculation_revision.py tests/test_analysis_schema.py
- Expected: CSV and real multi-sheet XLSX results match hand-calculated fixtures; workbook structure, cell-level provenance, formula/cache uncertainty, limits, assumptions, contradictions, invalid inputs, cancellation, and source-integrity outcomes are explicit; source files remain byte-identical.

Exit Criteria:
- Local Analyst tools are reusable, instrumented, bounded adapters over existing owners, with real CSV/XLSX read-only inspection and analysis, cell-level provenance, truthful formula semantics, no duplicate domain truth, and no hidden mutation.

### Task 6: Implement the toolbelt probe matrix, disposable MCP proof, and soak receipt

Purpose:
- Turn the tool layer into an operational reliability contract with explainable failures, sanitized receipts, and bounded repeated-run evidence.

Task Function:
- Build layered probes from capability contract through routing, execution, domain/persistence effects, failure recovery, and soak measurement.

Template Profile:
- Controller-selected: unresolved
- Selection basis: resolve from probe breadth and resource-observation requirements.

Validator Profile:
- Controller-selected: unresolved
- Selection basis: use an independent review profile at activation when probe output is used as a release gate.

Specification Coverage:
- Success and adversarial probes cover every runnable tool.
- Disposable MCP protocol proof independently discovers, calls, and closes an allowed read-only tool through the official SDK fixture.
- Foresight-path MCP proof independently covers Controller assignment -> native MAF MCP resolver binding -> MAF agent tool request -> MCP server -> result returned to the agent.
- Environment-gated real web/MCP probes attempt the configured connection; they report BLOCKED_EXTERNAL only when configuration is absent, FAILED for attempted failures, and VERIFIED only with a sanitized receipt.
- Soak establishes resource baselines after the 10-run warmup and observes owned resources, unfinished tasks, child processes, state/revision hash, failure class, and metric drift. File/socket counts and RSS remain platform-dependent diagnostics.

Required Skills:
- skill-backend-verification
- skill-test-driven-development

Files And Symbols:
- Inspect: evaluation/probes/real_web_probe.py, evaluation/probes/run_mcp_probe.py, evaluation/probes/run_anomaly_probe.py, evaluation/run.py, src/foresight_os/runtime/metrics.py
- Modify: new evaluation/probes/run_toolbelt_probe.py, new evaluation/probes/run_evidence_workflow_probe.py, new evaluation/probes/run_xlsx_probe.py, new evaluation/probes/run_foresight_mcp_probe.py, new evaluation/probes/run_toolbelt_anomaly_probe.py, evaluation/probes/run_mcp_probe.py, evaluation/probes/real_web_probe.py, evaluation/run.py, tests/test_local_toolbelt.py, tests/test_xlsx_probe.py, tests/test_mcp_probe_contract.py, tests/test_anomaly_probe.py
- Verify: evaluation/README.md, sanitized JSON receipts under work/toolbelt-probes

Dependencies:
- Tasks 1–5 provide the capabilities and workflow under test.
- Probe receipts contain only commit/probe/pattern/stage/participant/capability IDs, provider name or host, counts, latency, failure class, revision numbers, cleanup, pass/fail, and blocker reason.

Authority:
- Preauthorized local actions: run disposable loopback MCP, local HTTP fixtures, fixed-seed soak, and temporary resource observations; write only sanitized receipts under work/toolbelt-probes.
- Stop for: real credentials, private endpoints, external writes, raw payload capture, unexplained anomaly suppression, or making external availability a PR requirement.

Steps:
- [x] Step 1: Add capability-level success and failure cases for web search, page retrieval, spreadsheet read, data analysis, calculation, graph context, and domain validation. The spreadsheet cases must use real multi-sheet XLSX workbooks and cover hidden sheets/rows, selected ranges/tables, formulas versus cached values, dates/types/errors, merged headers, missing values, duplicates, cross-sheet references, source cell/range provenance, deterministic calculations, sensitivity/scenario analysis, stale-cache blocking, cancellation at parsing/conversion/analysis checkpoints, and unchanged source bytes.
- [x] Step 2: Add the evidence workflow probe with a disposable provider and assert candidate count, retrieval proof, claim/evidence linkage, revision transition, cleanup, and raw-payload exclusion. Add the XLSX-to-finding path and a persisted spreadsheet restart checkpoint proving completed extraction/analysis is not repeated and recovered provenance/formula statuses remain intact.
- [x] Step 3: Add the independent official-SDK disposable MCP protocol probe for discover/call/close, then add the separate Foresight-path probe for Controller assignment, native MAF binding, agent request, server call, result return, and session close. Enforce read-only discovery filtering in both, and fail the probe if either layer fails. Give `run_xlsx_probe.py` and `run_mcp_probe.py` an `--installed` mode that does not inject checkout `src` into `sys.path`, so clean-wheel proof exercises the installed package.
- [x] Step 4: Add the XLSX reliability probe with the mandatory real workbook fixture and a larger synthetic workbook; measure load/analysis latency, peak memory, processed rows/cells, result size, cancellation cleanup, formula uncertainty, provenance completeness, and SHA256 before/after equality. Then add the 10-warmup/100-measured fixed-seed soak with a fixed measured schedule of 25 success, 15 timeout, 15 cancellation, 15 MCP failure, 10 invalid-input, 10 budget-exhaustion, and 10 concurrent workflows. Establish baselines after warmup, define the expected result/failure class and metric delta for each scenario, require zero unfinished owned tasks/sessions/child processes after settled cleanup, and classify sustained or monotonic owned-resource drift over the final 20 measured samples. Add a clean-control case and a deliberately leaking fixture that the gate must detect.
- [x] Step 5: Run the deterministic contract/controller pattern matrices, the mandatory XLSX fixture and restart workflow, and both environment-gated real-provider probes. Emit stable VERIFIED, FAILED, or BLOCKED_EXTERNAL outcomes and never collapse missing configuration into deterministic success.

Verification:
- [x] python -m pytest -q tests/test_mcp_probe_contract.py tests/test_anomaly_probe.py
- [x] python evaluation/probes/run_toolbelt_probe.py --output-root work/toolbelt-probes
- [x] python evaluation/probes/run_evidence_workflow_probe.py --output-root work/toolbelt-probes
- [x] python evaluation/probes/run_xlsx_probe.py --output-root work/toolbelt-probes
- [x] python evaluation/probes/run_mcp_probe.py --mode disposable --output-root work/toolbelt-probes
- [x] python evaluation/probes/run_crawl4ai_probe.py --installed --output-root work/toolbelt-probes
- [x] python evaluation/probes/run_foresight_mcp_probe.py --output-root work/toolbelt-probes
- [x] python evaluation/probes/run_toolbelt_anomaly_probe.py --warmup 10 --runs 100 --seed 20261012 --output-root work/toolbelt-probes
- [x] python evaluation/probes/real_web_probe.py --query "${FORESIGHT_REAL_WEB_QUERY}" --output-root work/toolbelt-probes
- [x] python evaluation/probes/run_mcp_probe.py --mode real-mcp --output-root work/toolbelt-probes
- Expected: no unexplained incorrect result, unauthorized call, budget overrun, state corruption, stale artifact, misleading telemetry, leaked owned resource, or retained raw payload within the defined probe envelope.

Exit Criteria:
- Probe outputs are deterministic or explicitly environment-gated, sanitized, and sufficient to explain failures by layer.

### Task 7: Reconcile documentation, package configuration, and final proof

Purpose:
- Make repository documentation, optional dependencies, CI, and plan evidence truthful to the implemented toolbelt and probe tiers.

Task Function:
- Reconcile maintained docs and final verification with source and test truth.

Template Profile:
- Controller-selected: none (lead controller)
- Selection basis: documentation and final verification are lead-owned integration work.

Validator Profile:
- Controller-selected: none
- Selection basis: final verification skill owns the acceptance gate.

Specification Coverage:
- Semantic IDs, retrieval-proof gate, source-trust review, package extras, probe tiers, receipts, and external blockers are documented once at their owning layers.
- CI remains credential-free and fast; nightly/manual gates carry external or soak work.

Required Skills:
- skill-verification-before-completion
- skill-code-standards

Files And Symbols:
- Inspect: README.md, evaluation/README.md, docs/intent/maf-capability-decision.md, .github/workflows/ci.yml, pyproject.toml
- Modify: the same canonical documentation/configuration files and this plan only for accepted deviations and evidence
- Verify: all changed source/test/config/doc files and final Git diff

Dependencies:
- Tasks 1–6 complete with accepted task-local proof.
- Do not mark the plan completed from checked boxes alone; reconcile receipts, blockers, and final commands.

Authority:
- Preauthorized local actions: edit maintained docs/configuration and run final deterministic, package, probe-contract, and whitespace checks.
- Stop for: publishing results, pushing or merging, changing CI protection, deleting preserved artifacts, or claiming real provider verification without a receipt.

Steps:
- [x] Step 1: Update README, evaluation guidance, and MAF capability decision with the canonical semantic vocabulary and evidence workflow.
- [x] Step 2: Add openpyxl and pandas as core runtime dependencies in project.dependencies, pin or constrain them for reproducible CI, and keep only the disposable MCP path in an explicit optional dependency group. CI must always install the core dependencies and execute the real multi-sheet XLSX fixture; include a deterministic installation and fixture check for the accepted MCP extra.
- [x] Step 3: Record accepted probe receipts, external blockers, deviations, and deferred capabilities in the plan evidence and completion notes.
- [x] Step 4: Run final verification and reconcile plan status only after fresh evidence passes.

Verification:
- [x] python -m pytest -q
- [x] python -m compileall -q src tests evaluation
- [x] python evaluation/run.py --matrix contract --output-root work/toolbelt-probes
- [x] python evaluation/run.py --matrix controller
- [x] python evaluation/probes/run_xlsx_probe.py --output-root work/toolbelt-probes
- [x] python -m build --wheel --outdir work/fresh-wheel
- [x] python -m venv work/fresh-wheel-venv
- [x] powershell -NoProfile -Command "$wheel=@(Get-ChildItem 'work/fresh-wheel/*.whl'); if ($wheel.Count -ne 1) { throw 'expected exactly one newly built wheel' }; & 'work/fresh-wheel-venv/Scripts/python' -m pip install --no-deps $wheel[0].FullName"
- [x] powershell -NoProfile -Command "$repo=(Resolve-Path '.').Path; $smoke=Join-Path $env:TEMP 'foresight-wheel-smoke-20261012'; New-Item -ItemType Directory -Force $smoke | Out-Null; Push-Location $smoke; try { & (Join-Path $repo 'work/fresh-wheel-venv/Scripts/python') -c 'import importlib.metadata as m; import importlib.resources as r; assert m.version("foresight-os"); assert r.files("foresight_os").joinpath("schemas").is_dir()' } finally { Pop-Location }"
- [x] python -m venv work/fresh-base-venv
- [x] powershell -NoProfile -Command "$wheel=@(Get-ChildItem 'work/fresh-wheel/*.whl'); if ($wheel.Count -ne 1) { throw 'expected exactly one newly built wheel' }; & 'work/fresh-base-venv/Scripts/python' -m pip install $wheel[0].FullName"
- [x] powershell -NoProfile -Command "$repo=(Resolve-Path '.').Path; $smoke=Join-Path $env:TEMP 'foresight-installed-xlsx-smoke-20261012'; New-Item -ItemType Directory -Force $smoke | Out-Null; Push-Location $smoke; try { & (Join-Path $repo 'work/fresh-base-venv/Scripts/python') (Join-Path $repo 'evaluation/probes/run_xlsx_probe.py') --installed --fixture (Join-Path $repo 'tests/fixtures/analyst_multisheet.xlsx') --output-root (Join-Path $repo 'work/toolbelt-probes') } finally { Pop-Location }"
- [x] python -m venv work/fresh-mcp-venv
- [x] powershell -NoProfile -Command "$wheel=@(Get-ChildItem 'work/fresh-wheel/*.whl'); if ($wheel.Count -ne 1) { throw 'expected exactly one newly built wheel' }; & 'work/fresh-mcp-venv/Scripts/python' -m pip install ($wheel[0].FullName + '[mcp]')"
- [x] work/fresh-mcp-venv/Scripts/python evaluation/probes/run_mcp_probe.py --mode disposable --installed --output-root work/toolbelt-probes
- [x] git diff --check
- Expected: all deterministic checks pass, CSV and XLSX contract/provenance/failure/cancellation/source-integrity probes pass, the single newly built wheel installs into clean environments, no-deps package/schema inspection runs outside the checkout, the normal base wheel executes the XLSX probe outside the checkout without source-path injection, the accepted MCP extra installs and executes its disposable fixture, receipts are sanitized, external blockers are explicit, and no preserved generated output is staged.

Exit Criteria:
- Source, tests, probes, package metadata, documentation, and the final plan all describe the same implemented capability surface and evidence state.

## Completion Notes

- `IMPLEMENTATION_VERIFIED`: PASS. Typed routing, capability registry, retrieval boundary, evidence workflow, XLSX inspection/analysis, package metadata, schema, CI, tests, and compile checks pass.
- `TOOLBELT_RELIABILITY_VERIFIED`: PASS. The toolbelt, evidence workflow, XLSX finding path, disposable MCP path, Foresight MCP path, and fixed-seed anomaly soak pass with sanitized receipts and no detected owned-resource drift.
- `EXTERNAL_INTEGRATION`: the first-class web-search provider remains environment-owned; the hosted external-signal probe is `VERIFIED` for GitHub through the secure `gh` keyring, `VERIFIED` for Alpha Vantage using its explicitly marked public demo credential, and `BLOCKED_EXTERNAL` for FRED because its OAuth bearer token is absent. These outcomes remain distinct from implementation and toolbelt reliability proof.
- Local SearXNG integration: `VERIFIED` through the live `http://127.0.0.1:8888` instance with `FORESIGHT_WEB_SEARCH_PROVIDER=searxng`, producing 5 candidates, 1 instrumented tool call, sanitized output, and scope-owned cleanup. The unreachable-endpoint probe also classified the dependency failure as `WebSearchError` with exit status 1.
- Crawl4AI MAF-agent boundary: `VERIFIED` against the live IEA Global EV Outlook 2024 page through an injected `web_crawl` tool; public-destination validation, 4,000-character bounded extraction, provenance proof, raw-payload stripping, and scope cleanup passed in source-tree and installed-package modes.
- Power BI Modeling MCP boundary: EULA accepted and MCP server reachable; no configured connections or local Desktop/Analysis Services instances were available. A disposable offline model was created and disconnected cleanly, but the MCP correctly rejected DAX execution on offline connections, so live external data-analysis remains `BLOCKED_EXTERNAL` pending an approved connected model.
- Public-web bridge probe: `VERIFIED` against a real DuckDuckGo HTML response for the safe query `OpenAI official documentation`, producing 2 normalized candidates, 1 instrumented tool call, sanitized output, and scope-owned cleanup. The bridge exercised the existing Foresight provider contract without adding credentials or changing the approved endpoint boundary; its receipt is real-web evidence, not direct-provider configuration evidence.
- Configured web-search transport smoke: `VERIFIED` against a temporary loopback fixture; this separately proves adapter resolution, candidate normalization, instrumentation, and cleanup.
- XLSX release proof includes multi-sheet and hidden-content inspection, hidden rows, selected tables/ranges, merged headers, dates/types/errors, missing values, duplicates, cross-sheet references, formula/cache classification including stale-cache blocking, cell/range/workbook provenance, deterministic calculation/scenario/sensitivity results, cancellation checkpoints, pending-review restart recovery, and unchanged source SHA256.
- Intentional architecture refinement: the evidence workflow remains a thin persistence/acceptance application service; typed controller routing and `run_recipe_async` retain ownership of scheduling, lifecycle, budgets, and participant scopes.
- Hosted external signal MCP activation now follows one shared MAF-only binding layer in `src/foresight_os/runtime/external_signals.py`: GitHub maps to `technology_signals`, Alpha Vantage maps to `market_signals`, and FRED maps to `macro_signals`. Credentials remain runtime-only, provider calls are read-only, known catalogs are allowlisted, and owned MCP sessions close with the run scope. Alpha Vantage still needs `ALPHAVANTAGE_API_KEY` for production credential readiness, and FRED still needs `FRED_MCP_TOKEN` plus a bounded read operation. Crawl4AI remains activated as `web_crawl`; document parsing, internal knowledge, SQL, and artifact generation remain unavailable.
## Verification

Final artifact-level verification runs from a clean feature workspace with
preserved generated outputs excluded from the diff:

- python -m pytest -q
- python -m compileall -q src tests evaluation
- python evaluation/run.py --matrix contract --output-root work/toolbelt-probes
- python evaluation/run.py --matrix controller
- python evaluation/probes/run_toolbelt_probe.py --output-root work/toolbelt-probes
- python evaluation/probes/run_evidence_workflow_probe.py --output-root work/toolbelt-probes
- python evaluation/probes/run_xlsx_probe.py --output-root work/toolbelt-probes
- python evaluation/probes/run_mcp_probe.py --mode disposable --output-root work/toolbelt-probes
- [x] python evaluation/probes/run_crawl4ai_probe.py --installed --output-root work/toolbelt-probes
- [x] python evaluation/probes/run_external_signal_probe.py --output-root work/toolbelt-probes
- python evaluation/probes/run_foresight_mcp_probe.py --output-root work/toolbelt-probes
- python evaluation/probes/run_toolbelt_anomaly_probe.py --warmup 10 --runs 100 --seed 20261012 --output-root work/toolbelt-probes
- git diff --check
- git status --short --branch

Expected final evidence:

- no capability executes during resolution;
- no unassigned capability executes;
- no data-scope escape, unauthorized mutation, budget overrun, concurrency breach,
  Handoff permission inheritance, or Group Chat round overrun;
- no search-only material claim enters durable state;
- no raw external payload enters AnalysisState;
- every calculation carries reproducible inputs, formula, units, and provenance;
- no stale artifact is presented as current;
- no competing revision is lost;
- CSV and XLSX workbook inspection/analysis preserves required structure, formula/cache truth, cell/range provenance, deterministic scenario/sensitivity results, cancellation cleanup, and unchanged source SHA256;
- no owned agent, provider, MCP session, task, file, or socket leaks within the probe envelope;
- bounded graph queries do not perform a complete traversal before applying limits;
- real web and MCP results are recorded independently as VERIFIED, BLOCKED_EXTERNAL
  only when required configuration is absent, or FAILED when an attempted
  connection fails. External blocking or failure neither upgrades nor overwrites
  IMPLEMENTATION_VERIFIED or TOOLBELT_RELIABILITY_VERIFIED.
- hosted external signal receipts prove MAF-agent injection, remote tool
  discovery, a bounded read-only operation, sanitized result metadata, and
  scope-owned cleanup; demo credentials remain explicitly non-production-ready.

## Completion Criteria

The plan is ready for completion verification when:

1. all fourteen semantic capability IDs are represented in one canonical registry with truthful available or unavailable states;
2. typed Work Stage requirements replace substring routing and preserve legacy briefs without guessing;
3. web_search and page_retrieval complete the source-verification boundary;
4. one deterministic evidence workflow produces an evidence-linked accepted revision;
5. local CSV/XLSX spreadsheet reading, deterministic table analysis, calculation, graph, and validation bindings pass direct contract, provenance, failure, cancellation, and source-integrity probes;
6. failure, cancellation, budget, stale-revision, malformed-source, MCP, and cleanup paths are classified and tested;
7. the fixed-seed soak produces no unexplained drift in results, state, metrics, tasks, or resources;
8. docs, package extras, CI, receipts, and external blockers match repository truth;
9. all declared task proofs and final verification commands pass; and
10. any deferred document_read, real MCP, SQL, internal-knowledge, or artifact-generation work is recorded as a bounded follow-up rather than implied complete.

Completion evidence is reported as three independent outcomes:

- IMPLEMENTATION_VERIFIED: deterministic code, contract, tests, package, and schema checks pass.
- TOOLBELT_RELIABILITY_VERIFIED: vertical slices, fault probes, disposable MCP proof, and soak pass.
- EXTERNAL_INTEGRATION: VERIFIED, BLOCKED_EXTERNAL, or FAILED according to the configured real web/MCP probe receipt.
