from __future__ import annotations

from dataclasses import dataclass, is_dataclass, replace
from pathlib import Path
from typing import Any, Callable, Mapping

from foresight_os.analysis.reviewer import ReviewResult, review_analysis_state
from foresight_os.analysis.review_workflow import review_and_accept_pending_analysis
from foresight_os.analysis.workbook_engine import DomainAnalyzer, DomainAnalysis, WorkbookAnalysisEngine
from foresight_os.analysis.workbook_inputs import WorkbookLayoutSpec, resolve_workbook_contract
from foresight_os.domain.analysis_inputs import AnalysisInputContract
from foresight_os.domain.models import AnalysisState
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.local_toolbelt import WorkbookContext


@dataclass(frozen=True)
class WorkbookWorkflowResult:
    """Settled result for a standalone deterministic workbook workflow."""

    status: str
    state: AnalysisState | None = None
    domain_result: Any | None = None
    review: ReviewResult | None = None
    report_path: Path | None = None
    failure: str | None = None
    artifact_status: str = "not_requested"
    artifact_error: str | None = None
    source_fingerprint: str = ""
    layout_fingerprint: str = ""
    contract_fingerprint: str = ""
    diagnostics: tuple[str, ...] = ()
    metrics: Mapping[str, int] | None = None

    def __post_init__(self) -> None:
        if self.metrics is None:
            object.__setattr__(self, "metrics", {})


def _state_from_domain(domain: DomainAnalysis) -> AnalysisState | None:
    if isinstance(domain.state, AnalysisState):
        return domain.state
    candidate = getattr(domain.result, "state", None)
    return candidate if isinstance(candidate, AnalysisState) else None


def _with_state(value: Any, state: AnalysisState) -> Any:
    if is_dataclass(value) and hasattr(value, "state"):
        return replace(value, state=state)
    return value


