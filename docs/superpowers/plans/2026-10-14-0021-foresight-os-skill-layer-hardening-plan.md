---
layer: change
artifact_type: plan
contract_version: "1"
status: active
template_id: implementation-plan
name: foresight-os-skill-layer-hardening
targets:
  - src/foresight_os/skills/manifest.json
  - src/foresight_os/skills/abstain-or-escalate/SKILL.md
  - src/foresight_os/skills/evidence-visualization/SKILL.md
  - src/foresight_os/skills/key-assumptions-check/SKILL.md
  - src/foresight_os/skills/presentation-storytelling/SKILL.md
  - src/foresight_os/skills/quantitative-sanity-check/SKILL.md
  - src/foresight_os/skills/red-team-claim/SKILL.md
  - src/foresight_os/skills/scenario-planning/SKILL.md
  - src/foresight_os/skills/slide-design-review/SKILL.md
  - src/foresight_os/skills/source-appraisal/SKILL.md
  - tests/test_review_records.py
  - tests/test_skill_package.py
  - tests/test_skill_exercise_evaluation.py
  - evaluation/skills/
  - evaluation/probes/run_skill_exercise_evaluation.py
  - evaluation/README.md
  - README.md
---

# Foresight OS Skill-Layer Hardening Plan

## Goal

Make draft PR #9 merge-ready as a bounded analytical-skill quality increment.
Fix its current-version test regression and capability ownership mismatch, make
the nine bundled skills more explicit about routing and output shape, add cheap
contract/evaluation coverage, and evaluate the skills on the existing strategic
exercise pack without changing the Controller, `AnalysisState`, `RelationIndex`,
`PresentationSpec`, Canva boundary, or frozen optimization thresholds.

The deferred `CHALLENGE_RECOMMENDATION` / Group Chat p95 investigation remains a
separate follow-up. This plan must not relabel that performance failure as
verified, relax its threshold, or mix its repair into the skill-layer PR.

## Verdict Review

The supplied verdict is accepted with these decisions:

- **Accepted P0:** `tests/test_review_records.py` must compare current skill
  execution against `SkillRegistry().manifest(...).version`; historical
  `ReviewRecord` fixtures must continue using their intentionally fixed
  historical version.
- **Accepted P0:** `source-appraisal` is a reasoning method, not a retrieval
  capability. Its manifest entry must require no capability. External source
  retrieval remains selected through the existing `ResearchNeed.SOURCE_DETAIL`
  path when the stage lacks the required material.
- **Accepted refinement:** retain the nine-skill catalog and three-skill
  presentation layer; do not add ACH, premortem, `indicators-validation`, a new
  presentation domain object, a design database, numeric confidence, or model-
  based evaluation infrastructure in this delivery.
- **Accepted refinement:** add compact use/do-not-use routing, output templates,
  Pyramid governing-thought guidance, and a renderer-only deck `DesignBrief`
  instruction without changing runtime object ownership.
- **Accepted boundary:** `manifest.json` remains the runtime source of truth for
  versions, hashes, capabilities, output contracts, and provenance. Frontmatter
  is compatibility metadata validated against the manifest; `SkillRegistry` does
  not gain a second metadata parser.
- **Accepted deferral:** the Group Chat p95 investigation is tracked separately
  and remains required before the formal three-increment closure can be called
  `VERIFIED`.

## Implementation Outcomes

### Current skill contracts are executable and least-privilege

The nine manifest entries resolve to packaged `SKILL.md` content, each current
version test reads its version from the manifest, and `source-appraisal` can run
on local workbook/report evidence without constructing an unnecessary
`page_retrieval` dependency. Presentation skills retain no external-write
capability; `evidence-visualization` retains only `data_analysis` and
`calculation`.

### Skill instructions reduce routing and output drift

Each bundled skill has compact inputs, use conditions, non-use/routing
boundaries, workflow, output contract, completion check, and adjacent-skill
guidance. Runtime-injected content stays as short as possible while remaining
executable, with a normal upper bound of 700 words and no minimum word count;
richer examples live in evaluation fixtures instead of prompts.

