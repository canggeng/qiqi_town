from __future__ import annotations

import os
from argparse import Namespace
from pathlib import Path

os.environ["QIQI_TOWN_DATA_DIR"] = str(Path(".smoke-data-heading").resolve())

from panda3d.core import NodePath, loadPrcFileData  # noqa: E402

loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "audio-library-name null")
loadPrcFileData("", "notify-level warning")

from qiqi_town.app import QiqiTownApp  # noqa: E402

app = QiqiTownApp(Namespace(smoke_test=True, debug=False, debug_day=1, windowed=False))
app._begin_new_game(auto_save=False)
for target in ((4.0, -8.0), (0.0, -4.0), (-4.0, -8.0), (0.0, -12.0)):
    app.player.set_position(0.0, -8.0, 0.0)
    app.player.move_to(target)
    for _ in range(120):
        app.player.update(1 / 60)
    app.taskMgr.step()
    print(target, "H=", round(app.player.root.getH(), 1))
print("done")
app.destroy()
