"""资源路径与应用数据目录。

开发态从包目录读取；PyInstaller 打包态从 sys._MEIPASS 读取。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "QiqiTown"


def resource_root() -> Path:
    """返回包内资源根目录。"""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


def assets_dir() -> Path:
    return resource_root() / "assets"


def data_dir() -> Path:
    return resource_root() / "data"


def app_data_root() -> Path:
    """存档与设置根目录。

    测试可通过 QIQI_TOWN_DATA_DIR 指向临时目录。
    优先级：环境变量 > %APPDATA% > %LOCALAPPDATA% > 用户目录。
    不会回退到当前工作目录：从不同文件夹启动游戏时，cwd 会变化，
    导致下一次启动看起来“存档为空”。
    """
    override = os.environ.get("QIQI_TOWN_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()

    candidates: list[Path] = []
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(Path(appdata))
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        candidates.append(Path(localappdata))
    candidates.append(Path.home())
    if getattr(sys, "frozen", False):
        # 便携包在极端权限环境下，仍使用 exe 所在目录，保证路径稳定。
        candidates.append(Path(sys.executable).resolve().parent)

    for base in candidates:
        try:
            root = base / APP_DIR_NAME
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return root
        except OSError:
            continue
    # 稳定兜底：仍放在用户目录，而不是随 cwd 漂移。
    return Path.home() / APP_DIR_NAME


def legacy_save_dirs() -> list[Path]:
    """旧版本可能把存档写在 cwd 或 exe 旁边，用于首次启动迁移。"""
    dirs: list[Path] = []
    exe_dir = Path(sys.executable).resolve().parent
    for root in (
        Path.cwd() / APP_DIR_NAME / "saves",
        exe_dir / APP_DIR_NAME / "saves",
        exe_dir / "saves",
    ):
        if root not in dirs:
            dirs.append(root)
    return dirs


def saves_dir() -> Path:
    root = app_data_root() / "saves"
    root.mkdir(parents=True, exist_ok=True)
    return root


def settings_path() -> Path:
    return app_data_root() / "settings.json"


def logs_dir() -> Path:
    root = app_data_root() / "logs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def build_dir() -> Path:
    """开发期截图/临时输出目录，不写入安装包。"""
    root = Path.cwd() / "build"
    root.mkdir(parents=True, exist_ok=True)
    return root
