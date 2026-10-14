# Getting Started

This guide runs the local, provider-free vertical slice. It uses the committed
CSV fixture so the first result is deterministic and does not require model
provider, web-search, MCP, or Canva authentication.

## Prerequisites

- Python 3.11 or newer.
- A checkout of ForesightOS.
- The project dependencies installed in the active environment.

Install the package in editable mode:

```text
python -m pip install -e .
```

The exact command surface is discoverable with:

```text
python -m foresight_os.cli --help
```

## Run the local analysis

Use the repository fixture and an ignored work directory:

```text
python -m foresight_os.cli analyze --workbook evaluation/cases/case-001/workbook.csv --work-dir work/docs-quickstart --accept
```

Expected result:

- exit code `0`;
- JSON output containing `"accepted": true` and `"status": "accepted"`;
- committed state under `work/docs-quickstart/`.

The vertical slice reads the workbook, performs the bounded analyst/reviewer
sequence, persists `analysis.json`, and writes the report artifact. The
`--accept` flag is the explicit human acceptance input for this fixture path.

## Inspect the state

Inspect the persisted JSON with any local JSON viewer, or use Python:

```text
python -c "import json; print(json.dumps(json.load(open('work/docs-quickstart/analysis.json')), indent=2))"
```

The state includes the investigation ID, revision, evidence, claims,
implications, recommendations, relationships, artifacts, and invalidation
metadata. It is the durable analytical state; the Markdown report is a derived
artifact.

## Generate the executive report

```text
python -m foresight_os.cli report --work-dir work/docs-quickstart
```

Expected result:

- exit code `0`;
- output path `work/docs-quickstart/artifacts/executive-report.md`.

The report is regenerated from the state loaded by `AnalysisStore`; it does not
become a second source of analytical truth.

## Continue after changed evidence

Invalidate a finding and create the next revision with:

```text
python -m foresight_os.cli continue --work-dir work/docs-quickstart --changed-id claim-northern-demand-growth --reason "Updated source evidence"
```

For the committed case, expected output includes:

- exit code `0`;
- investigation ID `case-001`;
- revision `2`;
- reassessment ID `claim-northern-demand-growth`.

The continuation path records the reason, invalidates dependent state, and
preserves the revision boundary. Re-run `report` after completing any new
analysis or accepted mutation.

## Other CLI paths

The CLI also exposes `inspect-powerbi`, `challenge`, and `scope-change`. Use
`--help` for their current flags; this guide intentionally does not duplicate an
exhaustive flag table. Power BI project inspection is metadata-only and is
separate from the CSV vertical slice.

## Troubleshooting

- **Workbook not found:** confirm the path is relative to the repository root
  and that `evaluation/cases/case-001/workbook.csv` exists.
- **Invalid work directory:** use a disposable directory under `work/`; the
  store creates its files and locks there.
- **Provider unavailable:** provider-backed capabilities are optional for this
  guide. Missing configuration is a boundary result, not a reason to add
  credentials to the local quickstart.
- **Continuation target unknown:** inspect `analysis.json` and use an existing
  record ID in `--changed-id`.

The local path is intentionally narrower than the full evaluation and external
provider workflows documented in [Evidence and Evaluation](evidence-and-evaluation.md).
