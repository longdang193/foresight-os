---
name: foresight-execution
description: Use after explicit human execution approval to run an approved ForesightOS investigation, persist provisional analytical results, verify recovery, and report truthful deliverable status before analytical acceptance.
---

# ForesightOS Approved Execution

Use this repository-local host procedure only after a human has approved the
displayed `WorkBrief` projection, exact `ExecutionRecipe`, and adaptation
envelope. This procedure is a lifecycle guardrail around the shared execution
gate; it is not a participant skill, a second orchestration engine, or a second
analytical store.

## Boundary

```text
approved WorkBrief + approved ExecutionRecipe
  -> preflight approval, recipe, capabilities, output contract, and persistence
  -> execute approved stages through the shared gate
  -> produce structured stage results
  -> persist recoverable provisional AnalysisState
  -> verify reload, references, hashes, and workflow StageReceipt
  -> request analytical review
  -> report deliverable status
  -> stop for human analytical acceptance
```

Runtime settlement proves runtime settlement. A committed `StageReceipt` proves
what was durably persisted. Analytical review evaluates findings, assumptions,
uncertainty, and counterevidence. Human acceptance authorizes a specific
reviewed analytical revision. These are different states.

## Preflight

Before any provider or participant call, confirm:

- execution approval is current and binds the approved brief projection,
  recipe fingerprint, and adaptation envelope;
- each stage has a recognized `analysis-stage-result/v1` output contract and a
  supported execution-pattern/output-contract combination;
- structured-output configuration is available at result production time;
- the canonical result committer and writable `AnalysisStore` are available;
- required record types, input dependencies, and capabilities resolve; and
- the run scope, skill hashes, capability fingerprints, and model policy match
  the approved package.

If preflight fails, do not spend provider calls. Return a truthful incomplete,
blocked, or failed outcome with its stage and error code.

## Result and persistence rules

- Participants produce structured `analysis-stage-result/v1` content; they do
  not author canonical IDs, durable references, or result hashes.
- The system normalizes and validates schema, source locators, relationships,
  calculation inputs, units, and deterministic calculations where possible.
- Schema validity or a known source locator does not prove that a claim is true.
  Weakly supported or uncertain interpretations may remain provisional for
  review.
- `CanonicalResultCommitter` merges provisional state through `AnalysisStore`,
  reloads and verifies it, and returns a verified canonical result.
- The existing workflow is the only writer of `StageReceipt`; a receipt never
  means that a conclusion has been accepted.
- Infrastructure repair may unblock execution, but it is not completion of the
  approved analytical work.

## Status and acceptance

Report `runtime_status`, `persistence_status`, `analysis_status`, and each
deliverable status independently. Use truthful states such as `NOT_STARTED`,
`RUNNING`, `PARTIAL`, `PERSISTED`, `PENDING_REVIEW`, `ACCEPTED`,
`BLOCKED_INPUT`, `BLOCKED_EXTERNAL`, and `FAILED` when applicable.

Analytical acceptance binds to the specific reviewed `AnalysisState` revision,
material finding/recommendation fingerprint, and review identity. A changed
finding, recommendation, or material scope invalidates prior acceptance and
requires review and acceptance again.

Replacing a requested artifact with an outline is not silent completion. It is
either an approved revised deliverable or a produced outline with the original
deliverable reported as `NOT_STARTED`, `PARTIAL`, or `BLOCKED_*`.

## Completion check

Before reporting approved execution as successful, confirm that every executed
stage either has recoverable provisional canonical results with verified
provenance and receipt integrity or has an explicit incomplete, blocked, or
failed status. Confirm requested deliverables have corresponding durable
evidence or artifacts. Never infer analytical completion from model outputs,
`settled=true`, process exit, or an output count alone.

Cross-process pause and cancel remain deferred; do not imply that this
procedure provides them.
