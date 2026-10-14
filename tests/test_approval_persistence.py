from datetime import datetime, timezone

import pytest

from foresight_os.artifacts.approval import build_approval_package
from foresight_os.controller.proposal import build_execution_recipe
from foresight_os.domain.approval import AdaptationEnvelope, ApprovalRecord, ApprovalStatus
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.persistence.ids import canonical_json_hash
from foresight_os.wayfinding import create_work_brief


def test_approval_round_trip_and_stale_display_rejection(tmp_path):
    brief = create_work_brief("Question", investigation_id="persist")
    recipe = build_execution_recipe(brief).recipe
    store = AnalysisStore(tmp_path / "persist")
    store.save_brief(brief)
    store.save_recipe(recipe)
    package = build_approval_package(brief, recipe, AdaptationEnvelope())
    record = ApprovalRecord(
        brief.investigation_id,
        ApprovalStatus.APPROVED,
        package.projection,
        package.fingerprint,
        package.fingerprint,
        canonical_json_hash(recipe.to_dict()),
        "local_cli",
        datetime.now(timezone.utc).isoformat(),
    )
    store.save_execution_approval(record)
    assert store.load_execution_approval() == record
    with pytest.raises(ValueError):
        ApprovalRecord(
            brief.investigation_id,
            ApprovalStatus.APPROVED,
            package.projection,
            package.fingerprint,
            "stale",
            canonical_json_hash(recipe.to_dict()),
            "local_cli",
            "now",
        )
