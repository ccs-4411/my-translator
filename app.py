import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator
from google import genai

app = Flask(__name__)
CORS(app)

# 初始化最新版 Google GenAI Client
def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

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

        # --- 傳統模式 ---
        if engine == 'google':
            lang_codes = {"日文": "ja", "英文": "en", "韓文": "ko", "法文": "fr"}
            t_code = "zh-TW" if mode == 'other' else lang_codes.get(target_name, "en")
            res = GoogleTranslator(source='auto', target=t_code).translate(text)
            return jsonify({"translatedText": res})

        # --- AI 最新 2.0/3.0 模式 ---
        client = get_client()
        if not client:
            return jsonify({"translatedText": "錯誤：API Key 未設定"}), 500

        # 最新模型名稱：gemini-2.0-flash 或 gemini-1.5-flash
        model_id = "gemini-1.5-flash"
        
        if mode == 'me':
            prompt = f"請將這段中文翻譯成{target_name}，只需回傳結果：'{text}'"
        else:
            prompt = f"請將這段{target_name}翻譯成繁體中文，只需回傳結果：'{text}'"

        # 最新版 API 呼叫方式
        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )

        if response and response.text:
            return jsonify({"translatedText": response.text.strip()})
        else:
            return jsonify({"translatedText": "AI 回傳內容為空"}), 404

    except Exception as e:
        return jsonify({"translatedText": f"最新 API 報錯: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8888))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8888)))
