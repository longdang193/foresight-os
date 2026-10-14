# ForesightOS Project Contract

This file defines repository-specific behavior. Implementation and tests under `src/foresight_os/` and `tests/` are authoritative when prose disagrees.

## Project Purpose

- Turn a decision question and bounded source material into traceable claims, implications, recommendations, and local artifacts.
- Preserve review, revision, invalidation, provenance, uncertainty, and counterevidence state.
- Keep the provider-free local CSV/XLSX analysis path usable without authentication.
- Use [README.md](README.md) and [docs/architecture.md](docs/architecture.md) as orientation, not replacement runtime specifications.
- Make each recommendation traceable to evidence, assumptions, calculations, and a reassessment trigger.

## Foresight Process

- Start with a validated `WorkBrief` containing question, objective, horizon, constraints, stages, participants, and research needs.
- Resolve an `ExecutionRecipe`; direct, sequential, concurrent, handoff, and group-chat patterns are execution choices.
- Keep every `RecipeStage` explicit about inputs, outputs, participants, skills, capabilities, dependencies, limits, and expected results.
- Verify skill manifest hashes, output contracts, capability fingerprints, unavailable decisions, and run scope before execution.
- Record stage inputs, policy, provenance, result references, and commit status in receipts before reuse.
- Separate observations, assumptions, interpretations, recommendations, uncertainty, and monitoring triggers.
- Require review before acceptance; changed evidence or scope creates invalidation and a new revision rather than silent mutation.
- Derive reports and presentations from committed analytical state.
- Keep execution-pattern selection separate from the foresight process stages.

For strategic foresight intake, clarification, and WorkBrief creation or
refinement, use the repository-local host procedure
`.agents/skills/foresight-wayfinding/SKILL.md`.

`.agents/skills/` is the repository-local host-procedure boundary.
`src/foresight_os/skills/` remains the packaged participant/runtime
analytical-skill boundary. Do not substitute generic Wayfinding,
specification-drafting, or software implementation-planning procedures for
strategic intake. Foresight Wayfinding ends when the WorkBrief and execution
proposal are ready for human review.

## Architecture Invariants

- `AnalysisState` is the single durable owner for evidence, claims, implications, recommendations, calculations, relationships, artifacts, revisions, reviews, and invalidation metadata.
- `AnalysisStore` validates and writes state atomically; pending mutations stay separate until accepted.
- `StageReceipt` reuse requires matching fingerprints, committed results, and complete provenance.
- `FindingView` is accepted only when its current review is valid and no unresolved objection or missing input remains.
- NetworkX projections are derived query views, not a second analytical store.
- `PresentationSpec` is revision-bound, hash-checked, and either current or explicitly provisional.
- Preserve source locators, formula inputs, units, hashes, and invalidation reasons through calculations and artifacts.
- Keep optional adapters from changing the local analytical contract.

## Canonical Owners

- Work briefs, domain records, revisions, and invalidation belong under `src/foresight_os/domain/`.
- Recipe selection, skill resolution, and capability policy belong to their existing controller and runtime modules.
- The packaged skill registry is `src/foresight_os/controller/skills.py`; each procedure owns `src/foresight_os/skills/<skill-id>/SKILL.md`.
- Persistence and stage receipts belong to `src/foresight_os/persistence/analysis_store.py`.
- Review and finding validity belong to `src/foresight_os/domain/challenge.py`.
- Presentation compilation and delivery boundaries belong to `src/foresight_os/artifacts/presentation.py`.
- Maintained guidance belongs in `README.md` and `docs/`; historical decisions and evidence remain in `docs/intent/` and `docs/superpowers/`.

## Change Rules

- Extend an existing owner before adding a parallel registry, store, schema, receipt, or evidence format.
- Preserve single-source-of-truth behavior and symmetric create/delete, forward/reverse, and valid/invalid cases.
- Keep provider, renderer, and destination concerns at explicit boundaries; they must not invent analytical truth.
- Preserve accepted behavior, provenance, failure statuses, and invalidation semantics when refactoring.
- Update focused tests and owning documentation when contracts change.
- Keep credentials, authorization headers, raw provider payloads, and customer data out of source, state, receipts, fixtures, and public documentation.

## Verification Requirements

- Prove the changed owner with focused tests before relying on broad tests.
- Run `python -m pytest -q` and `python -m compileall -q src tests evaluation` for repository changes.
- Verify deterministic fixtures, hashes, persistence, invalidation, and receipt reuse when affected.
- Test important success and failure paths, including missing inputs, unavailable capabilities, malformed responses, and stale reviews.
- Label structural proof separately from model quality or human judgment; use `VERIFIED`, `FAILED`, `BLOCKED_INPUT`, `BLOCKED_EXTERNAL`, and `not_measured` truthfully.
- Add representative boundary or performance evidence when a material claim depends on it.
- Inspect the final diff and documentation links; do not claim external delivery without a durable receipt and required approval.

## Documentation Ownership

- Put onboarding and stable architecture guidance in `README.md` and `docs/`.
- Link new behavior to the maintained guide instead of copying a second specification into this file.
- Keep skill procedures beside their packaged skill and keep manifests, schemas, and tests aligned with owning code.
- Keep plans and evidence source-specific; do not rewrite historical records to make current guidance appear cleaner.
- Run the repository Markdown-link checker when documentation paths change.

## External Boundaries

- Web, Power BI, MCP, Canva, and other providers are optional; local analysis remains independently verifiable where supported.
- Missing credentials, unavailable providers, failed calls, and missing approved inputs remain explicit blocked or failed outcomes.
- Sanitize provider results before durable evidence and keep secrets out of persisted state and receipts.
- External mutation requires the existing human-approval boundary, an adapter, and a matching durable delivery receipt.
- A failed destination must not mark analytical state as delivered.
- Rendering and presentation output may summarize committed findings but cannot add unsupported claims, calculations, or fields.

## Maintenance Bias

- Prefer the smallest reversible change that preserves existing contracts.
- Inspect the canonical owner and adjacent tests before creating new structure.
- Remove duplicate instruction or documentation surfaces when they add no behavior and have no active consumer.
- Favor shared configuration and strategies over special cases.
- Measure performance claims with reproducible evidence rather than intuition.
- When source, tests, and prose conflict, fix the prose or investigate the implementation; do not silently weaken the authoritative contract.
