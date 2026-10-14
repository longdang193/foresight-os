---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: foresight-os-readme-showcase
targets:
  - README.md
  - docs/assets/foresight-os-flow.json
  - docs/assets/foresight-os-flow.html
  - docs/assets/foresight-os-flow.svg
  - docs/assets/technology-radar-flagship.svg
  - docs/superpowers/plans/2026-10-14-1349-foresight-os-readme-showcase-plan.md
---

# ForesightOS README Showcase

## Verdict Review

The supplied verdict is directionally correct and is adopted with three
implementation constraints:

1. Technology Radar is the flagship example because the repository already has
   a deterministic fixture, accepted workflow, scenarios, action categories,
   signposts, review state, and report output for it.
2. The README uses `traceable`, `evidence-grounded`, and `reviewable` rather
   than claiming formal “auditable AI”. Existing maturity and evidence limits
   remain visible, but move after the value proposition.
3. The promotion layer stays deliberately small: one README, one Archify flow
   visual, one real Technology Radar visual, and one reproducible flagship
   exercise. The Archify HTML is a linked interactive companion to the static
   README visual, not a separate product surface. The README does not promise
   that GitHub will execute the HTML; readers are told to download and open it
   locally. No marketing site, hosted demo, benchmark dashboard, or second
   promotional pipeline is introduced.

The README remains a product front door, not a replacement for the maintained
technical pages. Source code, tests, fixtures, `docs/`, and evaluation records
remain authoritative. This plan changes no runtime behavior, skill procedure,
provider integration, external destination, or analytical contract.

## Goal

Reposition the root README from an infrastructure-first overview to a concise
showcase of ForesightOS as an evidence-grounded strategic decision-support
system. A new visitor should understand the strategic problem, the product
answer, one convincing real example, and the boundaries of the evidence before
reaching the installation and architecture detail.

## Scope

### In scope

- Reorder and rewrite `README.md` around the strategic outcome and the
  evidence/review differentiator.
- Add one compact Archify strategic-foresight flow near the top of the README,
  with a GitHub-compatible static SVG, a linked interactive HTML artifact, and
  accessible text fallback.
- Add a comparison between a typical agent workflow and ForesightOS.
- Add a Technology Radar walkthrough sourced from the existing accepted local
  workflow and `tests/fixtures/exercise/04_Technology_Radar.xlsx`.
- Add the Archify flow source at `docs/assets/foresight-os-flow.json`, deliver
  it as `docs/assets/foresight-os-flow.html`, and export its canonical static
  SVG at `docs/assets/foresight-os-flow.svg` without hand-authoring a duplicate
  diagram. In the README, label the HTML as a downloadable local companion,
  not as an embedded or hosted viewer.
- Add one static `docs/assets/technology-radar-flagship.svg` snapshot derived
  from the accepted report; label it as a real generated artifact, not a mockup.
- Add a compact strategic foresight toolkit, coordination-as-enabler table,
  evidence-architecture explanation, and “Built to be checked” section.
- Preserve the working quickstart, canonical documentation links, maturity
  limits, provider boundaries, and truthful status vocabulary.
- Record exact suggested GitHub description and topic values as a handoff in the
  plan or PR notes without mutating external repository settings in this plan.

### Out of scope

- Runtime, CLI, schema, skill, manifest, fixture, evaluator, or test behavior.
- Rewriting the canonical pages under `docs/`; link to them instead.
- Adding a hosted demo, marketing site, docs platform, benchmark dashboard,
  badge system, video pipeline, or separate showcase repository.
- Adding a new runtime renderer, custom diagram renderer, hosted diagram
  service, or second source of analytical truth; Archify owns the flow source
  and generated HTML/SVG, while the Technology Radar SVG remains a release-
  style presentation snapshot only.
- Claiming model reasoning accuracy from structural or synthetic evaluation
  scores.
- Authenticating providers, publishing Canva designs, changing GitHub metadata,
  creating a release, or performing another external mutation without explicit
  approval and a separate execution step.

