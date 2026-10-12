from dataclasses import dataclass


@dataclass
class BudgetState:
    max_agent_steps: int
    max_correction_rounds: int
    max_total_agent_calls: int
    agent_steps: int = 0
    correction_rounds: int = 0
    total_agent_calls: int = 0

    def call(self) -> bool:
        if self.total_agent_calls >= self.max_total_agent_calls:
            return False
        self.total_agent_calls += 1
        return True

    def step(self) -> bool:
        if self.agent_steps >= self.max_agent_steps:
            return False
        self.agent_steps += 1
        return True

    def correct(self) -> bool:
        if self.correction_rounds >= self.max_correction_rounds:
            return False
        self.correction_rounds += 1
        return True

    @property
    def exhausted(self) -> bool:
        return (
            self.agent_steps >= self.max_agent_steps
            or self.total_agent_calls >= self.max_total_agent_calls
            or self.correction_rounds >= self.max_correction_rounds
        )
