---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: foresight-wayfinding-boundary
targets:
  - .agents/skills/foresight-wayfinding/SKILL.md
  - AGENTS.md
  - src/foresight_os/domain/models.py
  - src/foresight_os/domain/approval.py
  - src/foresight_os/domain/validation.py
  - src/foresight_os/schemas/work_brief.schema.json
  - src/foresight_os/wayfinding.py
  - src/foresight_os/persistence/analysis_store.py
  - src/foresight_os/artifacts/brief.py
  - src/foresight_os/artifacts/approval.py
  - src/foresight_os/cli.py
  - tests/test_wayfinding.py
  - tests/test_persistence.py
  - tests/test_approval_package.py
  - tests/test_cli.py
  - tests/test_host_wayfinding_routing.py
  - tests/test_ncc_wayfinding.py
  - tests/fixtures/wayfinding/ncc-2022-brief.yaml
  - docs/templates/work-brief-template.md
  - docs/templates/approval-package-example.md
  - work/ncc-2022-cosluxe-vietnam/brief.md
  - docs/architecture.md
  - docs/getting-started.md
  - docs/extending.md
  - docs/superpowers/plans/2026-10-14-2127-foresight-wayfinding-boundary-plan.md
---

# ForesightOS Strategic Wayfinding Boundary

## Goal

Implement the bounded correction recommended by the supplied verdict without
reopening the canonical architecture delivered in PR #12:

```text
repository host routing
  -> foresight-wayfinding
  -> typed WorkBrief with method provenance
  -> derived human-readable brief.md
  -> Controller-generated ExecutionRecipe
  -> complete ApprovalPackage
  -> human review before execution
```

The change must preserve the existing YAML-frontmatter `brief.md` load and
round-trip contract, keep `wayfinding.py` as the typed domain owner, and keep
the Controller as the owner of execution topology and capability resolution.
It must not register the host-facing procedure as a second packaged runtime
skill, create a second analytical store, make `map.md` canonical, or change
pause/cancel behavior across processes.

## Verdict Review

The verdict is accepted with these implementation constraints:

1. The repository has no tracked `.agents/` directory today. This change
   establishes `.agents/skills/` as a new repository-local host-procedure
   convention; it is not treated as an already guaranteed runtime surface.
2. The root `AGENTS.md` is the only tracked source for the repository contract;
   no tracked generator or alternate canonical source exists. The routing rule
   is therefore added there without creating a second instruction surface.
3. `src/foresight_os/skills/manifest.json` remains limited to participant/runtime
   methods. `foresight-wayfinding` is host-facing and is not added to that
   registry in this change.
4. `AnalysisStore.save_brief()` remains the durable structured owner. Its YAML
   front matter stays compatible while its visibly generated Markdown body
   becomes a useful strategic review view. A human-only CLI/API render avoids
   forcing readers to consume machine front matter.
5. Inferred dependencies, capabilities, and topology remain structural inputs
   or Controller decisions. Only explicit human constraints enter required
   execution intent.
6. The NCC workbook is an XLSX source boundary: `Case`, `Glossary`, and other
   relevant sheets are represented as structured-data research needs, with
   exact sheet identifiers and explicit inclusion/exclusion decisions.
7. Producer provenance is caller-supplied descriptive metadata. The Python
   domain layer never reads or hashes `.agents/...`, and producer metadata is
   excluded from material approval fingerprints.

## Implementation Outcomes

### Unambiguous strategic intake

ForesightOS has a uniquely named host procedure at
`.agents/skills/foresight-wayfinding/SKILL.md`, and `AGENTS.md` routes strategic
intake, WorkBrief creation, and WorkBrief refinement to it instead of generic
Wayfinding, specification drafting, or implementation planning.

### Provenance-safe, reviewable WorkBrief

`WorkBrief` can carry non-authenticating producer/method provenance, preserves
legacy brief compatibility, and renders material decision context, scope,
assumptions, unknowns, evidence boundary, stages, deliverables, direction,
and next step as derived Markdown in `brief.md`.

### Complete approval projection

The approval Markdown exposes the strategic assumptions and open dependencies
alongside explicit user-required intent and the resolved execution details:
skills, rationale, capabilities, access scope, participants, provider/model,
limits, review rules, reuse decisions, and adaptation envelope.

