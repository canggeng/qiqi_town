from __future__ import annotations

import sys

from panda3d.core import Filename, loadPrcFileData

loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "audio-library-name null")
loadPrcFileData("", "notify-level warning")

from direct.showbase.ShowBase import ShowBase  # noqa: E402
from direct.gui.OnscreenText import OnscreenText  # noqa: E402
from panda3d.core import TextNode  # noqa: E402

base = ShowBase()
print("BASE OK", flush=True)
path = "C:/Windows/Fonts/simhei.ttf"
fn = Filename.fromOsSpecific(path)
print("FILE", fn, fn.isRegularFile(), flush=True)
font = base.loader.loadFont(fn.getFullpath())
print("FONT", font, flush=True)
if font is not None:
    print("FONT NAME", font.getName(), flush=True)
text = OnscreenText(text="青禾镇 第1天", parent=base.aspect2d, pos=(-1.2, 0.8), scale=0.08, font=font)
print("TEXT", text.getText(), flush=True)
base.graphicsEngine.renderFrame()
base.win.getScreenshot().write(
    Filename.fromOsSpecific("D:/PythonEnvs/qiqi_town/build/font_probe.png")
)
base.destroy()
sys.exit(0)
