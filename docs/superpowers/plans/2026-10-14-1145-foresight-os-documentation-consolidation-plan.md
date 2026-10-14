---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: foresight-os-documentation-consolidation
targets:
  - README.md
  - docs/README.md
  - docs/getting-started.md
  - docs/architecture.md
  - docs/skills.md
  - docs/evidence-and-evaluation.md
  - docs/configuration.md
  - docs/extending.md
  - scripts/check_markdown_links.py
  - tests/test_markdown_links.py
---

# ForesightOS Documentation Consolidation

## Verdict Review

The supplied verdict is accepted with one implementation clarification: the
documentation change should preserve the existing `docs/intent/`,
`docs/superpowers/plans/`, and `docs/superpowers/evidence/` history, while
adding only seven flat user-facing pages under `docs/`. The root README remains
the product front door; it does not become a second reference manual.

The plan therefore treats this as a consolidation and maintenance-reduction
change, not a documentation-platform project. Source code, manifests, schemas,
`.env.example`, workflow definitions, and durable evidence remain technical
truth. Markdown explains those sources and links to them; it does not copy
their complete inventories.

## Scope

### In scope

- Create the seven canonical user-facing documentation pages named in the
  target list.
- Reduce `README.md` to a product overview, capability summary,
  architecture-at-a-glance, five-minute quickstart, current verification
  boundary, and links to `docs/README.md`.
- Move detailed provider, skill, evidence, configuration, and extension
  guidance out of `README.md` into the owning canonical pages.
- Remove the duplicated scheduled-evidence text and obsolete performance or
  provider claims from the README.
- Add one small local Markdown-link checker and one focused test module.
- Verify every current-status statement against source, workflow, or durable
  evidence rather than copying historical plan text.

### Out of scope

- MkDocs, Docusaurus, Sphinx, hosted documentation, generated navigation, or a
  documentation database.
- New `concepts/`, `architecture/`, `reference/`, `guides/`, `operations/`,
  `contributing/`, `decisions/`, or `diagrams/` directories.
- Runtime, CLI, schema, skill-manifest, provider, workflow, or packaging
  behavior changes.
- Adding a console entry point to `pyproject.toml`.
- Rewriting historical plans or governance files to look like current product
  documentation.
- Publishing Canva designs, authenticating providers, or changing external
  integrations.

## Canonical Ownership Map

| Documentation owner | Responsibility | Technical sources it must defer to |
|---|---|---|
| `README.md` | Product front door, capabilities, architecture summary, quickstart | `pyproject.toml`, `src/foresight_os/cli.py`, `docs/README.md` |
| `docs/README.md` | Navigation only | The six canonical content pages |
| `docs/getting-started.md` | Installation, first workbook analysis, report, continuation, common CLI flow | `pyproject.toml`, `src/foresight_os/cli.py`, `src/foresight_os/vertical_slice.py`, `src/foresight_os/persistence/recovery.py` |
| `docs/architecture.md` | Runtime, analytical state, artifact flow, execution patterns, provider boundaries | `src/foresight_os/controller/`, `src/foresight_os/analysis/`, `src/foresight_os/persistence/`, `src/foresight_os/artifacts/`, `src/foresight_os/runtime/` |
| `docs/skills.md` | Skill, capability, participant, pattern, registry, effective-plan, and invalidation concepts | `src/foresight_os/controller/skills.py`, `src/foresight_os/skills/manifest.json`, `src/foresight_os/skills/*/SKILL.md` |
| `docs/evidence-and-evaluation.md` | Status semantics, receipts, evidence tiers, evaluation limits, performance proof | `evaluation/run.py`, `evaluation/probes/`, `tests/test_evaluation_contract.py`, `tests/test_optimization_measurement.py`, `docs/superpowers/evidence/` |
| `docs/configuration.md` | Environment groups, inherited variables, provider/MCP behavior, secret handling | `.env.example`, `src/foresight_os/runtime/provider_config.py`, `src/foresight_os/runtime/web_search.py`, `src/foresight_os/clients/` |
| `docs/extending.md` | Add a skill, evaluator case, capability, provider adapter, or artifact destination | `src/foresight_os/skills/`, `evaluation/cases/`, `src/foresight_os/runtime/capabilities.py`, `src/foresight_os/artifacts/`, `tests/test_skills.py`, `tests/test_evaluation_contract.py`, `tests/test_capabilities.py`, `tests/test_presentation_spec.py` |

