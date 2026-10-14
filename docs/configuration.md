# Configuration

ForesightOS reads runtime configuration from inherited environment variables.
The committed `.env.example` is the variable inventory and safe starting point;
it is not a credential store.

## Local setup

```text
copy .env.example .env
```

The normal runtime does not load `.env` automatically. Load it through the
shell, IDE, CI job, or deployment secret manager that launches the process. The
live provider probe is different: it accepts an explicit `--env-file` and then
merges non-empty inherited variables over values read from that file.

Never commit `.env`, place production credentials in `.env.example`, or write
tokens into analysis state and receipts.

## Configuration groups

### Web search

- `FORESIGHT_WEB_SEARCH_PROVIDER` selects the configured JSON POST provider or
  `searxng`.
- `FORESIGHT_WEB_SEARCH_URL` is the required HTTP(S) endpoint.
- `FORESIGHT_WEB_SEARCH_TOKEN` is an optional bearer token.
- `FORESIGHT_SEARXNG_CATEGORIES` and `FORESIGHT_SEARXNG_LANGUAGE` tune SearXNG
  requests.

The runtime validates the endpoint scheme and response envelope. A web-search
capability is not available merely because a variable name exists; the endpoint
must be configured and the provider must return the expected result shape.

### Hosted signal providers

The optional MCP-backed capabilities use these credentials:

| Capability | Credential | Boundary rule |
|---|---|---|
| Technology signals | `GITHUB_MCP_TOKEN` | Uses the configured read-only GitHub tool allowlist. |
| Market signals | `ALPHAVANTAGE_API_KEY` | Uses the Alpha Vantage query credential and allowed operations. |
| Macro signals | `FRED_MCP_TOKEN` | Requires an explicit read-only operation allowlist. |

Endpoint overrides are available through `FORESIGHT_GITHUB_MCP_URL`,
`FORESIGHT_ALPHA_VANTAGE_MCP_URL`, and `FORESIGHT_FRED_MCP_URL`. FRED also
requires `FRED_MCP_READ_TOOL` and, when needed, `FRED_MCP_READ_ARGS_JSON`.
Providers are created selectively for required capabilities; missing
credentials remain an explicit unavailable or `BLOCKED_EXTERNAL` boundary.

### Probe-only variables

`FORESIGHT_ALLOW_ALPHA_DEMO` controls the local demo allowance. The real
boundary probes accept `FORESIGHT_REAL_WEB_QUERY`, `FORESIGHT_REAL_MCP_URL`,
`FORESIGHT_REAL_MCP_TOKEN`, and `FORESIGHT_REAL_MCP_QUERY`. These variables
support evidence collection; they do not make external evidence part of the
credential-free local analysis path.

## Provider and secret handling

Provider fingerprints may identify an endpoint and a credential digest for
provenance, but credentials themselves are not persisted. External results must
cross the evidence-validation boundary before becoming durable state. Raw
payloads, prompts, tokens, and authorization headers stay out of receipts.

The source of truth for available variables is `.env.example`; the source of
truth for provider behavior is the corresponding runtime adapter under
`src/foresight_os/runtime/`.
