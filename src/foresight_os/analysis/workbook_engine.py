from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from foresight_os.analysis.workbook_inputs import (
    MaterialView,
    ResolvedWorkbookLayout,
    WorkbookLayoutSpec,
    build_material_view,
    resolve_workbook_layout,
)
from foresight_os.domain.analysis_inputs import AnalysisInputContract
from foresight_os.runtime.local_toolbelt import (
    CancellationRequested,
    MissingWorkbookInputError,
    ToolbeltError,
    WorkbookContext,
)


@dataclass(frozen=True)
class DomainAnalysis:
    """Deterministic domain output before workflow lifecycle settlement."""

    result: Any
    state: Any | None = None
    diagnostics: tuple[str, ...] = ()


class DomainAnalyzer(Protocol):
    def __call__(self, material: MaterialView, contract: AnalysisInputContract) -> DomainAnalysis | Any:
        ...


@dataclass(frozen=True)
class WorkbookEngineResult:
    status: str
    domain_result: DomainAnalysis | None = None
    material_view: MaterialView | None = None
    layout: ResolvedWorkbookLayout | None = None
    context: WorkbookContext | None = None
    failure: str | None = None
    diagnostics: tuple[str, ...] = ()
    metrics: Mapping[str, int] = field(default_factory=dict)


class WorkbookAnalysisEngine:
    """Compose deterministic workbook inputs and invoke one domain analyzer."""

    def __init__(self, *, context: WorkbookContext | None = None) -> None:
        self.context = context

    def run(
        self,
        source: str | Path,
        contract: AnalysisInputContract | Mapping[str, Any],
        analyzer: DomainAnalyzer,
        *,
        layout_spec: WorkbookLayoutSpec | None = None,
        context: WorkbookContext | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ) -> WorkbookEngineResult:
        normalized_contract = AnalysisInputContract.from_dict(contract)
        active_context = context or self.context or WorkbookContext()
        spec = layout_spec or WorkbookLayoutSpec.from_contract(normalized_contract)
        selection = spec.selection
        if selection is None and normalized_contract.required_tables:
            selection = {
                "sheet_names": list(normalized_contract.required_tables),
                "include_hidden": True,
                "include_hidden_rows": True,
            }
        try:
            workbook = active_context.read(source, selection or None, cancel_check=cancel_check)
            layout = resolve_workbook_layout(workbook, spec)
            material = build_material_view(workbook, layout, normalized_contract)
            value = analyzer(material, normalized_contract)
            domain_result = value if isinstance(value, DomainAnalysis) else DomainAnalysis(result=value)
            metrics = {
                "capture_count": int(active_context.stats.capture_count),
                "xlsx_parse_count": int(active_context.stats.xlsx_parse_count),
                "materialized_table_count": len(material.tables),
                "materialized_row_count": sum(len(table.rows) for _, table in material.tables),
            }
            return WorkbookEngineResult(
                status="completed",
                domain_result=domain_result,
                material_view=material,
                layout=layout,
                context=active_context,
                diagnostics=domain_result.diagnostics,
                metrics=metrics,
            )
        except CancellationRequested as error:
            return WorkbookEngineResult(status="cancelled", context=active_context, failure=str(error))
        except MissingWorkbookInputError as error:
            return WorkbookEngineResult(status="blocked_input", context=active_context, failure=str(error))
        except ToolbeltError as error:
            return WorkbookEngineResult(status="blocked_input", context=active_context, failure=str(error))
        except Exception as error:  # domain adapters convert malformed output at the workflow boundary
            return WorkbookEngineResult(status="failed", context=active_context, failure=f"{type(error).__name__}: {error}")
