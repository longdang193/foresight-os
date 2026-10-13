from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from evaluation.probes.run_full_pipeline_exercise import pipeline_passes


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
