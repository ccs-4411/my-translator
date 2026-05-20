import os
import json
import io
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 初始化 Gemini API
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    # 使用 gemini-2.5-flash，反應速度最適合行動端應用
    model = genai.GenerativeModel('gemini-2.5-flash')  
    print("Gemini API 初始化成功")
else:
    print("⚠️ 警告: 未在環境變數中設定 GEMINI_API_KEY")
    model = None

def load_languages():
    lang_path = os.path.join(BASE_DIR, "languages.json")
    if os.path.exists(lang_path):
        with open(lang_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

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

@app.route("/sw.js")
def sw():
    return send_from_directory(BASE_DIR, "sw.js")

@app.route("/languages")
def get_langs():
    return jsonify(LANGUAGES)

# 1. 語音翻譯路徑 (文字模式對接)
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
        
        result = GoogleTranslator(source=source, target=target).translate(text)
        return jsonify({"translatedText": result})
    except Exception as e:
        print("語音翻譯錯誤:", e)
        return jsonify({"translatedText": "翻譯失敗"}), 500

# 2. 核心優化：Gemini 智慧掃描翻譯 (一魚兩吃 + 嚴格 JSON 模式)
@app.route("/ocr_translate", methods=["POST"])
def ocr_translate():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "沒有上傳圖片"}), 400
        
        if model is None:
            return jsonify({
                "ocrOriginal": "後端未設定 Gemini API Key",
                "ocrTranslated": "請向管理員確認環境變數設定。"
            }), 500
        
        file = request.files['image']
        image_bytes = file.read()
        
        # 設計高強度的任務指令，直接下達結構化輸出格式
        prompt = """
        你是一個高精準度的視覺文字辨識(OCR)與多國語言翻譯專家。
        請仔細閱讀圖片中的所有文字，並嚴格依照以下 JSON 格式回傳。
        不要包含額外的問候語，也不要包含 Markdown 語法的 ```json 標記。

        回傳格式範例：
        {
          "original": "你在圖片中識別到的完整原始文字內容（請保留其換行結構）",
          "translated": "將上述原始文字，完美翻譯成自然、在地化的台灣繁體中文（zh-TW），注意要符合台灣的科技用語習慣與通順語感"
        }
        """
        
        # 關鍵參數：強迫 Gemini 必須回傳純 JSON 格式（這能防範 LLM 輸出 markdown 廢話導致解析失敗）
        generation_config = {"response_mime_type": "application/json"}
        
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ], generation_config=generation_config)
        
        # 提取回應字串並解析
        response_text = response.text.strip() if response.text else "{}"
        result_data = json.loads(response_text)
        
        return jsonify({
            "ocrOriginal": result_data.get("original", "無法辨識圖片文字"),
            "ocrTranslated": result_data.get("translated", "翻譯失敗，請試著對焦並重新拍攝")
        })
        
    except json.JSONDecodeError as json_err:
        print("Gemini 回傳格式非合法 JSON:", json_err)
        return jsonify({
            "ocrOriginal": "格式解析失敗",
            "ocrTranslated": "AI 回傳了不正確的資料結構，請再試一次。"
        }), 500
    except Exception as e:
        print("OCR 核心引擎錯誤:", e)
        return jsonify({
            "ocrOriginal": f"辨識失敗: {str(i)}",
            "ocrTranslated": "請重新拍攝，並確保圖片文字清晰、沒有強烈反光。"
        }), 500

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    # 對接 Render 或其他雲端平台使用的動態 Port 綁定
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)

