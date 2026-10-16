from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Mapping


ANALYSIS_INPUT_CONTRACT_FIELDS = frozenset(
    {
        "domain",
        "name",
        "required_tables",
        "tables",
        "column_mappings",
        "entity_scope",
        "entities",
        "periods",
        "baseline_period",
        "comparison_period",
        "scenarios",
        "units",
        "reporting_currency",
        "currency",
        "conversion_rates",
        "duplicate_policy",
        "missing_value_policy",
        "required_calculations",
        "required_validation_checks",
        "validation_checks",
        "assumptions",
        "compatibility_assumption",
    }
)


def _tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(item) for item in value)


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_canonical(item) for item in value]
    if hasattr(value, "to_dict"):
        return _canonical(value.to_dict())
    return value


@dataclass(frozen=True)
class AnalysisInputContract:
    """Immutable, serializable input contract for one domain analysis."""

    domain: str
    required_tables: tuple[str, ...] = ()
    column_mappings: dict[str, str] = field(default_factory=dict)
    entity_scope: tuple[str, ...] = ()
    periods: tuple[str, ...] = ()
    baseline_period: str | None = None
    comparison_period: str | None = None
    scenarios: tuple[str, ...] = ()
    units: str = ""
    reporting_currency: str = ""
    conversion_rates: dict[str, float] = field(default_factory=dict)
    duplicate_policy: str = "flag_and_exclude"
    missing_value_policy: str = "preserve_as_issue"
    required_calculations: tuple[str, ...] = ()
    required_validation_checks: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    compatibility_assumption: str | None = None

    @classmethod
    def from_dict(cls, value: Mapping[str, Any] | AnalysisInputContract) -> AnalysisInputContract:
        if isinstance(value, cls):
            return value
        data = dict(value)
        unknown = sorted(set(data) - ANALYSIS_INPUT_CONTRACT_FIELDS)
        if unknown:
            raise ValueError(f"analysis input contract contains unsupported fields: {', '.join(unknown)}")
        rates = {str(key): float(rate) for key, rate in dict(data.get("conversion_rates", {})).items()}
        return cls(
            domain=str(data.get("domain", data.get("name", ""))),
            required_tables=_tuple(data.get("required_tables", data.get("tables", ()))),
            column_mappings={str(key): str(item) for key, item in dict(data.get("column_mappings", {})).items()},
            entity_scope=_tuple(data.get("entity_scope", data.get("entities", ()))),
            periods=_tuple(data.get("periods", ())),
            baseline_period=str(data["baseline_period"]) if data.get("baseline_period") is not None else None,
            comparison_period=str(data["comparison_period"]) if data.get("comparison_period") is not None else None,
            scenarios=_tuple(data.get("scenarios", ())),
            units=str(data.get("units", "")),
            reporting_currency=str(data.get("reporting_currency", data.get("currency", ""))),
            conversion_rates=rates,
            duplicate_policy=str(data.get("duplicate_policy", "flag_and_exclude")),
            missing_value_policy=str(data.get("missing_value_policy", "preserve_as_issue")),
            required_calculations=_tuple(data.get("required_calculations", ())),
            required_validation_checks=_tuple(data.get("required_validation_checks", data.get("validation_checks", ()))),
            assumptions=_tuple(data.get("assumptions", ())),
            compatibility_assumption=(str(data["compatibility_assumption"]) if data.get("compatibility_assumption") is not None else None),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "required_tables": list(self.required_tables),
            "column_mappings": dict(sorted(self.column_mappings.items())),
            "entity_scope": list(self.entity_scope),
            "periods": list(self.periods),
            "baseline_period": self.baseline_period,
            "comparison_period": self.comparison_period,
            "scenarios": list(self.scenarios),
            "units": self.units,
            "reporting_currency": self.reporting_currency,
            "conversion_rates": dict(sorted(self.conversion_rates.items())),
            "duplicate_policy": self.duplicate_policy,
            "missing_value_policy": self.missing_value_policy,
            "required_calculations": list(self.required_calculations),
            "required_validation_checks": list(self.required_validation_checks),
            "assumptions": list(self.assumptions),
            **({"compatibility_assumption": self.compatibility_assumption} if self.compatibility_assumption else {}),
        }

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(_canonical(self.to_dict()), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def validate(self) -> None:
        if not self.domain.strip():
            raise ValueError("analysis input contract requires a domain")
        if self.baseline_period and self.comparison_period and self.baseline_period == self.comparison_period:
            raise ValueError("baseline and comparison periods must differ")
        if self.duplicate_policy not in {"flag_and_exclude", "keep_first", "reject"}:
            raise ValueError(f"unsupported duplicate policy: {self.duplicate_policy}")
        if self.missing_value_policy not in {"preserve_as_issue", "exclude", "reject"}:
            raise ValueError(f"unsupported missing-value policy: {self.missing_value_policy}")
        for currency, rate in self.conversion_rates.items():
            if not currency.strip() or not math.isfinite(rate) or rate <= 0:
                raise ValueError(f"conversion rate for {currency!r} must be finite and positive")


@dataclass(frozen=True)
class NormalizedIntent:
    decision_question: str
    horizon: str
    stages: tuple[dict[str, Any], ...] = ()
    dependencies: tuple[str, ...] = ()
    source_needs: tuple[dict[str, Any], ...] = ()
    required_capabilities: tuple[str, ...] = ()
    review_checks: tuple[str, ...] = ()
    topology_requirements: tuple[str, ...] = ()
    resource_limits: dict[str, int | str] = field(default_factory=dict)
    contracts: tuple[AnalysisInputContract, ...] = ()

    @property
    def fingerprint(self) -> str:
        payload = {
            "decision_question": self.decision_question,
            "horizon": self.horizon,
            "stages": self.stages,
            "dependencies": self.dependencies,
            "source_needs": self.source_needs,
            "required_capabilities": self.required_capabilities,
            "review_checks": self.review_checks,
            "topology_requirements": self.topology_requirements,
            "resource_limits": self.resource_limits,
            "contracts": [contract.to_dict() for contract in self.contracts],
        }
        return hashlib.sha256(json.dumps(_canonical(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    def contract_for_domain(self, domain: str) -> AnalysisInputContract | None:
        wanted = str(domain).lower()
        return next((contract for contract in self.contracts if contract.domain.lower() == wanted), None)


def contract_for_domain(intent: NormalizedIntent | None, domain: str) -> AnalysisInputContract | None:
    return intent.contract_for_domain(domain) if intent is not None else None


def normalize_work_brief(brief: Any) -> NormalizedIntent:
    value = brief.to_dict() if hasattr(brief, "to_dict") else dict(brief)
    contracts_value = value.get("analysis_inputs") or {}
    if isinstance(contracts_value, Mapping):
        contracts_value = [
            {**dict(contract), "domain": str(domain)} if isinstance(contract, Mapping) else {"domain": str(domain)}
            for domain, contract in contracts_value.items()
        ]
    contracts = tuple(AnalysisInputContract.from_dict(item) for item in contracts_value)
    for contract in contracts:
        contract.validate()
    stages = tuple(dict(stage) for stage in value.get("stages", ()))
    source_needs = tuple(
        dict(need)
        for stage in stages
        for need in stage.get("research_needs", ())
        if isinstance(need, Mapping)
    )
    required_capabilities_values = list((value.get("execution_intent") or {}).get("required_capabilities", ()))
    required_capabilities_values.extend(
        capability
        for item in stages
        for capability in (item.get("execution_intent") or {}).get("required_capabilities", ())
    )
    required_capabilities = tuple(dict.fromkeys(str(capability) for capability in required_capabilities_values))
    return NormalizedIntent(
        decision_question=str(value.get("decision_question", "")),
        horizon=str(value.get("horizon", "unspecified")),
        stages=stages,
        dependencies=tuple(str(item) for item in value.get("open_dependencies", ())),
        source_needs=source_needs,
        required_capabilities=required_capabilities,
        review_checks=tuple(str(item) for item in value.get("user_preferences", {}).get("review_checks", ())),
        topology_requirements=tuple(str(item) for item in (value.get("execution_intent") or {}).get("required_patterns", ())),
        resource_limits={},
        contracts=contracts,
    )
