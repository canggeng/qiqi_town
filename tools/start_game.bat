@echo off
setlocal
cd /d "%~dp0"
if not exist "QiqiTown.exe" (
    echo QiqiTown.exe was not found. Please extract the whole zip first.
    pause
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-ChildItem -LiteralPath (Get-Location).Path -Recurse -File -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue"
start "" "%~dp0QiqiTown.exe"
