import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator
from gtts import gTTS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# =========================
# 主頁
# =========================
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

        codes = {
            "英文": "en",
            "日文": "ja",
            "韓文": "ko",
            "越南文": "vi",
            "西班牙文": "es",
            "泰文": "th",
            "法文": "fr",
            "德文": "de",
            "印尼文": "id",
            "俄文": "ru",
            "義大利文": "it",
            "菲律賓文": "tl"
        }

        target = codes.get(target_name, "en")

        if mode == "other":
            source = target
            target_lang = "zh-TW"
        else:
            source = "zh-TW"
            target_lang = target

        result = GoogleTranslator(source=source, target=target_lang).translate(text)

        return jsonify({"translatedText": result})

    except Exception as e:
        print("error:", e)
        return jsonify({"translatedText": "錯誤"}), 500


# =========================
# languages API
# =========================
@app.route("/languages")
def languages():
    return jsonify([
        {"name":"英文","voice":"en-US"},
        {"name":"日文","voice":"ja-JP"},
        {"name":"韓文","voice":"ko-KR"},
        {"name":"法文","voice":"fr-FR"},
        {"name":"德文","voice":"de-DE"},
        {"name":"西班牙文","voice":"es-ES"},
        {"name":"越南文","voice":"vi-VN"},
        {"name":"泰文","voice":"th-TH"}
    ])


# =========================
# TTS
# =========================
@app.route("/tts", methods=["POST"])
def tts():
    try:
        data = request.get_json()
        text = data.get("text", "")
        lang = data.get("lang", "en")

        filename = f"{uuid.uuid4().hex}.mp3"
        path = os.path.join("/tmp", filename)

        gTTS(text=text, lang=lang).save(path)

        return jsonify({"audio_url": f"/audio/{filename}"})

    except Exception as e:
        print(e)
        return jsonify({"error":"tts"}), 500


@app.route("/audio/<file>")
def audio(file):
    return send_from_directory("/tmp", file)


# =========================
# PWA manifest
# =========================
@app.route("/manifest.json")
def manifest():
    return jsonify({
        "name": "翻譯官",
        "short_name": "翻譯",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#1a73e8"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
