---
name: red-team-claim
description: Attempt to disprove a strategic claim or recommendation. Use for consequential findings, conflicting evidence, weak causal explanations, or adversarial review before acceptance.
---

# Red-Team Claim

## Inputs
Use target IDs, the strongest supported claim, evidence, calculations, assumptions, counterevidence, decision horizon, and selected review policy.

## Workflow
1. Restate the strongest defensible claim, preserving qualifications. Identify what would make it wrong rather than attacking a weaker substitute.
2. Form a plausible alternative explanation. Test measurement error, selection bias, source dependence, reverse causality, changed conditions, and implementation failure where relevant.
3. Design the smallest discriminating check. Inspect contradictory records or recompute a material result. Search externally only with granted tools; record query scope and unavailable access. Absence of a search result is not proof of absence.
4. Record material objections with `kind`, `target_id`, `statement`, existing `evidence_ids`, and `disposition`. Use `SOURCE_CONTRADICTION`, `CALCULATION_ERROR`, `UNSUPPORTED_ASSUMPTION`, `ALTERNATIVE_HYPOTHESIS`, `FAILURE_MODE`, or `INSUFFICIENT_EVIDENCE` as appropriate.
5. Leave objections `UNRESOLVED` unless evidence justifies a disposition. `ACCEPTED` means the objection is upheld, not that the recommendation is accepted. `REJECTED` requires an evidenced reason. Preserve decision-relevant dissent.
6. State which conclusion must narrow, change, or remain provisional and what observation would resolve the dispute. Respect the caller's scope and research budget.

## Output
When invoked by the reviewer runtime, return only `{"objections": [...]}` with the exact fields above. Include rationale, decision impact, and the resolving check in `statement`; do not invent schema fields. An empty list means no material objection found within scope, not proof of truth.

## Completion check
Separate findings from hypotheses and unavailable checks. Let the review policy and human decision process determine acceptance; never waive unresolved consequential issues because agents reached consensus.
