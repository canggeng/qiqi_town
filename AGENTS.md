# AGENTS.md

本文件是本项目对自动化开发代理和人类协作者的工程约定。

## 0. 不可妥协的开发方式：SDD + TDD

本项目使用 **SDD（Spec-Driven Development，规格驱动开发）** 与 **TDD（Test-Driven Development，测试驱动开发）** 组合开发。

### SDD：先写清楚，再实现

任何新功能、行为变化或缺陷修复，必须按以下顺序推进：

1. 阅读 `.specify/memory/constitution.md` 和 `docs/PROJECT_KNOWLEDGE.md`，确认没有违反项目原则。
2. 在 `specs/001-qiqi-town/spec.md` 中确认或补充用户场景、功能需求、验收标准。
3. 在 `specs/001-qiqi-town/plan.md`、`data-model.md` 或对应 `contracts/*.md` 中确认技术方案、数据结构和契约。
4. 在 `specs/001-qiqi-town/tasks.md` 中登记任务，明确测试方式和验收方式。
5. 先写测试，再写实现；实现过程中同步更新文档。
6. 完成后更新 `research.md`（如果产生了重要技术结论）、`quickstart.md`（如果改变了使用方式）和 `CHANGELOG.md`。

**规格是事实来源。** 如果实现与规格不一致，必须二选一：修正实现，或先更新规格并说明原因。禁止“代码已经这样了，所以规格就算了”。

### TDD：先红，再绿，再重构

对任何可测试的逻辑，必须遵循：

1. **Red**：先写一个会失败的测试，确认它确实失败。
2. **Green**：写最少的生产代码让测试通过。
3. **Refactor**：在测试保护下整理代码，不改变行为。

适用对象包括但不限于：

- 存档读写、迁移、损坏保护；
- 对话条件/效果、旗标、友谊；
- 主线推进、每日排期、奖励；
- 小游戏纯逻辑；
- 导航、朝向、鼠标射线、时间推进；
- 设置持久化。

对于纯视觉/资源类变更（颜色、模型摆放、圆角贴图、字体大小），如果不能写有意义的单元测试，必须：

- 通过 `uv run qiqi-town --smoke-test` 生成截图；
- 在交付说明中注明已检查的截图；
- 在 `tasks.md` 中登记人工验收项。

**没有测试、没有截图验证、也没有登记人工验收的实现，不算完成。**

## 1. 项目概览

- 游戏：5 岁的淇淇在青禾镇度过灯会前的五天。
- 技术栈：Python 3.14、Panda3D 1.10.16、DirectGUI。
- 平台：Windows 10/11 x64。
- 交付：PyInstaller `onedir` 免安装文件夹 + `QiqiTown.exe`。
- 内容：5 天主线、每天 3 个小游戏、12 个环境事件、20 张回忆贴纸、20+1 存档、原创音频、鼠标全流程操作。

## 2. 环境与命令

所有 Python 命令必须通过项目内 `.venv` 和 `uv` 执行，禁止全局 `pip install`。

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.uv-cache'

uv sync --frozen
uv run ruff check src tests
uv run pytest
uv run qiqi-town --smoke-test
uv run qiqi-town --debug
uv run qiqi-town --windowed
```

构建交付包：

```powershell
powershell -ExecutionPolicy Bypass -File tools/build.ps1
```

构建脚本会依次执行测试、PyInstaller、exe 冒烟测试和 zip 打包。

### 测试环境注意事项

- 测试必须使用 `tests/conftest.py` 的 `work_dir` fixture，不要使用 `pytest` 的 `tmp_path`/`tmpdir`；Windows 沙箱下临时目录 ACL 可能不可写。
- `pyproject.toml` 已关闭 pytest cache 和 tmpdir 插件，不要随意移除。
- 测试数据目录用 `QIQI_TOWN_DATA_DIR` 指向项目内临时目录，禁止写入真实 `%APPDATA%`。
- 测试必须可重复、无网络、无窗口、无音频依赖。

## 3. 目录与职责边界

```text
src/qiqi_town/
  app.py                 # 应用编排、场景切换、交互和模式切换
  paths.py               # 资源与用户数据路径
  config.py              # 常量、调色板、UI 文案常量
  core/                  # 纯 Python：状态、时间、存档、设置
  systems/               # 对话、任务、小游戏、音频、教程、每日排期
  world/                 # 程序化场景、角色、导航、地形
  ui/                    # DirectGUI 界面、HUD、圆角贴图、夜间过渡
  data/                  # 对话、贴纸等数据文件
  assets/                # 字体、音频
