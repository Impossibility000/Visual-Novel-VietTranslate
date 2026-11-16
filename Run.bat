@echo off
title AetherVN - Visual Novel Realtime Translator
cd /d "%~dp0"

echo =======================================================
echo   Khoi dong AetherVN - Visual Novel Realtime Translator
echo =======================================================
echo.

python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Co loi xay ra khi chay ung dung!
    pause
)

