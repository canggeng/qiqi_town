淇淇的小镇 · Windows 便携版

1. 请先把整个 zip 解压到任意文件夹，不要直接在压缩包里运行。
2. 双击“START_GAME.bat”。它会递归移除整个游戏文件夹的“来自 Internet”标记，再启动 QiqiTown.exe；请优先使用这个启动器，不要直接双击 exe。
3. 如果 Windows SmartScreen 仍然提示“无法识别的应用”：
   点击“更多信息”，再点击“仍要运行”。这是 Windows 对未签名程序的通用提示。
4. 想从一开始就避免这个提示：
   右键 zip 文件 → 属性 → 勾选“解除锁定” → 确定，然后再解压。
5. 如果使用 7-Zip 等工具解压，通常不会把下载标记带进文件，也可以直接运行 QiqiTown.exe。
6. 要彻底消除“发布者未知”，需要给 QiqiTown.exe 做代码签名；详见项目仓库的 docs/CODE_SIGNING.md。

存档位置：%APPDATA%\QiqiTown\saves
