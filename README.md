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
- semantic capability resolution with participant-scoped tools and explicit
  unavailable/approval results;
- first-class `web_search` capability with provider adapters, public-scope
  authorization, typed evidence candidates, and sanitized provenance;
- provenance-bearing `EvidenceCandidate` normalization before durable evidence;
- dependency invalidation, fresh-process continuation, and stale-artifact
  protection;
- one local client adapter over the canonical commands.

Provider/model execution is proven through the configured custom `9router`
OpenAI-compatible endpoint with one bounded structured-output probe.
Pattern support is separate from measurement: evaluation results tune defaults
and budgets but do not disable an implemented pattern. The configured custom
`9router` provider remains the live-probe boundary.

The first-class `web_search` capability accepts a provider adapter through
`FORESIGHT_WEB_SEARCH_URL` and optional `FORESIGHT_WEB_SEARCH_TOKEN`. The
adapter accepts a JSON POST request with `query`, `max_results`, and optional
`freshness`, and returns `{"results": [{"title", "url", "snippet"}]}`. Search
results are normalized into sanitized `EvidenceCandidate` records before they
can enter durable analysis state.

Verification runs accept a disposable `--output-root`; preserved probe outputs
under `work/` are not used as evaluation storage or rewritten by default.

The second client is a v0.2 stretch item. All clients must consume the same
durable state and must not own analytical truth.

External verification is tiered: deterministic local checks are release
evidence, the disposable MCP fixture is a nightly boundary check, and the
hosted-web probe is a health check for the first-class `web_search` capability.
Provider-backed search requires explicit environment configuration; unavailable
external providers remain `BLOCKED_EXTERNAL` and are reported separately from
implementation verification.
