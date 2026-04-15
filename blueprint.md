# VoiceForge — 藍圖 (blueprint.md)

## 功能分解樹

```
VoiceForge
├── F1: 模型管理
│   ├── F1.1: 本地模型檢查 (check_model_exists)
│   ├── F1.2: 自動下載 (download_model + huggingface_hub)
│   ├── F1.3: 進度回報 (callback → GUI 進度條)
│   └── F1.4: 自訂路徑 (settings → model_dir)
│
├── F2: 即時轉錄
│   ├── F2.1: 麥克風裝置列舉 (sounddevice.query_devices)
│   ├── F2.2: 即時錄音 (sounddevice.InputStream)
│   ├── F2.3: 音訊切片 → ASR (每 N 秒送出一段)
│   ├── F2.4: 結果即時顯示 (主執行緒更新 Textbox)
│   └── F2.5: 複製到剪貼簿 (pyperclip)
│
├── F3: 檔案轉錄
│   ├── F3.1: 檔案選擇對話框 (filedialog)
│   ├── F3.2: 支援格式 (WAV, MP3, FLAC, OGG, M4A)
│   ├── F3.3: 批次轉錄 (逐檔處理 + 進度顯示)
│   ├── F3.4: 結果表格顯示
│   └── F3.5: 匯出 TXT / 複製
│
├── F4: 智慧潤稿
│   ├── F4.1: LLM Provider 選擇 (Anthropic / OpenAI / Google)
│   ├── F4.2: 自訂 Prompt 模板
│   ├── F4.3: 潤稿結果對比顯示 (原文 vs 潤稿)
│   ├── F4.4: 串流輸出
│   └── F4.5: 複製 / 直接輸入
│
└── F5: 設定
    ├── F5.1: 模型目錄設定
    ├── F5.2: 模型大小選擇 (0.6B / 1.7B)
    ├── F5.3: API Key 管理
    ├── F5.4: 語言設定 (自動 / 手動)
    ├── F5.5: 主題設定 (System / Dark / Light)
    └── F5.6: 音訊裝置選擇
```

## 類別設計

### App (main.py)
```
App(ctk.CTk)
├── __init__()         → 初始化視窗、載入設定
├── _build_ui()        → 建構 CTkTabview + 4 分頁
├── _init_engine()     → 背景初始化 ASR 引擎
└── _on_closing()      → 清理資源
```

### ASREngine (core/asr_engine.py)
```
ASREngine
├── __init__(model_dir, model_size, device)
├── load_model()       → 載入 Qwen3ASRModel
├── transcribe_file()  → 轉錄檔案
├── transcribe_array() → 轉錄 numpy 陣列
├── is_loaded          → 模型是否已載入
└── unload_model()     → 釋放 GPU 記憶體
```

### ModelManager (utils/model_manager.py)
```
ModelManager
├── __init__(base_dir)
├── check_model_exists(model_name) → bool
├── download_model(model_name, progress_callback) → str
├── get_local_path(model_name) → str
└── list_available_models() → list[dict]

MODELS = {
    "Qwen3-ASR-0.6B":          "Qwen/Qwen3-ASR-0.6B",
    "Qwen3-ASR-1.7B":          "Qwen/Qwen3-ASR-1.7B",
    "Qwen3-ForcedAligner-0.6B": "Qwen/Qwen3-ForcedAligner-0.6B",
}
```

### AudioRecorder (core/audio_recorder.py)
```
AudioRecorder
├── __init__(sample_rate=16000)
├── start_recording(device_id)
├── stop_recording() → numpy.ndarray
├── get_devices() → list[dict]
└── is_recording → bool
```

### LLMPolisher (core/llm_polish.py)
```
LLMPolisher
├── polish(text, provider, model, prompt) → str
├── polish_stream(text, provider, model, prompt) → Generator[str]
└── _call_anthropic() / _call_openai() / _call_google()
```

## 執行緒模型

```
┌─────────────────┐
│   Main Thread    │  ← Tk mainloop, GUI 更新
│   (GUI Event)    │
├─────────────────┤
│  Worker Thread   │  ← 模型下載、ASR 推論、LLM 呼叫
│  (daemon=True)   │
├─────────────────┤
│  Recorder Thread │  ← sounddevice callback
│  (daemon=True)   │
└─────────────────┘

通訊方式：self.after(0, callback) 將結果推回主執行緒
```

## 變更歷史

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-04-14 | v0.1 | 初始藍圖建立 |
