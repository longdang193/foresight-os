# Architecture

ForesightOS is an evidence-aware analysis pipeline. It separates the decision
brief, execution policy, analytical state, and optional presentation outputs so
that a report can be traced back to the evidence and revision that produced it.

## End-to-end flow

```text
WorkBrief
  -> typed human intent and research needs
  -> controller policy and complete ExecutionRecipe
  -> derived ApprovalPackage and durable ApprovalRecord
  -> shared execution gate
  -> RecipeStage
  -> participants + skills + capabilities
  -> execution pattern and stage receipts
  -> AnalysisState
  -> review and finding views
  -> local report or optional presentation boundary
```

### 1. Work brief

`WorkBrief` records the decision question, objective, horizon, constraints,
stages, participants, and research needs. Validation happens before the brief
is used by the controller. The persisted `brief.md` keeps YAML front matter as
the canonical structured contract and appends a generated Markdown review view;
the body is not an input source. The `brief` CLI command renders that view
without creating another state file.

New briefs may include caller-supplied method provenance and typed required or
preferred execution intent. Provenance is descriptive, not authorization, and
is excluded from approval material fingerprints. Required topology or
capability constraints are retained only when explicitly supplied; research
needs remain the preferred input for later controller capability resolution.
Legacy pattern overrides are translated at load time and are not re-emitted.

Strategic Wayfinding is a host-facing procedure under
`.agents/skills/foresight-wayfinding/`. Packaged runtime analytical skills stay
under `src/foresight_os/skills/` and are selected by the controller; the host
procedure is not a second packaged skill or manifest entry.

### 2. Controller and recipe

The controller resolves policy into an `ExecutionRecipe`. A recipe names the
execution pattern, roles, budgets, completion rule, escalation rule, partial
result behavior, and one or more `RecipeStage` values. The supported patterns
are direct, sequential, concurrent, handoff, and group chat.

Each stage has an input and output contract, participant set, skill IDs,
dependencies, research needs, limits, and expected result. Dependencies and
stage fingerprints make reuse explicit rather than implicit.

`execution-recipe.json` is the exact controller or human-edited recipe reviewed
by the human. `ApprovalPackage` is a derived Markdown/JSON view. Approval is
stored separately in `execution-approval.json`; it binds the displayed package
fingerprint and is recorded only through the explicit local CLI human boundary.

### 3. Participants, skills, and capabilities

Participants are runtime roles such as an analyst, reviewer, or skeptic. A
participant can request skills and capabilities, but it does not own the
registry or analytical state.

The skill registry resolves packaged instructions from `manifest.json`, checks
the content SHA-256 hash, and exposes the skill output contract and provenance.
The capability resolver then maps requested capability IDs to native tools,
boundary adapters, deferred capabilities, or explicit unsupported decisions.

Capability resources are scoped to a run. Owned resources are closed at scope
end; borrowed resources are not closed by ForesightOS. This keeps external
clients and local caches from leaking across investigations.

### 4. Execution admission, execution, and receipts

User-facing execution paths reload the brief, exact recipe, and approval under
the `AnalysisStore` investigation lock. The shared execution gate rejects
missing, stale, rejected, superseded, or out-of-envelope approvals before MAF
dispatch. Direct `run_recipe_async` calls remain a low-level primitive for
tests and evaluation probes, not a public approval path.

The workflow runtime executes each stage using the selected pattern and
enforces the recipe limits. Stage receipts record input and policy fingerprints,
skill hashes, capability fingerprints, result references and hashes, commit
status, and provenance completeness. A receipt is reusable only when its
fingerprints and committed result evidence still match the current stage.

## Analytical state

`AnalysisState` is the durable analytical source of truth. It contains:

- evidence and source locators;
- claims, implications, and recommendations;
- calculations, relationships, and artifacts;
- revision history and revision status;
- review records and invalidation information.

`AnalysisStore` writes `analysis.json` atomically and uses a file lock. Pending
mutations are kept separately until accepted. A continuation can invalidate
dependent findings, create a new revision, and preserve the reason for the
change. Finding views only mark a record accepted when its current review is
valid and no unresolved objection or missing input remains.

## Artifact flow

The local executive report is written to `artifacts/executive-report.md` from
the committed analysis state. Presentation specifications are revision-bound,
hash-checked, and either `CURRENT` or `DRAFT / UNVALIDATED`.

Canva is an optional rendering boundary, not part of the analytical core. A
presentation can be published only when it is current, human-approved, backed
by an adapter, and accompanied by a matching durable delivery receipt. Local
analysis and report generation do not require Canva authentication.

## Boundaries and failure behavior

External providers are optional capabilities. Missing credentials, unavailable
providers, missing approved inputs, and failed operations remain explicit in
their receipts; they are not silently converted into successful evidence.
The local CSV/XLSX analysis path can therefore be verified without provider
access, while provider-backed checks remain separate boundary evidence.

The source of truth for behavior is the implementation and tests under
`src/foresight_os/` and `tests/`. This page is an orientation map, not a second
runtime specification.
