# 技术调研记录

## 2026-10-29 · 初始环境

- 系统 Python：3.14.3。
- uv：0.13.6。
- `uv pip install --system --dry-run panda3d` 解析到 `panda3d-1.10.16-cp314-cp314-win_amd64.whl`。
- PyInstaller 6.22.3 + pyinstaller-hooks-contrib 2026.9 可在 Python 3.14 下解析。
- 项目目录初始为空；已创建 SDD 文档与 uv 项目。
- 工作区曾出现 Windows 权限拒绝，已通过 ACL 修复工具处理；后续使用项目内临时/工作区路径。

## M0 验证结果

- Panda3D 1.10.16 在 Python 3.14 下可打开 offscreen 窗口并渲染。
- 鼠标拾取地面采用相机镜头 `extrude` + 与 z=0.03 平面求交，稳定，无需额外碰撞体。
- 中文字体：`loader.loadFont()` 必须传 **Panda3D 风格路径字符串**（`/c/Windows/Fonts/simhei.ttf`），
  不能直接传 `Filename`；传 `Filename` 会触发 `TypeError`。
- `msyh.ttc` 加载后没有字形，改用 `simhei.ttf` 正常。
- 发布字体已解决：从 PyPI 数据包 `pylopdf-fonts-zh-cn` 取得 **NotoSansSC-Regular.otf**（OFL 1.1），
  放入 `src/qiqi_town/assets/fonts/`，游戏优先加载随包字体，缺失时才回退系统字体。
- 音频：Panda3D 的 `p3openal_audio` 在 Windows 上可加载 22050 Hz/单声道 WAV；
  原创音乐/环境音/音效由 `tools/generate_audio.py` 生成，打包时随 `assets/audio` 一起收集。
- 字体与音频资源使 onedir 包增大约 30MB；冒烟测试使用 `audio-library-name null`，正常运行才启用 OpenAL。
- CJK 换行：Panda3D 的 `wordwrap` 对中文不可靠，采用按字符宽度估算 + 手动 `\n` 的 `wrap_cjk`。
- `--smoke-test`：offscreen 下截图成功，生成 `build/title.png`、`build/smoke.png`、
  `build/dialogue.png`、`build/save.png`、`build/settings.png`、`build/diary.png` 等。
- PyInstaller：
  - onedir 构建成功；`collect_data_files("panda3d")` 足够让 Panda3D 运行。
  - 数据目录需要以 `data`、`assets` 为 dest 放入 `_MEIPASS` 根，匹配 `paths.resource_root()`。
  - `console=False` 的窗口化 exe 在清空 `PYTHONHOME`/`PYTHONPATH` 的环境下可离屏渲染。
  - 窗口化 exe 的退出码在 PowerShell 中不可靠，改用 smoke 标记文件（`smoke.ok`）验证。
- 存档仓库：20 手动档 + 自动档、原子写、`.bak`、损坏检测均通过单元测试。
- 测试注意：Windows 沙箱下 pytest `tmp_path`/`tempfile.mkdtemp` 可能创建受限 ACL 目录；
  项目使用 `.test-tmp` + `Path.mkdir` 的 `work_dir` fixture，并在 pytest 配置中禁用 tmpdir 插件。

## 2026-10-30/31 · 交互与 UI 收尾

- **角色朝向**：Panda3D 中 `H=90` 会把模型 +Y 朝向转到 -X，因此行走朝向使用
  `atan2(-dx, dy)`；`heading_probe.py` 验证东/北/西/南分别为约 -90°/0°/90°/180°。
- **鼠标射线**：`Lens.extrude` 返回相机空间坐标，转到世界必须使用
  `render.getRelativePoint(cam, point)`；方向写反会导致所有地面点击失败。
- **无边框全屏**：`setFullscreen(True)` 在 2520×1680 测试环境触发
  `ChangeDisplaySettings failed`；改为 `Fullscreen(False)+Undecorated(True)+display size`，
  不切换分辨率，`fullscreen_probe.py` 可正常截图。
- **圆角 UI**：用 `PNMImage` 按控件长宽比生成白色圆角 alpha 贴图，
  `DirectFrame["frameTexture"]` + `frameColor` 着色；`ui/roundrect.py` 缓存复用。
- **存档目录**：旧逻辑写入失败会回退 cwd，换启动目录后看起来“存档为空”；
  现在固定 `%APPDATA%\QiqiTown`，回退 LOCALAPPDATA/用户目录/exe 目录，不回到 cwd；
  首次启动从 cwd/exe 旁迁移旧档，退出和关窗自动保存。
- **每日小游戏标记**：`TextNode` + `setBillboardPointEye()` 做 3D `?`/`√` 公告牌；
  `setDepthTest(False)`、固定 bin、阴影；`setShadow` 只接受两个偏移参数，不能传颜色。
  标记按 `slot_for(day, kind)` 重建，从 `MinigameState.completed` 派生符号；
  标记高度需避开 HUD，形状站点最终放在桌面 `z≈0.75`。
- **SmartScreen**：未签名 PyInstaller exe 无法从程序侧消除提示；启动器递归
  `Unblock-File` 整个目录，构建脚本支持 `QIQI_SIGN_CERT`/`QIQI_SIGN_PASSWORD` 可选签名。

## 待验证

1. 实际鼠标点击、右键拖动、滚轮在普通窗口下的手感与边界。
2. DirectGUI 中文字体在 1600×900/1920×1080 下的布局。
3. 随包 OFL 字体的获取/子集化（当前 PyPI `noto-cjk` 字体子包解析失败，GitHub 直连失败）。
4. 窗口化 exe 在真正无控制台环境（双击）下的启动与日志。
5. 音频设备/素材授权。
6. 多场景切换时的相机碰撞与光照。
