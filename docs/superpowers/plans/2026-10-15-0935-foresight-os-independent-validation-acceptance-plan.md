---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: foresight-os-independent-validation-acceptance
targets:
  - src/foresight_os/domain/models.py
  - src/foresight_os/domain/challenge.py
  - src/foresight_os/domain/validation.py
  - src/foresight_os/controller/policy.py
  - src/foresight_os/controller/recipes.py
  - src/foresight_os/analysis/reviewer.py
  - src/foresight_os/analysis/evidence_workflow.py
  - src/foresight_os/analysis/review_workflow.py
  - src/foresight_os/analysis/independent_validation.py
  - src/foresight_os/persistence/analysis_store.py
  - src/foresight_os/schemas/analysis.schema.json
  - src/foresight_os/schemas/execution_recipe.schema.json
  - src/foresight_os/artifacts/report.py
  - src/foresight_os/artifacts/presentation.py
  - evaluation/cases/ncc-2022-cosluxe-vietnam/
  - evaluation/probes/run_ncc_independent_validation.py
  - tests/fixtures/ncc-independent-validation.xlsx
  - tests/
  - docs/evidence-and-evaluation.md
---

# Foresight OS Independent Validation and Acceptance Plan

## Verdict Review

The verdict is accepted as the direction for the next delivery, with one
important scope correction: independent validation is a required workflow
phase, not a requirement for four permanent agents or a second validation
runtime.

The source review correctly identifies four gaps that must be closed together:

1. the recipe does not make review categories, reviewer capabilities, or review
   skills executable requirements;
2. the ordinary stage-result path does not itself establish a durable review
   record;
3. review selection can choose one passing current record while hiding another
   required validator's unresolved objection; and
4. review records are broader than the work actually checked and do not record
   reviewer or execution identity.

The verdict's quantitative corrections are also adopted. The implementation
must keep offline and ecommerce measures separate until definitions, periods,
units, and denominators are normalized; treat `1.08x` and `1.1664x` as planning
thresholds rather than observed business performance; and emit conditional
recommendations with explicit missing inputs when margin, capacity, or
distribution evidence is absent.

The review was source-based and did not rerun the NCC workbook. This plan
therefore includes a real-workbook, independent-calculation probe as required
local acceptance evidence when the external workbook and persisted analysis are
available, while CI uses a tiny generated fixture. Existing `AnalysisStore`, `ReviewRecord`,
`CapabilityResolver`, local spreadsheet toolbelt, and report/presentation
boundaries remain canonical. No second orchestration engine, review registry,
or connector-owned analytical store is introduced.

## Goal

Deliver an explicit validation phase between provisional findings and human
acceptance:

    provisional findings
      -> independent source/scope checks
      -> independent calculation reconciliation
      -> independent decision challenge
      -> discrepancy reconciliation and affected-finding recheck
      -> human acceptance
      -> final delivery

The phase must be executable from an approved `ExecutionRecipe`, persist
target-scoped review records with provenance and execution identity, aggregate
all required review categories before acceptance, and prove the behavior on
the NCC Cosluxe workbook without editing the source workbook or treating the
8% target as an observed result.

## Implementation Outcomes

### Explicit review requirements and routing

Compiled recipe stages declare the four stable review category IDs
`source_fidelity`, `scope_reconciliation`,
`calculation_reconciliation`, and `decision_challenge`. The Controller maps
those categories to reviewer capabilities and packaged skills independently of
the producer's capabilities. A validator can therefore read the workbook and
recompute metrics without relying on the analyst's calculation function.

The category vocabulary is typed and versioned by the approved
`ExecutionRecipe.review_policy` and `RecipeStage.review_checks`. System-derived
requirements are not copied into `WorkBrief`; only an explicit human request
for independent validation may remain in user intent. Existing free-text review
labels remain legacy and do not satisfy new typed coverage.

### Durable, target-scoped review evidence

Each persisted review record identifies its category, exact target IDs,
reviewer, execution and attempt identity, method, source/input fingerprints,
skill versions/hashes, policy identity, objections, and outcome. Legacy records
remain loadable but cannot satisfy a newly declared required review category.
The trusted review attachment path, rather than arbitrary stage output, owns
record creation and persistence.

### Aggregate acceptance and honest finding views

Derived finding views aggregate every required current review category. Missing
or stale coverage, unresolved blocking objections, and explicit missing inputs
remain visible. One passing validator or Group Chat consensus cannot override a
different required validator's unresolved failure. Reports and presentations
identify whether source fidelity, arithmetic, or decision support passed.

### Independent NCC reconciliation proof