`docs/intent/`, `docs/superpowers/plans/`, and `docs/superpowers/evidence/`
remain historical or durable-record owners. They are linked when useful but are
not rewritten into onboarding pages.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Isolation: use a fresh task-specific worktree from `origin/main`; preserve
  any dirty checkout and untracked outputs in the current workspace.
- Write ownership: one lead owns the documentation files; the coordination
  owner separately owns this plan’s status and ledger fields; the link checker
  and its tests are written only after the final local-link inventory is known.
- External boundary: no provider authentication, Canva mutation, publication,
  or network-dependent evidence is required.
- Completion authority: final verification reconciles the README, canonical
  pages, source-derived claims, link-check output, and Git diff.

## Coordination State

- Coordination owner: one lead controller (Codex); no task-level agent may
  change plan status, dependencies, acceptance criteria, or historical records.
- Base expectation: `origin/main` at bootstrap time; record the resolved base
  commit in the first checkpoint.
- Workspace expectation: a fresh task-specific worktree created from that base;
  do not use the current dirty checkout for implementation.
- Plan bootstrap: copy this plan into the fresh worktree before Task 0, commit
  it as the first tracked plan artifact, and keep the same path as the active
  plan throughout execution.
- Ledger fields: task status, executor, workspace, dependencies, accepted
  proof, blocker, and next action are updated in this plan by the coordination
  owner after each task boundary.
- Initial state: plan `active`, active task `0`, all tasks `proposed`,
  executor `unresolved`, blocker `none`, next action `create worktree and
  bootstrap plan`.
- Checkpoints: the lead creates a native Git checkpoint commit after each
  accepted task boundary; no force-push, stash-and-forget, or direct mutation of
  historical plans/evidence is permitted.
- Plan status transition: change `proposed` to `active` only at bootstrap and
  to `completed` only after Task 7 returns verified evidence.

## Acceptance Criteria

1. The six canonical content pages and `docs/README.md` exist at the exact
   paths in the ownership map.
2. `README.md` is reduced to approximately 150–250 lines and contains no
   duplicated scheduled-evidence section, exhaustive skill catalog, detailed
   provider setup, benchmark procedure, or internal governance instructions.
3. `docs/README.md` contains navigation links only and points to all six
   canonical content pages.
4. `getting-started.md` gives a linear install → analyze → inspect status →
   report → continue workflow using the existing `python -m foresight_os.cli`
   commands.
5. `architecture.md` explains the `WorkBrief` → `Controller` → `RecipeStage`
   → selected skills/capabilities → `AnalysisState` → review/finding/artifact
   flow and keeps Canva as an optional rendering boundary.
6. `skills.md` explains the distinction between skill, capability, participant,
   pattern, and controller, and identifies manifest/version/hash/reuse
   ownership without duplicating individual `SKILL.md` procedures.
7. `evidence-and-evaluation.md` defines `VERIFIED`, `FAILED`,
   `BLOCKED_INPUT`, `BLOCKED_EXTERNAL`, and `not_measured`, and prominently
   states that structural verification does not prove model reasoning quality.
8. `configuration.md` uses `.env.example` as the variable inventory and
   states that inherited environment variables are read without automatic
   `.env` loading.
9. `extending.md` gives bounded steps for adding a skill, evaluator case,
   capability, provider adapter, and artifact destination without introducing
   a second registry or evidence store.
10. No user-facing page duplicates private Project OS, Codex, CoS, or agent
    governance instructions from `AGENTS.md`.
11. The local Markdown-link checker passes for `README.md`, `docs/README.md`,
    all six canonical content pages, and the remaining tracked `docs/**/*.md`
    files; newly created canonical pages are included before they are tracked.
12. Existing source and test behavior remains unchanged; full tests, compile,
    link checking, and whitespace validation pass.

