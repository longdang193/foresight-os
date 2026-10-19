from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


ANALYSIS_INPUT_CONTRACT_FIELDS = frozenset(
    {
        "domain",
        "stage_id",
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
        "workbook_selection",
    }
)
GLOBAL_SCOPE = "GLOBAL_SCOPE"


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


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(item) for item in value)
    return value


@dataclass(frozen=True)
class AnalysisInputDeclaration:
    """Immutable sparse declaration preserved until workbook resolution."""

    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", MappingProxyType({str(key): _freeze(value) for key, value in self.values.items()}))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any], *, domain: str | None = None) -> "AnalysisInputDeclaration":
        data = dict(value)
        if domain is not None:
            data["domain"] = str(domain)
        if not str(data.get("domain", "")).strip():
            raise ValueError("analysis input declaration requires a domain")
        return cls(data)

    @property
    def domain(self) -> str:
        return str(self.values["domain"])

    @property
    def stage_id(self) -> str | None:
        value = self.values.get("stage_id")
        return str(value) if value is not None else None

    def to_dict(self) -> dict[str, Any]:
        return _canonical(self.values)

    def resolve(self) -> "AnalysisInputContract":
        return AnalysisInputContract.from_dict(self.to_dict())


@dataclass(frozen=True)
class _PeriodSpec:
    raw: str
    start_year: int
    start_month: int | None
    end_year: int
    end_month: int | None
    granularity: str

    @property
    def is_cross_year(self) -> bool:
        return self.start_year != self.end_year

    @property
    def start_key(self) -> tuple[int, int]:
        return self.start_year, self.start_month or 1

    @property
    def end_key(self) -> tuple[int, int]:
        return self.end_year, self.end_month or 12


def _parse_period(value: str) -> _PeriodSpec:
    raw = str(value)
    match = re.fullmatch(r"(\d{4})(?:(?:-(\d{2}))|(?:-Q([1-4])))?(?::(\d{4})(?:(?:-(\d{2}))|(?:-Q([1-4])))?)?", raw)
    if match is None:
        raise ValueError(f"invalid period syntax: {raw}")

    start_year = int(match.group(1))
    start_month = int(match.group(2)) if match.group(2) is not None else None
    start_quarter = int(match.group(3)) if match.group(3) is not None else None
    end_year = int(match.group(4) or start_year)
    end_month = int(match.group(5)) if match.group(5) is not None else None
    end_quarter = int(match.group(6)) if match.group(6) is not None else None
    for month in (start_month, end_month):
        if month is not None and not 1 <= month <= 12:
            raise ValueError(f"invalid period month: {raw}")

    start_key = (start_year, (start_quarter - 1) * 3 + 1 if start_quarter else start_month or 1)
    if end_quarter:
        end_key = (end_year, end_quarter * 3)
    elif end_month:
        end_key = (end_year, end_month)
    elif start_quarter:
        end_key = (end_year, start_quarter * 3)
    elif start_month:
        end_key = (end_year, start_month)
    else:
        end_key = (end_year, 12)
    if start_key > end_key:
        raise ValueError(f"invalid period range: {raw}")
    granularity = "range" if ":" in raw else "quarter" if start_quarter else "month" if start_month else "year"
    return _PeriodSpec(raw, start_year, start_key[1], end_year, end_key[1], granularity)


