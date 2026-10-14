---
layer: change
artifact_type: plan
contract_version: "1"
status: completed
template_id: implementation-plan
name: foresight-execution-persistence
targets:
  - host execution procedure
  - approved execution gate
  - typed canonical result persistence
  - stage receipts and reload integrity
  - NCC execution proof
---

# Foresight Execution Persistence Implementation Plan

## Goal

Make approved investigation execution analytically truthful and recoverable by
adding a host-facing execution procedure and one generic typed persistence path.
An approved public run must not report analytical completion merely because the
runtime settled or produced transient outputs. It must validate stage results,
persist them through `AnalysisStore`, verify provenance and hashes, make a
stage eligible for the existing workflow to write `StageReceipt` only after
durable state exists, and report requested deliverable completion separately
from runtime settlement. A receipt proves what was durably persisted, not that
a conclusion is correct. The existing low-level `run_recipe_async()` path
remains permissive for probes and tests, and cross-process pause/cancel remains
deferred. Infrastructure repair may unblock execution but is never a
substitute for completing the approved analytical work.

## Implementation Outcomes

### Host execution lifecycle is explicit

Add `.agents/skills/foresight-execution/SKILL.md` and routing guidance that
clearly separates Wayfinding, execution approval, approved execution,
analytical acceptance, and final deliverable assessment. The host procedure
defines preflight requirements, truthful failure classes, the hard completion
rule, approval-fingerprint handling, and the boundary between runtime status
and persisted analytical status without changing the participant skill
registry.

### Approved execution has one canonical persistence path

Implement a versioned `analysis-stage-result/v1` producer/consumer boundary
under `src/foresight_os/analysis/` that reuses existing domain models and
`AnalysisStore` as the single source of truth. Approved public execution binds
the contract to the approved recipe and configures structured output before any
provider work, persists validated stage state incrementally, verifies references
and hashes, and returns a verified result that makes the existing workflow's
receipt write eligible. Arbitrary model prose, malformed references, unknown
provenance, invalid calculations, and unsupported output contracts cannot become
analytical state.

### NCC and reload proof distinguish settlement from completion

Add focused backend and NCC integration proof for successful, invalid,
unavailable, stale-approval, partial-failure, crash-window, and reload paths.
Persisted results remain provisional until review and human acceptance bind to
the specific reviewed revision. A successful NCC architecture proof must
demonstrate recoverable typed evidence, calculations, receipt integrity, and
status in a fresh process; actual NCC analytical completion additionally
requires workbook-derived calculations, findings, review/challenge state,
assumptions, and requested outputs. `settled=true` or an output count alone is
not completion evidence.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-plan-document-reviewer`, `skill-executing-plans`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit declared repository files, add focused tests and fixtures, run declared local verification commands, inspect configured local runtime and existing repository state
- User-approval actions: push, merge, publication, external provider writes, credential configuration, destructive recovery, discard, cleanup, and any scope or base change
- Parallel ownership: `none; same-workspace writers execute sequentially`
- Sequential fallback: complete host routing, then typed contract, then persistence adapter, then gate/completion semantics, then backend/NCC proof, then documentation and final verification

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/canonical-architecture-20261014`
- Base commit: `f8aae963ec6b9e911c2a3c270849ce0fbd394155`
- Expected workspace: `tracked files clean; preserve unrelated untracked artifacts under build/, data/, src/foresight_os.egg-info/, and work/`
- Next action: `Task 1 — add the host execution procedure and explicit routing`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | routing tests and Markdown inspection | `python -m pytest -q tests/test_host_wayfinding_routing.py tests/test_wayfinding.py` passed; static host procedure added; dynamic host selection remains not_verified |
| Task 2 | `completed` | current | `codex` | Task 1 | producer/consumer contract, pattern, and invalid-promotion tests | `python -m pytest -q tests/test_result_committer.py tests/test_skills.py tests/test_controller_selection.py tests/test_orchestration_patterns.py` passed; strict nested contract, system-owned identities, reference/type rejection, structured-output injection, and pattern-context proof added |
| Task 3 | `completed` | current | `codex` | Task 2 | provisional merge, crash recovery, hydration, hash/reference, and workflow-receipt tests | `python -m pytest -q tests/test_result_committer.py tests/test_persistence.py tests/test_selective_reuse.py tests/test_evidence_workflow.py` passed; provisional reload, idempotent replay, conflict detection, fresh hydration, and receipt eligibility proved |
| Task 4 | `completed` | current | `codex` | Task 3 | preflight, gate, CLI, stale approval, status, and partial-failure tests | `python -m pytest -q tests/test_execution_gate.py tests/test_runtime_boundaries.py tests/test_cli.py` passed; approved execution injects typed persistence, unsupported contracts/canonical concurrent stages block before provider calls, workflow/CLI report runtime/persistence/analysis/deliverable statuses, low-level runs remain transient |
| Task 5 | `completed` | current | `codex` | Task 4 | direct backend, crash-window, reuse, and fresh-process reload proof | `python -m pytest -q tests/test_execution_persistence.py tests/test_persistence.py tests/test_selective_reuse.py tests/test_execution_gate.py` passed; crash-window replay is idempotent with no false receipt, and a fresh process reloads typed records, provenance, pending-review status, and deliverable assessment without provider work |
| Task 6 | `completed` | current | `codex` | Task 5 | separate NCC plumbing and actual analytical execution evidence | `python -m pytest -q tests/test_ncc_execution.py tests/test_ncc_wayfinding.py` passed; workbook boundary and hidden Others sheet verified, controlled durable artifact/review status proved, actual five-stage NCC analytical execution remains `not_verified` because no approved executor maps the workbook into the typed pipeline |
| Task 7 | `completed` | current | `codex` | Task 6 | docs, full tests, compile, link check, and final verification | `python -m pytest -q`, `python -m compileall -q src tests evaluation`, `python -m pytest -q tests/test_markdown_links.py`, and `git diff --check` passed; documentation reconciled; completion verification is `verified` with NCC analytical execution `not_verified` and cross-process pause/cancel deferred |

