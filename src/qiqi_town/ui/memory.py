"""山路记忆界面。"""

from __future__ import annotations

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGui import DirectButton, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, TransparencyAttrib

from qiqi_town.systems.minigames.memory import MemoryGame, random_memory_game

COLORS = (
    ("红", (0.92, 0.38, 0.34, 1.0)),
    ("黄", (0.96, 0.78, 0.34, 1.0)),
    ("蓝", (0.36, 0.63, 0.86, 1.0)),
    ("绿", (0.42, 0.72, 0.44, 1.0)),
)


class MemoryUi:
    def __init__(self, app) -> None:
        self.app = app
        self.font = app.font
        self.root = app.aspect2d.attachNewNode("memory_ui")
        self.root.hide()
        self.game: MemoryGame | None = None
        self._game_id = "mountain_memory"
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
        self.title = self._label("山路记忆", (0, 0.55), 0.075, TextNode.ACenter)
        self.subtitle = self._label("", (0, 0.45), 0.036, TextNode.ACenter)
        self.progress = self._label("", (0, -0.34), 0.034, TextNode.ACenter)
        self.buttons: list[DirectButton] = []
        for index, (label, color) in enumerate(COLORS):
            button = DirectButton(
                parent=self.root,
                text=label,
                text_font=self.font,
                text_fg=(0.16, 0.14, 0.12, 1.0),
                text_scale=0.045,
                frameColor=color,
                frameSize=(-0.16, 0.16, -0.10, 0.10),
                pos=(-0.6 + index * 0.4, 0, 0.02),
                relief=DGG.FLAT,
                command=self._press,
                extraArgs=[index],
            )
            button.setTransparency(TransparencyAttrib.MAlpha)
            self.buttons.append(button)
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

    def start(self, game_id: str = "mountain_memory") -> None:
        self._game_id = game_id
        self.game = random_memory_game()
        self._clear_reward()
        self.title["text"] = "山路记忆"
        self.subtitle["text"] = "记住亮起的颜色顺序，然后按同样的顺序点击。"
        self._update_texts()
        for button in self.buttons:
            button.show()
        self.root.show()

    def _update_texts(self) -> None:
        if self.game is None:
            return
        if self.game.showing:
            seq = "  ".join(COLORS[i][0] for i in self.game.sequence)
            self.subtitle["text"] = f"看清顺序：{seq}"
            self.progress["text"] = ""
        elif not self.game.finished:
            self.subtitle["text"] = "轮到你了，按刚才的顺序点击。"
            self.progress["text"] = f"已点 {len(self.game.input)} / {len(self.game.sequence)}"
        else:
            self.subtitle["text"] = "全部记住啦！"
            self.progress["text"] = ""

    def update(self, dt: float) -> None:
        if self.game is None:
            return
        was_showing = self.game.showing
        self.game.update(dt)
        if was_showing and not self.game.showing:
            self._update_texts()

    def _press(self, index: int) -> None:
        if self.game is None:
            return
        self.app.audio.play_sfx("click")
        result = self.game.press(index)
        if result == "wrong":
            self.app.audio.play_sfx("error", volume=0.6)
        self._update_texts()
        if result == "finished":
            self.app.audio.play_sfx("success")
            self._show_reward()

    def _show_reward(self) -> None:
        for button in self.buttons:
            button.hide()
        self.title["text"] = "记住啦！"
        self.subtitle["text"] = "山路上的彩色路标，已经记在淇淇心里。"
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
