"""灯会结局界面。"""

from __future__ import annotations

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGui import DirectButton, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode, TransparencyAttrib


class EndingUi:
    def __init__(self, app) -> None:
        self.app = app
        self.root = app.aspect2d.attachNewNode("ending_ui")
        self.root.hide()
        dim = DirectFrame(
            parent=self.root,
            frameColor=(0.04, 0.05, 0.08, 0.78),
            frameSize=(-2.2, 2.2, -1.6, 1.6),
            relief=DGG.FLAT,
        )
        dim.setTransparency(TransparencyAttrib.MAlpha)
        panel = DirectFrame(
            parent=self.root,
            frameColor=(0.99, 0.96, 0.88, 0.98),
            frameSize=(-0.85, 0.85, -0.62, 0.62),
            relief=DGG.FLAT,
        )
        panel.setTransparency(TransparencyAttrib.MAlpha)
        OnscreenText(
            parent=self.root,
            text="山顶的灯会",
            font=app.font,
            pos=(0, 0.45),
            scale=0.09,
            align=TextNode.ACenter,
            fg=(0.22, 0.19, 0.16, 1.0),
            mayChange=False,
        )
        OnscreenText(
            parent=self.root,
            text=(
                "红气球在风里轻轻晃。\n"
                "小满、阿泽、林老师，还有整座青禾镇，\n"
                "都在灯会的光里。\n\n"
                "这个夏天，淇淇会一直记得。"
            ),
            font=app.font,
            pos=(0, 0.22),
            scale=0.04,
            align=TextNode.ACenter,
            fg=(0.30, 0.26, 0.22, 1.0),
            mayChange=False,
        )
        DirectButton(
            parent=self.root,
            text="继续在小镇里逛逛",
            text_font=app.font,
            text_fg=(1.0, 0.98, 0.94, 1.0),
            text_scale=0.04,
            frameColor=(0.93, 0.52, 0.43, 0.98),
            frameSize=(-0.4, 0.4, -0.07, 0.07),
            pos=(0, 0, -0.38),
            relief=DGG.FLAT,
            command=app.finish_ending,
        )

    def show(self) -> None:
        self.root.show()

    def hide(self) -> None:
        self.root.hide()