## Task Breakdown

### Task 1: Add the host execution procedure and routing

**Purpose:**
- Establish the maintained host boundary between Wayfinding and approved execution without adding a participant/runtime skill or changing `src/foresight_os/skills/manifest.json`.

**Task Function:**
- Define and wire the host execution lifecycle.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: documentation and routing are bounded, deterministic, and low-risk once the accepted lifecycle boundary is preserved.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: the lead controller will run focused routing and documentation checks.

**Specification Coverage:**
- Add `.agents/skills/foresight-execution/SKILL.md`.
- Preserve the two human gates: investigation approval before execution and analytical acceptance after persistence.
- Define the hard completion rule: runtime settlement is not analytical completion.
- Keep cross-process pause/cancel deferred.

**Required Skills:**
- `skill-code-standards`
- `skill-plan-document-reviewer`

**Files And Symbols:**
- Inspect: `.agents/skills/foresight-wayfinding/SKILL.md`
- Inspect: `AGENTS.md`
- Inspect: `docs/architecture.md`, `docs/getting-started.md`, `docs/extending.md`
- Modify: `.agents/skills/foresight-execution/SKILL.md`
- Inspect only: `AGENTS.md` for generated project routing/invariants; do not edit this generated file
- Modify: `docs/architecture.md`, `docs/getting-started.md`, and `docs/extending.md` only where the maintained lifecycle guidance needs alignment
- Modify: `tests/test_host_wayfinding_routing.py`
- Verify: `.agents/skills/foresight-execution/SKILL.md`, routing tests, and generated-surface boundaries

**Dependencies:**
- Accepted verdict framing and current Wayfinding boundary.
- Current host routing tests and canonical architecture rules.

**Authority:**
- Preauthorized local actions: create the host skill, update routing guidance/tests, and run focused local checks.
- Stop for: changes to participant skill manifests, approval policy, cross-process pause/cancel, external publication, or any new orchestration/store registry.

**Steps:**
- [x] Step 1: Inspect current Wayfinding procedure, host routing tests, and maintained documentation to identify the canonical insertion points.
- [x] Step 2: Add the execution procedure with preflight, typed-persistence requirement, truthful statuses, analytical acceptance boundary, approval-fingerprint rule, and explicit deferral notes.
- [x] Step 3: Update only the owning routing and guidance surfaces, then add focused assertions that Wayfinding stops at approval and execution starts only from an approved brief/recipe.
- [x] Step 4: Prove static routing separately from host behavior; host selection remains explicitly `not_verified` because the host does not expose loaded skill path/hash in this run. State that infrastructure repair never substitutes for analytical completion.

