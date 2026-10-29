"""每天 3 个小游戏的排期与奖励。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GameSlot:
    id: str
    day: int
    kind: str
    title: str
    location: str
    sticker: str
    journal: str
    friend: str


GAME_SLOTS: tuple[GameSlot, ...] = (
    # 第 1 天
    GameSlot("d1_shape", 1, "shape", "形状小管家", "幼儿园", "sticker_shapes", "journal_shapes", "lin"),
    GameSlot("d1_catch", 1, "catch", "接住花瓣", "公园", "sticker_ducks", "journal_ducks", "su"),
    GameSlot("d1_rhythm", 1, "rhythm", "秋千节奏", "游乐场", "sticker_swing", "journal_swing", "chen"),
    # 第 2 天
    GameSlot("d2_story", 2, "story", "故事排排队", "图书馆", "sticker_story", "journal_story", "gu"),
    GameSlot("d2_find", 2, "find", "小镇找一找", "中心广场", "sticker_find", "journal_find", "su"),
    GameSlot("d2_rhythm", 2, "rhythm", "铃铛节奏", "游乐场", "sticker_swing", "journal_swing", "chen"),
    # 第 3 天
    GameSlot("d3_shape", 3, "shape", "颜色分类", "幼儿园", "sticker_shapes", "journal_shapes", "lin"),
    GameSlot("d3_catch", 3, "catch", "喂小鸭", "公园", "sticker_ducks", "journal_ducks", "su"),
    GameSlot("d3_memory", 3, "memory", "山路记忆", "青禾山", "sticker_memory", "journal_memory", "zhou"),
    # 第 4 天
    GameSlot("d4_rhythm", 4, "rhythm", "秋千节奏·进阶", "游乐场", "sticker_swing", "journal_swing", "chen"),
    GameSlot("d4_find", 4, "find", "找发夹", "中心广场", "sticker_find", "journal_find", "xiaoman"),
    GameSlot("d4_story", 4, "story", "朋友的故事", "图书馆", "sticker_story", "journal_story", "gu"),
    # 第 5 天
    GameSlot("d5_memory", 5, "memory", "山路记忆·最终", "青禾山", "sticker_memory", "journal_memory", "zhou"),
    GameSlot("d5_catch", 5, "catch", "接萤火虫", "公园", "sticker_firefly", "journal_firefly", "su"),
    GameSlot("d5_story", 5, "story", "灯会故事", "图书馆", "sticker_lantern", "journal_lantern", "gu"),
)

_BY_ID = {slot.id: slot for slot in GAME_SLOTS}


def slots_for_day(day: int) -> tuple[GameSlot, ...]:
    return tuple(slot for slot in GAME_SLOTS if slot.day == day)


def slot_for(day: int, kind: str) -> GameSlot | None:
    return next((slot for slot in GAME_SLOTS if slot.day == day and slot.kind == kind), None)


def slot_by_id(slot_id: str) -> GameSlot | None:
    return _BY_ID.get(slot_id)
