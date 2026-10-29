"""对话/事件条件与效果的纯逻辑求值。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from qiqi_town.core.state import GameState, QuestState


@dataclass
class EffectContext:
    hooks: dict[str, Callable[[dict[str, Any]], None]] | None = None


def evaluate_condition(condition: Any, state: GameState) -> bool:
    if condition is None:
        return True
    if not isinstance(condition, dict):
        return False

    if "all" in condition:
        items = condition["all"]
        return isinstance(items, list) and all(evaluate_condition(item, state) for item in items)
    if "any" in condition:
        items = condition["any"]
        return isinstance(items, list) and any(evaluate_condition(item, state) for item in items)
    if "not" in condition:
        return not evaluate_condition(condition["not"], state)

    if "flag" in condition:
        key = str(condition["flag"])
        expected = condition.get("value", True)
        if key not in state.flags:
            return False
        return state.flags.get(key) == expected

    if "day" in condition:
        expected = condition["day"]
        return _matches_any(state.day, expected)

    if "time" in condition:
        expected = condition["time"]
        phases = expected if isinstance(expected, list) else [expected]
        return _phase_of(state.time_minutes) in phases

    if "location" in condition:
        return _matches_any(state.location, condition["location"])

    if "friendship" in condition:
        spec = condition["friendship"]
        if not isinstance(spec, dict) or "npc" not in spec:
            return False
        value = state.friendship.get(str(spec["npc"]), 0)
        if "gte" in spec and value < int(spec["gte"]):
            return False
        if "lte" in spec and value > int(spec["lte"]):
            return False
        return not ("eq" in spec and value != int(spec["eq"]))

    if "sticker" in condition:
        return str(condition["sticker"]) in state.stickers

    if "quest_status" in condition:
        spec = condition["quest_status"]
        if not isinstance(spec, dict) or "quest" not in spec:
            return False
        quest = state.quests.get(str(spec["quest"]))
        return quest is not None and quest.status == spec.get("status")

    return False


def apply_effect(effect: Any, state: GameState, context: EffectContext | None = None) -> bool:
    if not isinstance(effect, dict):
        return False
    kind = str(effect.get("type", ""))

    if kind == "set_flag":
        state.flags[str(effect.get("key"))] = effect.get("value", True)
        return True
    if kind == "add_friendship":
        state.add_friendship(str(effect.get("npc", "")), int(effect.get("amount", 0)))
        return True
    if kind == "give_sticker":
        state.add_sticker(str(effect.get("id", "")))
        return True
    if kind == "add_journal":
        state.add_journal(str(effect.get("id", "")))
        return True
    if kind == "advance_quest":
        quest_id = str(effect.get("quest", ""))
        quest = state.quests.setdefault(quest_id, QuestState())
        quest.step = max(0, int(effect.get("step", quest.step + 1)))
        return True
    if kind == "set_quest_status":
        quest_id = str(effect.get("quest", ""))
        quest = state.quests.setdefault(quest_id, QuestState())
        status = str(effect.get("status", "active"))
        if status in {"locked", "active", "complete"}:
            quest.status = status
            return True
        return False
    if kind == "add_inventory":
        item = str(effect.get("id", ""))
        if item and item not in state.inventory:
            state.inventory.append(item)
        return True
    if kind == "remove_inventory":
        item = str(effect.get("id", ""))
        if item in state.inventory:
            state.inventory.remove(item)
        return True
    if kind == "set_story_complete":
        state.story_complete = True
        return True

    if context and context.hooks and kind in context.hooks:
        context.hooks[kind](effect)
        return True
    return False


def apply_effects(
    effects: Any, state: GameState, context: EffectContext | None = None
) -> list[bool]:
    if not isinstance(effects, list):
        return []
    return [apply_effect(effect, state, context) for effect in effects]


def _matches_any(value: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        return value in expected
    return value == expected


def _phase_of(minutes: int) -> str:
    if minutes < 12 * 60:
        return "morning"
    if minutes < 17 * 60:
        return "afternoon"
    return "dusk"
