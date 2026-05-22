import os
import json
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from deep_translator import GoogleTranslator
import easyocr

# 1. 確保路徑正確：取得目前 app.py 所在的絕對路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 初始化 Flask：強制導向絕對路徑，防止 Render 找不到網頁檔案
app = Flask(
    __name__, 
    template_folder=BASE_DIR, 
    static_folder=os.path.join(BASE_DIR, 'static')
)

print("🚀 正在初始化免費 OCR 引擎 (EasyOCR)...")
try:
    # 針對 Render 免費版優化：載入核心 4 語系，並強制關閉 GPU 模式以節省記憶體
    reader = easyocr.Reader(['ja', 'ko', 'en', 'ch_tra'], gpu=False)
    print("✅ EasyOCR 初始化成功！")
except Exception as e:
    print(f"❌ EasyOCR 初始化失敗: {e}")
    reader = None

# EasyOCR 語言代碼對照表
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

# 3. 讀取語系設定檔（使用絕對路徑防止 404）
lang_json_path = os.path.join(BASE_DIR, 'languages.json')
try:
    with open(lang_json_path, 'r', encoding='utf-8') as f:
        LANGUAGES = json.load(f)
    print("✅ 成功載入 languages.json")
except Exception as e:
    print(f"⚠️ 讀取 languages.json 失敗: {e}。啟動備用選單機制。")
    # 萬一檔案遺失的防護機制
    LANGUAGES = [
        {"group": "日韓", "name": "日文", "label": "日本語 🇯🇵", "code": "ja", "voice": "ja-JP"},
        {"group": "常用", "name": "英文", "label": "English 🇺🇸", "code": "en", "voice": "en-US"},
        {"group": "日韓", "name": "韓文", "label": "한국어 🇰🇷", "code": "ko", "voice": "ko-KR"}
    ]

@app.route('/')
def index():
    # 導向跟 app.py 放在同一個目錄下的 index.html
    return render_template('index.html')

@app.route('/languages', methods=['GET'])
@app.route('/api/languages', methods=['GET'])  # 同時支援兩種前端路由格式，防 404
def get_languages():
    return jsonify(LANGUAGES)

# 🎤 路由 1：語音/文字翻譯（完全免費、不用 API Key）
@app.route('/translate', methods=['POST'])
@app.route('/api/translate', methods=['POST'])  # 同時支援兩種前端路由格式，防 404
def translate():
    try:
        data = request.json or {}
        text = data.get('text', '')
        target_name = data.get('target', '英文')
        mode = data.get('mode', 'me')  # me: 中翻外, other: 外翻中

        if not text:
            return jsonify({"translatedText": ""})

        # 從語言清單中找出對應的 ISO 代碼（例如 ja, en）
        lang_code = "en"
        for l in LANGUAGES:
            if l['name'] == target_name:
                lang_code = l.get('code', 'en')
                break

        # 調用免費 Google 翻譯網頁接口
        if mode == 'me':
            translated = GoogleTranslator(source='zh-TW', target=lang_code).translate(text)
        else:
            translated = GoogleTranslator(source=lang_code, target='zh-TW').translate(text)

        return jsonify({"translatedText": translated.strip()})
    except Exception as e:
        print(f"💡 文字翻譯出錯: {e}")
        return jsonify({"error": str(e)}), 500

# 📸 路由 2：圖片 OCR 翻譯（完全免費、不用 API Key）
@app.route('/ocr_translate', methods=['POST'])
@app.route('/api/ocr_translate', methods=['POST'])  # 同時支援兩種前端路由格式，防 404
def ocr_translate():
    print("\n📥 [後端收到請求] 免費 OCR 翻譯觸發！")
    try:
        if 'image' not in request.files:
            return jsonify({"ocrOriginal": "", "ocrTranslated": "未接收到圖片檔案"}), 400

        image_file = request.files['image']
        target_lang_name = request.form.get('menu_lang', '日文')  
        image_bytes = image_file.read()

        if not image_bytes:
            return jsonify({"ocrOriginal": "", "ocrTranslated": "圖片資料為空"}), 400

        if reader is None:
            return jsonify({"ocrOriginal": "OCR 引擎未啟動", "ocrTranslated": "伺服器記憶體不足，OCR 模組未能成功載入。"}), 500

        # 進行圖片文字辨識
        print(f"⏳ 開始辨識圖片中的 {target_lang_name}...")
        ocr_results = reader.readtext(image_bytes, detail=0) 
        
        if not ocr_results:
            return jsonify({
                "ocrOriginal": "未能清晰辨識原文",
                "ocrTranslated": "圖片中找不到可辨識的文字，請拉近或對準一點再試一次。"
            })

        ocr_original_text = "\n".join(ocr_results)
        print(f"🎉 辨識成功！原文：\n{ocr_original_text}")

        # 轉換為 Google 翻譯相容的語言代碼
        lang_code = OCR_LANG_MAP.get(target_lang_name, 'auto')

        # 調用免費 Google 翻譯轉回台灣繁體中文
        print("⏳ 正在調用免費 Google 翻譯...")
        translated_text = GoogleTranslator(source=lang_code, target='zh-TW').translate(ocr_original_text)

        return jsonify({
            "ocrOriginal": ocr_original_text,
            "ocrTranslated": translated_text
        })

    except Exception as e:
        print(f"💥 後端 OCR 功能出錯: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # 本地測試用，Render 上會自動被 Gunicorn 接管
    app.run(host='0.0.0.0', port=5000, debug=True)