**Verification:**
- [x] `python -m pytest -q tests/test_host_wayfinding_routing.py tests/test_wayfinding.py`
- [x] Static inspection of `AGENTS.md` and canonical generator source; host-selection probe is `not_verified` because the host capability is unavailable.
- Expected: static routing remains explicit, the new execution procedure is discoverable, the participant registry is unchanged, and dynamic host selection is either evidenced or truthfully `not_verified`.

**Exit Criteria:**
- The host execution boundary is documented and tested, with no duplicate participant registry or execution engine introduced.

### Task 2: Define the typed canonical stage-result contract

**Purpose:**
- Provide one narrow transport/adapter contract that can promote only validated typed analytical results into the existing domain model.

**Task Function:**
- Design and implement the typed result normalization boundary.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: the contract is a focused backend boundary with high correctness importance and existing domain types to reuse.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: focused unit tests and source review provide independent contract checks.

**Specification Coverage:**
- Define the versioned `analysis-stage-result/v1` producer/consumer contract and bind it to each approved `RecipeStage` output contract.
- Configure provider/participant structured output before calls, parse provider-supported schema responses, and normalize them into the typed stage result.
- Define canonical production rules for each supported execution-pattern/output-contract combination; unsupported combinations fail preflight before provider calls.
- Reuse `Evidence`, `CalculationRecord`, `AnalyticalRecord`, `Relationship`, and system-owned local artifact references where applicable; authoritative `ReviewRecord` creation remains outside the committer.
- Keep `AnalysisState` as the single durable owner.
- Reject arbitrary prose, malformed references, unknown provenance, invalid calculations, and unsupported output contracts.
- Keep structural validation, deterministic calculation validation, and evidential review distinct; schema validity or known locators never claim that a finding is true.
- Make the system own canonical IDs, canonical serialization, result hashes, and durable references; participants may return content, existing source IDs, evidence references, and proposed relationships only.
- Preserve the existing low-level committer extension point rather than requiring a new runtime API.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `src/foresight_os/domain/models.py:AnalysisState`
- Inspect: `src/foresight_os/controller/recipes.py`
- Inspect: `src/foresight_os/schemas/execution_recipe.schema.json`
- Inspect: `src/foresight_os/runtime/workflow.py:run_recipe_async`
- Modify: `src/foresight_os/analysis/result_committer.py`
- Modify: `src/foresight_os/controller/recipes.py` and `src/foresight_os/schemas/execution_recipe.schema.json` for the narrow stage output-contract field
- Verify: `tests/test_result_committer.py`, `tests/test_controller_selection.py`, and `tests/test_orchestration_patterns.py`

**Dependencies:**
- Task 1 defines the host-facing requirement and vocabulary.
- Existing domain types and recipe output contracts are authoritative.

**Authority:**
- Preauthorized local actions: add the typed adapter/protocol and focused tests under `src/foresight_os/analysis/` and `tests/`.
- Stop for: new domain record categories, a second analytical store, arbitrary model-output promotion, or changes to recipe semantics beyond the adapter contract.

**Steps:**
- [x] Step 1: Inventory existing recipe output contracts and domain constructors; define `analysis-stage-result/v1` with stage identity, claims/implications/recommendations, evidence, calculations, relationships, assumptions, uncertainty, and monitoring indicators.
- [x] Step 2: Add generation-time structured-output configuration and a recipe-bound output contract; define pattern rules for direct, sequential, concurrent, handoff, and group-chat stages, requiring deterministic aggregation/final synthesis where multiple participant outputs exist.
- [x] Step 3: Implement normalization/validation with explicit rejection for prose-only payloads, missing or unknown source locators, invalid formula inputs/units, duplicate identifiers, malformed references, unsupported output contracts, and participant-authored canonical IDs/hashes.
- [x] Step 4: Add test-first proof for valid typed results and each rejection class, including deterministic system-owned canonical identities/hashes, deterministic calculation recomputation where possible, and idempotent normalization. Keep uncertainty/weak support persistible as provisional state for later review.

**Verification:**
- [x] `python -m pytest -q tests/test_result_committer.py`
- Expected: valid typed results normalize deterministically; invalid or prose-only results fail before any durable write.