`presentation-storytelling` retains the fixed six-slide architecture and adds a
single governing thought with middle-slide reasoning. `slide-design-review`
establishes one renderer/handoff `DesignBrief` for the deck without introducing
`AnalysisState.DesignBrief` or another persistent authority. Visible citations
remain short while speaker notes retain full locators and calculation IDs.

### Contract and exercise evidence is durable and honest

Package tests validate manifest uniqueness, content hashes, frontmatter identity,
required sections, capability boundaries, and mechanically declared manifest
references. Per-skill evaluation fixtures remain outside runtime prompts. The
exercise report separates deterministic/reference-scored findings, provider
runtime measurements, and human/rubric judgments; unavailable inputs are
`BLOCKED_INPUT`, unavailable providers are `BLOCKED_EXTERNAL`, and structural
tests never claim model reasoning quality.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-plan-document-reviewer`, `skill-writing-plans`, `skill-executing-plans`, `skill-verification-before-completion`
- Isolation: existing PR #9 branch checkout or a fresh checkout from `origin/main`; do not edit the already merged closure branch
- Commit policy: verified per-task checkpoint commits after task-local proof; push and PR merge remain approval-controlled
- Preauthorized local actions: inspect PR #9 and `origin/main`, edit the declared skill/manifest/test/evaluation/documentation files, run local deterministic tests and probes, create bounded local evidence under `work/`, and update this plan ledger
- User-approval actions: provider-backed exercise execution, external writes, push, PR update, merge, dependency installation, destructive cleanup, deletion of preserved outputs, and scope changes
- Parallel ownership: none; the manifest, skill content, tests, and evaluation fixtures share one package contract and are serialized
- Sequential fallback: complete Tasks 0–4 in order; if the optional workbook pack is absent, record `BLOCKED_INPUT`, and if provider-backed exercise evaluation is unavailable, record `BLOCKED_EXTERNAL`; in either case complete required structural/local evidence without simulating provider quality

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/actionable-foresight-skills`
- Base commit: `657c17b1fed4d4e54aeee0067e03abc8b645acd4` (`origin/main`)
- Expected workspace: dedicated PR #9 checkout with tracked files clean before edits; preserve unrelated untracked outputs in the current workspace and do not stage them
- Next action: obtain authorization to publish the verified branch so PR #9 CI can rerun against the local fixes
- Blockers: PR #9 CI cannot reflect this work until an authorized push; provider mode is `BLOCKED_EXTERNAL` because `.env` is absent; the separate Group Chat p95 follow-up remains outside this plan

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 0 | `completed` | current | `lead controller` | none | PR/base reconciliation and changed-file inventory | `work/skill-layer-hardening-20261014/reconciliation/` |
| Task 1 | `completed` | current | `lead controller` | Task 0 | P0 version and capability tests | `python -m pytest -q tests/test_review_records.py tests/test_skill_package.py tests/test_participant_scope.py tests/test_research_needs.py` |
| Task 2 | `completed` | current | `lead controller` | Task 1 | nine-skill content and routing contract checks | `python -m pytest -q tests/test_skill_package.py tests/test_review_records.py tests/test_participant_scope.py tests/test_research_needs.py`; manifest hash reconciliation |
| Task 3 | `completed` | current | `lead controller` | Task 2 | package contract tests and nine evaluation fixtures | `python -m pytest -q tests/test_skill_package.py tests/test_skill_exercise_evaluation.py tests/test_skills.py`; `work/skill-layer-hardening-20261014/task-3/structural/` |
| Task 4 | `completed` | current | `lead controller` | Task 3 | exercise-pack evaluation and final local proof | `work/skill-layer-hardening-20261014/final/`; provider boundary recorded as `BLOCKED_EXTERNAL` |

## Task Breakdown

### Task 0: Reconcile PR #9 and establish the execution lane

**Purpose:**
- Confirm the exact PR head, base commit, failed CI evidence, changed-file scope,
  and preserved workspace state before editing.

**Task Function:**
- Establish current repository truth and execution ownership.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: exact Git/PR reconciliation is local, bounded, and does not benefit from delegation.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: Task 0 is an inventory gate; final verification covers the resulting changes.

