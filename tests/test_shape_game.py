from qiqi_town.systems.minigames.shape_match import default_shape_game


def test_shape_game_complete() -> None:
    game = default_shape_game()
    assert not game.finished
    assert game.select_item("red_circle")
    assert game.choose_slot("circle") == "correct"
    assert game.select_item("blue_square")
    assert game.choose_slot("square") == "correct"
    assert game.select_item("yellow_triangle")
    assert game.choose_slot("triangle") == "correct"
    assert game.finished
    assert len(game.matched) == 3


def test_shape_game_wrong_choice_keeps_playing() -> None:
    game = default_shape_game()
    game.select_item("red_circle")
    assert game.choose_slot("square") == "wrong"
    assert game.mistakes == 1
    assert game.selected == "red_circle"
    assert not game.finished


def test_shape_game_requires_selection() -> None:
    game = default_shape_game()
    assert game.choose_slot("circle") == "ignored"
    assert not game.select_item("missing")
    assert game.select_item("red_circle")
    assert game.select_item("blue_square")
    assert game.selected == "blue_square"
