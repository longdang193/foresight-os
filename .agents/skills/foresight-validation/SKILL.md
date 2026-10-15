---
name: foresight-validation
description: Use when a persisted ForesightOS investigation is in PENDING_REVIEW and requires independent evidence checks, calculation reconciliation, scope review, objection handling, or a human acceptance package.
required_reads: []
distribution_tier: starter_kit
---

# ForesightOS Validation

Use this repository-local host procedure after approved execution has produced a
persisted `PENDING_REVIEW` `AnalysisState` and before any human analytical
acceptance or final delivery. It coordinates validation lifecycle work; it is
not a participant skill, a second review engine, a second analytical store, or
the authority that accepts an analytical revision.

## Boundary

```text
approved ExecutionRecipe
  + persisted PENDING_REVIEW AnalysisState
  + committed StageReceipts
  + approved review policy
  + accessible original sources
    -> resolve required review coverage
    -> derive exact target records
    -> run approved independent checks
    -> reconcile and persist trusted ReviewRecords
    -> aggregate current coverage
    -> route producer corrections and selective revalidation
    -> present a human acceptance package
    -> stop for human analytical decision
```

The lifecycle is:

```text
foresight-wayfinding
  -> human execution approval
  -> foresight-execution
  -> PENDING_REVIEW AnalysisState
  -> foresight-validation
  -> reviewed PENDING_REVIEW revision
  -> human analytical decision
  -> foresight-delivery only after acceptance
```

## Admission

Before invoking validators or deterministic capabilities, confirm:

- the input is persisted canonical analytical state, not transient model output;
- the revision is `PENDING_REVIEW` and is bound to the approved execution scope;
- the required `ExecutionRecipe`, stage receipts, run scope, skill hashes,
  capability fingerprints, and review policy are available and consistent;
- source locators, hashes, ranges, units, periods, and calculation inputs are
  recoverable from approved original sources; and
- the trusted review adapter and writable `AnalysisStore` are available.

If admission fails, do not start substantive validation. Report the truthful
state and missing prerequisite, such as `BLOCKED_INPUT`, `BLOCKED_EXTERNAL`, or
`FAILED`.

The host procedure executes the review requirements declared by the approved
recipe. It must not silently invent additional categories, participants,
capabilities, budgets, or execution patterns. If required coverage must change,
propose a recipe change, update the approval fingerprint, and require human
reapproval before executing the changed scope.

## Review coverage

The review policy may require categories such as:

| Category | Typical question | Possible implementation |
|---|---|---|
| `source_fidelity` | Do claims, locators, values, units, and periods match approved sources? | Source appraisal, source reread, deterministic locator checks |
| `scope_reconciliation` | Does the finding use the intended entity, period, denominator, and boundary? | Assumption check, mapping check, domain validation |
| `calculation_reconciliation` | Does an independently reconstructed calculation match the analyst result? | Raw-input recomputation, quantitative sanity check |
| `decision_challenge` | Does the recommendation survive counterevidence and material uncertainty? | Fresh skeptical reasoning, red-team claim, escalation |

These are review requirements, not permanent validator agents. The Controller
and MAF resolve them into approved participants, skills, tools, capabilities,
budgets, and execution patterns for the investigation. Do not hard-code Excel,
web retrieval, or any other provider-specific capability into this host skill.

Every required applicable category needs current coverage before validation is
complete. One passing validator does not establish complete coverage, and one
category's passing result does not substitute for another required category.

## Independent validation

Independence means:

> The validator derives its judgment independently from canonical inputs rather
> than certifying the producer's conclusion.

Another model provider is not required. The input path and reasoning context
must be independent enough to detect producer errors.

Use these patterns:

```text
Calculation
  wrong: analyst CalculationRecord -> call the same analyst function again -> PASS
  right: raw source cells -> reconstruct inputs -> deterministic calculation
         -> expected value -> compare with analyst value

Source fidelity
  wrong: analyst says Sheet A!B4 -> accept locator text
  right: open approved source -> verify source hash, sheet, cell/range,
         unit, value, and period

Decision challenge
  use: a fresh skeptical context that tests counterevidence, assumptions,
       uncertainty, and recommendation boundaries
```

Schema validity, successful tool execution, persisted stage results, and a
known source locator are useful structural checks but are not analytical
validation by themselves.

## Result trust boundary

Validator text must not be committed directly as a canonical analytical stage
result:

```text
validator output
  -> typed ReviewResult or deterministic check result
  -> trusted review adapter
  -> ReviewRecord
  -> AnalysisStore
```

Preserve the existing trust boundary. The adapter, not the host procedure or a
validator, owns normalization, target binding, currentness checks, durable IDs,
and persistence. Never create a parallel review store or evidence format.

Review evidence must be target-scoped and auditable. At minimum, expose the
target, source or reconstructed inputs, expected value or rule, analyst result,
delta or impact, tolerance where applicable, status, reason, provenance, and
review attempt identity. For example:

