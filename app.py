# app.py
import os
import json
from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory
)
from flask_cors import CORS
from deep_translator import GoogleTranslator
# 引入 Google 新版 GenAI 套件
from google import genai
from google.genai import types

app = Flask(
    __name__,
    static_folder='static'
)

CORS(app)

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# 初始化 Gemini 客戶端 (會自動讀取環境變數 GEMINI_API_KEY)
# 如果不想設環境變數，也可以寫成 client = genai.Client(api_key="你的KEY")
client = genai.Client()

# =========================
# 載入語言
# =========================
def load_languages():
    lang_path = os.path.join(
        BASE_DIR,
        "languages.json"
    )
    if os.path.exists(lang_path):
        with open(
            lang_path,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)
    return []

LANGUAGES = load_languages()

# =========================
# 取得語言代碼
# =========================
def get_lang_code(name):
    for lang in LANGUAGES:
        if lang["name"] == name:
            return lang["code"]
    return "en"

# =========================
# 首頁、manifest、sw.js
# =========================
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

# =========================
# 語音翻譯 API
# =========================
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

        result = GoogleTranslator(
            source=source,
            target=target
        ).translate(text)

        return jsonify({"translatedText": result})

    except Exception as e:
        print("翻譯錯誤:", e)
        return jsonify({"translatedText": "翻譯失敗"}), 500

# =========================
# 【全新加入】終極拍照辨識與翻譯 API
# =========================
@app.route("/ocr_translate", methods=["POST"])
def ocr_translate():
    try:
        # 1. 檢查有沒有上傳檔案
        if 'image' not in request.files:
            return jsonify({"error": "沒有上傳圖片"}), 400
            
        file = request.files['image']
        image_bytes = file.read()
        
        # 2. 呼叫最強大的 Gemini 2.5 Flash 來進行視覺辨識與直接翻譯
        # 我們直接給 AI 提示詞，要它同時吐出「原文」與「中文翻譯」，免去二次呼叫 API 的時間
        prompt = (
            "這是一張由翻譯 APP 拍攝的照片。請精準辨識出圖片中所有的文字（OCR），"
            "並將這些文字翻譯成『繁體中文（台灣習慣用語）』。\n"
            "請嚴格並僅以 JSON 格式回傳，格式如下：\n"
            '{"originalText": "辨識出的原本文字", "translatedText": "翻譯後的繁體中文"}'
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=file.content_type
                ),
                prompt,
            ],
            # 強制要求模型只回傳 JSON 物件
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        # 3. 解析 AI 回傳的 JSON 結果
        result_json = json.loads(response.text)
        return jsonify({
            "ocrOriginal": result_json.get("originalText", "").strip(),
            "ocrTranslated": result_json.get("translatedText", "").strip()
        })

    except Exception as e:
        print("拍照辨識或翻譯錯誤:", e)
        return jsonify({
            "ocrOriginal": "辨識失敗",
            "ocrTranslated": "後端服務錯誤"
        }), 500

# =========================
# Health Check
# =========================
@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
