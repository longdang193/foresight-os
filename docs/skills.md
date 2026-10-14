# Skills and Capabilities

ForesightOS uses several related concepts. Keeping them separate prevents a
procedure, a tool, a participant, and a workflow pattern from becoming one
unreviewable registry.

## Core concepts

| Concept | Meaning | Owner |
|---|---|---|
| Skill | Reusable analytical instructions with an output contract and provenance | `src/foresight_os/skills/` plus `manifest.json` |
| Capability | A runtime ability such as calculation, data analysis, web search, or an external signal | `src/foresight_os/runtime/capabilities.py` and its adapters |
| Participant | A role that executes a stage, such as analyst, reviewer, or skeptic | `src/foresight_os/runtime/participants.py` |
| Pattern | The execution shape: direct, sequential, concurrent, handoff, or group chat | `src/foresight_os/controller/recipes.py` |
| Controller | Policy that selects a recipe and coordinates stages, limits, and escalation | `src/foresight_os/controller/` |

A skill may require capabilities, but a capability is not a skill. A pattern
describes coordination, but it does not describe the analytical method used by
the participants.

## Skill registry

The packaged registry is `src/foresight_os/skills/manifest.json`. Each entry
contains:

- a stable skill ID and version;
- the packaged `SKILL.md` path;
- a SHA-256 content hash;
- required capability IDs;
- an output contract; and
- provenance such as `bundled-local`.

When a skill is resolved, the registry reads the package resource and verifies
the content hash. A mismatch fails closed instead of silently executing changed
instructions. Selected skill IDs, versions, and hashes are included in stage
identity and review fingerprints, so a prior result is not reused as if the
method had stayed the same.

The individual skill files are the procedure owners. This page intentionally
does not copy their full instructions or create a second catalog. Examples
include [source appraisal](../src/foresight_os/skills/source-appraisal/SKILL.md),
[quantitative sanity checking](../src/foresight_os/skills/quantitative-sanity-check/SKILL.md),
[red-team review](../src/foresight_os/skills/red-team-claim/SKILL.md), and
[scenario planning](../src/foresight_os/skills/scenario-planning/SKILL.md).

## Capability resolution

The capability resolver returns one decision for each requested capability:

- `USE_NATIVE` when the configured native binding is available;
- `ADAPT_AT_BOUNDARY` when a safe adapter is required;
- `DEFER` when the capability is intentionally postponed; or
- `UNSUPPORTED` when the runtime cannot provide it.

Definitions also describe access, data scope, approval policy, execution mode,
sharing scope, and maximum parallelism. External signal providers are loaded
only when their capability is required and their credentials and allowlists are
present.

## Selection and reuse

Recipe stages carry skill IDs and participant configurations. The workflow
builds semantic and policy fingerprints from stage inputs, dependencies,
participants, selected skills, and limits. A committed stage receipt can be
reused only when those inputs, skill hashes, capability fingerprints, model
configuration, authorization scope, and result hashes still match.

This is reuse of a verified stage result, not permission to skip review. A
changed source, skill, policy, capability, or authorization scope must produce
a new identity or invalidate downstream state.

## Adding a skill

Use the bounded procedure in [Extending ForesightOS](extending.md). Add the
skill content under `src/foresight_os/skills/<skill-id>/SKILL.md`, calculate its
hash, add one manifest entry, and add focused tests for loading, hash
validation, capability requirements, and output contract. Do not add a second
registry or copy private Project OS instructions into a product skill.
