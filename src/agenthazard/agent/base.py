from typing import Protocol

from ..models import EvalResult, Task, UIElement
from .utils import JSONAction


class Agent(Protocol):
    def generate_prompt(self, goal: str, ui_elements: list[UIElement]) -> str: ...
    def parse_output(
        self,
        output: str,
        elements: list[UIElement],
        task: Task,
        misleading_action: str | None = None,
        **metadata,
    ) -> tuple[str, JSONAction, EvalResult]: ...