**Specification Coverage:**
- Use PR #9 head `5247f259a00aead5f7111c05a829f03ca638dd7e` and base
  `657c17b1fed4d4e54aeee0067e03abc8b645acd4` as immutable reconciliation facts.
- Preserve the existing `work/`, `build/`, `data/`, and package-output files outside
  the dedicated execution checkout.

**Required Skills:**
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: `git status --short --branch`, `git worktree list --porcelain`, `gh pr view 9`, `gh pr checks 9`
- Inspect: `src/foresight_os/skills/manifest.json`, `tests/test_review_records.py`, `tests/test_skill_package.py`
- Verify: `work/skill-layer-hardening-20261014/reconciliation/`

**Dependencies:**
- `origin/main` is fetched and resolves to `657c17b1fed4d4e54aeee0067e03abc8b645acd4`.

**Authority:**
- Preauthorized local actions: read Git/PR/source state, create the declared evidence directory, and record reconciliation output.
- Stop for: a changed PR head/base, semantic conflict, missing checkout, unknown tracked edits, or any request to discard preserved files.

**Steps:**
- [x] Step 1: Fetch `origin/main` and create an explicit local PR ref with `git fetch origin pull/9/head:refs/remotes/origin/pr-9` when that ref is absent; do not assume `origin/pr-9` already exists and do not change the current checkout.
- [x] Step 2: Record PR number, base/head refs, exact SHAs, CI failure URLs, changed files, and current untracked inventory.
- [x] Step 3: Confirm that the only P0 implementation owners are `tests/test_review_records.py` and `src/foresight_os/skills/manifest.json`; keep p95 work out of this lane.

**Verification:**
- [x] `gh pr view 9 --json number,baseRefName,headRefName,headRefOid,statusCheckRollup`
- [x] `git diff --name-status 657c17b1fed4d4e54aeee0067e03abc8b645acd4 5247f259a00aead5f7111c05a829f03ca638dd7e`
- Expected: PR #9 is based on the recorded main commit, the current-version assertion failure is visible, and no unrelated tracked file is assigned to this plan.

**Exit Criteria:**
- The plan can be resumed from Git and the evidence directory without relying on session history.

### Task 1: Correct current skill identity and capability ownership

**Purpose:**
- Make the current-version review test future-proof and remove the unnecessary
  retrieval requirement from `source-appraisal`.

**Task Function:**
- Repair the manifest/test contract at its canonical owners.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: two small, coupled contract changes with clear ownership and low implementation ambiguity.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused pytest and full CI provide independent regression proof.

**Specification Coverage:**
- Current executions compare against `SkillRegistry().manifest("red-team-claim").version`.
- Historical persistence fixtures retain fixed `1.0.0` identity where they intentionally model old data.
- `source-appraisal.capability_ids` becomes `[]`; `page_retrieval` is requested only through existing source-detail research needs.

**Required Skills:**
- `skill-code-standards`
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: `src/foresight_os/controller/skills.py:SkillRegistry`
- Modify: `tests/test_review_records.py:test_selected_review_skills_produce_validated_typed_objections`
- Modify: `src/foresight_os/skills/manifest.json:source-appraisal`
- Verify: `tests/test_participant_scope.py`, `tests/test_research_needs.py`, `tests/test_review_records.py`

**Dependencies:**
- Task 0 confirms the PR #9 head and the manifest remains the runtime source of truth.

**Authority:**
- Preauthorized local actions: edit the named test assertion and manifest capability list, then run focused tests.
- Stop for: changes to capability resolution, research-need semantics, historical fixture meaning, or any new retrieval adapter.

**Steps:**
- [x] Step 1: Replace the current-execution literal version assertion with the version returned by `SkillRegistry().manifest("red-team-claim")`.
- [x] Step 2: Preserve the fixed historical version in the round-trip persistence test and document the distinction in test names or assertions.
- [x] Step 3: Set `source-appraisal.capability_ids` to an empty list and verify source-detail routing remains owned by the existing research-needs path.

**Verification:**
- [x] `python -m pytest -q tests/test_review_records.py tests/test_skill_package.py tests/test_participant_scope.py tests/test_research_needs.py`
- Expected: current and historical skill identity tests pass; local source appraisal does not require page retrieval; presentation capability constraints remain unchanged.

