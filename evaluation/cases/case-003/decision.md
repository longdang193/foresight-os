# Case 003: Synthetic Regional Demand Shift

## Decision question

Should the strategy team increase investment in the Northern Europe service
network for 2030?

## Owner and horizon

- Owner: strategy team
- Horizon: 2030
- Materiality: a recommendation is material when it changes regional capital
  allocation or service capacity.

## Scope

- Regions: Northern Europe, Southern Europe
- Metric: annual service demand index
- Source version: `case-001-v1`

## Expected traps

- Do not compare raw demand counts with indexed demand values.
- Do not treat the forecast column as observed history.
- Do not recommend Northern Europe from growth alone without checking the
  contradictory capacity constraint.

## Human verification protocol

1. Confirm the source version, sheet, range, units, and period.
2. Confirm that observed and forecast values are not mixed.
3. Check the capacity constraint before accepting the recommendation.
4. Reject any material statement without a reproducible source locator.

## Provisional assumptions and open dependencies

- Assumption: the 2030 planning horizon remains in scope.
- Dependency: capacity expansion cost is not included in this synthetic case.
