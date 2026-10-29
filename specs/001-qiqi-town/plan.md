# 技术计划：淇淇的小镇

**Spec**: `specs/001-qiqi-town/spec.md`  
**Constitution**: `.specify/memory/constitution.md`  
**Knowledge**: `docs/PROJECT_KNOWLEDGE.md`

## 1. 技术背景

- Windows 10/11 x64，鼠标可用。
- Python 3.14.3（系统已有），uv 0.13.6。
- Panda3D 1.10.16（已验证有 CPython 3.14 Windows 轮子）。
- PyInstaller 6.22.3（已验证与 Python 3.14 兼容）。
- 目标：离线单机、无管理员权限、中文界面。

## 2. 架构

```
Panda3D ShowBase
└─ QiqiTownApp
   ├─ GameState（纯数据）
   ├─ SceneManager（室外 / 家 / 幼儿园 / 图书馆）
   ├─ UIRouter（标题 / HUD / 暂停 / 存档 / 对话 / 日记 / 设置）
   ├─ Systems
   │  ├─ InputSystem / InteractionSystem
   │  ├─ TimeSystem / ScheduleSystem
   │  ├─ DialogueRunner / QuestSystem / EventDirector
   │  ├─ SaveRepository
   │  └─ AudioSystem
   └─ World
      ├─ TownBuilder / InteriorBuilder
      ├─ Terrain / NavGrid
      ├─ CharacterBuilder（淇淇/NPC）
      └─ CameraRig
```

数据流：鼠标/UI → `InteractionSystem`/`UIRouter` → 状态变更 → `GameState` → 事件/任务/对话 → 自动存档/UI 刷新。
存档只读写 `GameState` 与 `SaveMeta`，不触碰 Panda3D 节点。

## 3. 坐标与尺度

- Panda3D 使用 **Z 向上、Y 向前**。地面坐标为 `(x, y)`，高度 `z` 由地形函数或场景固定高度给出。
- 1 个世界单位 = 1 米。
- 小镇 140×140 米；淇淇身高约 1.05 米；建筑门高约 1.9 米。
- 相机距离 4–9 米，俯角 20–55°，室内自动缩短。
- 保存的玩家位置为 `x, y` 与朝向角度；加载时重新投影到地面。

## 4. 技术决策

| 决策 | 选择 | 理由 |
|---|---|---|
| 3D 引擎 | Panda3D | Python 原生、轮子可用、打包可控、无需编辑器 |
| 角色/场景 | 程序化几何体 | 不依赖外部资产、风格统一、可版本管理 |
| UI | Panda3D DirectGUI + 自定义主题/生成纹理 | 不引入额外 UI 框架 |
| 导航 | 0.5m 网格 + A* + 视线平滑 | 比导航网格简单，足够小镇尺度 |
| 地形 | 函数式高度 + 网格采样 | 角色高度、寻路和视觉使用同一数据源 |
| 存档 | JSON + 原子写 + `.bak` | 可调试、易测试、适合小体量 |
| 剧情 | JSON 数据 + 条件/效果求值器 | 内容与代码分离 |
| 小游戏 | 6 个 Python 类 + JSON 参数 | 15 次安排复用 |
| 打包 | PyInstaller onedir | 启动快、Panda3D 兼容性更稳 |
| 字体 | OFL 字体 + CJK 换行器 | 可分发、中文稳定 |

## 5. 模块与职责

### `core/state.py`
`GameState`、`PlayerState`、`QuestState`、`FriendshipState` 等 dataclass；JSON 往返与校验。

### `core/save_repository.py`
20 个手动槽 + 自动槽；列出元数据、保存、读取、删除；原子写；损坏检测；路径回退。

### `core/clock.py`
08:00–20:00 的时间推进、暂停、阶段（morning/afternoon/dusk）、天数切换。

### `core/events.py`
条件 DSL：`all`、`any`、`flag`、`day`、`time`、`friendship`、`sticker`、`location`；效果：旗标、友谊、贴纸、日记、任务步骤、小游戏、音效、UI。

### `world/meshkit.py`
盒子、UV 球、圆柱、圆锥、平面、环形、文字贴图等；支持顶点色和简单材质。

