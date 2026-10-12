from dataclasses import dataclass


@dataclass
class BudgetState:
    max_agent_steps: int
    max_correction_rounds: int
    max_total_agent_calls: int
    agent_steps: int = 0
    correction_rounds: int = 0
    total_agent_calls: int = 0
    max_branches: int | None = None
    max_handoffs: int | None = None
    max_rounds: int | None = None
    max_tool_calls: int | None = None
    branches: int = 0
    handoffs: int = 0
    rounds: int = 0
    tool_calls: int = 0

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

    def reserve(self, *, branches: int = 0, handoffs: int = 0, rounds: int = 0, tool_calls: int = 0) -> bool:
        if self.max_branches is not None and self.branches + branches > self.max_branches:
            return False
        if self.max_handoffs is not None and self.handoffs + handoffs > self.max_handoffs:
            return False
        if self.max_rounds is not None and self.rounds + rounds > self.max_rounds:
            return False
        if self.max_tool_calls is not None and self.tool_calls + tool_calls > self.max_tool_calls:
            return False
        self.branches += branches
        self.handoffs += handoffs
        self.rounds += rounds
        self.tool_calls += tool_calls
        return True

    @property
    def exhausted(self) -> bool:
        return (
            self.agent_steps >= self.max_agent_steps
            or self.total_agent_calls >= self.max_total_agent_calls
            or self.correction_rounds >= self.max_correction_rounds
        )
