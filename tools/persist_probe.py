from __future__ import annotations

import sys

from qiqi_town.core.save_repository import SaveRepository
from qiqi_town.core.state import GameState


def main(mode: str) -> None:
    repo = SaveRepository()
    if mode == "save":
        state = GameState.new_game()
        state.day = 3
        state.time_minutes = 19 * 60 + 12
        state.playtime_seconds = 123.0
        repo.save_manual(7, state)
        print("root", repo.root)
        print("saved", repo.manual_path(7), repo.manual_path(7).exists())
    else:
        print("root", repo.root)
        slots = repo.list_slots()
        print("slot7", slots[6].exists, slots[6].available, slots[6].meta.day if slots[6].meta else None)


if __name__ == "__main__":
    main(sys.argv[1])