The NCC probe consumes the actual persisted `AnalysisState` alongside the
workbook. It proves workbook hash and sheet/scope fidelity, raw-cell
recalculation of growth, shares, launch survival, and compounded thresholds,
category/channel mapping and comparability rules, conditional handling of
missing feasibility inputs, and rejection of wrong denominators, value/volume
mix-ups, invalid mappings, changed workbook hashes, and incomplete review
coverage.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-plan-document-reviewer`, `skill-executing-plans`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit the declared tracked sources, tests, fixture specification, probe, and maintained documentation; run declared local checks; write disposable validation evidence under a new `work/` output directory without changing preserved outputs
- User-approval actions: push, merge, publication, external provider calls, deletion or cleanup of existing `work/` outputs, and changes outside the declared targets
- Parallel ownership: none; shared review contracts and persistence require sequential integration
- Sequential fallback: Tasks 1–2 establish the contract, Tasks 3–4 implement independent validation and aggregate acceptance, Task 5 adds NCC evidence and documentation, and Task 6 performs final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Target base commit: `4a1458e` (`origin/main`, the verdict-identified current main)
- Reconciled execution workspace: `main` at `4a1458e`; the preserved untracked-output boundary was checked before fast-forward and remains in place
- Next action: none; implementation and verification are complete for the approved local scope
- Blockers: none for the declared local scope; decision challenge and human acceptance remain intentionally separate, explicit steps and are not claimed by the deterministic probe

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `complete` | current | `codex` | none | focused contract and recipe tests | `30 passed` in focused suite; accepted |
| Task 2 | `complete` | current | `codex` | Task 1 | model, schema, migration, and persistence tests | `31 passed` in focused suite; accepted |
| Task 3 | `complete` | current | `codex` | Tasks 1–2 | independent validator unit tests with seeded failures | `47 passed`; accepted |
| Task 4 | `complete` | current | `codex` | Tasks 2–3 | end-to-end review-phase and aggregate-acceptance tests | focused review/workflow suites passed; accepted |
| Task 5 | `complete` | current | `codex` | Task 4 | NCC workbook probe and report/documentation evidence | fixture and mutation matrix passed; revised real-workbook probe passes deterministic checks and remains `NOT_VERIFIED` pending challenge/acceptance |
| Task 6 | `complete` | current | `codex` | Tasks 1–5 | repository-wide required verification commands | fresh full suite, compileall, fixture probe, real probe, Markdown links, and diff checks passed; verifier `verified` |

## Task Breakdown

### Task 1: Make review categories executable in the approved recipe

**Purpose:**
- Convert the existing free-text recipe review labels into one typed, versioned, vendor-neutral contract without adding a second orchestration layer or changing `WorkBrief` intent.

**Task Function:**
- Contract and policy routing

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: the task is bounded but changes shared model and Controller contracts; resolve profile from current registry at activation.

**Validator Profile (optional):**
- Controller-selected: `not applicable`
- Selection basis: the lead controller owns contract integration; focused tests are the validator.

**Specification Coverage:**
- Explicit independent validation phase; flexible assignment rather than four permanent agents; reviewer capabilities and skills must be executable requirements; review policy must be approval-bound.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `src/foresight_os/controller/recipes.py:RecipeStage`, `ExecutionRecipe`, `src/foresight_os/controller/policy.py:ReviewPolicy`, `ReviewPolicyResolver`, `_recipe_for_patterns`, and `src/foresight_os/schemas/execution_recipe.schema.json`
- Modify: existing `RecipeStage.review_checks` and `ExecutionRecipe.review_policy` serialization, `src/foresight_os/controller/recipes.py:ReviewCheckKind`, `src/foresight_os/controller/policy.py:ReviewPolicyResolver`, `_recipe_for_patterns`, and `src/foresight_os/schemas/execution_recipe.schema.json`; do not add `WorkStage.review_checks` or change `work_brief.schema.json`
- Verify: `tests/test_controller_selection.py`, `tests/test_research_needs.py`, `tests/test_stage_inputs.py`, `tests/test_analysis_schema.py`, `tests/test_review_policy.py`, and the added `tests/test_execution_approval_fingerprint.py`

**Dependencies:**
- The target source is `4a1458e`; reconcile the workspace before editing because the current checkout is older than the target base.
- Use the existing `ResearchNeedKind`, `SkillRegistry`, and capability map as owners for capability identity; do not create a parallel review registry.
- Keep policy-derived requirements in Controller/`ReviewPolicy` and the approved recipe; `WorkBrief` remains the owner of investigation intent.

**Authority:**
- Preauthorized local actions: modify only the listed recipe, policy, schema, approval tests, and focused test files; run their focused tests.
- Stop for: changing existing `work/` outputs, introducing a new registry, or changing execution topology outside review-capability routing.

**Steps:**
- [x] Step 1: Introduce one typed `ReviewCheckKind` vocabulary for `source_fidelity`, `scope_reconciliation`, `calculation_reconciliation`, and `decision_challenge`; validate `RecipeStage.review_checks` against it while preserving unknown historical labels as legacy, non-satisfying values.
- [x] Step 2: Make `ReviewPolicyResolver` derive the union of applicable categories from target kind, material dependencies, research needs, and consequence level. Do not impose all four categories on every investigation; emit `independent-validation/v1` only for the new typed regime.
- [x] Step 3: Map review categories to analytical methods first, then resolve capabilities from material source dependencies. Structured-data and quantitative needs add `spreadsheet_read`/calculation capabilities only when those dependencies are declared.
- [x] Step 4: Compile producer capabilities from stage research needs and reviewer capabilities/skills from review categories separately. Preserve stage and participant `skill_ids`, unresolved capability reporting, direct-topology rejection semantics, and existing recipe serialization.
- [x] Step 5: Keep legacy labels such as `independent review` and `stage output validation` readable but non-satisfying; new Controller output uses only typed IDs. Requiring the new regime regenerates the recipe and requires human reapproval rather than reinterpreting an old approval.
- [x] Step 6: Prove that the existing approval fingerprint changes when required review coverage or policy version changes, while runtime reviewer attempt identity remains outside the execution approval projection.

**Verification:**
- [x] Run `python -m pytest -q tests/test_controller_selection.py tests/test_research_needs.py tests/test_stage_inputs.py tests/test_analysis_schema.py tests/test_review_policy.py tests/test_execution_approval_fingerprint.py` (`30 passed`).
- Expected: an approved recipe with typed checks compiles to distinct producer and reviewer requirements; missing or unknown new checks fail validation; legacy labels remain readable but cannot satisfy new coverage; existing recipe and stage-input behavior remains green; review-policy changes stale the prior execution approval.

**Exit Criteria:**
- Review category requirements are typed, versioned, validated, serialized in `execution_recipe.schema.json`, compiled into distinct producer/reviewer capability and skill assignments, and covered by approval-fingerprint tests without modifying `WorkBrief`.

### Task 2: Harden review identity, scope, and persistence

**Purpose:**
- Make every review record an auditable statement about what was checked, by whom, with which inputs, and under which execution attempt.

**Task Function:**
- Persistence and provenance hardening

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: the task changes durable state and migration behavior; resolve profile from current registry at activation.

**Validator Profile (optional):**
- Controller-selected: `not applicable`
- Selection basis: persistence round trips and schema validation provide bounded proof.

**Specification Coverage:**
- Review scope and trusted reviewer identity are explicit; review output uses the trusted attachment/persistence path; legacy state remains readable without falsely satisfying new coverage; retries and independent conflicts remain auditable.

**Required Skills:**
- `skill-code-standards`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/domain/models.py:AnalysisState`, `src/foresight_os/domain/challenge.py:ReviewRecord`, `review_validity`, `src/foresight_os/analysis/reviewer.py:ReviewResult`, `src/foresight_os/analysis/evidence_workflow.py:attach_review_record`, `src/foresight_os/persistence/analysis_store.py:load_analysis`, `_merge_states`
- Modify: `src/foresight_os/domain/models.py:AnalysisState`, `src/foresight_os/domain/challenge.py:ReviewRecord`, `ReviewCheckResult`, `FindingView`, `src/foresight_os/analysis/reviewer.py:ReviewResult` and review constructors, `src/foresight_os/analysis/evidence_workflow.py:attach_review_record`, `src/foresight_os/persistence/analysis_store.py`, `src/foresight_os/domain/validation.py`, `src/foresight_os/schemas/analysis.schema.json`
- Verify: `tests/test_review_records.py`, `tests/test_review_hardening.py`, `tests/test_evidence_workflow.py`, `tests/test_analysis_schema.py`

