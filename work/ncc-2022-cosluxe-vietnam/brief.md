---
investigation_id: ncc-2022-cosluxe-vietnam-entry
decision_question: Which Personal Care category should Cosluxe Nature enter first
  in Vietnam, and which channels should it prioritize across 2023-2025 to support
  stable growth of at least 8% from 2024 onward?
scope:
- Vietnam Personal Care category performance in offline channels using MAT 2YA, MAT
  YA, and MAT TY measures ending September 2022.
- Vietnam Personal Care ecommerce category growth, new launches, and survival of new
  launches.
- Vietnam consumer price-tier movement, essential and routine category perceptions,
  channel penetration, and shopping frequency.
- Vietnam traditional-trade regional and urban-rural dynamics, modern-trade store
  universe, and channel value sales.
- Cosluxe Nature portfolio focus, premium image, and natural-ingredient positioning
  as stated in the case materials.
desired_deliverables:
- A traceable category-attractiveness screen identifying a provisional first-entry
  category and its evidence.
- A three-year channel-prioritization and phasing recommendation for 2023-2025.
- Target consumer, price-tier, and premium-natural positioning hypotheses with explicit
  assumptions.
- A conditional growth bridge showing whether the proposed category-channel choices
  could support the 8% planning target from 2024 onward.
- Risks, evidence gaps, trigger conditions, and an executive presentation outline
  within the case's suggested maximum of 20 slides.
assumptions:
- Vietnam entry begins in 2023 and stable-growth planning begins from 2024 onward.
- Workbook facts retain their stated source, period, units, and dummy-case status.
- First entry category means the initial priority category, not exclusion of the remainder
  of the portfolio.
- Offline and ecommerce measures are not comparable until definitions, periods, and
  units are normalized.
- The 8% growth ambition is a planning target, not an observed result.
open_dependencies:
- Confirm launch budget, margin, supply, distribution, and portfolio-cannibalization
  constraints with the client.
- Confirm whether the recommendation optimizes revenue, profit, market share, reach,
  or a weighted combination.
- Confirm acceptable external desk-research scope and evidence-quality threshold for
  claims beyond the workbook.
- Reconcile category definitions and channel boundaries across the named workbook
  sheets.
- Validate whether the 2023-2025 horizon and 2024 growth baseline match the client's
  planning calendar.
current_direction: Build a traceable category-by-channel scorecard and keep any recommendation
  provisional until category growth, portfolio fit, consumer relevance, channel dynamics,
  competitive intensity, and execution constraints are reconciled.
next_useful_step: Normalize MAT TY versus MAT YA and MAT 2YA measures, reconcile them
  with channel and consumer evidence, and open the category and channel decision questions
  for review.
stages:
- stage_id: source-audit
  objective: Inventory workbook sources, definitions, periods, units, and comparability
    limits before calculating attractiveness.
  participants:
  - analyst
  subtasks: []
  dependencies: []
  expected_result: A source and metric dictionary with observed-versus-derived labels
    and unresolved comparability issues.
  research_needs:
  - kind: STRUCTURED_DATA
    query: Inspect the Case and Glossary sheets for business objectives, category
      definitions, source notes, and period conventions.
    source_hint: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx;
      sheets Case and Glossary
  - kind: STRUCTURED_DATA
    query: Inventory measures, units, and source notes across Macro & FMCG, Personal
      Care, Consumer, Channel Dynamic, Trad.Trade, Modern Trade, and Ecommerce.
    source_hint: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx;
      sheets Macro & FMCG, Personal Care, Consumer, Channel Dynamic, Trad.Trade, Modern
      Trade, Ecommerce
  - kind: VALIDATION
    query: Confirm whether offline, ecommerce, value, volume, store, penetration,
      and frequency measures can be compared directly.
    source_hint: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx;
      source notes and headers
  - kind: STRUCTURED_DATA
    query: Explicitly decide whether the hidden Others sheet is included in the first-pass
      evidence boundary.
    source_hint: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx;
      hidden sheet Others
  skill_ids: []
  limits: {}
- stage_id: category-screen
  objective: Compare candidate Personal Care categories on growth, scale, consumer
    relevance, portfolio fit, and competitive or launch signals.
  participants:
  - analyst
  subtasks: []
  dependencies:
  - source-audit
  expected_result: A reproducible category scorecard with sensitivity to alternative
    weights and explicit unresolved assumptions.
  research_needs:
  - kind: QUANTITATIVE_ANALYSIS
    query: Calculate MAT TY versus MAT YA and MAT 2YA growth, scale, and category
      contribution for candidate categories.
    source_hint: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx;
      sheet Personal Care
  - kind: QUANTITATIVE_ANALYSIS
    query: Compare ecommerce growth, new-launch intensity, and survival of new launches
      by candidate category.
    source_hint: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx;
      sheet Ecommerce
  - kind: EXISTING_EVIDENCE
    query: Connect consumer essentiality, face or body care relevance, price-tier
      movement, and Cosluxe portfolio fit to category hypotheses.
    source_hint: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx;
      sheets Consumer and Case
  skill_ids: []
  limits: {}
