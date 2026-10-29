from __future__ import annotations

import os
from argparse import Namespace
from pathlib import Path

os.environ["QIQI_TOWN_DATA_DIR"] = str(Path(".smoke-data-runtime").resolve())

from panda3d.core import loadPrcFileData  # noqa: E402

loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "audio-library-name null")
loadPrcFileData("", "notify-level warning")

from qiqi_town.app import QiqiTownApp  # noqa: E402
from qiqi_town.systems.daily_content import slot_for  # noqa: E402

args = Namespace(smoke_test=True, debug=False, debug_day=1, windowed=False)
app = QiqiTownApp(args)
app._begin_new_game(auto_save=False)
app.settings.text_speed = 999

# Day 1 shape
app.clock.day = 1
app.state.day = 1
app._activate_scene("town", app.town_scene.player_start, 0.0)
app.enter_interior("kindergarten")
app.start_shape_game()
assert app.mode == "minigame"
slot = slot_for(1, "shape")
app.end_minigame(success=True, game_id=slot.id)
assert slot.id in app.state.minigames
app.exit_to_town()

# Day 2 story
app.clock.day = 2
app.state.day = 2
app._activate_scene("town", (-14.0, -1.0), 0.0)
app.enter_interior("library")
app.start_story_game()
assert app.mode == "minigame"
slot = slot_for(2, "story")
app.end_extra_minigame(success=True, game_id=slot.id)
assert slot.id in app.state.minigames
app.exit_to_town()

# Day 2 rhythm
app.clock.day = 2
app.state.day = 2
app._activate_scene("town", (-20.0, -10.0), 0.0)
app.start_rhythm_game()
assert app.mode == "minigame"
slot = slot_for(2, "rhythm")
app.end_extra_minigame(success=True, game_id=slot.id)

# Day 3 memory
app.clock.day = 3
app.state.day = 3
app._activate_scene("town", (0.0, 14.0), 0.0)
app.start_memory_game()
assert app.mode == "minigame"
slot = slot_for(3, "memory")
app.end_extra_minigame(success=True, game_id=slot.id)

# Day 2 find
app.clock.day = 2
app.state.day = 2
app._activate_scene("town", (0.0, -8.0), 0.0)
app.start_find_game()
assert app.find_game.active
for target in list(app.find_game.targets):
    app._collect_sparkle(target)
assert slot_for(2, "find") is not None
assert not app.find_game.active

print("runtime probe ok; stickers:", len(app.state.stickers))
app.destroy()
