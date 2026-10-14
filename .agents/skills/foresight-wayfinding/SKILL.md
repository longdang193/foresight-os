---
name: foresight-wayfinding
description: Use when strategic foresight intake needs question clarification, bounded source inspection, or WorkBrief creation/refinement before execution.
---

# ForesightOS Strategic Wayfinding

Use this repository-local host procedure for strategic foresight intake. It is
a thin navigation layer around the typed ForesightOS contracts, not a second
workflow engine, analytical store, runtime skill registry, or planning map.

## Boundary

```text
strategic question
  -> clarify intent and constraints
  -> inspect supplied material enough to frame the work
  -> create/refine WorkBrief through foresight_os.wayfinding
  -> ask the Controller for an ExecutionRecipe
  -> render the brief and approval package
  -> stop for human review and approval
```

Wayfinding is complete when the WorkBrief and execution proposal are ready for
human review. It does not answer the substantive strategic questions that the
approved investigation is meant to answer.

## Procedure

1. Clarify the decision question, objective, horizon, scope, deliverables,
   assumptions, unknowns, and evidence boundary.
2. Inspect supplied files only enough to identify source structure, definitions,
   periods, units, likely research needs, and material limitations.
3. Use `foresight_os.wayfinding.create_work_brief()` or
   `refine_work_brief()` as the typed owner. Supply optional method provenance
   from the host when available; the Python package must not read or hash this
   skill file itself.
4. Record only explicit human constraints as required execution intent. Put
   inferred topology, capabilities, tools, and recommended patterns in research
   needs, preferences, or structural stage dependencies for the Controller.
5. Preserve genuine investigation dependencies. Do not force Sequential,
   Concurrent, Group Chat, or a capability merely because it appears useful.
6. Ask the Controller to resolve the exact ExecutionRecipe and render the
   human-readable brief and approval package from canonical state.
7. Stop before substantive execution. Human approval is required before the
   execution gate may dispatch the investigation.

## Source and artifact rules

- Treat `brief.md` YAML front matter as the canonical WorkBrief contract.
- Treat the Markdown body as generated; revise the typed WorkBrief rather than
  editing the rendered body as if it changed execution state.
- Do not create or require generic `map.md`. An optional derived artifact may
  be named `decision-map.md` when a human needs that view.
- For XLSX inputs, identify exact sheet names and express workbook inspection
  as structured-data research needs; do not invent document-reader needs.
- Keep growth, feasibility, and recommendation claims conditional when inputs
  such as budget, margin, supply, distribution, or external evidence are open.

## Completion check

Before handing off for review, confirm:

- the WorkBrief is valid and round-trips through `AnalysisStore`;
- the proposal is derived by the Controller;
- the human brief and approval package are regenerated from canonical fields;
- provenance is descriptive metadata, not authority;
- unresolved inputs and limitations are visible; and
- no execution begins without explicit human approval.
