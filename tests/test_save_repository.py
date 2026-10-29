import json

import pytest

from qiqi_town.core.save_repository import SaveError, SaveErrorCode, SaveRepository
from qiqi_town.core.state import GameState


def _state(day: int = 1) -> GameState:
    state = GameState.new_game()
    state.day = day
    state.time_minutes = 8 * 60 + day
    state.playtime_seconds = 12.5
    return state


def test_save_and_load_manual(work_dir) -> None:
    repo = SaveRepository(work_dir)
    meta = repo.save_manual(3, _state(2))
    assert meta.slot == 3
    assert meta.day == 2
    loaded = repo.load_manual(3)
    assert loaded.day == 2
    assert loaded.playtime_seconds == 12.5
    slots = repo.list_slots()
    assert len(slots) == 20
    assert slots[2].available
    assert slots[0].exists is False


def test_save_all_20_and_reject_21(work_dir) -> None:
    repo = SaveRepository(work_dir)
    for slot in range(1, 21):
        repo.save_manual(slot, _state((slot % 5) + 1))
    with pytest.raises(SaveError) as exc:
        repo.save_manual(21, _state())
    assert exc.value.code == SaveErrorCode.INVALID
    assert repo.count_manual() == 20


def test_auto_does_not_count_as_manual(work_dir) -> None:
    repo = SaveRepository(work_dir)
    repo.save_auto(_state(2))
    for slot in range(1, 21):
        repo.save_manual(slot, _state(1))
    assert repo.count_manual() == 20
    auto = repo.load_auto()
    assert auto.day == 2
    assert repo.auto_path.exists()


def test_overwrite_creates_backup(work_dir) -> None:
    repo = SaveRepository(work_dir)
    repo.save_manual(1, _state(1))
    repo.save_manual(1, _state(4))
    backup = repo.manual_path(1).with_suffix(".json.bak")
    assert backup.exists()
    assert repo.load_manual(1).day == 4


def test_corrupt_save_is_reported_not_deleted(work_dir) -> None:
    repo = SaveRepository(work_dir)
    path = repo.manual_path(2)
    path.write_text("{ not json", encoding="utf-8")
    slots = repo.list_slots()
    assert slots[1].exists is True
    assert slots[1].error is not None
    with pytest.raises(SaveError) as exc:
        repo.load_manual(2)
    assert exc.value.code == SaveErrorCode.CORRUPT
    assert path.exists()


def test_version_too_new(work_dir) -> None:
    repo = SaveRepository(work_dir)
    path = repo.manual_path(2)
    path.write_text(
        json.dumps({"schema_version": 99, "meta": {}, "state": {}}), encoding="utf-8"
    )
    with pytest.raises(SaveError) as exc:
        repo.load_manual(2)
    assert exc.value.code == SaveErrorCode.VERSION


def test_latest_prefers_newest(work_dir) -> None:
    repo = SaveRepository(work_dir)
    old = repo.save_manual(1, _state(1))
    repo.save_manual(2, _state(3))
    latest = repo.latest()
    assert latest is not None
    assert latest.slot == 2
    assert latest.meta is not None
    assert latest.meta.day == 3
    assert old.saved_at


def test_delete(work_dir) -> None:
    repo = SaveRepository(work_dir)
    repo.save_manual(1, _state())
    repo.delete_manual(1)
    assert not repo.manual_path(1).exists()
    assert repo.latest() is None