class WorkbookWorkflowRunner:
    """Apply the existing analysis lifecycle to a pure workbook engine result."""

    def __init__(self, store: AnalysisStore, *, engine: WorkbookAnalysisEngine | None = None) -> None:
        self.store = store
        self.engine = engine or WorkbookAnalysisEngine()

    def run(
        self,
        source: str | Path,
        contract: AnalysisInputContract | Mapping[str, Any],
        analyzer: DomainAnalyzer,
        *,
        layout_spec: WorkbookLayoutSpec | None = None,
        workbook_context: WorkbookContext | None = None,
        human_decision: str = "REJECT",
        output_dir: Path | None = None,
        report_name: str = "executive-report.md",
        render_report: Callable[[Path, Any, AnalysisState], None] | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> WorkbookWorkflowResult:
        if isinstance(contract, AnalysisInputContract):
            normalized = contract
        else:
            domain = dict(contract).get("domain", "")
            try:
                normalized = resolve_workbook_contract(domain, contract)
            except ValueError as error:
                if not str(error).startswith("unsupported workbook analysis domain:"):
                    raise
                normalized = AnalysisInputContract.from_dict(contract)
        engine_result = self.engine.run(
            source,
            normalized,
            analyzer,
            layout_spec=layout_spec,
            context=workbook_context,
            cancel_check=cancel_check,
            materialize_scope=False,
        )
        layout = engine_result.layout
        fingerprints = {
            "source_fingerprint": layout.source_sha256 if layout else "",
            "layout_fingerprint": layout.fingerprint if layout else "",
            "contract_fingerprint": normalized.fingerprint,
        }
        metrics = dict(engine_result.metrics)
        metrics["review_calls"] = 0
        metrics["acceptance_status"] = 0
        metrics["cancellation_settled"] = int(engine_result.status == "cancelled")

        if engine_result.status != "completed" or engine_result.domain_result is None:
            return WorkbookWorkflowResult(
                status=engine_result.status,
                failure=engine_result.failure,
                diagnostics=engine_result.diagnostics,
                metrics=metrics,
                **fingerprints,
            )

        state = _state_from_domain(engine_result.domain_result)
        if state is None:
            return WorkbookWorkflowResult(
                status="failed",
                domain_result=engine_result.domain_result.result,
                failure="domain analyzer did not return AnalysisState",
                diagnostics=engine_result.diagnostics,
                metrics=metrics,
                **fingerprints,
            )

        try:
            pending = self.store.save_pending(state)
            metrics["state_bytes"] = self.store.pending_analysis_path.stat().st_size
            review = review_analysis_state(pending)
            metrics["review_calls"] = 1
            acceptance = review_and_accept_pending_analysis(
                self.store,
                pending,
                review,
                f"review-{pending.investigation_id}-{pending.revision}",
                human_decision=human_decision,
                metadata={
                    "source_fingerprints": (
                        fingerprints["source_fingerprint"],
                        fingerprints["layout_fingerprint"],
                        fingerprints["contract_fingerprint"],
                    ),
                },
            )
            metrics["acceptance_status"] = 1 if acceptance.status == "accepted" else 0
            settled_result = _with_state(engine_result.domain_result.result, acceptance.state)
            if acceptance.status == "pending":
                return WorkbookWorkflowResult(
                    status="pending",
                    state=acceptance.state,
                    domain_result=settled_result,
                    review=review,
                    failure=acceptance.failure,
                    diagnostics=engine_result.diagnostics,
                    metrics=metrics,
                    **fingerprints,
                )
            if acceptance.status != "accepted":
                return WorkbookWorkflowResult(
                    status="rejected",
                    state=acceptance.state,
                    domain_result=settled_result,
                    review=review,
                    failure=acceptance.failure,
                    diagnostics=engine_result.diagnostics,
                    metrics=metrics,
                    **fingerprints,
                )

            report_path = None
            artifact_status = "not_requested"
            artifact_error = None
            if render_report is not None:
                report_root = Path(output_dir) if output_dir is not None else self.store.root / "artifacts"
                report_path = report_root / report_name
                try:
                    render_report(report_path, settled_result, acceptance.state)
                except Exception as error:
                    artifact_status = "failed"
                    artifact_error = f"{type(error).__name__}: {error}"
                else:
                    artifact_status = "accepted"
            return WorkbookWorkflowResult(
                status="accepted",
                state=acceptance.state,
                domain_result=settled_result,
                review=review,
                report_path=report_path,
                artifact_status=artifact_status,
                artifact_error=artifact_error,
                diagnostics=engine_result.diagnostics,
                metrics=metrics,
                **fingerprints,
            )
        except Exception as error:
            return WorkbookWorkflowResult(
                status="failed",
                state=state,
                domain_result=engine_result.domain_result.result,
                failure=f"{type(error).__name__}: {error}",
                diagnostics=engine_result.diagnostics,
                metrics=metrics,
                **fingerprints,
            )

    def retry_render(
        self,
        result: WorkbookWorkflowResult,
        *,
        render_report: Callable[[Path, Any, AnalysisState], None],
        output_dir: Path | None = None,
        report_name: str = "executive-report.md",
    ) -> WorkbookWorkflowResult:
        """Retry only artifact rendering for an already accepted revision."""
        if result.status != "accepted" or result.state is None or result.domain_result is None:
            return replace(
                result,
                artifact_status="failed",
                artifact_error="retry render requires an accepted analysis result",
            )
        report_root = Path(output_dir) if output_dir is not None else self.store.root / "artifacts"
        report_path = report_root / report_name
        try:
            render_report(report_path, result.domain_result, result.state)
        except Exception as error:
            return replace(
                result,
                report_path=report_path,
                artifact_status="failed",
                artifact_error=f"{type(error).__name__}: {error}",
            )
        return replace(
            result,
            report_path=report_path,
            artifact_status="accepted",
            artifact_error=None,
        )


def merge_input_contract(
    default: AnalysisInputContract,
    value: AnalysisInputContract | Mapping[str, Any] | None,
) -> AnalysisInputContract:
    """Compatibility wrapper for the canonical workbook contract resolver."""
    return resolve_workbook_contract(default.domain, value)