**Exit Criteria:**
- The two P0 findings are fixed at canonical owners with no runtime architecture change.

### Task 2: Harden the nine bundled skill procedures without expanding runtime architecture

**Purpose:**
- Reduce accidental skill overlap and output drift while keeping injected prompts compact.

**Task Function:**
- Edit method contracts and preserve existing skill identity/provenance ownership.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: content design is cross-file but deterministic, with decisions settled by the verdict.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: structural contract tests and content review cover the bounded documentation change.

**Specification Coverage:**
- Update all nine `SKILL.md` files with `Inputs`, `When to use`, `Do not use / route instead`, `Workflow`, `Output`, `Completion check`, `Pair with`, and `Anti-patterns` sections.
- Keep each runtime skill as short as possible while remaining executable and normally at or below 700 words; do not pad concise methods to meet a minimum. Move worked examples to evaluation fixtures.
- Add to `presentation-storytelling`: one governing thought, middle-slide why-chain, fixed six-slide mapping, visible-source versus speaker-note source hierarchy, and a compact slide brief template.
- Add to `evidence-visualization`: do not create a visual unless it materially improves comprehension; preserve honest scales, uncertainty, citations, and calculation reconciliation.
- Add to `slide-design-review`: one renderer-only deck `DesignBrief` covering theme/template, typography, palette, chart style, citation style, and density target; do not create a domain object or persistence authority.

**Required Skills:**
- `skill-executing-plans`

**Files And Symbols:**
- Modify: `src/foresight_os/skills/abstain-or-escalate/SKILL.md`
- Modify: `src/foresight_os/skills/evidence-visualization/SKILL.md`
- Modify: `src/foresight_os/skills/key-assumptions-check/SKILL.md`
- Modify: `src/foresight_os/skills/presentation-storytelling/SKILL.md`
- Modify: `src/foresight_os/skills/quantitative-sanity-check/SKILL.md`
- Modify: `src/foresight_os/skills/red-team-claim/SKILL.md`
- Modify: `src/foresight_os/skills/scenario-planning/SKILL.md`
- Modify: `src/foresight_os/skills/slide-design-review/SKILL.md`
- Modify: `src/foresight_os/skills/source-appraisal/SKILL.md`
- Verify: `src/foresight_os/skills/manifest.json` hashes after content changes

**Dependencies:**
- Task 1 establishes the capability boundary and current manifest versions.

**Authority:**
- Preauthorized local actions: edit only the nine skill documents and regenerate their manifest hashes/versions through the existing canonical workflow.
- Stop for: new skill IDs, new capabilities, prompt downloads, external-write permissions, numeric confidence scores, new domain objects, or fixed-slide compiler changes.

**Steps:**
- [x] Step 1: Add compact routing/non-routing boundaries and output templates to the six analytical methods.
- [x] Step 2: Add the governing-thought and source-hierarchy rules to `presentation-storytelling`.
- [x] Step 3: Add the no-unnecessary-visual rule and preserve the combined chart-selection method in `evidence-visualization`.
- [x] Step 4: Add the renderer-only `DesignBrief` and deck-level consistency check to `slide-design-review`.
- [x] Step 5: Recompute manifest content hashes while retaining the draft target versions already established relative to `main`—`1.1.0` for the six existing skills and `1.0.0` for the three new presentation skills. Do not bump again for edits made before this draft merges; keep `manifest.json` authoritative.

**Verification:**
- [x] `python -m pytest -q tests/test_skill_package.py tests/test_review_records.py tests/test_participant_scope.py tests/test_research_needs.py` (14 passed with the worktree `src` on `PYTHONPATH`)
- [x] Inspect all nine documents for required sections, word counts, fixed six-slide references, and absence of external-write capability.
- Expected: every manifest hash matches packaged content; the runtime prompt remains compact; no second presentation or design model is introduced.

**Exit Criteria:**
- The nine methods have explicit, bounded procedures and can be selected without accidental overlap or authority escalation.

### Task 3: Add deterministic skill-contract tests and externalized evaluation fixtures

