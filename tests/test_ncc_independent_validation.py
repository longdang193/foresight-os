from pathlib import Path

import openpyxl
import pytest

from foresight_os.analysis.independent_validation import (
    category_mapping_check,
    channel_comparability_check,
    conditional_check,
    growth_rate,
    planning_threshold_check,
    read_validation_source,
    reconcile_calculation,
    run_independent_validation,
)
from foresight_os.domain.challenge import ReviewSlotStatus
from foresight_os.runtime.local_toolbelt import SheetSelection, SourceSnapshot


def make_workbook(path: Path) -> None:
    workbook = openpyxl.Workbook()
    offline = workbook.active
    offline.title = "Offline"
    offline.append(["Period", "Category", "Value"])
    offline.append(["2022", "Core", 100])
    offline.append(["2024", "Core", 121])
    ecommerce = workbook.create_sheet("Ecommerce")
    ecommerce.append(["Period", "Category", "Value"])
    ecommerce.append(["2022", "Core", 50])
    ecommerce.append(["2024", "Core", 60])
    workbook.save(path)


def test_source_and_scope_checks_capture_hash_sheet_and_range(tmp_path):
    workbook = tmp_path / "ncc-fixture.xlsx"
    make_workbook(workbook)
    selection = SheetSelection(ranges=(("Offline", "A1:C3"), ("Ecommerce", "A1:C3")), include_hidden=True, include_hidden_rows=True)
    result = read_validation_source(workbook, selection)

    report = run_independent_validation(
        workbook,
        selection=selection,
        expected_sha256=result.workbook_sha256,
        expected_ranges=(
            ("Offline", "A1:C3"),
            ("Ecommerce", "A1:C3"),
        ),
        expected_sheets=("Offline", "Ecommerce"),
        expected_periods={"baseline": "2022", "current": "2024"},
    )

    assert report.workbook_sha256 == result.workbook_sha256
    assert [check.status for check in report.checks] == [ReviewSlotStatus.PASS, ReviewSlotStatus.PASS]
    assert {"Offline", "Ecommerce"}.issubset({item.name for item in result.sheets})


def test_independent_validation_reuses_supplied_snapshot(tmp_path, monkeypatch):
    workbook = tmp_path / "ncc-fixture.xlsx"
    make_workbook(workbook)
    selection = SheetSelection(ranges=(("Offline", "A1:C3"),), include_hidden=True, include_hidden_rows=True)
    snapshot = SourceSnapshot.capture(workbook)
    captures = 0
    original_capture = SourceSnapshot.capture

    def capture(*args, **kwargs):
        nonlocal captures
        captures += 1
        return original_capture(*args, **kwargs)

    monkeypatch.setattr(SourceSnapshot, "capture", capture)
    report = run_independent_validation(
        workbook,
        selection=selection,
        snapshot=snapshot,
        expected_sha256=snapshot.sha256,
        expected_ranges=(("Offline", "A1:C3"),),
        expected_sheets=("Offline",),
    )

    assert report.accepted
    assert captures == 0


def test_changed_hash_and_range_fail_without_editing_source(tmp_path):
    workbook = tmp_path / "ncc-fixture.xlsx"
    make_workbook(workbook)
    before = workbook.read_bytes()
    result = read_validation_source(workbook, SheetSelection(ranges=(("Offline", "A1:C3"),)))

    report = run_independent_validation(
        workbook,
        selection=SheetSelection(ranges=(("Offline", "A1:C3"),)),
        expected_sha256="changed-hash",
        expected_ranges=(("Offline", "A1:C9"),),
    )

    assert report.checks[0].status == ReviewSlotStatus.FAIL
    assert report.checks[1].status == ReviewSlotStatus.FAIL
    assert workbook.read_bytes() == before
    assert result.workbook_sha256 != "changed-hash"


def test_independent_arithmetic_detects_denominator_and_value_volume_mixups():
    expected = 121 / 100
    assert growth_rate(100, 121, 2) == pytest.approx(0.1)
    assert reconcile_calculation(check_id="calculation_reconciliation", expected=expected, actual=expected).status == ReviewSlotStatus.PASS
    assert reconcile_calculation(check_id="calculation_reconciliation", expected=expected, actual=121 / 50).status == ReviewSlotStatus.FAIL
    assert reconcile_calculation(check_id="calculation_reconciliation", expected=expected, actual=100 + 21).status == ReviewSlotStatus.FAIL


def test_category_mapping_and_channel_definition_failures_are_explicit():
    assert category_mapping_check("Core", ("Core", "Premium")).status == ReviewSlotStatus.PASS
    invalid = category_mapping_check("Unknown", ("Core", "Premium"))
    assert invalid.status == ReviewSlotStatus.FAIL
    incomparable = channel_comparability_check(
        definitions={
            "offline": {"definition": "sell-in", "period": "2022", "units": "value", "denominator": "stores"},
            "ecommerce": {"definition": "sell-out", "period": "2022", "units": "volume", "denominator": "orders"},
        }
    )
    assert incomparable.status == ReviewSlotStatus.FAIL


def test_planning_threshold_and_missing_feasibility_inputs_remain_honest():
    threshold = planning_threshold_check(initial=100, annual_rate=0.08, periods=2, analyst_actual=116.64)
    assert threshold.status == ReviewSlotStatus.PASS
    assert "planning threshold only" in threshold.interpretation
    missing = conditional_check("decision_challenge", ("margin", "capacity"), interpretation="conditional recommendation")
    assert missing.status == ReviewSlotStatus.PENDING
    assert missing.limitations == ("missing feasibility input: margin", "missing feasibility input: capacity")


def test_selected_checks_omit_irrelevant_categories_and_keep_unavailable_checks_pending(tmp_path):
    workbook = tmp_path / "ncc-fixture.xlsx"
    make_workbook(workbook)

    report = run_independent_validation(
        workbook,
        required_check_ids=("source_fidelity", "decision_challenge"),
        missing_inputs=("margin",),
    )

    assert [check.check_id for check in report.checks] == ["source_fidelity", "decision_challenge"]
    assert report.checks[0].status == ReviewSlotStatus.PASS
    assert report.checks[1].status == ReviewSlotStatus.PENDING
    assert report.checks[1].limitations == ("missing validation input: margin",)
    assert not report.accepted
