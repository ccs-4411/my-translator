import os
import json
from flask import Flask, request, jsonify, render_template
from deep_translator import GoogleTranslator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

# 網頁支援的外語代碼對照表
TRANS_LANG_MAP = {
    "日文": "ja", "韓文": "ko", "英文": "en", "法文": "fr",
    "德文": "de", "西班牙文": "es", "越南文": "vi", "泰文": "th"
}

lang_json_path = os.path.join(BASE_DIR, 'languages.json')
try:
    with open(lang_json_path, 'r', encoding='utf-8') as f:
        LANGUAGES = json.load(f)
except Exception as e:
    LANGUAGES = [
        {"group": "日韓", "name": "日文", "label": "日本語 🇯🇵", "code": "ja", "voice": "ja-JP"},
        {"group": "常用", "name": "英文", "label": "English 🇺🇸", "code": "en", "voice": "en-US"}
    ]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/languages', methods=['GET'])
@app.route('/api/languages', methods=['GET'])
def get_languages():
    return jsonify(LANGUAGES)

# 🎤 語音與文字翻譯路由（完全免費、不用 API Key）
@app.route('/translate', methods=['POST'])
@app.route('/api/translate', methods=['POST'])
def translate():
    try:
        data = request.json or {}
        text = data.get('text', '')
        target_name = data.get('target', '英文')
        mode = data.get('mode', 'me') # me: 中翻外, other: 外翻中

        if not text:
            return jsonify({"translatedText": ""})

        lang_code = "en"
        for l in LANGUAGES:
            if l['name'] == target_name:
                lang_code = l.get('code', 'en')
                break

        if mode == 'me':
            translated = GoogleTranslator(source='zh-TW', target=lang_code).translate(text)
        else:
            translated = GoogleTranslator(source=lang_code, target='zh-TW').translate(text)

        return jsonify({"translatedText": translated.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 📸 圖片純文字翻譯路由（後端只負責把前端辨識好的字拿來翻譯）
@app.route('/ocr_translate_text', methods=['POST'])
@app.route('/api/ocr_translate_text', methods=['POST'])
def ocr_translate_text():
    try:
        data = request.json or {}
        ocr_text = data.get('text', '').strip()
        target_lang_name = data.get('menu_lang', '日文')

        if not ocr_text:
            return jsonify({"ocrOriginal": "", "ocrTranslated": "未能識別出文字"})

        # 取得對應語言代碼並用免費 Google 翻譯轉成繁中
        lang_code = TRANS_LANG_MAP.get(target_lang_name, 'auto')
        translated_text = GoogleTranslator(source=lang_code, target='zh-TW').translate(ocr_text)

        return jsonify({
            "ocrOriginal": ocr_text,
            "ocrTranslated": translated_text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


