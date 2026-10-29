from qiqi_town.systems.minigames.story_order import StoryOrderGame, default_story_game


def test_story_order_can_be_solved() -> None:
    game = default_story_game()
    assert not game.finished
    assert game.select(0) == "selected"
    assert game.select(2) == "swapped"
    assert not game.finished
    assert game.select(0) == "selected"
    assert game.select(1) == "swapped"
    assert game.finished


def test_story_order_reselect_and_bounds() -> None:
    game = default_story_game()
    assert game.select(0) == "selected"
    assert game.select(0) == "deselected"
    assert game.selected is None
    assert game.select(99) == "ignored"


def test_story_order_completed_ignores_input() -> None:
    game = StoryOrderGame(cards=["a", "b"], target_order=[0, 1], order=[0, 1])
    assert game.finished
    assert game.select(0) == "finished"
