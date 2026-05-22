import os
import json
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from deep_translator import GoogleTranslator
import easyocr

app = Flask(__name__, template_folder='.')

# 初始化 免費的 OCR 辨識器（支援多國語言下載，第一次辨識時會自動下載包）
# 這裡先載入常用的英、日、韓、繁中，EasyOCR 會自動根據圖片切換
print("正在初始化免費 OCR 引擎 (EasyOCR)...")
reader = easyocr.Reader(['ja', 'ko', 'en', 'ch_tra']) 

# 對應 EasyOCR 的語系代碼對照表
OCR_LANG_MAP = {
    "日文": "ja",
    "韓文": "ko",
    "英文": "en",
    "法文": "fr",
    "德文": "de",
    "西班牙文": "es",
    "越南文": "vi",
    "泰文": "th"
}

try:
    with open('languages.json', 'r', encoding='utf-8') as f:
        LANGUAGES = json.load(f)
except Exception as e:
    print(f"⚠️ 讀取 languages.json 失敗: {e}")
    LANGUAGES = [{"group":"日韓","name": "日文", "label": "日本語 🇯🇵", "voice": "ja-JP"}]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/languages', methods=['GET'])
def get_languages():
    return jsonify(LANGUAGES)

# 1. 🎤 免費語音文字翻譯路由（不用 API Key）
@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        text = data.get('text', '')
        target_name = data.get('target', '英文')
        mode = data.get('mode', 'me') 

        if not text:
            return jsonify({"translatedText": ""})

        # 找出 languages.json 中對應的標準語系代碼 (例如 ja, en, ko)
        lang_code = "en"
        for l in LANGUAGES:
            if l['name'] == target_name:
                lang_code = l.get('code', 'en')
                break

        if mode == 'me':
            # 中文 翻成 外語
            translated = GoogleTranslator(source='zh-TW', target=lang_code).translate(text)
        else:
            # 外語 翻成 台灣繁體中文
            translated = GoogleTranslator(source=lang_code, target='zh-TW').translate(text)

        return jsonify({"translatedText": translated.strip()})
    except Exception as e:
        print(f"💡 語音翻譯錯誤: {e}")
        return jsonify({"error": str(e)}), 500

# 2. 📸 免費全場景 OCR 翻譯路由（不用 API Key）
@app.route('/ocr_translate', methods=['POST'])
def ocr_translate():
    print("\n📥 [後端收到請求] 免費 OCR 翻譯觸發！")
    try:
        if 'image' not in request.files:
            return jsonify({"ocrOriginal": "", "ocrTranslated": "未接收到圖片"}), 400

        image_file = request.files['image']
        target_lang_name = request.form.get('menu_lang', '日文')  
        image_bytes = image_file.read()

        if not image_bytes:
            return jsonify({"ocrOriginal": "", "ocrTranslated": "圖片資料為空"}), 400

        # 使用 EasyOCR 進行圖片文字辨識
        print(f"開始辨識圖片中的 {target_lang_name}...")
        ocr_results = reader.readtext(image_bytes, detail=0) # detail=0 只回傳文字列表
        
        if not ocr_results:
            return jsonify({
                "ocrOriginal": "未能清晰辨識原文",
                "ocrTranslated": "圖片中找不到可辨識的文字，請拉近或對準一點再試一次。"
            })

        # 將辨識到的多行文字組合成一段
        ocr_original_text = "\n".join(ocr_results)
        print(f"辨識成功！原文為：\n{ocr_original_text}")

        # 找出該語言對應的簡短代碼
        lang_code = OCR_LANG_MAP.get(target_lang_name, 'auto')

        # 呼叫免費 Google 翻譯轉成繁體中文
        print("正在調用免費 Google 翻譯...")
        translated_text = GoogleTranslator(source=lang_code, target='zh-TW').translate(ocr_original_text)

        return jsonify({
            "ocrOriginal": ocr_original_text,
            "ocrTranslated": translated_text
        })

    except Exception as e:
        print(f"💥 後端 OCR 核心功能出錯: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)



