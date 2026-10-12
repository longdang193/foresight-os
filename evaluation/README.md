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
