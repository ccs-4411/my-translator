import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("請先在 .env 檔案中設定 GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)

app = Flask(__name__, template_folder='.')

LANGUAGES = [
    {"name": "日文", "label": "🇯🇵", "voice": "ja-JP"},
    {"name": "韓文", "label": "🇰🇷", "voice": "ko-KR"},
    {"name": "英文", "label": "🇺🇸", "voice": "en-US"},
    {"name": "法文", "label": "🇫🇷", "voice": "fr-FR"},
    {"name": "德文", "label": "🇩🇪", "voice": "de-DE"},
    {"name": "西班牙文", "label": "🇪🇸", "voice": "es-ES"}
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/languages', methods=['GET'])
def get_languages():
    return jsonify(LANGUAGES)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        text = data.get('text', '')
        target = data.get('target', '英文')
        mode = data.get('mode', 'me') 

        if not text:
            return jsonify({"translatedText": ""})

        model = genai.GenerativeModel('gemini-1.5-flash')

        if mode == 'me':
            prompt = f"你是一個專業的隨身口譯官。請將以下中文口語翻譯成流暢在地、符合語境的{target}。請直接輸出翻譯結果，不要附帶任何解釋或標點符號之外的贅字：\n\n{text}"
        else:
            prompt = f"你是一個專業的隨身口譯官。請將以下{target}口語翻譯成台灣人常用的流暢繁體中文。請直接輸出翻譯結果，不要附帶任何解釋：\n\n{text}"

        response = model.generate_content(prompt)
        return jsonify({"translatedText": response.text.strip()})
    except Exception as e:
        print(f"💡 語音翻譯錯誤: {e}")
        return jsonify({"error": str(e)}), 500

# 2. 📸 萬能全場景 OCR 翻譯路由（不再受限於菜單）
@app.route('/ocr_translate', methods=['POST'])
def ocr_translate():
    print("\n📥 [後端收到請求] 萬能 OCR 翻譯觸發！")
    try:
        if 'image' not in request.files:
            return jsonify({"ocrOriginal": "", "ocrTranslated": "未接收到圖片"}), 400

        image_file = request.files['image']
        menu_lang = request.form.get('menu_lang', '日文')  # 這裡的變數名稱雖然叫 menu_lang，但僅作為辨識目標語系
        image_bytes = image_file.read()

        if not image_bytes:
            return jsonify({"ocrOriginal": "", "ocrTranslated": "圖片資料為空"}), 400

        model = genai.GenerativeModel('gemini-1.5-flash')

        image_parts = [
            {
                "mime_type": "image/jpeg",
                "data": image_bytes
            }
        ]

        # 🌟 重新設計的核心 Prompt：解鎖全場景辨識（菜單、藥妝、路牌、警語、說明書通通吃）
        prompt = f"""
        你是一個精通多國語言與各國在地生活文化的「全能隨身旅遊翻譯官」。
        請仔細辨識這張圖片中出現的所有 {menu_lang} 文字，不論它是菜單、藥妝包裝、路標、地鐵告示、商品說明、警語還是收據，並完成以下任務：
        
        1. 找出圖片中所有可辨識的該語系文字，將原本的 {menu_lang} 完整整理出來（此欄位命名為「原文整理」）。如果有多行或多個品項，請換行並用數字列表。
        2. 將這些文字翻譯成台灣人習慣、看得懂的「流暢繁體中文」（此欄位命名為「在地化翻譯」）。
        3. 翻譯原則：
           - 【如果是餐點/菜單】：請務必符合台灣餐飲習慣（例如：「海老」翻鮮蝦/大蝦、「唐揚げ」翻日式炸雞、「삼겹살」翻豬五五花）。
           - 【如果是藥妝/商品】：請翻出功效、用途或商品名稱（例如：化妝水、保濕乳液、感冒藥、止痛劑），若有成分或特殊警語請簡短翻譯。
           - 【如果是路牌/告示】：請翻出精確的指示或警語含意（例如：禁止通行、請勿觸摸、出口、乘車處）。
        4. 如果有特殊專有名詞、成分或看不懂的語詞，請在括號內用一句話簡短補充說明它是什麼。

        請嚴格依照以下格式輸出，不要包含任何 markdown 語法（不要加三個反引號）：

        【原文整理】
        (這裡列出辨識到的 {menu_lang} 原文)

        【在地化翻譯】
        (這裡列出對應的繁體中文流暢翻譯與補充說明)
        """

        response = model.generate_content([prompt, image_parts[0]])
        result_text = response.text.strip()
        
        print("🚀 Gemini 成功回傳萬能辨識結果！")

        ocr_original = "未能清晰辨識原文"
        ocr_translated = result_text

        if "【原文整理】" in result_text and "【在地化翻譯】" in result_text:
            parts = result_text.split("【在地化翻譯】")
            ocr_original = parts[0].replace("【原文整理】", "").strip()
            ocr_translated = parts[1].strip()

        return jsonify({
            "ocrOriginal": ocr_original,
            "ocrTranslated": ocr_translated
        })

    except Exception as e:
        print(f"💥 後端 OCR 核心功能出錯: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


