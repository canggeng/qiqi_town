# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：onedir + windowed。"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

ROOT = Path(SPECPATH).resolve().parent

datas = [
    (str(ROOT / "src" / "qiqi_town" / "data"), "data"),
    (str(ROOT / "src" / "qiqi_town" / "assets"), "assets"),
]
datas += collect_data_files("panda3d")
binaries = collect_dynamic_libs("panda3d")

a = Analysis(
    [str(ROOT / "src" / "qiqi_town" / "__main__.py")],
    pathex=[str(ROOT / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        "direct.gui.OnscreenText",
        "direct.gui.DirectGui",
        "direct.gui.DirectGuiGlobals",
        "direct.showbase.ShowBase",
        "direct.showbase.ShowBaseGlobal",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="QiqiTown",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="QiqiTown",
)
