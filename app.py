import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
from deep_translator import GoogleTranslator

app = Flask(__name__)
CORS(app)

# 1. 取得 API Key 並設定
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

LANG_MAP = {"日文": "ja", "英文": "en", "韓文": "ko", "法文": "fr", "中文": "zh-TW"}

@app.route('/')
def index():
    return send_from_directory(os.path.abspath(os.path.dirname(__file__)), 'index.html')

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        text = data.get('text', '')
        target_name = data.get('target', '中文')
        engine = data.get('engine', 'gemini')

        if engine == 'google':
            t_code = LANG_MAP.get(target_name, "en")
            res = GoogleTranslator(source='auto', target=t_code).translate(text)
            return jsonify({"translatedText": res})
        
        # --- AI 模式：強迫嘗試多種路徑 ---
        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-pro']
        last_err = "No API Key configured"
        
        for m in models_to_try:
            try:
                model = genai.GenerativeModel(m)
                # 簡化 Prompt 避免安全過濾
                resp = model.generate_content(f"Translate this to {target_name}: {text}")
                return jsonify({"translatedText": resp.text.strip()})
            except Exception as e:
                last_err = str(e)
                continue
        
        return jsonify({"translatedText": f"AI 撥號失敗: {last_err}"}), 404

    except Exception as e:
        return jsonify({"translatedText": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8888)))
