# 淇淇的小镇

一个用鼠标游玩的温馨 3D 小镇生活游戏。5 岁的淇淇在青禾镇度过夏日灯会前的五天：逛幼儿园、图书馆、公园、游乐场，爬上青禾山，和镇上的居民一起完成每天的小故事。

## 当前可玩内容（开发中）

- 3D 小镇：中心广场、家、幼儿园、图书馆、公园（池塘/鸭子）、游乐场（滑梯/秋千/跷跷板/沙坑）、可沿步道爬上的青禾山与山顶平台。
- 第三人称鼠标操作：左键点击寻路、右键拖动镜头、滚轮缩放；山道会自动抬高角色与镜头。
- 三个可进入室内：家、幼儿园、图书馆；场景切换、NPC、悬停交互提示。
- 对话系统：逐字显示、选项、条件/效果、旗标/友谊/贴纸。
- 五天主线：通过和各地点居民对话与选择，完成每天的主线；回家睡觉推进天数；第五天登顶看灯会结局，之后进入自由模式。
- 形状配对小游戏、日记界面、结局界面、标题/暂停/设置/20+1 存档界面。
- 随包 OFL 中文字体（Noto Sans SC）、自动存档、手动存档、损坏存档保护、exe 冒烟构建。

尚未完成：其余 5 套小游戏与每天 3 个小游戏排期、环境事件、音频、日程、相机碰撞与最终美术/性能打磨。

## 开发环境

- Windows 10/11 x64
- Python 3.14（uv 管理）
- Panda3D 1.10.16
- 所有依赖安装在项目内 `.venv`，不污染其他项目

```powershell
uv sync
uv run qiqi-town
```

开发期调试：

```powershell
uv run qiqi-town --smoke-test   # 启动、构建场景、截图、退出
uv run qiqi-town --debug         # 显示帧率
```

## 打包

```powershell
powershell -ExecutionPolicy Bypass -File tools/build.ps1
```

输出：`dist/QiqiTown/QiqiTown.exe`（onedir、无控制台）。

## 存档

- `%APPDATA%\QiqiTown\saves\slot_01.json` … `slot_20.json`
- `%APPDATA%\QiqiTown\saves\autosave.json`
- 设置：`%APPDATA%\QiqiTown\settings.json`

## SDD 文档

- `.specify/memory/constitution.md`：项目宪法
- `docs/PROJECT_KNOWLEDGE.md`：世界观、角色、系统决策
- `specs/001-qiqi-town/spec.md`：需求规格
- `specs/001-qiqi-town/plan.md`：技术方案
- `specs/001-qiqi-town/tasks.md`：实施任务与验收
- `specs/001-qiqi-town/research.md`：技术验证记录

## 许可与致谢

见 `CREDITS.md`。
