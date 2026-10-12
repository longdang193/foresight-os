# Evaluation Report: case-002

## Thresholds
{"contradiction_precision": 0.8, "contradiction_recall": 0.8, "finding_coverage": 0.8, "supported_claim_precision": 0.9, "traceability": 1.0}

## Comparison
- `ordinary`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "direct", "provider_failures": 0, "recipe": "DIRECT", "retries": 0, "run_id": "run-26c3d5fed372489ea14e4caef11eff8d", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `semantic`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "sequential", "provider_failures": 0, "recipe": "ANALYZE", "retries": 0, "run_id": "run-e94f592ffdf6418a99db339c5d0ff6b5", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `sequential`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "sequential", "provider_failures": 0, "recipe": "ANALYZE_REVIEW", "retries": 0, "run_id": "run-47f1531775c0409cb91a4f69b63d36c1", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `controller`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "sequential", "provider_failures": 0, "recipe": "ANALYZE_REVIEW", "retries": 0, "run_id": "run-83b43a2ce6a849b99966ba54d3c44d5a", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `concurrent`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "concurrent", "provider_failures": 0, "recipe": "CONCURRENT", "retries": 0, "run_id": "run-e106469e3a9742c788914e1ce9ee1972", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}
- `handoff`: {"admitted": true, "contradiction_precision": 1.0, "contradiction_recall": 1.0, "finding_coverage": 1.0, "human_correction_effort": 1, "recovery_success": true, "run_metrics": {"correction_rounds": 0, "input_tokens": null, "model_calls": 0, "output_tokens": null, "pattern": "handoff", "provider_failures": 0, "recipe": "HANDOFF", "retries": 0, "run_id": "run-4b075d93405d45b993ec27b33b3350be", "wall_time_ms": 0}, "supported_claim_precision": 1.0, "traceability": 1.0}

- Controller recipe: `ANALYZE_REVIEW`
- Admitted pattern: `ordinary`

## Limitations
- Provider-backed calls are environment-gated; deterministic domain execution remains the local comparison baseline.
