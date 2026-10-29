import json

from qiqi_town.core.state import GameState, QuestState
from qiqi_town.paths import data_dir
from qiqi_town.systems.dialogue import DialogueRunner
from qiqi_town.systems.dialogue_data import load_dialogue_nodes


def _run_to_end(entry: str, state: GameState) -> None:
    runner = DialogueRunner.from_data(load_dialogue_nodes(), state)
    assert runner.start(entry), f"dialogue {entry} did not start"
    for _ in range(80):
        if runner.finished:
            return
        if runner.waiting_for_choice:
            runner.choose(0)
        else:
            runner.advance()
    raise AssertionError(f"dialogue {entry} did not finish")


def _state(day: int) -> GameState:
    state = GameState.new_game()
    state.day = day
    state.time_minutes = 9 * 60
    state.quests[f"day{day}_main"] = QuestState(step=0, status="active")
    return state


def test_conversation_data_has_all_days() -> None:
    nodes = load_dialogue_nodes()
    assert {
        "lin_intro_1",
        "gu_day2_1",
        "su_day3_1",
        "chen_day4_1",
        "summit_day5_1",
    }.issubset(nodes)


def test_daily_quests_complete() -> None:
    cases = [
        (1, "lin_intro_1", "day1_main", "sticker_day1"),
        (2, "gu_day2_1", "day2_main", "sticker_map"),
        (3, "su_day3_1", "day3_main", "sticker_picnic"),
        (4, "chen_day4_1", "day4_main", "sticker_hairpin"),
        (5, "summit_day5_1", "day5_main", "sticker_night"),
    ]
    for day, entry, quest_id, sticker_id in cases:
        state = _state(day)
        _run_to_end(entry, state)
        assert state.quests[quest_id].status == "complete", (day, quest_id)
        assert sticker_id in state.stickers, (day, sticker_id)
    assert state.story_complete is True


def test_sticker_ids_exist_in_catalog() -> None:
    catalog = json.loads((data_dir() / "stickers.json").read_text(encoding="utf-8"))
    valid = {item["id"] for item in catalog}
    nodes = load_dialogue_nodes()
    for node in nodes.values():
        effects = node.get("effects", []) or []
        for choice in node.get("choices", []) or []:
            effects += choice.get("effects", []) or []
        for effect in effects:
            if isinstance(effect, dict) and effect.get("type") == "give_sticker":
                assert effect["id"] in valid, effect["id"]