tests/                   # pytest 单元/集成测试
specs/001-qiqi-town/     # SDD 规格、计划、契约、任务、研究
tools/                   # 构建、资源生成、运行时探针
```

职责约束：

- `core/` 不得依赖 Panda3D，必须能在无窗口环境下测试。
- `ui/` 只负责展示和输入转发，不得藏主线规则、奖励规则或存档规则。
- 对话文本、事件、小游戏配置优先放 `data/`；不要把剧情写死在 UI 里。
- `app.py` 可以编排，但复杂规则应下沉到 `systems/` 或 `core/`。
- 存档只序列化 `GameState`，绝不序列化 Panda3D 节点。

## 4. SDD 文档地图

| 文档 | 作用 | 何时更新 |
|---|---|---|
| `.specify/memory/constitution.md` | 项目不可妥协原则 | 原则变化时（很少） |
| `docs/PROJECT_KNOWLEDGE.md` | 世界观、角色、长期决策 | 角色/世界/技术约定变化时 |
| `specs/001-qiqi-town/spec.md` | 用户场景、功能需求、验收 | 新功能/行为变化前 |
| `specs/001-qiqi-town/plan.md` | 架构与技术方案 | 模块/技术决策变化时 |
| `specs/001-qiqi-town/data-model.md` | 状态、存档、对话、NPC 数据模型 | 字段/实体变化时 |
| `specs/001-qiqi-town/contracts/*.md` | CLI、存档、对话契约 | 契约变化时 |
| `specs/001-qiqi-town/tasks.md` | 任务分解和完成状态 | 开始/完成任务时 |
| `specs/001-qiqi-town/research.md` | 技术验证结论 | 产生新结论时 |
| `specs/001-qiqi-town/quickstart.md` | 运行/试玩说明 | 操作方式变化时 |
| `CHANGELOG.md` | 版本更新记录 | 每次 Git 上传前 |

规格、计划、契约和任务之间必须保持一致。不要只改代码不改文档。

## 5. 测试策略

### 单元测试

放在 `tests/test_*.py`，覆盖纯逻辑：

- `test_save_repository.py`：20+1 存档、损坏、版本、迁移；
- `test_dialogue.py` / `test_events.py` / `test_children.py` / `test_mom.py`：对话与效果；
- `test_daily_content.py`：每天 3 个小游戏、15 次排期；
- `test_nav.py`：寻路与可走性；
- `test_*_game.py`：各小游戏纯逻辑；
- `test_clock.py` / `test_state.py`：时间与状态。

### 运行时探针

`tools/` 下的探针用于覆盖不适合普通 pytest 的 Panda3D 行为：

- `runtime_probe.py`：小游戏启动/结束；
- `full_flow_probe.py`：五天主线、夜间过渡、存档；
- `click_probe.py`：鼠标屏幕坐标到地面；
- `heading_probe.py`：角色朝向；
- `night_probe.py`：夜间过渡截图；
- `fullscreen_probe.py`：无边框全屏；
- `persist_probe.py`：跨进程存档持久化。

探针需要写入项目内 `.smoke-data-*` 或 `.test-tmp`，不得污染真实存档。

### 冒烟与视觉检查

每次涉及场景、UI、字体、布局、资源或打包的变更，必须运行：

```powershell
uv run qiqi-town --smoke-test
```

并检查 `build/` 下相关截图。构建脚本还会运行打包后的 exe 冒烟测试。

## 6. 编码约定

- Python 3.14；文件使用 UTF-8；中文 UI 文案使用简体中文。
- 使用 `from __future__ import annotations`，公开函数/方法写类型标注。
- 行宽 100，遵循 ruff 检查。
- 优先小函数、明确命名；避免在一个方法里塞入多个系统规则。
- 不要引入未经验证的大型框架；运行时依赖保持 Panda3D + 标准库。
- 新增资源必须通过 `qiqi_town.paths` 解析，兼容开发态和 PyInstaller。
- 修改 UTF-8 源文件必须使用编辑/写入工具，禁止用 PowerShell `Get-Content | Set-Content` 整体重写；这会造成中文乱码和语法损坏。
- 删除/移动文件前必须确认绝对路径是目标路径。

### Panda3D 约定

- 坐标：Z 向上、Y 向前；地面存档只存 `(x, y)`。
- 角色朝向：模型正面为 +Y；Panda3D 中 `H=90` 会把 +Y 转向 -X，因此方向角为：

  ```python
  heading = math.atan2(-dx, dy)
  ```

- 鼠标射线从相机空间转到世界空间时使用：

  ```python
  world_point = render.getRelativePoint(cam, camera_space_point)
  ```

  不要把方向写反，否则点击地面会失效。
- 相机不直接序列化；切场景使用 `CameraRig.snap_to()` 避免镜头从旧位置飞过来。
- 场景导航使用 `NavGrid`；交互点必须验证 `find_path` 可达。

## 7. 数据与存档契约

- 手动档：`slot_01.json` … `slot_20.json`。
- 自动档：`autosave.json`。
- 根目录：`%APPDATA%\QiqiTown`；不可写时回退 `%LOCALAPPDATA%`、用户目录或 exe 目录，**不得回退到当前工作目录**。
- 写入必须原子化，保留 `.bak`，损坏存档不得覆盖。
- 旧版写在 cwd/exe 旁的存档应在首次启动时迁移。
- 退出游戏和窗口关闭时自动保存一次。
- 修改存档字段必须同步更新：
  - `specs/001-qiqi-town/contracts/save-format.md`
  - `specs/001-qiqi-town/data-model.md`
  - 迁移/版本测试
- 设置文件为 `%APPDATA%\QiqiTown\settings.json`；新增设置项要有默认值和读取兼容。

## 8. 内容与许可

- 音频必须为项目原创或明确可商用；当前音频由 `tools/generate_audio.py` 程序生成。
- 字体使用随包 `Noto Sans SC`（OFL 1.1），保留 `OFL-NotoSansSC.txt`。
- 不打包带水印的用户参考图；`docs/reference/` 仅用于比对。
- 新增第三方素材必须更新 `CREDITS.md`，写清来源和许可证。
- 不在代码、测试或提交中写入密钥、token、个人路径或存档隐私数据。

## 9. 版本与发布

版本规则见 `CHANGELOG.md`：

- 初始版本：`V1.0.0`（2026.10.29）；
- 每次 Git push 对应一个版本；
- 上传前先新增版本条目；
- 只递增最后一位：`V1.0.0 → V1.0.1 → V1.0.2 …`；
- 同一批多个提交只算一个版本；
- 未上传的本地修改不单独占版本号，并入下一次上传记录。

发布前检查：

- [ ] `uv run ruff check src tests` 通过
- [ ] `uv run pytest` 全部通过
- [ ] `uv run qiqi-town --smoke-test` 通过并检查截图
- [ ] 涉及 UI/场景的变更已人工检查
- [ ] `CHANGELOG.md` 已增加对应版本
- [ ] `dist/`、`.smoke-data-*`、`.test-tmp/`、`*.zip` 未被提交
- [ ] `START_GAME.bat`、`README-PORTABLE.txt` 已包含在发布包
- [ ] 试玩包可启动，存档目录可写

构建产物不进入 Git；发布 zip 单独交付或作为 GitHub Release 附件。

## 10. 当前已知限制

- exe 未做代码签名，SmartScreen 仍可能提示未知发布者；使用 `START_GAME.bat` 或先解除 zip 锁定。
- 相机碰撞回退、更多分辨率/低配性能的人工验收仍可继续完善。
- 全屏使用无边框窗口方案，不强制切换显示器分辨率。

## 11. 代理执行清单

开始任务前：

1. 阅读本文件、宪法、相关 spec/plan/tasks 和 `CHANGELOG.md`。
2. 确认工作区干净，或明确当前未提交变更属于本次任务。
3. 找到对应测试文件；没有就先创建。
4. 先写失败测试，再实现。

结束任务前：

1. 运行 ruff 和 pytest。
2. 涉及 UI/场景/打包时运行 smoke 和对应探针。
3. 更新 spec/plan/data-model/contracts/tasks 中受影响的文档。
4. 更新 `CHANGELOG.md`（仅准备上传时）。
5. 报告修改文件、测试命令和结果；不要声称未运行的检查已通过。

---

**一句话：先规格，后测试，再实现；文档、测试、构建和版本记录必须一起交付。**
