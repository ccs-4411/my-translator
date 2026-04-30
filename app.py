import os
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# 設定 Gemini API
API_KEY = os.environ.get('GEMINI_API_KEY')
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("!!! 警告：環境變數 GEMINI_API_KEY 未設定 !!!")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        target = data.get('target', '中文')
        text = data.get('text', '')
        
        if not text:
            return jsonify({"translatedText": ""})

        # 優先嘗試 2.0，若失敗會被下面 except 捕捉
        model_name = 'gemini-2.0-flash'
        print(f"嘗試使用 {model_name} 翻譯: {text[:10]}...")
        
        model = genai.GenerativeModel(model_name)
        prompt = f"你是一個專業翻譯。請將以下內容翻譯成{target}，只要給我結果，不要有解釋：'{text}'"
        
        response = model.generate_content(prompt)
        
        # 解析回傳結果
        if hasattr(response, 'text'):
            result = response.text.strip()
        elif response.candidates:
            result = response.candidates[0].content.parts[0].text.strip()
        else:
            result = "AI 未生成結果"

        return jsonify({"translatedText": result})

    except Exception as e:
        # --- 關鍵除錯：這段會把真正的錯誤原因印在 Render Logs ---
        print("======== API ERROR LOG START ========")
        traceback.print_exc() 
        error_msg = str(e)
        print("========= API ERROR LOG END =========")
        
        # 如果是 429 或者是模型不存在，建議使用者檢查 Key
        if "429" in error_msg:
            return jsonify({"translatedText": "API 權限限制 (429)。請檢查 API Key 是否有效或更換新 Key。"}), 429
        return jsonify({"translatedText": f"系統錯誤: {error_msg}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
