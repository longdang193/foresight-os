---
layer: change
artifact_type: plan
status: active
template_id: implementation-plan
name: foresight-os-agents-contract-consolidation
targets:
  - AGENTS.md
  - CLAUDE.md
  - GEMINI.md
  - docs/superpowers/plans/2026-10-14-1305-foresight-os-agents-contract-consolidation-plan.md
---

# ForesightOS Agent Contract Consolidation

## Verdict Review

The supplied verdict is accepted with one explicit user-directed change:
`CLAUDE.md` and `GEMINI.md` will be removed rather than retained as five-line
adapter stubs. The repository currently contains three byte-identical copies of
the same starter-kit contract, and repository search found no tracked sync
script or consumer that requires the two adapter filenames. Keeping them would
preserve duplicate maintenance without adding ForesightOS-specific behavior.

The verdict's main refinement is correct: the repository-level `AGENTS.md`
should be a compact ForesightOS delta, not a general engineering handbook.
Global agent behavior remains outside this repository. This plan does not edit
global instructions, credentials, runtime code, or documentation content except
where a verification step identifies a stale reference to the removed files.

The existing `AGENTS.md` header claims that the file is generated from a
canonical source, but the current repository contains no tracked
`sync_agent_adapters.py` or second tracked source for that content. Task 0 must
confirm that provenance in the execution worktree. If no canonical source is
found there, the root `AGENTS.md` becomes the single tracked project contract;
the inaccurate starter-kit/generation preamble is removed rather than
preserved.

## Scope

### In scope

- Replace the root `AGENTS.md` with a 70–100 line ForesightOS-specific
  contract.
- Preserve only project-specific purpose, foresight process, architecture
  invariants, canonical owners, change rules, verification requirements,
  documentation ownership, external boundaries, and maintenance bias.
- Remove `CLAUDE.md` and `GEMINI.md` from the repository.
- Search tracked repository references and maintained configuration for stale
  references to the removed adapter files or the absent sync generator.
- Verify the resulting contract and deletion without changing runtime behavior.

### Out of scope

- Editing `~/.codex/AGENTS.md`, `~/.agents/skills`, or any global instruction
  surface.
- Adding replacement `CLAUDE.md` or `GEMINI.md` stubs.
- Reintroducing Project OS, CoS, Herdr, DeepAgents, dcode, profile-selection,
  memory, generic Git, worktree, browser, frontend, backend, or MCP-governance
  instructions into the repository contract.
- Moving methodology from skill files into `AGENTS.md`.
- Runtime, CLI, schema, evaluation, provider, packaging, or documentation
  behavior changes.
- Rewriting historical plans or evidence records.

## Canonical Ownership

| Owner | Responsibility |
|---|---|
| `AGENTS.md` | Compact ForesightOS project contract for repository changes |
| `README.md` | Product entry point and concise capability overview |
| `docs/README.md` | User documentation navigation |
| `docs/getting-started.md` | Normal local usage |
| `docs/architecture.md` | Architecture and execution semantics |
| `docs/skills.md` | Skill and capability model |
| `docs/evidence-and-evaluation.md` | Evidence, status, and evaluation semantics |
| `docs/configuration.md` | Environment and provider configuration |
| `docs/extending.md` | Extension procedures |
| `docs/intent/` | Durable design intent |
| `docs/superpowers/plans/` | Historical and active implementation plans |
| `docs/superpowers/evidence/` | Durable verification evidence |
| Source, tests, manifests, and schemas | Executable and structural truth |

`AGENTS.md` may link to these owners but must not duplicate their complete
procedures, inventories, or private governance.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Isolation: execute in a fresh task-specific worktree from the resolved
  `origin/main`; preserve the current dirty checkout and its untracked outputs.
- Write ownership: one lead owns `AGENTS.md`, the two deletions, and this
  plan's task ledger; no parallel writer is needed.
- External boundary: no authentication, publication, provider call, or external
  mutation is required.
- Completion authority: final verification reconciles the contract, deleted
  files, repository references, and Git diff.

## Coordination State

- Coordination owner: one lead controller; only the lead changes plan status,
  task dependencies, acceptance criteria, or historical records.
