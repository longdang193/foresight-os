---
name: key-assumptions-check
description: Expose and test conditions underlying a claim, scenario, or recommendation. Use when incomplete information or planning assumptions could change a strategic decision.
---

# Key Assumptions Check

## Inputs
Use the target ID, decision, horizon, supporting evidence, calculations, dependencies, and constraints. Keep supplied facts separate from assumptions.

## Workflow
1. Ask what must remain true for the conclusion to hold. Inspect demand, cost, timing, capacity, adoption, regulation, and competitor responses where relevant.
2. Record each material assumption's origin, evidence IDs, applicable period, and basis: observed, inferred, or an explicit planning choice. Do not turn absent evidence into a factual assertion.
3. Prioritize by decision sensitivity and uncertainty. Test assumptions that could reverse the recommendation first; do not require an exhaustive register before useful analysis begins.
4. Vary selected assumptions within evidenced ranges or clearly labeled hypothetical ranges. Use authorized deterministic tools for numerical thresholds; state qualitative consequences when inputs are insufficient.
5. Specify observable disconfirmation conditions: indicator, threshold/event, observation window, and triggered action. Identify correlated assumptions to avoid double-counting a driver.

## Output
Return an assumption table with target ID, assumption, basis/evidence, uncertainty, effect if false, disconfirmation condition, and next evidence needed. Distinguish robust actions from conditional commitments.

When the caller requests `ChallengeObjection`, return only that envelope using `UNSUPPORTED_ASSUMPTION` or `FAILURE_MODE`, target ID, available evidence IDs, and `UNRESOLVED` until addressed. Missing support can be an objection without a fabricated citation.

## Completion check
Every decision-critical assumption has an explicit consequence if false. Proceed provisionally when uncertainty is tolerable; abstain or escalate only the affected consequential conclusion. Do not manufacture numerical probabilities.
