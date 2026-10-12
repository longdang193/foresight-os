# Evaluation Report: case-001

## Thresholds
{"contradiction_precision": 0.8, "contradiction_recall": 0.8, "finding_coverage": 0.8, "supported_claim_precision": 0.9, "traceability": 1.0}

## Comparison
- `ordinary`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "direct", "provider_failures": 0, "recipe": "DIRECT", "retries": 0, "run_id": "run-3658da1360474486bab7b86ceb2b6dc5", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `semantic`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "sequential", "provider_failures": 0, "recipe": "ANALYZE", "retries": 0, "run_id": "run-33255b91bb7b4c269e64485374e4be00", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `sequential`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "sequential", "provider_failures": 0, "recipe": "ANALYZE_REVIEW", "retries": 0, "run_id": "run-5a81ceedc0d14d648ad6a4538b47c9df", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `controller`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "sequential", "provider_failures": 0, "recipe": "ANALYZE_REVIEW", "retries": 0, "run_id": "run-3891aef7a4a543c8b62a7c72e57565d4", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `concurrent`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "concurrent", "provider_failures": 0, "recipe": "CONCURRENT", "retries": 0, "run_id": "run-bc738bdb7c7e476fb240280b5cdb8a26", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `handoff`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "handoff", "provider_failures": 0, "recipe": "HANDOFF", "retries": 0, "run_id": "run-b532ee2c1d074806b908ec61adf3a7d0", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}

- Controller recipe: `ANALYZE_REVIEW`
- Admitted pattern: `ordinary`

## Limitations
- Provider-backed calls are environment-gated; deterministic domain execution remains the local comparison baseline.
