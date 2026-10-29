from __future__ import annotations

import os
import time
from argparse import Namespace
from pathlib import Path

os.environ["QIQI_TOWN_DATA_DIR"] = str(Path(".smoke-data-perf").resolve())

from panda3d.core import loadPrcFileData  # noqa: E402

loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "audio-library-name null")
loadPrcFileData("", "notify-level warning")

from qiqi_town.app import QiqiTownApp  # noqa: E402

app = QiqiTownApp(Namespace(smoke_test=True, debug=False, debug_day=1, windowed=False))
app._begin_new_game(auto_save=False)
for _ in range(10):
    app.taskMgr.step()
start = time.perf_counter()
frames = 240
for _ in range(frames):
    app.taskMgr.step()
elapsed = time.perf_counter() - start
print(f"frames={frames} elapsed={elapsed:.3f}s avg_ms={elapsed / frames * 1000:.2f}")
app.destroy()