**Dependencies:**
- Task 1 defines the valid review category IDs.
- Preserve `input_fingerprint`, skill versions/hashes, policy identity, atomic `AnalysisStore` writes, and pending-token behavior. The existing lock/read/merge/atomic-write boundary remains the persistence owner.

**Authority:**
- Preauthorized local actions: modify only the listed review domain, adapter, persistence, schema, and focused test files; run serialization and persistence tests against temporary stores.
- Stop for: destructive migration of existing analysis files, changing review identity into a credential, or persisting raw provider payloads.

**Steps:**
- [x] Step 1: Add typed v2 review metadata: `check_id`, `reviewer_id`, `execution_id`, `attempt_id`, `method`, `source_fingerprints`, dependency-level fingerprints, slot key, and supersession/conflict references. Reviewer identity is provenance, not authentication, and trusted runtime context—not model output—supplies these fields.
- [x] Step 2: Add a nested `ReviewCheckResult` for category-specific evidence: status, expected, actual, delta, tolerance, source/input IDs, interpretation, and limitations. Source checks retain expected/observed fingerprints plus source/input identity; decision challenges can remain objection-led.
- [x] Step 3: Change `attach_review_record` to receive explicit target IDs and trusted review metadata, reject empty targets, and attach only the records actually checked. Legacy callers remain readable through the legacy attachment path; typed callers cannot omit scope.
- [x] Step 4: Define a review slot as target + typed check + policy version + material fingerprint + method. Same-reviewer retries supersede the prior attempt without deleting it; independent validators on the same inputs remain conflicting.
- [x] Step 5: Migrate durable `AnalysisState` representation from schema version 1 to version 2. Legacy records remain readable, are marked legacy, and do not satisfy typed coverage.
- [x] Step 6: Update JSON schema, validation, load/migrate, merge, and round-trip serialization. Source SHA and dependency fingerprints remain separate inputs to material review validity.
- [x] Step 7: Add derived coverage statuses `PASS`, `FAIL`, `PENDING`, `STALE`, and `CONFLICT` without changing canonical analytical records; focused persistence tests prove idempotent/supersession/conflict behavior at the store boundary.

