"""用户设置：音量、文字速度、镜头灵敏度、窗口模式。"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from qiqi_town.paths import settings_path


@dataclass
class Settings:
    master_volume: float = 0.8
    music_volume: float = 0.6
    sfx_volume: float = 0.8
    text_speed: float = 35.0
    camera_sensitivity: float = 1.0
    window_width: int = 1600
    window_height: int = 900
    fullscreen: bool = False
    tutorial_hints: bool = True

    @classmethod
    def from_dict(cls, raw: Any) -> Settings:
        if not isinstance(raw, dict):
            return cls()
        return cls(
            master_volume=_clamp(raw.get("master_volume"), 0.0, 1.0, 0.8),
            music_volume=_clamp(raw.get("music_volume"), 0.0, 1.0, 0.6),
            sfx_volume=_clamp(raw.get("sfx_volume"), 0.0, 1.0, 0.8),
            text_speed=_clamp(raw.get("text_speed"), 5.0, 120.0, 35.0),
            camera_sensitivity=_clamp(raw.get("camera_sensitivity"), 0.2, 3.0, 1.0),
            window_width=max(1280, _safe_int(raw.get("window_width"), 1600)),
            window_height=max(720, _safe_int(raw.get("window_height"), 900)),
            fullscreen=bool(raw.get("fullscreen", False)),
            tutorial_hints=bool(raw.get("tutorial_hints", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SettingsRepository:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else settings_path()

    def load(self) -> Settings:
        if not self.path.exists():
            return Settings()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return Settings()
        return Settings.from_dict(raw)

    def save(self, settings: Settings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            tmp.write_text(
                json.dumps(settings.to_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            os.replace(tmp, self.path)
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass


def _safe_int(raw: Any, default: int) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _clamp(raw: Any, low: float, high: float, default: float) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, value))
