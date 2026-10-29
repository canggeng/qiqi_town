"""山路记忆：记住颜色顺序并重复。"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class MemoryGame:
    sequence: list[int] = field(default_factory=list)
    input: list[int] = field(default_factory=list)
    reveal_time: float = 2.2
    timer: float = 2.2
    mistakes: int = 0
    started: bool = True

    def __post_init__(self) -> None:
        if not self.sequence:
            self.sequence = [2, 0, 3, 1]

    @property
    def showing(self) -> bool:
        return self.timer > 0

    @property
    def finished(self) -> bool:
        return len(self.input) >= len(self.sequence) and self.input == self.sequence

    def update(self, dt: float) -> None:
        if self.timer > 0:
            self.timer = max(0.0, self.timer - dt)

    def press(self, index: int) -> str:
        if self.showing:
            return "wait"
        if self.finished:
            return "finished"
        if not 0 <= index < 4:
            return "ignored"
        expected = self.sequence[len(self.input)]
        if index == expected:
            self.input.append(index)
            return "correct" if not self.finished else "finished"
        self.mistakes += 1
        self.input.clear()
        return "wrong"


def random_memory_game(rng: random.Random | None = None) -> MemoryGame:
    rng = rng or random.Random()
    return MemoryGame(sequence=[rng.randrange(4) for _ in range(4)])