## Canonical Ownership Map

| Surface | Responsibility | Authority |
|---|---|---|
| `README.md` | Product front door, value proposition, showcase, quickstart, and links | Repository source and maintained `docs/` pages |
| `docs/assets/foresight-os-flow.json` | Canonical source for the README's strategic-foresight flow | Repository-backed workflow evidence plus Archify workflow schema v2 |
| `docs/assets/foresight-os-flow.html` | Delivered downloadable interactive flowchart companion | Archify `deliver` receipt for the checked JSON source |
| `docs/assets/foresight-os-flow.svg` | Static GitHub-compatible flowchart shown in the README | Canonical Archify SVG export from the delivered HTML |
| `docs/assets/technology-radar-flagship.svg` | One visual snapshot of the accepted flagship output | Generated Technology Radar report and fixture digest |
| Technology Radar analysis | Decision question, assessments, scenarios, signposts, recommendation, and review state | `src/foresight_os/analysis/technology_radar.py` |
| Technology Radar fixture | Reproducible source workbook | `tests/fixtures/exercise/04_Technology_Radar.xlsx` |
| Workflow proof | Accepted report and current `FindingView` state | `tests/test_technology_powerbi_validator.py` and `AnalysisStore` |
| Technical detail | Architecture, getting started, skills, evidence, configuration, and extension guidance | `docs/README.md` and linked pages |

The static SVG is not a canonical analytical output. It must include a source
note and fixture SHA-256 in its metadata or visible caption so a reviewer can
trace it back to the accepted report. The README must not reproduce the full
report, receipt schema, skill catalog, or provider configuration inventory. The
Archify JSON is the single source for the flowchart; the README embeds only its
static SVG, links the delivered HTML, and includes a concise text fallback.

## Execution Approach

- Mode: `inline sequential`.
- Coordination: `git-tracked` because the plan, generated visual, README, and
  source-derived validation need durable task checkpoints.
- Isolation: execute in a fresh task-specific worktree from the resolved
  `origin/main`; preserve the current dirty checkout and its untracked outputs.
- Write ownership: one lead owns the README and visual; the coordination owner
  alone updates this plan's status, ledger, and completion evidence.
- Shared-write rule: generate and validate the Archify flow and source-derived
  Technology Radar evidence before writing README claims; only the final task
  may mark the plan completed.
- External boundary: no authentication, publication, GitHub mutation, Canva
  mutation, or provider-backed evidence is required.
- Completion authority: final verification reconciles README claims, visual
  provenance, source links, tests, and the Git diff.

## Coordination State

- Coordination owner: one lead controller; no task agent changes plan status,
  acceptance criteria, dependencies, or historical records.
- Base expectation: `origin/main` at bootstrap; record the resolved base commit
  in the first execution checkpoint.
- Workspace expectation: fresh task-specific worktree; do not use the current
  dirty checkout for implementation.
- Plan bootstrap: copy this plan into the fresh worktree before Task 0, commit
  it as the first tracked plan artifact, and keep this path as the active plan.
- Checkpoints: create a native Git checkpoint after each accepted task boundary.
- Stop for: missing fixture or workflow proof, unsupported product claims,
  request for external mutation, or a need to change runtime behavior.

## Acceptance Criteria

1. The hero leads with “Evidence-grounded strategic foresight with traceable AI
   workflows” or an equivalent source-backed formulation, not the existing
   infrastructure-first “evidence-aware strategic reasoning prototype”.
2. The first screen communicates this flow in product terms through an Archify
   workflow diagram with at most 12 primary nodes: strategic question →
   decision framing → evidence and deterministic analysis → specialists and
   skills → challenge → scenarios and implications → recommendation → artifact
   → evidence change → selective reassessment. The source uses workflow schema
   v2 with `meta.quality_profile: "showcase"`, and the README provides both a
   static SVG and an accessible text fallback plus a link to the interactive
   HTML.
3. A visible differentiator table explains why ForesightOS is not merely a
   capable model or generic multi-agent framework.
