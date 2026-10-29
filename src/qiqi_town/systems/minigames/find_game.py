"""小镇 3D 找一找：在镇子里找到闪光的小东西。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FindGame:
    targets: dict[str, tuple[float, float, float]]
    labels: dict[str, str] = field(default_factory=dict)
    found: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.active = False

    @property
    def total(self) -> int:
        return len(self.targets)

    @property
    def finished(self) -> bool:
        return len(self.found) >= self.total

    def start(self) -> None:
        self.active = True
        self.found.clear()

    def collect(self, target_id: str) -> str:
        if not self.active or self.finished:
            return "inactive"
        if target_id not in self.targets or target_id in self.found:
            return "invalid"
        self.found.add(target_id)
        return "complete" if self.finished else "collected"

    def stop(self) -> None:
        self.active = False


def default_find_game() -> FindGame:
    return FindGame(
        targets={
            "fountain": (2.4, 2.4, 0.8),
            "park": (13.8, -12.2, 0.8),
            "playground": (-19.0, -11.8, 1.3),
            "library": (-12.0, -0.5, 0.8),
            "trail": (0.0, 22.0, 3.2),
        },
        labels={
            "fountain": "喷泉边的闪光",
            "park": "池塘边的闪光",
            "playground": "滑梯旁的闪光",
            "library": "图书馆门口的闪光",
            "trail": "山道上的闪光",
        },
    )
