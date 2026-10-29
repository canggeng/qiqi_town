"""可交互物定义。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Interactable:
    id: str
    label: str
    world_pos: tuple[float, float, float]
    approach_pos: tuple[float, float]
    on_interact: Callable[[], None]
    radius: float = 2.3
    kind: str = "npc"
    data: dict[str, Any] | None = None

    @property
    def ground_pos(self) -> tuple[float, float]:
        return (self.world_pos[0], self.world_pos[1])
