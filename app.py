import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# 設定 Gemini API (支援 2.0/2.5 Key)
API_KEY = os.environ.get('GEMINI_API_KEY')
if API_KEY:
    genai.configure(api_key=API_KEY)
    # 使用 2.0-flash 是目前最穩定的選擇
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    print("錯誤：找不到 GEMINI_API_KEY 環境變數")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        target = data.get('target', '中文')
        text = data.get('text', '')
        
        if not text or len(text.strip()) < 1:
            return jsonify({"translatedText": ""})

        # 嚴格指令，避免 AI 廢話過多
        prompt = f"你是一個專業翻譯。請將以下內容翻譯成{target}，只要給我翻譯後的結果，不要有任何多餘解釋：'{text}'"
        
        response = model.generate_content(prompt)
        
        # 解析 Response
        if hasattr(response, 'text'):
            result = response.text.strip()
        elif response.candidates:
            result = response.candidates[0].content.parts[0].text.strip()
        else:
            result = "翻譯未生成"

        print(f"成功: {text} -> {result}")
        return jsonify({"translatedText": result})

    except Exception as e:
        error_msg = str(e)
        # 如果發生 429 錯誤，回傳友善提示
        if "429" in error_msg:
            return jsonify({"translatedText": "系統忙碌中 (429)，請稍等 10 秒再試"}), 429
        print(f"錯誤: {error_msg}")
        return jsonify({"translatedText": f"錯誤: {error_msg}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