@dataclass(frozen=True)
class AnalysisInputContract:
    """Immutable, serializable input contract for one domain analysis."""

    domain: str
    stage_id: str | None = None
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
    workbook_selection: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name in (
            "required_tables",
            "entity_scope",
            "periods",
            "scenarios",
            "required_calculations",
            "required_validation_checks",
            "assumptions",
        ):
            object.__setattr__(self, field_name, _tuple(getattr(self, field_name)))
        object.__setattr__(self, "column_mappings", MappingProxyType({str(key): str(value) for key, value in self.column_mappings.items()}))
        object.__setattr__(self, "conversion_rates", MappingProxyType({str(key): float(value) for key, value in self.conversion_rates.items()}))
        object.__setattr__(self, "workbook_selection", MappingProxyType(_canonical(dict(self.workbook_selection))))
        self.validate()

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
            stage_id=str(data["stage_id"]) if data.get("stage_id") is not None else None,
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
            workbook_selection=dict(data.get("workbook_selection", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            **({"stage_id": self.stage_id} if self.stage_id else {}),
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
            **({"workbook_selection": _canonical(self.workbook_selection)} if self.workbook_selection else {}),
        }

    @property
    def fingerprint(self) -> str:
        payload_value = self.to_dict()
        payload_value.pop("stage_id", None)
        payload = json.dumps(_canonical(payload_value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @property
    def period_specs(self) -> tuple[_PeriodSpec, ...]:
        return tuple(_parse_period(period) for period in (*self.periods, self.baseline_period, self.comparison_period) if period is not None)

    def validate(self) -> None:
        if not self.domain.strip():
            raise ValueError("analysis input contract requires a domain")
        if self.baseline_period and self.comparison_period and self.baseline_period == self.comparison_period:
            raise ValueError("baseline and comparison periods must differ")
        if self.duplicate_policy not in {"flag_and_exclude", "keep_first", "reject"}:
            raise ValueError(f"unsupported duplicate policy: {self.duplicate_policy}")
        if self.missing_value_policy not in {"preserve_as_issue", "exclude", "reject"}:
            raise ValueError(f"unsupported missing-value policy: {self.missing_value_policy}")
        self.period_specs
        for field_name, value in (("units", self.units), ("reporting_currency", self.reporting_currency)):
            if value and not value.strip():
                raise ValueError(f"{field_name} must not be blank")
        if self.reporting_currency and not re.fullmatch(r"[A-Za-z]{3}", self.reporting_currency):
            raise ValueError("reporting currency must be a three-letter code")
        for currency, rate in self.conversion_rates.items():
            if not currency.strip() or not math.isfinite(rate) or rate <= 0:
                raise ValueError(f"conversion rate for {currency!r} must be finite and positive")
        for field_name, values in (("required_calculations", self.required_calculations), ("required_validation_checks", self.required_validation_checks)):
            if any(not value.strip() for value in values):
                raise ValueError(f"{field_name} must not contain blank values")


@dataclass(frozen=True)
class NormalizedIntent:
    decision_question: str
    horizon: str
    stages: tuple[dict[str, Any], ...] = ()
    dependencies: tuple[str, ...] = ()
    source_needs: tuple[dict[str, Any], ...] = ()
    required_capabilities: tuple[str, ...] = ()
    required_participants: tuple[str, ...] = ()
    review_checks: tuple[str, ...] = ()
    topology_requirements: tuple[str, ...] = ()
    resource_limits: dict[str, int | str] = field(default_factory=dict)
    contracts: tuple[AnalysisInputContract, ...] = ()
    declarations: tuple[AnalysisInputDeclaration, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "stages", tuple(_freeze(item) for item in self.stages))
        object.__setattr__(self, "source_needs", tuple(_freeze(item) for item in self.source_needs))
        object.__setattr__(self, "resource_limits", _freeze(self.resource_limits))
        object.__setattr__(self, "dependencies", tuple(str(item) for item in self.dependencies))
        object.__setattr__(self, "required_capabilities", tuple(str(item) for item in self.required_capabilities))
        object.__setattr__(self, "required_participants", tuple(str(item) for item in self.required_participants))
        object.__setattr__(self, "review_checks", tuple(str(item) for item in self.review_checks))
        object.__setattr__(self, "topology_requirements", tuple(str(item) for item in self.topology_requirements))

    @property
    def fingerprint(self) -> str:
        payload = {
            "decision_question": self.decision_question,
            "horizon": self.horizon,
            "stages": self.stages,
            "dependencies": self.dependencies,
            "source_needs": self.source_needs,
            "required_capabilities": self.required_capabilities,
            "required_participants": self.required_participants,
            "review_checks": self.review_checks,
            "topology_requirements": self.topology_requirements,
            "resource_limits": self.resource_limits,
            "contracts": [contract.to_dict() for contract in self.contracts],
        }
        return hashlib.sha256(json.dumps(_canonical(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    def contract_for_domain(self, domain: str, stage_id: str | None = None) -> AnalysisInputContract | None:
        return self._resolve_contract(domain, stage_id, required=False)

    def resolve_contract_for_domain(self, domain: str, stage_id: str) -> AnalysisInputContract:
        return self._resolve_contract(domain, stage_id, required=True)

    def declared_contract_for_domain(self, domain: str, stage_id: str | None = None) -> AnalysisInputDeclaration | None:
        return self._resolve_declaration(domain, stage_id, required=False)

    def resolve_declared_contract_for_domain(self, domain: str, stage_id: str) -> AnalysisInputDeclaration:
        declaration = self._resolve_declaration(domain, stage_id, required=True)
        assert declaration is not None
        return declaration

    def _resolve_declaration(
        self,
        domain: str,
        stage_id: str | None,
        *,
        required: bool,
    ) -> AnalysisInputDeclaration | None:
        wanted = str(domain).lower()
        scoped = [
            declaration
            for declaration in self.declarations
            if stage_id is not None and declaration.stage_id == str(stage_id) and declaration.domain.lower() == wanted
        ]
        global_matches = [
            declaration
            for declaration in self.declarations
            if declaration.stage_id is None and declaration.domain.lower() == wanted
        ]
        candidates = scoped or global_matches
        if len(candidates) > 1:
            scope = str(stage_id) if scoped else GLOBAL_SCOPE
            raise ValueError(f"ambiguous analysis input contract scope: {scope}:{domain}")
        if candidates:
            return candidates[0]
        if required:
            raise ValueError(f"missing analysis input contract: {stage_id}:{domain}")
        return None

    def _resolve_contract(
        self,
        domain: str,
        stage_id: str | None,
        *,
        required: bool,
    ) -> AnalysisInputContract | None:
        wanted = str(domain).lower()
        scoped = [
            contract
            for contract in self.contracts
            if stage_id is not None and contract.stage_id == str(stage_id) and contract.domain.lower() == wanted
        ]
        global_matches = [
            contract
            for contract in self.contracts
            if contract.stage_id is None and contract.domain.lower() == wanted
        ]
        candidates = scoped or global_matches
        if len(candidates) > 1:
            scope = str(stage_id) if scoped else GLOBAL_SCOPE
            raise ValueError(f"ambiguous analysis input contract: {scope}:{domain}")
        if candidates:
            return candidates[0]
        if required:
            raise ValueError(f"missing analysis input contract: {stage_id}:{domain}")
        return None


def contract_for_domain(
    intent: NormalizedIntent | None,
    domain: str,
    stage_id: str | None = None,
) -> AnalysisInputContract | None:
    return intent.contract_for_domain(domain, stage_id) if intent is not None else None


def normalize_work_brief(brief: Any) -> NormalizedIntent:
    value = brief.to_dict() if hasattr(brief, "to_dict") else dict(brief)
    contracts_value = value.get("analysis_inputs") or {}
    if isinstance(contracts_value, Mapping):
        expanded: list[Mapping[str, Any]] = []
        for domain, contract in contracts_value.items():
            if isinstance(contract, (list, tuple)):
                expanded.extend(
                    {**dict(item), "domain": str(domain)} if isinstance(item, Mapping) else {"domain": str(domain)}
                    for item in contract
                )
            else:
                expanded.append({**dict(contract), "domain": str(domain)} if isinstance(contract, Mapping) else {"domain": str(domain)})
        contracts_value = expanded
    stages = tuple(dict(stage) for stage in value.get("stages", ()))
    stage_ids = {str(stage.get("stage_id", "")) for stage in stages}
    declarations = tuple(AnalysisInputDeclaration.from_dict(item) for item in contracts_value)
    contracts = tuple(declaration.resolve() for declaration in declarations)
    seen_scopes: set[tuple[str, str]] = set()
    for contract in contracts:
        contract.validate()
        scope = contract.stage_id or GLOBAL_SCOPE
        key = (scope, contract.domain.lower())
        if key in seen_scopes:
            raise ValueError(f"duplicate analysis input contract scope: {scope}:{contract.domain}")
        seen_scopes.add(key)
        if contract.stage_id is not None and contract.stage_id not in stage_ids:
            raise ValueError(f"unknown analysis input contract stage: {contract.stage_id}")
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
    required_participants_values = list((value.get("execution_intent") or {}).get("required_participants", ()))
    required_participants_values.extend(
        participant
        for item in stages
        for participant in (item.get("execution_intent") or {}).get("required_participants", ())
    )
    required_participants = tuple(dict.fromkeys(str(participant) for participant in required_participants_values))
    resource_limits = dict(value.get("resource_limits") or {})
    resource_limits.update(dict((value.get("execution_intent") or {}).get("resource_limits") or {}))
    for item in stages:
        resource_limits.update(dict(item.get("limits") or {}))
    return NormalizedIntent(
        decision_question=str(value.get("decision_question", "")),
        horizon=str(value.get("horizon", "unspecified")),
        stages=stages,
        dependencies=tuple(str(item) for item in value.get("open_dependencies", ())),
        source_needs=source_needs,
        required_capabilities=required_capabilities,
        required_participants=required_participants,
        review_checks=tuple(str(item) for item in value.get("user_preferences", {}).get("review_checks", ())),
        topology_requirements=tuple(str(item) for item in (value.get("execution_intent") or {}).get("required_patterns", ())),
        resource_limits=resource_limits,
        contracts=contracts,
        declarations=declarations,
    )
