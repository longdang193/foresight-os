from dataclasses import dataclass
from typing import Callable

from foresight_os.domain.challenge import ChallengeProposal
from foresight_os.domain.models import AnalysisState


@dataclass(frozen=True)
class GroupChatResult:
    proposal: ChallengeProposal
    rounds: int
    speakers: tuple[str, ...]
    terminated: bool


def run_challenge_recommendation(
    state: AnalysisState,
    analyst: Callable[[AnalysisState, ChallengeProposal | None], ChallengeProposal],
    skeptic: Callable[[AnalysisState, ChallengeProposal], ChallengeProposal],
    max_rounds: int = 4,
) -> GroupChatResult:
    if max_rounds < 1:
        raise ValueError("max_rounds must be positive")
    proposal: ChallengeProposal | None = None
    speakers: list[str] = []
    for round_number in range(max_rounds):
        if round_number % 2 == 0:
            next_proposal = analyst(state, proposal)
            speaker = "analyst"
        else:
            next_proposal = skeptic(state, proposal or ChallengeProposal())
            speaker = "skeptic"
        speakers.append(speaker)
        if proposal is not None and next_proposal == proposal:
            proposal.validate({item.id for item in state.evidence})
            return GroupChatResult(proposal, round_number + 1, tuple(speakers), True)
        proposal = next_proposal
    assert proposal is not None
    proposal.validate({item.id for item in state.evidence})
    return GroupChatResult(proposal, max_rounds, tuple(speakers), True)