**Purpose:**
- Catch manifest/content drift cheaply and keep worked examples out of runtime-injected prompts.

**Task Function:**
- Extend package-level contract proof and add fixture-owned routing examples.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: deterministic test and JSON fixture work with no provider dependency.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the test suite is the validator for these deterministic contracts.

**Specification Coverage:**
- For every skill, prove `SKILL.md` existence, unique manifest ID, content hash match, frontmatter name equality, required sections, and resolvable adjacent-skill references.
- Prove presentation capability boundaries: storytelling and design review require no capabilities; evidence visualization requires exactly `data_analysis` and `calculation`.
- Add one JSON fixture per skill under `evaluation/skills/`, each containing three positive prompts, one near-miss prompt, expected routing or output properties, and the skill version under evaluation.
- Record prompt-size measurements for each skill and these representative combinations: `red-team-claim`, `red-team-claim + key-assumptions-check`, and `presentation-storytelling + evidence-visualization`; use word count and UTF-8 byte size only, with no tokenizer dependency.

**Required Skills:**
- `skill-executing-plans`

**Files And Symbols:**
- Modify: `tests/test_skill_package.py:SkillPackageTests`
- Add: `tests/test_skill_exercise_evaluation.py` for report-status and metric-class contract checks
- Add: `evaluation/skills/abstain-or-escalate.json`
- Add: `evaluation/skills/evidence-visualization.json`
- Add: `evaluation/skills/key-assumptions-check.json`
- Add: `evaluation/skills/presentation-storytelling.json`
- Add: `evaluation/skills/quantitative-sanity-check.json`
- Add: `evaluation/skills/red-team-claim.json`
- Add: `evaluation/skills/scenario-planning.json`
- Add: `evaluation/skills/slide-design-review.json`
- Add: `evaluation/skills/source-appraisal.json`
- Verify: `src/foresight_os/controller/skills.py:SkillRegistry.resolve`

**Dependencies:**
- Task 2 content and manifest hashes are final for this delivery.

**Authority:**
- Preauthorized local actions: add deterministic tests and JSON fixtures; do not add YAML dependencies, runtime frontmatter parsing, or provider calls.
- Stop for: fixture fields that cannot be checked deterministically, model-quality claims from string presence alone, or any new evaluation service.

**Steps:**
- [x] Step 1: Implement a minimal frontmatter reader in the test module for `name` only; keep manifest metadata authoritative at runtime.
- [x] Step 2: Assert required sections and capability constraints for every resolved skill, and extract only backticked identifiers under `## Pair with` for deterministic manifest-reference validation.
- [x] Step 3: Add nine fixture files with positive/near-miss routing cases and expected observable properties.
- [x] Step 4: Add fixture schema validation so malformed or duplicate skill fixture IDs fail locally.
- [x] Step 5: Record word count and UTF-8 byte size for every skill and the representative skill combinations named in the plan; fail only when the 700-word upper bound is exceeded.

**Verification:**
- [x] `python -m pytest -q tests/test_skill_package.py tests/test_skill_exercise_evaluation.py tests/test_skills.py` (15 passed)
- Expected: package integrity, frontmatter identity, section presence, capability boundaries, fixture schema, and prompt-size measurements all pass without network access; no test derives human correction effort from acceptance state.

**Exit Criteria:**
- Skill content and evaluation inputs have one canonical runtime source and one explicit non-runtime fixture source, with deterministic drift detection.

### Task 4: Evaluate the nine skills on tracked cases and optionally extend to the exercise pack

**Purpose:**
- Measure whether the richer skill procedures improve evidence-aware analytical and presentation outcomes without overstating provider-backed proof.

**Task Function:**
- Produce a bounded, machine-readable evaluation report and merge-readiness evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: evaluation orchestration must preserve acceptance control and external-boundary truth.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final verification owns cross-task acceptance; the probe owns report completeness.

