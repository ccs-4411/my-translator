import os
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai

# 強制定位根目錄
base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)

# 1. 檢查並設定 API KEY
API_KEY = os.environ.get('GEMINI_API_KEY')
if API_KEY:
    genai.configure(api_key=API_KEY)
    print("--- 成功讀取 API KEY ---")
    # 在日誌印出可用模型，這能幫我們確認 404 原因
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"您的 Key 支援的模型: {m.name}")
    except:
        print("無法列出模型清單，可能是 Key 已失效")
else:
    print("!!! 錯誤：環境變數 GEMINI_API_KEY 是空的 !!!")

@app.route('/')
def index():
    # 確保 index.html 存在於根目錄
    return send_from_directory(base_dir, 'index.html')

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        target = data.get('target', '中文')
        text = data.get('text', '')
        
        if not text:
            return jsonify({"translatedText": ""})

        # 2. 嘗試最穩定的路徑 (不要加 models/ 前綴，讓 SDK 自己處理)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"翻譯成{target}：{text}"
        response = model.generate_content(prompt)
        
        # 3. 解析結果
        if hasattr(response, 'text'):
            result = response.text.strip()
        else:
            # 備用解析路徑
            result = response.candidates[0].content.parts[0].text.strip()

        return jsonify({"translatedText": result})

    except Exception as e:
        print("======== 翻譯發生錯誤 ========")
        traceback.print_exc()
        error_msg = str(e)
        
        # 如果是 404，通常是模型名稱不對
        if "404" in error_msg:
            return jsonify({"translatedText": "模型路徑錯誤 (404)，請檢查 API Key 權限"}), 404
        return jsonify({"translatedText": f"錯誤: {error_msg}"}), 500

if __name__ == '__main__':
    # Render 會給 PORT，沒給就用 10000
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
