# VoiceForge — 計畫書 (plan.md)

## 專案概述

VoiceForge 是一個完全本地化的 Python GUI 桌面工具，使用 Qwen3-ASR 進行語音轉錄，
結合 LLM API 進行智慧潤稿，模型預設下載到專案本地 `./models/` 目錄。

## 目標

1. **即時語音轉錄** — 透過麥克風即時錄音並轉文字
2. **檔案批次轉錄** — 支援 WAV/MP3/FLAC 等音訊檔案轉文字
3. **智慧潤稿** — 透過 LLM（Claude/GPT/Gemini）潤飾轉錄文字
4. **本地模型管理** — 首次啟動自動下載模型到 `./models/`

## 技術選型

| 領域 | 技術 |
|------|------|
| 語言 | Python 3.11+ |
| 專案管理 | uv (pyproject.toml) |
| ASR 引擎 | qwen-asr (Qwen3-ASR-0.6B / 1.7B) |
| 對齊器 | Qwen3-ForcedAligner-0.6B |
| GUI 框架 | customtkinter + CTkTabview |
| 錄音 | sounddevice + numpy |
| LLM API | anthropic / openai / google-generativeai |
| 剪貼簿 | pyperclip |
| 快捷鍵 | keyboard |
| 自動輸入 | pyautogui |

## 里程碑

### Phase 1 — 基礎框架 (v0.1)
- [x] uv 專案初始化
- [x] 模型自動下載管理器
- [x] ASR 引擎封裝（支援本地模型路徑）
- [x] 4 分頁 GUI 骨架

### Phase 2 — 核心功能 (v0.2)
- [x] 即時轉錄分頁（錄音 + 即時顯示）
- [x] 檔案轉錄分頁（拖放/選擇 + 批次）
- [x] 潤稿模式分頁（LLM 潤飾）
- [x] 設定分頁（模型路徑、API Key、語言）

### Phase 3 — 進階功能 (v0.3)
- [ ] 時間戳對齊（ForcedAligner）
- [ ] SRT/VTT 字幕匯出
- [x] Push to Talk 全域快捷鍵（toggle / hold 模式，預設 ctrl+shift+space）
- [x] 轉錄後自動發送到焦點視窗（剪貼串+Ctrl+V）
- [ ] PyInstaller 打包

### Phase 4 — 文字加工 / 記錄 (v0.4)
- [x] OpenCC 繁簡轉換（可在設定頁開關，支援 t2s/s2t/t2tw/tw2s/s2tw 模式）
- [x] 歷史記錄（將錄音 WAV + 轉錄文字存到 `./history/`，背景執行緒不阻塞 UI）
- [x] 累計字數統計（首頁底部 `📊 累計轉錄：N 字` 標籤，持久化到 config.json）
- [x] UI 執行緒審查（確認 `_stop_and_transcribe` 已用 daemon 執行緒，UI 不卡頓）

## 風險與緩解

| 風險 | 緩解方案 |
|------|----------|
| 模型下載失敗 | 提供手動下載指令與離線放置路徑 |
| GPU 記憶體不足 | 自動降級到 0.6B 模型或 CPU 模式 |
| LLM API 連線失敗 | 明確錯誤提示，支援離線轉錄 |

## 變更歷史

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-04-14 | v0.1 | 初始計畫建立 |
| 2026-07-15 | v0.3 | 新增 Push to Talk 全域快捷鍵、轉錄後自動發送功能 |
| 2026-07-15 | v0.4 | 新增 OpenCC 繁簡轉換、歷史記錄、累計字數統計 |
