from __future__ import annotations

import os
from argparse import Namespace
from pathlib import Path

os.environ["QIQI_TOWN_DATA_DIR"] = str(Path(".smoke-data-flow").resolve())

from panda3d.core import loadPrcFileData  # noqa: E402

loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "audio-library-name null")
loadPrcFileData("", "notify-level warning")

from qiqi_town.app import QiqiTownApp  # noqa: E402

ENTRIES = {
    1: "lin_intro_1",
    2: "gu_day2_1",
    3: "su_day3_1",
    4: "chen_day4_1",
    5: "summit_day5_1",
}

args = Namespace(smoke_test=True, debug=False, debug_day=1, windowed=False)
app = QiqiTownApp(args)
app._begin_new_game(auto_save=False)
app.settings.text_speed = 999.0


def run_dialogue(entry: str) -> None:
    app.start_dialogue(entry)
    assert app.mode == "dialogue", entry
    for _ in range(80):
        if app.mode != "dialogue":
            break
        app.dialogue_ui.update(2.0)
        if app.dialogue_ui._choice_ready:
            app.dialogue_ui._choose(0)
        else:
            app.dialogue_ui.handle_click()
    assert app.mode != "dialogue", entry


for day in range(1, 5):
    app.clock.day = day
    app.state.day = day
    app.state.quests.setdefault(f"day{day}_main", __import__("qiqi_town.core.state", fromlist=["QuestState"]).QuestState(0, "active"))
    run_dialogue(ENTRIES[day])
    assert app.state.quests[f"day{day}_main"].status == "complete", day
    if day < 5:
        before = app.clock.day
        app.sleep_to_next_day()
        assert app.mode == "transition"
        for _ in range(300):
            if app.mode == "playing":
                break
            app.night_ui.update(0.1)
            app.taskMgr.step()
        assert app.mode == "playing", "night transition did not finish"
        assert app.clock.day == before + 1, (before, app.clock.day)

app.clock.day = 5
app.state.day = 5
app.state.quests.setdefault("day5_main", __import__("qiqi_town.core.state", fromlist=["QuestState"]).QuestState(0, "active"))
run_dialogue("summit_day5_1")
assert app.state.story_complete
assert app.mode == "ending"
app.finish_ending()
assert app.mode == "playing"

app._sync_state_from_world()
app.save_repo.save_manual(4, app.state)
loaded = app.save_repo.load_manual(4)
assert loaded.story_complete and loaded.day == 5
print("full flow ok:", loaded.day, loaded.stickers, loaded.location)
app.destroy()
