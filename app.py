import os, requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/', methods=['GET', 'POST'])
def unified_handler():
    # 如果是用瀏覽器直接打開 (GET)，顯示網頁
    if request.method == 'GET':
        return send_from_directory(BASE_DIR, 'index.html')
    
    # 如果是程式呼叫 (POST)，執行翻譯
    try:
        data = request.get_json()
        text = data.get('text', '測試')
        # ... 這裡放入你之前的翻譯邏輯 ...
        return jsonify({"translatedText": f"收到數據：{text}"})
    except Exception as e:
        return jsonify({"translatedText": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
