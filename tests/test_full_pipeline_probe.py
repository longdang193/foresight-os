from __future__ import annotations

import sys
from types import SimpleNamespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from evaluation.probes.run_full_pipeline_exercise import _selection_for_table, pipeline_passes


def test_full_pipeline_probe_uses_ranges_for_implicit_used_range_tables():
    table = SimpleNamespace(sheet="Sales_History", name="A1:K124", source_range="A1:K124")

    selection = _selection_for_table(table)

    assert selection.ranges == (("Sales_History", "A1:K124"),)
    assert selection.tables == ()


def test_full_pipeline_probe_preserves_named_table_selection():
    table = SimpleNamespace(sheet="Demand", name="DemandTable", source_range="A1:B3")

    selection = _selection_for_table(table)

    assert selection.tables == (("Demand", "DemandTable"),)
    assert selection.ranges == ()


def test_full_pipeline_probe_requires_one_current_accepted_finding_view_per_case():
    report = {
        "validator_denied": True,
        "cases": [
            {
                "status": "accepted",
                "review_accepted": True,
                "finding_view_count": 0,
                "finding_view_statuses": [],
                "finding_view_accepted": [],
                "review_record_count": 1,
                "source_unchanged": True,
                "failure": None,
            }
        ],
    }

    assert pipeline_passes(report) is False
