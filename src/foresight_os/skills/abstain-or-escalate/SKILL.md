---
name: abstain-or-escalate
description: Decide how to proceed when evidence, analytical validity, or authority is insufficient. Use for unresolved consequential objections, missing inputs, stale findings, or unavailable required capabilities.
---

# Abstain or Escalate

## Inputs

Use the decision question, affected finding or recommendation IDs, consequence
and reversibility, review status, missing inputs, unresolved objections, tool
availability, and authority limits.

## When to use

Use when a gap may change a consequential conclusion, when a required review is
stale or unresolved, when an input or capability is unavailable, or when the
requested action exceeds the caller's authority.

## Do not use / route instead

Do not use as a blanket intake gate for ordinary ambiguity or incomplete but
non-material work. Route source validity to `source-appraisal`, assumptions to
`key-assumptions-check`, numerical defects to `quantitative-sanity-check`, and
claim challenge to `red-team-claim`.

## Workflow

1. Name the affected conclusion and classify the boundary: evidence gap,
   calculation defect, contradiction, stale review, unavailable capability,
   missing input, or authority limit. Separate execution failure from
   analytical uncertainty.
2. Decide whether the gap changes the decision or only its precision. Continue
   independent supported work and preserve useful partial results.
3. Choose one disposition: proceed within scope, issue a labeled provisional
   finding, abstain from the affected recommendation, or escalate a specific
   decision to the responsible human.
4. Define the smallest resolving action, required evidence or authority, and
   stopping condition. State what can continue while pending. Do not retry an
   unavailable provider indefinitely or silently substitute an unapproved one.
5. Preserve assumptions, uncertainty, counterevidence, disconfirmation
   conditions, and provenance in the handoff.

## Output

Return disposition, affected IDs, reason and consequence, useful partial
findings, resolving action, pending evidence or authority, stopping condition,
and the specific decision requested from the human. Keep `BLOCKED_EXTERNAL`,
execution failure, missing input, and provisional analysis distinct.

When the caller requests `ChallengeObjection`, return only that envelope with
an appropriate kind and `UNRESOLVED` for unresolved issues. Use an empty
evidence-ID list when support is missing; never fabricate provenance.

## Completion check

Another analyst can take the next step without reconstructing context. The
recommendation remains withheld when its acceptance requirements are unmet, and
the disposition does not grant publication, external-write, or strategic
approval authority.

## Pair with

- `key-assumptions-check` for decision-critical assumptions.
- `source-appraisal` for source support boundaries.
- `red-team-claim` for consequential objections.

## Anti-patterns

- Treating a completed runtime, attractive slide, or accepted objection as approval.
- Hiding a provider or authority failure inside a generic uncertainty label.
- Escalating the whole investigation when one bounded claim is affected.
