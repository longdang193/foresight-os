# Extending ForesightOS

## Preserve canonical owners

Keep decision truth in `WorkBrief`, complete execution truth in
`ExecutionRecipe`, human authorization in `ApprovalRecord`, and analytical
truth in `AnalysisState`. `ApprovalPackage` is a derived review projection;
do not add a second approval store or copy the recipe into the brief. Public
execution must use the shared execution gate, while low-level workflow calls
remain explicit test/probe primitives.

Extensions should add one bounded owner to the existing system. Preserve the
single analysis state, skill registry, capability resolver, and evidence
receipt boundaries instead of introducing parallel stores or registries.

## Add a host-facing strategic procedure

Use `.agents/skills/<procedure-id>/SKILL.md` for repository-local host routing
and strategic intake procedures. Keep the packaged runtime skill boundary under
`src/foresight_os/skills/`; do not add a host procedure to
`src/foresight_os/skills/manifest.json` unless it is also a runtime analytical
skill with a validated output contract.

Wayfinding procedures may capture decision questions, provisional scope,
research needs, and caller-supplied method provenance. They must not promote
unresolved recommendations into required execution topology or capability
constraints, read or hash their own `.agents/` source, create a second brief
store, or make a generic `map.md` canonical. The controller resolves execution
from the validated WorkBrief, and `AnalysisStore` remains the sole brief store.

Add approved execution behavior to `.agents/skills/foresight-execution/`, not
to the packaged participant registry. The procedure must use the shared
execution gate, require a recipe-bound structured result contract and canonical
result persistence before provider work, keep persisted results provisional
until review and human acceptance, and report runtime, persistence, analysis,
and deliverable statuses separately. Infrastructure repair may unblock work but
must not be reported as completion of the approved analysis.

Add presentation delivery behavior to `.agents/skills/foresight-delivery/`, not
to the packaged participant registry. Delivery must validate accepted state,
current presentation-spec provenance, one requested destination, and a durable
receipt persisted through `AnalysisStore`; an unavailable adapter or local
persistence failure must remain blocked or failed.

## Add a skill

1. Create `src/foresight_os/skills/<skill-id>/SKILL.md` with a focused method,
   output contract, limitations, and provenance-safe instructions.
2. Add one entry to `src/foresight_os/skills/manifest.json` with the stable ID,
   semantic version, content path, SHA-256 hash, required capability IDs,
   output contract, and provenance.
3. Keep capability requirements in the manifest; do not call providers directly
   from the skill text.
4. Add or update routing and evaluation coverage in `evaluation/skills/` when
   the skill changes the evaluated contract.
5. Add focused tests for loading, hash mismatch failure, capability
   resolution, and any output contract that can be checked structurally.

The registry in `src/foresight_os/controller/skills.py` is the only packaged
skill registry. Individual `SKILL.md` files remain the procedure owners.

## Add an evaluation case

Create a new directory under `evaluation/cases/` containing the decision
context, workbook or other approved fixture, and reference findings with
reproducible source locators. Update the evaluation contract tests when the
case pack or rubric contract changes. Keep participant inputs separate from
validator or reference material and report missing packs as `BLOCKED_INPUT`.

Use `evaluation/run.py` and the existing probe scripts as entry points. Do not
embed customer data, credentials, or provider payloads in a fixture.

## Add a capability

1. Add a `CapabilityDefinition` to `DEFAULT_CAPABILITIES` in
   `src/foresight_os/runtime/capabilities.py` with access, scope, approval,
   execution mode, and parallelism values.
2. Implement the smallest native binding or boundary adapter needed by the
   resolver.
3. Keep run-owned resources in `CapabilityScope` and close owned resources at
   scope end.
4. Define unavailable, deferred, missing-credential, and failure behavior
   explicitly; do not silently fall back to an unrelated provider.
5. Add focused tests in `tests/test_capabilities.py` and an integration probe
   only when a real boundary is material.

## Add a provider adapter

Provider adapters belong under `src/foresight_os/runtime/` or
`src/foresight_os/clients/`. Read endpoint and credential names from the
environment, validate the boundary response, and sanitize results before they
enter durable evidence. Use an explicit allowlist for read operations where
the provider supports multiple tools.

Provider access is optional. Missing credentials or unavailable external state
must remain `BLOCKED_EXTERNAL` or an explicit capability-unavailable decision.
Never write secrets, authorization headers, prompts, or raw payloads to
`AnalysisState` or receipts. Add tests for missing configuration, malformed
responses, provider errors, and successful sanitization.

## Add an artifact destination

Local artifacts are represented by `Artifact` records linked to source findings
through `Relationship` records. Add a destination adapter at the artifact
boundary and preserve the source revision, spec hash, and durable receipt.

For presentation output, validate the revision-bound `PresentationSpec` before
delivery. External mutation requires the existing human-approval boundary and
must not become a default capability. A failed or unavailable destination must
not change the analytical state to look delivered.

## Verification checklist

- The new owner has a focused module, test, and documentation link.
- Existing stores, manifests, and receipt schemas remain the canonical owners.
- Local deterministic tests cover the important success and failure paths.
- External or provider proof is labeled separately from local verification.
- `python -m pytest -q` and the relevant evaluation probe pass without adding
  undocumented flags or a second source of truth.
