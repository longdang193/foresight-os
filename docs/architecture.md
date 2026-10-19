# Architecture

ForesightOS is an evidence-aware analysis pipeline. It separates the decision
brief, execution policy, analytical state, and optional presentation outputs so
that a report can be traced back to the evidence and revision that produced it.

## End-to-end flow

```text
WorkBrief
  -> typed human intent and research needs
  -> NormalizedIntent and domain AnalysisInputContract declarations
  -> verified XLSX tables and source-row provenance
  -> domain analysis and independent validation
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

`WorkBrief.analysis_inputs` is the single persisted declaration of domain input
scope. `normalize_work_brief()` derives one ephemeral `NormalizedIntent` per
execution, including deterministic contract fingerprints; it is not a second
registry or analytical state store. The five production XLSX analyzers consume
their selected periods, entities, scenarios, units, mappings, and conversions
from these contracts while retaining domain-specific calculations and review
state. `AnalysisStore` remains the owner of accepted evidence, calculations,
findings, invalidation, and provenance.

Strategic Wayfinding is a host-facing procedure under
`.agents/skills/foresight-wayfinding/`. Packaged runtime analytical skills stay
under `src/foresight_os/skills/` and are selected by the controller; the host
procedure is not a second packaged skill or manifest entry.

Approved investigation execution is a separate host-facing procedure under
`.agents/skills/foresight-execution/`. Wayfinding stops at human execution
approval. Execution performs preflight, dispatches the approved recipe through
the shared gate, persists provisional analytical results, verifies recovery, and
stops again for analytical review and human acceptance. Runtime settlement is
not analytical completion.

Accepted presentation delivery is a separate host-facing procedure under
`.agents/skills/foresight-delivery/`. It validates the accepted revision and
current presentation-spec hash, invokes one requested adapter, and persists a
matching receipt through `AnalysisStore`. Provider success without local proof
remains failed or blocked.

Source-grounded validation is a separate host-facing procedure under
`.agents/skills/foresight-validation/`. It reuses the selected deterministic
checks, review records, dependency invalidation, and human acceptance owners;
it does not add a second validator or durable status hierarchy.

### Workbook input path

The local XLSX path has one ephemeral input composition boundary:
`WorkbookContext` captures or reuses bounded source snapshots, resolves a
`ResolvedWorkbookLayout` from a domain-owned `WorkbookLayoutSpec`, and builds a
provenance-preserving `MaterialView` for the selected contract scope.
`WorkbookAnalysisEngine` invokes the domain analyzer without persistence or
acceptance side effects. `WorkbookWorkflowRunner` then delegates pending-state
writes, review, acceptance, invalidation metadata, report gating, and lifecycle
status conversion to the existing owners. Recipe execution uses the engine
directly so stage receipts and analytical acceptance are not nested or
duplicated.

The public `analyze` command dispatches CSV to the existing vertical slice and
dispatches XLSX only through an explicit domain or one unambiguous domain in
`brief.md`. Missing or ambiguous XLSX domain selection is `BLOCKED_INPUT`.

Workbook defaults, lazy analyzer dispatch, and explicit analyzer versions are
owned by `workbook_registry.py`; compatibility helpers delegate to that
registry rather than maintaining a second map. A behavior-changing analyzer
edit requires an explicit registry version bump so stage receipt fingerprints
remain deterministic.

Each workbook execution captures one bounded source snapshot before layout and
materialization. That snapshot supplies reads, provenance, hashes, and receipt
identity for the run; changing the source path after capture affects only a
later execution. Artifact rendering is independent of accepted analytical
state, and an accepted revision can be rendered again without rerunning
analysis or review.

The deterministic review core is importable without initializing
`agent_framework`. Agent-assisted review remains behind the compatibility
facade in `reviewer.py`, so provider-bound execution is not required for local
workbook analysis or deterministic review checks.

Reader and persistence counters are exposed only as measurement facts. The
optimization probe records archive scans, selected material, formula counts,
openpyxl loads, source capture/hash counts, materialization time, persistence
bytes/time, and repeated process-cold samples. Candidate XLSX optimizations
must pass correctness/resource, warm/reuse, and cold-noise-floor gates before
they are retained; the current baseline retains no unproven reader change.

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
end; borrowed resources are not closed by ForesightOS. Local workbook reads use
one run-owned `WorkbookContext` under the capability scope. It retains bounded
immutable source snapshots, selection-aware derived results, authority records,
and reuse statistics, then clears them with the scope. This keeps external
clients and workbook state from leaking across investigations.

Low-level `spreadsheet_read` and `calculation` calls that omit a
`WorkbookContext` retain a bounded process-local compatibility authority for
legacy callers. Orchestrated capability execution does not use that fallback:
the middleware always supplies the run-owned context and authority index.

### 4. Execution admission, execution, and receipts

User-facing execution paths reload the brief, exact recipe, and approval under
the `AnalysisStore` investigation lock. The shared execution gate rejects
missing, stale, rejected, superseded, or out-of-envelope approvals before MAF
dispatch. Direct `run_recipe_async` calls remain a low-level primitive for
tests and evaluation probes, not a public approval path.

The workflow runtime executes each stage using the selected pattern and
enforces the recipe limits. Structured stage results are normalized through the
approved output contract before they enter analytical state. The committer
persists provisional state and returns a verified canonical result; the
workflow is the sole writer of `StageReceipt`. Stage receipts record input and policy fingerprints,
skill hashes, capability fingerprints, analyzer identities for deterministic
workbook stages, result references and hashes, commit status, and provenance
completeness. A receipt is reusable only when its fingerprints and committed
result evidence still match the current stage.
When a provider returns completed local tool results without a final message,
the runtime performs one bounded no-tool structured retry using those transient
results; malformed or empty output remains subject to canonical validation.
Canonical validation may consume the recipe's bounded correction round, but it
never invents references or upgrades rejected output.

Approved execution reports four independent outcome dimensions: runtime
settlement, persistence, analytical review/acceptance, and each requested
deliverable. A settled runtime may therefore report `PERSISTED` with
`PENDING_REVIEW`, or a mixture of persisted and not-started deliverables; it
must not infer completion from `settled=true`, process exit, or output count.
Canonical typed persistence currently rejects concurrent stages during
preflight because branch aggregation has no declared deterministic result
contract. Low-level orchestration still supports concurrent probes without the
approved committer.

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
valid and no unresolved objection or missing input remains. They also provide a
compact derived summary (`supported`, `uncertain`, `correction-needed`, or
`human-review-pending`) while retaining source, validation, and execution detail
for progressive disclosure.

## Artifact flow

The local executive report is written to `artifacts/executive-report.md` from
the committed analysis state. Presentation specifications are revision-bound,
hash-checked, and either `CURRENT` or `DRAFT / UNVALIDATED`.

Canva and PPTX are optional rendering boundaries, not part of the analytical
core. A presentation can be delivered only when it is current, human-approved,
backed by exactly one requested adapter, and accompanied by a matching durable
delivery receipt. Local analysis and report generation do not require provider
authentication.

## Boundaries and failure behavior

External providers are optional capabilities. Missing credentials, unavailable
providers, missing approved inputs, and failed operations remain explicit in
their receipts; they are not silently converted into successful evidence.
The local CSV/XLSX analysis path can therefore be verified without provider
access, while provider-backed checks remain separate boundary evidence.

The source of truth for behavior is the implementation and tests under
`src/foresight_os/` and `tests/`. This page is an orientation map, not a second
runtime specification.
