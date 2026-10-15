---
name: foresight-validation
description: Use when a provisional ForesightOS analysis needs source-grounded validation, selective review escalation, or an acceptance-ready status projection before human decision.
---

# ForesightOS Validation

Use this repository-local host procedure after provisional analytical state is
persisted and before reporting an analysis as accepted. It routes validation
through the existing source, review, persistence, and artifact owners; it is
not a participant skill, a second validator, or a new durable status model.

## Inputs

- the approved source boundary and exact workbook or evidence selections;
- the provisional `AnalysisState` and its current revision;
- the effective review policy and selected required checks;
- the run-scoped capability context and any declared missing inputs; and
- the requested report or other local deliverable projection.

## When to use

Use it when deterministic source fidelity, scope reconciliation, calculation
reconciliation, decision challenge, or human acceptance must be checked before
an analytical revision is treated as current and usable.

Do not use it to execute a new investigation, invent findings, replace a
specialist analytical skill, or make an external delivery decision. Route
strategic intake to `foresight-wayfinding`, approved execution to
`foresight-execution`, and presentation delivery to `foresight-delivery`.

## Workflow

1. Reload the canonical `AnalysisState` and verify the source fingerprint,
   selected sheets/ranges, periods, units, and expected scope.
2. Call `read_validation_source()` and `run_independent_validation()` from
   `foresight_os.analysis.independent_validation` using the run-scoped source
   cache. Select only checks required by effective policy; keep required but
   unavailable checks `PENDING`.
3. Attach review results through `run_review_phase()` and the existing
   `AnalysisStore` workflow. Preserve source locators, calculation inputs,
   review fingerprints, objections, limitations, and missing-input reasons.
4. Derive `FindingView` values and the report summary from
   `foresight_os.domain.challenge`; use dependency closure for precise
   invalidation and conservative reassessment when closure is uncertain.
5. Request explicit human acceptance through `accept_pending_analysis()`.
   Persist a new revision when material evidence or scope changed; never
   silently reuse acceptance from an earlier revision.
6. Report runtime, persistence, validation, review, acceptance, and deliverable
   status separately. A local report or renderer may summarize state but may
   not add unsupported claims or mark an unaccepted revision accepted.

## Critical invariants

- A source hash and locator identify the exact evidence used by a check.
- Missing, contradictory, stale, failed, or unavailable inputs remain visible;
  they are not converted into passes or zeros.
- Selective invalidation may preserve unaffected findings, but uncertain
  dependency coverage requires conservative reassessment.
- Automated review and human acceptance remain separate decisions.
- Provider failure or unavailable credentials remain `BLOCKED_EXTERNAL` and do
  not erase valid local analytical state.
- The host procedure is not added to `src/foresight_os/skills/manifest.json`.

## Stop condition

Stop with a truthful pending, failed, blocked, or rejected outcome when the
source changed, required validation is incomplete, review coverage is stale or
conflicted, a required input is missing, or human acceptance has not been
granted. Do not claim a supported recommendation or successful deliverable
without current evidence, current review, and the required durable receipt.
