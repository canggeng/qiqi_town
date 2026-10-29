"""睡觉时的夜间过渡：淡入黑屏、晚安、第二天清晨、淡出。"""

from __future__ import annotations

from collections.abc import Callable

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGui import DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, TransparencyAttrib


class NightTransitionUi:
    def __init__(self, app) -> None:
        self.app = app
        self.root = app.aspect2d.attachNewNode("night_transition")
        self.root.hide()
        self.dim = DirectFrame(
            parent=self.root,
            frameColor=(0.02, 0.03, 0.06, 0.0),
            frameSize=(-2.2, 2.2, -1.6, 1.6),
            relief=DGG.FLAT,
        )
        self.dim.setTransparency(TransparencyAttrib.MAlpha)
        self.title = OnscreenText(
            parent=self.root,
            text="晚安，淇淇。",
            font=app.font,
            pos=(0, 0.08),
            scale=0.105,
            align=TextNode.ACenter,
            fg=(1.0, 0.93, 0.78, 1.0),
            mayChange=True,
        )
        self.subtitle = OnscreenText(
            parent=self.root,
            text="今天也辛苦啦。",
            font=app.font,
            pos=(0, -0.06),
            scale=0.04,
            align=TextNode.ACenter,
            fg=(0.92, 0.84, 0.70, 1.0),
            mayChange=True,
        )
        self.title.hide()
        self.subtitle.hide()
        self.phase = "idle"
        self._timer = 0.0
        self._alpha = 0.0
        self._next_day = 1
        self._night_message = "今天也辛苦啦。"
        self._on_midpoint: Callable[[], None] | None = None
        self._on_done: Callable[[], None] | None = None

    def start(
        self,
        next_day: int,
        on_midpoint: Callable[[], None],
        on_done: Callable[[], None],
        *,
        night_message: str | None = None,
    ) -> None:
        self._next_day = next_day
        self._night_message = night_message or "今天也辛苦啦。"
        self._on_midpoint = on_midpoint
        self._on_done = on_done
        self._timer = 0.0
        self._alpha = 0.0
        self.phase = "fade_in"
        self._set_alpha(0.0)
        self.title.hide()
        self.subtitle.hide()
        self.root.show()

    def update(self, dt: float) -> None:
        if self.phase == "idle":
            return
        if self.phase == "fade_in":
            self._alpha = min(1.0, self._alpha + dt / 0.55)
            self._set_alpha(self._alpha)
            if self._alpha >= 1.0:
                self.phase = "night"
                self._timer = 0.0
                self.title["text"] = "晚安，淇淇。"
                self.subtitle["text"] = self._night_message
                self.title.show()
                self.subtitle.show()
        elif self.phase == "night":
            self._timer += dt
            if self._timer >= 0.9:
                if self._on_midpoint is not None:
                    self._on_midpoint()
                self.phase = "morning"
                self._timer = 0.0
                self.title["text"] = f"第 {self._next_day} 天 · 清晨"
                self.subtitle["text"] = "新的一天开始了。"
        elif self.phase == "morning":
            self._timer += dt
            if self._timer >= 1.0:
                self.phase = "fade_out"
        elif self.phase == "fade_out":
            self._alpha = max(0.0, self._alpha - dt / 0.55)
            self._set_alpha(self._alpha)
            if self._alpha <= 0.0:
                self.root.hide()
                self.phase = "idle"
                if self._on_done is not None:
                    self._on_done()

    def _set_alpha(self, alpha: float) -> None:
        self.dim["frameColor"] = (0.02, 0.03, 0.06, alpha)
