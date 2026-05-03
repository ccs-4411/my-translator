import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# --- Server 端 Key 綁定設定 ---
# 1. 建議在 PythonAnywhere 的 Web 頁面設定環境變數
# 2. 或者直接把你的 Key 貼在下方的引號內 (最直接的做法)
SERVER_GEMINI_KEY = os.environ.get('GEMINI_API_KEY') or "你的_GEMINI_API_KEY_貼在這裡"

# 設定 Gemini
genai.configure(api_key=SERVER_GEMINI_KEY)
# 使用 1.5-flash 模型，速度最快且對免費 Key 負擔最小
model = genai.GenerativeModel('gemini-1.5-flash')

# 語言清單 (對應前端)
LANG_MAP = {
    "英文": "English",
    "日文": "Japanese",
    "韓文": "Korean",
    "法文": "French",
    "德文": "German",
    "俄文": "Russian",
    "印尼文": "Indonesian",
    "泰文": "Thai",
    "西班牙文": "Spanish"
}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        text = data.get('text', '').strip()
        target_name = data.get('target', '英文')
        mode = data.get('mode', 'me') # me: 中翻外, other: 外翻中

        if not text:
            return jsonify({"translatedText": ""})

        # 取得目標語言的英文名稱
        target_lang_en = LANG_MAP.get(target_name, target_name)

        # 設定翻譯指令 (Prompt)
        if mode == 'other':
            # 對方講外語 -> 翻成中文
            prompt = f"你是一位專業的隨身口譯。請將這段 {target_lang_en} 翻譯成道地的「繁體中文(台灣語氣)」。只需要給我翻譯後的結果，不要有任何解釋或引號：\n{text}"
        else:
            # 我講中文 -> 翻成外語
            prompt = f"你是一位專業的隨身口譯。請將這段中文翻譯成道地的 {target_lang_en} 口語。只需要給我翻譯後的結果，不要有任何解釋或引號：\n{text}"

        # 執行 Gemini 翻譯
        response = model.generate_content(prompt)
        translated_text = response.text.strip()

        # Log 到伺服器端觀察
        print(f"[{mode}] {text} -> {translated_text}")

        return jsonify({"translatedText": translated_text})

    except Exception as e:
        print(f"翻譯錯誤: {str(e)}")
        # 如果是 PythonAnywhere 免費版連線限制，這裡會報錯
        return jsonify({"translatedText": "伺服器繁忙或 API 連線受限，請稍後再試"}), 500

if __name__ == '__main__':
    app.run(debug=True)
