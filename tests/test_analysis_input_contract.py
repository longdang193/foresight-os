from pathlib import Path

import pytest

from foresight_os.analysis.supplier_resilience import analyze_supplier_resilience
from foresight_os.domain.analysis_inputs import AnalysisInputContract, normalize_work_brief
from foresight_os.domain.models import WorkBrief
from foresight_os.domain.validation import ValidationError, validate_work_brief


def _brief(**analysis_inputs):
    return WorkBrief(
        "contract-test",
        "Which inputs should be assessed?",
        [],
        ["analysis"],
        [],
        [],
        "assess",
        "execute",
        analysis_inputs=analysis_inputs,
    )


def test_analysis_input_contract_round_trips_and_fingerprints_deterministically():
    contract = AnalysisInputContract(
        domain="supplier_resilience",
        required_tables=("Supplier_Master",),
        periods=("2026",),
        reporting_currency="EUR",
        conversion_rates={"USD": 0.92, "EUR": 1.0},
        assumptions=("legacy compatibility",),
    )
    value = validate_work_brief(_brief(supplier_resilience=contract.to_dict()))
    normalized = normalize_work_brief(value)

    assert normalized.contract_for_domain("supplier_resilience") == contract
    assert normalized.contract_for_domain("supplier_resilience").fingerprint == contract.fingerprint
    assert validate_work_brief(value)["analysis_inputs"][0]["domain"] == "supplier_resilience"


def test_invalid_contract_policy_is_rejected_before_analysis():
    with pytest.raises((ValidationError, ValueError), match="duplicate policy"):
        validate_work_brief(_brief(supplier_resilience={"domain": "supplier_resilience", "duplicate_policy": "invented"}))


def test_explicit_incomplete_supplier_conversion_does_not_use_legacy_fx():
    source = Path("tests/fixtures/exercise/02_Supplier_Resilience.xlsx")
    analysis = analyze_supplier_resilience(
        source,
        AnalysisInputContract(
            domain="supplier_resilience",
            conversion_rates={"EUR": 1.0},
            reporting_currency="EUR",
        ),
    )

    assert any(issue.kind == "UNSUPPORTED_CONVERSION" for issue in analysis.data_quality_issues)


def test_legacy_supplier_contract_retains_documented_fx_assumption():
    analysis = analyze_supplier_resilience(Path("tests/fixtures/exercise/02_Supplier_Resilience.xlsx"))

    assert any("USD=0.92" in assumption for assumption in analysis.assumptions)
