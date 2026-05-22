import os
import json
from flask import Flask, request, jsonify, render_template
from deep_translator import GoogleTranslator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

# OCR 專用語言代碼映射表
TRANS_LANG_MAP = {
    "日文": "ja", "韓文": "ko", "英文": "en", "法文": "fr",
    "德文": "de", "西班牙文": "es", "越南文": "vi", "泰文": "th"
}

# 載入自訂的語言選單設定
lang_json_path = os.path.join(BASE_DIR, 'languages.json')
try:
    with open(lang_json_path, 'r', encoding='utf-8') as f:
        LANGUAGES = json.load(f)
except Exception as e:
    # 預備防呆選單
    LANGUAGES = [
        {"group": "日韓", "name": "日文", "label": "日本語 🇯🇵", "code": "ja", "voice": "ja-JP"},
        {"group": "常用", "name": "英文", "label": "English 🇺🇸", "code": "en", "voice": "en-US"},
        {"group": "日韓", "name": "韓文", "label": "한국어 🇰🇷", "code": "ko", "voice": "ko-KR"}
    ]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/languages', methods=['GET'])
@app.route('/api/languages', methods=['GET'])
def get_languages():
    return jsonify(LANGUAGES)

# 🎤 語音與文字雙向翻譯路由（即時顯示日誌與監控）
@app.route('/translate', methods=['POST'])
@app.route('/api/translate', methods=['POST'])
def translate():
    try:
        data = request.json or {}
        text = data.get('text', '').strip()
        target_name = data.get('target', '英文')
        mode = data.get('mode', 'me') # me: 中翻外, other: 外翻中

        if not text:
            return jsonify({"translatedText": ""})

        # 尋找對應的語言代碼
        lang_code = "en"
        for l in LANGUAGES:
            if l['name'] == target_name:
                lang_code = l.get('code', 'en')
                break

        # 執行免費 Google 翻譯
        if mode == 'me':
            print(f"[Log] 正在將中文翻譯為 {target_name}: {text}")
            translated = GoogleTranslator(source='zh-TW', target=lang_code).translate(text)
        else:
            print(f"[Log] 正在將 {target_name} 翻譯為中文: {text}")
            translated = GoogleTranslator(source=lang_code, target='zh-TW').translate(text)

        print(f"[Log] 翻譯結果: {translated}")
        return jsonify({"translatedText": translated.strip()})
    except Exception as e:
        print(f"[Error] 翻譯發生錯誤: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 📸 圖片 OCR 文字翻譯路由
@app.route('/ocr_translate_text', methods=['POST'])
@app.route('/api/ocr_translate_text', methods=['POST'])
def ocr_translate_text():
    try:
        data = request.json or {}
        ocr_text = data.get('text', '').strip()
        target_lang_name = data.get('menu_lang', '日文')

        if not ocr_text:
            return jsonify({"ocrOriginal": "", "ocrTranslated": "未能識別出文字"})

        print(f"[Log] 收到前端 OCR 文字 ({target_lang_name})，準備翻譯...")
        lang_code = TRANS_LANG_MAP.get(target_lang_name, 'auto')
        translated_text = GoogleTranslator(source=lang_code, target='zh-TW').translate(ocr_text)

        print(f"[Log] OCR 翻譯成功")
        return jsonify({
            "ocrOriginal": ocr_text,
            "ocrTranslated": translated_text
        })
    except Exception as e:
        print(f"[Error] OCR 翻譯發生錯誤: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


