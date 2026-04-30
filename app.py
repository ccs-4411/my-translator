import os
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
from deep_translator import GoogleTranslator

app = Flask(__name__)
CORS(app)

base_dir = os.path.abspath(os.path.dirname(__file__))

# 1. Gemini 設定
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# 語言代碼對照表
LANG_MAP = {
    "日文": "ja", "英文": "en", "韓文": "ko", "法文": "fr", "中文": "zh-TW"
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

        # --- 傳統 Google 翻譯模式 ---
        if engine == 'google':
            target_code = LANG_MAP.get(target_lang_name, "en")
            translated = GoogleTranslator(source='auto', target=target_code).translate(text)
            return jsonify({"translatedText": translated})

        # --- AI Gemini 翻譯模式 ---
        else:
            # 嘗試多種模型路徑以避開 404
            model_candidates = [
                'models/gemini-1.5-flash-latest',
                'models/gemini-1.5-flash',
                'gemini-1.5-flash-latest',
                'gemini-1.5-flash'
            ]
            
            last_err = ""
            for model_name in model_candidates:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(f"翻譯成{target_lang_name}，只要翻譯結果：'{text}'")
                    if response and response.text:
                        return jsonify({"translatedText": response.text.strip()})
                except Exception as e:
                    last_err = str(e)
                    continue
            
            return jsonify({"translatedText": f"AI 暫時失效 (原因: {last_err})"}), 404

    except Exception as e:
        return jsonify({"translatedText": f"系統錯誤: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8888))
    app.run(host='0.0.0.0', port=port)
