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

# 只有 OCR 核心部分使用 Google GenAI 套件
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

# 初始化 Gemini 客戶端 (會自動讀取環境變數 GEMINI_API_KEY)
# 請至 Google AI Studio 免費申請 API Key 並設定到環境變數中
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
# 語音/文字對談翻譯 API (使用原本的 Google 翻譯)
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

        # 中文 → 外語
        if mode == "me":
            source = "zh-TW"
            target = target_code
        # 外語 → 中文
        else:
            source = target_code
            target = "zh-TW"

        # 使用原本的 deep-translator 進行字串翻譯
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
# 拍照辨識 API (職責分離：AI 只做 OCR 抓取，Google 負責長文翻譯)
# =========================
@app.route("/ocr_translate", methods=["POST"])
def ocr_translate():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "沒有上傳圖片"}), 400
            
        file = request.files['image']
        image_bytes = file.read()
        
        # 1. 第一步：讓 Gemini 2.5 Flash 專心把圖片內的所有字摳出來（拔除 JSON 以免大段文字噴錯）
        prompt = (
            "這是一張由翻譯 APP 拍攝的照片。請以最高的準確度，"
            "精準辨識並寫出圖片中所有的文字（OCR）。\n"
            "注意事項：\n"
            "1. 不要進行任何翻譯，直接輸出原本的語言文字即可。\n"
            "2. 保持原本的排版與換行。\n"
            "3. 不要添加任何多餘的解釋或 Markdown 標記（如 ``` 等）。"
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

        # 2. 第二步：辨識出來的純文字，直接丟給 Google 翻譯處理長文
        # 設定為自動偵測來源語言 (source="auto")，統一翻譯成台灣習慣的繁體中文
        try:
            translated_text = GoogleTranslator(
                source="auto",
                target="zh-TW"
            ).translate(ocr_text)
        except Exception as trans_err:
            print("OCR 辨識後的 Google 翻譯階段失敗:", trans_err)
            translated_text = "文字辨識成功，但翻譯時發生錯誤。"

        # 3. 乾乾淨淨地回傳給前端渲染
        return jsonify({
            "ocrOriginal": ocr_text,
            "ocrTranslated": translated_text
        })

    except Exception as e:
        print("OCR 核心流程發生錯誤:", e)
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

# =========================
# 啟動伺服器
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port
    )
