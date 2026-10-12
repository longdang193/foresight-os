from dataclasses import dataclass


@dataclass
class RunMetrics:
    run_id: str
    recipe: str
    pattern: str
    model_calls: int = 0
    retries: int = 0
    correction_rounds: int = 0
    wall_time_ms: int = 0
    provider_failures: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    branches: int = 0
    parallelism: int = 0
    handoffs: int = 0
    chat_rounds: int = 0
    cleanup_complete: bool = False


@dataclass(frozen=True)
class RunResult:
    run_id: str
    outputs: tuple[object, ...]
    metrics: RunMetrics
