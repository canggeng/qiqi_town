"""故事排序小游戏：点击两张卡交换位置，排成正确顺序。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StoryOrderGame:
    cards: list[str]
    target_order: list[int]
    order: list[int] = field(default_factory=list)
    selected: int | None = None

    def __post_init__(self) -> None:
        if not self.order:
            self.order = [2, 0, 1] if len(self.cards) == 3 else list(reversed(range(len(self.cards))))

    @property
    def finished(self) -> bool:
        return self.order == self.target_order

    def label_at(self, index: int) -> str:
        return self.cards[self.order[index]]

    def select(self, index: int) -> str:
        if self.finished:
            return "finished"
        if not 0 <= index < len(self.order):
            return "ignored"
        if self.selected is None:
            self.selected = index
            return "selected"
        if self.selected == index:
            self.selected = None
            return "deselected"
        a, b = self.selected, index
        self.order[a], self.order[b] = self.order[b], self.order[a]
        self.selected = None
        return "swapped"


def default_story_game() -> StoryOrderGame:
    return StoryOrderGame(
        cards=["一颗小种子", "一株小芽", "一朵小花"],
        target_order=[0, 1, 2],
    )
