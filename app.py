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

        text = data.get('text', '').strip()
        target_name = data.get('target', '英文')
        mode = data.get('mode', 'me')

        if not text:
            return jsonify({"translatedText": ""})

        # 語言代碼表 (需與前端 index.html 完全一致)
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

        # 取得選單語系的代碼
        target_lang_code = codes.get(target_name, "en")

        # --- 強化翻譯邏輯 ---
        if mode == 'other':
            # 對方講外語：來源是選單語言，目標是中文
            source_lang = target_lang_code
            target_lang = "zh-TW"
        else:
            # 我講中文：來源是中文，目標是選單語言
            source_lang = "zh-TW"
            target_lang = target_lang_code
        
        # 明確指定 source，不讓 Google 用猜的，準確度大幅提升
        translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        
        print(f"[{mode}] 翻譯: {text} ({source_lang}) -> {translated} ({target_lang})")
        return jsonify({"translatedText": translated})

    except Exception as e:
        print(f"翻譯錯誤報錯: {e}")
        return jsonify({"translatedText": "翻譯連線逾時，請重試"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