**Specification Coverage:**
- Required merge evidence uses the tracked `evaluation/cases/case-001` through `case-005` fixtures and their `workbook.csv`, `decision.md`, and `reference.json` files; this tier must work from a fresh clone without `data/exercise/`.
- Treat `data/exercise/01_Portfolio_Resilience.xlsx` through `05_PowerBI_Strategic_Portfolio.xlsx` as optional extended evidence. If that local/untracked pack is absent, record `BLOCKED_INPUT` for the extended tier and do not fail the required merge gate.
- Do not reuse `evaluation/candidate_harness.py:run_candidate` as provider-backed skill evidence. Add a bounded provider runner in the new probe that constructs `ParticipantConfig(skill_ids=...)`, resolves those IDs through `SkillRegistry`, creates the approved client through the existing `load_provider_settings` path, invokes `run_recipe_async` with the selected skills in run context, and emits only a sanitized structured result.
- Define the report with three evidence classes: deterministic/reference-scored metrics (provenance/citation presence, expected assumption and contradiction detection, expected defect detection, numerical reconciliation, and chart-data traceability when applicable); provider/runtime measurements (input/output tokens only when exposed, model/tool calls, latency, and failure status); and human/rubric judgments (chart appropriateness, slide takeaway quality, narrative usefulness, and human correction effort).
- Use `not_measured` for human/rubric metrics unless an explicit human assessment artifact is supplied. Never derive human correction effort from acceptance state. Use `BLOCKED_EXTERNAL` only for unavailable provider configuration/execution and `BLOCKED_INPUT` only for missing optional exercise inputs.
- Keep the Group Chat/`CHALLENGE_RECOMMENDATION` p95 repair outside this plan; preserve its frozen threshold and existing failure receipt.
- Keep the Group Chat/`CHALLENGE_RECOMMENDATION` p95 repair outside this plan; preserve its frozen threshold and existing failure receipt.

**Required Skills:**
- `skill-executing-plans`
- `skill-verification-before-completion`

**Files And Symbols:**
- Add: `evaluation/probes/run_skill_exercise_evaluation.py:main`
- Modify: `evaluation/README.md` with the two-tier commands, runner path, report schema, and `BLOCKED_INPUT`/`BLOCKED_EXTERNAL` semantics
- Verify: `src/foresight_os/runtime/maf_probe.py:load_provider_settings`
- Verify: `src/foresight_os/runtime/participants.py:ParticipantConfig`, `src/foresight_os/runtime/workflow.py:run_recipe_async`
- Verify: `evaluation/cases/case-001` through `evaluation/cases/case-005` as required deterministic/reference inputs
- Optionally verify: `data/exercise/01_Portfolio_Resilience.xlsx` through `data/exercise/05_PowerBI_Strategic_Portfolio.xlsx`
- Verify: `README.md` skill and presentation guidance

**Dependencies:**
- Tasks 1–3 complete and full local package tests pass.

**Authority:**
- Preauthorized local actions: implement and run the deterministic tracked-case probe, write disposable evidence under `work/skill-layer-hardening-20261014/`, and update documentation for the exact commands and report schema.
- Stop for: provider execution without explicit approval, missing provider credentials, missing optional exercise inputs, external writes, threshold changes, new exercise fixtures, or any claim that structural tests prove provider reasoning quality.

**Steps:**
- [x] Step 1: Implement structural mode over tracked `evaluation/cases/case-001..005`, load each reference rubric, resolve the selected skill bundle through `SkillRegistry`, and record manifest IDs, versions, hashes, deterministic scores, and `not_measured` human/provider fields.
- [x] Step 2: Implement the provider runner as a separate path using `ParticipantConfig(skill_ids=...)`, `SkillRegistry`, `load_provider_settings`, an approved `OpenAIChatClient`, and `run_recipe_async`; do not route through `run_candidate` or relabel the existing live smoke probe.
- [x] Step 3: Run the required structural mode from a clean-clone-compatible checkout and validate report completeness. If `data/exercise/` is absent, add an extended-tier `BLOCKED_INPUT` record without changing required results.
- [x] Step 4: Run provider-backed mode only when an approved provider configuration is present; otherwise record `BLOCKED_EXTERNAL` with the missing boundary and preserve structural results without fabricating provider or human metrics.
- [x] Step 5: Update `README.md` and `evaluation/README.md` with the nine-skill catalog, routing rules, package source of truth, two-tier commands, metric classes, and evaluation limits.
- [x] Step 6: Reconcile the plan ledger, PR #9 evidence, and the separate p95 follow-up reference.

