"""形状配对小游戏的纯逻辑。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ShapeItem:
    id: str
    label: str
    slot: str
    color: tuple[float, float, float, float]


@dataclass(frozen=True)
class ShapeSlot:
    id: str
    label: str


@dataclass
class ShapeMatchGame:
    items: list[ShapeItem]
    slots: list[ShapeSlot]
    selected: str | None = None
    matched: set[str] = field(default_factory=set)
    mistakes: int = 0

    @property
    def finished(self) -> bool:
        return len(self.matched) == len(self.items)

    def select_item(self, item_id: str) -> bool:
        if self.finished or item_id in self.matched:
            return False
        if item_id not in {item.id for item in self.items}:
            return False
        self.selected = item_id
        return True

    def choose_slot(self, slot_id: str) -> str:
        if self.finished or self.selected is None:
            return "ignored"
        item = next((item for item in self.items if item.id == self.selected), None)
        if item is None:
            return "ignored"
        if item.slot == slot_id:
            self.matched.add(item.id)
            self.selected = None
            return "correct"
        self.mistakes += 1
        return "wrong"


def default_shape_game() -> ShapeMatchGame:
    return ShapeMatchGame(
        items=[
            ShapeItem("red_circle", "红色圆形", "circle", (0.92, 0.35, 0.32, 1.0)),
            ShapeItem("blue_square", "蓝色方形", "square", (0.35, 0.62, 0.86, 1.0)),
            ShapeItem("yellow_triangle", "黄色三角", "triangle", (0.96, 0.78, 0.35, 1.0)),
        ],
        slots=[
            ShapeSlot("circle", "圆形的家"),
            ShapeSlot("square", "方形的家"),
            ShapeSlot("triangle", "三角的家"),
        ],
    )
