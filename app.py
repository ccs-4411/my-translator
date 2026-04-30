import os
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# 獲取 API KEY
API_KEY = os.environ.get('GEMINI_API_KEY')
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("API KEY 未設定，請檢查 Render 環境變數")

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

        # 鎖定 1.5-flash，這是目前免費版在亞太區最穩的模型
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 增加翻譯的精準度指令
        prompt = f"你是一個即時翻譯機。請將以下內容翻譯成{target}，只要給我翻譯結果即可，不要有任何解釋或引號：{text}"
        
        response = model.generate_content(prompt)
        
        # 增加解析防錯機制
        try:
            result = response.text.strip()
        except:
            result = response.candidates[0].content.parts[0].text.strip()

        print(f"[成功] {text} -> {result}")
        return jsonify({"translatedText": result})

    except Exception as e:
        print("======== API 報錯詳細內容 ========")
        traceback.print_exc()
        error_msg = str(e)
        
        # 針對常見的 429 或區域錯誤回報
        if "429" in error_msg:
            return jsonify({"translatedText": "API 目前限制存取 (429)，請稍後再試或檢查 Key 狀態"}), 429
        elif "location" in error_msg.lower():
            return jsonify({"translatedText": "區域不支援，請確認伺服器是否在新加坡"}), 403
            
        return jsonify({"translatedText": f"錯誤: {error_msg}"}), 500

if __name__ == '__main__':
    # 確保 Render 能夠透過 PORT 變數啟動
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
