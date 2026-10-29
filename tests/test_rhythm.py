from qiqi_town.systems.minigames.rhythm import RhythmGame


def test_rhythm_hit_in_zone() -> None:
    game = RhythmGame(position=0.6)
    assert game.in_zone
    assert game.hit() == "hit"
    assert game.hits == 1


def test_rhythm_miss_outside_zone() -> None:
    game = RhythmGame(position=0.1)
    assert not game.in_zone
    assert game.hit() == "miss"
    assert game.misses == 1


def test_rhythm_bounces_and_finishes() -> None:
    game = RhythmGame(position=0.95, direction=1.0, speed=1.0)
    game.update(0.2)
    assert 0.0 <= game.position <= 1.0
    assert game.direction == -1.0
    game.hits = 5
    assert game.finished
    assert game.hit() == "finished"
