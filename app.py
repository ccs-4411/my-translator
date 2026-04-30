import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# 1. 解決 PythonAnywhere 免費版連線限制 (一定要加)
os.environ['http_proxy'] = "http://proxy.server:3128"
os.environ['https_proxy'] = "http://proxy.server:3128"

# 2. 設定 API Key (從環境變數讀取，或直接貼在這裡也可以)
# 建議確保在 Web 頁面的 WSGI 檔案裡有設定過這個環境變數
api_key = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

@app.route('/')
def index():
    # 確保 index.html 跟 app.py 在同一個目錄
    return send_from_directory('.', 'index.html')

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        target_lang = data.get('target', '日文')
        text = data.get('text', '')

        if not text:
            return jsonify({"error": "沒有輸入文字"}), 400

        prompt = f"將以下中文翻譯成道地的 {target_lang} 口語，只需要給我翻譯後的結果： '{text}'"
        response = model.generate_content(prompt)

        return jsonify({"translatedText": response.text.strip()})
    except Exception as e:
        # 如果出錯，會回傳具體的錯誤訊息給手機
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
