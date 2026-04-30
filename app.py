import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# Render 會自動偵測 Port，所以不需要手動設定
api_key = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        target = data.get('target', '中文')
        text = data.get('text', '')
        prompt = f"將以下文字翻譯成道地的 {target} 口語，只需要給我翻譯後的結果： '{text}'"
        response = model.generate_content(prompt)
        return jsonify({"translatedText": response.text.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Render 部署需要的設定
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))