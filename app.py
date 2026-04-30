import os
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator

app = Flask(__name__)
CORS(app)

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

        if engine == 'google':
            t_code = "zh-TW" if mode == 'other' else {"英文":"en","日文":"ja","韓文":"ko","法文":"fr"}.get(target_name, "en")
            res = GoogleTranslator(source='auto', target=t_code).translate(text)
            return jsonify({"translatedText": res})

        # --- AI 模式：帶有模型排錯機制 ---
        if not API_KEY:
            return jsonify({"translatedText": "Error: Render 環境變數未設定"}), 500

        genai.configure(api_key=API_KEY)
        
        # 嘗試模型列表（由新到舊）
        model_names = ['models/gemini-1.5-flash', 'gemini-1.5-flash', 'gemini-pro']
        
        success = False
        last_exception = ""
        
        for m_name in model_names:
            try:
                model = genai.GenerativeModel(m_name)
                prompt = f"Translate to {target_name}: '{text}'" if mode == 'me' else f"Translate to Traditional Chinese: '{text}'"
                resp = model.generate_content(prompt)
                return jsonify({"translatedText": resp.text.strip()})
            except Exception as e:
                last_exception = str(e)
                continue
        
        # 如果走到這裡，代表所有模型都失敗，回傳伺服器目前的清單供除錯
        available_models = [m.name for m in genai.list_models()]
        return jsonify({
            "translatedText": f"模型找不到。報錯: {last_exception}。伺服器目前可用模型: {available_models}"
        }), 404

    except Exception as e:
        return jsonify({"translatedText": f"系統錯誤: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8888)))

    except Exception as e:
        return jsonify({"translatedText": f"錯誤: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8888)))