- stage_id: channel-screen
  objective: Determine which traditional trade, modern trade, and ecommerce channels
    should lead, follow, or support the entry plan across 2023-2025.
  participants:
  - analyst
  subtasks: []
  dependencies:
  - source-audit
  expected_result: A phased channel recommendation linked to shopper reach, frequency,
    store economics, regional dynamics, and category fit.
  research_needs:
  - kind: QUANTITATIVE_ANALYSIS
    query: Compare Personal Care value sales and growth across modern trade, traditional
      trade, and ecommerce.
    source_hint: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx;
      sheets Channel Dynamic, Trad.Trade, Modern Trade, Ecommerce
  - kind: EXISTING_EVIDENCE
    query: Reconcile channel penetration and shopping frequency with store-universe
      and regional or urban-rural dynamics.
    source_hint: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx;
      sheets Consumer, Modern Trade, Trad.Trade
  - kind: VALIDATION
    query: Test whether proposed phasing is consistent with the chosen category's
      launch and distribution requirements.
    source_hint: Derived category-channel scorecard
  skill_ids: []
  limits: {}
- stage_id: joint-validation
  objective: Test the interaction between category attractiveness and channel phasing
    before committing to a recommendation.
  participants:
  - analyst
  subtasks: []
  dependencies:
  - category-screen
  - channel-screen
  expected_result: A joint category-channel assessment with explicit trade-offs, alternative
    weights, and conditional growth logic.
  research_needs:
  - kind: VALIDATION
    query: Reconcile category choice, channel sequence, consumer relevance, portfolio
      fit, and the conditional 8% growth bridge.
    source_hint: Outputs from source-audit, category-screen, and channel-screen
  skill_ids: []
  limits: {}
- stage_id: challenge-synthesis
  objective: Challenge the recommendation, expose contradictions, and prepare a reviewable
    executive-story outline.
  participants:
  - analyst
  - reviewer
  subtasks: []
  dependencies:
  - joint-validation
  expected_result: A reviewed recommendation outline with evidence links, assumptions,
    risks, triggers, and no unsupported claims.
  research_needs:
  - kind: VALIDATION
    query: Challenge the recommendation against alternative categories, channel phasing,
      data limitations, and the 8% growth target.
    source_hint: All prior stage outputs and the supplied workbook
  - kind: ARTIFACT_OUTPUT
    query: Produce an executive presentation outline within the suggested maximum
      of 20 slides.
    source_hint: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx;
      sheet Case
  skill_ids: []
  limits: {}
horizon: 2023 entry; 2023-2025 channel plan; stable-growth planning from 2024 onward
consequence_level: high
user_preferences:
  evidence_basis: supplied_workbook_first
  review: independent
  audience: Cosluxe Nature business-planning and strategy stakeholders
  presentation_limit_slides: 20
---

# Work Brief

> Generated from the canonical WorkBrief fields.
> Revise the structured WorkBrief rather than editing this generated body.

## Decision

Which Personal Care category should Cosluxe Nature enter first in Vietnam, and which channels should it prioritize across 2023-2025 to support stable growth of at least 8% from 2024 onward?

## Context

- Investigation: ncc-2022-cosluxe-vietnam-entry
- Horizon: 2023 entry; 2023-2025 channel plan; stable-growth planning from 2024 onward
- Consequence level: high

## Scope

- Vietnam Personal Care category performance in offline channels using MAT 2YA, MAT YA, and MAT TY measures ending September 2022.
- Vietnam Personal Care ecommerce category growth, new launches, and survival of new launches.
- Vietnam consumer price-tier movement, essential and routine category perceptions, channel penetration, and shopping frequency.
- Vietnam traditional-trade regional and urban-rural dynamics, modern-trade store universe, and channel value sales.
- Cosluxe Nature portfolio focus, premium image, and natural-ingredient positioning as stated in the case materials.

## Evidence and research needs

