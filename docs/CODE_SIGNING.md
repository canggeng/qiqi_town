# Windows SmartScreen 与代码签名

## 为什么会出现“Windows 已保护你的电脑”

`QiqiTown.exe` 由 PyInstaller 生成，默认没有商业代码签名证书。Windows 11 的 Microsoft Defender SmartScreen 会对以下情况提示“发布者未知 / 无法识别的应用”：

- 文件来自 Internet，仍带有 Mark-of-the-Web（Zone.Identifier）；
- 可执行文件没有受信任的代码签名；
- 该文件哈希在 Microsoft 的 SmartScreen 信誉库中还没有积累足够信誉。

这不是游戏代码本身报错，也不是病毒提示，而是 Windows 对未签名新程序的通用保护。

## 已经提供的缓解方式

1. **优先使用 `START_GAME.bat`**
   - 它会递归清除整个游戏目录的“来自 Internet”标记，再启动 `QiqiTown.exe`。
   - 直接双击 `QiqiTown.exe` 不会执行这一步。

2. **先解除 zip 锁定再解压**
   - 右键下载的 zip → 属性 → 勾选“解除锁定” → 确定 → 解压。
   - 这样解压出来的 exe 通常不再带 Mark-of-the-Web。

3. **使用 7-Zip 等工具解压**
   - 许多解压工具不会把下载标记写入每个文件。

4. **首次运行时选择“更多信息 → 仍要运行”**
   - 仅在你确认文件来自本项目时使用。
   - 不要为了运行未知来源程序而全局关闭 SmartScreen。

## 彻底消除提示：代码签名

要真正避免“发布者未知”，必须使用 Windows 信任的代码签名证书对 exe 签名：

- **OV 代码签名证书**：较常见，签名后需要一定下载量/时间积累 SmartScreen 信誉；
- **EV 代码签名证书**：通常能更快建立信誉，但申请和验证更严格；
- 自签名证书不能解决其他电脑上的 SmartScreen 提示，不建议作为发布方案。

签名必须在打包完成后、生成 zip 之前进行。项目构建脚本已支持可选签名：

```powershell
$env:QIQI_SIGN_CERT = "C:\secure\qiqi-town-codesign.pfx"
$env:QIQI_SIGN_PASSWORD = "证书密码"
powershell -ExecutionPolicy Bypass -File tools/build.ps1
```

要求：

- 已安装 Windows SDK 的 `signtool.exe`；
- `QIQI_SIGN_CERT` 指向 `.pfx` 文件；
- `QIQI_SIGN_PASSWORD` 为证书密码；
- 时间戳服务器默认为 `http://timestamp.digicert.com`。

如果没有设置 `QIQI_SIGN_CERT`，构建脚本仍会生成可运行的 exe，但会明确提示这是未签名构建。

手动签名命令示例：

```powershell
signtool sign /fd SHA256 /f C:\secure\qiqi-town-codesign.pfx /p "证书密码" `
  /tr http://timestamp.digicert.com /td SHA256 `
  dist\QiqiTown\QiqiTown.exe

signtool verify /pa dist\QiqiTown\QiqiTown.exe
```

不要将 `.pfx`、密码或证书私钥提交到 Git 仓库。
