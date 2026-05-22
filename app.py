import os
import json
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from deep_translator import GoogleTranslator
import easyocr

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 改回標準的 Flask 結構，確保 index.html 放在 templates 資料夾內
app = Flask(__name__)

print("🚀 正在初始化免費 OCR 引擎 (EasyOCR)...")
try:
    reader = easyocr.Reader(['ja', 'ko', 'en', 'ch_tra'], gpu=False)
    print("✅ EasyOCR 初始化成功！")
except Exception as e:
    print(f"❌ EasyOCR 初始化失敗: {e}")
    reader = None

OCR_LANG_MAP = {
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

# 萬能路由相容：不管是 /languages 還是 /api/languages 都能通
@app.route('/languages', methods=['GET'])
@app.route('/api/languages', methods=['GET'])
def get_languages():
    return jsonify(LANGUAGES)

@app.route('/translate', methods=['POST'])
@app.route('/api/translate', methods=['POST'])
def translate():
    try:
        data = request.json or {}
        text = data.get('text', '')
        target_name = data.get('target', '英文')
        mode = data.get('mode', 'me')

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

@app.route('/ocr_translate', methods=['POST'])
@app.route('/api/ocr_translate', methods=['POST'])
def ocr_translate():
    try:
        if 'image' not in request.files:
            return jsonify({"ocrOriginal": "", "ocrTranslated": "未接收到圖片檔案"}), 400

        image_file = request.files['image']
        target_lang_name = request.form.get('menu_lang', '日文')  
        image_bytes = image_file.read()

        if not image_bytes or reader is None:
            return jsonify({"ocrOriginal": "引擎未就緒", "ocrTranslated": "請檢查後端日誌"}), 500

        ocr_results = reader.readtext(image_bytes, detail=0) 
        if not ocr_results:
            return jsonify({"ocrOriginal": "未辨識到文字", "ocrTranslated": "請再試一次"})

        ocr_original_text = "\n".join(ocr_results)
        lang_code = OCR_LANG_MAP.get(target_lang_name, 'auto')
        translated_text = GoogleTranslator(source=lang_code, target='zh-TW').translate(ocr_original_text)

        return jsonify({
            "ocrOriginal": ocr_original_text,
            "ocrTranslated": translated_text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)