**Verification:**
- [x] Run `python -m pytest -q tests/test_review_records.py tests/test_review_hardening.py tests/test_evidence_workflow.py tests/test_analysis_schema.py tests/test_review_v2.py` (`31 passed`).
- Expected: target-scoped v2 records round-trip through `AnalysisStore`; legacy records load but do not satisfy new required checks; changed material inputs make the matching record stale; retries preserve history and supersede only their slot; repeated attachment is idempotent by review ID; conflicting validator records remain visible.
- [ ] Inspect the temporary store's `analysis.pending.json` and `analysis.json` in the test output when the persistence tests exercise accepted and rejected paths.
- Expected: only typed review metadata and sanitized provenance are persisted.

**Exit Criteria:**
- Review records have explicit scope, typed reconciliation evidence, trusted execution provenance, schema/migration behavior, retry/conflict semantics, and concurrency coverage; the persistence boundary cannot turn broad or anonymous review output into accepted coverage.

### Task 3: Implement reusable deterministic validation mechanics

**Purpose:**
- Add reusable deterministic validation mechanics that derive expected values from canonical inputs before comparing them with provisional analyst results. Keep strategic decision challenge separate from deterministic source and calculation proof.

**Task Function:**
- Independent reconciliation

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: the task requires workbook semantics, arithmetic independence, and failure classification; resolve profile from current registry at activation.

**Validator Profile (optional):**
- Controller-selected: `unresolved while task is pending`
- Selection basis: select independently from the executor based on the bounded validation contract; the validator must be able to inspect raw workbook data and reason about arithmetic failures.

