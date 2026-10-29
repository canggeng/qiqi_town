# Credits 与授权

## 角色参考

- `docs/reference/qiqi_portrait.jpg`：用户提供的淇淇形象参考图，仅作角色设计比对，**不打包进 exe、不在游戏中展示**。
- 游戏内淇淇 3D 模型为项目内原创程序化几何体，参考其轮廓、服装与配色，不复制原图像素。
- 参考图带有“豆包 AI 生成”水印；如需在宣传或游戏内使用，请先取得无水印、明确授权的版本。

## 字体

游戏随包使用 **Noto Sans SC Regular**（SIL Open Font License 1.1）：

- 文件：`src/qiqi_town/assets/fonts/NotoSansSC-Regular.otf`
- 来源：Noto CJK（通过 PyPI 数据包 `pylopdf-fonts-zh-cn` 获取的 OFL 版本）
- 授权文本：`src/qiqi_town/assets/fonts/OFL-NotoSansSC.txt`
- 用途：界面、对话、标题显示。

开发期会优先加载随包字体；若缺失则回退到 Windows 系统 `SimHei`。发布包必须确认字体文件被包含。

## 音频

尚未加入音频素材。计划使用 CC0 / 免版税音乐与音效，逐项记录来源、作者、许可证 URL。

## 代码

项目代码由本项目开发，未复制第三方代码。运行时依赖：

- Panda3D 1.10.16 — Modified BSD License
- PyInstaller 6.22.3（仅构建期） — GPL with exception
- uv / Python 3.14 — 各自许可证

## 图像

所有 3D 场景、角色、UI 均为程序化生成，未使用外部模型或贴图。
