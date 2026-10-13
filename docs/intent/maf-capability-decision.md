# MAF Capability Decision

Status: MAF package installed; provider/model execution is proven through the
configured custom `9router` OpenAI-compatible endpoint.

## Observed local boundary

The local Python environment provides `agent-framework==1.21.0`. A bounded
live probe reads the active provider, model, and base URL from Codex
`config.toml`, reads the configured key assignment from the repository `.env`,
and uses MAF's `OpenAIChatClient` transport. This proves transport
compatibility for custom OpenAI-compatible providers; it does not imply that
MAF only supports OpenAI or Anthropic.

## Capability matrix

| Capability | Decision | Evidence and limit |
| --- | --- | --- |
| Single agent | `ADAPT_AT_BOUNDARY` | Live `9router` call through MAF completed with the configured `combo-high` model. |
| Sequential | `USE_NATIVE` | `agent_framework.orchestrations.SequentialBuilder` imports and bounded workflow tests. |
| Concurrent | `USE_NATIVE` | `agent_framework.orchestrations.ConcurrentBuilder` imports; branch limits remain Controller-owned. |
| Handoff | `USE_NATIVE` | `agent_framework.orchestrations.HandoffBuilder` imports; allowed destinations remain recipe-owned. |
| Group Chat | `USE_NATIVE` | `agent_framework.orchestrations.GroupChatBuilder` imports; round and termination limits remain recipe-owned. |
| Human input | `ADAPT_AT_BOUNDARY` | `AgentExecutorRequest` imports; user interaction remains a client boundary. |
| Structured output | `ADAPT_AT_BOUNDARY` | Live `9router` call returned the typed `ProbeReply` through MAF response-format handling. |
| Checkpoint/restart | `USE_NATIVE` | `WorkflowCheckpoint` round-trips through native `FileCheckpointStorage`; process-boundary resume remains recipe-owned. |
| Web search | `ADAPT_AT_BOUNDARY` | First-class `web_search` capability uses an injected provider adapter, public-scope authorization, runtime instrumentation, and validated `EvidenceCandidate` results; provider availability remains environment-owned. |
| Page retrieval | `ADAPT_AT_BOUNDARY` | Bounded HTTP(S) retrieval revalidates redirects and public destinations, strips raw payloads, and issues retrieval-only proof before durable evidence normalization. |
| Crawl4AI web crawl | `ADAPT_AT_BOUNDARY` | Optional Crawl4AI binding is injected as a read-only MAF agent tool, validates public destinations, bounds extracted evidence, and issues crawl retrieval proof before durable evidence normalization. |
| GitHub MCP signals | `ADAPT_AT_BOUNDARY` | Hosted Streamable HTTP MCP tool is injected into MAF agents under `technology_signals`; the integration restricts the advertised catalog to read-only repository, code, issue, release, and search operations. |
| Alpha Vantage MCP signals | `ADAPT_AT_BOUNDARY` | Hosted Streamable HTTP MCP tool is injected into MAF agents under `market_signals`; the integration uses the provider's API-key query authentication and a bounded read-only allowlist. |
| FRED MCP signals | `ADAPT_AT_BOUNDARY` | OAuth-protected hosted Streamable HTTP MCP tool is injected into MAF agents under `macro_signals`; activation remains credential- and operation-configured, with the provider endpoint treated as read-only by policy. |
| Spreadsheet read | `USE_NATIVE` | Core `openpyxl` binding returns typed multi-sheet workbook data with hidden-content, formula/cache, cell/range provenance, and source-integrity checks. |
| Data analysis | `USE_NATIVE` | Deterministic bounded table operations cover nulls, duplicates, comparisons, scenarios, and sensitivity ordering. |
| Calculation | `USE_NATIVE` | Reproducible calculations preserve formula, units, input IDs, and block unusable formula caches. |
| Graph context | `USE_NATIVE` | Bounded provenance and impact context reuse the existing indexed graph query owner. |
| Domain validation | `USE_NATIVE` | Existing evidence and analysis validation remain the persistence gate. |
| Document read | `UNSUPPORTED` | Registered semantic ID with an explicit unavailable result; adapter deferred. |
| Internal knowledge | `UNSUPPORTED` | Registered semantic ID with explicit internal-scope denial/unavailable result; adapter deferred. |
| Artifact generation | `UNSUPPORTED` | Registered semantic ID with explicit unavailable result; mutation adapter deferred. |
| Magentic | `DEFER` | Explicitly outside the current bounded scope; it is not part of the supported pattern contract. |

## Shared vertical-slice guardrail

- `max_agent_steps`: 5 per role
- `max_correction_rounds`: 1
- `max_total_agent_calls`: 3
- exhaustion: no accepted recommendation; route to a human decision/review
  boundary

## Live probe evidence

On October 12, 2026, the bounded probe was run with the repository `.env` and
the active Codex `config.toml`:

```text
provider=9router
model=combo-high
base_url=http://127.0.0.1:17667/v1
agent-framework=1.21.0
success=true
structured_output=true
latency_ms=3480
```

The probe reports metadata only. It does not print the key, prompt, response
content, headers, or request body.

The native pattern surface is bounded to Direct, Sequential, Concurrent, Handoff,
and Group Chat; Magentic is not part of this delivery. Task 3 may activate
against the proven local and provider contract. Any task
requiring a real provider call must retain the explicit provider, model,
endpoint, authentication, timeout, and bounded-call boundary. Providers that
implement the OpenAI-compatible API can use the same MAF client path; provider
specific extensions remain outside this probe.

The completed delivery also exercised sanitized native smokes for Sequential,
Concurrent, Handoff, and Group Chat. These records establish bounded completion
against the configured provider boundary; native `RunMetrics` model-call,
handoff, and chat-round counters now come from MAF workflow events. The cleanup
flag is set only after every agent close attempt completes without error, but it
is not an independent provider settlement receipt. In particular, a successful
Handoff smoke can still report zero transfers when the provider does not select
one. Treat these results as capability smoke evidence, not a guarantee of
provider-specific behavior.

Evaluation records preserve four independent facts: pattern support, runtime
availability, Controller selection, and measured run output. Contract and
Controller matrices fail closed on mismatches. Benchmark measurements can tune
budgets and defaults, but cannot downgrade an implemented pattern or change
capability admission. Candidate scoring consumes the selected recipe output and
records sanitized quality, latency, model/tool, reuse, correction, and cleanup
dimensions only.

## External proof tiers

The disposable MCP fixture is the credential-free protocol proof. The hosted-web
probe exercises the first-class `web_search` capability through its configured
provider adapter. `run_external_signal_probe.py` separately exercises the
hosted GitHub, Alpha Vantage, and FRED MCP boundaries through injected MAF
tools. Each external provider requires its own approved environment
configuration and actual invocation.
Missing configuration is `BLOCKED_EXTERNAL`, not a synthetic success. Reports
retain only endpoint host, source identity, retrieval time, typed candidate
metadata, metrics, and cleanup status; credentials, prompts, headers, and raw
payloads are excluded.