### Correct NCC intake semantics

The NCC intake example can be regenerated without treating inferred Sequential
execution, inferred stage topology, or Wayfinding-selected capabilities as
human requirements; its growth bridge is conditional and its workbook source
hints use exact identifiers. `map.md` is not required for canonical intake; an
optional derived artifact is named `decision-map.md` if a later surface needs
one.

### Regression and documentation proof

Focused tests cover routing collision, producer provenance, brief save/load
round trips, renderer material-field coverage, approval-field coverage, and
required-versus-preferred intent semantics. Maintained architecture and usage
guidance describe the same ownership boundaries without duplicating runtime
contracts.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Required skills: `skill-writing-skills`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit only the declared plan targets, inspect current source and preserved untracked artifacts, record baseline state, run local tests/compilation/link checks, and preserve all unrelated untracked outputs
- User-approval actions: external provider calls, publication, push/merge, destructive cleanup, or modification/deletion of unrelated untracked artifacts
- Parallel ownership: `none; the renderer, model, persistence, approval, fixture, and routing changes share contract dependencies`
- Sequential fallback: complete host routing, then model/validation/persistence, then renderers, then NCC/documentation reconciliation, then final verification

## Task Breakdown

### Task 1: Establish the host-facing wayfinding owner and routing

**Purpose:**
- Create one uniquely named repository-local host procedure and make strategic intake resolve to it without registering a duplicate runtime skill.

**Task Function:**
- Define host navigation and enforce the boundary between strategic clarification and execution.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded documentation/skill authoring with low implementation risk and no delegation benefit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: static routing assertions and the final documentation/link checks provide focused proof.

**Specification Coverage:**
- Verdict sections 1–6: uniquely named `foresight-wayfinding`, explicit repository routing, thin coordination around existing contracts, and no runtime registry duplication.
- New boundary decision: `.agents/skills/` is the repository-local host-procedure boundary; `src/foresight_os/skills/` remains the packaged participant/runtime analytical-skill boundary.

**Required Skills:**
- `skill-writing-skills`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `AGENTS.md`, `src/foresight_os/wayfinding.py:create_work_brief`, `src/foresight_os/controller/proposal.py:build_execution_recipe`, `src/foresight_os/controller/skills.py:SkillRegistry`
- Modify: `.agents/skills/foresight-wayfinding/SKILL.md`, `AGENTS.md`
- Verify: `tests/test_host_wayfinding_routing.py`, `src/foresight_os/skills/manifest.json`

**Dependencies:**
- The verdict review above and the existing canonical owner table.
- No tracked generator/source exists for the generated-file header in `AGENTS.md`; preserve the current contract and add only the routing rule plus the new host-boundary convention.

**Authority:**
- Preauthorized local actions: create the declared host skill, update the concise routing section in `AGENTS.md`, add focused static tests, and run local checks.
- Stop for: any request to register the host skill in the packaged runtime manifest, edit shared/global skills, or replace the repository contract with a second source.

**Steps:**
- [x] Step 0: Before implementation, record `git rev-parse HEAD`, `git status --short --untracked-files=all`, and the list of unrelated untracked artifacts; do not use a stale verdict SHA as the baseline.
- [x] Step 1: Create `.agents/skills/foresight-wayfinding/SKILL.md` with the strategic clarification, bounded source inspection, WorkBrief creation/refinement, Controller proposal, review-package, and human-approval stopping rules.
- [x] Step 2: State explicitly that required patterns, participants, capabilities, and reasoning controls are only recorded when supplied as human constraints; observations become research needs or Controller inputs.
- [x] Step 3: Add the repository routing rule to `AGENTS.md`, including the stop condition that Wayfinding ends at a reviewable WorkBrief and proposal.
- [x] Step 4: Add static routing/collision checks that require the unique ID and exact route, forbid a runtime-manifest registration, and verify canonical code paths do not depend on `map.md`; assert contract boundaries rather than exact prose.

