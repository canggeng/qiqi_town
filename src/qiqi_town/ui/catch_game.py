"""接花瓣（公园）界面。"""

from __future__ import annotations

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGui import DirectButton, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, TransparencyAttrib

from qiqi_town.systems.minigames.catch_game import CatchGame


class CatchUi:
    def __init__(self, app) -> None:
        self.app = app
        self.font = app.font
        self.root = app.aspect2d.attachNewNode("catch_ui")
        self.root.hide()
        self.game: CatchGame | None = None
        self._game_id = "park_catch"
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
            frameSize=(-0.9, 0.9, -0.66, 0.66),
            relief=DGG.FLAT,
        )
        panel.setTransparency(TransparencyAttrib.MAlpha)
        self.title = self._label("接住花瓣", (0, 0.55), 0.075, TextNode.ACenter)
        self.subtitle = self._label("点击飘动的花瓣，接住 6 片。", (0, 0.46), 0.032, TextNode.ACenter)
        self.progress = self._label("0 / 6", (0, -0.35), 0.036, TextNode.ACenter)
        self.flower = DirectButton(
            parent=self.root,
            text="花瓣",
            text_font=self.font,
            text_fg=(0.38, 0.17, 0.15, 1.0),
            text_scale=0.036,
            frameColor=(1.0, 0.66, 0.72, 0.98),
            frameSize=(-0.18, 0.18, -0.09, 0.09),
            pos=(0, 0, 0.1),
            relief=DGG.FLAT,
            command=self._catch,
        )
        self.flower.setTransparency(TransparencyAttrib.MAlpha)
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

    def start(self, game_id: str = "park_catch") -> None:
        self._game_id = game_id
        self.game = CatchGame()
        self._clear_reward()
        self.title["text"] = "接住花瓣"
        self.subtitle["text"] = "点击飘动的花瓣，接住 6 片。"
        self.progress["text"] = "0 / 6"
        self.flower.show()
        self.flower.setPos(0, 0, 0.1)
        self.root.show()

    def update(self, dt: float) -> None:
        if self.game is None or self.game.finished:
            return
        self.game.update(dt)
        self.flower.setPos(self.game.x, 0, self.game.y)

    def _catch(self) -> None:
        if self.game is None:
            return
        result = self.game.catch()
        if result == "caught":
            self.app.audio.play_sfx("page", volume=0.5)
        self.progress["text"] = f"{self.game.catches} / {self.game.target}"
        if self.game.finished:
            self.app.audio.play_sfx("success")
            self._show_reward()

    def _show_reward(self) -> None:
        self.flower.hide()
        self.title["text"] = "接住啦！"
        self.subtitle["text"] = "花瓣轻轻落在淇淇的手心里。"
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

    def _clear_reward(self) -> None:
        if self.reward_button is not None:
            self.reward_button.destroy()
            self.reward_button = None

    def hide(self) -> None:
        self.root.hide()
        self.game = None
        self._clear_reward()