## Task Breakdown

| Task | Status | Executor | Outcome | Dependencies | Accepted proof | Blocker | Next action |
|---|---|---|---|---|---|---|---|
| 0. Establish documentation baseline | completed | Codex | Source-backed inventory of README claims, docs owners, commands, variables, skills, evidence, and stale wording | None | CLI, runtime, skill, evaluation, environment, artifact, and test sources inspected; ownership map reconciled | none | author architecture and skills pages |
| 1. Author architecture and skills pages | completed | Codex | Canonical runtime/analytical architecture and skill model pages | Task 0 | `docs/architecture.md` and `docs/skills.md` added; source ownership and optional Canva boundary documented | none | author evidence and configuration pages |
| 2. Author evidence and configuration pages | completed | Codex | Canonical evidence vocabulary, evaluation tiers, performance boundary, and configuration behavior | Task 0 | `docs/evidence-and-evaluation.md` and `docs/configuration.md` added; statuses and `.env.example` ownership reconciled | none | author getting-started and extending pages |
| 3. Author getting-started and extending pages | completed | Codex | One runnable user workflow and one bounded contributor extension workflow | Tasks 1–2 | `docs/getting-started.md` and `docs/extending.md` added with reviewed CSV quickstart and extension owners | none | add documentation navigation |
| 4. Add documentation navigation | completed | Codex | `docs/README.md` links users to the six canonical content pages without duplicating content | Tasks 1–3 | navigation-only `docs/README.md` links all six canonical pages | none | reduce and reconcile README |
| 5. Reduce and reconcile README | completed | Codex | Root README becomes a concise product front door and points to canonical docs | Tasks 1–4 | README rewritten to product overview, quickstart, architecture, evidence boundary, and canonical links | none | implement explicit-target checker |
| 6. Add local Markdown-link validation | completed | Codex | Lightweight checker and focused tests for all canonical and historical local links | Tasks 1–5 | checker passed across explicit canonical targets plus tracked docs; focused tests passed | none | perform final documentation verification |
| 7. Perform final documentation verification | completed | Codex | Full evidence that content, links, source ownership, and repository behavior are consistent | Tasks 0–6 | link checker passed for 22 Markdown paths; focused and full pytest passed; compileall and diff check passed; README 151 lines; worktree clean | none | preserve verified branch state |

### Task 0: Establish the documentation baseline

**Purpose:**
- Identify what can be moved, what must be rewritten, and which sources own
  exact values before creating new pages.

**Task Function:**
- Source reconciliation and documentation ownership analysis.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers the verdict’s SSOT map, maintenance-reduction goal, and no-duplication
  boundary.

**Required Skills:**
- `skill-writing-plans`, `skill-code-standards`.

**Files And Symbols:**
- Read `README.md`, `.env.example`, `pyproject.toml`, `src/foresight_os/cli.py`.
- Read `src/foresight_os/controller/`, `src/foresight_os/analysis/`,
  `src/foresight_os/persistence/`, `src/foresight_os/artifacts/`,
  `src/foresight_os/runtime/`, and `src/foresight_os/skills/manifest.json`.
- Read `evaluation/run.py`, `evaluation/probes/`, relevant `tests/`,
  `.github/workflows/`, and `docs/superpowers/evidence/`.

**Dependencies:**
- None.

**Authority:**
- Preauthorized: read-only inspection and plan-local notes.
- Stop for: a source/README conflict that cannot be resolved from current code,
  a missing command named by the verdict, or a request to expand the page tree.

**Steps:**
1. Create the fresh task-specific worktree from `origin/main` and record its
   absolute path, resolved base commit, branch, and clean/dirty state.
2. Copy this plan into the fresh worktree before editing any implementation
   file, commit it as the first checkpoint, and change its status to `active`.
3. Initialize the task ledger with the current task, executor, dependencies,
   accepted proof, blocker, and next action fields from `Coordination State`.
4. Record the current README line count and headings.
5. Extract every README command, environment variable, status claim, provider
   claim, benchmark threshold, and skill description.
