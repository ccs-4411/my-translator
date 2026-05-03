import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator
from gtts import gTTS

# 🔥 正確 static（解決 /static 404）
app = Flask(__name__, static_folder='static')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# =========================
# 首頁（一定要支援 GET，避免 405）
# =========================
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        return send_from_directory(BASE_DIR, "index.html")

    try:
        # 🔥 防 415
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"translatedText": ""})

        text = data.get("text", "").strip()
        target = data.get("target", "英文")
        mode = data.get("mode", "me")

        if not text:
            return jsonify({"translatedText": ""})

        codes = {
            "英文": "en",
            "日文": "ja",
            "韓文": "ko",
            "西班牙文": "es",
            "法文": "fr",
            "德文": "de",
            "泰文": "th",
            "越南文": "vi"
        }

        target_code = codes.get(target, "en")

        if mode == "other":
            source_lang = target_code
            target_lang = "zh-TW"
        else:
            source_lang = "zh-TW"
            target_lang = target_code

        translated = GoogleTranslator(
            source=source_lang,
            target=target_lang
        ).translate(text)

        print(f"[翻譯] {text} → {translated}")

        return jsonify({"translatedText": translated})

    except Exception as e:
        print("翻譯錯誤:", e)
        return jsonify({"translatedText": "翻譯失敗"}), 500


# =========================
# 語言 API
# =========================
@app.route("/languages")
def languages():
    return jsonify([
        {"name": "英文", "voice": "en-US"},
        {"name": "日文", "voice": "ja-JP"},
        {"name": "韓文", "voice": "ko-KR"},
        {"name": "西班牙文", "voice": "es-ES"},
        {"name": "法文", "voice": "fr-FR"},
        {"name": "德文", "voice": "de-DE"},
        {"name": "泰文", "voice": "th-TH"},
        {"name": "越南文", "voice": "vi-VN"}
    ])


# =========================
# 🔊 TTS（語音）
# =========================
@app.route("/tts", methods=["POST"])
def tts():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "no data"}), 400

        text = data.get("text", "")
        lang = data.get("lang", "en")

        if not text:
            return jsonify({"error": "empty"}), 400

        filename = f"{uuid.uuid4().hex}.mp3"
        path = f"/tmp/{filename}"

        gTTS(text=text, lang=lang).save(path)

        return jsonify({"audio_url": f"/audio/{filename}"})

    except Exception as e:
        print("TTS錯誤:", e)
        return jsonify({"error": "tts fail"}), 500


# =========================
# 播放音檔
# =========================
@app.route("/audio/<filename>")
def audio(filename):
    return send_from_directory("/tmp", filename)


# =========================
# 🔥 static（保險）
# =========================
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


# =========================
# 健康檢查（Render）
# =========================
@app.route("/health")
def health():
    return "ok"


# =========================
# 啟動
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
