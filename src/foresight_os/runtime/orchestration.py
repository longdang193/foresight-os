from dataclasses import dataclass, field
from datetime import datetime, timezone
import asyncio
from threading import Lock

from foresight_os.runtime.workflow import run_recipe, run_recipe_async
from foresight_os.runtime.execution_gate import ExecutionGate, execute_approved_investigation


class RunControlError(RuntimeError):
    pass


@dataclass(frozen=True)
class RunControlEvent:
    run_id: str
    event: str
    at: str
    detail: str = ""


@dataclass
class RunControl:
    run_id: str
    state: str = "running"
    events: list[RunControlEvent] = field(default_factory=list)
    _resume: asyncio.Event = field(default_factory=asyncio.Event, repr=False)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def __post_init__(self) -> None:
        self._resume.set()
        self.record("started")

    def record(self, event: str, detail: str = "") -> None:
        with self._lock:
            self.events.append(RunControlEvent(self.run_id, event, datetime.now(timezone.utc).isoformat(), detail))

    def request_pause(self) -> None:
        with self._lock:
            self.state = "pause_requested"
            self._resume.clear()
        self.record("pause_requested")

    def request_resume(self) -> None:
        with self._lock:
            self.state = "running"
            self._resume.set()
        self.record("resumed")

    def request_cancel(self) -> None:
        with self._lock:
            self.state = "cancel_requested"
            self._resume.set()
        self.record("cancel_requested")

    async def before_stage(self) -> None:
        while True:
            with self._lock:
                state = self.state
            if state == "cancel_requested":
                with self._lock:
                    self.state = "canceled"
                self.record("canceled")
                raise RunControlError("run canceled before stage dispatch")
            if state == "pause_requested":
                self.record("paused")
                await self._resume.wait()
                continue
            return


_RUN_CONTROLS: dict[str, RunControl] = {}


def register_run_control(control: RunControl) -> None:
    _RUN_CONTROLS[control.run_id] = control


def get_run_control(run_id: str) -> RunControl | None:
    return _RUN_CONTROLS.get(run_id)


def unregister_run_control(run_id: str) -> None:
    _RUN_CONTROLS.pop(run_id, None)

__all__ = [
    "ExecutionGate",
    "RunControl",
    "RunControlError",
    "RunControlEvent",
    "execute_approved_investigation",
    "get_run_control",
    "register_run_control",
    "run_recipe",
    "run_recipe_async",
    "unregister_run_control",
]
