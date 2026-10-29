"""音频系统：原创轻音乐、环境音与交互音效。"""

from __future__ import annotations

import logging
from pathlib import Path

from panda3d.core import Filename

from qiqi_town.core.settings import Settings
from qiqi_town.paths import assets_dir

log = logging.getLogger(__name__)


class AudioSystem:
    def __init__(self, base, settings: Settings) -> None:
        self.base = base
        self.settings = settings
        self.manager = None
        if getattr(base, "sfxManagerList", None):
            self.manager = base.sfxManagerList[0]
        self.music: dict[str, object] = {}
        self.sfx: dict[str, object] = {}
        self._music_sound = None
        self._ambient_sound = None
        self._current_music = ""
        self._current_ambient = ""
        self._load_assets()
        self.set_volumes(
            settings.master_volume,
            settings.music_volume,
            settings.sfx_volume,
        )

    def _load_assets(self) -> None:
        root = assets_dir() / "audio"
        for name in (
            "town_day",
            "interior",
            "dusk",
        ):
            self.music[name] = self._load(root / f"{name}.wav")
        for name in ("ambience_town", "ambience_interior"):
            self.music[name] = self._load(root / f"{name}.wav")
        for path in root.glob("*.wav"):
            if path.stem in self.music:
                continue
            sound = self._load(path)
            if sound is not None:
                self.sfx[path.stem] = sound

    def _load(self, path: Path):
        if not path.exists() or not getattr(self.base, "loader", None):
            return None
        try:
            path_str = Filename.fromOsSpecific(str(path)).getFullpath()
            return self.base.loader.loadSfx(path_str)
        except Exception as exc:  # noqa: BLE001
            log.warning("音频加载失败 %s: %s", path, exc)
            return None

    @property
    def available(self) -> bool:
        return self.manager is not None and bool(self.music or self.sfx)

    def set_volumes(self, master: float, music: float, sfx: float) -> None:
        self.master = max(0.0, min(1.0, float(master)))
        self.music_volume = max(0.0, min(1.0, float(music)))
        self.sfx_volume = max(0.0, min(1.0, float(sfx)))
        if self._music_sound is not None:
            self._music_sound.setVolume(self.master * self.music_volume * 0.8)
        if self._ambient_sound is not None:
            self._ambient_sound.setVolume(self.master * self.music_volume * 0.55)

    def play_music(self, name: str) -> None:
        if name == self._current_music:
            return
        sound = self.music.get(name)
        if sound is None:
            return
        self.stop_music()
        try:
            sound.setLoop(True)
            sound.setVolume(self.master * self.music_volume * 0.8)
            sound.play()
            self._music_sound = sound
            self._current_music = name
        except Exception as exc:  # noqa: BLE001
            log.warning("音乐播放失败: %s", exc)

    def play_ambient(self, name: str) -> None:
        if name == self._current_ambient:
            return
        sound = self.music.get(name)
        if sound is None:
            return
        self.stop_ambient()
        try:
            sound.setLoop(True)
            sound.setVolume(self.master * self.music_volume * 0.55)
            sound.play()
            self._ambient_sound = sound
            self._current_ambient = name
        except Exception as exc:  # noqa: BLE001
            log.warning("环境音播放失败: %s", exc)

    def stop_music(self) -> None:
        if self._music_sound is not None:
            try:
                self._music_sound.stop()
            except Exception as exc:  # noqa: BLE001
                log.debug("停止音乐失败: %s", exc)
        self._music_sound = None
        self._current_music = ""

    def stop_ambient(self) -> None:
        if self._ambient_sound is not None:
            try:
                self._ambient_sound.stop()
            except Exception as exc:  # noqa: BLE001
                log.debug("停止环境音失败: %s", exc)
        self._ambient_sound = None
        self._current_ambient = ""

    def play_sfx(self, name: str, *, volume: float = 1.0) -> None:
        sound = self.sfx.get(name)
        if sound is None:
            return
        try:
            sound.setVolume(self.master * self.sfx_volume * volume)
            sound.play()
        except Exception as exc:  # noqa: BLE001
            log.debug("音效播放失败 %s: %s", name, exc)

    def stop_all(self) -> None:
        self.stop_music()
        self.stop_ambient()
