# 淇淇的小镇

一个用鼠标游玩的温馨 3D 小镇生活游戏。5 岁的淇淇在青禾镇度过夏日灯会前的五天：逛幼儿园、图书馆、公园、游乐场，爬上青禾山，和镇上的居民一起完成每天的小故事。

## 当前可玩内容（开发中）

- 3D 小镇：中心广场、家、幼儿园、图书馆、公园（池塘/鸭子）、游乐场（滑梯/秋千/跷跷板/沙坑）、可沿步道爬上的青禾山与山顶平台。
- 第三人称鼠标操作：左键点击寻路、右键拖动镜头、滚轮缩放；山道会自动抬高角色与镜头。
- 三个可进入室内：家、幼儿园、图书馆；场景切换、NPC、悬停交互提示。
- 对话系统：逐字显示、选项、条件/效果、旗标/友谊/贴纸。
- 五天主线：通过和各地点居民对话与选择，完成每天的主线；回家睡觉推进天数；第五天登顶看灯会结局，之后进入自由模式。
- 每天 3 个小游戏，共 6 套玩法：形状配对、故事排序、秋千节奏、接花瓣、山路记忆、小镇 3D 找一找；按天排期并显示在日记里。
- 幼儿园新增安思宜、邵文星两位小朋友；公园的鸭子一家也可以对话。
- 睡觉时会播放“晚安 → 第二天清晨”的夜间过渡画面。
- 12 个环境小事件（告示牌、喷泉、团子、倒下的书、鸭子、围巾、树上的气球、沙堡、画、手套、松鼠、山顶灯笼），其中多数带选择。
- 原创轻音乐/环境音/音效（town/interior/dusk、鸟鸣、点击、开门、脚步、秋千、灯笼等）。
- 日记界面、结局界面、标题/暂停/设置/20+1 存档界面、首次进入的鼠标教程。
- 随包 OFL 中文字体（Noto Sans SC）、自动存档、手动存档、损坏存档保护、exe 冒烟构建。

尚未完成：相机碰撞回退、最终性能/美术打磨、更多结局差异与完整人工鼠标验收。

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
