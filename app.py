import os
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
from deep_translator import GoogleTranslator

app = Flask(__name__)
CORS(app)

# 獲取絕對路徑
base_dir = os.path.abspath(os.path.dirname(__file__))

# 1. Gemini 設定
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# 語言對照表 (針對傳統翻譯引擎)
LANG_MAP = {
    "日文": "ja",
    "英文": "en",
    "韓文": "ko",
    "法文": "fr",
    "中文": "zh-TW"
}

@app.route('/')
def index():
    return send_from_directory(base_dir, 'index.html')

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        text = data.get('text', '')
        target_lang_name = data.get('target', '中文')
        engine = data.get('engine', 'gemini')

        if not text:
            return jsonify({"translatedText": ""})

        # --- 引擎 A: Google 傳統翻譯 ---
        if engine == 'google':
            target_code = LANG_MAP.get(target_lang_name, "en")
            translated = GoogleTranslator(source='auto', target=target_code).translate(text)
            return jsonify({"translatedText": translated})

        # --- 引擎 B: Gemini AI 翻譯 ---
        else:
            # 修正 404 重點：手動加上 models/ 前綴並使用 flash-latest
            model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
            prompt = f"你是一位翻譯。翻譯成{target_lang_name}，只要結果：'{text}'"
            response = model.generate_content(prompt)
            
            if hasattr(response, 'text'):
                result = response.text.strip()
            else:
                result = response.candidates[0].content.parts[0].text.strip()
            
            return jsonify({"translatedText": result})

    except Exception as e:
        error_msg = str(e)
        print(f"Error detail: {error_msg}")
        # 如果 1.5 還是 404，這裡回傳友善提示
        if "404" in error_msg:
            return jsonify({"translatedText": "模型路徑錯誤(404)，請切換穩定模式或檢查 Region"}), 404
        return jsonify({"translatedText": f"錯誤: {error_msg}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8888))
    app.run(host='0.0.0.0', port=port)
