"""秋千节奏界面。"""

from __future__ import annotations

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGui import DirectButton, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, TransparencyAttrib

from qiqi_town.systems.minigames.rhythm import RhythmGame
from qiqi_town.ui.roundrect import round_button, round_widget


class RhythmUi:
    def __init__(self, app) -> None:
        self.app = app
        self.font = app.font
        self.root = app.aspect2d.attachNewNode("rhythm_ui")
        self.root.hide()
        self.game: RhythmGame | None = None
        self._game_id = "playground_rhythm"
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
        round_widget(panel, radius=0.05)
        self.title = self._label("秋千节奏", (0, 0.54), 0.075, TextNode.ACenter)
        self.subtitle = self._label("指针进入亮色区域时，点击“推秋千！”。", (0, 0.45), 0.03, TextNode.ACenter)
        self.progress = self._label("", (0, -0.33), 0.036, TextNode.ACenter)
        # 节奏条
        self.bar_bg = DirectFrame(
            parent=self.root,
            frameColor=(0.78, 0.72, 0.62, 0.9),
            frameSize=(-0.5, 0.5, -0.045, 0.045),
            pos=(0, 0, 0.14),
            relief=DGG.FLAT,
        )
        self.bar_bg.setTransparency(TransparencyAttrib.MAlpha)
        self.zone = DirectFrame(
            parent=self.root,
            frameColor=(0.97, 0.76, 0.35, 0.9),
            frameSize=(-0.1, 0.1, -0.05, 0.05),
            pos=(0.15, 0, 0.14),
            relief=DGG.FLAT,
        )
        self.zone.setTransparency(TransparencyAttrib.MAlpha)
        self.marker = DirectFrame(
            parent=self.root,
            frameColor=(0.90, 0.30, 0.27, 1.0),
            frameSize=(-0.018, 0.018, -0.08, 0.08),
            pos=(-0.4, 0, 0.14),
            relief=DGG.FLAT,
        )
        self.marker.setTransparency(TransparencyAttrib.MAlpha)
        self.push_button = DirectButton(
            parent=self.root,
            text="推秋千！",
            text_font=self.font,
            text_fg=(1.0, 0.98, 0.94, 1.0),
            text_scale=0.042,
            frameColor=(0.93, 0.52, 0.43, 0.98),
            frameSize=(-0.3, 0.3, -0.08, 0.08),
            pos=(0, 0, -0.12),
            relief=DGG.FLAT,
            command=self._push,
        )
        self.push_button.setTransparency(TransparencyAttrib.MAlpha)
        round_button(self.push_button, radius=0.04)
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

    def start(self, game_id: str = "playground_rhythm") -> None:
        self._game_id = game_id
        self.game = RhythmGame()
        self._clear_reward()
        self.title["text"] = "秋千节奏"
        self.subtitle["text"] = "指针进入亮色区域时，点击“推秋千！”。"
        self.progress["text"] = "推起 0 / 5 次"
        self.push_button.show()
        self.marker.setX(-0.4)
        self.root.show()

    def update(self, dt: float) -> None:
        if self.game is None or self.game.finished:
            return
        self.game.update(dt)
        self.marker.setX(-0.5 + self.game.position)

    def _push(self) -> None:
        if self.game is None:
            return
        result = self.game.hit()
        if result == "hit":
            self.app.audio.play_sfx("swing")
        else:
            self.app.audio.play_sfx("error", volume=0.5)
        self.progress["text"] = f"推起 {self.game.hits} / {self.game.target_hits} 次"
        if self.game.finished:
            self.app.audio.play_sfx("success")
            self._show_reward()

    def _show_reward(self) -> None:
        self.push_button.hide()
        self.title["text"] = "秋千飞高啦！"
        self.subtitle["text"] = "小满在秋千上笑得很开心。"
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

    def _clear_reward(self) -> None:
        if self.reward_button is not None:
            self.reward_button.destroy()
            self.reward_button = None

    def hide(self) -> None:
        self.root.hide()
        self.game = None
        self._clear_reward()
