"""Polish and translation templates for the LLM polisher — v0.5.

Each template is a dict with:
    name   : str  — display name shown in the OptionMenu
    prompt : str  — system prompt injected into the LLM call
"""

from __future__ import annotations

# ──────────────────────────────────────────────────────────────────────────────
# 潤稿模板 (20 種情境)
# ──────────────────────────────────────────────────────────────────────────────

POLISH_TEMPLATES: list[dict[str, str]] = [
    {
        "name": "通用潤稿",
        "prompt": (
            "請潤飾以下語音辨識文字，修正錯字、加標點符號，保持原意，"
            "使文句流暢自然。只輸出潤飾後的文字，不要加說明。"
        ),
    },
    {
        "name": "正式公文",
        "prompt": (
            "請將以下口語文字改寫為正式公文語體：用詞嚴謹、句式完整、標點正確。"
            "只輸出改寫後的文字，不要加說明。"
        ),
    },
    {
        "name": "Email 草稿",
        "prompt": (
            "請將以下語音筆記整理成一封專業的商務電子郵件，包含適當的稱謂與結語。"
            "只輸出郵件正文，不要加說明。"
        ),
    },
    {
        "name": "會議記錄",
        "prompt": (
            "請將以下口語錄音整理為結構化的會議記錄，分為：討論重點、決議事項、"
            "待辦行動。條列式輸出，不要加說明。"
        ),
    },
    {
        "name": "演講稿",
        "prompt": (
            "請將以下口語表達整理為流暢的演講稿：節奏感強、段落清晰、情感到位。"
            "只輸出演講稿，不要加說明。"
        ),
    },
    {
        "name": "學術論文摘要",
        "prompt": (
            "請將以下文字改寫為適合學術論文的摘要風格：客觀、精煉、無口語化表達。"
            "只輸出摘要，不要加說明。"
        ),
    },
    {
        "name": "社群媒體貼文",
        "prompt": (
            "請將以下文字改寫為吸引人的社群媒體貼文，語氣輕鬆有趣，"
            "可加入適度 emoji，長度控制在 280 字以內。只輸出貼文，不要加說明。"
        ),
    },
    {
        "name": "新聞稿",
        "prompt": (
            "請將以下文字整理為專業新聞稿格式：倒金字塔結構、用語客觀中立、"
            "包含必要的 5W1H。只輸出新聞稿，不要加說明。"
        ),
    },
    {
        "name": "故事敘述",
        "prompt": (
            "請將以下說話內容改寫為生動的故事敘述形式，加強描寫細節、"
            "情感與節奏感，使讀者沉浸其中。只輸出故事內容，不要加說明。"
        ),
    },
    {
        "name": "精簡摘要",
        "prompt": (
            "請將以下文字精簡為簡短摘要（不超過原文長度的 30%），"
            "保留最核心的資訊。只輸出摘要，不要加說明。"
        ),
    },
    {
        "name": "口語化改寫",
        "prompt": (
            "請將以下較為生硬或正式的文字改寫為自然流暢的口語表達，"
            "適合日常對話使用。只輸出改寫後的文字，不要加說明。"
        ),
    },
    {
        "name": "標點符號修正",
        "prompt": (
            "請僅為以下文字加入正確的標點符號（逗號、句號、問號、驚嘆號等），"
            "不要更改任何文字內容。只輸出加標點後的文字，不要加說明。"
        ),
    },
    {
        "name": "客服回覆",
        "prompt": (
            "請將以下文字改寫為專業的客服回覆語氣：禮貌、同理、解決導向，"
            "適合直接回覆給客戶。只輸出回覆內容，不要加說明。"
        ),
    },
    {
        "name": "產品描述",
        "prompt": (
            "請將以下文字改寫為吸引購買的產品描述文案：突出賣點、"
            "語氣積極、引發消費者共鳴。只輸出描述文案，不要加說明。"
        ),
    },
    {
        "name": "法律條文風格",
        "prompt": (
            "請將以下文字改寫為法律條文風格：措辭嚴謹、定義明確、"
            "句式完整規範。只輸出改寫後的文字，不要加說明。"
        ),
    },
    {
        "name": "醫療報告",
        "prompt": (
            "請將以下語音文字整理為醫療記錄格式：客觀陳述症狀、使用標準醫學術語、"
            "條理清晰。只輸出報告內容，不要加說明。"
        ),
    },
    {
        "name": "教學說明",
        "prompt": (
            "請將以下文字改寫為清晰易懂的教學說明：步驟條列、語氣親切、"
            "適合初學者理解。只輸出說明內容，不要加說明。"
        ),
    },
    {
        "name": "詩意改寫",
        "prompt": (
            "請將以下文字改寫為富有詩意的散文形式：意象豐富、語言優美、"
            "情感細膩。只輸出改寫後的內容，不要加說明。"
        ),
    },
    {
        "name": "錯字修正",
        "prompt": (
            "請僅修正以下文字中的錯別字和語音辨識錯誤，不要更改句子結構或措辭。"
            "只輸出修正後的文字，不要加說明。"
        ),
    },
    {
        "name": "訪談問題整理",
        "prompt": (
            "請將以下訪談或採訪內容整理為問答格式，清楚區分提問與回答，"
            "保留原意但使表達更清晰。只輸出整理後的問答，不要加說明。"
        ),
    },
]

# ──────────────────────────────────────────────────────────────────────────────
# 翻譯模板 (20 國語言)
# ──────────────────────────────────────────────────────────────────────────────

