# VoiceForge — 知識圖譜 (knowledge_graph.md)

## 節點（Nodes）

### 模組節點

| ID | 名稱 | 類型 | 路徑 |
|----|------|------|------|
| M1 | App | class | main.py |
| M2 | ASREngine | class | core/asr_engine.py |
| M3 | AudioRecorder | class | core/audio_recorder.py |
| M4 | LLMPolisher | class | core/llm_polish.py |
| M5 | ModelManager | class | utils/model_manager.py |
| M6 | ConfigManager | class | utils/config.py |
| M7 | RealtimePage | class | pages/realtime_page.py |
| M8 | FilePage | class | pages/file_page.py |
| M9 | PolishPage | class | pages/polish_page.py |
| M10 | SettingsPage | class | pages/settings_page.py |
| M11 | audio_utils | module | utils/audio_utils.py |
| M12 | PTTController | feature | pages/realtime_page.py |
| M13 | AutoSender | feature | pages/realtime_page.py |

### 外部依賴節點

| ID | 名稱 | 版本 | 用途 |
|----|------|------|------|
| E1 | qwen-asr | >=0.2.0 | ASR 模型推論 |
| E2 | huggingface-hub | >=0.25.0 | 模型下載 |
| E3 | customtkinter | >=5.2.0 | GUI 框架 |
| E4 | sounddevice | >=0.5.0 | 麥克風錄音 |
| E5 | numpy | >=1.26.0 | 音訊陣列處理 |
| E6 | torch | >=2.1.0 | 模型推論後端 |
| E7 | anthropic | >=0.40.0 | Claude API |
| E8 | openai | >=1.50.0 | OpenAI API |
| E9 | google-generativeai | >=0.8.0 | Gemini API |
| E10 | keyboard | >=0.13.5 | 全域快捷鍵 (PTT) |
| E11 | pyperclip | >=1.8.0 | 剪貼簿寫入（自動發送） |

### 模型節點

| ID | 名稱 | HuggingFace ID | 預設路徑 |
|----|------|----------------|----------|
| D1 | Qwen3-ASR-0.6B | Qwen/Qwen3-ASR-0.6B | models/Qwen3-ASR-0.6B |
| D2 | Qwen3-ASR-1.7B | Qwen/Qwen3-ASR-1.7B | models/Qwen3-ASR-1.7B |
| D3 | ForcedAligner-0.6B | Qwen/Qwen3-ForcedAligner-0.6B | models/Qwen3-ForcedAligner-0.6B |

## 邊（Edges）

### 依賴關係

```
M1 (App) ──uses──→ M2 (ASREngine)
M1 (App) ──uses──→ M3 (AudioRecorder)
M1 (App) ──uses──→ M4 (LLMPolisher)
M1 (App) ──uses──→ M5 (ModelManager)
M1 (App) ──uses──→ M6 (ConfigManager)
M1 (App) ──contains──→ M7 (RealtimePage)
M1 (App) ──contains──→ M8 (FilePage)
M1 (App) ──contains──→ M9 (PolishPage)
M1 (App) ──contains──→ M10 (SettingsPage)

M2 (ASREngine) ──depends──→ E1 (qwen-asr)
M2 (ASREngine) ──depends──→ E6 (torch)
M2 (ASREngine) ──loads──→ D1/D2 (Qwen3-ASR models)

M3 (AudioRecorder) ──depends──→ E4 (sounddevice)
M3 (AudioRecorder) ──depends──→ E5 (numpy)

M4 (LLMPolisher) ──depends──→ E7 (anthropic)
M4 (LLMPolisher) ──depends──→ E8 (openai)
M4 (LLMPolisher) ──depends──→ E9 (google-generativeai)

M5 (ModelManager) ──depends──→ E2 (huggingface-hub)
M5 (ModelManager) ──manages──→ D1/D2/D3 (models)

M7 (RealtimePage) ──uses──→ M2 (ASREngine)
M7 (RealtimePage) ──uses──→ M3 (AudioRecorder)
M7 (RealtimePage) ──contains──→ M12 (PTTController)
M7 (RealtimePage) ──contains──→ M13 (AutoSender)
M12 (PTTController) ──depends──→ E10 (keyboard)
M13 (AutoSender) ──depends──→ E10 (keyboard)
M13 (AutoSender) ──depends──→ E11 (pyperclip)
M10 (SettingsPage) ──configures──→ M12 (PTTController)
M10 (SettingsPage) ──configures──→ M13 (AutoSender)

M8 (FilePage) ──uses──→ M2 (ASREngine)
M8 (FilePage) ──uses──→ M11 (audio_utils)

M9 (PolishPage) ──uses──→ M4 (LLMPolisher)

M10 (SettingsPage) ──uses──→ M5 (ModelManager)
M10 (SettingsPage) ──uses──→ M6 (ConfigManager)
```

### 資料流

```
Audio Input ──→ M3 (AudioRecorder) ──ndarray──→ M2 (ASREngine) ──text──→ M7/M8 (Pages)
                                                                    │
                                                                    ▼
                                                            M4 (LLMPolisher)
                                                                    │
                                                                    ▼
                                                             M9 (PolishPage)
```

## 社群 / 聚落

| 聚落 | 包含節點 | 職責 |
|------|----------|------|
| GUI Cluster | M1, M7, M8, M9, M10, E3 | 使用者介面 |
| ASR Cluster | M2, M3, M11, E1, E4, E5, E6 | 語音辨識 |
| LLM Cluster | M4, E7, E8, E9 | 智慧潤稿 |
| Infra Cluster | M5, M6, E2 | 模型管理與設定 |

## 變更歷史

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-04-14 | v0.1 | 初始知識圖譜建立 |