- Bootstrap: resolve the execution base commit and create a fresh worktree
  before editing the contract. Because this plan is currently untracked, copy
  only this approved plan into the execution worktree, verify its content hash,
  and create the initial Git checkpoint containing the plan before Task 1. Do
  not copy any other untracked checkout artifacts. Record the execution branch,
  base commit, workspace path, initial HEAD, and checkpoint commit in this plan
  before Task 1.
- Checkpoints: create a native Git checkpoint after each accepted task boundary.
- Plan status transition: `proposed` → `active` at bootstrap; `active` →
  `completed` only after final verification returns verified evidence.
- Stop condition: if execution discovers a real canonical generator/source for
  `AGENTS.md`, stop before editing and update the plan to use that owner.

### Execution Log

- Plan review: `review-1` passed on review turn 2 of 2 after the three P2
  findings were incorporated.
- Execution branch: `codex/documentation-consolidation`.
- Base commit and initial HEAD: `4935beccba36eead81a4f35a9e67c85f7a691122`.
- Execution worktree:
  `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\documentation-consolidation\foresight-OS`.
- Approved-plan SHA-256: `51C092597C5724DC5721F4381B717A8D073CA7858E652F9A1F40CC98F57232DB`.
- Initial plan checkpoint commit: `740579dc16fee13f61151d1c295bac37e817958f`.
- Task 0 accepted: the three instruction files are byte-identical; no tracked
  generator or alternate canonical source exists; all filename/generator
  references are intentional records in this plan; and separate `--follow`
  history checks resolve to the same original starter-kit commit.
- Task 1 accepted: `AGENTS.md` is now a 70-line ForesightOS-specific contract
  with all nine required sections and no generic handbook terms.
- Task 2 accepted: `CLAUDE.md` and `GEMINI.md` are deleted; the remaining
  filename and generator mentions are intentional plan records only, with no
  source, script, configuration, or maintained-document dependency.

## Acceptance Criteria

1. `AGENTS.md` is between 70 and 100 lines and contains only ForesightOS
   project-specific instructions.
2. The contract has the nine sections: Project Purpose, Foresight Process,
   Architecture Invariants, Canonical Owners, Change Rules, Verification
   Requirements, Documentation Ownership, External Boundaries, and Maintenance
   Bias.
3. The process preserves decision-first reasoning, provenance, deterministic
   analysis, distinct observations/assumptions/interpretations/recommendations,
   uncertainty, counterevidence, proportional review, monitoring, and
   presentation truthfulness.
4. Execution-pattern selection remains separate from foresight process stages;
   direct, sequential, concurrent, handoff, and group chat remain coordination
   mechanisms selected by one controller.
5. The contract protects `AnalysisState`, NetworkX projections, `FindingView`,
   `ReviewRecord`, `StageReceipt`, `PresentationSpec`, and deterministic XLSX
   analysis as their existing owners without creating a second authority.
6. Change and verification rules require boundary proof, provenance and
   invalidation checks, source-preserving XLSX/calculation behavior, stale-review
   rejection, receipt reuse safety, and measured evidence for performance claims.
7. `CLAUDE.md` and `GEMINI.md` are deleted and no tracked file requires them.
8. No runtime, test, schema, provider, packaging, or user-documentation
   behavior changes are introduced by this work.
9. Focused repository checks, full tests, compilation, whitespace validation,
   and final scope review pass.

## Task Breakdown

| Task | Status | Executor | Outcome | Dependencies | Accepted proof | Blocker | Next action |
|---|---|---|---|---|---|---|---|
| 0. Establish contract provenance and baseline | completed | lead | Confirm `AGENTS.md` ownership, adapter-file references, and current line/content baseline | None | verified | none | rewrite canonical contract |
| 1. Rewrite the ForesightOS project contract | completed | lead | Compact repo-specific `AGENTS.md` with nine required sections and no generic governance | Task 0 | verified | none | delete duplicate adapters |
| 2. Remove duplicate adapter files and stale references | completed | lead | Delete `CLAUDE.md` and `GEMINI.md`; reconcile any tracked consumers | Tasks 0–1 | verified | none | run final verification |
| 3. Verify contract, deletion, and scope | active | lead | Fresh proof that only the approved instruction surfaces changed | Tasks 1–2 | pending | none | run focused and broad checks |

