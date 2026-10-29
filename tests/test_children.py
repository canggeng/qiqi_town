from qiqi_town.core.state import GameState
from qiqi_town.systems.dialogue import DialogueRunner
from qiqi_town.systems.dialogue_data import load_dialogue_nodes


def _run(entry: str) -> GameState:
    state = GameState.new_game()
    runner = DialogueRunner.from_data(load_dialogue_nodes(), state)
    assert runner.start(entry)
    for _ in range(30):
        if runner.finished:
            break
        if runner.waiting_for_choice:
            runner.choose(0)
        else:
            runner.advance()
    return state


def test_an_dialogue() -> None:
    state = _run("an_intro_1")
    assert state.flags.get("met_an")
    assert state.friendship.get("an", 0) >= 1


def test_shao_dialogue() -> None:
    state = _run("shao_intro_1")
    assert state.flags.get("met_shao")
    assert state.friendship.get("shao", 0) >= 1


def test_duck_dialogue() -> None:
    state = _run("ducks_talk_1")
    assert state.flags.get("event_ducks_seen")
