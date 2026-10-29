from qiqi_town.systems.minigames.memory import MemoryGame


def test_memory_sequence_and_finish() -> None:
    game = MemoryGame(sequence=[2, 0, 3, 1], timer=0.0)
    assert game.press(2) == "correct"
    assert game.press(0) == "correct"
    assert game.press(3) == "correct"
    assert game.press(1) == "finished"
    assert game.finished


def test_memory_wrong_resets_input() -> None:
    game = MemoryGame(sequence=[0, 1, 2, 3], timer=0.0)
    game.press(0)
    assert game.press(2) == "wrong"
    assert game.input == []
    assert game.mistakes == 1


def test_memory_waits_during_reveal() -> None:
    game = MemoryGame(sequence=[0, 1, 2, 3], timer=1.0)
    assert game.showing
    assert game.press(0) == "wait"
    game.update(2.0)
    assert not game.showing
    assert game.press(0) == "correct"
