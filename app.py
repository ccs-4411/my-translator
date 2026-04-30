import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# 設定 Gemini API
API_KEY = os.environ.get('GEMINI_API_KEY')
if API_KEY:
    genai.configure(api_key=API_KEY)
    # 這裡選用 2.0-flash，相容性最高
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    print("錯誤：找不到環境變數 GEMINI_API_KEY")

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

        prompt = f"你是一個專業的隨身翻譯官。請將以下文字翻譯成道地的 {target} 口語，只需要給我翻譯後的結果，不要有任何解釋： '{text}'"
        
        # 呼叫 Gemini
        response = model.generate_content(prompt)
        
        # 強化解析機制：相容不同版本的回傳格式
        try:
            if hasattr(response, 'text'):
                result = response.text.strip()
            elif response.candidates:
                result = response.candidates[0].content.parts[0].text.strip()
            else:
                result = "AI 未能生成內容，請再試一次"
        except Exception as parse_error:
            print(f"解析錯誤: {parse_error}")
            result = "解析翻譯結果時出錯"

        print(f"成功翻譯: {text} -> {result}")
        return jsonify({"translatedText": result})

    except Exception as e:
        error_msg = str(e)
        print(f"發生錯誤: {error_msg}")
        return jsonify({"translatedText": f"錯誤訊息：{error_msg}"}), 500

if __name__ == '__main__':
    # Render 環境必須綁定 PORT 變數
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    app.run(host='0.0.0.0', port=port)
