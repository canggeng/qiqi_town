from __future__ import annotations

import os
from argparse import Namespace
from pathlib import Path

os.environ["QIQI_TOWN_DATA_DIR"] = str(Path(".smoke-data-fullscreen").resolve())

from panda3d.core import Filename, loadPrcFileData  # noqa: E402

loadPrcFileData("", "win-size 1280 720")
loadPrcFileData("", "audio-library-name null")
loadPrcFileData("", "notify-level warning")

from qiqi_town.app import QiqiTownApp  # noqa: E402

app = QiqiTownApp(Namespace(smoke_test=False, debug=False, debug_day=1, windowed=True))
app._begin_new_game(auto_save=False)
app.toggle_fullscreen()
for _ in range(3):
    app.taskMgr.step()
app.graphicsEngine.renderFrame()
app.win.getScreenshot().write(
    Filename.fromOsSpecific(str(Path("build/fullscreen.png").resolve()))
)
print("fullscreen setting:", app.settings.fullscreen)
app.toggle_fullscreen()
for _ in range(2):
    app.taskMgr.step()
app.destroy()
