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
