# Foresight OS v0.1

Foresight OS is a small evidence-aware strategic reasoning prototype. Its
runtime vocabulary is intentionally separate from the build document:

`Investigation → Work Brief → Execution Recipe → Run → Analysis State → Artifact`

The current prototype provides:

- a synthetic workbook evaluation case;
- validated Work Brief and Analysis State persistence in `brief.md` and
  `analysis.json`;
- native Microsoft Agent Framework Direct, Sequential, Concurrent, Handoff, and
  Group Chat pattern contracts with bounded Controller recipes;
- explicit budget exhaustion and settled run metrics;
- dependency invalidation, fresh-process continuation, and stale-artifact
  protection;
- one local client adapter over the canonical commands.

Provider/model execution is proven through the configured custom `9router`
OpenAI-compatible endpoint with one bounded structured-output probe.
Pattern support is separate from measurement: evaluation results tune defaults
and budgets but do not disable an implemented pattern. The configured custom
`9router` provider remains the live-probe boundary.

The second client is a v0.2 stretch item. All clients must consume the same
durable state and must not own analytical truth.
