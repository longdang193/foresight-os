---
name: presentation-storytelling
description: Turn reviewed foresight findings into a decision-focused presentation brief. Use for executive slides, a Canva handoff, or report-to-presentation requests that must preserve evidence and uncertainty.
---

# Presentation Storytelling

## Inputs
Use the canonical AnalysisState revision, derived FindingViews, decision question, horizon, audience, presentation spec, and supplied brand/template constraints. Ask only for information that materially changes the story; otherwise state reasonable audience assumptions.

## Workflow
1. Identify the audience's decision and the few findings that change it. Check review currency and source revision. Label provisional content visibly and keep it outside the normal external-publication path.
2. Use the existing six-slide PresentationSpec: decision and scope; evidence and signals; scenarios and uncertainties; strategic options; recommendation; reassessment plan. Respect the compiler's fixed titles and schema. Other layouts require an explicit supported boundary, not silently altered JSON.
3. Assign each slide a distinct purpose and concise key message. Select different content for each role; avoid repeating findings. Preserve conditions that affect the conclusion rather than truncating them to fit.
4. Associate every factual key point with finding/evidence IDs and every derived number with calculation IDs. Send new research or calculations back to analysis for review before presenting them as established results.
5. Specify a chart for a useful quantitative comparison, a scenario table for alternatives, or a cited statement when a chart adds no value. Apply evidence-visualization for charts; never invent data to fill a slide.
6. Add short visible source labels beside factual displays and full locators in speaker notes: title/publisher, date, URL or workbook version/sheet/range, and transformation/calculation reference. Retain internal IDs for machine traceability. Do not expose private paths, tokens, or restricted data.
7. Preserve uncertainty, counterevidence, confidence rationale, disconfirmation conditions, and monitoring triggers. Distinguish an analyst recommendation from a human-approved decision.

## Output
Return a slide brief with number, purpose, key message, exact copy, finding/evidence/calculation IDs, visual request, visible citation, speaker notes, and material caveats. Keep renderer-specific instructions in the handoff, not invented PresentationSpec fields or a second analytical store. The canonical compiler owns spec generation and hashing.

## Completion check
Apply slide-design-review to content and rendered pages when available. Missing sources or stale recommendations prevent a decision-ready result. Report unavailable rendering honestly. This skill grants no external write authority. Use connected native Canva tools/adapter and the existing human-approval boundary for delivery.
