# ForesightOS

ForesightOS is an evidence-aware strategic reasoning prototype. It turns a
decision question and structured source material into traceable claims,
implications, recommendations, and local artifacts while preserving review,
revision, and invalidation state.

## What it does

- Reads bounded local workbook or CSV inputs and records source locators.
- Selects a bounded execution recipe for direct, sequential, concurrent,
  handoff, or group-chat work.
- Resolves reusable skills and runtime capabilities without merging their
  responsibilities.
- Persists analytical state, revisions, calculations, relationships, review
  records, and invalidation metadata.
- Generates an evidence-linked executive report from committed state.
- Keeps optional web, MCP, Power BI, and presentation boundaries separate from
  the provider-free local analysis path.

ForesightOS does not treat a model response or an external provider result as
accepted evidence automatically. Missing inputs, unavailable providers, failed
checks, and unresolved review issues remain explicit.

## Five-minute local quickstart

Requirements: Python 3.11 or newer and the project dependencies.

```text
python -m pip install -e .
python -m foresight_os.cli --help
python -m foresight_os.cli analyze --workbook evaluation/cases/case-001/workbook.csv --work-dir work/docs-quickstart --accept
python -m foresight_os.cli report --work-dir work/docs-quickstart
```

The local fixture path requires no provider authentication. The analysis command
returns an accepted status and writes state under `work/docs-quickstart/`.
The report command writes:

```text
work/docs-quickstart/artifacts/executive-report.md
```

To continue after changed evidence:

```text
python -m foresight_os.cli continue --work-dir work/docs-quickstart --changed-id claim-northern-demand-growth --reason "Updated source evidence"
```

See [Getting Started](docs/getting-started.md) for expected outputs, state
inspection, troubleshooting, and the difference between the local CSV path and
optional XLSX, Power BI, or provider boundaries.

## Architecture at a glance

```text
WorkBrief
  -> controller policy and ExecutionRecipe
  -> RecipeStage
  -> participants + skills + capabilities
  -> bounded workflow and stage receipts
  -> AnalysisState
  -> review and finding views
  -> report or optional presentation boundary
```

The `WorkBrief` captures the decision question, objective, horizon, constraints,
stages, participants, and research needs. The controller turns it into a
recipe. Each stage carries its pattern, participants, skill IDs, dependencies,
limits, and expected result. The runtime resolves capabilities and records
fingerprints before executing.

`AnalysisState` is the durable analytical owner. It contains evidence, claims,
implications, recommendations, calculations, relationships, artifacts,
revisions, review records, and invalidation information. `AnalysisStore` writes
validated state atomically and keeps pending mutations separate from accepted
revisions.

Reports are derived from committed state. Optional presentations are revision-
bound and cannot be sent to an external destination without the existing human
approval and durable receipt boundary.

See [Architecture](docs/architecture.md) for the runtime flow and state model.

## Evidence and verification boundary

The repository distinguishes local structural proof from model or provider
quality. Common statuses are:

- `VERIFIED`: required deterministic checks passed;
- `FAILED`: an attempted operation or acceptance check failed;
- `BLOCKED_INPUT`: approved inputs are absent or incomplete;
- `BLOCKED_EXTERNAL`: a provider or protected external boundary is unavailable;
- `not_measured`: a required human or performance measurement was not collected.

Structural checks can prove schemas, hashes, persistence, invalidation, fixture
determinism, and boundary handling. They do not prove strategic usefulness or
model reasoning quality. Evaluation thresholds and durable receipts live with
the evaluation sources, not in this README.

## Documentation

Use [the documentation index](docs/README.md) for the maintained user-facing
guides:

- [Getting Started](docs/getting-started.md)
- [Architecture](docs/architecture.md)
- [Skills and Capabilities](docs/skills.md)
- [Evidence and Evaluation](docs/evidence-and-evaluation.md)
- [Configuration](docs/configuration.md)
- [Extending ForesightOS](docs/extending.md)

The repository also retains historical plans and durable evidence under
`docs/intent/` and `docs/superpowers/`. Those records remain source-specific and
are not duplicated into onboarding pages.

## Repository map

```text
src/foresight_os/       runtime, domain, controller, persistence, artifacts
evaluation/              frozen cases, rubrics, probes, and reports
tests/                   unit and contract tests
docs/                    maintained user guides and durable project records
schemas/                 checked-in schema inputs
scripts/                 repository maintenance helpers
```

The implementation and tests are authoritative when this overview and source
behavior differ.

## Development checks

Run the full test suite from the repository root:

```text
python -m pytest -q
python -m compileall -q src tests evaluation
```

For configuration, use `.env.example` as the variable inventory. The runtime
reads inherited environment variables; it does not automatically load `.env`.
Keep credentials out of source, state, receipts, and public documentation.

For contribution workflows, start with [Extending ForesightOS](docs/extending.md)
and keep new behavior inside its existing owner rather than adding a parallel
registry, store, or evidence format.
