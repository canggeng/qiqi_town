from qiqi_town.systems.minigames.find_game import default_find_game


def test_find_game_collect_all() -> None:
    game = default_find_game()
    game.start()
    assert game.active
    for target_id in list(game.targets):
        result = game.collect(target_id)
    assert game.finished
    assert len(game.found) == 5
    assert result == "complete"


def test_find_game_invalid_and_inactive() -> None:
    game = default_find_game()
    assert game.collect("fountain") == "inactive"
    game.start()
    assert game.collect("missing") == "invalid"
    assert game.collect("fountain") == "collected"
    assert game.collect("fountain") == "invalid"
