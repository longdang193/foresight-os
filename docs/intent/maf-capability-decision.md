# MAF Capability Decision

Status: MAF package installed; provider/model execution remains an explicit
boundary because no authentication or network/model access was requested.

## Observed local boundary

The local Python environment now provides `agent-framework==1.21.0`. No
authentication, network/model access, or custom orchestration fallback was
performed. The probe verifies importable native boundaries and local
checkpoint persistence only.

## Capability matrix

| Capability | Decision | Evidence and limit |
| --- | --- | --- |
| Single agent | `ADAPT_AT_BOUNDARY` | `Agent` API imports; provider execution is not exercised. |
| Sequential review | `USE_NATIVE` | `WorkflowBuilder` chaining API imports. |
| Human input | `ADAPT_AT_BOUNDARY` | `AgentExecutorRequest` imports; user interaction remains a client boundary. |
| Structured output | `ADAPT_AT_BOUNDARY` | `Agent.run` exposes provider structured-output options; provider execution is not exercised. |
| Checkpoint/restart | `USE_NATIVE` | `WorkflowCheckpoint` round-trips through `InMemoryCheckpointStorage`. |
| Group Chat | `DEFER` | Explicitly outside the v0.1 scope. |
| Magentic | `DEFER` | Explicitly outside the v0.1 scope. |

## Shared vertical-slice guardrail

- `max_agent_steps`: 5 per role
- `max_correction_rounds`: 1
- `max_total_agent_calls`: 3
- exhaustion: no accepted recommendation; route to a human decision/review
  boundary

Task 3 may activate against the proven local contract. Any task requiring a
real provider call must retain the explicit authentication/model boundary and
must not claim provider execution from this local probe alone.
