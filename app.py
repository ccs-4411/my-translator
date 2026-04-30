import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# 確保抓到正確的檔案路徑
base_dir = os.path.abspath(os.path.dirname(__file__))

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# 使用 1.5-flash 在 Render 環境最穩定
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def index():
    # 修正：使用絕對路徑指向 index.html
    return send_from_directory(base_dir, 'index.html')

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        text = data.get('text')
        target_lang = data.get('target')
        
        prompt = f"你是一位專業的旅行翻譯官。請將以下內容翻譯成道地的 {target_lang} 口語，只需要回傳翻譯結果，不要有任何解釋。內容： '{text}'"
        
        response = model.generate_content(prompt)
        return jsonify({"translatedText": response.text.strip()})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # 關鍵：Render 必須使用環境變數中的 PORT，且 host 必須是 0.0.0.0
    port = int(os.environ.get('PORT', 8888))
    app.run(host='0.0.0.0', port=port)
