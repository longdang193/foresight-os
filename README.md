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
- bounded `page_retrieval` with SSRF checks and adapter-issued retrieval proof;
- deterministic Analyst toolbelt bindings for CSV/XLSX inspection, table
  analysis, calculations, graph context, and domain validation;
- mandatory multi-sheet XLSX release proof covering hidden content, formulas
  versus cached values, dates/errors, merged headers, cross-sheet references,
  provenance, scenarios, cancellation limits, and unchanged source bytes;
- provenance-bearing `EvidenceCandidate` normalization before durable evidence;
- dependency invalidation, fresh-process continuation, and stale-artifact
  protection;
- relation-aware, bounded NetworkX graph context rebuilt from durable
  relationships;
- six bundled analytical method skills with manifest hashes and stage-local
  injection; no runtime skill downloads;
- immutable review records bound to material-input fingerprints and derived
  finding views; accepted recommendations require a current accepted review;
- committed stage-cache reuse that preserves dependency order and skips new
  model/tool calls for complete hits;
- one local client adapter over the canonical commands.

Provider/model execution is proven through the configured custom `9router`
OpenAI-compatible endpoint with one bounded structured-output probe.
Pattern support is separate from measurement: evaluation results tune defaults
and budgets but do not disable an implemented pattern. The configured custom
`9router` provider remains the live-probe boundary.

The first-class `web_search` capability accepts a provider adapter through
`FORESIGHT_WEB_SEARCH_URL` and optional `FORESIGHT_WEB_SEARCH_TOKEN`. The
default `json-post` provider accepts a JSON POST request with `query`,
`max_results`, and optional `freshness`, and returns
`{"results": [{"title", "url", "snippet"}]}`. A local SearXNG instance can be
selected explicitly with `FORESIGHT_WEB_SEARCH_PROVIDER=searxng`; point the
same URL at its base URL, such as `http://127.0.0.1:8888`, and optionally set
`FORESIGHT_SEARXNG_CATEGORIES` or `FORESIGHT_SEARXNG_LANGUAGE`. Search results
are discovery candidates only: a source must pass bounded
`page_retrieval` and carry adapter-issued retrieval proof before it can enter
durable analysis state. Source credibility remains a separate human decision.

The semantic registry contains `web_search`, `page_retrieval`, `web_crawl`,
`spreadsheet_read`, `data_analysis`, `calculation`, `graph_context`, and
`domain_validation`, plus explicitly unavailable `document_read`,
`internal_knowledge`, and `artifact_generation` follow-ups.

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

## External Signal MCP Integrations

Foresight exposes three hosted, read-only signal providers as MAF-agent tools
through the vendor-neutral `technology_signals`, `market_signals`, and
`macro_signals` capabilities. The controller never calls these providers
directly. Credentials are read at run time and are never written to receipts.

- **GitHub MCP** — technology, repository, ecosystem, and competitor signals;
  configure `GITHUB_MCP_TOKEN` or use the local `gh` keyring only for a probe.
- **Alpha Vantage MCP** — market and financial foresight; configure
  `ALPHAVANTAGE_API_KEY`.
- **FRED MCP Connector** — macroeconomic and quantitative foresight; configure
  the OAuth bearer token in `FRED_MCP_TOKEN` plus a bounded read operation for
  the live probe. Activation also requires `FRED_MCP_READ_TOOL`; only that
  explicitly allowlisted tool is exposed to the MAF agent.

Run `python evaluation/probes/run_external_signal_probe.py --output-root
work/toolbelt-probes` to verify MAF injection, remote discovery, a bounded
read-only call, result sanitization, and scope cleanup. Missing credentials are
reported as `BLOCKED_EXTERNAL`; a successful transport with a public demo key
is not considered production credential readiness.

### Local environment setup

Use the committed `.env.example` as the variable inventory for local work:

```text
copy .env.example .env
```

The runtime reads inherited environment variables and does not load `.env`
automatically. This keeps production behavior explicit: local shells may load
`.env` through their own tooling, while CI and deployments inject secrets from
their secret manager. Do not commit `.env`; it is ignored by Git. MCP
subprocesses must receive the same variables through their launcher rather than
assuming that a parent application's `.env` loader is inherited.

## MAF-Agent Web Crawling

Crawl4AI is activated as the optional `web_crawl` capability for MAF agents. It
provides bounded crawling for company reports, policy websites, and hard-to-extract
pages. Crawl results pass public-destination validation, provenance normalization,
read-only authorization, raw-payload stripping, and scope-owned cleanup before
they can become durable evidence.
External MCP results must enter the same sanitized evidence boundary as web
search: no raw payloads in durable analysis state, explicit source identity,
retrieval time, query provenance, read-only authorization, and independent
`VERIFIED`/`BLOCKED_EXTERNAL`/`FAILED` receipts.

## Optimization release evidence

The optimization probe records the frozen baseline and release receipts under ignored `work/optimization-baseline/` and `work/optimization-release/`.

- Baseline: `python evaluation/probes/run_optimization_probe.py --mode baseline --output work/optimization-baseline/receipt.json`
- Release: `python evaluation/probes/run_optimization_probe.py --mode release --output work/optimization-release/receipt.json`
- Acceptance is frozen at two warmups and ten measured runs per MAF pattern, with p95/event-loop regressions capped at 20%, peak allocation at 15%, no tool-call increase per accepted finding, and a 100-run no-growth soak.
- Compare receipts with `python evaluation/probes/compare_optimization_receipts.py --baseline work/optimization-plan/baseline/receipt.json --release work/optimization-plan/release/receipt.json`.
- `CapabilityScope` owns run-scoped semaphores, bounded blocking execution, cancellation settlement, workbook reuse, and cleanup. Native MCP tools use public Agent Framework middleware; local XLSX reads remain read-only and preserve source-path provenance.
- Browser crawling keeps certificate validation enabled, validates each destination and same-host DNS change, and uses native WebSocket/service-worker controls.
