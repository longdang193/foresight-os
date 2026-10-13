---
name: slide-design-review
description: Review slide content and rendered designs for evidence fidelity, readable visuals, citations, and decision usefulness. Use before Canva delivery or after changing source findings.
---

# Slide Design Review

## Inputs
Use the source revision, PresentationSpec/slide brief, canonical findings/calculations, rendered pages or design read-back, audience, and design constraints. Distinguish content-only review from visual inspection.

## When to use
Use before a renderer or Canva handoff, after source findings change, or when
reviewing a rendered deck for evidence fidelity, readability, and decision
usefulness.

## Do not use / route instead
Do not create new analytical findings, calculations, PresentationSpec fields,
or publication authority. Route story structure to
`presentation-storytelling`, chart construction to `evidence-visualization`,
and unresolved analytical defects to the owning review skill.

## Workflow
1. Check source revision, review currency, and artifact staleness. Match slides to findings. Flag unsupported claims, dropped qualifications, changed units, and provisional recommendations presented as accepted.
2. Check that each slide serves its purpose and makes one understandable key point. Remove repetition and presenter narration. Keep decision-relevant evidence; move details to notes or an appendix only when the supported template permits it.
3. Verify chart values, labels, denominators, periods, scenario boundaries, and rounding against calculation records. Require visible distinctions between observed data and projections. Check axes and scales for misleading comparisons.
4. Check factual key points for appropriate attribution. Sources must substantiate the displayed claim. Use readable short citations and full URLs or workbook locators plus calculation references in notes. Internal evidence IDs alone are insufficient for an external audience.
5. Inspect rendered pages at presentation scale for overflow, overlap, contrast, hierarchy, and label readability. Follow the user's template; otherwise prefer approximately 32-point titles, 20-point body copy, readable source labels, ample spacing, and a restrained palette. Shorten copy before shrinking it. Do not rely on color alone.
6. Preserve uncertainty, counterevidence, disconfirmation conditions, and monitoring actions where they affect the recommendation. Visuals must support the argument, not decorate unsupported assertions.
7. Produce one renderer-only `DesignBrief` handoff containing template/theme, typography hierarchy, restrained palette, chart style, citation style, and density target. Treat it as a transient handoff contract, not a new domain object or persistence authority.
8. Return specific fixes by slide and severity. Correct supported wording/layout within scope; return new claims or changed calculations to analysis/review. Recheck affected slides after edits.

## Output
Return the renderer-only `DesignBrief` plus per-slide issues with severity (blocking, material, cosmetic), observed problem, exact correction, source references, and verification still needed. State analytical fidelity, visual readability, and external save/delivery status separately.

## Completion check
Mark decision-ready only after material content and visual issues are resolved against current sources. If rendered pages are unavailable, report visual review as unverified. Never infer a saved Canva edit from a preview; use confirmed native transaction/job results. This review grants no publication authority and does not replace human strategic approval.

## Pair with
- `presentation-storytelling` for the governing thought and six-slide content contract.
- `evidence-visualization` for chart correctness and necessity.
- `abstain-or-escalate` when fidelity or approval requirements remain blocked.

## Anti-patterns
- Treating `DesignBrief` as persistent analytical truth.
- Shrinking text or removing caveats to hide overflow and density problems.
- Claiming external save, publication, or Canva delivery from an unconfirmed preview.
