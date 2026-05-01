import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator

app = Flask(__name__)
CORS(app)

# 從環境變數讀取 API Key
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
            t_code = "zh-TW" if mode == 'other' else lang_codes.get(target_name, "en")
            res = GoogleTranslator(source='auto', target=t_code).translate(text)
            return jsonify({"translatedText": res})

        # --- AI Gemini 模式 (改用 API 直接請求) ---
        if not API_KEY:
            return jsonify({"translatedText": "錯誤：Render 未偵測到 API Key"}), 500

        # 設定提示詞
        if mode == 'me':
            prompt = f"將這段中文翻譯成{target_name}，只需回傳翻譯後的內容：'{text}'"
        else:
            prompt = f"將這段{target_name}翻譯成繁體中文，只需回傳翻譯後的內容：'{text}'"

        # 呼叫 Google Gemini API (2026 最新端點)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        response = requests.post(url, headers=headers, json=payload, timeout=10)
        res_data = response.json()

        # 檢查回傳結果
        if response.status_code == 200:
            translated_text = res_data['candidates'][0]['content']['parts'][0]['text']
            return jsonify({"translatedText": translated_text.strip()})
        else:
            # 這裡會直接把 Google 的錯誤原因傳回前端
            error_reason = res_data.get('error', {}).get('message', '未知 API 錯誤')
            return jsonify({"translatedText": f"Google API 報錯 ({response.status_code}): {error_reason}"}), response.status_code

    except Exception as e:
        return jsonify({"translatedText": f"連線發生錯誤: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