4. The Technology Radar section identifies the real decision question, shows
   evidence and source-family adjustment, states the challenge/counterhypothesis,
   presents Invest/Experiment/Monitor action categories, and names signposts or
   disconfirmation conditions.
5. The showcase is backed by an accepted `run_technology_radar_workflow` result
   from the tracked fixture; the README does not invent values absent from that
   result.
6. The repository contains at most two new promotional visuals: the Archify
   flowchart (`foresight-os-flow.json`, delivered `.html`, and canonical `.svg`)
   and `docs/assets/technology-radar-flagship.svg`. The Technology Radar SVG
   visibly includes a recommendation, evidence or source reference,
   counterevidence or caveat, uncertainty/scenario context, and a monitoring or
   “what changes our mind” cue. Both visuals have accessible alternative text
   or fallback copy in the README, and the Archify outputs are traceable to
   delivery receipts.
7. The README contains a compact strategic foresight toolkit covering evidence,
   critical reasoning, uncertainty, decision support, governance, and
   communication without copying individual `SKILL.md` procedures.
8. Coordination patterns are framed as an enabler selected for the reasoning
   problem, with concise Direct, Sequential, Concurrent, Handoff, and Group
   Chat use cases rather than as the product headline.
9. The evidence architecture is expressed as a user benefit: recommendations
   remain connected to evidence, calculations, assumptions, counterevidence,
   reviews, relationships, and revision state.
10. “Built to be checked” separates deterministic runtime, contract/controller,
    XLSX, skill, reuse/invalidation, and performance evidence from provider
    reasoning quality and human strategic usefulness.
11. The existing five-minute quickstart remains runnable and moves below the
    value/showcase sections; canonical links to `docs/README.md` and maintained
    pages remain valid.
12. Maturity, prototype, optional-boundary, blocked-status, and evidence-limit
    language remains present under a later maturity/evidence-boundary section,
    not deleted from the README.
13. The README and visual introduce no external mutation, runtime behavior,
    analytical schema, or second maintenance owner.
14. Archify showcase validation and delivery, Archify browser evidence or an
     explicit unavailable-browser skip, focused Technology Radar tests, full
     tests, compilation, Markdown links, both SVG parses, whitespace validation,
     and final scope review pass. Any browser/runtime failure blocks acceptance;
     automated browser evidence and perceptual visual review are reported
     separately and truthfully.

## Suggested External Handoff

These values are prepared for a separately approved GitHub metadata action; the
README plan does not apply them automatically:

- Description: `Evidence-grounded strategic foresight with traceable AI workflows, deterministic analysis, adversarial review, and selective reassessment.`
- Topics: `strategic-foresight`, `decision-support`, `ai-agents`,
  `multi-agent-systems`, `microsoft-agent-framework`, `scenario-planning`,
  `xlsx-analysis`, `evidence-based-ai`, `python`.
- Do not add `rag` unless repository behavior and future positioning make it a
  central visitor expectation.
- Leave homepage empty until a genuinely useful destination exists.
- Consider a `v0.1.0` release only after the showcase state is stable and under a
  separate release approval.

## Task Breakdown

| Task | Status | Executor | Outcome | Dependencies | Accepted proof | Blocker | Next action |
|---|---|---|---|---|---|---|---|
| 0. Establish README and showcase baseline | completed | lead controller | Source-backed inventory completed; existing README, docs owners, Technology Radar fixture, and Archify requirements reconciled | None | source inventory complete | none | completed |
| 1. Generate and validate flow and flagship evidence | completed | lead controller | Archify workflow source, delivered HTML, exported SVG, accepted radar report, and source-derived flagship SVG created | Task 0 | 9/9 showcase checks, 0 errors, 0 warnings; browser containment pass; radar workflow accepted | none | completed |
| 2. Rewrite README as the product showcase | completed | lead controller | README now leads with the strategic problem, static flow, local interactive companion, radar visual, toolkit, evidence boundaries, quickstart, and docs | Tasks 0–1 | README link and content checks pass | none | completed |
| 3. Reconcile links, claims, and external handoff | completed | lead controller | Claims and links reconciled to source, fixture, report, and generated visual provenance; no external mutation performed | Tasks 1–2 | 23 Markdown paths checked; no external handoff requested | none | completed |
| 4. Perform final README delivery verification | completed | lead controller | Focused tests, full suite, compilation, SVG parsing, Markdown links, diff check, Archify delivery, and browser visual checks completed | Tasks 0–3 | focused tests pass; full suite pass; visual-check pass in light/dark viewports | none | completed |

