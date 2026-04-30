import os
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator

app = Flask(__name__)
CORS(app)

# 取得 API Key
API_KEY = os.environ.get("GEMINI_API_KEY")

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
        mode = data.get('mode', 'me')

        if not text:
            return jsonify({"translatedText": ""})

        # --- 傳統 Google 模式 ---
        if engine == 'google':
            lang_codes = {"日文": "ja", "英文": "en", "韓文": "ko", "法文": "fr"}
            if mode == 'other':
                t_code = "zh-TW"
            else:
                t_code = lang_codes.get(target_name, "en")
            
            res = GoogleTranslator(source='auto', target=t_code).translate(text)
            return jsonify({"translatedText": res})

        # --- AI Gemini 模式 ---
        if not API_KEY:
            return jsonify({"translatedText": "Error: GEMINI_API_KEY 未設定"}), 500

        genai.configure(api_key=API_KEY)
        # 使用最新的 flash 模型名稱
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        if mode == 'me':
            prompt = f"將這段中文翻譯成{target_name}，只需回傳翻譯文字：'{text}'"
        else:
            prompt = f"將這段{target_name}翻譯成繁體中文，只需回傳翻譯文字：'{text}'"
            
        response = model.generate_content(prompt)
        
        if response and response.text:
            return jsonify({"translatedText": response.text.strip()})
        else:
            return jsonify({"translatedText": "AI 回傳內容為空"}), 404

    except Exception as e:
        # 這裡就是你原本報錯的地方，現在確保縮排正確
        return jsonify({"translatedText": f"發生錯誤: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8888))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8888)))
