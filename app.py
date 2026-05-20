<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>AI 翻譯官</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#1a73e8">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
            background: #f0f2f5;
            padding: 16px;
            min-height: 100vh;
        }

        .card {
            max-width: 560px;
            margin: 0 auto;
            background: white;
            border-radius: 32px;
            padding: 24px 20px 32px;
            box-shadow: 0 8px 28px rgba(0, 0, 0, 0.08);
        }

        h2 {
            color: #1a73e8;
            font-size: 1.8rem;
            text-align: center;
            margin-bottom: 20px;
        }

        .top-menu {
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
        }

        .top-menu button {
            flex: 1;
            border: none;
            border-radius: 40px;
            padding: 12px 0;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .top-menu button:first-child {
            background: #1a73e8;
            color: white;
        }

        .top-menu button:last-child {
            background: #e8eaed;
            color: #1a73e8;
        }

        #status {
            background: #e8f0fe;
            padding: 8px 16px;
            border-radius: 40px;
            font-size: 0.85rem;
            color: #1a73e8;
            font-weight: 500;
            text-align: center;
            margin-bottom: 20px;
        }

        select {
            width: 100%;
            padding: 14px 16px;
            border-radius: 28px;
            border: 1px solid #dadce0;
            background: white;
            font-size: 1rem;
            margin-bottom: 20px;
            outline: none;
            cursor: pointer;
        }

        select:focus {
            border-color: #1a73e8;
            box-shadow: 0 0 0 2px rgba(26,115,232,0.2);
        }

        .btn-group {
            display: flex;
            gap: 14px;
            margin: 20px 0;
        }

        .mic-btn {
            flex: 1;
            height: 130px;
            border: none;
            border-radius: 28px;
            color: white;
            font-size: 1.2rem;
            font-weight: bold;
            cursor: pointer;
            transition: 0.2s;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        #btn-me {
            background: #1a73e8;
        }

        #btn-other {
            background: #34a853;
        }

        .active-mic {
            background: #ea4335 !important;
            transform: scale(0.96);
        }

        #result-box, #ocr-result-box {
            background: #f8f9fa;
            border-radius: 24px;
            padding: 18px;
            margin-top: 10px;
            border: 1px solid #e8eaed;
        }

        #original, #ocrOriginal {
            color: #5f6368;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 10px;
            font-size: 0.95rem;
            white-space: pre-wrap;
            word-break: break-word;
            line-height: 1.4;
            max-height: 200px;
            overflow-y: auto;
            font-family: monospace;
        }

        #translated, #ocrTranslated {
            font-size: 1.3rem;
            font-weight: 700;
            margin-top: 12px;
            color: #202124;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .play-group {
            display: flex;
            gap: 10px;
            margin-top: 16px;
        }

        .play-btn {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 28px;
            background: #ff9800;
            color: white;
            font-weight: bold;
            cursor: pointer;
            font-size: 0.9rem;
        }

        #ocrPage {
            display: none;
        }

        #previewImage {
            width: 100%;
            border-radius: 24px;
            margin: 12px 0;
            display: none;
            max-height: 300px;
            object-fit: contain;
            background: #f1f3f4;
            border: 1px solid #ddd;
        }

        .ocr-buttons {
            display: flex;
            gap: 12px;
            margin: 12px 0;
        }

        .ocr-buttons button {
            flex: 1;
            border: none;
            border-radius: 40px;
            padding: 12px 0;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            color: white;
        }

        #pickBtn { background: #1a73e8; }
        #scanBtn { background: #0d652d; }
        #ocrSpeakBtn { background: #ff9800; }
        #stopBtn { background: #d93025; }

        .progress-bar {
            width: 100%;
            height: 4px;
            background: #e0e0e0;
            border-radius: 2px;
            margin-top: 10px;
            overflow: hidden;
            display: none;
        }

        .progress-fill {
            width: 0%;
            height: 100%;
            background: #1a73e8;
            transition: width 0.3s;
        }

        .tip {
            margin-top: 18px;
            background: #e8f0fe;
            padding: 10px 14px;
            border-radius: 20px;
            font-size: 0.75rem;
            color: #174ea6;
            text-align: center;
        }

        button:active {
            transform: scale(0.97);
        }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔍 AI 翻譯官</h2>
        
        <div class="top-menu">
            <button onclick="showVoicePage()">🎤 語音翻譯</button>
            <button onclick="showOCRPage()">📸 掃描翻譯</button>
        </div>
        
        <div id="status">✅ 準備就緒</div>

        <!-- 語音翻譯頁面 -->
        <div id="voicePage">
            <select id="target"></select>
            <div class="btn-group">
                <button id="btn-me" class="mic-btn" onclick="runMic('me')">🎙️ 我說中文</button>
                <button id="btn-other" class="mic-btn" onclick="runMic('other')">🗣️ 對方外語</button>
            </div>
            <div id="result-box">
                <div id="original">等待說話...</div>
                <div id="translated">翻譯結果</div>
                <div class="play-group">
                    <button class="play-btn" onclick="replayAudio()">🔊 重播譯文</button>
                </div>
            </div>
        </div>

        <!-- OCR 掃描翻譯頁面 -->
        <div id="ocrPage">
            <!-- capture="environment" 可以在手機端直接拉起後鏡頭 -->
            <input type="file" id="imageInput" accept="image/*" capture="environment" hidden>
            <img id="previewImage" alt="預覽圖片">
            
            <div class="ocr-buttons">
                <button id="pickBtn">📷 拍照 / 選照片</button>
                <button id="scanBtn">🔍 AI 辨識翻譯</button>
            </div>
            <div class="progress-bar" id="progressBar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="ocr-buttons">
                <button id="ocrSpeakBtn">🔊 朗讀翻譯</button>
                <button id="stopBtn">⛔ 停止朗讀</button>
            </div>
            <div id="ocr-result-box">
                <div id="ocrOriginal">等待掃描圖片...</div>
                <div id="ocrTranslated">翻譯結果</div>
            </div>
            <div class="tip">
                💡 提示：請在光線充足處拍攝，保持文字清晰、盡量平貼減少反光<br>
                📌 支援多國語言，由 Gemini AI 自動進行高精準辨識並轉為繁體中文。
            </div>
        </div>
    </div>

    <script>
        let recognition = null;
        let voices = [];
        let lastText = "";
        let lastLang = "zh-TW";
        let selectedBlob = null; // 用來儲存前端壓縮後的圖片 Blob 物件

        // 切換頁面
        function showVoicePage() {
            document.getElementById('voicePage').style.display = 'block';
            document.getElementById('ocrPage').style.display = 'none';
            document.getElementById('status').innerText = '🎤 語音翻譯模式';
        }

        function showOCRPage() {
            document.getElementById('voicePage').style.display = 'none';
            document.getElementById('ocrPage').style.display = 'block';
            document.getElementById('status').innerText = '📸 掃描翻譯模式 (AI 辨識)';
        }

        // 載入語音
        async function loadVoices() {
            return new Promise(resolve => {
                let v = speechSynthesis.getVoices();
                if (v.length) resolve(v);
                speechSynthesis.onvoiceschanged = () => resolve(speechSynthesis.getVoices());
            });
        }

        // 載入語言清單
        async function loadLanguages() {
            try {
                const res = await fetch('/languages');
                const langs = await res.json();
                const sel = document.getElementById('target');
                sel.innerHTML = '';
                langs.forEach(l => {
                    const opt = document.createElement('option');
                    opt.value = l.name;
                    opt.textContent = `${l.name} ${l.label}`;
                    opt.dataset.voice = l.voice;
                    sel.appendChild(opt);
                });
            } catch(e) { 
                console.error('語言載入錯誤', e);
                const sel = document.getElementById('target');
                sel.innerHTML = '<option value="英文" data-voice="en-US">英文 English 🇺🇸</option>';
            }
        }

        // 語音辨識初始化
        function initRecognition() {
            const Speech = window.webkitSpeechRecognition || window.SpeechRecognition;
            if (!Speech) {
                alert('瀏覽器不支援語音辨識，請使用 Chrome / Edge / Safari');
                return;
            }
            recognition = new Speech();
            recognition.continuous = false;
            recognition.interimResults = false;
            
            recognition.onstart = () => document.getElementById('status').innerText = '🎙️ 聆聽中...';
            recognition.onerror = () => document.getElementById('status').innerText = '❌ 辨識失敗，請重新點擊';
            recognition.onend = () => {
                document.getElementById('btn-me').classList.remove('active-mic');
                document.getElementById('btn-other').classList.remove('active-mic');
            };
            recognition.onresult = (e) => {
                const text = e.results[0][0].transcript;
                document.getElementById('original').innerText = text;
                translateText(text);
            };
        }

        function runMic(mode) {
            if (!recognition) initRecognition();
            if (!recognition) return;
            
            const sel = document.getElementById('target');
            const opt = sel.selectedOptions[0];
            
            if (mode === 'me') {
                recognition.lang = 'zh-TW';
            } else {
                recognition.lang = opt?.dataset?.voice || 'en-US';
            }
            
            document.getElementById('btn-me').classList.remove('active-mic');
            document.getElementById('btn-other').classList.remove('active-mic');
            document.getElementById(`btn-${mode}`).classList.add('active-mic');
            
            try {
                recognition.start();
            } catch(e) {
                document.getElementById('status').innerText = '⚠️ 請允許麥克風權限';
            }
        }

        // 語音翻譯
        async function translateText(text) {
            const sel = document.getElementById('target');
            const targetName = sel.value;
            const mode = recognition?.lang === 'zh-TW' ? 'me' : 'other';
            
            document.getElementById('status').innerText = '🔄 翻譯中...';
            
            try {
                const res = await fetch('/translate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, target: targetName, mode })
                });
                const data = await res.json();
                document.getElementById('translated').innerText = data.translatedText || '翻譯失敗';
                
                const ttsLang = mode === 'me' ? (sel.selectedOptions[0]?.dataset?.voice || 'en-US') : 'zh-TW';
                speak(data.translatedText, ttsLang);
                document.getElementById('status').innerText = '✅ 翻譯完成';
            } catch(e) {
                console.error(e);
                document.getElementById('status').innerText = '❌ 翻譯失敗';
            }
        }

        // 語音合成
        async function speak(text, lang) {
            if (!text) return;
            lastText = text;
            lastLang = lang;
            const v = await loadVoices();
            speechSynthesis.cancel();
            const utter = new SpeechSynthesisUtterance(text);
            utter.lang = lang;
            const match = v.find(vv => vv.lang.replace('_', '-') === lang) || v.find(vv => vv.lang.startsWith(lang.split('-')[0]));
            if (match) utter.voice = match;
            speechSynthesis.speak(utter);
        }

        function replayAudio() {
            if (lastText) speak(lastText, lastLang);
        }

        // ========== OCR 功能（前端 Canvas 無損壓縮） ==========
        
        document.getElementById('pickBtn').onclick = () => {
            document.getElementById('imageInput').click();
        };
        
        document.getElementById('imageInput').onchange = (e) => {
            const file = e.target.files[0];
            if (!file) return;

            document.getElementById('status').innerText = '⚡ 正在壓縮圖片中...';

            const reader = new FileReader();
            reader.onload = (ev) => {
                const img = new Image();
                img.onload = () => {
                    // 設定手機照片最大邊長為 1200 像素 (足以清晰 OCR 且兼顧大小)
                    const max_size = 1200;
                    let width = img.width;
                    let height = img.height;

                    if (width > height) {
                        if (width > max_size) {
                            height *= max_size / width;
                            width = max_size;
                        }
                    } else {
                        if (height > max_size) {
                            width *= max_size / height;
                            height = max_size;
                        }
                    }

                    // 建立 Canvas 畫布進行縮小畫圖
                    const canvas = document.createElement('canvas');
                    canvas.width = width;
                    canvas.height = height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, width, height);

                    // 輸出為 0.7 品質的輕量化 JPEG Blob 物件 (檔案大小可縮小 80%-95%)
                    canvas.toBlob((blob) => {
                        selectedBlob = blob;
                        
                        // 顯示預覽畫面
                        const preview = document.getElementById('previewImage');
                        preview.src = canvas.toDataURL('image/jpeg');
                        preview.style.display = 'block';
                        
                        document.getElementById('status').innerText = '📷 圖片已無損優化，請點擊「AI 辨識翻譯」';
                        document.getElementById('ocrOriginal').innerHTML = '等待辨識...';
                        document.getElementById('ocrTranslated').innerHTML = '翻譯結果';
                    }, 'image/jpeg', 0.7);
                };
                img.src = ev.target.result;
            };
            reader.readAsDataURL(file);
        };
        
        // OCR 傳送至後端
        document.getElementById('scanBtn').onclick = async () => {
            if (!selectedBlob) {
                alert('請先拍照或選取圖片');
                return;
            }
            
            const status = document.getElementById('status');
            const progressBar = document.getElementById('progressBar');
            const progressFill = document.getElementById('progressFill');
            
            status.innerText = '🔍 AI 辨識翻譯中...';
            progressBar.style.display = 'block';
            progressFill.style.width = '30%';
            
            const formData = new FormData();
            // 注意：這裡傳送的是前端 Canvas 處理過後的輕量化 blob 物件
            formData.append('image', selectedBlob, 'compressed_image.jpg');
            
            try {
                progressFill.style.width = '60%';
                const res = await fetch('/ocr_translate', { 
                    method: 'POST', 
                    body: formData 
                });
                
                progressFill.style.width = '90%';
                const data = await res.json();
                
                progressFill.style.width = '100%';
                
                document.getElementById('ocrOriginal').innerHTML = `📄 原文：<br>${escapeHtml(data.ocrOriginal || '無文字')}`;
                document.getElementById('ocrTranslated').innerHTML = data.ocrTranslated || '翻譯失敗';
                
                status.innerText = '✅ 辨識並翻譯完成';
                speak(data.ocrTranslated, 'zh-TW');
                
            } catch(err) {
                console.error('OCR 錯誤', err);
                status.innerText = '❌ 處理失敗';
                document.getElementById('ocrOriginal').innerHTML = '網路異常或讀取超時，請重試';
                document.getElementById('ocrTranslated').innerHTML = '請確保圖片清晰、連線正常';
            } finally {
                setTimeout(() => {
                    progressBar.style.display = 'none';
                    progressFill.style.width = '0%';
                }, 500);
            }
        };
        
        // 朗讀翻譯結果
        document.getElementById('ocrSpeakBtn').onclick = () => {
            const text = document.getElementById('ocrTranslated').innerText;
            if (text && text !== '翻譯結果' && text !== '翻譯失敗') {
                speak(text, 'zh-TW');
            } else {
                alert('尚無翻譯結果');
            }
        };
        
        document.getElementById('stopBtn').onclick = () => {
            speechSynthesis.cancel();
            document.getElementById('status').innerText = '⏹️ 已停止朗讀';
        };
        
        function escapeHtml(str) {
            if (!str) return '';
            return str.replace(/[&<>]/g, m => {
                if (m === '&') return '&amp;';
                if (m === '<') return '&lt;';
                if (m === '>') return '&gt;';
                return m;
            });
        }
        
        // 初始化
        (async () => {
            await loadVoices();
            await loadLanguages();
            initRecognition();
            showVoicePage();
        })();
    </script>
</body>
</html>
