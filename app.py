import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# 獲取目前目錄
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/', methods=['GET', 'POST'])
def home():
    # GET: 顯示網頁
    if request.method == 'GET':
        return send_from_directory(BASE_DIR, 'index.html')
    
    # POST: 執行翻譯
    try:
        data = request.get_json()
        if not data:
            return jsonify({"translatedText": "無數據"}), 400

        text = data.get('text', '')
        target_name = data.get('target', '英文')
        mode = data.get('mode', 'me')

        if not text:
            return jsonify({"translatedText": ""})

        # 設定語言代碼 (新增 越南、西班牙、泰文)
        codes = {
            "日文": "ja", 
            "英文": "en", 
            "韓文": "ko", 
            "法文": "fr",
            "越南文": "vi",
            "西班牙文": "es",
            "泰文": "th"
        }

        # 如果是「我講中文」(mode='me')，目標是外語
        # 如果是「對方講外語」(mode='other')，目標是繁體中文
        t_code = "zh-TW" if mode == 'other' else codes.get(target_name, "en")
        
        # 執行 Google 翻譯
        translated = GoogleTranslator(source='auto', target=t_code).translate(text)
        
        return jsonify({"translatedText": translated})

    except Exception as e:
        return jsonify({"translatedText": f"翻譯出錯: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