**Specification Coverage:**
- Provide the mechanics needed to verify source fidelity, scope reconciliation, calculation reconciliation, and explicit missing-input conditions without claiming future feasibility or independently proving strategic challenge.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/local_toolbelt.py:spreadsheet_read`, `SheetSelection`, `WorkbookReadResult`, `TypedTable`, and the existing benchmark validator only for compatible result shapes
- Add: `src/foresight_os/analysis/independent_validation.py` for generic mechanics, `evaluation/cases/ncc-2022-cosluxe-vietnam/review-spec.json`, and `tests/test_ncc_independent_validation.py`
- Modify: `src/foresight_os/runtime/local_toolbelt.py` only when the existing API cannot expose required provenance or hidden-content facts; do not turn `src/foresight_os/analysis/foresight_validator.py` into the generic review engine
- Verify: `tests/test_local_toolbelt.py`, `tests/test_ncc_independent_validation.py`

**Dependencies:**
- Tasks 1–2 define the review category and provenance contracts.
- Repository tests use a tiny generated or sanitized XLSX fixture under temporary directories. The real NCC workbook is an external local fixture: record its SHA-256 and sanitized evidence, but never track or copy its bytes into Git.

**Authority:**
- Preauthorized local actions: add reusable deterministic validation mechanics, the NCC review specification, and focused tests; create disposable generated or copied workbooks under pytest temporary directories; run local workbook checks.
- Stop for: modifying or tracking the real workbook, adding an Excel formula engine, using analyst calculation functions as the independent oracle, treating a clean fixture as proof of actual analyst validation, or making external network calls.

**Steps:**
- [x] Step 1: Capture source SHA-256, sheet inventory, selected ranges, periods, units, category labels, and channel boundaries as sanitized evidence, using `include_hidden=True` and `include_hidden_rows=True` where supported.
- [x] Step 2: Reconstruct expected growth, shares, launch-survival ratios, and compounded thresholds directly from raw cell values. Record baseline period and period count explicitly; label threshold checks as planning math, not achieved performance.
- [x] Step 3: Keep offline and ecommerce calculations separate unless the review specification proves aligned definitions, periods, units, and denominators. Emit conditional results with named missing inputs for margin, capacity, distribution, or cannibalization gaps.
- [x] Step 4: Build typed reconciliation evidence with calculation ID, metric, source cells, expected, analyst actual, delta, tolerance, and status. The expected value must be computed before comparison and must not call the producer's calculation function.
- [x] Step 5: Add mutations to the persisted candidate result for wrong denominator, value/volume mix-up, and invalid category mapping; use a copied workbook only for changed source hash or changed cell/range tests. Ensure each failure identifies category, target, source inputs, and expected/actual values.
- [x] Step 6: Build the NCC review specification with typed categories, source-to-capability mappings, and source/channel comparability constraints without embedding generated `work/` output. Leave `decision_challenge` as `NOT_RUN` unless a separately authorized reviewer or human uses the trusted path.

**Verification:**
- [ ] Run `python -m pytest -q tests/test_local_toolbelt.py tests/test_ncc_independent_validation.py`.
- Expected: generated CI fixtures pass source/scope checks and independently reconstructed arithmetic; each planted mutation fails the intended check with a stable failure class; the real source remains unchanged and no workbook bytes enter tracked state.
- [ ] Confirm numeric checks compute expected values before comparing against any analyst result and do not call the analyst's calculation implementation.
- Expected: the test spy or independent implementation proves the validator does not reuse the producer's calculation function.

**Exit Criteria:**
- The repository has reusable, provider-free deterministic validation mechanics and NCC-specific rules with explicit provenance and planted-failure detections; strategic decision challenge remains separately evidenced.

### Task 4: Add the validation phase and aggregate all required coverage

**Purpose:**
- Enforce the verdict's ordered workflow and make human acceptance depend on complete, current, target-scoped review coverage.

**Task Function:**
- Review-phase orchestration and acceptance gate

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: this is the highest-risk shared behavior change because it crosses reviewer execution, persistence, invalidation, and human acceptance; resolve profile from current registry at activation.

**Validator Profile (optional):**
- Controller-selected: `unresolved while task is pending`
- Selection basis: select an independent validator able to exercise success, failure, state, and idempotency boundaries.

**Specification Coverage:**
- Provisional findings become accepted only after independent checks, discrepancy reconciliation, affected-finding recheck, and explicit human acceptance. Validator concurrency is optional; independence is about separate derivation, not separate file I/O. Group Chat disagreement cannot erase unresolved objections.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/domain/challenge.py:select_review_record`, `derive_finding_views`, `accepted_consequential_recommendation`, `src/foresight_os/analysis/reviewer.py:review_reasoning_with_skills`, `src/foresight_os/analysis/evidence_workflow.py:accept_pending_evidence`, `src/foresight_os/vertical_slice.py:run_vertical_slice`, and acceptance callers in `analysis/portfolio_resilience.py`, `analysis/powerbi_strategic_portfolio.py`, `analysis/supplier_resilience.py`, `analysis/ev_capacity_investment.py`, and `analysis/technology_radar.py`
- Modify: `src/foresight_os/domain/challenge.py` with aggregate coverage helpers and derived `FindingView` logic; `src/foresight_os/analysis/reviewer.py` with per-check execution; `src/foresight_os/analysis/review_workflow.py:accept_pending_analysis` with the coordinator and shared acceptance gate; `src/foresight_os/analysis/evidence_workflow.py` with the trusted review-phase adapter and recheck boundary; update `src/foresight_os/artifacts/report.py` and `src/foresight_os/artifacts/presentation.py` for per-category status. Do not modify `runtime/workflow.py` unless implementation proves typed review transport cannot use the existing seam; add it to targets before editing if that occurs.
- Verify: `tests/test_finding_view.py`, `tests/test_evidence_workflow.py`, `tests/test_review_hardening.py`, `tests/test_portfolio_resilience.py`, `tests/test_supplier_and_ev_resilience.py`, `tests/test_technology_powerbi_validator.py`

**Dependencies:**
- Tasks 1–3 provide review category policy, target-scoped record metadata, and independent check producers.
- Preserve existing `PENDING_REVIEW`, `ACCEPTED`, `REJECTED`, and stale-review semantics for workflows that do not declare the new typed categories. Keep `AnalysisStore` as persistence owner, not policy engine.

**Authority:**
- Preauthorized local actions: modify only the declared review, workflow, artifact, and focused test files; run temporary-store and generated-fixture boundary tests.
- Stop for: changing human acceptance into automatic acceptance, letting generic stage output bypass the trusted adapter, or changing unrelated execution patterns.

**Steps:**
- [x] Step 1: Replace final reliance on `select_review_record()` with deterministic `ReviewCoverage` aggregation that filters by target, typed category, slot, current material/dependency fingerprints, and recipe/policy identity. Retain the old selector only for compatibility paths.
- [x] Step 2: Distinguish coverage from outcome: missing required category is `PENDING_REVIEW`; a blocking source/arithmetic error is `REJECTED`; complete coverage with material non-blocking missing inputs is `PROVISIONAL`; complete coverage without material unresolved issues is eligible for automated review success.
- [x] Step 3: Add a review-phase coordinator that derives checks independently, optionally runs independent deterministic checks concurrently, persists each typed result through trusted `attach_review_record()`, and never routes review output through the normal stage-result committer.
- [x] Step 4: Add discrepancy handling that assigns corrections to the producer, preserves unresolved objections, invalidates only affected review slots, and reruns only affected categories after a new analysis revision. Retries supersede the exact slot; independent PASS/FAIL records remain a conflict until reconciled.
- [x] Step 5: Add one shared `accept_pending_analysis()` gate used by all named public human-acceptance workflows. It checks required coverage, currentness, blocking objections, recipe/policy identity, the specific `AnalysisState` revision, and the human decision before calling `AnalysisStore.commit_revision()`.
- [x] Step 6: Allow a human to accept the reviewed analytical package while individual recommendations remain provisional; keep `accepted_consequential_recommendation()` false when required feasibility inputs are missing. Group Chat may resolve interpretation but cannot delete or overwrite a required validator record.
- [x] Step 7: Render per-category results, limitations, missing inputs, conflicts, and human acceptance separately in reports and presentations. A probe exit code must never be described as recommendation acceptance.

