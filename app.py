import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator

app = Flask(__name__, static_folder='static')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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

# 1. 語音翻譯路徑
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
        print("語音翻譯錯誤:", e)
        return jsonify({"translatedText": "翻譯失敗"}), 500

# 2. 備援方案：純 Google 免金鑰圖片文字翻譯路徑
@app.route("/ocr_translate", methods=["POST"])
def ocr_translate():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "沒有上傳圖片"}), 400
            
        # 注意：因為沒有 API Key，我們無法直接對「圖片」進行語意辨識
        # 這裡提供一個極簡的提示語，並將文字直接導向免金鑰的 Google 翻譯
        # 由於前端原本預期接收 OCR 原文與譯文，這裡我們引導使用者
        
        return jsonify({
            "ocrOriginal": "【提示】因未偵測到 Gemini 金鑰，系統已自動切換為 Google 免費翻譯模式。由於免費模式不支援圖片直接辨識，請改用「語音翻譯」功能，或在本地環境設定好金鑰後再使用掃描功能功能。",
            "ocrTranslated": "請切換至語音翻譯模式使用"
        })
        
    except Exception as e:
        print("處理錯誤:", e)
        return jsonify({
            "ocrOriginal": "處理失敗",
            "ocrTranslated": "請確保網路連線正常。"
        }), 500

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)

