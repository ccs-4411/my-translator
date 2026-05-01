import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator

# 初始化 Flask，強制指定目前的目錄為靜態檔案目錄
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# 取得環境變數中的 API Key
API_KEY = os.environ.get("GEMINI_API_KEY")
# 取得目前檔案所在的絕對路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    """回傳首頁 index.html"""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/translate', methods=['POST'])
@app.route('/translate/', methods=['POST'])  # 雙路由防止 404 錯誤
def translate():
    try:
        data = request.json
        if not data:
            return jsonify({"translatedText": "錯誤：無效的請求內容"}), 400

        text = data.get('text', '')
        target_name = data.get('target', '英文')
        engine = data.get('engine', 'gemini')
        mode = data.get('mode', 'me')

        if not text:
            return jsonify({"translatedText": ""})

        # --- 傳統 Google 翻譯模式 ---
        if engine == 'google':
            lang_codes = {"日文": "ja", "英文": "en", "韓文": "ko", "法文": "fr"}
            t_code = "zh-TW" if mode == 'other' else lang_codes.get(target_name, "en")
            res = GoogleTranslator(source='auto', target=t_code).translate(text)
            return jsonify({"translatedText": res})

        # --- AI Gemini 模式 (使用純 Requests 呼叫 API) ---
        if not API_KEY:
            return jsonify({"translatedText": "錯誤：Render 環境變數 GEMINI_API_KEY 未設定"}), 500

        # 根據模式設定提示詞 (Prompt)
        if mode == 'me':
            prompt = f"請將這段中文翻譯成{target_name}，只需回傳翻譯結果，不要有任何多餘的解釋：'{text}'"
        else:
            prompt = f"請將這段{target_name}翻譯成繁體中文，只需回傳翻譯結果，不要有任何多餘的解釋：'{text}'"

        # Google Gemini API 2026 最新端點
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        # 發送 API 請求
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        res_data = response.json()

        if response.status_code == 200:
            try:
                # 解析 API 回傳的 JSON 結構
                translated_text = res_data['candidates'][0]['content']['parts'][0]['text']
                return jsonify({"translatedText": translated_text.strip()})
            except (KeyError, IndexEror):
                return jsonify({"translatedText": "解析 API 回傳格式時出錯"}), 500
        else:
            # 顯示 Google API 回傳的具體錯誤訊息 (如 403 區域限制或 400 Key 錯誤)
            msg = res_data.get('error', {}).get('message', '未知錯誤')
            return jsonify({"translatedText": f"Google API 報錯 ({response.status_code}): {msg}"}), response.status_code

    except Exception as e:
        return jsonify({"translatedText": f"伺服器發生異常: {str(e)}"}), 500

# 除錯用路由：如果你的 /translate 還是 404，請瀏覽 網址/check_files
@app.route('/check_files')
def check_files():
    files = os.listdir(BASE_DIR)
    return jsonify({
        "current_dir": BASE_DIR,
        "files_found": files,
        "api_key_set": bool(API_KEY)
    })

if __name__ == '__main__':
    # Render 會自動設定 PORT 環境變數
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
