from qiqi_town.systems.daily_content import GAME_SLOTS, slot_by_id, slot_for, slots_for_day


def test_each_day_has_three_unique_games() -> None:
    for day in range(1, 6):
        slots = slots_for_day(day)
        assert len(slots) == 3
        assert len({slot.id for slot in slots}) == 3
        assert len({slot.kind for slot in slots}) == 3


def test_all_slots_unique_and_reachable() -> None:
    ids = [slot.id for slot in GAME_SLOTS]
    assert len(ids) == 15
    assert len(set(ids)) == 15
    for slot in GAME_SLOTS:
        assert slot_by_id(slot.id) == slot
        assert slot_for(slot.day, slot.kind) == slot
