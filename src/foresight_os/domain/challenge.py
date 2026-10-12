from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChallengeProposal:
    agreements: tuple[str, ...] = ()
    disagreements: tuple[str, ...] = ()
    counterevidence: tuple[str, ...] = ()
    unsupported_assumptions: tuple[str, ...] = ()
    proposed_changes: tuple[str, ...] = ()
    unresolved_questions: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def validate(self, known_evidence_ids: set[str]) -> None:
        if not self.evidence_ids:
            raise ValueError("challenge proposal requires evidence")
        if not set(self.evidence_ids).issubset(known_evidence_ids):
            raise ValueError("challenge proposal references unknown evidence")
        if self.unsupported_assumptions and not self.unresolved_questions:
            raise ValueError("unsupported assumptions require unresolved questions")