**Verification:**
- [x] Read the new skill and routing section; expected: every named owner points to an existing canonical module or declared host path.
- [x] Run `python -m pytest -q tests/test_host_wayfinding_routing.py`; expected: the repository route is unambiguous and the runtime manifest is unchanged by this task.
- [x] Host/client discovery probe disposition: `not_measured`; this host session exposes no observable selected-skill path/hash surface, so no host-selection verification is claimed.

**Exit Criteria:**
- A repository-aware agent has one explicit host-facing route for strategic WorkBrief intake, with no duplicate runtime skill or map-based promotion requirement; static routing proof is separate from host-selection proof.

### Task 2: Add method provenance and preserve intent semantics

**Purpose:**
- Make the producer of a WorkBrief observable as method provenance while ensuring Wayfinding recommendations cannot silently become required execution constraints.

**Task Function:**
- Extend the typed brief contract and its compatibility normalization without changing Controller ownership of executable topology.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: schema/persistence work is contract-sensitive but bounded to existing WorkBrief owners.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused round-trip and validation tests exercise the changed contract directly.

**Specification Coverage:**
- Verdict sections 6 and 12–13: add a small non-authenticating producer block; distinguish required human intent, preferred intent, structural observations, research needs, and Controller resolution.
- Preserve legacy `execution_pattern_override` translation and existing brief readers.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/domain/models.py:WorkBrief`, `ExecutionIntent`, `src/foresight_os/wayfinding.py:create_work_brief`, `refine_work_brief`, `src/foresight_os/domain/validation.py:_normalize_work_brief`, `_normalize_execution_intent`
- Modify: `src/foresight_os/domain/models.py:WorkBrief` and new typed provenance value, `src/foresight_os/wayfinding.py:create_work_brief`/`refine_work_brief`, `src/foresight_os/domain/validation.py`, `src/foresight_os/schemas/work_brief.schema.json`, `src/foresight_os/persistence/analysis_store.py:load_brief`, `src/foresight_os/domain/approval.py:ApprovalProjection.from_values`
- Verify: `tests/test_wayfinding.py`, `tests/test_persistence.py`, `tests/test_analysis_schema.py`, `tests/test_controller_selection.py`, `tests/test_approval_contract.py`

**Dependencies:**
- Task 1 defines the producer ID and host procedure contract.
- Existing `ExecutionIntent.source` and legacy normalization remain authoritative for compatibility.

**Authority:**
- Preauthorized local actions: extend the existing WorkBrief model/schema/normalization/load path, add focused regression tests, and run local boundary checks.
- Stop for: a second brief store, authenticated identity claims, changing Controller recipe-selection policy, or removing legacy brief compatibility.

**Steps:**
- [x] Step 1: Add a small typed producer/method provenance value with `id`, `source`, `contract_version`, and optional content hash; treat it as descriptive provenance, not authorization. The caller supplies it; `wayfinding.py` must never open, read, or hash `.agents/...`.
- [x] Step 2: Add an optional `WorkBrief.producer` field with absent-value compatibility; normalize and reconstruct it through validation and `AnalysisStore.load_brief()` and include it in the schema and canonical serialization.
- [x] Step 3: Define approval semantics explicitly: retain the descriptive `producer` block for supplementary display, but compute `ApprovalProjection.fingerprint` from a shared material-projection canonicalizer that removes only `brief.producer`; update `validate_approval_record()` to use the same canonicalizer so persistence and runtime admission agree.
- [x] Step 4: Keep `refine_work_brief()` explicit: required fields are caller-supplied constraints, preferred fields are preferences, and omitted topology/capability fields stay omitted rather than inferred into required intent.
- [x] Step 5: Add tests proving producer round-trip, legacy brief round-trip, preferred-only intent has no required pattern/capability, explicit human-required intent is retained exactly, producer-only changes leave the approval material fingerprint unchanged, scope/required-intent changes alter it, and persisted approval validation uses the same result.

**Verification:**
- [x] Run `python -m pytest -q tests/test_wayfinding.py tests/test_persistence.py tests/test_analysis_schema.py tests/test_controller_selection.py`; expected: all existing and new WorkBrief tests pass.
- [x] Inspect serialized front matter; expected: producer is present only when supplied, required/preferred fields retain their meaning, and legacy overrides still load.
- [x] Build approval projections with and without producer metadata; expected: producer remains descriptive/supplementary, producer-only changes do not change the material fingerprint, and canonical decision or required-intent changes do.

**Exit Criteria:**
- WorkBrief provenance is caller-supplied, portable, durable, and non-authoritative; it is excluded from approval material hashing; intent semantics are explicit; and no inferred Wayfinding choice is promoted to a required execution constraint.

### Task 3: Render a real human-readable WorkBrief while retaining front matter

**Purpose:**
- Turn `brief.md` into a reviewable strategic brief without changing its canonical structured persistence contract.

**Task Function:**
- Build a deterministic derived Markdown view from validated WorkBrief fields and integrate it into atomic brief persistence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: one new pure renderer plus one existing persistence integration; deterministic and reversible.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: renderer snapshots/assertions and save/load round-trip tests provide direct proof.

**Specification Coverage:**
- Verdict sections 8–10: YAML front matter remains canonical; Markdown body contains decision, context, scope, evidence, assumptions, stages, deliverables, direction, and next step; the body is visibly generated; arbitrary body edits never change execution semantics; a human-only render surface is available without another persisted file.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/persistence/analysis_store.py:save_brief`, `load_brief`, `src/foresight_os/domain/validation.py:validate_work_brief`
- Modify: `src/foresight_os/artifacts/brief.py:render_work_brief_markdown` (new), `src/foresight_os/persistence/analysis_store.py:save_brief`, `src/foresight_os/cli.py:build_parser`/`main`
- Verify: `tests/test_persistence.py`, `tests/test_wayfinding.py`, `tests/test_cli.py`, `docs/templates/work-brief-template.md`

