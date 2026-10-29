# Credits 与授权

## 角色参考

- `docs/reference/qiqi_portrait.jpg`：用户提供的淇淇形象参考图，仅作角色设计比对，**不打包进 exe、不在游戏中展示**。
- 游戏内淇淇 3D 模型为项目内原创程序化几何体，参考其轮廓、服装与配色，不复制原图像素。
- 参考图带有“豆包 AI 生成”水印；如需在宣传或游戏内使用，请先取得无水印、明确授权的版本。

## 字体

当前开发版使用 Windows 系统自带 `SimHei`（黑体）读取中文：

- 文件：`C:/Windows/Fonts/simhei.ttf`
- 用途：开发期界面/对话显示。
- 发布前必须替换为可再分发的 OFL 字体（目标：Noto Sans SC 或 LXGW WenKai），并把授权文本加入本文件。

> 当前 exe 尚未附带字体文件，跨机器运行依赖目标 Windows 安装中文字体。这是首版待办项。

## 音频

尚未加入音频素材。计划使用 CC0 / 免版税音乐与音效，逐项记录来源、作者、许可证 URL。

## 代码

项目代码由本项目开发，未复制第三方代码。运行时依赖：

- Panda3D 1.10.16 — Modified BSD License
- PyInstaller 6.22.3（仅构建期） — GPL with exception
- uv / Python 3.14 — 各自许可证

## 图像

所有 3D 场景、角色、UI 均为程序化生成，未使用外部模型或贴图。
