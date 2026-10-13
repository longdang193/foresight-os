---
name: evidence-visualization
description: Select and verify evidence-based charts or tables for foresight reports and slides. Use for quantitative comparisons, trends, uncertainty, scenarios, and strategic option trade-offs.
---

# Evidence Visualization

## Inputs
Use the slide's key message, canonical findings/calculation IDs, source table/range, row grain, filters, units, period, and scenarios. Reuse verified data; request missing extraction through authorized tools.

## Workflow
1. Specify the comparison. Trace every plotted value to evidence and, when transformed, a reproducible calculation. Verify totals, denominators, missing values, aggregation, and comparability with quantitative-sanity-check.
2. Choose the simplest useful display:

   | Question | Display | Check |
   | --- | --- | --- |
   | Which option/category is larger? | Sorted bar or dot plot | Consistent units; zero baseline for length-encoded bars |
   | How does a measure change over time? | Line chart | Honest time spacing; mark missing observations/revisions |
   | How do scenarios differ? | Range/dot plot or table | Common horizon; label assumptions and ranges |
   | Which inputs change the decision? | Sensitivity/tornado chart | Common baseline and explicit tested ranges |
   | Are two measures associated? | Scatter plot | Comparable observations; association does not establish causality |
   | Is evidence qualitative or sparse? | Cited table or text | No manufactured numerical scale |

3. Preserve units, dates, denominators, geography, currency basis, and filters in labels/notes. Distinguish observed values from projections with labels and line styles, not color alone. Scenario bounds are not statistical confidence intervals.
4. Use deterministic chart tooling or native editable charts/tables. Never use image generation for exact data graphics. Avoid 3D effects, misleading axis truncation, unexplained dual axes, and ungrounded weighted scores.
5. Write a restrained caption stating what the graphic establishes and its limitation. Put a short source citation beside it and full locator/transformation details in notes. Keep consequential caveats visible on the slide.
6. Inspect readability, overlapping marks, uncertainty, ordering, and accessibility. Reconcile displayed values and rounding to calculation records.

## Output
Return chart/table type, title/caption, data values and units, finding/evidence/calculation IDs, axes/series, filters, rounding, uncertainty treatment, source citation, and renderer instructions. Treat this as a derived visual brief; do not add unsupported PresentationSpec fields or new analytical truth.

## Completion check
Every displayed value has provenance and the graphic supports its key point. If data or tools are unavailable, return a labeled visual proposal or qualitative alternative; do not claim rendering or verification. Tool permissions remain those granted by the controller.
