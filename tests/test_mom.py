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
    assert runner.finished
    return state


def test_mom_morning_dialogue() -> None:
    state = _run("mom_morning_1")
    assert state.friendship.get("mom", 0) >= 1


def test_mom_afternoon_dialogue() -> None:
    state = _run("mom_afternoon_1")
    assert state.friendship.get("mom", 0) >= 1


def test_mom_night_dialogue() -> None:
    state = _run("mom_night_1")
    assert state.friendship.get("mom", 0) >= 1