6. Map each extracted item to one canonical source from the ownership table.
7. Mark obsolete, duplicated, or externally blocked claims for rewrite rather
   than copying them into a new page.
8. Confirm that `python -m foresight_os.cli --help` is the valid CLI discovery
   path and that no console entry point exists in `pyproject.toml`.

**Verification:**
- `python -m foresight_os.cli --help`
- `git status --short --branch`
- `rg -n "scheduled-evidence|Group Chat|FORESIGHT_|Canva|Power BI|Optimization" README.md`

**Exit Criteria:**
- Every README section has one destination or an explicit removal decision.

### Task 1: Author architecture and skills pages

**Purpose:**
- Explain how ForesightOS works and how its reasoning methods are selected
  without duplicating implementation truth.

**Task Function:**
- Current architecture and skill-concept documentation.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers `docs/architecture.md` and `docs/skills.md` from the SSOT map.

**Required Skills:**
- `skill-code-standards`.

**Files And Symbols:**
- Create `docs/architecture.md` from `src/foresight_os/controller/`,
  `src/foresight_os/analysis/`, `src/foresight_os/persistence/`,
  `src/foresight_os/artifacts/`, and `src/foresight_os/runtime/`.
- Create `docs/skills.md` from `src/foresight_os/controller/skills.py`,
  `src/foresight_os/skills/manifest.json`, and the bundled `SKILL.md` files.

**Dependencies:**
- Task 0.

**Authority:**
- Preauthorized: create the two named Markdown files and embed two Mermaid
  diagrams.
- Stop for: a proposed second analytical state, finding store, skill registry,
  or provider-specific architecture page.

**Steps:**
1. Describe the `WorkBrief` → controller → recipe/stage → execution →
   `AnalysisState` → review/finding/artifact lifecycle.
2. Describe Direct, Sequential, Concurrent, Handoff, and Group Chat as
   coordination patterns, including bounded rounds and budgets without copying
   implementation constants that are not stable documentation contracts.
3. Explain the Canva boundary as `FindingView` → `PresentationSpec` → human
   approval → optional renderer/provider.
4. Define Skill, Capability, Participant, Pattern, and Controller in `skills.md`.
5. Explain skill ID, version, content hash, manifest, effective plan, required
   capabilities, registry reuse, and invalidation.
6. Link exact procedural details to bundled `SKILL.md` files instead of copying
   their instructions.

**Verification:**
- `rg -n "AnalysisState|FindingView|PresentationSpec|SkillRegistry|content hash|BLOCKED_EXTERNAL" docs/architecture.md docs/skills.md`
- `git diff --check`

**Exit Criteria:**
- Both pages have one clear responsibility and every exact contract points to
  its source owner.

### Task 2: Author evidence and configuration pages

**Purpose:**
- Give users a truthful model of verification, status semantics, provider
  boundaries, and local configuration.

**Task Function:**
- Evidence and configuration contract documentation.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers `docs/evidence-and-evaluation.md` and `docs/configuration.md`.

**Required Skills:**
- `skill-backend-verification` for source-backed status and boundary proof.

**Files And Symbols:**
- Create `docs/evidence-and-evaluation.md` from `evaluation/run.py`,
  `evaluation/probes/run_skill_exercise_evaluation.py`,
  `evaluation/probes/compare_optimization_receipts.py`,
  `tests/test_evaluation_contract.py`, `tests/test_optimization_measurement.py`,
  and `docs/superpowers/evidence/`.
- Create `docs/configuration.md` from `.env.example`,
  `src/foresight_os/runtime/provider_config.py`,
  `src/foresight_os/runtime/web_search.py`, and `src/foresight_os/clients/`.

**Dependencies:**
- Task 0.

**Authority:**
- Preauthorized: create the two named Markdown files and link to `.env.example`
  and durable evidence.
- Stop for: a claim that structural evaluation proves model quality, a claim
  that missing providers are successful, or a duplicated environment-variable
  inventory.

**Steps:**
1. Define `VERIFIED`, `FAILED`, `BLOCKED_INPUT`, `BLOCKED_EXTERNAL`, and
   `not_measured` using current evaluator and receipt behavior.
