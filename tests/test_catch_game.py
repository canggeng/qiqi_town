import random

from qiqi_town.systems.minigames.catch_game import CatchGame


def test_catch_finishes_after_six() -> None:
    game = CatchGame(rng=random.Random(1))
    for _ in range(6):
        assert game.catch() == "caught"
    assert game.finished
    assert game.catch() == "finished"


def test_catch_moves_target() -> None:
    game = CatchGame(rng=random.Random(2))
    game.move_timer = 0.0
    game.update(0.1)
    assert game.move_timer == game.move_interval
    assert -0.55 <= game.x <= 0.55
