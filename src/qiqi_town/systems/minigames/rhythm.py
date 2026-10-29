"""秋千节奏小游戏：在指针进入亮色区域时点击。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RhythmGame:
    zone_start: float = 0.55
    zone_end: float = 0.75
    speed: float = 0.6
    position: float = 0.1
    direction: float = 1.0
    hits: int = 0
    misses: int = 0
    target_hits: int = 5

    def update(self, dt: float) -> None:
        if self.finished:
            return
        self.position += self.direction * self.speed * max(0.0, dt)
        if self.position >= 1.0:
            self.position = 2.0 - self.position
            self.direction = -1.0
        elif self.position <= 0.0:
            self.position = -self.position
            self.direction = 1.0

    @property
    def in_zone(self) -> bool:
        return self.zone_start <= self.position <= self.zone_end

    @property
    def finished(self) -> bool:
        return self.hits >= self.target_hits

    def hit(self) -> str:
        if self.finished:
            return "finished"
        if self.in_zone:
            self.hits += 1
            return "hit"
        self.misses += 1
        return "miss"
