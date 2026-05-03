import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ===== 載入語言 =====
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

# ===== API =====
@app.route("/languages")
def languages():
    return jsonify(LANGUAGES)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        return send_from_directory(BASE_DIR, "index.html")

    try:
        data = request.get_json()
        text = data.get("text", "").strip()
        target_name = data.get("target", "英文")
        mode = data.get("mode", "me")

        if not text:
            return jsonify({"translatedText": ""})

        target_code = get_lang_code(target_name)

        if mode == "other":
            source = target_code
            target = "zh-TW"
        else:
            source = "zh-TW"
            target = target_code

        result = GoogleTranslator(source=source, target=target).translate(text)

        return jsonify({"translatedText": result})

    except Exception as e:
        print("錯誤:", e)
        return jsonify({"translatedText": "翻譯失敗"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