2. Present the evidence tiers from unit/integration tests through optional
   provider and human assessment.
3. State prominently that structural verification does not prove model
   reasoning quality.
4. Explain workload identity, repeat stability, performance thresholds, and
   durable receipt provenance without hard-coding historical numbers as current
   results.
5. Group configuration by web search, hosted MCP signals, provider overrides,
   probe-only settings, and secret handling.
6. State that inherited environment variables are read and `.env` is not loaded
   automatically; use `.env.example` for the exact variable inventory.

**Verification:**
- `rg -n "VERIFIED|FAILED|BLOCKED_INPUT|BLOCKED_EXTERNAL|not_measured|does not prove|\.env\.example|inherited environment" docs/evidence-and-evaluation.md docs/configuration.md`
- `python -m pytest -q tests/test_evaluation_contract.py tests/test_optimization_measurement.py`

**Exit Criteria:**
- Evidence claims match evaluator code and receipts; configuration claims match
  `.env.example` and runtime configuration code.

### Task 3: Author getting-started and extending pages

**Purpose:**
- Provide one successful user path and one safe extension path.

**Task Function:**
- Workflow and contributor guidance.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers `docs/getting-started.md` and `docs/extending.md`.

**Required Skills:**
- `skill-code-standards`.

**Files And Symbols:**
- Create `docs/getting-started.md` from `pyproject.toml`, `src/foresight_os/cli.py`,
  `src/foresight_os/vertical_slice.py`, and
  `src/foresight_os/persistence/recovery.py`.
- Create `docs/extending.md` from `src/foresight_os/skills/`,
  `evaluation/cases/`, `src/foresight_os/runtime/capabilities.py`,
  `src/foresight_os/artifacts/`, and adjacent tests.

**Dependencies:**
- Tasks 1–2.

**Authority:**
- Preauthorized: create the two named Markdown files and use existing CLI
  commands only.
- Stop for: adding a new CLI command, adding a console entry point, or claiming
  provider credentials are required for the local quickstart.

**Steps:**
1. Write the linear workflow with the runnable repository fixture:
   `python -m foresight_os.cli analyze --workbook evaluation/cases/case-001/workbook.csv --work-dir work/docs-quickstart --accept`.
   Document the expected exit code `0` and output status `accepted`.
2. Show status inspection by reading `work/docs-quickstart/analysis.json`, then
   run `python -m foresight_os.cli report --work-dir work/docs-quickstart` and
   document the expected exit code `0` and generated
   `work/docs-quickstart/artifacts/executive-report.md` path.
3. Show continuation with
   `python -m foresight_os.cli continue --work-dir work/docs-quickstart --changed-id claim-northern-demand-growth --reason "Updated source evidence"`.
   Document the expected exit code `0`, investigation ID `case-001`, revision
   `2`, and reassessment ID `claim-northern-demand-growth`.
4. Keep XLSX and Power BI capability references separate from this CLI
   quickstart; `src/foresight_os/analysis/workbook.py` currently consumes the
   repository’s CSV case format for the documented vertical slice.
5. Add a short troubleshooting section for missing files, unavailable external
   providers, and invalid work directories.
6. Explain how to add a skill: `SKILL.md`, manifest entry, required capabilities,
   version/hash update, routing/evaluation coverage, and tests.
7. Explain how to add an evaluator case, capability/provider adapter, and
   artifact destination while preserving the existing state and evidence owners.
8. Link exact CLI flags to `python -m foresight_os.cli --help` rather than
   maintaining a second exhaustive flag table.

**Verification:**
- `python -m foresight_os.cli --help`
- `python -m pytest -q tests/test_vertical_slice.py tests/test_client_continuation.py tests/test_skills.py`
- Manually execute the documented local command sequence against a disposable
  work directory using `evaluation/cases/case-001/workbook.csv`, and verify
  the documented exit codes, accepted status, report path, and revision-2
  continuation output.

**Exit Criteria:**
- A new user can complete the documented local path without provider
  authentication, and an experienced contributor can identify every extension
  owner without guessing.

### Task 4: Author documentation navigation

**Purpose:**
- Make the seven canonical pages discoverable without duplicating their content.

