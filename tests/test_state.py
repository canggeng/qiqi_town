from qiqi_town.core.state import GameState, MinigameState, PlayerState, QuestState


def test_new_game_defaults() -> None:
    state = GameState.new_game()
    assert state.day == 1
    assert state.location == "home"
    assert state.quests["day1_main"].status == "active"
    assert state.player.is_valid()


def test_state_roundtrip() -> None:
    state = GameState.new_game()
    state.day = 3
    state.time_minutes = 700
    state.location = "park"
    state.player = PlayerState(1.25, -3.5, 0.75)
    state.flags["met_su"] = True
    state.quests["day3_main"] = QuestState(step=2, status="active")
    state.minigames["day3_ducks"] = MinigameState(completed=True, best=5, plays=2)
    state.stickers.extend(["sticker_a", "sticker_b"])
    state.friendship["xiaoman"] = 99
    state.add_sticker("sticker_a")
    raw = state.to_dict()
    loaded = GameState.from_dict(raw)
    assert loaded.day == 3
    assert loaded.location == "park"
    assert loaded.player.x == 1.25
    assert loaded.flags["met_su"] is True
    assert loaded.quests["day3_main"].step == 2
    assert loaded.minigames["day3_ducks"].completed is True
    assert loaded.stickers == ["sticker_a", "sticker_b"]
    assert loaded.friendship["xiaoman"] == 5


def test_invalid_values_are_repaired() -> None:
    loaded = GameState.from_dict(
        {
            "day": 99,
            "time_minutes": 9999,
            "location": "moon",
            "player": {"x": float("nan"), "y": 1, "facing": 0},
        }
    )
    assert loaded.day == 5
    assert loaded.time_minutes == 20 * 60
    assert loaded.location == "home"
    assert loaded.player.x == 0.0


def test_state_unknown_location_falls_back() -> None:
    loaded = GameState.from_dict({"location": "not_a_place"})
    assert loaded.location == "home"
