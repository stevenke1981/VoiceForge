@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title VoiceForge - Qwen3 語音轉錄工具

echo ============================================
echo   VoiceForge - Qwen3 本地語音轉錄與智慧潤稿
echo ============================================
echo.

:: ── [1/3] 檢查 uv ──────────────────────────────────────────────────────────
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] uv 未安裝。請先安裝 uv：
    echo   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo.
    pause
    exit /b 1
)

:: ── [2/3] 同步依賴 ──────────────────────────────────────────────────────────
echo [1/3] 同步依賴（含 Google GenAI）...
uv sync --extra google
if %errorlevel% neq 0 (
    echo [ERROR] 依賴同步失敗，請檢查網路連線。
    pause
    exit /b 1
)

:: ── [2/3] 啟動 ──────────────────────────────────────────────────────────────
echo.
echo [2/2] 啟動 VoiceForge...
echo.
uv run python main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 程式異常退出。
    pause
)
