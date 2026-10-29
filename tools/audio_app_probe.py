from __future__ import annotations

from argparse import Namespace

from panda3d.core import loadPrcFileData

loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "audio-library-name p3openal_audio")
loadPrcFileData("", "notify-level warning")

from qiqi_town.app import QiqiTownApp  # noqa: E402

args = Namespace(smoke_test=False, debug=False, debug_day=1, windowed=False)
app = QiqiTownApp(args)
print("audio available:", app.audio.available, flush=True)
print("music:", app.audio._current_music, "ambient:", app.audio._current_ambient, flush=True)
for _ in range(5):
    app.taskMgr.step()
app.destroy()
