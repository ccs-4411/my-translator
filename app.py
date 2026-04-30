import os
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator

app = Flask(__name__)
CORS(app)

# 設定 API Key
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
        target_name = data.get('target', '英文')
        engine = data.get('engine', 'gemini')
        mode = data.get('mode', 'me') # me 代表我講中文，other 代表對方講外語

        if not text: return jsonify({"translatedText": ""})

        # --- 傳統模式 ---
        if engine == 'google':
            t_code = "zh-TW" if mode == 'other' else LANG_MAP.get(target_name, "en")
            res = GoogleTranslator(source='auto', target=t_code).translate(text)
            return jsonify({"translatedText": res})
        
        # --- AI 模式 ---
        if not API_KEY: return jsonify({"translatedText": "API Key 未設定"}), 500
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        if mode == 'me':
            prompt = f"請將這段中文翻譯成道地的{target_name}，只需要翻譯結果：'{text}'"
        else:
            prompt = f"請將這段{target_name}翻譯成流暢的繁體中文，只需要翻譯結果：'{text}'"
            
        resp = model.generate_content(prompt)
        return jsonify({"translatedText": resp.text.strip()})

    except Exception as e:
        return jsonify({"translatedText": f"錯誤: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8888)))
