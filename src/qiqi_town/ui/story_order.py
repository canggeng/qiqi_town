"""故事排序界面。"""

from __future__ import annotations

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGui import DirectButton, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, TransparencyAttrib

from qiqi_town.systems.minigames.story_order import StoryOrderGame, default_story_game
from qiqi_town.ui.roundrect import round_button, round_widget


class StoryOrderUi:
    def __init__(self, app) -> None:
        self.app = app
        self.font = app.font
        self.root = app.aspect2d.attachNewNode("story_order_ui")
        self.root.hide()
        self.game: StoryOrderGame | None = None
        self._game_id = "library_story"
        dim = DirectFrame(
            parent=self.root,
            frameColor=(0.06, 0.05, 0.045, 0.72),
            frameSize=(-2.2, 2.2, -1.6, 1.6),
            relief=DGG.FLAT,
        )
        dim.setTransparency(TransparencyAttrib.MAlpha)
        panel = DirectFrame(
            parent=self.root,
            frameColor=(0.99, 0.96, 0.88, 0.98),
            frameSize=(-0.9, 0.9, -0.7, 0.7),
            relief=DGG.FLAT,
        )
        panel.setTransparency(TransparencyAttrib.MAlpha)
        round_widget(panel, radius=0.05)
        self.title = self._label("故事排排队", (0, 0.58), 0.075, TextNode.ACenter)
        self.subtitle = self._label("点击两张卡片，把它们换到正确的顺序。", (0, 0.49), 0.032, TextNode.ACenter)
        self.status = self._label("", (0, -0.38), 0.034, TextNode.ACenter)
        self.card_root = self.root.attachNewNode("cards")
        self.reward_button: DirectButton | None = None

    def _label(self, text: str, pos: tuple[float, float], scale: float, align) -> OnscreenText:
        return OnscreenText(
            parent=self.root,
            text=text,
            font=self.font,
            pos=pos,
            scale=scale,
            align=align,
            fg=(0.18, 0.16, 0.15, 1.0),
            shadow=(1.0, 0.98, 0.9, 0.5),
            mayChange=True,
        )

    def start(self, game_id: str = "library_story") -> None:
        self._game_id = game_id
        self.game = default_story_game()
        self.title["text"] = "故事排排队"
        self.subtitle["text"] = "点击两张卡片，把它们换到正确的顺序。"
        self.status["text"] = ""
        self._clear_reward()
        self._rebuild()
        self.root.show()

    def hide(self) -> None:
        self.root.hide()
        self.game = None
        self._clear_reward()

    def _rebuild(self) -> None:
        for node in self.card_root.getChildren():
            node.removeNode()
        if self.game is None:
            return
        self.buttons: list[DirectButton] = []
        for index in range(len(self.game.order)):
            selected = self.game.selected == index
            button = DirectButton(
                parent=self.card_root,
                text=self.game.label_at(index),
                text_font=self.font,
                text_fg=(0.20, 0.17, 0.14, 1.0),
                text_scale=0.038,
                text_align=TextNode.ACenter,
                frameColor=(1.0, 0.86, 0.62, 1.0) if selected else (0.90, 0.80, 0.65, 0.98),
                frameSize=(-0.24, 0.24, -0.16, 0.16),
                pos=(-0.6 + index * 0.6, 0, 0.15),
                relief=DGG.FLAT,
                command=self._select,
                extraArgs=[index],
            )
            button.setTransparency(TransparencyAttrib.MAlpha)
            round_button(button, radius=0.035)
            self.buttons.append(button)

    def _select(self, index: int) -> None:
        if self.game is None:
            return
        self.app.audio.play_sfx("click")
        result = self.game.select(index)
        if result == "swapped":
            self.app.audio.play_sfx("page")
        self._rebuild()
        if self.game.finished:
            self.status["text"] = "顺序对啦！"
            self.app.audio.play_sfx("success")
            self._show_reward()

    def _show_reward(self) -> None:
        self._clear_cards()
        self.title["text"] = "故事排好啦！"
        self.subtitle["text"] = "小种子长成小芽，又开出一朵小花。"
        self.status["text"] = ""
        self.reward_button = DirectButton(
            parent=self.root,
            text="收下贴纸",
            text_font=self.font,
            text_fg=(1.0, 0.98, 0.94, 1.0),
            text_scale=0.042,
            frameColor=(0.93, 0.52, 0.43, 0.98),
            frameSize=(-0.32, 0.32, -0.08, 0.08),
            pos=(0, 0, -0.18),
            relief=DGG.FLAT,
            command=lambda: self.app.end_extra_minigame(success=True, game_id=self._game_id),
        )
        self.reward_button.setTransparency(TransparencyAttrib.MAlpha)
        round_button(self.reward_button, radius=0.04)

    def _clear_cards(self) -> None:
        for node in self.card_root.getChildren():
            node.removeNode()

    def _clear_reward(self) -> None:
        if self.reward_button is not None:
            self.reward_button.destroy()
            self.reward_button = None
