from qiqi_town.core.conditions import EffectContext, apply_effect, apply_effects, evaluate_condition
from qiqi_town.core.state import GameState


def _state() -> GameState:
    state = GameState.new_game()
    state.day = 2
    state.time_minutes = 10 * 60
    state.location = "library"
    state.flags["met_gu"] = True
    state.friendship["gu"] = 2
    state.stickers.append("owl")
    return state


def test_condition_all_and_flag() -> None:
    state = _state()
    assert evaluate_condition({"all": [{"flag": "met_gu"}, {"day": 2}]}, state)
    assert not evaluate_condition({"flag": "missing"}, state)
    assert evaluate_condition({"flag": "met_gu", "value": True}, state)


def test_condition_time_and_location() -> None:
    state = _state()
    assert evaluate_condition({"time": "morning"}, state)
    assert evaluate_condition({"location": ["library", "home"]}, state)
    assert not evaluate_condition({"time": "dusk"}, state)


def test_condition_friendship_and_sticker() -> None:
    state = _state()
    assert evaluate_condition({"friendship": {"npc": "gu", "gte": 2}}, state)
    assert not evaluate_condition({"friendship": {"npc": "gu", "gte": 3}}, state)
    assert evaluate_condition({"sticker": "owl"}, state)


def test_condition_any_not() -> None:
    state = _state()
    assert evaluate_condition({"any": [{"day": 3}, {"day": 2}]}, state)
    assert evaluate_condition({"not": {"day": 3}}, state)


def test_effects_update_state() -> None:
    state = GameState.new_game()
    apply_effects(
        [
            {"type": "set_flag", "key": "shared_balloon", "value": True},
            {"type": "add_friendship", "npc": "xiaoman", "amount": 2},
            {"type": "give_sticker", "id": "sticker_shapes"},
            {"type": "add_journal", "id": "day1_new_friend"},
            {"type": "advance_quest", "quest": "day1_main", "step": 2},
            {"type": "add_inventory", "id": "jam"},
        ],
        state,
    )
    assert state.flags["shared_balloon"] is True
    assert state.friendship["xiaoman"] == 2
    assert state.stickers == ["sticker_shapes"]
    assert state.journal_entries == ["day1_new_friend"]
    assert state.quests["day1_main"].step == 2
    assert state.inventory == ["jam"]


def test_effect_hook() -> None:
    state = GameState.new_game()
    called = {}
    ctx = EffectContext(hooks={"play_sfx": lambda effect: called.update(effect)})
    assert apply_effect({"type": "play_sfx", "id": "chime"}, state, ctx)
    assert called["id"] == "chime"
    assert not apply_effect({"type": "unknown"}, state)