### Task 0: Establish README and showcase baseline

**Purpose:**
- Prevent promotional copy from outrunning current product behavior or creating
  a second documentation owner.

**Task Function:**
- Repository documentation and source-evidence inventory.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers the verdict's positioning, Archify flow, Technology Radar flagship,
  source-backed promotion, and maintenance-minimization constraints.

**Required Skills:**
- `skill-code-standards`.

**Files And Symbols:**
- `README.md`, `docs/README.md`, `docs/getting-started.md`,
  `docs/architecture.md`, `docs/evidence-and-evaluation.md`.
- `src/foresight_os/analysis/technology_radar.py`:
  `analyze_technology_radar`, `run_technology_radar_workflow`,
  `render_technology_report`.
- `tests/fixtures/exercise/04_Technology_Radar.xlsx` and
  `tests/test_technology_powerbi_validator.py`.
- Existing tracked image/SVG assets and `scripts/check_markdown_links.py`.
- Shared Archify skill inputs: `~/.agents/skills/archify/schemas/workflow.schema.json`,
  `~/.agents/skills/archify/schemas/common.schema.json`, one workflow example,
  `~/.agents/skills/archify/references/delivery-contract.md`, and
  `~/.agents/skills/archify/references/viewer-runtime.md` for the canonical SVG
  export path.

**Dependencies:**
- None.

**Authority:**
- Preauthorized: read-only source inspection, test inspection, and temporary
  local workflow execution.
- Stop for: missing fixture, rejected workflow status, absent report sections,
  or a claim that cannot be tied to an authoritative source.

**Steps:**
1. Record the current README section order, quickstart commands, links, status
   vocabulary, maturity language, and implementation-first explanations.
2. Confirm the technical detail already owned by the linked docs and list only
   the README-facing summaries that need to remain.
3. Inspect the Technology Radar fixture, analyzer, renderer, and test assertions.
4. Confirm the repository has no existing visual asset to reuse and that adding
   one SVG snapshot is smaller than adding a renderer or demo pipeline.
5. Record the source-derived claims and the exact provenance required for the
   visual and README walkthrough in this plan's execution log.

**Verification:**
- `Get-Content README.md` and `rg -n` source ownership checks.
- `rg -n 'technology|radar|action_category|Signposts|FindingView' src tests docs`.
- `rg --files -g '!work/**' | rg '\.(png|jpg|jpeg|webp|svg)$'`.

**Exit Criteria:**
- The lead can identify every README claim's source, the existing showcase
  workflow, the two permitted visual outputs, and the Archify source/delivery
  boundary without adding new behavior.

### Task 1: Generate and validate the flow and flagship evidence

**Purpose:**
- Produce the source-backed Archify flow and one real, accepted Technology Radar
  result before writing promotional claims or visual content.

**Task Function:**
- Archify workflow authoring, deterministic artifact delivery, and flagship-artifact
  provenance reconciliation.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers acceptance criteria 2, 4–6 and the verdict's “real output” requirement.

**Required Skills:**
- `skill-code-standards`.
- `skill-verification-before-completion`.
- `archify`.

**Files And Symbols:**
- Read the repository workflow authority in `docs/`, `src/`, and `tests/` plus
  the Archify workflow schema, common schema, one matching example, and delivery
  contract from `~/.agents/skills/archify`.
- Create `docs/assets/foresight-os-flow.json`, deliver
  `docs/assets/foresight-os-flow.html`, and export
  `docs/assets/foresight-os-flow.svg` from the delivered Archify artifact.
