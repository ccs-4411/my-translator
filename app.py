import os
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
# 使用 deep-translator 作為傳統 Google 翻譯的穩定方案
from deep_translator import GoogleTranslator

app = Flask(__name__)
CORS(app)

# 獲取絕對路徑
base_dir = os.path.abspath(os.path.dirname(__file__))

# 1. Gemini 設定
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
# 使用你在 Render 測試成功的最新穩定版模型名稱
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# 語言對照表 (針對傳統翻譯引擎)
LANG_MAP = {
    "日文": "ja",
    "英文": "en",
    "韓文": "ko",
    "法文": "fr",
    "中文": "zh-TW"
}

@app.route('/')
def index():
    return send_from_directory(base_dir, 'index.html')

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        text = data.get('text', '')
        target_lang_name = data.get('target', '中文')
        engine = data.get('engine', 'gemini')

        if not text:
            return jsonify({"translatedText": ""})

        # --- 引擎 A: Google 傳統翻譯 ---
        if engine == 'google':
            target_code = LANG_MAP.get(target_lang_name, "en")
            translated = GoogleTranslator(source='auto', target=target_code).translate(text)
            return jsonify({"translatedText": translated})

        # --- 引擎 B: Gemini AI 翻譯 ---
        else:
            prompt = f"你是一位專業翻譯官。請將內容翻譯成道地的 {target_lang_name} 口語，只要結果，不要解釋：'{text}'"
            response = model.generate_content(prompt)
            
            if hasattr(response, 'text'):
                result = response.text.strip()
            else:
                result = response.candidates[0].content.parts[0].text.strip()
            
            return jsonify({"translatedText": result})

    except Exception as e:
        print("======== 翻譯出錯 ========")
        traceback.print_exc()
        return jsonify({"translatedText": f"錯誤: {str(e)}"}), 500

if __name__ == '__main__':
    # Render 環境必須使用 0.0.0.0
    port = int(os.environ.get('PORT', 8888))
    app.run(host='0.0.0.0', port=port)
    app.run(host='0.0.0.0', port=port)
