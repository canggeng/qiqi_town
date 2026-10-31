# 淇淇的小镇 · 构建脚本
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:UV_CACHE_DIR = Join-Path $Root ".uv-cache"

Write-Host "== uv sync =="
uv sync --frozen
if ($LASTEXITCODE -ne 0) { throw "uv sync failed" }

Write-Host "== tests =="
uv run pytest
if ($LASTEXITCODE -ne 0) { throw "tests failed" }

Write-Host "== pyinstaller =="
uv run pyinstaller tools/qiqi_town.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) { throw "pyinstaller failed" }

$Exe = Join-Path $Root "dist\QiqiTown\QiqiTown.exe"
if (-not (Test-Path $Exe)) { throw "missing $Exe" }

$SignCert = $env:QIQI_SIGN_CERT
if ($SignCert) {
    Write-Host "== sign exe =="
    if (-not (Test-Path $SignCert)) { throw "signing certificate not found: $SignCert" }
    $SignTool = (Get-Command signtool.exe -ErrorAction SilentlyContinue).Source
    if (-not $SignTool) { throw "signtool.exe not found; install Windows SDK or add it to PATH" }
    $SignPassword = $env:QIQI_SIGN_PASSWORD
    if (-not $SignPassword) { throw "QIQI_SIGN_PASSWORD is required when QIQI_SIGN_CERT is set" }
    & $SignTool sign /fd SHA256 /f $SignCert /p $SignPassword /tr http://timestamp.digicert.com /td SHA256 $Exe
    if ($LASTEXITCODE -ne 0) { throw "code signing failed" }
    & $SignTool verify /pa $Exe
    if ($LASTEXITCODE -ne 0) { throw "signature verification failed" }
} else {
    Write-Host "== unsigned build (set QIQI_SIGN_CERT to sign) =="
}

Write-Host "== smoke exe =="
$DataDir = Join-Path $Root ".smoke-data-exe-build"
$env:QIQI_TOWN_DATA_DIR = $DataDir
New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
$Marker = Join-Path $DataDir "smoke.ok"
if (Test-Path $Marker) { Remove-Item $Marker -Force }
& $Exe --smoke-test
$deadline = (Get-Date).AddSeconds(60)
while (-not (Test-Path $Marker) -and (Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 500
}
if (-not (Test-Path $Marker)) { throw "exe smoke test timed out" }
Write-Host "smoke marker: $Marker"

Write-Host "== zip =="
$Version = "0.1.0"
$DistDir = Join-Path $Root "dist\QiqiTown"
Copy-Item (Join-Path $Root "README.md") (Join-Path $DistDir "README.md") -Force
Copy-Item (Join-Path $Root "CREDITS.md") (Join-Path $DistDir "CREDITS.md") -Force
Copy-Item (Join-Path $Root "src\qiqi_town\assets\fonts\OFL-NotoSansSC.txt") (Join-Path $DistDir "FONT-LICENSE-NotoSansSC.txt") -Force
Copy-Item (Join-Path $Root "tools\start_game.bat") (Join-Path $DistDir "START_GAME.bat") -Force
Copy-Item (Join-Path $Root "tools\PORTABLE_README.txt") (Join-Path $DistDir "README-PORTABLE.txt") -Force
Copy-Item (Join-Path $Root "docs\CODE_SIGNING.md") (Join-Path $DistDir "CODE_SIGNING.md") -Force
Unblock-File -LiteralPath $Exe -ErrorAction SilentlyContinue
$Zip = Join-Path $Root "dist\QiqiTown_v${Version}_windows_x64.zip"
if (Test-Path $Zip) { Remove-Item $Zip -Force }
Compress-Archive -Path (Join-Path $DistDir "*") -DestinationPath $Zip
Unblock-File -LiteralPath $Zip -ErrorAction SilentlyContinue
Write-Host "Done: $Zip"
