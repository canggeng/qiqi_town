"""日记界面：今日目标、贴纸、居民关系。"""

from __future__ import annotations

import json

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGui import DirectButton, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, TransparencyAttrib

from qiqi_town.config import DAY_TITLES
from qiqi_town.paths import data_dir
from qiqi_town.systems.daily_content import slots_for_day
from qiqi_town.ui.roundrect import round_button, round_widget

STICKER_SLOTS = 20


def load_stickers() -> list[dict]:
    path = data_dir() / "stickers.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return raw if isinstance(raw, list) else []


class DiaryUi:
    def __init__(self, app) -> None:
        self.app = app
        self.font = app.font
        self.root = app.aspect2d.attachNewNode("diary_ui")
        self.root.hide()
        self.stickers = load_stickers()
        self._dim = DirectFrame(
            parent=self.root,
            frameColor=(0.06, 0.05, 0.045, 0.62),
            frameSize=(-2.2, 2.2, -1.6, 1.6),
            relief=DGG.FLAT,
        )
        self._dim.setTransparency(TransparencyAttrib.MAlpha)
        self._panel = DirectFrame(
            parent=self.root,
            frameColor=(0.99, 0.96, 0.88, 0.98),
            frameSize=(-1.26, 1.26, -0.9, 0.9),
            relief=DGG.FLAT,
        )
        self._panel.setTransparency(TransparencyAttrib.MAlpha)
        round_widget(self._panel, radius=0.05)
        self.title = self._label("淇淇的日记", (0, 0.80), 0.07, TextNode.ACenter)
        self.day_title = self._label("", (-1.16, 0.64), 0.045)
        self.quest_text = self._label("", (-1.16, 0.55), 0.032)
        self.game_text = self._label("", (-1.16, 0.42), 0.030)
        self.friend_text = self._label("", (-1.16, 0.14), 0.030)
        self.sticker_title = self._label("回忆贴纸", (0.05, 0.64), 0.045)
        self.sticker_count = self._label("", (1.16, 0.64), 0.032, TextNode.ARight)
        self.sticker_buttons: list[OnscreenText] = []
        self._build_sticker_slots()
        self._label(
            "每个小游戏和每一段故事，都会变成一张回忆贴纸。",
            (-1.16, -0.81),
            0.026,
            TextNode.ALeft,
            fg=(0.45, 0.40, 0.34, 1.0),
        )
        back = DirectButton(
            parent=self.root,
            text="返回",
            text_font=self.font,
            text_fg=(0.18, 0.16, 0.15, 1.0),
            text_scale=0.038,
            frameColor=(0.93, 0.75, 0.51, 0.98),
            frameSize=(-0.22, 0.22, -0.06, 0.06),
            pos=(1.02, 0, -0.81),
            relief=DGG.FLAT,
            command=self._close,
        )
        back.setTransparency(TransparencyAttrib.MAlpha)
        round_button(back, radius=0.03)

    def _close(self) -> None:
        self.app.close_diary()

    def _label(
        self,
        text: str,
        pos: tuple[float, float],
        scale: float,
        align=TextNode.ALeft,
        *,
        fg=(0.18, 0.16, 0.15, 1.0),
    ) -> OnscreenText:
        return OnscreenText(
            parent=self.root,
            text=text,
            font=self.font,
            pos=pos,
            scale=scale,
            align=align,
            fg=fg,
            shadow=(1.0, 0.98, 0.9, 0.5),
            mayChange=True,
        )

    def _build_sticker_slots(self) -> None:
        x0, y0 = -0.05, 0.49
        for index in range(STICKER_SLOTS):
            col = index % 4
            row = index // 4
            label = OnscreenText(
                parent=self.root,
                text="？",
                font=self.font,
                pos=(x0 + col * 0.31, y0 - row * 0.20),
                scale=0.026,
                align=TextNode.ACenter,
                fg=(0.55, 0.50, 0.44, 0.9),
                mayChange=True,
            )
            self.sticker_buttons.append(label)

    def show(self) -> None:
        self.root.show()
        self.refresh()

    def hide(self) -> None:
        self.root.hide()

    def refresh(self) -> None:
        state = self.app.state
        day = state.day
        self.day_title["text"] = f"第 {day} 天 · {DAY_TITLES.get(day, '')}"
        quest = state.quests.get(f"day{day}_main")
        if quest is None:
            quest_text = "今天还没有新的任务。"
        elif quest.status == "complete":
            quest_text = "今日主线：已完成"
        else:
            quest_text = "今日主线：进行中"
        self.quest_text["text"] = quest_text
        games = slots_for_day(day)
        lines = ["今日小游戏："]
        for slot in games:
            done = state.minigames.get(slot.id)
            lines.append(f"{slot.title}（{'已完成' if done and done.completed else '未完成'}）")
        self.game_text["text"] = "\n".join(lines)
        friends = state.friendship
        self.friend_text["text"] = (
            "朋友们：\n"
            f"小满 {friends.get('xiaoman', 0)}/5\n"
            f"林老师 {friends.get('lin', 0)}/5\n"
            f"顾爷爷 {friends.get('gu', 0)}/5\n"
            f"安思宜 {friends.get('an', 0)}/5\n"
            f"邵文星 {friends.get('shao', 0)}/5"
        )
        self.sticker_count["text"] = f"{len(state.stickers)} / {STICKER_SLOTS}"
        for index, label in enumerate(self.sticker_buttons):
            if index < len(self.stickers):
                sticker = self.stickers[index]
                unlocked = sticker["id"] in state.stickers
                label["text"] = sticker["name"] if unlocked else "？"
                label["fg"] = (0.70, 0.37, 0.31, 1.0) if unlocked else (0.55, 0.50, 0.44, 0.8)
            else:
                label["text"] = "？"
                label["fg"] = (0.55, 0.50, 0.44, 0.8)