**Verification:**
- [x] Run focused review and workflow tests listed above.
- Expected: a passing source review plus missing calculation coverage remains pending; a blocking calculation error is rejected; a passing calculation review cannot override an unresolved decision challenge; a stale workbook hash invalidates the affected workbook-dependent slots; a corrected producer result causes only affected slots to recheck before acceptance; a provisional package can be human-accepted without making a consequential recommendation decision-ready.
- [x] Exercise the direct backend boundary with accepted, pending, rejected, malformed-review, missing-input, stale-input, and duplicate-attempt cases.
- Expected: final `AnalysisStore` state, review records, revision status, and finding views match the declared outcome; no raw payload or secret is persisted; rerunning an identical attempt is idempotent.

**Exit Criteria:**
- Human acceptance is possible only through the shared gate after all required current review slots have coverage, policy/revision identities match, and no unresolved blocking objection remains. Coverage completion does not force every non-blocking finding to become decision-ready.

### Task 5: Integrate NCC recipe evidence, probe output, and maintained guidance

**Purpose:**
- Prove that the concrete NCC arrangement uses the new contract and leave one maintained explanation of the validation boundary.

**Task Function:**
- Case integration and evidence packaging

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: the task combines a bounded fixture, executable probe, and documentation reconciliation; resolve profile from current registry at activation.

**Validator Profile (optional):**
- Controller-selected: `unresolved while task is pending`
- Selection basis: independently inspect the probe receipt and compare it with the source workbook and review policy.

