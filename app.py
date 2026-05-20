import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator
from google import genai
from google.genai import types
import io
from PIL import Image, ImageEnhance, ImageFilter

app = Flask(__name__, static_folder='static')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 初始化 Gemini
client = genai.Client()

# ================== 載入語言清單 ==================
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

# ================== 靜態路由 ==================
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

# ================== 語音翻譯 (維持 Google 翻譯) ==================
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
        
        # 使用 Google 翻譯
        result = GoogleTranslator(source=source, target=target).translate(text)
        return jsonify({"translatedText": result})
    except Exception as e:
        print("翻譯錯誤:", e)
        return jsonify({"translatedText": "翻譯失敗"}), 500

# ================== OCR 辨識 (Gemini 強化) + Google 翻譯 ==================
def preprocess_image_for_ocr(image_bytes):
    """後端強化：對比度提升 + 銳利化"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # 限制最大寬度
        max_width = 2000
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # 對比度增強
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.35)
        
        # 銳利化
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=92, optimize=True)
        return output.getvalue()
    except Exception as e:
        print("預處理異常:", e)
        return image_bytes

@app.route("/ocr_translate", methods=["POST"])
def ocr_translate():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "沒有上傳圖片"}), 400
        
        file = request.files['image']
        raw_bytes = file.read()
        
        # 後端預處理
        enhanced_image_bytes = preprocess_image_for_ocr(raw_bytes)
        
        # Gemini 強力 OCR 提示詞
        prompt_text = (
            "你是一個精準的OCR引擎。嚴格遵守以下規則：\n"
            "1. 只輸出圖片中的原始文字，不要翻譯、不要解釋、不要加註釋。\n"
            "2. 保留標點符號、數字、空格和換行結構。\n"
            "3. 支援繁體中文、簡體中文、英文、日文、韓文等多種語言混合。\n"
            "4. 不要使用Markdown、不要用代碼框。\n"
            "5. 找出圖片中所有可辨識的文字，包括小字、按鈕文字。"
        )
        
        # Gemini 辨識文字
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[
                types.Part.from_bytes(data=enhanced_image_bytes, mime_type="image/jpeg"),
                prompt_text
            ]
        )
        
        ocr_text = response.text.strip() if response.text else ""
        
        if not ocr_text or len(ocr_text) < 2:
            ocr_text = "無法辨識文字，請確認圖片光線充足且文字清晰。"
        
        # 使用 Google 翻譯成繁體中文
        try:
            translated = GoogleTranslator(source='auto', target='zh-TW').translate(ocr_text)
        except Exception as trans_err:
            print("翻譯錯誤:", trans_err)
            translated = "翻譯服務暫時異常"
        
        return jsonify({
            "ocrOriginal": ocr_text,
            "ocrTranslated": translated
        })
        
    except Exception as e:
        print("OCR 錯誤:", e)
        return jsonify({
            "ocrOriginal": "辨識失敗，請重新拍攝清楚圖片",
            "ocrTranslated": "請嘗試光線充足、對焦清晰"
        }), 500

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
