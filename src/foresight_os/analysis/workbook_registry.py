from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from importlib import import_module
from typing import Any


@dataclass(frozen=True)
class DomainWorkbookSpec:
    domain: str
    analyzer_module: str
    analyzer_symbol: str
    analyzer_version: str

    def default_contract(self):
        from foresight_os.domain.analysis_inputs import AnalysisInputContract

        defaults = {
            "portfolio_resilience": AnalysisInputContract(
                domain=self.domain,
                required_tables=("Brief", "Sales_History", "Fixed_Costs", "Scenario_Assumptions", "Strategic_Options", "Reported_KPIs"),
                periods=("2026", "2025"),
                baseline_period="2026",
                comparison_period="2025",
                scenarios=("Downside", "Base", "Upside"),
                units="EUR",
                reporting_currency="EUR",
                compatibility_assumption="legacy workbook metadata defaults",
            ),
            "supplier_resilience": AnalysisInputContract(
                domain=self.domain,
                required_tables=("Brief", "Supplier_Master", "Incidents", "Scenario_Assumptions", "Mitigation_Options"),
                units="EUR",
                reporting_currency="EUR",
                conversion_rates={"EUR": 1.0, "USD": 0.92, "CNY": 0.13},
                compatibility_assumption="legacy supplier workbook FX map: EUR=1.0, USD=0.92, CNY=0.13",
            ),
            "ev_capacity_investment": AnalysisInputContract(
                domain=self.domain,
                required_tables=("Brief", "Demand_History", "Demand_Scenarios", "Capacity", "Infrastructure", "Policy_Signals", "Strategic_Options", "Reported_KPIs"),
                periods=("2025", "2026", "2030"),
                scenarios=("Low", "Base", "High"),
                units="units",
                compatibility_assumption="legacy workbook scenario defaults",
            ),
            "technology_radar": AnalysisInputContract(
                domain=self.domain,
                required_tables=("Brief", "Signals", "Company_Relevance", "Competitor_Actions", "Scenario_Signposts", "Priority_Scoring"),
                units="index",
                compatibility_assumption="legacy technology radar scope",
            ),
            "powerbi_strategic_portfolio": AnalysisInputContract(
                domain=self.domain,
                required_tables=("Brief", "Dim_Region", "Dim_Segment", "Fact_Performance", "Targets", "Forward_Signals", "Measure_Definitions", "Dashboard_Snapshot", "Strategic_Options", "Change_One_Input"),
                baseline_period="2025-01:2025-09",
                comparison_period="2026-01:2026-09",
                units="EUR",
                periods=("2025-01:2025-09", "2026-01:2026-09"),
                compatibility_assumption="legacy Power BI comparable-period defaults",
            ),
        }
        return defaults[self.domain]

    def load_analyzer(self) -> Callable[..., Any]:
        module = import_module(self.analyzer_module)
        return getattr(module, self.analyzer_symbol)


_SPECS = {
    "portfolio_resilience": DomainWorkbookSpec("portfolio_resilience", "foresight_os.analysis.portfolio_resilience", "_analyze_portfolio_material", "1"),
    "supplier_resilience": DomainWorkbookSpec("supplier_resilience", "foresight_os.analysis.supplier_resilience", "_analyze_supplier_material", "1"),
    "ev_capacity_investment": DomainWorkbookSpec("ev_capacity_investment", "foresight_os.analysis.ev_capacity_investment", "_analyze_ev_material", "1"),
    "technology_radar": DomainWorkbookSpec("technology_radar", "foresight_os.analysis.technology_radar", "_analyze_technology_material", "1"),
    "powerbi_strategic_portfolio": DomainWorkbookSpec("powerbi_strategic_portfolio", "foresight_os.analysis.powerbi_strategic_portfolio", "_analyze_powerbi_material", "1"),
}
WORKBOOK_DOMAINS = tuple(_SPECS)


def get_workbook_spec(domain: str) -> DomainWorkbookSpec:
    try:
        return _SPECS[str(domain)]
    except KeyError as error:
        raise ValueError(f"unsupported workbook analysis domain: {domain}") from error


def default_workbook_contract_for(domain: str):
    return get_workbook_spec(domain).default_contract()


def get_workbook_analyzer(domain: str) -> Callable[..., Any]:
    return get_workbook_spec(domain).load_analyzer()


def workbook_analyzer_version_for(domain: str) -> str:
    return get_workbook_spec(domain).analyzer_version


def workbook_analyzer_fingerprint_for(domain: str) -> str:
    import hashlib

    payload = f"{domain}:{workbook_analyzer_version_for(domain)}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class _LazyAnalyzerMap(Mapping[str, Callable[..., Any]]):
    def __getitem__(self, domain: str) -> Callable[..., Any]:
        return get_workbook_analyzer(domain)

    def __iter__(self) -> Iterator[str]:
        return iter(WORKBOOK_DOMAINS)

    def __len__(self) -> int:
        return len(WORKBOOK_DOMAINS)


def workbook_analyzer_map() -> Mapping[str, Callable[..., Any]]:
    return _LazyAnalyzerMap()
