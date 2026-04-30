import os
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai

# 強制獲取絕對路徑，解決 Render 找不到 index.html 的問題
base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)

# 1. 設定 API KEY
API_KEY = os.environ.get('GEMINI_API_KEY')
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("錯誤：找不到 GEMINI_API_KEY")

# 2. 路由：首頁
@app.route('/')
def index():
    return send_from_directory(base_dir, 'index.html')

# 3. 翻譯邏輯 (加入穩定版 v1 修正)
@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        target = data.get('target', '中文')
        text = data.get('text', '')

        if not text:
            return jsonify({"translatedText": ""})

        # 關鍵修正：確保使用 gemini-1.5-flash，這是目前在雲端環境最穩的模型
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"你是一個專業翻譯。請將以下內容翻譯成{target}，只要翻譯後的結果：'{text}'"
        
        # 呼叫 API
        response = model.generate_content(prompt)
        
        # 檢查並解析回傳
        if hasattr(response, 'text'):
            result = response.text.strip()
        else:
            result = response.candidates[0].content.parts[0].text.strip()

        return jsonify({"translatedText": result})

    except Exception as e:
        error_msg = str(e)
        print("======== API 報錯詳情 ========")
        traceback.print_exc()
        
        # 如果發生 404，給予明確提示
        if "404" in error_msg:
            return jsonify({"translatedText": "模型路徑錯誤 (404)。請確認 Render 的 Region 設為 Singapore 且使用 1.5 模型。"}), 404
        return jsonify({"translatedText": f"錯誤: {error_msg}"}), 500

if __name__ == '__main__':
    # 重要：Render 必須使用 0.0.0.0
    port = int(os.environ.get('PORT', 8888))
    app.run(host='0.0.0.0', port=port)
