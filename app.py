import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from deep_translator import GoogleTranslator

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return send_from_directory(BASE_DIR, 'index.html')
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"translatedText": "無數據"}), 400

        text = data.get('text', '')
        target_name = data.get('target', '英文')
        mode = data.get('mode', 'me')

        if not text:
            return jsonify({"translatedText": ""})

        # 這裡的名稱必須與前端選單顯示的文字完全一致
        codes = {
            "英文": "en",
            "日文": "ja",
            "韓文": "ko",
            "越南文": "vi",
            "西班牙文": "es",
            "泰文": "th",
            "法文": "fr",
            "德文": "de",
            "印尼文": "id",
            "俄文": "ru",
            "義大利文": "it",
            "菲律賓文": "tl"
        }

        # 如果是對方講話，翻譯目標固定為繁體中文
        if mode == 'other':
            t_code = "zh-TW"
        else:
            # 如果在字典找不到，才預設為英文
            t_code = codes.get(target_name, "en")
        
        translated = GoogleTranslator(source='auto', target=t_code).translate(text)
        return jsonify({"translatedText": translated})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"translatedText": "翻譯伺服器暫時無回應"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
