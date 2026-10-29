"""游戏状态：可从存档序列化的纯数据。"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from qiqi_town.config import (
    DAY_END_MINUTE,
    DAY_START_MINUTE,
    DAY_TITLES,
    LOCATION_LABELS,
    SAVE_SCHEMA_VERSION,
)

VALID_LOCATIONS = {
    "town",
    "home",
    "kindergarten",
    "library",
    "park",
    "playground",
    "mountain",
    "square",
}


@dataclass
class PlayerState:
    x: float = 0.0
    y: float = 0.0
    facing: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {"x": float(self.x), "y": float(self.y), "facing": float(self.facing)}

    @classmethod
    def from_dict(cls, raw: Any) -> PlayerState:
        if not isinstance(raw, dict):
            return cls()
        return cls(
            x=_finite_float(raw.get("x"), 0.0),
            y=_finite_float(raw.get("y"), 0.0),
            facing=_finite_float(raw.get("facing"), 0.0),
        )

    def is_valid(self) -> bool:
        return all(math.isfinite(v) for v in (self.x, self.y, self.facing))


@dataclass
class QuestState:
    step: int = 0
    status: str = "active"

    def to_dict(self) -> dict[str, Any]:
        return {"step": int(self.step), "status": self.status}

    @classmethod
    def from_dict(cls, raw: Any) -> QuestState:
        if not isinstance(raw, dict):
            return cls()
        status = raw.get("status", "active")
        if status not in {"locked", "active", "complete"}:
            status = "active"
        return cls(step=max(0, _safe_int(raw.get("step"), 0)), status=status)


@dataclass
class MinigameState:
    completed: bool = False
    best: int = 0
    plays: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {"completed": bool(self.completed), "best": int(self.best), "plays": int(self.plays)}

    @classmethod
    def from_dict(cls, raw: Any) -> MinigameState:
        if not isinstance(raw, dict):
            return cls()
        return cls(
            completed=bool(raw.get("completed", False)),
            best=max(0, _safe_int(raw.get("best"), 0)),
            plays=max(0, _safe_int(raw.get("plays"), 0)),
        )


@dataclass
class GameState:
    schema_version: int = SAVE_SCHEMA_VERSION
    day: int = 1
    time_minutes: int = DAY_START_MINUTE
    location: str = "home"
    spawn_id: str = "home_start"
    player: PlayerState = field(default_factory=PlayerState)
    flags: dict[str, Any] = field(default_factory=dict)
    quests: dict[str, QuestState] = field(default_factory=dict)
    minigames: dict[str, MinigameState] = field(default_factory=dict)
    inventory: list[str] = field(default_factory=list)
    stickers: list[str] = field(default_factory=list)
    friendship: dict[str, int] = field(default_factory=dict)
    journal_entries: list[str] = field(default_factory=list)
    seen_dialogues: list[str] = field(default_factory=list)
    playtime_seconds: float = 0.0
    story_complete: bool = False

    @classmethod
    def new_game(cls) -> GameState:
        return cls(
            day=1,
            time_minutes=DAY_START_MINUTE,
            location="home",
            spawn_id="home_start",
            player=PlayerState(x=0.0, y=-2.0, facing=0.0),
            quests={"day1_main": QuestState(step=0, status="active")},
        )

    @property
    def location_label(self) -> str:
        return LOCATION_LABELS.get(self.location, self.location)

    @property
    def quest_title(self) -> str:
        return DAY_TITLES.get(self.day, "")

    @property
    def day_title(self) -> str:
        return DAY_TITLES.get(self.day, "")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": int(self.schema_version),
            "day": int(self.day),
            "time_minutes": int(self.time_minutes),
            "location": self.location,
            "spawn_id": self.spawn_id,
            "player": self.player.to_dict(),
            "flags": dict(self.flags),
            "quests": {k: v.to_dict() for k, v in self.quests.items()},
            "minigames": {k: v.to_dict() for k, v in self.minigames.items()},
            "inventory": list(self.inventory),
            "stickers": list(self.stickers),
            "friendship": {k: int(v) for k, v in self.friendship.items()},
            "journal_entries": list(self.journal_entries),
            "seen_dialogues": list(self.seen_dialogues),
            "playtime_seconds": round(float(self.playtime_seconds), 2),
            "story_complete": bool(self.story_complete),
        }

    @classmethod
    def from_dict(cls, raw: Any) -> GameState:
        if not isinstance(raw, dict):
            raise ValueError("state 必须是一个对象")
        state = cls()
        state.schema_version = _safe_int(raw.get("schema_version"), SAVE_SCHEMA_VERSION)
        state.day = min(5, max(1, _safe_int(raw.get("day"), 1)))
        state.time_minutes = _clamp_int(
            raw.get("time_minutes"), DAY_START_MINUTE, DAY_END_MINUTE, DAY_START_MINUTE
        )
        location = raw.get("location")
        state.location = location if location in VALID_LOCATIONS else "home"
        state.spawn_id = str(raw.get("spawn_id") or "home_start")
        state.player = PlayerState.from_dict(raw.get("player"))
        if not state.player.is_valid():
            state.player = PlayerState()
        state.flags = _dict_any(raw.get("flags"))
        state.quests = {
            str(k): QuestState.from_dict(v) for k, v in _dict_any(raw.get("quests")).items()
        }
        state.minigames = {
            str(k): MinigameState.from_dict(v) for k, v in _dict_any(raw.get("minigames")).items()
        }
        state.inventory = _str_list(raw.get("inventory"))
        state.stickers = _str_list(raw.get("stickers"))
        state.friendship = {
            str(k): max(0, min(5, _safe_int(v, 0)))
            for k, v in _dict_any(raw.get("friendship")).items()
        }
        state.journal_entries = _str_list(raw.get("journal_entries"))
        state.seen_dialogues = _str_list(raw.get("seen_dialogues"))
        state.playtime_seconds = max(0.0, _finite_float(raw.get("playtime_seconds"), 0.0))
        state.story_complete = bool(raw.get("story_complete", False))
        return state

    def add_sticker(self, sticker_id: str) -> bool:
        if not sticker_id or sticker_id in self.stickers:
            return False
        self.stickers.append(sticker_id)
        return True

    def add_journal(self, entry_id: str) -> bool:
        if not entry_id or entry_id in self.journal_entries:
            return False
        self.journal_entries.append(entry_id)
        return True

    def add_friendship(self, npc: str, amount: int) -> None:
        current = self.friendship.get(npc, 0)
        self.friendship[npc] = max(0, min(5, current + int(amount)))

    def mark_dialogue_seen(self, dialogue_id: str) -> None:
        if dialogue_id and dialogue_id not in self.seen_dialogues:
            self.seen_dialogues.append(dialogue_id)


def _dict_any(raw: Any) -> dict[str, Any]:
    return dict(raw) if isinstance(raw, dict) else {}


def _str_list(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(v) for v in raw if isinstance(v, (str, int))]


def _safe_int(raw: Any, default: int) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _clamp_int(raw: Any, low: int, high: int, default: int) -> int:
    return max(low, min(high, _safe_int(raw, default)))


def _finite_float(raw: Any, default: float) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if math.isfinite(value) else default
