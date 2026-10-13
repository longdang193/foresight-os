---
name: quantitative-sanity-check
description: Verify numerical claims, spreadsheet calculations, scenario results, and chart values. Use before accepting quantitative findings or putting derived numbers into reports and slides.
---

# Quantitative Sanity Check

## Inputs
Use target IDs, source tables/ranges, input IDs, formula/transformation, units, period, filters, and calculation records. Request authorized spreadsheet access when only an unexplained total is supplied.

## When to use
Use before accepting a material numerical finding, comparing scenarios or
options, or placing derived values in a report, chart, or slide.

## Do not use / route instead
Do not replace missing source data with an assumed value or use this method to
judge source credibility, narrative structure, or visual aesthetics. Route
source support to `source-appraisal`, assumptions to
`key-assumptions-check`, and chart selection to `evidence-visualization`.

## Workflow
1. Establish row grain and comparison scope. Check keys, duplicates, joins, hidden/filtered rows, missing values, errors, units, currency, and date coverage. Preserve missing values; never silently substitute zero.
2. Inspect formulas and cached values separately. A cached Excel result does not prove recalculation or freshness. Mark unavailable/stale formula results and use the declared recalculation boundary; never claim openpyxl recalculated a workbook.
3. Recompute material totals and ratios with granted analysis/calculation tools. Verify denominators, weighted versus simple averages, percentage versus percentage-point changes, signs, and currency conversions.
4. Reconcile totals to components and check a representative row independently. Retain input evidence IDs, transformation, result, units, and source ranges in the existing calculation contract.
5. Test decision-sensitive inputs and a plausible adverse case. Identify when the recommendation changes; label assumed ranges. Round only for display.

## Output
Return checked calculation IDs, recomputed results, discrepancies, scope, formula-trust status, sensitivity thresholds, and unresolved inputs. State the numerical tolerance and its rationale.

When the caller requests `ChallengeObjection`, return only that envelope. A `CALCULATION_ERROR` needs existing evidence/calculation IDs; use `INSUFFICIENT_EVIDENCE` when inputs are unavailable. Explain the discrepancy and decision impact in `statement`.

## Completion check
Trace every material number to reproducible inputs. Example: 40% to 50% is +10 percentage points or +25% relative, not +10% relative. Withhold affected quantitative conclusions when formula trust or comparability remains unresolved.

## Pair with
- `source-appraisal` for source scope, version, and locator validity.
- `key-assumptions-check` for decision-sensitive ranges.
- `evidence-visualization` for chart-value reconciliation.

## Anti-patterns
- Treating cached workbook values as proof of recalculation or freshness.
- Silently converting missing, filtered, or incomparable values to zero.
- Reporting precision beyond the source, formula, or declared tolerance.