**Exit Criteria:**
- A stable typed contract exists that is independent of providers/renderers and cannot silently turn arbitrary prose into analytical state.

### Task 3: Implement the canonical persistence adapter

**Purpose:**
- Persist validated stage results incrementally through `AnalysisStore`, verify durable integrity, and make receipt creation conditional on successful persistence.

**Task Function:**
- Implement the generic canonical result committer and its durable integrity checks.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: this is the core backend correctness change and requires source-first integration with existing persistence APIs.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: direct store tests and failure injection cover the boundary independently of runtime tests.

**Specification Coverage:**
- Reuse `AnalysisStore.save_pending()`, `save_stage_receipt()`, `load_pending()`, and `load_analysis()`.
- Persist durably provisional `AnalysisState` stage-by-stage; do not mark it accepted from participant output.
- The committer validates, persists, reloads, verifies, and returns `CanonicalStageResult`; the existing workflow remains the only `StageReceipt` writer.
- Accumulate pending state by loading current pending state, otherwise accepted state/initial state, merging the stage delta deterministically, validating, saving, reloading, and verifying.
- Generate canonical IDs, serialization, hashes, and durable references in the system; make repeated commits idempotent and reject same-ID/different-content conflicts.
- Recover a crash after `save_pending()` but before receipt creation without duplicating records; recreate a receipt only after the same hashes and references verify.
- Hydrate `run_context["canonical_records"]` from persisted `AnalysisState` using the exact serializer used for receipt hashes, so fresh-process selective reuse works without provider calls.
- Serialize commits per investigation while allowing independent analytical research stages to execute concurrently; validate changed records and their direct dependency closure incrementally.
- Preserve durably persisted provisional stages when a later stage fails; do not claim whole-run analytical completion.
- Do not add a second store or status database.

