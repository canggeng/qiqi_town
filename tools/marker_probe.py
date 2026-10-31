from __future__ import annotations

import os
from argparse import Namespace
from pathlib import Path

os.environ["QIQI_TOWN_DATA_DIR"] = str(Path(".smoke-data-markers").resolve())

from panda3d.core import Filename, Point2, loadPrcFileData  # noqa: E402

loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "audio-library-name null")
loadPrcFileData("", "win-size 1600 900")
loadPrcFileData("", "notify-level warning")

from qiqi_town.app import QiqiTownApp  # noqa: E402
from qiqi_town.core.state import MinigameState  # noqa: E402

app = QiqiTownApp(Namespace(smoke_test=True, debug=False, debug_day=1, windowed=False))
app._begin_new_game(auto_save=False)
assert set(app.game_marker_nodes) == {"d1_shape", "d1_catch", "d1_rhythm"}
assert app.game_marker_nodes["d1_shape"].node().getText() == "?"
app.enter_interior("kindergarten")
app.player.set_position(2.4, -2.6, 0.0)
app.camera_rig.snap_to(app.player.position, app.player.z)
for _ in range(3):
    app.taskMgr.step()

for key, node in app.game_marker_nodes.items():
    text = node.node()
    print(key, "text=", repr(text.getText()), "font_class=", type(text.getFont()).__name__, "scale=", node.getScale())
    print("  pos", node.getPos(app.render), "bounds", node.getBounds())
    p = app.cam.getRelativePoint(app.render, node.getPos(app.render))
    projected = Point2()
    app.camLens.project(p, projected)
    print("  cam-space", p, "project", projected)

app.graphicsEngine.renderFrame()
app.win.getScreenshot().write(
    Filename.fromOsSpecific(str(Path("build/marker_close.png").resolve()))
)

marker_point = app.cam.getRelativePoint(
    app.render, app.game_marker_nodes["d1_shape"].getPos(app.render)
)
marker_screen = Point2()
app.camLens.project(marker_point, marker_screen)

class FakeMouse:
    def hasMouse(self):
        return True

    def getMouse(self):
        return marker_screen

app.mouseWatcherNode = FakeMouse()
hovered = app._find_hovered()
assert hovered is not None and hovered.id == "game_marker_d1_shape", hovered
hovered.on_interact()
assert app.mode == "minigame"
app.end_minigame(success=False, game_id="d1_shape")
app.mouseWatcherNode = None

app.exit_to_town()
app.player.set_position(13.0, -15.0, 0.0)
app.camera_rig.snap_to(app.player.position, app.player.z)
for _ in range(3):
    app.taskMgr.step()
app.graphicsEngine.renderFrame()
app.win.getScreenshot().write(
    Filename.fromOsSpecific(str(Path("build/marker_park.png").resolve()))
)
app.enter_interior("kindergarten")

app.state.minigames["d1_shape"] = MinigameState(completed=True, best=3, plays=1)
app._refresh_game_markers()
assert app.game_marker_nodes["d1_shape"].node().getText() == "√"
app.graphicsEngine.renderFrame()
app.win.getScreenshot().write(
    Filename.fromOsSpecific(str(Path("build/marker_done.png").resolve()))
)
print("after complete", sorted(app.game_marker_nodes))

app.clock.day = 2
app.state.day = 2
app._refresh_game_markers()
assert set(app.game_marker_nodes) == {"d2_find", "d2_rhythm", "d2_story"}
print("day2", sorted(app.game_marker_nodes))
app.destroy()
