from __future__ import annotations

import os
from argparse import Namespace
from pathlib import Path

os.environ["QIQI_TOWN_DATA_DIR"] = str(Path(".smoke-data-click").resolve())

from panda3d.core import Point2, Point3, loadPrcFileData  # noqa: E402

loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "audio-library-name null")
loadPrcFileData("", "notify-level warning")

from qiqi_town.app import QiqiTownApp  # noqa: E402

app = QiqiTownApp(Namespace(smoke_test=True, debug=False, debug_day=1, windowed=False))
app._begin_new_game(auto_save=False)
app._activate_scene("town", app.town_scene.player_start, 3.14159)
for y in (0.4, 0.1, -0.2, -0.5, -0.8):
    for x in (-0.6, 0.0, 0.6):
        point = app._screen_to_ground(Point2(x, y))
        print(f"screen=({x:.1f},{y:.1f}) -> {None if point is None else (round(point.x,1), round(point.y,1))}")
near = Point3()
far = Point3()
app.camLens.extrude(Point2(0, 0), near, far)
print("raw near", near, "raw far", far, "cam", app.cam.getPos(), "hpr", app.cam.getHpr())
near_world = app.cam.getRelativePoint(app.render, near)
far_world = app.cam.getRelativePoint(app.render, far)
print("cam", app.cam.getPos(), "near", near_world, "far", far_world, "dir", far_world - near_world)
app.destroy()