- Create `docs/assets/technology-radar-flagship.svg` and temporary reports,
  receipts, screenshots, or browser sidecars only under the existing ignored
  `.tmp-tests/readme-showcase/` directory or a system temporary directory.
  Verify the chosen path with `git check-ignore` before generation. If the
  delivery contract writes sidecars beside the checked HTML, move the evidence
  into the ignored directory and remove the sidecars before handoff.

**Dependencies:**
- Task 0.

**Authority:**
- Preauthorized: local Archify validation/delivery, canonical SVG export,
  fixture execution, temporary report generation, and creation of the two named
  visual outputs.
- Stop for: any provider requirement, non-accepted result, missing review state,
  Archify validation or delivery failure, unsupported claim, or request for a
  third visual/pipeline.

**Steps:**
1. Freeze the repository-backed flow as a readable main path with at most 12
   primary nodes: strategic question → decision framing/wayfinding → evidence
   and deterministic XLSX analysis → analytical skills/specialists → adversarial
   review → scenarios/implications → recommendation → report/presentation →
   evidence change → selective reassessment. Keep exception or blocked paths
   sparse and subordinate to the main path.
2. Resolve the active worktree root to `$repo`, then run the Archify commands
   from the shared skill root `~/.agents/skills/archify`. Author
   `$repo/docs/assets/foresight-os-flow.json` with `schema_version: 2`,
   `diagram_type: "workflow"`, `meta.quality_profile: "showcase"`, stable
   domain-specific IDs, accessible labels, and no claims not supported by the
   repository. Run the Archify validator after each candidate edit:
   `node bin/archify.mjs validate workflow "$repo/docs/assets/foresight-os-flow.json" --quality showcase --json`.
3. Freeze the final candidate only after showcase validation reports 9/9 checks,
   zero composition errors, and zero warnings. Deliver the exact source with:
   `node bin/archify.mjs deliver workflow "$repo/docs/assets/foresight-os-flow.json" "$repo/docs/assets/foresight-os-flow.html" --quality showcase --json`.
4. Run `node bin/archify.mjs visual-check "$repo/docs/assets/foresight-os-flow.html" --json`
   after successful delivery. Record the specification/artifact hashes,
   `browser_evidence`, and truthful `visual_review` status separately; do not
   claim perceptual review from deterministic or browser receipts alone. Move
   any receipt, PNG, or contact-sheet sidecars needed for evidence into
   `.tmp-tests/readme-showcase/`, then remove unapproved sidecars from
   `docs/assets/` before the README task starts. Exit 1 or any runtime/capture
   failure blocks acceptance; exit 2 is an allowed unavailable-browser skip
   only when the final handoff records it explicitly.
5. Use Archify's canonical dual-theme SVG export from the delivered HTML (or its
   packaged export helper when available) to create
   `docs/assets/foresight-os-flow.svg`; do not hand-author a second flowchart
   source or visually edit the export. Keep the README's static image and
   interactive link bound to the same delivered source.
6. Run `run_technology_radar_workflow` with `human_decision="ACCEPT"` against
   the tracked fixture in a temporary `AnalysisStore`.
7. Require `status == "accepted"`, an existing report, all expected report
   sections (`Signal quality`, `Competing hypotheses`, `Alternative futures`,
   `Action category`, `Signposts`), and accepted current finding views.
8. Capture the fixture SHA-256, decision question, horizon, action categories,
   recommendation, caveat/counterhypothesis, scenario cue, and signposts from
   the generated report/result. Use current generated values, not hardcoded
   marketing claims, if the fixture changes before execution.
9. Create one accessible static SVG snapshot showing the flagship decision,
   action categories, evidence/review cues, and reassessment signposts. Embed
   the source fixture digest and generation note in SVG metadata or caption.
10. Review both visuals textually and visually for legibility, unsupported
    claims, clipping, and a clear distinction between generated evidence and
    illustration.

**Verification:**
- Archify validation proves 9/9 showcase checks with zero errors and warnings;
  the delivery receipt records specification and artifact SHA-256 values.
