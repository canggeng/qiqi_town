"""对话运行器：节点、条件、选项、效果。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from qiqi_town.core.conditions import EffectContext, apply_effects, evaluate_condition
from qiqi_town.core.state import GameState


@dataclass
class DialogueChoice:
    text: str
    next: str | None = None
    effects: list[dict[str, Any]] | None = None


@dataclass
class DialogueNode:
    id: str
    speaker: str
    text: str
    next: str | None = None
    choices: list[DialogueChoice] | None = None
    effects: list[dict[str, Any]] | None = None
    condition: dict[str, Any] | None = None
    portrait: str = "happy"


class DialogueRunner:
    def __init__(
        self,
        nodes: dict[str, DialogueNode],
        state: GameState,
        *,
        effect_context: EffectContext | None = None,
        on_change: Callable[[], None] | None = None,
    ) -> None:
        self.nodes = nodes
        self.state = state
        self.effect_context = effect_context or EffectContext()
        self.on_change = on_change
        self.current: DialogueNode | None = None
        self.finished = True
        self._start_id: str | None = None

    @classmethod
    def from_data(
        cls,
        raw: dict[str, Any],
        state: GameState,
        *,
        effect_context: EffectContext | None = None,
        on_change: Callable[[], None] | None = None,
    ) -> DialogueRunner:
        nodes: dict[str, DialogueNode] = {}
        for node_id, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            choices = None
            if isinstance(entry.get("choices"), list):
                choices = [
                    DialogueChoice(
                        text=str(choice.get("text", "")),
                        next=choice.get("next"),
                        effects=choice.get("effects"),
                    )
                    for choice in entry["choices"]
                    if isinstance(choice, dict)
                ]
            nodes[str(node_id)] = DialogueNode(
                id=str(node_id),
                speaker=str(entry.get("speaker", "")),
                text=str(entry.get("text", "")),
                next=entry.get("next"),
                choices=choices,
                effects=entry.get("effects"),
                condition=entry.get("condition"),
                portrait=str(entry.get("portrait", "happy")),
            )
        return cls(nodes, state, effect_context=effect_context, on_change=on_change)

    @property
    def waiting_for_choice(self) -> bool:
        return bool(self.current and self.current.choices)

    def start(self, node_id: str) -> bool:
        node = self.nodes.get(node_id)
        if node is None:
            return False
        self.finished = False
        self._start_id = node_id
        self._enter(node)
        return not self.finished

    def advance(self) -> bool:
        if self.finished or self.current is None:
            return False
        if self.current.choices:
            return False
        if self.current.next:
            self._enter_id(self.current.next)
        else:
            self._finish()
        return not self.finished

    def choose(self, index: int) -> bool:
        if self.finished or self.current is None or not self.current.choices:
            return False
        if not 0 <= index < len(self.current.choices):
            return False
        choice = self.current.choices[index]
        apply_effects(choice.effects or [], self.state, self.effect_context)
        if choice.next:
            self._enter_id(choice.next)
        else:
            self._finish()
        return not self.finished

    def _enter_id(self, node_id: str) -> None:
        if node_id not in self.nodes:
            self._finish()
            return
        self._enter(self.nodes[node_id])

    def _enter(self, node: DialogueNode) -> None:
        if not evaluate_condition(node.condition, self.state):
            if node.next:
                self._enter_id(node.next)
            else:
                self._finish()
            return
        self.current = node
        self.state.mark_dialogue_seen(node.id)
        apply_effects(node.effects or [], self.state, self.effect_context)
        if self.on_change:
            self.on_change()

    def _finish(self) -> None:
        self.finished = True
        self.current = None
        if self.on_change:
            self.on_change()
