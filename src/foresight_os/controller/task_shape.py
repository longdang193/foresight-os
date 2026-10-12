from dataclasses import dataclass


@dataclass(frozen=True)
class TaskShape:
    ordered_dependencies: bool = False
    independent_subtasks: bool = False
    dynamic_specialist_routing: bool = False
    interactive_deliberation: bool = False
    review_required: bool = False

    def __post_init__(self) -> None:
        if not all(isinstance(value, bool) for value in self.__dict__.values()):
            raise ValueError("task-shape signals must be boolean")