- The Archify `visual-check` receipt is artifact-bound and reports browser
  evidence as `passed`, `failed`, or `skipped` without being conflated with
  perceptual review.
- A temporary Python invocation proves accepted status, report existence,
  required sections, and current accepted `FindingView` records.
- `python -c "import xml.etree.ElementTree as ET; ET.parse('docs/assets/foresight-os-flow.svg')"`.
- `python -c "import xml.etree.ElementTree as ET; ET.parse('docs/assets/technology-radar-flagship.svg')"`.
- Compare every visible Archify flow label with the repository-backed flow and
  every Technology Radar SVG value and label with the generated report/result.

**Exit Criteria:**
- The Archify JSON, delivered HTML, and canonical SVG are one source-traceable,
  readable flowchart with no new runtime or renderer code, and
  `docs/assets/technology-radar-flagship.svg` is a source-traceable, readable
  snapshot of an accepted Technology Radar workflow.

### Task 2: Rewrite README as the product showcase

**Purpose:**
- Make the strategic problem and ForesightOS outcome clear before exposing
  implementation detail.

**Task Function:**
- Product-facing README revision with source-backed technical summaries.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers acceptance criteria 1–3 and 7–12.

**Required Skills:**
- `skill-code-standards`.

**Files And Symbols:**
- Write `README.md` only; link to existing `docs/` pages rather than rewriting
  them.
- Reference `docs/assets/foresight-os-flow.svg` with accessible alt text, a
  concise text fallback, and a link explicitly labelled as a downloadable local
  HTML companion; do not describe the HTML as a GitHub-hosted viewer.
- Reference `docs/assets/technology-radar-flagship.svg` with accessible alt text
  and a source/provenance caption.

**Dependencies:**
- Tasks 0–1.

**Authority:**
- Preauthorized: README copy, section order, tables, diagrams-as-text, and
  links to the named local asset and maintained docs.
- Stop for: new runtime claims, invented benchmark results, missing source
  evidence, or a need to edit canonical technical pages.

**Steps:**
1. Replace the opening with the approved traceable strategic-foresight
   positioning and a concise outcome-oriented subheadline.
2. Add the Archify static flow before the quickstart, link
   `docs/assets/foresight-os-flow.html` as “Download the interactive flowchart
   (open locally)”, and provide a concise text fallback for readers who cannot
   render images or open the artifact. Keep technical object names for the
   later architecture section. State that GitHub displays the HTML as a file;
   readers must download it and open it locally for the interactive viewer.
3. Add the visible “What makes ForesightOS different” comparison using only
   repository-backed distinctions: evidence/review attachment, versioned
   skills, task-shaped coordination, deterministic spreadsheet analysis,
   invalidation/selective reassessment, explicit blocked statuses, and
   revision-linked artifacts.
4. Add “See it in action: Technology Radar” with the generated visual, decision
   question, five action categories or grouped actions, counterhypothesis,
   scenarios, signposts, and a provider-free reproducible command using the
   tracked fixture. Publish this exact command, changing only line wrapping:

   ```powershell
   python -c "from pathlib import Path; from foresight_os.analysis.technology_radar import run_technology_radar_workflow; from foresight_os.domain.challenge import derive_finding_views; from foresight_os.persistence.analysis_store import AnalysisStore; r=run_technology_radar_workflow(AnalysisStore(Path('.tmp-tests/readme-showcase/radar-case')), Path('tests/fixtures/exercise/04_Technology_Radar.xlsx'), human_decision='ACCEPT'); report=r.report_path.read_text(encoding='utf-8') if r.report_path else ''; assert r.status == 'accepted' and r.report_path and r.report_path.exists() and all(item.accepted for item in derive_finding_views(r.analysis)) and all(section in report for section in ['Signal quality', 'Competing hypotheses', 'Alternative futures', 'Action category', 'Signposts']); print(f'{r.status}: {r.report_path}')"
   ```

   Link the command to the fixture/workflow context and explain that it writes
   only to the existing ignored `.tmp-tests/readme-showcase/` directory.
