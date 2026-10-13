from dataclasses import dataclass, field
from enum import StrEnum


class FailureClass(StrEnum):
    PROVIDER = "provider"
    TOOL = "tool"
    DOMAIN_VALIDATION = "domain_validation"
    TIMEOUT = "timeout"
    CANCELLATION = "cancellation"
    BUDGET = "budget"
    CLEANUP = "cleanup"


class CleanupError(RuntimeError):
    """Raised when a run cannot close an owned runtime resource."""


class BudgetExceededError(RuntimeError):
    """Raised before dispatch when a declared run limit would be exceeded."""


@dataclass(frozen=True)
class ConcurrentAggregate:
    results: tuple[object, ...]
    failures: tuple[BaseException, ...] = ()


@dataclass
class RunMetrics:
    run_id: str
    recipe: str
    pattern: str
    model_calls: int = 0
    participant_invocations: int = 0
    retries: int = 0
    correction_rounds: int = 0
    wall_time_ms: int = 0
    provider_failures: int = 0
    tool_calls: int = 0
    tool_failures: int = 0
    tool_latency_ms: int = 0
    queue_wait_ms: int = 0
    execution_time_ms: int = 0
    cancellation_settlements: int = 0
    duplicate_retrievals: int = 0
    domain_failures: int = 0
    timeout_failures: int = 0
    cancellation_failures: int = 0
    budget_failures: int = 0
    cleanup_failures: int = 0
    cleanup_failure_message: str | None = None
    provider_requests: int | None = None
    primary_failure_class: str | None = None
    primary_failure_message: str | None = None
    capability_reuses: int = 0
    human_correction: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    branches: int = 0
    parallelism: int = 0
    handoffs: int = 0
    chat_rounds: int = 0
    cleanup_complete: bool = False
    failure_class: str | None = None
    failure_message: str | None = None
    failure_counts: dict[str, int] = field(default_factory=dict)
    settled: bool = False

    def record_failure(self, failure_class: FailureClass, error: BaseException) -> None:
        if failure_class == FailureClass.CLEANUP and self.failure_class is not None:
            self.cleanup_failure_message = str(error)
        else:
            self.failure_class = failure_class.value
            self.failure_message = str(error)
            if failure_class != FailureClass.CLEANUP:
                self.primary_failure_class = failure_class.value
                self.primary_failure_message = str(error)
        key = failure_class.value
        self.failure_counts[key] = self.failure_counts.get(key, 0) + 1
        if failure_class == FailureClass.PROVIDER:
            self.provider_failures += 1
        elif failure_class == FailureClass.TOOL:
            self.tool_failures += 1
        elif failure_class == FailureClass.DOMAIN_VALIDATION:
            self.domain_failures += 1
        elif failure_class == FailureClass.TIMEOUT:
            self.timeout_failures += 1
        elif failure_class == FailureClass.CANCELLATION:
            self.cancellation_failures += 1
        elif failure_class == FailureClass.BUDGET:
            self.budget_failures += 1
        elif failure_class == FailureClass.CLEANUP:
            self.cleanup_failures += 1
            if self.cleanup_failure_message is None:
                self.cleanup_failure_message = str(error)


@dataclass(frozen=True)
class RunResult:
    run_id: str
    outputs: tuple[object, ...]
    metrics: RunMetrics
