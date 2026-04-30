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

# 語言對照表
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

        # --- 引擎 B: Gemini AI 翻譯 (具備自動路徑修復) ---
        else:
            model_names = [
                'models/gemini-1.5-flash-latest',
                'models/gemini-1.5-flash',
                'gemini-1.5-flash-latest',
                'gemini-1.5-flash'
            ]
            
            last_err = ""
            for name in model_names:
                try:
                    model = genai.GenerativeModel(name)
                    prompt = f"你是一位專業翻譯。請將內容翻譯成道地的 {target_lang_name} 口語，只需要翻譯結果：'{text}'"
                    response = model.generate_content(prompt)
                    
                    if hasattr(response, 'text'):
                        return jsonify({"translatedText": response.text.strip()})
                    else:
                        res = response.candidates[0].content.parts[0].text.strip()
                        return jsonify({"translatedText": res})
                except Exception as e:
                    last_err = str(e)
                    continue 
            
            return jsonify({"translatedText": f"AI 暫時失效，請切換穩定模式 (404 Error)"}), 404

    except Exception as e:
        return jsonify({"translatedText": f"伺服器錯誤: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8888))
    app.run(host='0.0.0.0', port=port)