**Required Skills:**
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-systematic-debugging`

**Files And Symbols:**
- Inspect: `src/foresight_os/persistence/analysis_store.py:AnalysisStore.save_pending`
- Inspect: `src/foresight_os/persistence/analysis_store.py:AnalysisStore.save_stage_receipt`
- Inspect: `src/foresight_os/persistence/analysis_store.py:StageReceipt`
- Inspect: `src/foresight_os/domain/models.py:AnalysisState`
- Inspect: `src/foresight_os/runtime/workflow.py:run_recipe_async`
- Modify: `src/foresight_os/analysis/result_committer.py`
- Modify: `src/foresight_os/domain/models.py` for the canonical-record projection and `src/foresight_os/runtime/workflow.py` for hydration/receipt eligibility
- Verify: `tests/test_result_committer.py`, `tests/test_persistence.py`, `tests/test_selective_reuse.py`, `tests/test_evidence_workflow.py`, and `tests/test_execution_gate.py`

**Dependencies:**
- Task 2 typed result contract.
- Existing atomic/pending persistence and selective reuse behavior.

**Authority:**
- Preauthorized local actions: implement the adapter against existing store APIs and add failure-injection/integrity tests.
- Stop for: persistence schema replacement, receipt writes before durable state, loss of provenance/hash checks, or behavior changes to direct low-level probes.

**Steps:**
- [x] Step 1: Implement deterministic pending-state accumulation from pending/accepted state, selective changed-record/dependency validation, and system-owned canonical identity/hash generation.
- [x] Step 2: Serialize commits per investigation using the existing file lock/atomic writer without globally serializing provider/tool work; call `save_pending()`, reload, and verify references, hashes, locators, formula inputs, units, and provenance.
- [x] Step 3: Return `CanonicalStageResult` only after verification; leave receipt creation to `workflow.py`, and leave no receipt eligible when write/reload/reference/hash verification fails.
- [x] Step 4: Add crash-window recovery: simulate process loss after pending persistence and before receipt write, then rerun in a fresh process and prove idempotent merge, conflict detection, and receipt reconstruction only after verification.
- [x] Step 5: Rebuild `run_context["canonical_records"]` from persisted `AnalysisState`, prove fresh-process selective reuse without a provider call, and confirm the existing no-committer direct-probe regression remains unchanged.

**Verification:**
- [x] `python -m pytest -q tests/test_result_committer.py tests/test_selective_reuse.py tests/test_evidence_workflow.py`
- [x] Crash-window and fresh-process reuse probes over the persisted fixture
- Expected: valid stages persist as provisional state; workflow writes receipts only after a verified committer result; failed persistence creates no false receipt; earlier provisional stages remain recoverable; retries do not duplicate records; direct no-committer runs remain transient.

**Exit Criteria:**
- The generic committer provides the only approved path from typed stage output to durable analytical state and proves receipt ordering/integrity.

### Task 4: Enforce approved-execution preflight and completion semantics

**Purpose:**
- Configure canonical persistence before provider work in public approved execution while keeping low-level runtime probes permissive and CLI status truthful.

**Task Function:**
- Integrate the committer into the approval gate and separate runtime, analysis, and deliverable outcomes.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: the change is concentrated in existing gate/workflow/CLI owners with focused regression coverage.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: gate and CLI tests provide boundary-focused validation.

**Specification Coverage:**
- Update `ExecutionGate.execute()` and `execute_approved_investigation()` to preflight the canonical committer before provider calls.
- Keep `run_recipe_async()` without a committer valid for low-level probes/tests.
- Return explicit `FAILED` / `RESULT_PERSISTENCE_UNAVAILABLE` for missing approved public persistence.
- Preflight approval currentness, recipe fingerprint, recognized stage output contract, structured-output availability, pattern/contract compatibility, committer configuration, supported record types, writable `AnalysisStore`, input dependencies, and resolvable capabilities before any provider call.
- Bind execution approval to the WorkBrief semantic projection, approved `ExecutionRecipe`, and adaptation envelope; bind analytical acceptance to the specific reviewed `AnalysisState` revision, material finding/recommendation fingerprint, and review identity.
- Report `runtime_status`, `persistence_status`, `analysis_status`, and per-deliverable status separately. Support truthful states such as `NOT_STARTED`, `RUNNING`, `PARTIAL`, `PERSISTED`, `PENDING_REVIEW`, `ACCEPTED`, `BLOCKED_INPUT`, `BLOCKED_EXTERNAL`, and `FAILED` without requiring a new global enum if existing types can represent them.
- Treat replacing a requested deliverable with an outline or another artifact as a scope change requiring the normal proposal/reapproval path; otherwise report the produced artifact and the requested deliverable as separately incomplete/not started.
- Narrow CLI exception classification without collapsing persistence, provider, domain, or cleanup failures.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `src/foresight_os/runtime/execution_gate.py:ExecutionGate.execute`
- Inspect: `src/foresight_os/runtime/execution_gate.py:execute_approved_investigation`
- Inspect: `src/foresight_os/runtime/workflow.py:run_recipe_async`
- Inspect: `src/foresight_os/domain/approval.py:ApprovalRecord`
- Inspect: `src/foresight_os/domain/challenge.py:ReviewRecord`
- Inspect: `src/foresight_os/cli.py`
- Modify: `src/foresight_os/runtime/execution_gate.py`
- Modify: `src/foresight_os/runtime/workflow.py`
- Modify: `src/foresight_os/cli.py`
- Verify: `tests/test_execution_gate.py`, `tests/test_runtime_boundaries.py`, `tests/test_cli.py`

**Dependencies:**
- Task 3 canonical committer and its typed return contract.
- Existing approval, recipe fingerprint, metrics, and failure-classification behavior.

**Authority:**
- Preauthorized local actions: configure approved gate execution, add typed completion/status reporting, narrow CLI handling, and update focused tests.
- Stop for: cross-process pause/cancel, broad runtime API redesign, provider credential changes, or marking analytical completion from runtime metrics alone.

**Steps:**
- [x] Step 1: Trace all gate callers and failure paths before editing; use systematic debugging to confirm shared callers and check for the same missing-persistence defect elsewhere.
- [x] Step 2: Add full preflight for approval, recipe/output-contract, structured-output mode, pattern compatibility, committer, record support, writable store, dependencies, and capabilities; fail before provider work with a stage/error code and `provider_calls: 0` when blocked.
- [x] Step 3: Thread the committer through approved execution while preserving the optional low-level path; classify runtime, persistence, provisional analysis, review/acceptance, and deliverable outcomes separately.
- [x] Step 4: Make approval and acceptance content-bound; invalidate analytical acceptance when the reviewed revision or material finding/recommendation fingerprint changes, and require re-review/re-acceptance.
- [x] Step 5: Treat deliverable substitution as a scope change and narrow CLI exceptions into provider configuration, capability, persistence unavailable, validation, integrity, analysis persistence, approval admission, and cleanup classes.
- [x] Step 6: Add regression proof for missing persistence, unsupported contracts, stale approval, provider failure, persistence failure, bad calculation, deliverable substitution, and successful-but-pending-review analytical state.

**Verification:**
- [x] `python -m pytest -q tests/test_execution_gate.py tests/test_runtime_boundaries.py tests/test_cli.py`
- Expected: approved execution cannot call providers without canonical persistence or a supported structured result contract; low-level probes still work; stale approvals and persistence failures are explicit; CLI output separates runtime settlement from persistence/review/deliverables and does not imply completion from `settled=true` or output count.

**Exit Criteria:**
- Public approved execution is guarded by canonical persistence, while low-level runtime compatibility and distinct failure semantics are preserved.

### Task 5: Prove backend integrity and fresh-process reload

**Purpose:**
- Demonstrate that persisted analytical state, receipts, references, hashes, and status survive process boundaries and important failure paths.

**Task Function:**
- Execute direct backend verification and diagnose/patch any shared persistence defect found.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: verification is deterministic and must remain under one lead because it may patch shared callers discovered by debugging.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: fresh-process assertions and direct store inspection are the required independent proof.

**Specification Coverage:**
- Verify success, invalid typed result, write failure, stale approval, partial stage failure, receipt/reference mismatch, and fresh-process reload.
- Confirm final state/side effects, idempotent stage reuse where existing semantics require it, and no false receipt after failure.
- Use `skill-systematic-debugging` for root cause, shared-caller tracing, and same-defect search; use `skill-test-driven-development` for behavior changes.

**Required Skills:**
- `skill-systematic-debugging`
- `skill-test-driven-development`
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `src/foresight_os/persistence/analysis_store.py`
- Inspect: `src/foresight_os/runtime/execution_gate.py`
- Inspect: `src/foresight_os/runtime/workflow.py`
- Modify: the canonical owner and focused regression test only if a verified shared defect is found
- Modify: `tests/test_execution_persistence.py`
- Verify: `tests/test_execution_persistence.py`, `tests/test_persistence.py`, `tests/test_selective_reuse.py`, `tests/test_execution_gate.py`, plus a subprocess reload probe

**Dependencies:**
- Task 4 approved-execution integration.
- A deterministic local fixture and repository-supported Python runtime.

**Authority:**
- Preauthorized local actions: run direct backend probes, add focused regression tests, and patch the verified shared root cause within declared owners.
- Stop for: unresolved external dependency, credential/network access, destructive fixture cleanup, or a behavior change without a focused regression proof.

**Steps:**
- [x] Step 1: Run the focused proof matrix and record exact failure classifications, durable state, receipts, references, hashes, and resource settlement.
- [x] Step 2: If an anomaly appears, trace the failing path to its canonical owner, enumerate shared callers, search for the same defect elsewhere, and patch the smallest owner-level fix.
- [x] Step 3: Add or update a focused regression test before rerunning the affected proof; do not weaken assertions to accommodate the anomaly.
- [x] Step 4: Simulate a crash after pending persistence and before receipt creation, then rerun the same stage in a fresh process and assert no duplicate records, no silent same-ID overwrite, and receipt reconstruction only after hash verification.
- [x] Step 5: Spawn a fresh Python process against the persisted fixture, hydrate canonical records from `AnalysisState`, and assert that typed records, provenance, receipts, status, and deliverable assessment reload without transient runtime state or a provider call.

**Verification:**
- [x] `python -m pytest -q tests/test_execution_persistence.py tests/test_persistence.py tests/test_selective_reuse.py tests/test_execution_gate.py`
- [x] Fresh-process reload probe using the repository’s supported Python runtime
- Expected: every required success/failure/crash-window path has an explicit outcome; root-cause patches have regression proof; fresh reload recovers durable analytical state and canonical records without provider work and never infers completion from runtime settlement alone.

**Exit Criteria:**
- Direct backend behavior is verified at the persistence boundary and any discovered shared defect is patched with focused regression evidence.

### Task 6: Add NCC deliverable-based end-to-end proof

**Purpose:**
- Replace output-count/settlement-only NCC evidence with a deterministic or bounded end-to-end proof of durable analytical content and requested deliverables.

**Task Function:**
- Validate the canonical execution path against the NCC brief and its existing bounded source fixture.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: the NCC proof is a bounded integration slice that depends on the completed generic path and existing local fixture support.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: the proof itself must inspect durable state and deliverable status rather than rely on runtime summaries.

**Specification Coverage:**
- Separate deterministic persistence/plumbing proof from actual NCC analytical execution. The fixture proof may use controlled typed results, but those results must not be reported as evidence that the NCC business case was solved.
- Verify actual workbook-derived category evidence/calculations, channel evidence, conditional growth bridge, challenge/review records, positioning assumptions, and requested outputs when the real NCC path is run.
- Prove process exit and fresh-process reload for both the deterministic plumbing path and the actual NCC path when available.
- Keep provider-backed live probes optional and explicitly blocked when credentials/capabilities are unavailable; do not persist secrets or raw provider payloads.

**Required Skills:**
- `skill-backend-verification`
- `skill-systematic-debugging`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `tests/test_ncc_wayfinding.py`
- Inspect: `tests/fixtures/wayfinding/ncc-2022-brief.yaml`
- Inspect: existing NCC work/fixture harnesses under `tests/` and `work/`
- Modify: `tests/test_ncc_execution.py`
- Verify: `tests/test_ncc_execution.py` and its fresh-process probe

**Dependencies:**
- Tasks 1–5 complete.
- Approved NCC brief/recipe and bounded local source material.

**Authority:**
- Preauthorized local actions: extend local NCC fixtures/tests and run bounded integration probes without external writes.
- Stop for: missing approved input, unavailable required provider capability, live credential access, or any claim of NCC completion unsupported by durable state and deliverable evidence.

**Steps:**
- [x] Step 1: Map each brief stage and requested deliverable to the canonical typed result and persisted record/reference expected by the current domain model.
- [x] Step 2: Inspect `tests/fixtures/wayfinding/ncc-2022-brief.yaml` and confirm whether `required_patterns: sequential` and `required_capabilities: spreadsheet_read` are human-required; if not, remove those requirements through the normal brief/approval path and preserve the existing dependency topology.
- [x] Step 3: Run deterministic plumbing proof with controlled typed results and inspect structured result, provisional pending state, workflow receipt, fresh reload, and status without calling it NCC analytical evidence.
- [ ] Step 4: Run the actual workbook-derived NCC path when the approved capability is available; currently `not_verified` because the repository has no approved executor that maps the workbook into the five-stage typed pipeline, so no analytical completion claim is made.
- [x] Step 5: Assert separate runtime, persistence, analytical-review/acceptance, and deliverable statuses; assert that `outputs=6`, `settled=true`, or a simulated typed fixture alone do not pass.
- [x] Step 6: Reload the NCC result in a fresh process and record `BLOCKED_EXTERNAL` or `not_verified` truthfully if actual provider/capability-backed analytical execution has not occurred.

**Verification:**
- [x] NCC-focused pytest and bounded integration probe
- [x] Fresh-process reload assertion over the NCC persistence directory
- Expected: deterministic plumbing and actual NCC evidence are labeled separately; every requested deliverable is either durably present with corresponding evidence/artifact or explicitly `BLOCKED_INPUT`, `BLOCKED_EXTERNAL`, `NOT_STARTED`, `PARTIAL`, `PENDING_REVIEW`, or `FAILED`; no unsupported complete claim is emitted.

**Exit Criteria:**
- NCC completion can be assessed from recoverable analytical state and deliverable status, not transient output count or runtime settlement.

### Task 7: Reconcile documentation and perform final verification

**Purpose:**
- Align maintained guidance with the implemented lifecycle and produce fresh repository-level completion evidence.

**Task Function:**
- Reconcile changed owners, documentation, tests, and final verification evidence.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final reconciliation is sequential and requires current repository truth after all implementation tasks.

**Validator Profile (optional):**
- Controller-selected: `none`
- Selection basis: `skill-verification-before-completion` is the final independent acceptance method.

**Specification Coverage:**
- Document runtime settlement versus analytical completion.
- Document provisional persistence, receipt meaning, analytical review, and revision-specific human acceptance.
- Keep optional providers and missing capabilities explicit.
- Document truthful status vocabulary and deliverable substitution/scope-change handling.
- Preserve cross-process pause/cancel as a documented deferral.
- Reconcile tests, generated surfaces, links, and final plan evidence.

**Required Skills:**
- `skill-verification-before-completion`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: all files changed by Tasks 1–6 and `git diff --stat`
- Modify: `README.md`, `docs/architecture.md`, `docs/getting-started.md`, `docs/extending.md`, and owner-specific docs only where required by implemented behavior
- Verify: plan, Markdown links, tests, compile output, and tracked diff

**Dependencies:**
- Tasks 1–6 complete and accepted by the lead controller.
- Any anomaly, patch, deviation, or blocked external proof is recorded in the plan ledger.

**Authority:**
- Preauthorized local actions: update maintained documentation and run the declared final verification commands.
- Stop for: unreviewed scope, failed required verification, unrecorded generated changes, or any Git disposition action not explicitly authorized.

**Steps:**
- [x] Step 1: Update maintained documentation from the canonical implementation and remove duplicate or stale lifecycle claims.
- [x] Step 2: Normalize and inspect the plan Markdown for escaped syntax/path separators, then run focused tests, the full test suite, compile checks, Markdown-link checks, and `git diff --check`; inspect the final tracked diff without staging unrelated untracked artifacts.
- [x] Step 3: Run `skill-verification-before-completion`, record immutable evidence paths/identifiers, and leave the plan proposed/active until its completion gate is actually satisfied.

**Verification:**
- [x] `python -m pytest -q`
- [x] `python -m compileall -q src tests evaluation`
- [x] `python -m pytest -q tests/test_markdown_links.py`
- [x] repository Markdown-link checker for changed docs and plan links
- [x] `git diff --check`
- Expected: all required checks pass or explicit blocked/unavailable outcomes are recorded; no unrelated untracked artifact is added.

**Exit Criteria:**
- Documentation, tests, source, plan ledger, and verification evidence agree; the branch is ready for separately authorized Git disposition.

## Verification

- `python -m pytest -q`
- `python -m compileall -q src tests evaluation`
- repository Markdown-link checker for changed documentation and plan links
- `git diff --check`
- fresh-process reload probe for canonical persisted state and NCC deliverables
- deterministic crash-window recovery and canonical-record hydration probe
- static routing proof plus host-selection evidence or `host skill selection: not_verified`
- `skill-verification-before-completion` returns `verified` before any completion claim

## Completion Criteria

The plan is ready for completion verification when:

1. the host execution skill and routing explicitly separate approval, execution, persistence, analytical review, and human acceptance
2. approved public execution configures a recipe-bound `analysis-stage-result/v1` producer and typed canonical committer before provider work
3. supported pattern/output-contract combinations are defined; unsupported combinations fail preflight before provider calls
4. valid typed stage results persist incrementally as provisional `AnalysisState` through `AnalysisStore`, with system-owned identity/hash and receipt/reference integrity verified in order
5. the existing workflow is the sole `StageReceipt` writer, and crash-window retries are idempotent with fresh-process canonical-record hydration
6. arbitrary prose and invalid provenance/calculations/output contracts cannot become analytical state, while uncertain but structurally valid results remain reviewable as provisional
7. runtime settlement, persistence, analytical review/acceptance, and deliverable status are reported separately with truthful error classes
8. low-level no-committer probes and selective-reuse behavior remain compatible
9. direct backend, failure, partial-stage, stale-approval, crash-window, and fresh-process reload proofs pass
10. NCC deterministic plumbing proof is separated from actual workbook-derived analytical execution; unrun actual analysis remains `BLOCKED_EXTERNAL` or `not_verified`
11. NCC requested deliverables are assessed from corresponding durable evidence/artifacts and explicit statuses rather than output count or `settled=true`
12. execution approval and analytical acceptance are content-bound, and material revision changes invalidate prior acceptance
13. all justified anomalies are root-caused with shared-caller tracing and focused regression proof when behavior changes
14. documentation, tests, compile checks, link checks, normalized Markdown, and final verification are reconciled with current repository truth
15. cross-process pause/cancel remains explicitly deferred and no second store, orchestration engine, NCC-specific runtime, or third agent registry is introduced

The plan may be marked `completed` only after `skill-verification-before-completion` runs fresh verification, confirms these criteria against repository evidence, finds no unresolved required task or unrecorded deviation, and returns `verified`.