**Dependencies:**
- Task 2 supplies the final WorkBrief serialization/provenance shape.
- The existing YAML-frontmatter parser remains the only load source; the body is derived output.

**Authority:**
- Preauthorized local actions: add the pure renderer, integrate it into `save_brief()`, update focused tests/template guidance, and run local persistence checks.
- Stop for: splitting persistence into `work-brief.json`, parsing human-edited Markdown as authority, or changing approval fingerprints to ignore canonical structured fields.

**Steps:**
- [x] Step 1: Implement stable section ordering and escaping for decision, context, scope, evidence/research needs, assumptions, open dependencies, proposed investigation stages, deliverables, current direction, and next step.
- [x] Step 2: Keep front matter generated from `validate_work_brief()` and append only the derived body returned by the renderer; add a visible generated-view warning instructing readers to revise the WorkBrief rather than edit the rendered body.
- [x] Step 3: Ensure empty collections render as “not specified” when unknown and “none declared” only when explicit absence is known; ensure research-need source hints remain visible.
- [x] Step 4: Add the exact human-only `foresight-os brief --work-dir ...` CLI command that loads the canonical WorkBrief and prints only the generated human body without creating another file.
- [x] Step 5: Add contract assertions for material fields and a save/load test proving body edits cannot alter the loaded WorkBrief, recipe, or approval material fingerprint.

**Verification:**
- [x] Run `python -m pytest -q tests/test_persistence.py tests/test_wayfinding.py`; expected: saved `brief.md` has valid front matter plus readable Markdown sections and round-trips semantically.
- [x] Run `python -m pytest -q tests/test_cli.py`; expected: the human-only brief render prints the generated body and does not create a second persisted state file.
- [x] Run a focused renderer assertion; expected: no sensitive provider credentials or raw provider payloads appear in the rendered body.

**Exit Criteria:**
- Opening `brief.md` gives a strategist a useful generated review document, the human-only render is available without front matter, and the structured front matter remains the sole durable WorkBrief contract.

### Task 4: Complete the approval Markdown projection

**Purpose:**
- Make the final review artifact complete enough to approve the exact investigation without consulting hidden JSON fields or unrelated files.

**Task Function:**
- Extend the existing derived approval renderer; do not create another approval store or alter approval admission semantics.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: focused view-layer change over existing `ApprovalProjection` and `ExecutionRecipe` data.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: existing renderer tests plus new field assertions cover both primary and detailed output.

