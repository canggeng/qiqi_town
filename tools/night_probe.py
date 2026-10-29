from __future__ import annotations

import os
from argparse import Namespace
from pathlib import Path

os.environ["QIQI_TOWN_DATA_DIR"] = str(Path(".smoke-data-night").resolve())

from panda3d.core import Filename, loadPrcFileData  # noqa: E402

loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "audio-library-name null")
loadPrcFileData("", "win-size 1600 900")
loadPrcFileData("", "notify-level warning")

from qiqi_town.app import QiqiTownApp  # noqa: E402

app = QiqiTownApp(Namespace(smoke_test=True, debug=False, debug_day=1, windowed=False))
app._begin_new_game(auto_save=False)
app.state.quests["day1_main"].status = "complete"
app.enter_interior("home")
app.sleep_to_next_day()
app.night_ui.update(0.7)
app.graphicsEngine.renderFrame()
app.win.getScreenshot().write(
    Filename.fromOsSpecific(str(Path("build/night.png").resolve()))
)
app.destroy()
