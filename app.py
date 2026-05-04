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
    if not os.path.exists(lang_path):
        return []
    with open(lang_path, "r", encoding="utf-8") as f:
        return json.load(f)

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
        source, target = ("zh-TW", target_code) if mode == "me" else (target_code, "zh-TW")

        result = GoogleTranslator(source=source, target=target).translate(text)
        return jsonify({"translatedText": result})
    except Exception as e:
        return jsonify({"translatedText": "翻譯失敗"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