**Specification Coverage:**
- Verdict section 11: assumptions, unknowns, user-required constraints, selected skills and rationale, capabilities/tools, access scope, participants/responsibilities, models/profiles, limits, review rules, reuse decisions, and adaptation envelope.
- Render only values captured by the approved WorkBrief/ExecutionRecipe/AdaptationEnvelope projection; do not consult mutable runtime registry defaults or invent unresolved values. Preserve approval fingerprint, JSON projection, and execution gate behavior.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/artifacts/approval.py:render_approval_markdown`, `src/foresight_os/domain/approval.py:ApprovalProjection`, `src/foresight_os/controller/recipes.py:ExecutionRecipe`/`RecipeStage`
- Modify: `src/foresight_os/artifacts/approval.py:render_approval_markdown`
- Verify: `tests/test_approval_package.py`, `tests/test_approval_contract.py`, `tests/test_execution_gate.py`, `docs/templates/approval-package-example.md`

**Dependencies:**
- Task 2 supplies producer and intent fields; Task 3 establishes the strategic brief vocabulary.
- Existing `ApprovalProjection` and `ApprovalRecord` remain canonical.

**Authority:**
- Preauthorized local actions: add deterministic Markdown sections/lines and focused renderer tests without changing projection shape or approval admission.
- Stop for: storing a second approval artifact, changing the projection fingerprint inputs, or treating rendered text as approval.

**Steps:**
- [x] Step 1: Add a decision-context section for assumptions, open dependencies, producer provenance as supplementary metadata, and required/preferred intent.
- [x] Step 2: Expand detailed stage output to include only captured skill IDs, stage rationale, capabilities, access scope, participants and responsibilities, limits, review checks, completion/escalation/partial-result rules, provider, model, and reasoning controls; expose captured recipe-level budgets, partial-result policy, review policy, and adaptation policy in the summary.
- [x] Step 3: Use `not specified` or `unavailable` for unresolved captured values and never resolve current registry output contracts, versions, hashes, defaults, tool bindings, or permissions merely to enrich the view.
- [x] Step 4: Keep reuse candidates and adaptation envelope visible and preserve deterministic ordering/escaping.
- [x] Step 5: Update example documentation and add contract assertions for every material field named by the verdict without asserting exact prose.

**Verification:**
- [x] Run `python -m pytest -q tests/test_approval_package.py tests/test_approval_contract.py tests/test_execution_gate.py`; expected: renderer coverage passes, only approved captured fields are rendered, and approval fingerprints/admission behavior remain unchanged.

**Exit Criteria:**
- The Markdown approval package contains both strategic framing and exact resolved execution details required for informed human approval.

### Task 5: Reconcile NCC intake semantics and deprecate generic map canonicality

**Purpose:**
- Apply the verdict’s semantic corrections to the NCC intake path and ensure the canonical process does not require the existing generic `map.md` artifact.

**Task Function:**
- Convert source observations into research needs and conditional deliverables while preserving the workbook evidence boundary.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: bounded intake/documentation reconciliation; no new execution engine or data adapter is needed.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused WorkBrief fixture assertions and source-hint inspection are sufficient.

**Specification Coverage:**
- Verdict sections 7, 12–16: no default `map.md`, exact XLSX source hints, explicit workbook sheet inventory, conditional growth bridge, interacting category/channel questions, and research-needs-first capability resolution.
- Preserve genuine investigation dependencies while removing only inferred execution-pattern mandates and unsupported capability requirements.
- Treat corrections to canonical NCC front matter as a real WorkBrief revision that makes any old recipe/approval stale through the existing fingerprint/reproposal mechanism.
- Keep cross-process pause/cancel deferred.

**Required Skills:**
- `spreadsheets:Spreadsheets`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `work/ncc-2022-cosluxe-vietnam/brief.md`, `docs/superpowers/plans/wayfinding/2026-10-14-1900-ncc-cosluxe-vietnam/map.md`, and `data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx`
- Modify: `tests/fixtures/wayfinding/ncc-2022-brief.yaml`, `tests/test_ncc_wayfinding.py`, `work/ncc-2022-cosluxe-vietnam/brief.md` only as a regenerated derived artifact update after the typed contract is ready, and `docs/architecture.md`, `docs/getting-started.md`, `docs/extending.md`
- Verify: fixture-to-brief-to-recipe-to-approval round trip; confirm no runtime code requires `map.md`

**Dependencies:**
- Tasks 1–4 complete so the corrected brief can be rendered and reviewed through canonical owners.
- Preserve the workbook and all unrelated untracked `work/`, `data/`, and `build/` artifacts.

**Authority:**
- Preauthorized local actions: inspect the NCC workbook and existing derived artifacts, update only the declared NCC brief and maintained docs, add focused semantic assertions, and run local checks.
- Stop for: changing source workbook contents, importing hindsight external research, making category/channel answers before execution, or deleting the existing untracked map/artifacts.

**Steps:**
- [x] Step 1: Inventory visible and hidden sheets, including `Macro & FMCG` and `Others`, and explicitly mark each as included or excluded for the first pass.
- [x] Step 2: Add a tracked sanitized canonical fixture at `tests/fixtures/wayfinding/ncc-2022-brief.yaml` with exact sheet identifiers such as `Trad.Trade`; represent `Case` and `Glossary` as structured-data/source-inspection needs rather than `DOCUMENT_REVIEW` or hard-coded capabilities.
- [x] Step 3: Preserve the investigation graph: `source-audit` precedes `category-screen` and `channel-screen`; both feed `joint-validation`; `challenge/synthesis` follows joint validation. Remove inferred `required_patterns` and unsupported required capabilities while retaining these genuine `WorkStage.dependencies`.
- [x] Step 4: Rewrite the growth deliverable as a conditional bridge and use research needs for capability resolution; do not force global Sequential or a required Concurrent pattern.
- [x] Step 5: Test the fixture through validation, WorkBrief construction, `save_brief()`, `load_brief()`, human rendering, `build_execution_recipe()`, and `render_approval_markdown()`; assert contract properties rather than exact prose.
- [x] Step 6: Regenerate `work/ncc-2022-cosluxe-vietnam/brief.md` from the typed fixture/API route and document `brief.md` as canonical intake with `decision-map.md` as optional derived output; do not generate or require generic `map.md`.
- [x] Step 7: If an old NCC recipe or approval exists, prove the corrected canonical brief causes the existing stale-fingerprint/reproposal path rather than retaining approval for the old front matter.

**Verification:**
- [x] Inspect the regenerated NCC `brief.md`; expected: exact source hints, conditional growth language, no inferred required topology/capability, explicit unknowns, and preserved genuine stage dependencies.
- [x] Run `python -m pytest -q tests/test_ncc_wayfinding.py`; expected: the tracked fixture completes the typed brief/renderer/recipe/approval path without reading or promoting `map.md`.
- [x] Change a material NCC front-matter field against an old proposal; expected: the existing fingerprint/reproposal mechanism marks old execution state stale and requires fresh approval.

**Exit Criteria:**
- NCC intake is reproducible from tracked sanitized data, truthful about what is known and what must be learned, preserves real stage dependencies, lets the Controller resolve execution, and treats generic Wayfinding `map.md` as unnecessary state.

### Task 6: Reconcile maintained documentation and run final verification

**Purpose:**
- Align maintained guidance with the implemented ownership boundaries and produce fresh repository-level proof.

**Task Function:**
- Audit cross-surface consistency and verify the final artifact without claiming external delivery.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final source/test/doc consistency check with no delegation benefit.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the final verification skill owns fresh completion evidence.

**Specification Coverage:**
- Project contract canonical owners and verification requirements.
- Verdict’s consolidated boundary: host skill → WorkBrief → Controller → readable brief/approval → human approval.
- Existing maintained templates must be updated deliberately rather than treated as hypothetical; lifecycle state must move `proposed → active → completed` only after fresh verification.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: all declared plan targets and `git diff --check`
- Modify: `docs/architecture.md`, `docs/getting-started.md`, `docs/extending.md`, `docs/templates/work-brief-template.md`, and `docs/templates/approval-package-example.md` only where needed to align with the implemented contract
- Verify: `tests/`, `src/`, `evaluation/`, and Markdown links

**Dependencies:**
- Tasks 1–5 complete with no unresolved contract deviation.

**Authority:**
- Preauthorized local actions: run the declared repository checks, fix only documentation/link inconsistencies caused by this plan, and inspect the final diff while preserving unrelated untracked artifacts.
- Stop for: failed required checks that imply a new scope, external delivery claims, destructive cleanup, or changes to deferred pause/cancel behavior.

**Steps:**
- [x] Step 1: Re-read the changed source, tests, skill, templates, and docs as one ownership graph; remove duplicated or contradictory guidance and regenerate the approval example from actual renderer output where practical.
- [x] Step 2: Run focused tests first, then the full repository test suite and compile check.
- [x] Step 3: Run the Markdown-link checker over changed maintained docs and inspect `git diff --check`.
- [x] Step 4: Record any failure as `FAILED`, `BLOCKED_INPUT`, or `BLOCKED_EXTERNAL` rather than weakening the contract. When implementation begins, transition the plan to `active`; mark it `completed` only after fresh final verification.
- [x] Step 5: Record host-selection evidence separately from static routing evidence: `VERIFIED` only with an observable host-session probe, otherwise `not_measured`.

**Verification:**
- [x] `python -m pytest -q`
- [x] `python -m compileall -q src tests evaluation`
- [x] `python scripts/check_markdown_links.py AGENTS.md README.md --tracked-docs` (the checker accepts explicit files or `--tracked-docs`, not the `docs` directory as a positional path)
- [x] `git diff --check`
- Expected: all required checks pass, links resolve, only declared source/docs/tests are changed, and unrelated untracked artifacts remain untouched.

**Exit Criteria:**
- The implementation can proceed from this plan without inventing owners, schemas, task boundaries, or proof; final verification commands are runnable and all deferrals are explicit.

## Verification

Current final evidence: full repository tests, compile checks, Markdown-link
checks, and diff hygiene pass on the active working tree. Static host routing is
`VERIFIED` through `tests/test_host_wayfinding_routing.py`; actual host-session
selection is `not_measured` because no observable host selection surface is
available in this session. Cross-process pause/cancel remains deferred.

Use these artifact-level checks after implementation, in addition to each task’s
focused proof:

- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `python scripts/check_markdown_links.py AGENTS.md README.md --tracked-docs`
- `git diff --check`
- Run the tracked NCC fixture through validation, save/load, human rendering, recipe construction, approval rendering, and stale-proposal proof.
- Inspect `brief.md` front matter/body and the rendered approval Markdown for the NCC fixture and regenerated work directory.
- Confirm `wayfinding.py` can create/refine a brief when `.agents/` is absent and that caller-supplied provenance is the only host-method input.
- Confirm changing producer metadata alone leaves the approval material fingerprint unchanged, while changing scope or required intent changes it.
- Confirm approval rendering is regenerated from canonical WorkBrief + exact recipe and does not consult mutable current registry defaults.
- Confirm `src/foresight_os/skills/manifest.json` has no `foresight-wayfinding` entry and no code path requires generic `map.md`.

## Completion Criteria

The plan is ready for completion verification when:

1. Tasks 1–6 have task-local proof and no unresolved required dependency.
2. Host routing is statically `VERIFIED`; actual host selection is `VERIFIED` only with a host-session probe and otherwise recorded as `not_measured`.
3. `wayfinding.py` remains portable without `.agents/`; host-provided producer provenance round-trips without authority and is excluded from approval material hashing.
4. Host routing, WorkBrief provenance, brief rendering, approval rendering, and NCC semantic corrections agree with the verdict and project contract.
5. YAML-frontmatter persistence, legacy brief loading, genuine WorkStage dependencies, approval fingerprints, stale-proposal invalidation, and execution admission remain compatible.
6. The generated human-readable brief and approval package contain the material captured fields needed for review and clearly distinguish unknown/unavailable values.
7. NCC is reproducible from tracked sanitized fixture data, and the real work-dir brief is regenerated through typed APIs rather than hand-maintained.
8. No generic map, runtime skill duplicate, second analytical store, or cross-process pause/cancel behavior was introduced.
9. Full tests, compile checks, Markdown-link checks, and diff hygiene checks pass, with any blocked external evidence recorded truthfully.
