import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator

app = Flask(__name__, static_folder='static')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LANG_FILE = "languages.json"

def load_languages():
    if not os.path.exists(LANG_FILE):
        return []
    with open(LANG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

LANGUAGES = load_languages()

def get_lang_code(name):
    for lang in LANGUAGES:
        if lang["name"] == name:
            return lang["code"]
    return "en"

# ===== 路由設定 =====

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/manifest.json")
def serve_manifest():
    return send_from_directory(BASE_DIR, "manifest.json")

@app.route("/languages")
def get_langs():
    return jsonify(LANGUAGES)

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

        # me: 中 -> 外, other: 外 -> 中
        if mode == "other":
            source, target = target_code, "zh-TW"
        else:
            source, target = "zh-TW", target_code

        result = GoogleTranslator(source=source, target=target).translate(text)
        return jsonify({"translatedText": result})
    except Exception as e:
        print("錯誤:", e)
        return jsonify({"translatedText": "翻譯失敗"}), 500

if __name__ == "__main__":
    # PWA 測試建議使用 host="0.0.0.0"
    app.run(host="0.0.0.0", port=5000, debug=True)host="0.0.0.0", port=5000, debug=True)
