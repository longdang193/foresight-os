from pathlib import Path

import pytest

from foresight_os.domain.challenge import ChallengeProposal
from foresight_os.persistence.analysis_store import AnalysisStore
from foresight_os.runtime.group_chat import run_challenge_recommendation
from foresight_os.vertical_slice import run_vertical_slice


ROOT = Path(__file__).parents[1]
WORKBOOK = ROOT / "evaluation" / "cases" / "case-001" / "workbook.csv"


def test_group_chat_terminates_deterministically_after_useful_exchange(tmp_path: Path):
    run_vertical_slice(WORKBOOK, tmp_path / "case-001", human_accept=True)
    state = AnalysisStore(tmp_path / "case-001").load_analysis()
    evidence_id = next(item.id for item in state.evidence if "capacity_index-2030" in item.id)
    proposal = ChallengeProposal(
        agreements=("capacity constraint matters",),
        disagreements=("growth alone is sufficient",),
        proposed_changes=("keep recommendation conditional",),
        evidence_ids=(evidence_id,),
    )

    result = run_challenge_recommendation(state, lambda _state, _previous: proposal, lambda _state, current: current)

    assert result.rounds == 2
    assert result.speakers == ("analyst", "skeptic")
    assert result.proposal == proposal


def test_group_chat_rejects_unsupported_consensus(tmp_path: Path):
    run_vertical_slice(WORKBOOK, tmp_path / "case-001", human_accept=True)
    state = AnalysisStore(tmp_path / "case-001").load_analysis()

    with pytest.raises(ValueError, match="requires evidence"):
        run_challenge_recommendation(
            state,
            lambda _state, _previous: ChallengeProposal(agreements=("consensus",)),
            lambda _state, proposal: proposal,
        )