**Specification Coverage:**
- The NCC validation stage has workbook-read and calculation capabilities, the final challenge has explicit review skills, review checks are consumed rather than merely labeled, and the source-based verdict becomes runtime evidence only when it reconciles the actual persisted analysis.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/controller/policy.py:select_recipe`, `src/foresight_os/controller/skills.py:SkillRegistry`, the persisted NCC `AnalysisState` under the local analysis directory, and the external workbook path when available
- Add: `evaluation/probes/run_ncc_independent_validation.py`, `evaluation/cases/ncc-2022-cosluxe-vietnam/review-spec.json`, `tests/fixtures/ncc-independent-validation.xlsx`, `tests/test_ncc_recipe_and_probe.py`
- Modify: `docs/evidence-and-evaluation.md` with the maintained independent-validation workflow and evidence contract
- Verify: disposable output under `work/ncc-independent-validation-20261015/`; do not modify existing `work/` outputs or persist workbook bytes

**Dependencies:**
- Tasks 1–4 must pass before the NCC probe is treated as release evidence.
- Repository tests use a generated or sanitized fixture. Local NCC acceptance may use the real workbook only as an external local fixture, recording SHA-256, sheet names, ranges, metric IDs, expected/actual values, and statuses without committing workbook bytes. The probe must also load the actual persisted `AnalysisState`.

**Authority:**
- Preauthorized local actions: add the declared review specification, probe, focused tests, and documentation; execute the probe into a new disposable output directory.
- Stop for: editing or deleting existing `work/` artifacts, copying raw workbook bytes into tracked state, treating fixture-only checks as analyst validation, or calling external providers.

**Steps:**
- [x] Step 1: Encode the NCC stage's typed review categories, reviewer capability union, reviewer skill IDs, target scope, source/channel constraints, and conditional feasibility rules in the case review specification.
- [x] Step 2: Generate the approved recipe from the canonical Work Brief path and assert the reviewer role, typed stage review checks, policy version, capability IDs, skill IDs, dependencies, and review-required topology without adding validation fields to `WorkBrief`.
- [x] Step 3: Require `--workbook`, `--analysis-dir`, `--review-spec`, and `--output-root`. Load the persisted NCC state and bind the receipt to investigation ID, state revision, pending-state fingerprint, execution-recipe fingerprint, target record IDs, calculation IDs, and workbook SHA-256.
- [x] Step 4: Reconcile each calculation using raw-cell expectations against the persisted analyst result and emit typed expected/actual/delta/tolerance/source-input evidence. If the analysis snapshot is absent, return `BLOCKED_INPUT/NOT_VERIFIED`, never `PASS`.
- [x] Step 5: Keep deterministic source/scope/calculation checks separate from `decision_challenge`. Report `decision_challenge: NOT_RUN` and overall coverage as incomplete unless a separately authorized reviewer or human completes the challenge through the trusted path.
- [x] Step 6: Add probe assertions for wrong denominator, value/volume mix, invalid category mapping, changed source hash/range, missing persisted analysis, retry supersession, and one required validator failing while another passes.
- [x] Step 7: Update `docs/evidence-and-evaluation.md` to distinguish source fidelity, arithmetic reconciliation, decision support, automated review outcome, and human acceptance; document that the real workbook is an external local fixture and the 8% target is planning math, not observed performance.

**Verification:**
- [x] Run the probe against a generated CI fixture with `--workbook`, a persisted fixture analysis with `--analysis-dir`, the NCC `review-spec.json`, and a new `work/ncc-independent-validation-20261015/` output root.
- Expected: deterministic source hash, typed review categories, reviewer capabilities and skills present, no unsupported cross-channel comparison, explicit conditional missing-input treatment, actual-vs-expected reconciliation, and `decision_challenge: NOT_RUN` unless separately authorized.
- [x] Run the same probe locally against `data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx` with the available persisted NCC snapshot; record a sanitized receipt and never copy the workbook into Git. The run is retained as a failed compatibility check because the workbook does not contain the declared `Offline` scope.
- Expected: missing workbook or analysis, and incompatible source scope, produce a non-accepting result rather than a false PASS or acceptance claim. The revised actual-workbook run passes source fidelity and scope reconciliation, while retaining `decision_challenge: NOT_RUN` and `human_acceptance: NOT_RUN` in `work/ncc-independent-validation-20261015/real-v2/receipt.json`.
- [x] Run the same probe's mutation matrix or its focused test entry point.
- Expected: wrong denominator, value/volume mix, invalid category mapping, changed hash, and one unresolved required validator each fail with a stable status and no false acceptance.

**Exit Criteria:**
- The NCC case has durable, reproducible runtime evidence that reconciles actual persisted analyst output with an external workbook, preserves decision-challenge limits, and does not mistake fixture-only validation for an accepted strategic conclusion.

### Task 6: Complete repository verification and reconcile the plan ledger

**Purpose:**
- Establish fresh repository-wide proof without changing preserved workspace outputs or claiming completion from checked boxes alone.

**Task Function:**
- Final verification and evidence reconciliation

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: final verification requires repository-wide evidence and current plan/Git reconciliation; resolve profile from current registry at activation.

**Validator Profile (optional):**
- Controller-selected: `unresolved while task is pending`
- Selection basis: `skill-verification-before-completion` owns the independent completion gate.

**Specification Coverage:**
- Required project verification commands, direct backend proof, deterministic fixtures, hashes, persistence, invalidation, retry/conflict behavior, concurrent merge safety, receipt reuse where affected, and documentation links are fresh and truthful.

**Required Skills:**
- `skill-verification-before-completion`, `skill-plan-document-reviewer`

**Files And Symbols:**
- Inspect: all changed files and the task ledger in this plan
- Modify: this plan only for accepted evidence, deviations, blockers, and final status; never mark it `completed` before a fresh `verified` result
- Verify: repository status, diff, focused tests, full tests, compileall, NCC probe, and Markdown links if documentation paths changed

**Dependencies:**
- Tasks 1–5 complete with accepted task-local proof.
- Existing untracked outputs remain preserved and are not evidence of new work unless the probe explicitly writes a new named output.

**Authority:**
- Preauthorized local actions: run the declared verification commands, inspect diffs/status, update this plan's ledger and evidence fields, and write only new disposable probe output.
- Stop for: push, merge, publication, cleanup of preserved outputs, or a completion claim when any required check is failed, blocked, stale, or unrecorded. A blocked real-workbook probe is not a passing acceptance result.

**Steps:**
- [x] Step 1: Run focused tests for typed recipe policy, approval fingerprints, schema migration, persistence, retries/conflicts, concurrent attachments, deterministic validation, and shared acceptance.
- [x] Step 2: Run `python -m pytest -q` and `python -m compileall -q src tests evaluation`.
- [x] Step 3: Run the NCC probe against the generated fixture and persisted analysis snapshot; when the external workbook and real analysis are available, run the local NCC probe with `--analysis-dir` and inspect sanitized receipts.
- [x] Step 4: Confirm fresh-process reload preserves both concurrent `ReviewRecord`s, slot supersession history, pending tokens, and coverage state; confirm no record is lost or duplicated at the existing lock/merge/atomic-write boundary.
- [x] Step 5: Run `git diff --check` and inspect `git status --short --branch`; confirm only declared tracked files changed, the target base is reconciled, and all prior untracked outputs remain untouched.
- [x] Step 6: Run `python scripts/check_markdown_links.py README.md docs/README.md docs/getting-started.md docs/architecture.md docs/skills.md docs/evidence-and-evaluation.md docs/configuration.md docs/extending.md --tracked-docs` and `python -m pytest -q tests/test_markdown_links.py`.
- [x] Step 7: Apply `skill-verification-before-completion`; fresh repository-wide evidence returned `verified` after the approved source-scope revision.

**Verification:**
- [x] `python -m pytest -q`
- [x] `python -m compileall -q src tests evaluation`
- [x] `python evaluation/probes/run_ncc_independent_validation.py --workbook tests/fixtures/ncc-independent-validation.xlsx --analysis-dir work/ncc-independent-validation-20261015/fixture-analysis --review-spec tests/fixtures/ncc-independent-validation-review-spec.json --output-root work/ncc-independent-validation-20261015/final`
- [x] `python evaluation/probes/run_ncc_independent_validation.py --workbook "data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx" --analysis-dir work/ncc-2022-cosluxe-vietnam --review-spec evaluation/cases/ncc-2022-cosluxe-vietnam/review-spec.json --output-root work/ncc-independent-validation-20261015/real-v2` — exits `0` and records `NOT_VERIFIED` with source, scope, and selected arithmetic checks passing; decision challenge and human acceptance remain `NOT_RUN`.
- [x] `git diff --check`
- Expected: all required repository and generated-fixture commands exit `0`; the final verifier reports `verified`; no unresolved task, stale plan state, failed required proof, or scope deviation remains. The real local NCC probe is recorded separately as `VERIFIED` only when both external inputs exist; otherwise it is truthfully `BLOCKED_INPUT/NOT_VERIFIED`.

Fresh verification result: `verified`. The approved revision aligns the case specification with the external workbook, and the rerun at `work/ncc-independent-validation-20261015/real-v2/receipt.json` passes deterministic source, scope, and selected raw-cell calculation checks. The fixture rerun at `work/ncc-independent-validation-20261015/final-v2/receipt.json` also passes. Both receipts correctly retain `decision_challenge: NOT_RUN` and `human_acceptance: NOT_RUN`; those are separate acceptance phases, not failures of this implementation task.

**Exit Criteria:**
- The plan ledger, changed source, tests, documentation, and fresh verification receipts agree. Only then may the lead controller update plan status or pursue separately authorized Git disposition.

## Verification

Final artifact-level verification is owned by `skill-verification-before-completion` after task-local proof passes:

- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `python evaluation/probes/run_ncc_independent_validation.py --workbook tests/fixtures/ncc-independent-validation.xlsx --analysis-dir work/ncc-independent-validation-20261015/fixture-analysis --review-spec tests/fixtures/ncc-independent-validation-review-spec.json --output-root work/ncc-independent-validation-20261015/final-v2`
- `python evaluation/probes/run_ncc_independent_validation.py --workbook "data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx" --analysis-dir work/ncc-2022-cosluxe-vietnam --review-spec evaluation/cases/ncc-2022-cosluxe-vietnam/review-spec.json --output-root work/ncc-independent-validation-20261015/real-v2`
- `python scripts/check_markdown_links.py README.md docs/README.md docs/getting-started.md docs/architecture.md docs/skills.md docs/evidence-and-evaluation.md docs/configuration.md docs/extending.md --tracked-docs`
- `python -m pytest -q tests/test_markdown_links.py`
- `git diff --check`
- `git status --short --branch`, confirming existing untracked outputs remain untouched and only declared tracked files are in scope

The final verifier must return `verified` before this plan changes from
`active` to `completed`.

Current verifier disposition: `verified`. The source scope is aligned to the
actual workbook, all required local checks pass, and no human acceptance or
decision-challenge result is being represented as completed by the probe.

## Completion Criteria

The plan is ready for completion verification when:

1. The approved `ExecutionRecipe` and `ReviewPolicy` declare and enforce the four typed review categories with distinct reviewer capabilities and skills; `WorkBrief` remains free of system-derived review requirements.
2. Review records are target-scoped and include trusted reviewer, execution, attempt, method, source/dependency fingerprints, typed reconciliation evidence, policy identity, slot, and skill identity.
3. Legacy review records remain readable but cannot satisfy newly declared review coverage.
4. Independent NCC checks load actual persisted analysis, derive expected arithmetic from raw cells before comparison, and preserve workbook hash, sheet, period, unit, mapping, range, and channel provenance without tracking workbook bytes.
5. The system detects wrong denominators, value/volume mix-ups, invalid category mappings, changed workbook hashes, and incomplete review coverage.
6. Aggregate `ReviewCoverage` and `FindingView`s keep every required validator's unresolved objection or conflict visible; Group Chat consensus cannot erase it.
7. Corrections invalidate and recheck only affected findings before human acceptance.
8. Missing feasibility inputs produce conditional recommendations, and reports distinguish source fidelity, arithmetic, decision support, and human acceptance.
9. Direct backend success/failure, final state, idempotency, persistence, retry/supersession, conflict, concurrent merge, invalidation, receipt reuse where affected, and sanitized-receipt proof pass on fresh runs.
10. `skill-verification-before-completion` returns `verified`; only then may the lead controller update plan status or perform separately authorized Git disposition.
