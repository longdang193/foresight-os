from dataclasses import dataclass
import inspect
from typing import Any, Mapping

from foresight_os.runtime.participants import AgentFactory, ParticipantConfig


async def _close_agent(agent: object) -> None:
    close = getattr(agent, "close", None)
    if close is None:
        return
    result = close()
    if inspect.isawaitable(result):
        await result


@dataclass
class AnalystExecutor:
    client: Any | None = None
    factory: AgentFactory | None = None
    participant: ParticipantConfig | None = None
    run_context: Mapping[str, Any] | None = None

    async def execute(self, prompt: str) -> Any:
        if self.client is None:
            return {"role": "analyst", "status": "completed", "prompt": prompt}
        factory = self.factory or AgentFactory(self.client)
        participant = self.participant or ParticipantConfig("analyst", "analyst", "structured analytical proposal")
        agent = factory.create(participant, self.run_context or {})
        response = await agent.run(prompt)
        return getattr(response, "value", None) or getattr(response, "text", "")


@dataclass
class ReviewerExecutor:
    client: Any | None = None
    factory: AgentFactory | None = None
    participant: ParticipantConfig | None = None
    run_context: Mapping[str, Any] | None = None

    async def execute(self, prompt: str) -> Any:
        if self.client is None:
            return {"role": "reviewer", "status": "completed", "prompt": prompt}
        factory = self.factory or AgentFactory(self.client)
        participant = self.participant or ParticipantConfig("reviewer", "reviewer", "structured review of the proposal")
        agent = factory.create(participant, self.run_context or {})
        response = await agent.run(prompt)
        return getattr(response, "value", None) or getattr(response, "text", "")
