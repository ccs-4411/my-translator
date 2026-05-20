import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator
import google.generativeai as genai
import io
from PIL import Image

app = Flask(__name__, static_folder='static')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 初始化 Gemini - 使用正確的寫法
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')  # 使用 1.5 flash 速度更快
    print("Gemini API 初始化成功")
else:
    print("警告: 未設定 GEMINI_API_KEY")
    model = None

def load_languages():
    lang_path = os.path.join(BASE_DIR, "languages.json")
    if os.path.exists(lang_path):
        with open(lang_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

LANGUAGES = load_languages()

def get_lang_code(name):
    for lang in LANGUAGES:
        if lang["name"] == name:
            return lang["code"]
    return "en"

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/manifest.json")
def serve_manifest():
    return send_from_directory(BASE_DIR, "manifest.json")

@app.route("/sw.js")
def sw():
    return send_from_directory(BASE_DIR, "sw.js")

@app.route("/languages")
def get_langs():
    return jsonify(LANGUAGES)

# 語音翻譯
@app.route("/translate", methods=["POST"])
def translate():
    try:
        data = request.get_json()
        text = data.get("text", "").strip()
        target_name = data.get("target", "")
        mode = data.get("mode", "me")
        
        if not text:
            return jsonify({"translatedText": ""})
        
        target_code = get_lang_code(target_name)
        
        if mode == "me":
            source = "zh-TW"
            target = target_code
        else:
            source = target_code
            target = "zh-TW"
        
        result = GoogleTranslator(source=source, target=target).translate(text)
        return jsonify({"translatedText": result})
    except Exception as e:
        print("翻譯錯誤:", e)
        return jsonify({"translatedText": "翻譯失敗"}), 500

# Gemini OCR 辨識
@app.route("/ocr_translate", methods=["POST"])
def ocr_translate():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "沒有上傳圖片"}), 400
        
        if model is None:
            return jsonify({
                "ocrOriginal": "API 金鑰未設定",
                "ocrTranslated": "請設定 GEMINI_API_KEY 環境變數"
            }), 500
        
        file = request.files['image']
        image_bytes = file.read()
        
        # 將圖片轉為 PIL Image 並壓縮
        img = Image.open(io.BytesIO(image_bytes))
        
        # 限制圖片大小，加快處理速度
        max_size = 1500
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size))
        
        # 轉為 bytes
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        
        # 使用 Gemini 辨識文字
        prompt = """請仔細閱讀這張圖片中的所有文字，只輸出文字內容，不要加任何說明或翻譯。
如果圖片模糊，請根據你的判斷盡可能輸出最可能的文字。
直接輸出文字即可："""
        
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": buffer.getvalue()}
        ])
        
        ocr_text = response.text.strip() if response.text else ""
        
        if not ocr_text:
            ocr_text = "無法辨識文字，請確保圖片清晰、光線充足"
        
        # 使用 Google 翻譯成繁體中文
        try:
            translated = GoogleTranslator(source='auto', target='zh-TW').translate(ocr_text)
        except Exception as trans_err:
            print("翻譯錯誤:", trans_err)
            translated = "翻譯服務異常，但原文已辨識"
        
        return jsonify({
            "ocrOriginal": ocr_text,
            "ocrTranslated": translated
        })
        
    except Exception as e:
        print("OCR 錯誤:", e)
        return jsonify({
            "ocrOriginal": f"辨識失敗: {str(e)}",
            "ocrTranslated": "請重新拍攝"
        }), 500

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
