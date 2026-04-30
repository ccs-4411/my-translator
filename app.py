import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# 設定 Gemini API
api_key = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def index():
    # 確保 Render 能正確讀取 index.html
    return send_from_directory('.', 'index.html')

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        target = data.get('target', '中文')
        text = data.get('text', '')
        # 強調口語翻譯
        prompt = f"你是一個專業的隨身翻譯官。請將以下文字翻譯成道地的 {target} 口語，只需要給我翻譯後的結果，不要有任何解釋： '{text}'"
        response = model.generate_content(prompt)
        return jsonify({"translatedText": response.text.strip()})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Render 專用 Port 設定
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