TRANSLATION_TEMPLATES: list[dict[str, str]] = [
    {
        "name": "→ 英文 English",
        "prompt": (
            "Please translate the following text into natural, fluent English. "
            "Preserve the original meaning and tone. Output only the translated text."
        ),
    },
    {
        "name": "→ 日文 日本語",
        "prompt": (
            "以下のテキストを自然で流暢な日本語に翻訳してください。"
            "原文の意味とトーンを保ってください。翻訳文のみを出力してください。"
        ),
    },
    {
        "name": "→ 韓文 한국어",
        "prompt": (
            "다음 텍스트를 자연스럽고 유창한 한국어로 번역해 주세요. "
            "원문의 의미와 어조를 유지해 주세요. 번역문만 출력해 주세요."
        ),
    },
    {
        "name": "→ 簡體中文",
        "prompt": (
            "请将以下文字翻译成自然流畅的简体中文，保留原文的意思和语气。"
            "只输出翻译结果，不要加说明。"
        ),
    },
    {
        "name": "→ 繁體中文",
        "prompt": (
            "請將以下文字翻譯成自然流暢的繁體中文，保留原文的意思和語氣。"
            "只輸出翻譯結果，不要加說明。"
        ),
    },
    {
        "name": "→ 法文 Français",
        "prompt": (
            "Veuillez traduire le texte suivant en français naturel et fluide, "
            "en préservant le sens et le ton originaux. "
            "Produisez uniquement le texte traduit."
        ),
    },
    {
        "name": "→ 德文 Deutsch",
        "prompt": (
            "Bitte übersetzen Sie den folgenden Text ins natürliche, flüssige Deutsch. "
            "Behalten Sie Bedeutung und Ton bei. Geben Sie nur den übersetzten Text aus."
        ),
    },
    {
        "name": "→ 西班牙文 Español",
        "prompt": (
            "Por favor, traduzca el siguiente texto al español natural y fluido, "
            "preservando el significado y el tono originales. "
            "Produzca solo el texto traducido."
        ),
    },
    {
        "name": "→ 葡萄牙文 Português",
        "prompt": (
            "Por favor, traduza o texto a seguir para o português natural e fluente, "
            "preservando o significado e o tom originais. "
            "Produza apenas o texto traduzido."
        ),
    },
    {
        "name": "→ 義大利文 Italiano",
        "prompt": (
            "Si prega di tradurre il testo seguente in italiano naturale e scorrevole, "
            "preservando il significato e il tono originali. "
            "Producete solo il testo tradotto."
        ),
    },
    {
        "name": "→ 俄文 Русский",
        "prompt": (
            "Пожалуйста, переведите следующий текст на естественный и свободный русский язык, "
            "сохраняя исходный смысл и тон. Выведите только переведённый текст."
        ),
    },
    {
        "name": "→ 阿拉伯文 العربية",
        "prompt": (
            "يرجى ترجمة النص التالي إلى اللغة العربية الطبيعية والسلسة، "
            "مع الحفاظ على المعنى والنبرة الأصليين. "
            "أخرج النص المترجم فقط."
        ),
    },
    {
        "name": "→ 泰文 ภาษาไทย",
        "prompt": (
            "กรุณาแปลข้อความต่อไปนี้เป็นภาษาไทยที่เป็นธรรมชาติและคล่องแคล่ว "
            "โดยรักษาความหมายและโทนดั้งเดิม ให้แสดงเฉพาะข้อความที่แปลแล้ว"
        ),
    },
    {
        "name": "→ 越南文 Tiếng Việt",
        "prompt": (
            "Vui lòng dịch văn bản sau sang tiếng Việt tự nhiên và trôi chảy, "
            "giữ nguyên nghĩa và giọng điệu ban đầu. "
            "Chỉ xuất văn bản đã dịch."
        ),
    },
    {
        "name": "→ 印尼文 Bahasa Indonesia",
        "prompt": (
            "Harap terjemahkan teks berikut ke dalam bahasa Indonesia yang alami dan lancar, "
            "dengan mempertahankan makna dan nada aslinya. "
            "Hasilkan teks terjemahan saja."
        ),
    },
    {
        "name": "→ 荷蘭文 Nederlands",
        "prompt": (
            "Vertaal de volgende tekst naar natuurlijk en vloeiend Nederlands, "
            "met behoud van de originele betekenis en toon. "
            "Geef alleen de vertaalde tekst weer."
        ),
    },
    {
        "name": "→ 波蘭文 Polski",
        "prompt": (
            "Proszę przetłumaczyć poniższy tekst na naturalny i płynny język polski, "
            "zachowując oryginalne znaczenie i ton. "
            "Wygeneruj tylko przetłumaczony tekst."
        ),
    },
    {
        "name": "→ 土耳其文 Türkçe",
        "prompt": (
            "Lütfen aşağıdaki metni doğal ve akıcı Türkçeye çevirin, "
            "orijinal anlam ve tonu koruyun. "
            "Sadece çevrilmiş metni çıktı olarak verin."
        ),
    },
    {
        "name": "→ 印度文 हिन्दी",
        "prompt": (
            "कृपया निम्नलिखित पाठ का प्राकृतिक और प्रवाहमय हिंदी में अनुवाद करें, "
            "मूल अर्थ और स्वर को बनाए रखें। "
            "केवल अनुवादित पाठ आउटपुट करें।"
        ),
    },
    {
        "name": "→ 瑞典文 Svenska",
        "prompt": (
            "Vänligen översätt följande text till naturlig och flytande svenska, "
            "bevara den ursprungliga meningen och tonen. "
            "Mata bara ut den översatta texten."
        ),
    },
]