### Task 0: Establish contract provenance and baseline

**Purpose:**
- Prevent edits to a generated surface when a canonical source exists elsewhere.

**Task Function:**
- Repository instruction-surface inventory and source reconciliation.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers the verdict's generated-header concern and the deletion decision.

**Required Skills:**
- `skill-code-standards`.

**Files And Symbols:**
- Inspect `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `repo_config/`, `.github/`,
  `scripts/`, and tracked Markdown/configuration files.

**Dependencies:**
- None.

**Authority:**
- Preauthorized: read-only repository search and Git history inspection.
- Stop for: any discovered canonical generator/source outside the three root
  files, a required adapter consumer, or a scope-changing instruction.

**Steps:**
1. Confirm the resolved base commit and fresh worktree.
2. Compare hashes and content of the three root instruction files.
3. Search tracked files for `CLAUDE.md`, `GEMINI.md`, `sync_agent_adapters`, and
   generated-surface references. Classify every match as an operational
   dependency, a stale active promise, this plan's intentional record, or
   pre-existing historical evidence; only the first two categories block
   deletion.
4. Inspect Git history for the origin of the generated preamble.
5. Record the result in this plan's coordination log. Treat root `AGENTS.md`
   as the canonical contract only when no other tracked source is found.

**Verification:**
- `git ls-files AGENTS.md CLAUDE.md GEMINI.md scripts repo_config .github`
- `git grep -n -e 'CLAUDE.md' -e 'GEMINI.md' -e 'sync_agent_adapters' -- ':!work/**'`
- `git log --follow -- AGENTS.md`
- `git log --follow -- CLAUDE.md`
- `git log --follow -- GEMINI.md`

**Exit Criteria:**
- The plan names the actual canonical owner and confirms whether deletion is
  safe without inventing a generator or adapter dependency.

### Task 1: Rewrite the ForesightOS project contract

**Purpose:**
- Replace starter-kit and generic governance text with the smallest contract
  needed to protect ForesightOS behavior.

**Task Function:**
- Canonical project instruction drafting.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers acceptance criteria 1–6 and the verdict's nine-section structure.

**Required Skills:**
- `skill-code-standards`.

**Files And Symbols:**
- Rewrite `AGENTS.md` only after Task 0 confirms it is the canonical tracked
  project contract.

**Dependencies:**
- Task 0.

**Authority:**
- Preauthorized: rewrite `AGENTS.md` within the approved section and line-count
  limits.
- Stop for: adding global agent policy, methodology procedures, or a second
  canonical owner.

**Steps:**
1. Remove the generated starter-kit preamble if Task 0 finds no generator or
   canonical source.
2. Add the nine required sections in this order: Project Purpose, Foresight
   Process, Architecture Invariants, Canonical Owners, Change Rules,
   Verification Requirements, Documentation Ownership, External Boundaries,
   Maintenance Bias.
3. State that one controller selects coordination patterns independently from
   analytical methods and specialist selection.
4. Name existing source owners exactly; link to maintained docs instead of
   copying their procedures or inventories.
5. Preserve explicit boundaries for credentials, external evidence, external
   mutation, Canva/rendering, provenance, sanitization, invalidation, and
   truthful blocked statuses.
6. Keep the resulting file between 70 and 100 lines and free of generic
   Project OS, Codex, CoS, Herdr, DeepAgents, dcode, memory, worktree,
   browser, frontend, backend, or MCP-governance instructions.

**Verification:**
- `Get-Content AGENTS.md | Measure-Object -Line`
- `rg -n 'Project OS|CoS|Herdr|DeepAgents|dcode|Context Cleaner|memory policy|worktree procedure|profile selection|generic Git|frontend rules|browser rules' AGENTS.md`
- `rg -n '^## ' AGENTS.md`

**Exit Criteria:**
- `AGENTS.md` is a compact, source-linked ForesightOS contract with no
  duplicated global handbook content.

### Task 2: Remove duplicate adapter files and stale references

**Purpose:**
- Eliminate identical maintenance copies now that `AGENTS.md` is the single
  tracked project contract.

**Task Function:**
- Repository instruction-surface cleanup.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers the explicit user direction to remove `CLAUDE.md` and `GEMINI.md`.

**Required Skills:**
- `skill-code-standards`.

**Files And Symbols:**
- Delete `CLAUDE.md`.
- Delete `GEMINI.md`.
- Update only tracked references discovered by Task 0; do not edit unrelated
  historical records or ignored `work/` artifacts.

**Dependencies:**
- Tasks 0–1.

**Authority:**
- Preauthorized: delete the two named root files and remove stale active
  references.
- Stop for: any consumer that requires a platform-specific file, or any need to
  publish/authenticate externally.

**Steps:**
1. Delete the two identical adapter files.
2. Re-run tracked search for their filenames and the absent generator name.
3. Confirm the root contract and maintained docs do not promise that adapter
   files exist.
4. Do not create replacement stubs; the absence is intentional and documented
   by the plan and Git diff.

**Verification:**
- `Test-Path CLAUDE.md; Test-Path GEMINI.md` must both be `False`.
- `git grep -n -e 'CLAUDE.md' -e 'GEMINI.md' -e 'sync_agent_adapters' -- ':!work/**'` returns no active references.

**Exit Criteria:**
- Only the canonical `AGENTS.md` remains at the repository root for project
  agent instructions.

### Task 3: Verify contract, deletion, and scope

**Purpose:**
- Prove the instruction cleanup is complete and has not changed product
  behavior or introduced hidden documentation drift.

**Task Function:**
- Final repository verification and Git-scope reconciliation.

**Template Profile:**
- `unresolved`; lead controller resolves through Planning Dispatch.

**Specification Coverage:**
- Covers all acceptance criteria and final completion evidence.

**Required Skills:**
- `skill-verification-before-completion`.
- `skill-code-standards`.

**Files And Symbols:**
- `AGENTS.md`, deleted root adapters, `README.md`, `docs/`, `repo_config/`,
  source, tests, and final Git diff.

**Dependencies:**
- Tasks 0–2.

**Authority:**
- Preauthorized: local search, tests, compilation, diff review, and plan-status
  updates.
- Stop for: broken references, runtime diff, unapproved file changes, or a
  failed required check.

**Steps:**
1. Validate line count and required headings in `AGENTS.md`.
2. Confirm adapter files are absent and no operational dependencies or stale
   active promises remain. References in this plan and pre-existing historical
   evidence are allowed only when the Task 0 inventory classifies them and they
   do not claim that the deleted files or generator are required.
3. Run `python scripts/check_markdown_links.py AGENTS.md README.md
   --tracked-docs` when that checker exists in the resolved base; otherwise run
   a deterministic local-link audit over `AGENTS.md`, `README.md`, and `docs/`.
4. Run the full test suite and compile check to prove no runtime behavior
   changed.
5. Run `git diff --check`, inspect staged/unstaged/untracked state, and confirm
   the diff contains only `AGENTS.md`, the two deletions, and this plan.
6. Mark the plan `completed` only after every required proof passes.

**Verification:**
- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- `git diff --check`
- `git status --short --branch`
- `git diff --stat origin/main...HEAD`
- `git grep -n -e 'CLAUDE.md' -e 'GEMINI.md' -e 'sync_agent_adapters' -- ':!work/**'`
  followed by the Task 0 classification check: remaining matches may only be
  this plan or pre-existing historical evidence, never source, scripts,
  configuration, or maintained documentation with an active dependency.

**Exit Criteria:**
- The repository has one compact ForesightOS agent contract, no duplicate
  adapter files, no stale active references, and no runtime behavior changes.

## Final Handoff

The intended delivery changes are limited to:

- a 70–100 line ForesightOS-specific `AGENTS.md`;
- deletion of `CLAUDE.md`;
- deletion of `GEMINI.md`; and
- this tracked implementation plan.

The intended commit message is:

```text
docs: consolidate ForesightOS agent instructions
```
