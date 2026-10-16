# Runtime Consolidation Release 1

- Date: 2026-10-16
- Worktree: `C:\Users\HOANG PHI LONG DANG\.codex\worktrees\foresight-os-runtime-consolidation\foresight-OS`
- Branch: `codex/foresight-os-runtime-consolidation`
- Base: `c8c17db0663fbbcab696215308aa5b7f386bb2b4`
- Scope: Task 2 identity and lifecycle trust boundaries

| Gate | Result | Evidence / limitation |
| --- | --- | --- |
| Caller-supplied or serialized table fingerprints cannot authorize identity | PASS | `TypedTable.material_fingerprint` is derived with `init=False`; serialized fingerprints are ignored; changed rows, range, hidden state, and coerced material receive distinct identities. |
| Join-table material changes analysis identity | PASS | `tests/test_local_toolbelt.py::test_join_table_material_identity_changes_analysis_cache_key` passed. |
| Capability admission is metadata-only | PASS | Counting factory test confirms admission invokes zero factories and registers zero resources. |
| Activation registers owned resources and scope cleanup closes them | PASS | Existing lazy/reuse and async resource-factory tests pass; setup-failure regression confirms a resource created before a later activation error closes exactly once. |
| Setup failure preserves primary error and settles metrics | PASS | `tests/test_runtime_boundaries.py::test_capability_setup_failure_closes_resources_created_before_primary_error` passed. |
| Cancellation remains primary and non-retryable | PASS | Existing cancellation subset and full focused lifecycle suite pass unchanged. |
| Cleanup failure remains secondary to primary failure | PASS | `tests/test_runtime_boundaries.py::test_cleanup_failure_remains_secondary_to_primary_run_failure` passed; cleanup is recorded without replacing cancellation. |
| Focused Release 1 suite | PASS | `python -m pytest -q tests/test_local_toolbelt.py tests/test_capabilities.py tests/test_runtime_boundaries.py tests/test_orchestration_patterns.py` passed. |

Implementation notes:

- Added a fixed typed-table identity version and recomputed material identity on every construction.
- Added resolver admission that validates definitions, policy, authorization, bindings, and factory shape without activation.
- Added setup-failure cleanup around capability activation before the main run `try/finally`; secondary cleanup errors remain diagnostics.
- No persistence schema, provider dependency, or world-copy rollback redesign was introduced; those remain scoped to later tasks.

Task 2 conclusion: Release 1 identity and lifecycle gates are PASS. Existing cancellation and cleanup semantics remain preserved, and no caller-controlled table identity can produce a trusted cache hit.

## Task 3 semantic portability gate

| Gate | Result | Evidence / limitation |
| --- | --- | --- |
| Typed period meaning preserves valid same-year and cross-year ranges | PASS | Private immutable `_PeriodSpec` parsing preserves year/month/granularity/start/end and accepts valid cross-year ranges such as `2025-10:2026-03`. |
| Reversed ranges fail before workbook capture | PASS | Reversed same-year and cross-year ranges fail with the focused portability suite. |
| Explicit mappings fail exact-or-fail | PASS | Missing mapped columns produce stable `MISSING_MAPPED_COLUMN` failures before compatibility/default mapping. |
| Brief-local validation precedes source I/O | PASS | Focused contract and portability tests cover invalid syntax/order, explicit scope, mapping shape, and policy completeness before workbook capture. |
| Analyzer and validator portability regressions | PASS | `python -m pytest -q tests/test_analysis_input_contract.py tests/test_brief_portability.py tests/test_case_portability.py tests/test_technology_powerbi_validator.py tests/test_supplier_and_ev_resilience.py` passed. |

Task 3 conclusion: explicit period and mapping semantics are now exact-or-fail while serialized brief compatibility remains intact. Source-dependent checks remain downstream of schema discovery and before analytical transformation.
