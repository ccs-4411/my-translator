import os, requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator

app = Flask(__name__)
CORS(app)

# 打印啟動訊息到 Render Log，方便我們確認
print("--- 翻譯程式正在啟動 ---")

@app.route('/translate', methods=['POST', 'GET']) # 允許 GET 測試
def translate_api():
    if request.method == 'GET':
        return jsonify({"msg": "路由正常活著，請改用 POST 發送數據"}), 200

    try:
        data = request.get_json()
        if not data:
            return jsonify({"translatedText": "無數據"}), 400
            
        text = data.get('text', '')
        target = data.get('target', '英文')
        mode = data.get('mode', 'me')
        
        # 簡易 Google 翻譯邏輯 (測試路由用)
        codes = {"日文": "ja", "英文": "en", "韓文": "ko", "法文": "fr"}
        t_code = "zh-TW" if mode == 'other' else codes.get(target, "en")
        res = GoogleTranslator(source='auto', target=t_code).translate(text)
        
        return jsonify({"translatedText": res})
    except Exception as e:
        return jsonify({"translatedText": str(e)}), 500

@app.route('/')
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
