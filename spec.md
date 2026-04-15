# VoiceForge — 規格書 (spec.md)

## 1. 系統架構

```
┌─────────────────────────────────────────────┐
│                  main.py                     │
│             (App 啟動入口)                    │
├─────────────────────────────────────────────┤
│              GUI Layer (pages/)              │
│  ┌──────────┬──────────┬────────┬────────┐  │
│  │ 即時轉錄 │ 檔案轉錄 │ 潤稿   │ 設定   │  │
│  │ realtime │ file     │ polish │settings│  │
│  └──────────┴──────────┴────────┴────────┘  │
├─────────────────────────────────────────────┤
│              Core Layer (core/)              │
│  ┌──────────────┬────────────────────────┐  │
│  │ asr_engine   │ llm_polish             │  │
│  │ (Qwen3-ASR)  │ (Claude/GPT/Gemini)    │  │
│  └──────────────┴────────────────────────┘  │
│  ┌──────────────┐                           │
│  │audio_recorder│                           │
│  └──────────────┘                           │
├─────────────────────────────────────────────┤
│             Utils Layer (utils/)             │
│  ┌────────┬──────────────┬──────────────┐   │
│  │ config │ model_manager│ audio_utils  │   │
│  └────────┴──────────────┴──────────────┘   │
├─────────────────────────────────────────────┤
│              models/ (本地模型)               │
│  Qwen3-ASR-0.6B / 1.7B / ForcedAligner     │
└─────────────────────────────────────────────┘
```

## 2. 模組規格

### 2.1 utils/model_manager.py

**職責**：管理本地模型下載與驗證

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `check_model_exists(model_name)` | str | bool | 檢查本地模型是否完整 |
| `download_model(model_name, callback)` | str, Callable | str | 下載模型並回傳本地路徑 |
| `get_local_path(model_name)` | str | str | 取得模型本地絕對路徑 |
| `list_available_models()` | - | list[dict] | 列出所有可用模型清單 |

### 2.2 core/asr_engine.py

**職責**：封裝 Qwen3-ASR 轉錄功能

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `load_model(model_size)` | str | None | 載入指定大小模型 |
| `transcribe_file(file_path, language)` | str, str? | TranscriptResult | 轉錄音訊檔案 |
| `transcribe_array(audio_np, sr, language)` | ndarray, int, str? | TranscriptResult | 轉錄 numpy 陣列 |
| `unload_model()` | - | None | 釋放模型記憶體 |

### 2.3 core/audio_recorder.py

**職責**：管理麥克風錄音

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `start_recording(device_id)` | int? | None | 開始錄音 |
| `stop_recording()` | - | ndarray | 停止錄音並回傳音訊 |
| `get_devices()` | - | list[dict] | 列出可用音訊裝置 |
| `is_recording` | - | bool | 錄音狀態 |

### 2.4 core/llm_polish.py

**職責**：LLM 潤稿處理

| 方法 | 參數 | 回傳 | 說明 |
|------|------|------|------|
| `polish(text, provider, prompt)` | str, str, str? | str | 潤飾文字 |
| `set_api_key(provider, key)` | str, str | None | 設定 API Key |

### 2.5 utils/config.py

**職責**：持久化設定管理

- 設定檔位置：`./config.json`
- 預設值：模型路徑 `./models`、語言自動偵測、主題跟隨系統

### 2.6 pages/ 分頁元件

| 分頁 | 檔案 | 功能 |
|------|------|------|
| 即時轉錄 | `realtime_page.py` | 麥克風錄音 → 即時轉文字 |
| 檔案轉錄 | `file_page.py` | 選擇/拖放音檔 → 批次轉錄 |
| 潤稿模式 | `polish_page.py` | 選擇 LLM → 潤飾轉錄結果 |
| 設定 | `settings_page.py` | 模型路徑、API Key、語言、主題 |

## 3. 資料流

### 即時轉錄流程
```
麥克風 → sounddevice → numpy array → asr_engine.transcribe_array() → GUI 顯示
```

### 檔案轉錄流程
```
選擇檔案 → asr_engine.transcribe_file() → 結果列表 → 複製/匯出
```

### 潤稿流程
```
轉錄文字 → 選擇 LLM Provider → llm_polish.polish() → 潤稿結果 → 複製
```

## 4. 設定結構 (config.json)

```json
{
  "model_dir": "./models",
  "default_model": "Qwen3-ASR-0.6B",
  "language": null,
  "device": "auto",
  "theme": "System",
  "llm_provider": "anthropic",
  "api_keys": {
    "anthropic": "",
    "openai": "",
    "google": ""
  },
  "audio_device": null,
  "sample_rate": 16000,
  "max_recording_seconds": 300
}
```

## 變更歷史

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-04-14 | v0.1 | 初始規格建立 |
