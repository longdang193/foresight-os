---
name: abstain-or-escalate
description: Decide how to proceed when evidence, analytical validity, or authority is insufficient. Use for unresolved consequential objections, missing inputs, stale findings, or unavailable required capabilities.
---

# Abstain or Escalate

## Inputs
Use the decision, consequence and reversibility, review status, missing inputs, unresolved objections, tool availability, and authority limits.

## Workflow
1. Identify the affected conclusion and boundary: evidence gap, calculation defect, contradiction, stale review, unavailable tool, or missing authority. Separate execution failure from analytical uncertainty.
2. Determine whether the gap changes the decision or only its precision. Continue independent, supported work and return useful partial results.
3. Choose a disposition: proceed within scope; provide a labeled provisional finding; abstain from the affected recommendation; or escalate a specific decision to the responsible human. Do not impose blanket intake gates for normal ambiguity.
4. Define the smallest resolving action, required evidence/authority, and stopping condition. State what can continue while pending. Do not retry unavailable providers indefinitely or silently substitute unapproved ones.
5. Preserve assumptions, uncertainty, counterevidence, and disconfirmation conditions in the handoff. A completed runtime, attractive slide, or accepted objection is not strategic approval.

## Output
Return disposition, affected target IDs, reason and consequence, useful partial findings, resolving action, and the decision requested from the human. Keep `BLOCKED_EXTERNAL`, execution failure, and provisional analysis distinct.

When the caller requests `ChallengeObjection`, return only that envelope with an appropriate kind and `UNRESOLVED` for unresolved issues. Missing evidence can use an empty evidence-ID list; never fabricate provenance to satisfy a field.

## Completion check
Make the next step actionable without forcing the user to reconstruct context. Preserve existing review and authorization boundaries. Withhold consequential recommendations whose acceptance requirements remain unmet.
