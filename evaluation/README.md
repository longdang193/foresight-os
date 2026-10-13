# Evaluation Contract

Evaluation has three independent records:

- **Capability**: whether a native pattern is implemented and available in the
  current runtime.
- **Selection**: which ordered `RecipeStage` sequence the Controller chose for
  a Work Brief.
- **Measurement**: what one candidate Run measured for quality, latency, calls,
  retries, failures, and human correction.

Measurement can tune defaults and budgets; it never changes the capability
record or makes a slower pattern unsupported.

Each candidate record keeps pattern support and runtime availability separate
from Controller selection and measured output. The scorer consumes the selected
recipe output only; a missing or failed recipe output is not silently replaced
with the vertical-slice baseline. Measurements include model calls, tool calls,
duplicate retrievals, latency, parallelism, run-scoped capability reuse,
human correction, quality, and cleanup state.

The contract and Controller matrices are executable gates: a selection or
support/availability mismatch exits nonzero rather than producing a passing
report.

The v0.1 benchmark uses one synthetic workbook case and one frozen rubric. It
compares three levels without changing the decision question:

- **A — ordinary prompt:** a capable single agent receives the workbook, the
  decision question, ordinary instructions, and source tools. It does not
  receive a Work Brief, evidence schema, Wayfinding contract, or structured
  evidence requirements.
- **B — semantic:** the same agent receives the same workbook, question, and
  source tools plus the Work Brief, evidence schema, Wayfinding contract, and
  evidence requirements.
- **C — coordination:** level B inputs plus one tested coordination pattern.

The same rubric and human/reference adjudication apply to all three levels.
Level B and C share the evidence contract; level A is judged on the same
outcomes without being forced to emit structured evidence.

The case is synthetic and contains no customer data or external dependencies.

## Probe tiers

- Pull requests run deterministic tests, package-resource checks, the contract
  and Controller matrices, and the anomaly probe without credentials.
- Nightly jobs may run the disposable MCP fixture and fixed-seed anomaly/soak
  checks.
- `web_search` is a runtime capability, not a probe-only feature. The hosted-web
  probe exercises its provider adapter, authorization, instrumentation, and
  `EvidenceCandidate` output.
- The configured adapter uses `FORESIGHT_WEB_SEARCH_URL` and optional
  `FORESIGHT_WEB_SEARCH_TOKEN`; it accepts a JSON POST body with `query`,
  `max_results`, and optional `freshness`, and returns a `results` array with
  `title`, `url`, and `snippet` fields.
- Crawl4AI is available as an optional `web_crawl` capability for MAF agents; the live probe exercises public-destination validation, sanitized extraction, provenance, MAF tool injection, and scope cleanup.
- GitHub MCP, Alpha Vantage MCP, and FRED MCP are available as MAF-agent-only
  capabilities named `technology_signals`, `market_signals`, and
  `macro_signals`. Their live probe discovers the hosted MCP catalog, invokes a
  bounded read operation, records only sanitized receipt metadata, and closes
  the run-owned MCP resource.
- `run_external_signal_probe.py` uses `GITHUB_MCP_TOKEN`,
  `ALPHAVANTAGE_API_KEY`, and `FRED_MCP_TOKEN`. For local smoke testing only,
  `FORESIGHT_ALLOW_ALPHA_DEMO=1` enables Alpha Vantage's public demo credential;
  that receipt is explicitly marked non-production-ready. FRED's OAuth-protected
  endpoint also requires `FRED_MCP_READ_TOOL` and
  `FRED_MCP_READ_ARGS_JSON` for a safe operation probe.
- A local SearXNG adapter is available through the same capability boundary:
  set `FORESIGHT_WEB_SEARCH_PROVIDER=searxng` and point
  `FORESIGHT_WEB_SEARCH_URL` at the SearXNG base URL. The adapter requests
  `/search?format=json`, maps SearXNG `content` and `publishedDate` fields to
  the canonical candidate shape, and preserves the same public-scope and
  sanitized-evidence rules.
- Real MCP and provider-backed web search require environment-gated adapters.
  Missing approved configuration is reported as `BLOCKED_EXTERNAL`, never as a
  passing fake result.
- XLSX inspection is a release requirement, not an optional probe. The fixed
  multi-sheet fixture proves sheet/row visibility, table and range selection,
  merged headers, dates, types, errors, formulas versus cached values,
  cross-sheet references, duplicate/null/scenario analysis, cell/range
  provenance, cancellation limits, and SHA256 equality before and after read.
- `run_toolbelt_probe.py`, `run_evidence_workflow_probe.py`, and
  `run_xlsx_probe.py` are deterministic local receipts. `run_mcp_probe.py`
  proves the disposable protocol boundary; `run_foresight_mcp_probe.py`
  separately proves the Controller-to-MCP path.

Probe reports retain endpoint hosts, source identity, timestamps, typed
metadata, metrics, and cleanup status only. Tokens, prompts, headers, and raw
external payloads are not durable evidence.
