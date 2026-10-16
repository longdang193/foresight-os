# Optimization Baseline Receipt

- schema: optimization-baseline/v1
- recorded_at_utc: 2026-10-16
- workspace: C:/Users/HOANG PHI LONG DANG/.codex/worktrees/recommended-sequence-followup/foresight-OS
- branch: codex/recommended-sequence-followup
- base_commit: 1e76c2e4242b42f3bcbccd8a4b5551782f86a733
- origin_main_at_recording: 1e76c2e4242b42f3bcbccd8a4b5551782f86a733
- base_matches_origin_main: True
- python: Python 3.13.5
- pytest: 8.3.5
- openpyxl: 3.1.5
- fixture_identity: 	ests/test_local_toolbelt.py (pytest-generated analyst_multisheet.xlsx fixture)
- fixture_source_hash: c194801b2201c2dc12f20fae929eb628de4b3a8d8bb9f392cbda36409a0b5742 (fixture generator source; generated workbook is per-test temporary data)
- plan_hash_at_recording: 7c0a4aa22e9bb5c77c898afcd223af478b7c913d4a8161c8df29a040f778220

## Owner Drift Check

- SourceSnapshot, WorkbookReadCache, WorkbookContext, spreadsheet_read, and data_analysis remain in src/foresight_os/runtime/local_toolbelt.py.
- AnalysisInputContract, NormalizedIntent, and normalize_work_brief remain in src/foresight_os/domain/analysis_inputs.py.
- Focused regression locations remain in 	ests/test_optimization_measurement.py, 	ests/test_controller_selection.py, and 	ests/test_execution_gate.py.
- No repository-wide architecture re-investigation was performed.

## Focused Correctness Baseline

- Command: python -m pytest -q tests/test_optimization_measurement.py tests/test_controller_selection.py tests/test_execution_gate.py
- Result: PASSED (28 tests)
- Raw output: work/optimization-baseline/focused-tests.txt

## Known Release-A Gate

The existing analysis cache key is (analysis, table.id, operation, limits) and therefore does not encode the table material/view. A hidden-row or caller-supplied-ID collision remains an expected pre-change failure mode. Task 2 must add a regression proving distinct material views cannot alias and that a same-view repeat does hit the cache.

## Preserved Dirty Paths At Baseline


 M docs/superpowers/plans/2026-10-16-foresight-os-recommended-implementation-sequence-plan.md
?? work/optimization-baseline/focused-tests.txt


## Structural Measurement Status

- Cold/warm production-path comparison: not_measured at Task 1; the existing probe contract will be reused after source/context changes.
- Provider/model quality: not_applicable to this local baseline.
- Human acceptance: not_applicable to this local baseline.
