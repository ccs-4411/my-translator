import os, requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# 取得環境變數
API_KEY = os.environ.get("GEMINI_API_KEY")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/', methods=['GET', 'POST'])
def unified_handler():
    # --- GET: 回傳網頁介面 ---
    if request.method == 'GET':
        return send_from_directory(BASE_DIR, 'index.html')
    
    # --- POST: 執行翻譯邏輯 ---
    try:
        data = request.get_json()
        if not data:
            return jsonify({"translatedText": "無有效的請求數據"}), 400

        text = data.get('text', '')
        target_name = data.get('target', '英文')
        engine = data.get('engine', 'gemini')
        mode = data.get('mode', 'me')

        if not text:
            return jsonify({"translatedText": ""})

        # 1. 傳統模式 (Google Translator)
        if engine == 'google':
            codes = {"日文": "ja", "英文": "en", "韓文": "ko", "法文": "fr"}
            t_code = "zh-TW" if mode == 'other' else codes.get(target_name, "en")
            res = GoogleTranslator(source='auto', target=t_code).translate(text)
            return jsonify({"translatedText": res})

        # 2. AI 模式 (Gemini API)
        if not API_KEY:
            return jsonify({"translatedText": "錯誤：未設定 API Key"}), 500

        # 設定 AI 提示詞
        if mode == 'me':
            prompt = f"將這段中文翻譯成{target_name}，只需回傳翻譯後的內容：'{text}'"
        else:
            prompt = f"將這段{target_name}翻譯成繁體中文，只需回傳翻譯後的內容：'{text}'"

        # 呼叫 Gemini 1.5 Flash
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        response = requests.post(url, json=payload, timeout=12)
        res_data = response.json()

        if response.status_code == 200:
            # 解析 Google API 回傳的結構
            try:
                translated_text = res_data['candidates'][0]['content']['parts'][0]['text']
                return jsonify({"translatedText": translated_text.strip()})
            except:
                return jsonify({"translatedText": "解析 AI 回傳格式失敗"}), 500
        else:
            # 顯示 Google 的具體報錯訊息
            err_msg = res_data.get('error', {}).get('message', '未知 API 錯誤')
            return jsonify({"translatedText": f"AI 報錯 ({response.status_code}): {err_msg}"}), response.status_code

    except Exception as e:
        return jsonify({"translatedText": f"伺服器異常: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
