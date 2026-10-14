# Execution Approval Package Example

This example is derived from the persisted `brief.md` and
`execution-recipe.json`. The approval record stores only the canonical
projection, its fingerprint, and the local CLI approval metadata.

The Markdown is a generated review view. It includes captured assumptions,
unknowns, user intent, selected skills, resolved stage controls, budgets,
review rules, reuse decisions, and the approved adaptation envelope. Missing
captured values remain `not specified` or `unavailable`; the renderer does not
consult mutable registry defaults or invent provider payloads.

```text
Question: What decision should be made?
Pattern: sequential
Fingerprint: <displayed projection fingerprint>
Approval source: local_cli
Stale reuse fallback: stop
```
