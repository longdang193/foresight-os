# Evaluation Report: case-005

## Thresholds
{"contradiction_precision": 0.8, "contradiction_recall": 0.8, "finding_coverage": 0.8, "supported_claim_precision": 0.9, "traceability": 1.0}

## Comparison
- `ordinary`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "direct", "provider_failures": 0, "recipe": "DIRECT", "retries": 0, "run_id": "run-53f69db62afe4d36b8646e521cc7a965", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `semantic`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "sequential", "provider_failures": 0, "recipe": "ANALYZE", "retries": 0, "run_id": "run-3e37318e3e85499580d599a8d13b478d", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `sequential`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "sequential", "provider_failures": 0, "recipe": "ANALYZE_REVIEW", "retries": 0, "run_id": "run-9008cdd810af49f7876956e85a5f4e7e", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `controller`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "sequential", "provider_failures": 0, "recipe": "ANALYZE_REVIEW", "retries": 0, "run_id": "run-15f6b358656146998b656fbcadcce2a2", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `concurrent`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "concurrent", "provider_failures": 0, "recipe": "CONCURRENT", "retries": 0, "run_id": "run-0910e2cb85e14c6882923f2e95d58edb", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `handoff`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "handoff", "provider_failures": 0, "recipe": "HANDOFF", "retries": 0, "run_id": "run-f639f960829f41fcaa00d00ad395fb33", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}

- Controller recipe: `ANALYZE_REVIEW`
- Admitted pattern: `ordinary`

## Limitations
- Provider-backed calls are environment-gated; deterministic domain execution remains the local comparison baseline.
