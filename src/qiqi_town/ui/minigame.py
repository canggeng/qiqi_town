"""形状配对小游戏界面。"""

from __future__ import annotations

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGui import DirectButton, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, TransparencyAttrib

from qiqi_town.systems.minigames.shape_match import ShapeMatchGame, default_shape_game
from qiqi_town.ui.roundrect import round_button, round_widget


class MinigameUi:
    def __init__(self, app) -> None:
        self.app = app
        self.font = app.font
        self.root = app.aspect2d.attachNewNode("minigame_ui")
        self.root.hide()
        self.game: ShapeMatchGame | None = None
        self._game_id = "day1_shapes"
        self.dim = DirectFrame(
            parent=self.root,
            frameColor=(0.06, 0.05, 0.045, 0.72),
            frameSize=(-2.2, 2.2, -1.6, 1.6),
            relief=DGG.FLAT,
        )
        self.dim.setTransparency(TransparencyAttrib.MAlpha)
        self.panel = DirectFrame(
            parent=self.root,
            frameColor=(0.99, 0.96, 0.88, 0.98),
            frameSize=(-0.92, 0.92, -0.76, 0.76),
            relief=DGG.FLAT,
        )
        self.panel.setTransparency(TransparencyAttrib.MAlpha)
        round_widget(self.panel, radius=0.05)
        self.title = self._label("形状小管家", (0, 0.64), 0.075, TextNode.ACenter)
        self.subtitle = self._label(
            "先点下面的形状，再点上面它的家。", (0, 0.55), 0.032, TextNode.ACenter
        )
        self.status = self._label("", (0, -0.46), 0.036, TextNode.ACenter)
        self.slot_root = self.root.attachNewNode("slots")
        self.item_root = self.root.attachNewNode("items")
        self.reward_button: DirectButton | None = None
        self._build_buttons()
        self._update_buttons()

    def _label(self, text: str, pos: tuple[float, float], scale: float, align) -> OnscreenText:
        return OnscreenText(
            parent=self.root,
            text=text,
            font=self.font,
            pos=pos,
            scale=scale,
            align=align,
            fg=(0.18, 0.16, 0.15, 1.0),
            shadow=(1.0, 0.98, 0.9, 0.6),
            mayChange=True,
        )

    def _build_buttons(self) -> None:
        for node in self.slot_root.getChildren():
            node.removeNode()
        for node in self.item_root.getChildren():
            node.removeNode()
        self.slot_buttons: dict[str, DirectButton] = {}
        self.item_buttons: dict[str, DirectButton] = {}
        if self.game is None:
            return
        for index, slot in enumerate(self.game.slots):
            x = -0.55 + index * 0.55
            button = DirectButton(
                parent=self.slot_root,
                text=slot.label,
                text_font=self.font,
                text_fg=(0.22, 0.19, 0.16, 1.0),
                text_scale=0.034,
                frameColor=(0.88, 0.80, 0.66, 0.98),
                frameSize=(-0.24, 0.24, -0.11, 0.11),
                pos=(x, 0, 0.25),
                relief=DGG.FLAT,
                command=self._choose_slot,
                extraArgs=[slot.id],
            )
            button.setTransparency(TransparencyAttrib.MAlpha)
            round_button(button, radius=0.04)
            self.slot_buttons[slot.id] = button
        for index, item in enumerate(self.game.items):
            x = -0.55 + index * 0.55
            button = DirectButton(
                parent=self.item_root,
                text=item.label,
                text_font=self.font,
                text_fg=(0.16, 0.14, 0.12, 1.0),
                text_scale=0.032,
                frameColor=item.color,
                frameSize=(-0.24, 0.24, -0.11, 0.11),
                pos=(x, 0, -0.18),
                relief=DGG.FLAT,
                command=self._select_item,
                extraArgs=[item.id],
            )
            button.setTransparency(TransparencyAttrib.MAlpha)
            round_button(button, radius=0.04)
            self.item_buttons[item.id] = button

    def _update_buttons(self) -> None:
        if self.game is None:
            return
        for item_id, button in self.item_buttons.items():
            if item_id in self.game.matched:
                button.hide()
            else:
                button.show()
                item = next(item for item in self.game.items if item.id == item_id)
                selected = self.game.selected == item_id
                button["frameColor"] = (
                    (min(1.0, item.color[0] + 0.15), min(1.0, item.color[1] + 0.15), min(1.0, item.color[2] + 0.15), 1.0)
                    if selected
                    else item.color
                )
        for slot_id, button in self.slot_buttons.items():
            matched = any(item.slot == slot_id and item.id in self.game.matched for item in self.game.items)
            button["frameColor"] = (0.70, 0.78, 0.63, 0.9) if matched else (0.88, 0.80, 0.66, 0.98)
        if self.game.finished:
            self.status["text"] = "全部放对啦！"
        elif self.game.selected is None:
            self.status["text"] = ""
        else:
            item = next((item for item in self.game.items if item.id == self.game.selected), None)
            self.status["text"] = f"选中：{item.label}" if item else ""

    def start(self, game_id: str = "day1_shapes") -> None:
        self._game_id = game_id
        self.game = default_shape_game()
        self.title["text"] = "形状小管家"
        self.subtitle["text"] = "先点下面的形状，再点上面它的家。"
        self.status["text"] = ""
        if self.reward_button is not None:
            self.reward_button.destroy()
            self.reward_button = None
        self._build_buttons()
        self._update_buttons()
        self.root.show()

    def hide(self) -> None:
        self.root.hide()
        self.game = None
        if self.reward_button is not None:
            self.reward_button.destroy()
            self.reward_button = None

    def _select_item(self, item_id: str) -> None:
        if self.game is None:
            return
        self.app.audio.play_sfx("click")
        if self.game.select_item(item_id):
            self._update_buttons()

    def _choose_slot(self, slot_id: str) -> None:
        if self.game is None:
            return
        self.app.audio.play_sfx("click")
        result = self.game.choose_slot(slot_id)
        if result == "correct":
            self.app.audio.play_sfx("success", volume=0.55)
            self._update_buttons()
            if self.game.finished:
                self._show_reward()
        elif result == "wrong":
            self.app.audio.play_sfx("error", volume=0.6)
            self.status["text"] = "这里不是它的家，再试试。"
            self._update_buttons()

    def _show_reward(self) -> None:
        self._clear_buttons()
        self.title["text"] = "完成啦！"
        self.subtitle["text"] = "你帮每个形状找到了自己的家。"
        self.status["text"] = ""
        self.reward_button = DirectButton(
            parent=self.root,
            text="收下贴纸",
            text_font=self.font,
            text_fg=(1.0, 0.98, 0.94, 1.0),
            text_scale=0.042,
            frameColor=(0.93, 0.52, 0.43, 0.98),
            frameSize=(-0.32, 0.32, -0.08, 0.08),
            pos=(0, 0, -0.22),
            relief=DGG.FLAT,
            command=lambda: self.app.end_minigame(success=True, game_id=self._game_id),
        )
        self.reward_button.setTransparency(TransparencyAttrib.MAlpha)
        round_button(self.reward_button, radius=0.04)

    def _clear_buttons(self) -> None:
        for node in self.slot_root.getChildren():
            node.removeNode()
        for node in self.item_root.getChildren():
            node.removeNode()

    def cancel(self) -> None:
        self.app.end_minigame(success=False, game_id=self._game_id)
