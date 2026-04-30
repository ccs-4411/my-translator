import os
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai

# 強制抓取目前程式碼所在的資料夾路徑
base_dir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)

# 設定 API
API_KEY = os.environ.get('GEMINI_API_KEY')
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("錯誤：找不到 API KEY")

# 修正 404：確保路徑絕對正確
@app.route('/')
def index():
    # 使用 path.join 確保在 Linux (Render) 上路徑正確
    return send_from_directory(base_dir, 'index.html')

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        target = data.get('target', '中文')
        text = data.get('text', '')
        
        if not text: return jsonify({"translatedText": ""})

        # 使用最穩定的 1.5 模型
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"翻譯成{target}，只要結果：{text}"
        response = model.generate_content(prompt)
        
        if hasattr(response, 'text'):
            result = response.text.strip()
        else:
            result = response.candidates[0].content.parts[0].text.strip()

        return jsonify({"translatedText": result})

    except Exception as e:
        print("======== 報錯內容 ========")
        traceback.print_exc()
        return jsonify({"translatedText": f"錯誤: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
