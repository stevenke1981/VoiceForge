# VoiceForge

**Qwen3 本地語音轉錄與智慧潤稿工具**

VoiceForge 是一個完全本地化的 Python 桌面應用，使用 Qwen3-ASR 進行語音辨識，
並結合 LLM API（Claude / GPT / Gemini）進行智慧潤稿。

模型預設下載到專案根目錄 `./models/`，首次啟動時自動從 HuggingFace 下載。

---

## 功能特色

- 🎙️ **即時語音轉錄** — 麥克風錄音即時轉文字
- 📁 **檔案批次轉錄** — 支援 WAV / MP3 / FLAC / OGG / M4A
- ✍️ **智慧潤稿** — Claude / GPT / Gemini 潤飾轉錄文字
- 📦 **本地模型** — 模型存放在專案目錄，無需全域安裝
- ⚡ **GPU 加速** — 支援 CUDA，自動偵測 GPU
- 🌐 **多語言** — 支援 52 種語言自動偵測

---

## 系統需求

- Python 3.11 或 3.12
- [uv](https://docs.astral.sh/uv/) 套件管理工具
- 至少 4GB RAM（CPU 模式）/ 4GB+ VRAM（GPU 模式）
- Windows 10+、macOS 12+、Linux

---

## 快速開始

### 1. 安裝 uv

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 克隆專案

```bash
git clone <repo-url> VoiceForge
cd VoiceForge
```

### 3. 同步依賴

```bash
uv sync
```

### 4. 啟動應用

**Windows:**
```cmd
start.bat
```

**macOS / Linux:**
```bash
chmod +x start.sh
./start.sh
```

**或直接使用 uv：**
```bash
uv run python main.py
```

### 5. 首次啟動 — 模型下載

首次啟動時，VoiceForge 會自動檢查 `./models/` 目錄：
- 若模型不存在，會自動從 HuggingFace 下載
- 預設下載 `Qwen3-ASR-0.6B`（約 1.2 GB）
- 下載進度會顯示在 GUI 上

模型目錄結構：
```
models/
├── Qwen3-ASR-0.6B/         # ~1.2 GB
├── Qwen3-ASR-1.7B/         # ~3.4 GB (可選)
└── Qwen3-ForcedAligner-0.6B/ # ~1.2 GB (可選)
```

---

## 手動下載模型

如果自動下載失敗，可以手動下載：

```bash
# 使用 uv run 確保在虛擬環境中
uv run python -c "
from huggingface_hub import snapshot_download
snapshot_download('Qwen/Qwen3-ASR-0.6B', local_dir='./models/Qwen3-ASR-0.6B')
"
```

或使用 huggingface-cli：
```bash
uv run huggingface-cli download Qwen/Qwen3-ASR-0.6B --local-dir ./models/Qwen3-ASR-0.6B
```

---

## 設定

設定檔位於 `./config.json`，首次啟動時自動建立。

| 設定項 | 說明 | 預設值 |
|--------|------|--------|
| model_dir | 模型存放路徑 | `./models` |
| default_model | 預設 ASR 模型 | `Qwen3-ASR-0.6B` |
| language | 辨識語言 | `null`（自動偵測）|
| device | 推論裝置 | `auto` |
| llm_provider | LLM 提供者 | `anthropic` |

---

## 專案結構

```
VoiceForge/
├── main.py                 # 應用入口
├── core/
│   ├── __init__.py
│   ├── asr_engine.py       # Qwen3-ASR 引擎封裝
│   ├── audio_recorder.py   # 麥克風錄音管理
│   └── llm_polish.py       # LLM 潤稿
├── pages/
│   ├── __init__.py
│   ├── realtime_page.py    # 即時轉錄分頁
│   ├── file_page.py        # 檔案轉錄分頁
│   ├── polish_page.py      # 潤稿模式分頁
│   └── settings_page.py    # 設定分頁
├── utils/
│   ├── __init__.py
│   ├── config.py           # 設定管理
│   ├── model_manager.py    # 模型下載管理
│   └── audio_utils.py      # 音訊工具
├── models/                 # 本地模型目錄
├── pyproject.toml          # uv 專案設定
├── requirements.txt        # pip 相容
├── start.bat               # Windows 啟動
├── start.sh                # Unix 啟動
└── .python-version
```

---

## PyInstaller 打包

```bash
uv run pip install pyinstaller

uv run pyinstaller --noconfirm --onedir --windowed \
    --name VoiceForge \
    --add-data "models:models" \
    --hidden-import qwen_asr \
    --hidden-import customtkinter \
    --hidden-import sounddevice \
    --hidden-import anthropic \
    --hidden-import openai \
    --hidden-import google.generativeai \
    main.py
```

打包後檔案位於 `dist/VoiceForge/`。

---

## 常見問題

### 模型下載失敗
1. 檢查網路連線
2. 若在中國大陸，設定 HuggingFace 鏡像：
   ```bash
   set HF_ENDPOINT=https://hf-mirror.com  # Windows
   export HF_ENDPOINT=https://hf-mirror.com  # Linux/Mac
   ```
3. 使用手動下載方式（見上方說明）

### GPU 記憶體不足 (OOM)
- 使用 0.6B 模型而非 1.7B
- 在設定中將裝置改為 `cpu`
- 降低 `max_inference_batch_size`

### 「model type qwen3_asr not recognized」
- 確保使用 `qwen-asr` 套件（非直接用 transformers）
- 執行 `uv sync` 重新安裝依賴

### 錄音無聲音
- 檢查系統麥克風權限
- 在設定頁面切換音訊裝置

---

## 授權

MIT License

## 變更歷史

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-04-14 | v0.1 | 初始版本 |
