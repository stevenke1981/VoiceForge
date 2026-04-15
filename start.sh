#!/usr/bin/env bash
set -euo pipefail

echo "============================================"
echo "  VoiceForge - Qwen3 本地語音轉錄與智慧潤稿"
echo "============================================"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "[ERROR] uv 未安裝。請先安裝 uv："
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "[1/2] 同步依賴..."
uv sync

echo "[2/2] 啟動 VoiceForge..."
echo ""
uv run python main.py