**Task Function:**
- Documentation navigation.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers `docs/README.md` as a navigation-only owner.

**Required Skills:**
- None beyond the plan’s documentation ownership rules.

**Files And Symbols:**
- Create `docs/README.md`.

**Dependencies:**
- Tasks 1–3.

**Authority:**
- Preauthorized: add links and one-sentence audience descriptions only.
- Stop for: copying conceptual, configuration, or command reference content
  into the index.

**Steps:**
1. Add sections for New Users, Understanding ForesightOS, Configuration and
   Evidence, and Extending ForesightOS.
2. Link all six canonical content pages with repository-relative paths.
3. Link the historical `docs/intent/`, `docs/superpowers/plans/`, and
   `docs/superpowers/evidence/` locations as records, not onboarding material.

**Verification:**
- Confirm exactly seven canonical page links with `rg -n "getting-started|architecture|skills|evidence-and-evaluation|configuration|extending" docs/README.md`.

**Exit Criteria:**
- `docs/README.md` is navigational and contains no duplicated technical rules.

### Task 5: Reduce and reconcile the root README

**Purpose:**
- Make the README a concise product front door that routes users to canonical
  documentation.

**Task Function:**
- User-facing entry-point consolidation.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers the verdict’s 150–250 line target, stale-claim cleanup, and README
  ownership boundary.

**Required Skills:**
- `skill-code-standards`.

**Files And Symbols:**
- Modify `README.md` only after Tasks 1–4 are complete.

**Dependencies:**
- Tasks 1–4.

**Authority:**
- Preauthorized: rewrite README content and links within the approved scope.
- Stop for: unrelated runtime changes, new provider claims, or a README longer
  than 250 lines without a documented source-backed reason.

**Steps:**
1. Keep the title, one-sentence value proposition, Why ForesightOS, key
   capabilities, architecture-at-a-glance, quickstart, short verification
   status, documentation link, and development command.
2. Keep concise capability summaries for XLSX, web/MCP, Power BI metadata, and
   optional Canva rendering; link details to the canonical pages.
3. Remove duplicated scheduled-evidence text, exhaustive skill descriptions,
   provider setup, detailed benchmark instructions, and internal governance.
4. Replace obsolete unresolved Group Chat wording with the current verified
   local status, while preserving explicit `BLOCKED_EXTERNAL` boundaries.
5. Ensure the README does not claim a console entry point that `pyproject.toml`
   does not provide.

**Verification:**
- `((Get-Content README.md).Count -ge 150) -and ((Get-Content README.md).Count -le 250)`
- `rg -n "scheduled-evidence|p95 unresolved|AGENTS|CoS|Project OS" README.md` must return no user-facing documentation matches.
- `rg -n "docs/README.md|getting-started.md|architecture.md|skills.md|evidence-and-evaluation.md|configuration.md|extending.md" README.md`

**Exit Criteria:**
- README is a navigable front door, not a duplicate reference manual.

### Task 6: Add local Markdown-link validation

**Purpose:**
- Prevent broken local links without adding a documentation platform.

**Task Function:**
- Lightweight repository documentation validation.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers the verdict’s single-documentation-automation recommendation.

**Required Skills:**
- `skill-test-driven-development`.

**Files And Symbols:**
- Create `scripts/check_markdown_links.py`.
- Create `tests/test_markdown_links.py`.

**Dependencies:**
- Tasks 1–5.

**Authority:**
- Preauthorized: local filesystem reads and deterministic test fixtures.
- Stop for: network fetching, link-checker dependency installation, or mutation
  of documentation content from the checker.

**Steps:**
1. Support positional Markdown paths plus a `--tracked-docs` switch. Scan the
   explicit target set: `README.md`, `docs/README.md`,
   `docs/getting-started.md`, `docs/architecture.md`, `docs/skills.md`,
   `docs/evidence-and-evaluation.md`, `docs/configuration.md`,
   `docs/extending.md`, plus all remaining tracked `docs/**/*.md` files.
   The explicit canonical list is mandatory so new pages are checked before
   they are added to the Git index.
