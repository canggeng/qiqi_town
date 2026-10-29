"""存档仓库：20 个手动档 + 1 个自动档。

纯 Python，不依赖 Panda3D，便于无窗口测试。
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from qiqi_town.config import (
    DAY_TITLES,
    LOCATION_LABELS,
    SAVE_SCHEMA_VERSION,
    SAVE_SLOT_COUNT,
)
from qiqi_town.core.state import GameState
from qiqi_town.paths import app_data_root


class SaveErrorCode(str, Enum):
    IO = "io"
    CORRUPT = "corrupt"
    VERSION = "version"
    FULL = "full"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


class SaveError(Exception):
    def __init__(self, code: SaveErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class SaveMeta:
    slot: int
    is_auto: bool
    saved_at: str
    playtime_seconds: float
    day: int
    time_minutes: int
    location_label: str
    quest_title: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot": int(self.slot),
            "is_auto": bool(self.is_auto),
            "saved_at": self.saved_at,
            "playtime_seconds": round(float(self.playtime_seconds), 2),
            "day": int(self.day),
            "time_minutes": int(self.time_minutes),
            "location_label": self.location_label,
            "quest_title": self.quest_title,
        }

    @classmethod
    def from_dict(cls, raw: Any, *, fallback_slot: int = 0) -> SaveMeta:
        if not isinstance(raw, dict):
            raise SaveError(SaveErrorCode.CORRUPT, "存档 meta 不是对象")
        slot = _safe_int(raw.get("slot"), fallback_slot)
        day = max(1, min(5, _safe_int(raw.get("day"), 1)))
        time_minutes = max(0, min(24 * 60, _safe_int(raw.get("time_minutes"), 8 * 60)))
        return cls(
            slot=slot,
            is_auto=bool(raw.get("is_auto", False)),
            saved_at=str(raw.get("saved_at") or ""),
            playtime_seconds=max(0.0, _safe_float(raw.get("playtime_seconds"), 0.0)),
            day=day,
            time_minutes=time_minutes,
            location_label=str(raw.get("location_label") or ""),
            quest_title=str(raw.get("quest_title") or DAY_TITLES.get(day, "")),
        )

    @property
    def display_time(self) -> str:
        return f"{self.time_minutes // 60:02d}:{self.time_minutes % 60:02d}"


@dataclass
class SaveSlotInfo:
    slot: int
    is_auto: bool
    exists: bool
    meta: SaveMeta | None = None
    error: str | None = None

    @property
    def available(self) -> bool:
        return self.exists and self.meta is not None and self.error is None


class SaveRepository:
    def __init__(self, root: Path | None = None, slot_count: int = SAVE_SLOT_COUNT) -> None:
        self.root = Path(root) if root is not None else app_data_root()
        self.slot_count = int(slot_count)
        self.saves_dir = self.root / "saves"
        self.saves_dir.mkdir(parents=True, exist_ok=True)

    # ---- paths ---------------------------------------------------------
    def manual_path(self, slot: int) -> Path:
        self._validate_slot(slot)
        return self.saves_dir / f"slot_{slot:02d}.json"

    @property
    def auto_path(self) -> Path:
        return self.saves_dir / "autosave.json"

    @staticmethod
    def _validate_slot(slot: int) -> None:
        if not 1 <= int(slot) <= SAVE_SLOT_COUNT:
            raise SaveError(SaveErrorCode.INVALID, f"存档槽位必须在 1–{SAVE_SLOT_COUNT}")

    # ---- list ----------------------------------------------------------
    def list_slots(self) -> list[SaveSlotInfo]:
        infos: list[SaveSlotInfo] = []
        for slot in range(1, self.slot_count + 1):
            path = self.manual_path(slot)
            infos.append(self._inspect(path, slot=slot, is_auto=False))
        return infos

    def list_all(self) -> list[SaveSlotInfo]:
        return [self._inspect(self.auto_path, slot=0, is_auto=True), *self.list_slots()]

    def _inspect(self, path: Path, *, slot: int, is_auto: bool) -> SaveSlotInfo:
        if not path.exists():
            return SaveSlotInfo(slot=slot, is_auto=is_auto, exists=False)
        try:
            meta = self._read_meta(path, fallback_slot=slot)
            meta.slot = slot
            meta.is_auto = is_auto
            return SaveSlotInfo(slot=slot, is_auto=is_auto, exists=True, meta=meta)
        except SaveError as exc:
            return SaveSlotInfo(slot=slot, is_auto=is_auto, exists=True, error=exc.message)
        except OSError as exc:
            return SaveSlotInfo(
                slot=slot, is_auto=is_auto, exists=True, error=f"无法读取：{exc}"
            )

    def count_manual(self) -> int:
        return sum(1 for path in self.saves_dir.glob("slot_*.json") if path.is_file())

    def has_any(self) -> bool:
        return self.auto_path.exists() or self.count_manual() > 0

    def latest(self) -> SaveSlotInfo | None:
        candidates: list[SaveSlotInfo] = []
        auto = self._inspect(self.auto_path, slot=0, is_auto=True)
        if auto.available:
            candidates.append(auto)
        for slot in self.list_slots():
            if slot.available:
                candidates.append(slot)
        if not candidates:
            return None

        def sort_key(info: SaveSlotInfo) -> tuple[float, float]:
            meta = info.meta
            assert meta is not None
            try:
                parsed = datetime.fromisoformat(meta.saved_at).timestamp()
            except (TypeError, ValueError):
                parsed = 0.0
            path = self.auto_path if info.is_auto else self.manual_path(info.slot)
            try:
                mtime = path.stat().st_mtime
            except OSError:
                mtime = 0.0
            return parsed, mtime

        return max(candidates, key=sort_key)

    # ---- save ----------------------------------------------------------
    def save_manual(self, slot: int, state: GameState) -> SaveMeta:
        self._validate_slot(slot)
        path = self.manual_path(slot)
        meta = self._make_meta(slot=slot, is_auto=False, state=state)
        self._write(path, state, meta)
        return meta

    def save_auto(self, state: GameState) -> SaveMeta:
        meta = self._make_meta(slot=0, is_auto=True, state=state)
        self._write(self.auto_path, state, meta)
        return meta

    def _make_meta(self, *, slot: int, is_auto: bool, state: GameState) -> SaveMeta:
        return SaveMeta(
            slot=slot,
            is_auto=is_auto,
            saved_at=datetime.now().astimezone().isoformat(timespec="microseconds"),
            playtime_seconds=state.playtime_seconds,
            day=state.day,
            time_minutes=state.time_minutes,
            location_label=LOCATION_LABELS.get(state.location, state.location),
            quest_title=DAY_TITLES.get(state.day, ""),
        )

    def _write(self, path: Path, state: GameState, meta: SaveMeta) -> None:
        payload = {
            "schema_version": SAVE_SCHEMA_VERSION,
            "meta": meta.to_dict(),
            "state": state.to_dict(),
        }
        tmp = path.with_suffix(path.suffix + ".tmp")
        try:
            tmp.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            # 先重新解析临时文件，确认写入内容是完整 JSON。
            json.loads(tmp.read_text(encoding="utf-8"))
            if path.exists():
                shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
            os.replace(tmp, path)
        except OSError as exc:
            self._safe_unlink(tmp)
            raise SaveError(SaveErrorCode.IO, f"写入存档失败：{exc}") from exc
        except json.JSONDecodeError as exc:
            self._safe_unlink(tmp)
            raise SaveError(SaveErrorCode.CORRUPT, "写入校验失败") from exc

    # ---- load ----------------------------------------------------------
    def load_manual(self, slot: int) -> GameState:
        self._validate_slot(slot)
        return self._load(self.manual_path(slot))

    def load_auto(self) -> GameState:
        return self._load(self.auto_path)

    def load(self, slot: int | str) -> GameState:
        if slot == "auto":
            return self.load_auto()
        return self.load_manual(int(slot))

    def _load(self, path: Path) -> GameState:
        if not path.exists():
            raise SaveError(SaveErrorCode.NOT_FOUND, "存档不存在")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise SaveError(SaveErrorCode.IO, f"无法读取存档：{exc}") from exc
        except json.JSONDecodeError as exc:
            raise SaveError(SaveErrorCode.CORRUPT, "存档不是有效的 JSON") from exc
        if not isinstance(raw, dict):
            raise SaveError(SaveErrorCode.CORRUPT, "存档根节点不是对象")
        version = _safe_int(raw.get("schema_version"), 0)
        if version > SAVE_SCHEMA_VERSION:
            raise SaveError(SaveErrorCode.VERSION, "存档版本高于当前游戏版本")
        state_raw = raw.get("state")
        if not isinstance(state_raw, dict):
            raise SaveError(SaveErrorCode.CORRUPT, "存档缺少 state")
        try:
            state = GameState.from_dict(state_raw)
        except (TypeError, ValueError) as exc:
            raise SaveError(SaveErrorCode.CORRUPT, f"存档状态无效：{exc}") from exc
        state.schema_version = version or SAVE_SCHEMA_VERSION
        return state

    def _read_meta(self, path: Path, *, fallback_slot: int) -> SaveMeta:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise SaveError(SaveErrorCode.IO, f"无法读取存档：{exc}") from exc
        except json.JSONDecodeError as exc:
            raise SaveError(SaveErrorCode.CORRUPT, "存档不是有效的 JSON") from exc
        if not isinstance(raw, dict):
            raise SaveError(SaveErrorCode.CORRUPT, "存档根节点不是对象")
        version = _safe_int(raw.get("schema_version"), 0)
        if version > SAVE_SCHEMA_VERSION:
            raise SaveError(SaveErrorCode.VERSION, "存档版本过高")
        meta_raw = raw.get("meta")
        if not isinstance(meta_raw, dict):
            raise SaveError(SaveErrorCode.CORRUPT, "存档缺少 meta")
        return SaveMeta.from_dict(meta_raw, fallback_slot=fallback_slot)

    # ---- delete --------------------------------------------------------
    def delete_manual(self, slot: int) -> None:
        self._validate_slot(slot)
        path = self.manual_path(slot)
        if not path.exists():
            raise SaveError(SaveErrorCode.NOT_FOUND, "存档不存在")
        try:
            path.unlink()
            backup = path.with_suffix(path.suffix + ".bak")
            if backup.exists():
                backup.unlink()
        except OSError as exc:
            raise SaveError(SaveErrorCode.IO, f"删除存档失败：{exc}") from exc

    @staticmethod
    def _safe_unlink(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def _safe_int(raw: Any, default: int) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _safe_float(raw: Any, default: float) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default