### `world/character_builder.py`
淇淇/NPC 程序化拼装、气球节点、表情切换、动画状态。

### `world/nav.py`
`NavGrid`：可走性、A*、最近可走点、路径平滑。

### `world/town.py` / `interiors.py`
程序化搭建中心广场、家、幼儿园、图书馆、公园、游乐场、山道；交互物和碰撞体注册。

### `entities/player.py`
行走、转向、路径跟随、高度贴合、动画状态。

### `entities/camera_rig.py`
跟随、右键旋转、滚轮缩放、碰撞回退。

### `systems/interaction.py`
鼠标拾取、悬停高亮、点击地面/物体、走到交互点后触发、UI 拦截。

### `systems/dialogue.py`
对话节点运行、逐字显示、选项、效果。

### `systems/quests.py`
5 个每日主线，步骤完成条件、奖励、解锁睡觉。

### `systems/minigames/`
6 套小游戏，共用 `MinigameSession` 接口；奖励与日记接入。

### `ui/`
主题、通用控件、路由、标题/HUD/暂停/存档/日记/设置/结局。

## 6. 存档契约

- 路径：`%APPDATA%\QiqiTown\saves`；回退 `%LOCALAPPDATA%\QiqiTown\saves`。
- 文件：`slot_01.json` … `slot_20.json`，`autosave.json`，`settings.json`。
- 元数据在存档顶层 `meta`，状态在 `state`。
- `schema_version` 当前为 `1`。
- 写入：`tmp` → 校验 → `.bak` → `os.replace`。
- 读取：JSON 解析失败或校验失败 → 返回错误，不删除原文件。
- 20 个手动档上限在 UI 和仓库两层强制。

## 7. 打包

- `tools/build.ps1`：`uv sync --frozen` → `uv run pytest` → `uv run pyinstaller tools/qiqi_town.spec` → 冒烟 → zip。
- `qiqi_town.spec`：
  - `datas`：`src/qiqi_town/assets`、`src/qiqi_town/data`、字体、音频、文档。
  - `hiddenimports`：Panda3D 必要模块（根据 M0 实际）。
  - `windowed=True`，图标 `build/qiqi.ico`。
  - 输出 `dist/QiqiTown/QiqiTown.exe`。
- `paths.py` 在 frozen 时使用 `sys._MEIPASS`。
- 验收：清空 `PYTHONHOME`/`PYTHONPATH`，仅保留系统 PATH，从 `dist` 启动 `--smoke-test`。

## 8. 里程碑

| 阶段 | 交付 | 门禁 |
|---|---|---|
| M0 技术纵切 | 窗口、点击寻路、相机、中文文本、角色灰模、存档 | exe 冒烟通过，灰模可辨 |
| M1 基础框架 | 状态机、UI 路由、存档界面、设置、标题/暂停 | 20+1 存档测试通过 |
| M2 小镇世界 | 室外/三个室内、角色、NPC、导航、交互 | 可自由走动、进出、对话 |
| M3 内容 | 5 天、15 小游戏、20 贴纸、事件、结局 | 完整通关 |
| M4 打磨 | 音频、表情、粒子、教程、性能 | 60 FPS 目标 |
| M5 交付 | exe、README、CREDITS、验收 | 无 Python 可运行 |

## 9. 风险与缓解

- **Panda3D 打包**：M0 先验证；必要时自定义 hook；回退 Python 3.13。
- **中文排版**：早期用真实对话测试 CJK 换行；统一文本组件。
- **角色还原**：M0 灰模对照；M2 上色截图对照；接受“低多边形演绎”而非写实。
- **导航/山道**：先做平地，再让山道坡度 ≤35°；点击无效时给反馈。
- **范围**：6 套小游戏复用；不增加独立玩法；每日内容用数据驱动。
- **音频授权**：只收录有清晰授权的素材；无授权则不发布该素材。

## 10. 质量门禁

- 每个里程碑运行 `uv run pytest` 与 `uv run qiqi-town --smoke-test`。
- 每个里程碑保留截图/日志。
- 完整通关清单见 `specs/001-qiqi-town/tasks.md` 的验收部分。
