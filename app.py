# app.py
import os
import json
from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory
)
from flask_cors import CORS
from deep_translator import GoogleTranslator

# 引入 Google 官方 GenAI 套件
from google import genai
from google.genai import types

app = Flask(
    __name__,
    static_folder='static'
)

CORS(app)

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# 初始化 Gemini 客戶端 (自動讀取系統環境變數 GEMINI_API_KEY)
# 請至 Google AI Studio 免費申請 API Key
client = genai.Client()

# =========================
# 載入語言清單
# =========================
def load_languages():
    lang_path = os.path.join(
        BASE_DIR,
        "languages.json"
    )
    if os.path.exists(lang_path):
        with open(
            lang_path,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)
    return []

LANGUAGES = load_languages()

# =========================
# 取得語言代碼
# =========================
def get_lang_code(name):
    for lang in LANGUAGES:
        if lang["name"] == name:
            return lang["code"]
    return "en"

# =========================
# 靜態檔案路徑路由
# =========================
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

# =========================
# 語音/文字對談翻譯 API (維持 Google 翻譯)
# =========================
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

        result = GoogleTranslator(
            source=source,
            target=target
        ).translate(text)

        return jsonify({
            "translatedText": result
        })

    except Exception as e:
        print("語音/文字翻譯錯誤:", e)
        return jsonify({
            "translatedText": "翻譯失敗"
        }), 500

# =========================
# 拍照辨識 API (強效防呆職責分離版)
# =========================
@app.route("/ocr_translate", methods=["POST"])
def ocr_translate():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "沒有上傳圖片"}), 400
            
        file = request.files['image']
        image_bytes = file.read()
        
        # 1. 第一步：強硬的 OCR 提示詞，逼 AI 一字不漏地把英/日/中文摳出來
        prompt = (
            "你是一個專業的網頁與文件 OCR 辨識系統。請仔細掃描這張圖片，"
            "將圖片中看到的『所有文字』一字不漏地擷取出來。\n"
            "嚴格遵守以下規則：\n"
            "1. 必須完整保留圖片中的所有英文單字、數字、標點符號與原本的段落換行。\n"
            "2. 即使是網頁代碼、排版按鈕或角落小字，只要是人類看得懂的字就必須抓出來。\n"
            "3. 絕對不要進行任何翻譯、解釋、潤飾或歸納，只需要原汁原味輸出辨識出的原本文字。\n"
            "4. 不要添加額外的說明（例如不需寫 Here is the text:），也不要用 ``` 等 Markdown 語法包裹輸出。"
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=file.content_type
                ),
                prompt,
            ]
        )

        ocr_text = response.text.strip() if response.text else ""
        
        if not ocr_text:
            return jsonify({
                "ocrOriginal": "無法辨識圖片中的文字",
                "ocrTranslated": "請重新拍攝清楚的圖片"
            })

        # 2. 第二步：交給最擅長長文本的 Google 翻譯轉成繁體中文
        try:
            translated_text = GoogleTranslator(
                source="auto",
                target="zh-TW"
            ).translate(ocr_text)
        except Exception as trans_err:
            print("OCR 翻譯階段失敗:", trans_err)
            translated_text = "文字辨識成功，但翻譯時發生錯誤。"

        return jsonify({
            "ocrOriginal": ocr_text,
            "ocrTranslated": translated_text
        })

    except Exception as e:
        print("OCR 核心流程錯誤:", e)
        return jsonify({
            "ocrOriginal": "辨識失敗",
            "ocrTranslated": "後端視覺辨識暫時無法回應"
        }), 500

# =========================
# Health Check
# =========================
@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port
    )
