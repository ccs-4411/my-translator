import os
import json
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from deep_translator import GoogleTranslator
from gtts import gTTS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LANG_FILE = os.path.join(BASE_DIR, "languages.json")

def load_languages():
    with open(LANG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

LANGS = load_languages()

def get_code(name):
    for l in LANGS:
        if l["name"] == name:
            return l["code"]
    return "en"

# =========================
# 翻譯 API
# =========================
@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json(force=True)

    text = data.get("text", "")
    target = get_code(data.get("target"))
    mode = data.get("mode", "me")

    if mode == "other":
        source = target
        target = "zh-TW"
    else:
        source = "zh-TW"

    result = GoogleTranslator(source=source, target=target).translate(text)

    return jsonify({"text": result})

# =========================
# TTS API
# =========================
@app.route("/tts", methods=["POST"])
def tts():
    data = request.get_json(force=True)

    text = data.get("text")
    lang = data.get("lang", "en")

    filename = f"{uuid.uuid4().hex}.mp3"
    path = os.path.join(BASE_DIR, filename)

    gTTS(text=text, lang=lang).save(path)

    return jsonify({"url": "/" + filename})

# =========================
# Render
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