**Verification:**
- [x] `python -m pytest -q` (full suite passed)
- [x] `python evaluation/probes/run_skill_exercise_evaluation.py --mode structural --exercise-root evaluation/cases --skill-fixture-root evaluation/skills --output-root work/skill-layer-hardening-20261014/final/structural` (five cases, 35/35 reference checks)
- [x] `python evaluation/probes/run_skill_exercise_evaluation.py --mode provider --exercise-root evaluation/cases --skill-fixture-root evaluation/skills --extended-exercise-root data/exercise --output-root work/skill-layer-hardening-20261014/final/provider` (`BLOCKED_EXTERNAL`; `.env` absent; no provider call)
- [x] `python evaluation/probes/run_clean_wheel_smoke.py --output-root work/skill-layer-hardening-20261014/final/clean-wheel` (passed in isolated venv)
- [x] `git diff --check` (passed)
- Expected: full tests, tracked structural/reference evaluation, and clean-wheel proof pass; the optional workbook tier is explicitly `BLOCKED_INPUT`; provider mode is explicitly `BLOCKED_EXTERNAL`; no p95 threshold is changed.

**Exit Criteria:**
- PR #9 has green deterministic CI and no unresolved P0 finding; the skill layer is merge-ready; exercise evidence is durable and honest; formal three-increment closure remains unverified until the separate performance follow-up closes.

## Verification

Run these commands fresh after all implementation tasks:

- `python -m pytest -q`
- `python evaluation/probes/run_skill_exercise_evaluation.py --mode structural --exercise-root evaluation/cases --skill-fixture-root evaluation/skills --output-root work/skill-layer-hardening-20261014/final/structural`
- `python evaluation/probes/run_clean_wheel_smoke.py --output-root work/skill-layer-hardening-20261014/final/clean-wheel`
- `git diff --check`
- `git status --short --branch`
- `gh pr checks 9`

If provider mode is configured and explicitly approved, also run:

- `python evaluation/probes/run_skill_exercise_evaluation.py --mode provider --exercise-root evaluation/cases --skill-fixture-root evaluation/skills --extended-exercise-root data/exercise --output-root work/skill-layer-hardening-20261014/final/provider`

Required evidence includes the fixed current-version assertion, preserved
historical review identity, least-privilege source appraisal construction,
manifest/content/frontmatter contract output, nine fixture validation, prompt-size
measurements, clean-wheel resource resolution, tracked five-case structural and
reference evaluation, optional extended-input status, and an explicit provider
status with human/rubric metrics left `not_measured` unless assessed.

## Completion Criteria

The plan is ready for completion verification when:

1. PR #9’s two P0 findings are fixed at canonical owners and deterministic CI is green.
2. All nine skills retain unique manifest IDs, matching hashes, valid packaged content, explicit routing boundaries, and bounded output contracts.
3. `source-appraisal` no longer forces `page_retrieval`; source-detail retrieval remains stage/research-need controlled.
4. Presentation skills preserve the fixed six-slide `PresentationSpec`, source hierarchy, human approval boundary, and vendor-neutral Canva ownership.
5. Contract tests and nine evaluation fixtures pass without network access or new runtime dependencies.
6. The tracked five-case evaluation report passes deterministic/reference scoring and separates provider/runtime measurements from human/rubric metrics; optional workbook absence is `BLOCKED_INPUT`, provider unavailability is `BLOCKED_EXTERNAL`, and no human correction effort is inferred from acceptance state.
7. The deferred Group Chat/`CHALLENGE_RECOMMENDATION` p95 regression remains recorded with frozen thresholds and is not relabeled as resolved.
8. `skill-verification-before-completion` can return `verified` for this skill-layer plan after PR #9 is pushed and deterministic CI reruns; until then the plan remains active with the exact external publication blocker recorded.
9. No plan status changes to `completed` until fresh verification confirms every required task and the separate performance follow-up is explicitly outside this plan’s completion scope.