5. Add the compact strategic foresight toolkit and describe orchestration as an
   enabler with the five concise pattern use cases.
6. Add the user-benefit evidence architecture and “Built to be checked” table,
   explicitly separating structural proof from provider reasoning quality and
   human strategic usefulness.
7. Move the existing quickstart, architecture detail, maturity/evidence
   boundaries, documentation links, and development checks into the revised
   order without changing their runnable commands or truthful limitations.
8. Add one restrained technology line only if every named dependency remains
   present in `pyproject.toml` or the documented boundary; do not add a logo
   wall or unsupported product badge.

**Verification:**
- Read the complete README as a new visitor and as a contributor.
- Run the exact published Technology Radar command from the repository root and
  confirm it prints `accepted`, creates a report, and leaves accepted finding
  views in the isolated output directory.
- Confirm the flow link is labelled for local download/opening and does not
  promise GitHub-hosted HTML execution.
- `rg -n 'auditable AI|100%|reasoning accuracy|prototype|BLOCKED_EXTERNAL|not_measured|Technology Radar|Built to be checked' README.md`.
- Compare quickstart commands and documentation links with their owning files.

**Exit Criteria:**
- README is a concise, source-backed showcase with the strategic value first,
  the Technology Radar proof visible, and technical detail deferred to its
  canonical pages.

### Task 3: Reconcile links, claims, and external handoff

**Purpose:**
- Catch stale links, overclaims, visual drift, and accidental external scope
  before final acceptance.

**Task Function:**
- Documentation claim, provenance, and external-boundary reconciliation.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers acceptance criteria 5, 10–13 and the verdict's GitHub-surface advice.

**Required Skills:**
- `skill-code-standards`.
- `skill-verification-before-completion`.

**Files And Symbols:**
- `README.md`, `docs/assets/foresight-os-flow.json`,
  `docs/assets/foresight-os-flow.html`, `docs/assets/foresight-os-flow.svg`,
  `docs/assets/technology-radar-flagship.svg`,
  `docs/README.md`, linked `docs/*.md`, `pyproject.toml`, and the generated
  temporary Technology Radar report.
- The exact GitHub description/topics in this plan's Suggested External
  Handoff; no GitHub API or browser mutation.

**Dependencies:**
- Task 2.

**Authority:**
- Preauthorized: local link checks, source comparison, copy correction, and
  recording the metadata handoff.
- Stop for: a required GitHub setting change, release creation, provider
  authentication, or any unresolved factual claim.

**Steps:**
1. Check every new README link and JSON, HTML, and SVG path against the local
   repository; confirm the static flow and linked HTML come from the same
   Archify source.
2. Reconcile all numeric, status, action, and technology claims with source
   code, tests, fixture output, and generated visual provenance.
3. Confirm the README does not imply that structural evaluation proves model
   reasoning quality or human strategic usefulness.
4. Confirm the flowchart link is explicitly a local download/open instruction,
   not a promise that GitHub executes the HTML, and that the published
   Technology Radar command is the exact provider-free command tested in Task 2.
5. Confirm the external description/topics are ready for a separately approved
   GitHub action, but do not apply them during this README change.

**Verification:**
- `python scripts/check_markdown_links.py README.md --tracked-docs`.
- `git grep -n -e 'auditable AI' -e '100% AI' -e 'reasoning accuracy' -- README.md` returns no overclaim.
- `git diff --check`.

**Exit Criteria:**
- All README claims and links are source-backed, both visuals are traceable,
  Archify receipts are preserved as execution evidence, and external metadata
  is documented only as a gated handoff.

### Task 4: Perform final README delivery verification

**Purpose:**
- Prove the showcase change is complete, narrow, reproducible, and behaviorally
  safe.

**Task Function:**
- Final documentation verification and Git-scope reconciliation.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers all acceptance criteria and final completion evidence.

**Required Skills:**
- `skill-verification-before-completion`.
- `skill-code-standards`.

