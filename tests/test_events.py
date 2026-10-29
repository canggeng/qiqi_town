import json

from qiqi_town.core.state import GameState
from qiqi_town.paths import data_dir
from qiqi_town.systems.dialogue import DialogueRunner
from qiqi_town.systems.dialogue_data import load_dialogue_nodes

EVENT_IDS = (
    "notice",
    "fountain",
    "cat",
    "books",
    "ducks",
    "scarf",
    "balloon",
    "sandcastle",
    "art",
    "mitten",
    "squirrel",
    "lantern",
)


def _run(event_id: str) -> GameState:
    state = GameState.new_game()
    runner = DialogueRunner.from_data(load_dialogue_nodes(), state)
    assert runner.start(f"ev_{event_id}_1")
    for _ in range(40):
        if runner.finished:
            break
        if runner.waiting_for_choice:
            runner.choose(0)
        else:
            runner.advance()
    assert runner.finished
    return state


def test_all_events_complete_and_set_flags() -> None:
    for event_id in EVENT_IDS:
        state = _run(event_id)
        assert state.flags.get(f"event_{event_id}_seen"), event_id


def test_event_sticker_ids_are_valid() -> None:
    catalog = json.loads((data_dir() / "stickers.json").read_text(encoding="utf-8"))
    valid = {item["id"] for item in catalog}
    nodes = load_dialogue_nodes()
    for key, node in nodes.items():
        if not key.startswith("ev_"):
            continue
        effects = node.get("effects", []) or []
        for choice in node.get("choices", []) or []:
            effects += choice.get("effects", []) or []
        for effect in effects:
            if isinstance(effect, dict) and effect.get("type") == "give_sticker":
                assert effect["id"] in valid