- [STRUCTURED_DATA] Inspect the Case and Glossary sheets for business objectives, category definitions, source notes, and period conventions. (source: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx; sheets Case and Glossary)
- [STRUCTURED_DATA] Inventory measures, units, and source notes across Macro & FMCG, Personal Care, Consumer, Channel Dynamic, Trad.Trade, Modern Trade, and Ecommerce. (source: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx; sheets Macro & FMCG, Personal Care, Consumer, Channel Dynamic, Trad.Trade, Modern Trade, Ecommerce)
- [VALIDATION] Confirm whether offline, ecommerce, value, volume, store, penetration, and frequency measures can be compared directly. (source: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx; source notes and headers)
- [STRUCTURED_DATA] Explicitly decide whether the hidden Others sheet is included in the first-pass evidence boundary. (source: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx; hidden sheet Others)
- [QUANTITATIVE_ANALYSIS] Calculate MAT TY versus MAT YA and MAT 2YA growth, scale, and category contribution for candidate categories. (source: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx; sheet Personal Care)
- [QUANTITATIVE_ANALYSIS] Compare ecommerce growth, new-launch intensity, and survival of new launches by candidate category. (source: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx; sheet Ecommerce)
- [EXISTING_EVIDENCE] Connect consumer essentiality, face or body care relevance, price-tier movement, and Cosluxe portfolio fit to category hypotheses. (source: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx; sheets Consumer and Case)
- [QUANTITATIVE_ANALYSIS] Compare Personal Care value sales and growth across modern trade, traditional trade, and ecommerce. (source: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx; sheets Channel Dynamic, Trad.Trade, Modern Trade, Ecommerce)
- [EXISTING_EVIDENCE] Reconcile channel penetration and shopping frequency with store-universe and regional or urban-rural dynamics. (source: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx; sheets Consumer, Modern Trade, Trad.Trade)
- [VALIDATION] Test whether proposed phasing is consistent with the chosen category's launch and distribution requirements. (source: Derived category-channel scorecard)
- [VALIDATION] Reconcile category choice, channel sequence, consumer relevance, portfolio fit, and the conditional 8% growth bridge. (source: Outputs from source-audit, category-screen, and channel-screen)
- [VALIDATION] Challenge the recommendation against alternative categories, channel phasing, data limitations, and the 8% growth target. (source: All prior stage outputs and the supplied workbook)
- [ARTIFACT_OUTPUT] Produce an executive presentation outline within the suggested maximum of 20 slides. (source: data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx; sheet Case)

## Assumptions

- Vietnam entry begins in 2023 and stable-growth planning begins from 2024 onward.
- Workbook facts retain their stated source, period, units, and dummy-case status.
- First entry category means the initial priority category, not exclusion of the remainder of the portfolio.
- Offline and ecommerce measures are not comparable until definitions, periods, and units are normalized.
- The 8% growth ambition is a planning target, not an observed result.

## Open dependencies

- Confirm launch budget, margin, supply, distribution, and portfolio-cannibalization constraints with the client.
- Confirm whether the recommendation optimizes revenue, profit, market share, reach, or a weighted combination.
- Confirm acceptable external desk-research scope and evidence-quality threshold for claims beyond the workbook.
- Reconcile category definitions and channel boundaries across the named workbook sheets.
- Validate whether the 2023-2025 horizon and 2024 growth baseline match the client's planning calendar.

## Proposed investigation

### source-audit

- Objective: Inventory workbook sources, definitions, periods, units, and comparability limits before calculating attractiveness.
- Participants: analyst
- Subtasks: not specified
- Dependencies: not specified
- Expected result: A source and metric dictionary with observed-versus-derived labels and unresolved comparability issues.
- Skills: not specified
- Execution intent:
- not specified

### category-screen

- Objective: Compare candidate Personal Care categories on growth, scale, consumer relevance, portfolio fit, and competitive or launch signals.
- Participants: analyst
- Subtasks: not specified
- Dependencies: source-audit
- Expected result: A reproducible category scorecard with sensitivity to alternative weights and explicit unresolved assumptions.
- Skills: not specified
- Execution intent:
- not specified

### channel-screen

- Objective: Determine which traditional trade, modern trade, and ecommerce channels should lead, follow, or support the entry plan across 2023-2025.
- Participants: analyst
- Subtasks: not specified
- Dependencies: source-audit
- Expected result: A phased channel recommendation linked to shopper reach, frequency, store economics, regional dynamics, and category fit.
- Skills: not specified
- Execution intent:
- not specified

### joint-validation

- Objective: Test the interaction between category attractiveness and channel phasing before committing to a recommendation.
- Participants: analyst
- Subtasks: not specified
- Dependencies: category-screen, channel-screen
- Expected result: A joint category-channel assessment with explicit trade-offs, alternative weights, and conditional growth logic.
- Skills: not specified
- Execution intent:
- not specified

### challenge-synthesis

- Objective: Challenge the recommendation, expose contradictions, and prepare a reviewable executive-story outline.
- Participants: analyst, reviewer
- Subtasks: not specified
- Dependencies: joint-validation
- Expected result: A reviewed recommendation outline with evidence links, assumptions, risks, triggers, and no unsupported claims.
- Skills: not specified
- Execution intent:
- not specified

## Deliverables

- A traceable category-attractiveness screen identifying a provisional first-entry category and its evidence.
- A three-year channel-prioritization and phasing recommendation for 2023-2025.
- Target consumer, price-tier, and premium-natural positioning hypotheses with explicit assumptions.
- A conditional growth bridge showing whether the proposed category-channel choices could support the 8% planning target from 2024 onward.
- Risks, evidence gaps, trigger conditions, and an executive presentation outline within the case's suggested maximum of 20 slides.

## Current direction

Build a traceable category-by-channel scorecard and keep any recommendation provisional until category growth, portfolio fit, consumer relevance, channel dynamics, competitive intensity, and execution constraints are reconciled.

## Next step

Normalize MAT TY versus MAT YA and MAT 2YA measures, reconcile them with channel and consumer evidence, and open the category and channel decision questions for review.
