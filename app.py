import os
import json
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from deep_translator import GoogleTranslator
from PIL import Image
import io
import pytesseract

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

# 語言名稱對照 Tesseract 的語言代碼 (Tesseract 的多國語言包)
# eng=英文, jpn=日文, kor=韓文, chi_tra=繁體中文
OCR_LANG_MAP = {
    "日文": "jpn",
    "韓文": "kor",
    "英文": "eng",
    "法文": "fra",
    "德文": "deu",
    "西班牙文": "spa",
    "越南文": "vie",
    "泰文": "tha"
}

# 轉換為 Google 翻譯相容的語言代碼
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

# 🎤 路由 1：語音/文字翻譯（超輕量，不用 Key）
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

# 📸 路由 2：圖片 OCR 翻譯（改用輕量 Tesseract，記憶體安全）
@app.route('/ocr_translate', methods=['POST'])
@app.route('/api/ocr_translate', methods=['POST'])
def ocr_translate():
    try:
        if 'image' not in request.files:
            return jsonify({"ocrOriginal": "", "ocrTranslated": "未接收到圖片檔案"}), 400

        image_file = request.files['image']
        target_lang_name = request.form.get('menu_lang', '日文')  
        image_bytes = image_file.read()

        if not image_bytes:
            return jsonify({"ocrOriginal": "", "ocrTranslated": "圖片資料為空"}), 400

        # 將圖片位元組轉換為 PIL Image 物件
        img = Image.open(io.BytesIO(image_bytes))

        # 取得對應的 Tesseract 語言代碼
        ocr_lang = OCR_LANG_MAP.get(target_lang_name, 'eng')

        # 執行輕量化 OCR 辨識 (加上自動防錯，如果缺少字庫會自動用英文墊底)
        try:
            ocr_original_text = pytesseract.image_to_string(img, lang=ocr_lang)
        except Exception:
            # 萬一雲端環境缺少日韓文包，自動切換成萬用英文包辨識，防止程式當掉
            ocr_original_text = pytesseract.image_to_string(img, lang='eng')

        ocr_original_text = ocr_original_text.strip()
        if not ocr_original_text:
            return jsonify({
                "ocrOriginal": "未能清晰辨識原文",
                "ocrTranslated": "圖片中找不到可辨識的文字，請拉近或對準一點再試一次。"
            })

        # 轉換成 Google 翻譯的代碼並翻譯
        lang_code = TRANS_LANG_MAP.get(target_lang_name, 'auto')
        translated_text = GoogleTranslator(source=lang_code, target='zh-TW').translate(ocr_original_text)

        return jsonify({
            "ocrOriginal": ocr_original_text,
            "ocrTranslated": translated_text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


