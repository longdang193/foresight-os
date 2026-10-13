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

## Skill exercise evaluation

The bundled skill layer has one manifest-owned runtime source and one
fixture-owned evaluation source. The nine files under `evaluation/skills/`
contain routing examples and expected observable output properties; they are
not injected into runtime prompts. Package tests verify manifest IDs, normalized
UTF-8 content hashes, frontmatter identity, required sections, adjacent-skill
references, least-privilege capabilities, and prompt-size measurements.

Run the required offline tier with no provider or network dependency:

```text
PYTHONPATH=src py evaluation/probes/run_skill_exercise_evaluation.py --mode structural --exercise-root evaluation/cases --skill-fixture-root evaluation/skills --output-root work/skill-layer-hardening-20261014/final/structural
```

Structural mode validates the tracked `case-001` through `case-005`
reference records and reports deterministic completeness counts. It does not
claim model quality. The optional `data/exercise/` workbook tier is reported as
`BLOCKED_INPUT` when absent.

Provider mode is a separate, explicitly environment-gated path:

```text
PYTHONPATH=src py evaluation/probes/run_skill_exercise_evaluation.py --mode provider --exercise-root evaluation/cases --skill-fixture-root evaluation/skills --extended-exercise-root data/exercise --output-root work/skill-layer-hardening-20261014/final/provider
```

It uses `ParticipantConfig.skill_ids`, `SkillRegistry`, the approved provider
settings/client, and `run_recipe_async`. Missing credentials, configuration, or
the provider package produce `BLOCKED_EXTERNAL`; the report preserves the
structural result. Every report has three independent metric classes:

- `deterministic_reference`: package and frozen-reference checks;
- `provider_runtime`: provider latency, calls, failures, and cleanup facts;
- `human_rubric`: human judgments, left `not_measured` unless assessed.

Do not infer correction effort from acceptance state, provider availability, or
deterministic reference completeness. This evaluation does not change the
Controller, `AnalysisState`, `PresentationSpec`, Canva boundary, or frozen
optimization thresholds, and it does not close the separate Group Chat p95
investigation.

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
  endpoint also requires the explicit read-only allowlist `FRED_MCP_READ_TOOL` and
  `FRED_MCP_READ_ARGS_JSON` for a safe operation probe.
- `.env.example` is the committed inventory of local environment variables. The
  evaluation code reads inherited variables directly; it does not load `.env`.
  CI and production deployments must inject secrets through their secret
  manager, and missing provider credentials remain `BLOCKED_EXTERNAL`.
- A local SearXNG adapter is available through the same capability boundary:
  set `FORESIGHT_WEB_SEARCH_PROVIDER=searxng` and point
  `FORESIGHT_WEB_SEARCH_URL` at the SearXNG base URL. The adapter requests
  `/search?format=json`, maps SearXNG `content` and `publishedDate` fields to
  the canonical candidate shape, and preserves the same public-scope and
  sanitized-evidence rules.
- Real MCP and provider-backed web search require environment-gated adapters.
  Missing approved configuration is reported as `BLOCKED_EXTERNAL`, never as a
  passing fake result.
- CSV and XLSX inspection are release capabilities; XLSX inspection is a release
  requirement, not an optional probe. The fixed
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

## Optimization pass evidence

`run_optimization_probe.py` is the release-level measurement entry point. It compares cold/warm XLSX reads and all five native MAF patterns, proves a credential-free native Streamable HTTP MCP discovery path, records separate model/local/MCP/external economics, token counters, accepted-finding-normalized values, per-pattern latency components, portable RSS/resource snapshots, and runs a 100-run resource soak. Baseline and release receipts share the schema owned by `optimization_measurement.py`; missing required evidence, workload/schema mismatches, zero denominators, resource growth, or threshold regressions fail comparison closed.

`run_selective_reuse_probe.py` validates fresh-process reuse and sidecar receipt provenance. `run_strategic_exercise.py` stages participant-visible workbooks without the validator key and proves filesystem scope denial. `run_clean_wheel_smoke.py` builds and installs only the new wheel in a disposable environment outside the repository tree.

`run_full_pipeline_exercise.py` verifies the complete local XLSX path across the
five participant workbooks. It copies participant inputs into an allowlisted
scope, selects a numeric table column, runs the finding workflow with explicit
acceptance, reloads the committed state in a fresh store, and requires one
accepted `CURRENT` `FindingView` plus a persisted review record per workbook.
It also verifies source hashes remain unchanged and the validator workbook is
denied by the participant scope:

```text
python evaluation/probes/run_full_pipeline_exercise.py --exercise-root data/exercise --output-root work/closure-full-pipeline-20261013-r3
```

The optimization contract keeps blocking XLSX work off the event loop, shares run-scoped capacity and cancellation settlement, keeps provider construction selective, and uses public Agent Framework function middleware for native MCP invocations. XLSX cache entries are immutable and run-local; keys include canonical source identity, digest, selection, and effective limits. Browser controls retain certificate verification, redirect/DNS validation, WebSocket interception, and service-worker blocking.
