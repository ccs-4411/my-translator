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

# ================== 語音翻譯 ==================
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

# ================== Gemini OCR 強化版 (專為藥品文字) ==================
def preprocess_image_advanced(image_bytes):
    """進階圖片前處理：去反光、增強對比、銳利化"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # 縮放到合理大小
        max_width = 2000
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # 強烈對比增強 (藥品文字通常較淡)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        
        # 亮度增強
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        
        # 銳利化
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=200, threshold=2))
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=95, optimize=True)
        return output.getvalue()
    except Exception as e:
        print("預處理異常:", e)
        return image_bytes

@app.route("/ocr_gemini", methods=["POST"])
def ocr_gemini():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "沒有上傳圖片"}), 400
        
        file = request.files['image']
        mode = request.form.get('mode', 'medicine')
        raw_bytes = file.read()
        
        # 進階圖片預處理
        enhanced_image_bytes = preprocess_image_advanced(raw_bytes)
        
        # 根據模式選擇不同的提示詞
        if mode == "medicine":
            prompt_text = """你是專業的藥品標籤OCR系統。請仔細分析這張藥品包裝/藥包/藥盒的圖片。

重要規則（嚴格遵守）：
1. 只輸出圖片中的原始文字，不要翻譯、不要解釋、不要加註釋
2. 特別注意辨識以下藥品相關內容：
   - 藥品名稱 (Brand/Generic name)
   - 劑量 (mg, mcg, g 等)
   - 用法用量 (Take, Daily, Once, Twice, etc.)
   - 有效期限 (EXP, Expiry, Use by)
   - 批號 (Lot, Batch)
3. 保留所有數字、單位、標點符號
4. 如果文字有反光或模糊，根據上下文盡可能推測正確文字
5. 按原始順序輸出，保留換行

請開始辨識藥品圖片中的文字："""
        else:
            prompt_text = """你是精準的OCR引擎。請仔細掃描這張圖片中的所有文字。

規則：
1. 只輸出原始文字，不要翻譯、不要解釋
2. 保留標點符號、數字、空格和換行
3. 支援英文、中文、日文、韓文混合
4. 不要使用Markdown或代碼框

請輸出圖片中的文字："""
        
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[
                types.Part.from_bytes(data=enhanced_image_bytes, mime_type="image/jpeg"),
                prompt_text
            ]
        )
        
        ocr_text = response.text.strip() if response.text else ""
        
        if not ocr_text or len(ocr_text) < 3:
            ocr_text = "無法辨識文字。請確認：圖片光線充足、文字清晰、藥品平貼無反光"
        
        # 翻譯成繁體中文
        try:
            translated = GoogleTranslator(source='auto', target='zh-TW').translate(ocr_text)
        except Exception as trans_err:
            print("翻譯錯誤:", trans_err)
            translated = "翻譯服務暫時異常，但原文已辨識如上"
        
        return jsonify({
            "ocrText": ocr_text,
            "translatedText": translated
        })
        
    except Exception as e:
        print("OCR 錯誤:", e)
        return jsonify({
            "ocrText": f"辨識失敗: {str(e)}",
            "translatedText": "請重新拍攝，確保光線充足、文字清晰"
        }), 500

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
