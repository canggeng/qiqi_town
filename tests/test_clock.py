from qiqi_town.config import DAY_END_MINUTE, DAY_START_MINUTE
from qiqi_town.core.clock import GameClock


def test_clock_starts_at_eight_and_advances() -> None:
    clock = GameClock()
    assert clock.display_time == "08:00"
    clock.tick(60)
    assert clock.display_time == "09:00"
    assert clock.phase == "morning"


def test_clock_caps_at_end() -> None:
    clock = GameClock(minutes=DAY_END_MINUTE - 1)
    clock.tick(1000)
    assert clock.minutes == DAY_END_MINUTE
    assert clock.at_end
    assert clock.phase == "dusk"


def test_clock_pause() -> None:
    clock = GameClock(paused=True)
    clock.tick(100)
    assert clock.minutes == DAY_START_MINUTE


def test_advance_day() -> None:
    clock = GameClock(day=1, minutes=900)
    assert clock.advance_day() is True
    assert clock.day == 2
    assert clock.minutes == DAY_START_MINUTE
    clock.day = 5
    assert clock.advance_day() is False
    assert clock.day == 5


def test_phase_boundaries() -> None:
    assert GameClock(minutes=11 * 60 + 59).phase == "morning"
    assert GameClock(minutes=12 * 60).phase == "afternoon"
    assert GameClock(minutes=17 * 60).phase == "dusk"
