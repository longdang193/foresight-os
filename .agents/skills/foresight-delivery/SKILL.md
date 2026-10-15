---
name: foresight-delivery
description: Deliver an accepted, current PresentationSpec through one explicitly requested local or external adapter with a matching durable receipt.
---

# ForesightOS Delivery

Use this host procedure only after analytical review and human acceptance of the
specific `AnalysisState` revision and its current `PresentationSpec`.

## Boundary

```text
accepted AnalysisState + current PresentationSpec
  -> validate revision, spec hash, destination, and adapter availability
  -> invoke exactly one requested adapter
  -> validate the provider or local success receipt
  -> persist the receipt through AnalysisStore on the presentation Artifact
  -> reload and verify the persisted receipt
```

This is a host procedure, not a participant skill and not a second analytical
store. It must not create findings, recommendations, calculations, or claims.

## Admission and status

- Require `RevisionStatus.ACCEPTED`, a current presentation specification, and
  a matching revision-bound specification hash.
- Require exactly one requested destination such as `pptx` or `canva`.
- Require explicit human approval before external mutation.
- If the adapter is unavailable, report `BLOCKED_EXTERNAL`; do not claim
  delivery and do not manufacture a receipt.
- A provider success without local receipt persistence is `FAILED`, not complete.
- Reload the state and reject missing, stale, mismatched, or unsuccessful proof.

## Receipt and safety rules

Receipts must identify the destination, provider, source revision,
presentation-spec hash, successful state, and timezone-aware verification time.
Never persist credentials, authorization headers, prompts, or raw provider
payloads. Canva and PPTX are separate adapters; invoke at most one per request.

Cross-process pause and cancel remain deferred.
