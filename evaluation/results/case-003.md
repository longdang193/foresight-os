# Evaluation Report: case-003

## Thresholds
{"contradiction_precision": 0.8, "contradiction_recall": 0.8, "finding_coverage": 0.8, "supported_claim_precision": 0.9, "traceability": 1.0}

## Comparison
- `ordinary`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "direct", "provider_failures": 0, "recipe": "DIRECT", "retries": 0, "run_id": "run-2939aad046b2458e9c7d3a0ac4e5e779", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `semantic`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "sequential", "provider_failures": 0, "recipe": "ANALYZE", "retries": 0, "run_id": "run-9d2662ebc14548539fae689af51bbe38", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `sequential`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "sequential", "provider_failures": 0, "recipe": "ANALYZE_REVIEW", "retries": 0, "run_id": "run-fc5e4ad11dd04decac420549af56106c", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `controller`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "sequential", "provider_failures": 0, "recipe": "ANALYZE_REVIEW", "retries": 0, "run_id": "run-013bb7da504947fcae61f07392029825", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `concurrent`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "concurrent", "provider_failures": 0, "recipe": "CONCURRENT", "retries": 0, "run_id": "run-f34f868eb24d44b2861ba60c6566d36d", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `handoff`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "handoff", "provider_failures": 0, "recipe": "HANDOFF", "retries": 0, "run_id": "run-d1981df1cd40442f94c3b5dfbd160059", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}

- Controller recipe: `ANALYZE_REVIEW`
- Admitted pattern: `ordinary`

## Limitations
- Provider-backed calls are environment-gated; deterministic domain execution remains the local comparison baseline.
