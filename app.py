import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator
from gtts import gTTS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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
# TTS（手機穩定版）
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

        tts = gTTS(text=text, lang=lang)
        tts.save(path)

        return jsonify({"audio_url": f"/audio/{filename}"})

    except Exception as e:
        print("TTS error:", e)
        return jsonify({"error": "tts failed"}), 500


@app.route("/audio/<file>")
def audio(file):
    return send_from_directory("/tmp", file)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
