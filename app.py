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

        target_lang_code = codes.get(target_name, "en")

        if mode == "other":
            source_lang = target_lang_code
            target_lang = "zh-TW"
        else:
            source_lang = "zh-TW"
            target_lang = target_lang_code

        translated = GoogleTranslator(
            source=source_lang,
            target=target_lang
        ).translate(text)

        return jsonify({"translatedText": translated})

    except Exception as e:
        print("翻譯錯誤:", e)
        return jsonify({"translatedText": "翻譯錯誤"}), 500


# =========================
# 🔥 languages（iPhone 白畫面關鍵修復）
# =========================
@app.route("/languages")
def languages():
    return jsonify([
        {"group":"亞洲","name":"英文","voice":"en-US","label":"English 🇺🇸"},
        {"group":"亞洲","name":"日文","voice":"ja-JP","label":"日本語 🇯🇵"},
        {"group":"亞洲","name":"韓文","voice":"ko-KR","label":"한국어 🇰🇷"},
        {"group":"歐洲","name":"法文","voice":"fr-FR","label":"Français 🇫🇷"},
        {"group":"歐洲","name":"德文","voice":"de-DE","label":"Deutsch 🇩🇪"},
        {"group":"歐洲","name":"西班牙文","voice":"es-ES","label":"Español 🇪🇸"},
        {"group":"亞洲","name":"越南文","voice":"vi-VN","label":"Tiếng Việt 🇻🇳"},
        {"group":"亞洲","name":"泰文","voice":"th-TH","label":"ไทย 🇹🇭"}
    ])


# =========================
# TTS（穩定）
# =========================
@app.route("/tts", methods=["POST"])
def tts():
    try:
        data = request.get_json()
        text = data.get("text", "")
        lang = data.get("lang", "en")

        if not text:
            return jsonify({"error": "no text"}), 400

        filename = f"{uuid.uuid4().hex}.mp3"
        path = os.path.join("/tmp", filename)

        gTTS(text=text, lang=lang).save(path)

        return jsonify({"audio_url": f"/audio/{filename}"})

    except Exception as e:
        print("TTS error:", e)
        return jsonify({"error": "tts failed"}), 500


@app.route("/audio/<file>")
def audio(file):
    return send_from_directory("/tmp", file)


# =========================
# Render 啟動
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