**Files And Symbols:**
- `README.md`, the Archify flow source and generated artifacts,
  `docs/assets/technology-radar-flagship.svg`, this plan, source, tests,
  evaluation, and final Git diff.

**Dependencies:**
- Tasks 0–3.

**Authority:**
- Preauthorized: local tests, Archify validation/delivery/browser checks,
  compilation, link checks, SVG parsing, diff review, and plan-status updates.
- Stop for: failed checks, runtime diff, unapproved asset proliferation,
  broken quickstart, external mutation, or untracked implementation files.

**Steps:**
1. Run the focused Technology Radar test module and the full test suite.
2. Re-run the final Archify validation and delivery checks from the committed
   flow source, then run compilation, Markdown-link, SVG-parse, and whitespace
   checks.
3. Inspect the final README, Archify HTML/SVG, and Technology Radar visual
   together at normal reading size; report automated browser evidence and
   perceptual review independently.
4. Confirm the diff contains only `README.md`, the Archify source and generated
   artifacts, the Technology Radar SVG, this plan, and any explicitly approved
   generated documentation asset.
5. Confirm no runtime, fixture, evaluator, skill, provider, or canonical docs
   changed and preserve unrelated working-tree artifacts.
6. Treat Archify `visual-check` exit 1 or any runtime/capture failure as a
   blocker. Treat exit 2 with receipt status `skipped` as acceptable only when
   Chrome/Chromium is unavailable, the deterministic delivery checks pass, and
   the final handoff records `browser_evidence: skipped`; keep
   `visual_review` as skipped unless a capable visual reviewer actually inspects
   the artifact. Mark the plan `completed` only after every required proof
   passes or this explicitly permitted unavailable-browser condition is
   recorded.

**Verification:**
- `python -m pytest -q tests/test_technology_powerbi_validator.py`.
- `python -m pytest -q`.
- `python -m compileall -q src tests evaluation`.
- `python scripts/check_markdown_links.py README.md --tracked-docs`.
- From `~/.agents/skills/archify`, after setting `$repo` to the active worktree root: `node bin/archify.mjs validate workflow "$repo/docs/assets/foresight-os-flow.json" --quality showcase --json`.
- From `~/.agents/skills/archify`, after setting `$repo` to the active worktree root: `node bin/archify.mjs deliver workflow "$repo/docs/assets/foresight-os-flow.json" "$repo/docs/assets/foresight-os-flow.html" --quality showcase --json`.
- From `~/.agents/skills/archify`, after setting `$repo` to the active worktree root: `node bin/archify.mjs visual-check "$repo/docs/assets/foresight-os-flow.html" --json`; preserve evidence in the existing ignored `.tmp-tests/readme-showcase/` directory and clean sidecars from `docs/assets/`.
- `python -c "import xml.etree.ElementTree as ET; ET.parse('docs/assets/foresight-os-flow.svg')"`.
- `python -c "import xml.etree.ElementTree as ET; ET.parse('docs/assets/technology-radar-flagship.svg')"`.
- `git diff --check`.
- `git status --short --branch`.
- `git diff --stat origin/main...HEAD`.
- `git diff --name-only origin/main...HEAD` contains only the approved targets.

**Exit Criteria:**
- The root README immediately explains the strategic problem and ForesightOS
  answer, shows the checked Archify flow and one real traceable Technology Radar
  output, preserves honest evidence boundaries and runnable onboarding, and
  introduces no new product behavior or maintenance system.

## Final Handoff

The intended delivery changes are limited to:

- the revised product-facing `README.md`;
- one Archify workflow source at `docs/assets/foresight-os-flow.json`;
- one delivered interactive flowchart at `docs/assets/foresight-os-flow.html`;
- one canonical static flowchart export at `docs/assets/foresight-os-flow.svg`;
- one source-derived `docs/assets/technology-radar-flagship.svg`; and
- this tracked implementation plan.

Suggested commit message:

```text
docs: add Archify flow to ForesightOS README showcase
```
