from __future__ import annotations

import os
from argparse import Namespace
from pathlib import Path

os.environ["QIQI_TOWN_DATA_DIR"] = str(Path(".smoke-data-dialogue").resolve())

from panda3d.core import Filename, loadPrcFileData  # noqa: E402

loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "audio-library-name null")
loadPrcFileData("", "win-size 1600 900")
loadPrcFileData("", "notify-level warning")

from qiqi_town.app import QiqiTownApp  # noqa: E402

app = QiqiTownApp(Namespace(smoke_test=True, debug=False, debug_day=1, windowed=False))
app._begin_new_game(auto_save=False)
app.settings.text_speed = 999
app.start_dialogue("lin_intro_1")
app.dialogue_ui.update(2.0)
app.graphicsEngine.renderFrame()
app.win.getScreenshot().write(
    Filename.fromOsSpecific(str(Path("build/dialogue_continue.png").resolve()))
)
app.destroy()
