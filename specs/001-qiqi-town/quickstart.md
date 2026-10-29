# 快速开始

## 环境

```powershell
uv sync
uv run qiqi-town
```

首次同步会创建 `.venv` 并安装 Panda3D。所有依赖均在项目内。

## 冒烟测试

```powershell
uv run pytest
uv run qiqi-town --smoke-test
```

`--smoke-test` 会构建场景、渲染若干帧、保存 `build/smoke.png` 并退出；用于开发与打包后的快速检查。

## 打包

```powershell
powershell -ExecutionPolicy Bypass -File tools/build.ps1
```

输出：`dist/QiqiTown/QiqiTown.exe` 和 `dist/QiqiTown_v0.1.0_windows_x64.zip`（版本号以脚本为准）。

## 存档

- `%APPDATA%\QiqiTown\saves\slot_01.json` … `slot_20.json`
- `%APPDATA%\QiqiTown\saves\autosave.json`
- 设置：`%APPDATA%\QiqiTown\settings.json`

删除整个 `QiqiTown` 目录可重置所有存档与设置。

## 开发约定

1. 先改规格/数据，再改实现。
2. 纯逻辑（存档、时间、导航、条件、小游戏计分）必须有单元测试。
3. 每完成一个里程碑更新 `specs/001-qiqi-town/tasks.md`。
4. 中文文本统一使用 `ui.theme` 中的字体与换行工具。
