# Evidence and Evaluation

ForesightOS separates analytical evidence, runtime receipts, and evaluation
judgments. A green structural check proves that a contract or boundary behaved
as implemented; it does not prove that a model produced good reasoning.

## Evidence model

An `Evidence` record carries a stable ID, source locator, source version and
date, excerpt, limitations, and an optional measurement key. Claims,
implications, and recommendations refer to evidence IDs and retain their basis
(`OBSERVED`, `DERIVED`, or `ASSUMED`), assessment, assumptions, uncertainty,
and disconfirmation conditions.

Calculations record their formula, input IDs, output, units, and source
locators. Relationships connect evidence to analytical records and artifacts.
This makes a report traceable without storing raw provider payloads or secrets.

## Status vocabulary

Use the following statuses consistently in probes, receipts, and reports:

| Status | Meaning |
|---|---|
| `VERIFIED` | The required deterministic checks completed and their acceptance conditions passed. |
| `FAILED` | The operation ran, but a required check, contract, provider operation, or acceptance condition failed. |
| `BLOCKED_INPUT` | Approved inputs or fixtures are absent, incomplete, or outside the allowed scope, so the operation cannot be judged. |
| `BLOCKED_EXTERNAL` | An external provider, credential, network boundary, or protected integration is unavailable or intentionally not exercised. |
| `NOT_VERIFIED` | Deterministic checks may have passed, but required review coverage, decision challenge, or human acceptance is incomplete. |
| `not_measured` | A metric requires human judgment or a measurement that was not collected; it is not a passing value. |

`BLOCKED_EXTERNAL` is a truthful boundary result, not a substitute for
provider success. In the same way, `BLOCKED_INPUT` must not be turned into a
zero score or a successful empty run.

## Independent validation and acceptance

The independent-validation workflow separates five facts that must not be
collapsed into one green flag:

- **Source fidelity** records workbook SHA-256, sheets, selected ranges,
  periods, units, and channel boundaries.
- **Scope reconciliation** checks that the declared category, period, unit,
  denominator, and source ranges are aligned before cross-channel comparison.
- **Calculation reconciliation** derives expected growth, shares, survival
  ratios, and planning thresholds from raw cells before comparing the persisted
  analyst result. A planning threshold such as 8% is planning math, not
  observed performance.
- **Decision challenge** is a separate human or authorized-reviewer check. A
  deterministic probe reports `NOT_RUN` when it is not authorized to perform
  that challenge.
- **Human acceptance** is an explicit decision over the reviewed analytical
  package. It never follows automatically from a passing probe; missing
  required coverage, stale inputs, conflicts, or unresolved blocking
  objections keep the package pending or rejected.

For the provider-free fixture, run:

```text
python evaluation/probes/run_ncc_independent_validation.py --workbook tests/fixtures/ncc-independent-validation.xlsx --analysis-dir <persisted-analysis-directory> --review-spec tests/fixtures/ncc-independent-validation-review-spec.json --output-root work/ncc-independent-validation-20261015/final
```

For the external NCC workbook, run the maintained case specification with a
matching persisted analysis directory:

```text
python evaluation/probes/run_ncc_independent_validation.py --workbook "data/exercise1-nielsenIQ/NCC 2022 - Semi Final Case - Data set.xlsx" --analysis-dir <persisted-ncc-analysis-directory> --review-spec evaluation/cases/ncc-2022-cosluxe-vietnam/review-spec.json --output-root work/ncc-independent-validation-20261015/real
```

The maintained NCC review specification targets the external 2022 workbook's
`Macro & FMCG`, `Personal Care`, `Modern Trade`, and `Ecommerce` ranges. The
probe derives selected growth and ratio expectations directly from raw cell
coordinates and compares them with the persisted calculations. The real NCC
workbook remains an external local fixture. Receipts may record its hash and
sanitized source metadata, but workbook bytes and raw provider payloads must
not enter Git or durable analytical state.

## Evaluation levels

The evaluation contract compares progressively richer conditions:

- **A — ordinary prompt:** a capable single agent receives the workbook and
  decision question.
- **B — semantic:** the same inputs are paired with the semantic evidence and
  output contract.
- **C — coordination:** level B inputs plus one tested coordination pattern.

The frozen rubric measures supported-claim precision, finding coverage,
contradiction precision and recall, traceability, cost per accepted finding,
verification effort, recovery success, and maintainability cost. Acceptance
requires the thresholds in `evaluation/rubric.md`, including complete
traceability for accepted material statements and successful recovery without
duplicate or stale current artifacts.

## Receipts and durable records

Durable receipts should contain status, timestamps, typed metadata, metrics,
input or source identity, and cleanup state. They must not contain prompts,
tokens, authorization headers, or raw external payloads. The evidence workflow
and scheduled workflow keep deterministic local checks separate from optional
provider-backed checks.

The durable records under `docs/superpowers/evidence/` are historical evidence
owners. They may be linked from current documentation, but their claims should
not be copied into a new page without checking the receipt and its scope.

## Performance evidence

The optimization probe is the release-level measurement entry point. It records
baseline/release receipts, stage and resource metrics, tool-call economics,
accepted-finding-normalized values, and a no-growth soak. Comparisons fail
closed on missing evidence, schema or workload mismatch, zero denominators,
resource growth, or threshold regressions.

Run structural evaluation and release measurement through the scripts documented
in `evaluation/README.md` and `.github/workflows/evidence.yml`. Keep provider
evidence in its protected, separately invoked boundary.

## What verification does not prove

Structural verification can prove file shape, hashes, schemas, deterministic
fixtures, persistence, invalidation, or boundary handling. It cannot by itself
prove model reasoning quality, strategic usefulness, factual completeness, or
human acceptance. Those claims require the reference rubric, source-grounded
adjudication, and—when applicable—human review.