```text
Target: calculation-category-growth
Source: Personal Care!B12:C12
Expected: 12.4%
Analyst result: 15.8%
Delta: +3.4 pp
Tolerance: 0.01 pp
Status: FAIL
Reason: Analyst used total-market denominator instead of category denominator.
```

Do not reduce review evidence to `Validator PASS` or `Validator FAIL` without
the facts needed for reconciliation and later audit.

## Reconciliation and revalidation

Aggregate coverage against the current analytical revision, not against the
existence of any historical review record.

Distinguish these cases:

```text
same target + old attempt FAIL + producer correction
  -> new attempt PASS
  -> supersession of the prior attempt for that review slot

same current target + validator A PASS + validator B FAIL
  -> genuine disagreement
  -> unresolved until reconciled with a disposition and rationale
```

When producer output changes materially, invalidate the affected review
coverage and selectively revalidate the impacted targets. Do not silently reuse
stale passes. When a group discussion resolves disagreement, preserve every
objection and record the disposition; never delete the losing objection.

Corrections return to the producer or the owning analytical workflow. This
procedure may route the correction and revalidation request, but it must not
silently mutate analytical truth or bypass the normal revision/invalidation
semantics.

## Outcomes and acceptance package

Keep these questions separate:

```text
Is required coverage complete?
What is the current review outcome?
Has a human accepted this analytical revision?
```

Use truthful outcomes:

- `PASS` means the applicable check passed for its current target and input.
- `FAIL` means a material mismatch or unresolved blocking objection exists.
- `NEEDS_CONFIRMATION` means the evidence or mapping requires human or domain
  confirmation before treating it as settled.
- `PROVISIONAL` means the available evidence supports a bounded or conditional
  conclusion while material inputs remain missing; it is not artificial failure.
- `BLOCKED_INPUT`, `BLOCKED_EXTERNAL`, and `FAILED` identify inability to finish
  the required check and must not be reported as passes.

A recommendation can be `PROVISIONAL` when its limits are explicit, for example
when a limited pilot is supported but margin or capacity evidence is missing.
An unsupported claim such as national profitability with no margin evidence is
blocked rather than made provisional.

The acceptance package should show:

- the revision identity and currentness status;
- required categories and their target-scoped coverage;
- passed, failed, provisional, missing, blocked, and unresolved checks;
- reconciliation facts, objections, dispositions, and superseded attempts;
- limitations, missing inputs, counterevidence, and reassessment triggers; and
- a clear readiness statement for the human analytical decision.

The package must not imply that review results grant acceptance. `ReviewRecord`
validity and aggregate coverage are evidence for the human decision, not a
replacement for it.

## Stop boundary

`foresight-validation` never accepts or rejects the analytical revision itself.
It ends by presenting current review coverage, unresolved objections,
limitations, and readiness for a human decision.

Do not start final delivery until the applicable human-acceptance and delivery
policy authorizes the specific reviewed revision and current
`PresentationSpec`.

## Quick reference

| Situation | Required action | Forbidden shortcut |
|---|---|---|
| No persisted current state | Stop and report missing admission input | Validate transient model output |
| Required category missing | Route approved review execution | Treat another category as a substitute |
| Calculation result to verify | Reconstruct from raw approved inputs | Rerun the producer's calculation only |
| Source locator to verify | Re-read source and check hash/range/unit/period | Accept locator text as proof |
| Producer correction | Invalidate affected coverage and revalidate selectively | Reuse stale passes |
| Current validators disagree | Preserve both objections and reconcile | Delete the losing result |
| Coverage complete | Present acceptance package | Auto-accept the revision |
| Human acceptance granted | Hand off to delivery policy | Deliver an unaccepted revision |

## Common mistakes

- Creating four permanent validator host skills instead of resolving review
  categories through the approved recipe.
- Treating `foresight-validation` as a new source of correctness rather than a
  lifecycle coordinator around `ReviewPolicy`, trusted review adapters, and
  `AnalysisStore`.
- Calling the same producer function with the same inputs and labeling the
  output independent.
- Reporting a passing source check as if it also validated calculations,
  feasibility, or recommendation quality.
- Counting historical review records without checking target, revision,
  currentness, supersession, and unresolved objections.
- Letting automated review status or a complete coverage report imply human
  analytical acceptance.
- Hard-coding spreadsheet capabilities when the approved investigation uses a
  different source type.

## Ownership

- `ReviewPolicy` determines what must be checked.
- Controller and MAF determine who and how the approved checks run.
- Specialist packaged skills provide reasoning methods.
- Deterministic capabilities provide factual and numerical checks.
- The trusted review adapter and `AnalysisStore` persist review evidence.
- Aggregate coverage logic determines current reconciliation truth.
- Human reviewers accept, reject, or request analytical revision.

The host procedure coordinates these owners; it does not replace them.
