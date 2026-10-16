# Runtime Consolidation Baseline

- Date: 2026-10-16
- Worktree: `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\foresight-os-runtime-consolidation\foresight-OS`
- Branch: `codex/foresight-os-runtime-consolidation`
- Base: `c8c17db0663fbbcab696215308aa5b7f386bb2b4`
- Environment: Python 3.11+; repository dependencies available; provider-free local path.

| Gate | Result | Evidence / limitation |
| --- | --- | --- |
| Caller-supplied table fingerprint cannot poison identity | FAILED | Four tables with the same caller fingerprint but different rows, `dataclasses.replace()`, and coerced serialized input all retained one fingerprint. |
| Cancellation remains caller-visible | PASS | `python -m pytest -q tests/test_runtime_boundaries.py -k cancellation` passed 2 tests; existing cancellation behavior is preserved at baseline. |
| Explicit missing mapping fails | FAILED | `apply_column_mappings([{'Actual': 1}], {'Canonical': 'Missing'})` returned the row unchanged. |
| Reversed/cross-year period semantics are rejected | FAILED | `AnalysisInputContract` accepted `2026-09:2026-03` and `2026-03:2025-09`. |
| Focused baseline suite | PASS | `python -m pytest -q tests/test_optimization_measurement.py tests/test_controller_selection.py tests/test_execution_gate.py tests/test_local_toolbelt.py tests/test_runtime_boundaries.py` passed. |

Task 1 conclusion: baseline is trustworthy; the identity, mapping, and period defects are reproduced and cancellation is a preserved green behavior. No primary-checkout files were modified.
