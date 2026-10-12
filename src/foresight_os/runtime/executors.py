from dataclasses import dataclass
from typing import Any


@dataclass
class AnalystExecutor:
    client: Any | None = None

    async def execute(self, prompt: str) -> Any:
        if self.client is None:
            return {"role": "analyst", "status": "completed", "prompt": prompt}
        agent = self.client.as_agent(instructions="Return a structured analytical proposal.")
        response = await agent.run(prompt)
        return getattr(response, "value", None) or getattr(response, "text", "")


@dataclass
class ReviewerExecutor:
    client: Any | None = None

    async def execute(self, prompt: str) -> Any:
        if self.client is None:
            return {"role": "reviewer", "status": "completed", "prompt": prompt}
        agent = self.client.as_agent(instructions="Return a structured review of the proposal.")
        response = await agent.run(prompt)
        return getattr(response, "value", None) or getattr(response, "text", "")
