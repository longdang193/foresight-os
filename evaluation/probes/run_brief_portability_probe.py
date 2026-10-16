from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable


ROOT = Path(__file__).parents[2]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contract(domain: str, **overrides: Any):
    from foresight_os.domain.analysis_inputs import AnalysisInputContract

    return AnalysisInputContract(domain=domain, **overrides)


def _cases() -> tuple[dict[str, Any], ...]:
    from foresight_os.analysis.ev_capacity_investment import analyze_ev_capacity_investment
    from foresight_os.analysis.portfolio_resilience import analyze_portfolio_resilience
    from foresight_os.analysis.powerbi_strategic_portfolio import analyze_powerbi_strategic_portfolio
    from foresight_os.analysis.supplier_resilience import analyze_supplier_resilience
    from foresight_os.analysis.technology_radar import analyze_technology_radar

    return (
        {
            "domain": "portfolio_resilience",
            "fixture": "01_Portfolio_Resilience.xlsx",
            "analyze": analyze_portfolio_resilience,
            "contract": _contract("portfolio_resilience", baseline_period="2025", comparison_period="2024", periods=("2025",), entity_scope=("DACH",), scenarios=("Base",), reporting_currency="EUR"),
            "selected_inputs": {"baseline_period": "2025", "comparison_period": "2024", "entity_scope": ["DACH"], "scenarios": ["Base"]},
        },
        {
            "domain": "supplier_resilience",
            "fixture": "02_Supplier_Resilience.xlsx",
            "analyze": analyze_supplier_resilience,
            "contract": _contract("supplier_resilience", reporting_currency="EUR", conversion_rates={"EUR": 1.0}),
            "selected_inputs": {"reporting_currency": "EUR", "conversion_rates": ["EUR"]},
        },
        {
            "domain": "ev_capacity_investment",
            "fixture": "03_EV_Capacity_Investment.xlsx",
            "analyze": analyze_ev_capacity_investment,
            "contract": _contract("ev_capacity_investment", periods=("2030",), entity_scope=("DACH",), scenarios=("Base",), units="units"),
            "selected_inputs": {"periods": ["2030"], "entity_scope": ["DACH"], "scenarios": ["Base"]},
        },
        {
            "domain": "technology_radar",
            "fixture": "04_Technology_Radar.xlsx",
            "analyze": analyze_technology_radar,
            "contract": _contract("technology_radar", entity_scope=("Zonal Architecture",), units="index"),
            "selected_inputs": {"entity_scope": ["Zonal Architecture"]},
        },
        {
            "domain": "powerbi_strategic_portfolio",
            "fixture": "05_PowerBI_Strategic_Portfolio.xlsx",
            "analyze": analyze_powerbi_strategic_portfolio,
            "contract": _contract("powerbi_strategic_portfolio", baseline_period="2025", comparison_period="2026", entity_scope=("Analytics",), units="EUR"),
            "selected_inputs": {"baseline_period": "2025", "comparison_period": "2026", "entity_scope": ["Analytics"]},
        },
    )


def _summary(analysis: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "contract_fingerprint": analysis.contract_fingerprint,
        "evidence_count": len(analysis.state.evidence),
        "calculation_count": len(analysis.state.calculations),
        "issue_kinds": sorted({item.kind for item in analysis.data_quality_issues}),
    }
    if hasattr(analysis, "segment_baselines"):
        values["selected_scope_total"] = round(sum(item.revenue for item in analysis.segment_baselines), 6)
    elif hasattr(analysis, "metrics"):
        values["selected_scope_total"] = round(sum(item.spend_eur for item in analysis.metrics), 6)
    elif hasattr(analysis, "scenarios"):
        values["selected_scope_count"] = len(analysis.scenarios)
    elif hasattr(analysis, "assessments"):
        values["selected_scope_count"] = len(analysis.assessments)
    elif hasattr(analysis, "segment_assessments"):
        values["selected_scope_count"] = len(analysis.segment_assessments)
    return values


def run(output_root: Path) -> dict[str, Any]:
    fixture_root = ROOT / "tests" / "fixtures" / "exercise"
    missing = [case["fixture"] for case in _cases() if not (fixture_root / case["fixture"]).is_file()]
    if missing:
        return {"schema_version": 1, "status": "BLOCKED_INPUT", "missing_fixtures": missing, "cases": []}

    output_root.mkdir(parents=True, exist_ok=True)
    cases: list[dict[str, Any]] = []
    with TemporaryDirectory(prefix="foresight-brief-portability-") as temporary:
        temp_root = Path(temporary)
        for case in _cases():
            source = fixture_root / case["fixture"]
            copied = temp_root / case["fixture"]
            shutil.copyfile(source, copied)
            analyze: Callable[..., Any] = case["analyze"]
            try:
                baseline = analyze(copied)
                changed = analyze(copied, case["contract"])
                baseline_summary = _summary(baseline)
                changed_summary = _summary(changed)
                changed_scope = baseline_summary.get("selected_scope_total", baseline_summary.get("selected_scope_count")) != changed_summary.get("selected_scope_total", changed_summary.get("selected_scope_count"))
                unsupported_conversion = "UNSUPPORTED_CONVERSION" in changed_summary["issue_kinds"]
                structural_assertion = changed.contract_fingerprint != baseline.contract_fingerprint and (changed_scope or unsupported_conversion)
                status = "VERIFIED" if structural_assertion else "FAILED"
                cases.append({
                    "domain": case["domain"],
                    "status": status,
                    "source_sha256": _sha256(source),
                    "fixture_copy_sha256": _sha256(copied),
                    "contract_fingerprint": changed.contract_fingerprint,
                    "selected_inputs": case["selected_inputs"],
                    "baseline": baseline_summary,
                    "changed": changed_summary,
                    "structural_assertion": "changed brief changes selected scope or exposes unsupported conversion",
                    "provider_status": "not_measured",
                    "human_acceptance": "not_measured",
                })
            except Exception as error:
                cases.append({"domain": case["domain"], "status": "FAILED", "error_type": type(error).__name__, "error": str(error)})

    receipt = {
        "schema_version": 1,
        "status": "VERIFIED" if cases and all(case["status"] == "VERIFIED" for case in cases) else "FAILED",
        "evidence_scope": "production XLSX analyzer path with deterministic changed-brief contracts",
        "cases": cases,
        "limitations": [
            "provider/model quality and human acceptance are not measured by this local structural probe",
            "receipts contain hashes, contract identities, and outcome summaries only; raw workbook payloads are excluded",
        ],
    }
    receipt_path = output_root / "brief-portability-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT / "work" / "brief-portability-20261016" / "final")
    args = parser.parse_args(argv)
    if not args.output_root.is_absolute():
        args.output_root = ROOT / args.output_root
    if not args.output_root.exists():
        args.output_root.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT / "src"))
    receipt = run(args.output_root)
    return 0 if receipt["status"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
