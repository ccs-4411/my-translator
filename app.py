import os, uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator
from gtts import gTTS

app = Flask(__name__, static_folder='static')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# =========================
# 前端
# =========================
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


# =========================
# 語言
# =========================
@app.route("/languages")
def languages():
    return jsonify([
        {"name":"英文","voice":"en-US"},
        {"name":"日文","voice":"ja-JP"},
        {"name":"韓文","voice":"ko-KR"},
        {"name":"西班牙文","voice":"es-ES"},
        {"name":"法文","voice":"fr-FR"},
        {"name":"德文","voice":"de-DE"},
        {"name":"泰文","voice":"th-TH"},
        {"name":"越南文","voice":"vi-VN"}
    ])


# =========================
# 翻譯
# =========================
@app.route("/", methods=["POST"])
def translate():
    try:
        data = request.get_json()
        text = data.get("text","")
        target = data.get("target","英文")
        mode = data.get("mode","me")

        codes = {
            "英文":"en","日文":"ja","韓文":"ko","西班牙文":"es",
            "法文":"fr","德文":"de","泰文":"th","越南文":"vi"
        }

        target_code = codes.get(target,"en")

        if mode == "other":
            src = target_code
            tgt = "zh-TW"
        else:
            src = "zh-TW"
            tgt = target_code

        result = GoogleTranslator(source=src, target=tgt).translate(text)

        return jsonify({"translatedText": result})

    except Exception as e:
        print(e)
        return jsonify({"translatedText":"錯誤"}), 500


# =========================
# TTS
# =========================
@app.route("/tts", methods=["POST"])
def tts():
    try:
        data = request.get_json()
        text = data.get("text","")
        lang = data.get("lang","en")

        filename = f"{uuid.uuid4().hex}.mp3"
        path = f"/tmp/{filename}"

        gTTS(text=text, lang=lang).save(path)

        return jsonify({"audio_url": f"/audio/{filename}"})

    except Exception as e:
        print(e)
        return jsonify({"error":"tts fail"}), 500


@app.route("/audio/<f>")
def audio(f):
    return send_from_directory("/tmp", f)


# =========================
# 健康檢查（防 Render 睡眠）
# =========================
@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
