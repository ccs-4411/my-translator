import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# 優先讀取環境變數
API_KEY = os.environ.get('GEMINI_API_KEY')
if API_KEY:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    print("警告：找不到 GEMINI_API_KEY 環境變數！")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/translate', methods=['POST'])
def translate():
    try:
        if not API_KEY:
            return jsonify({"translatedText": "錯誤：伺服器未設定 API Key"}), 500
            
        data = request.json
        target = data.get('target', '中文')
        text = data.get('text', '')
        
        if not text:
            return jsonify({"translatedText": "（無語音內容）"})

        prompt = f"你是一個翻譯官。請將以下文字翻譯成{target}，只需要給我翻譯後的口語結果，不要有任何解釋： '{text}'"
        
        # 呼叫 Gemini
        response = model.generate_content(prompt)
        
        # 檢查 response 結構是否正確
        if hasattr(response, 'text') and response.text:
            result = response.text.strip()
            print(f"翻譯成功: {text} -> {result}") # 這會印在 Render 日誌
            return jsonify({"translatedText": result})
        else:
            return jsonify({"translatedText": "AI 沒有回傳結果，請再試一次"})

    except Exception as e:
        error_msg = str(e)
        print(f"發生錯誤: {error_msg}")
        return jsonify({"translatedText": f"錯誤：{error_msg}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
