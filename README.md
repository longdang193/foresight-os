# Foresight OS v0.1

Foresight OS is a small evidence-aware strategic reasoning prototype. Its
runtime vocabulary is intentionally separate from the build document:

`Investigation → Work Brief → Execution Recipe → Run → Analysis State → Artifact`

The current prototype provides:

- a synthetic workbook evaluation case;
- validated Work Brief and Analysis State persistence in `brief.md` and
  `analysis.json`;
- native Microsoft Agent Framework workflow chaining for local deterministic
  analyst/reviewer steps;
- bounded Controller recipes and explicit budget exhaustion;
- dependency invalidation, fresh-process continuation, and stale-artifact
  protection;
- one local client adapter over the canonical commands.

Provider/model execution is not exercised without authentication or network
access. `Concurrent` and `Handoff` remain evaluation-only probes and are
deferred because the frozen case shows no measurable value over sequential
review within the accepted budget.

The second client is a v0.2 stretch item. All clients must consume the same
durable state and must not own analytical truth.