2. Parse Markdown inline links and reference links using the standard library.
3. Ignore `http`, `https`, `mailto`, and fragment-only links; resolve relative
   repository paths from the linking file’s directory.
4. Report each missing local target with source file and line number, and return
   nonzero when any target is missing.
5. Add tests covering a valid relative link, a missing relative link, a valid
   fragment-only link, ignored external links, and an untracked canonical-page
   fixture passed through the explicit target list.

**Verification:**
- `python scripts/check_markdown_links.py README.md docs/README.md docs/getting-started.md docs/architecture.md docs/skills.md docs/evidence-and-evaluation.md docs/configuration.md docs/extending.md --tracked-docs`
- `python -m pytest -q tests/test_markdown_links.py`

**Exit Criteria:**
- The checker passes on the repository and has no network or third-party
  dependency.

### Task 7: Perform final documentation verification

**Purpose:**
- Prove the documentation consolidation is complete and has not changed runtime
  behavior or expanded scope.

**Task Function:**
- Final source-backed documentation and repository verification.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers all acceptance criteria and the final reconciliation boundary.

**Required Skills:**
- `skill-verification-before-completion`, `skill-code-standards`.

**Files And Symbols:**
- Review all files in the target list, `pyproject.toml`, `.env.example`,
  `src/foresight_os/cli.py`, `src/foresight_os/skills/manifest.json`,
  `evaluation/`, `tests/test_skills.py`, `tests/test_evaluation_contract.py`,
  `tests/test_capabilities.py`, `tests/test_presentation_spec.py`,
  `tests/test_vertical_slice.py`, this plan file, and the final Git diff.

**Dependencies:**
- Tasks 0–6.

**Authority:**
- Preauthorized: local tests, link checks, source inspection, diff review, and
  updates to this plan’s status and ledger fields.
- Stop for: broken links, stale source-derived claims, any runtime diff,
  unapproved file changes, or failed tests.

**Steps:**
1. Run the focused documentation-link tests and checker.
2. Run the full test suite and compile check.
3. Review README line count, headings, canonical links, and removed stale text.
4. Review every new page against its source ownership map and verify no exact
   environment, CLI, skill, schema, or benchmark inventory was duplicated.
5. Run `git diff --check` and `git status --short --branch`.
6. Set this plan to `completed` only after all mandatory commands pass and the
   diff contains only the approved documentation scope.

**Verification:**
- `python scripts/check_markdown_links.py README.md docs/README.md docs/getting-started.md docs/architecture.md docs/skills.md docs/evidence-and-evaluation.md docs/configuration.md docs/extending.md --tracked-docs`
- `python -m pytest -q tests/test_markdown_links.py`
- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `git diff --check`
- `git status --short --branch`

**Exit Criteria:**
- All acceptance criteria pass, no runtime behavior changes are present, and
  the final plan status and Git evidence agree.

## Final Handoff

The implementation is complete when the repository contains one product
front-door README, seven canonical user-facing Markdown pages, unchanged
historical plan/evidence records, and one deterministic local-link checker.
The change must not claim provider-backed or human-quality evidence that is not
present in durable receipts.

The intended delivery commit message is:

```text
docs: consolidate user documentation and simplify README
```

### Coordination Log

- Bootstrap: branch `codex/documentation-consolidation`; base `origin/main` at `391e92b`; initial worktree HEAD `391e92b`; workspace `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\documentation-consolidation\foresight-OS`.
- Task 0 baseline: inspected `pyproject.toml`, `src/foresight_os/cli.py`, vertical-slice and recovery paths, controller skill registry, packaged manifest, runtime capabilities/provider configuration, evaluation contracts, artifact boundaries, and related tests. No runtime changes are authorized.
- Task 7 final verification: `python scripts/check_markdown_links.py ... --tracked-docs`, `python -m pytest -q`, `python -m compileall -q src tests evaluation`, and `git diff --check` all passed. The documented quickstart independently returned accepted revision `1`, generated `artifacts/executive-report.md`, and continued to revision `2` with reassessment ID `claim-northern-demand-growth`. Disposable verification outputs were removed; final status is clean.
