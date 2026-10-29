"""接花瓣 / 喂小鸭：点击移动中的目标。"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class CatchGame:
    target: int = 6
    catches: int = 0
    x: float = 0.0
    y: float = 0.0
    move_timer: float = 0.0
    move_interval: float = 1.0
    rng: random.Random = field(default_factory=random.Random)

    @property
    def finished(self) -> bool:
        return self.catches >= self.target

    def update(self, dt: float) -> None:
        if self.finished:
            return
        self.move_timer -= dt
        if self.move_timer <= 0:
            self.move_timer = self.move_interval
            self.x = self.rng.uniform(-0.55, 0.55)
            self.y = self.rng.uniform(-0.15, 0.30)

    def catch(self) -> str:
        if self.finished:
            return "finished"
        self.catches += 1
        self.move_timer = 0.0
        return "caught"
