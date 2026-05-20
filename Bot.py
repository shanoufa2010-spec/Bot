import discord
from discord.ext import commands
import os
import asyncio
import json
import aiohttp
from threading import Thread
from flask import Flask, render_template_string, request, redirect, url_for, session

# 🌐 إعداد خادم الويب والمواضع الثلاثة
app = Flask('')
app.secret_key = os.getenv("FLASK_SECRET", "LTB_SUPER_SECRET_KEY_9988")

# 🔒 الإعدادات الافتراضية المستقرة من صورك
BOT_CONFIG = {
    "web_user": "admin",
    "web_pass": "LTB_Owner_2026",
    "wallet_bep20": "0x280ca19aAAF32F81dfb0245e88bc567222aF718F",
    "wallet_trc20": "TNkNLf2zjjE5EKWYGnb6Tmp2b2DPXmJwU8",
    "log_channel_id": "1506320607032381581",
    "welcome_channel_id": "1505753282755170324",
    "reviews_channel_id": "1505753282755170324"
}

ACCOUNTS_FILE = "accounts.json"
AI_HISTORY_FILE = "ai_history.json"
DB_ACCOUNTS = {}
AI_CHAT_HISTORY = []

def load_data():
    global DB_ACCOUNTS, AI_CHAT_HISTORY
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f: DB_ACCOUNTS = json.load(f)
        except: DB_ACCOUNTS = {}
    if not DB_ACCOUNTS:
        DB_ACCOUNTS = {
            "45": {"id": "45", "title": "حساب ستيم بريميوم - قراند V", "img_url": "https://i.imgur.com/8N69F3R.png", "price": "5 USDT"},
            "10": {"id": "10", "title": "حساب بوبجي ليفيل 70 مشحون", "img_url": "https://i.imgur.com/vXY8B9n.png", "price": "12 USDT"}
        }
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f: json.dump(DB_ACCOUNTS, f, ensure_ascii=False, indent=4)
        
    if os.path.exists(AI_HISTORY_FILE):
        try:
            with open(AI_HISTORY_FILE, "r", encoding="utf-8") as f: AI_CHAT_HISTORY = json.load(f)
        except: AI_CHAT_HISTORY = []

load_data()

AI_CHANNEL_ID = 1505753282361032820
GEMINI_API_KEY = "AIzaSyChRyGo7heDrQUY1HFdiTaiBORt1-XXIOw"

# -------------------------------------------------------------------
# 🛒 [الموقع 1]: المتجر العام للزبائن (تصميم فخم متناسق مع الديسكورد)
# -------------------------------------------------------------------
STORE_FRONT_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>متجر LTB الإعلاني المباشر 🛒</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #36393f; color: #dcddde; margin: 0; padding: 40px 20px; }
        .header { text-align: center; margin-bottom: 50px; }
        .header h1 { color: #fff; margin-bottom: 10px; font-weight: 700; letter-spacing: 0.5px; }
        .header p { color: #b9bbbe; font-size: 16px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 25px; max-width: 1200px; margin: 0 auto; }
        .card { background: #2f3136; border-radius: 8px; overflow: hidden; border: 1px solid #202225; transition: 0.2s ease-in-out; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
        .card:hover { transform: translateY(-4px); box-shadow: 0 8px 20px rgba(0,0,0,0.4); border-color: #5865F2; }
        .card img { width: 100%; height: 190px; object-fit: cover; background: #202225; border-bottom: 1px solid #202225; }
        .card-body { padding: 20px; position: relative; }
        .card-id { background: #5865F2; color: #fff; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
        .card-title { margin: 15px 0 10px 0; font-size: 16px; color: #fff; font-weight: 600; line-height: 1.4; }
        .card-price { color: #3ba55d; font-weight: 700; font-size: 16px; margin-bottom: 18px; display: flex; align-items: center; gap: 5px; }
        .btn-order { display: block; text-align: center; background: #202225; color: #5865F2; border: 1px solid #5865F2; padding: 10px; border-radius: 4px; text-decoration: none; font-weight: 600; font-size: 14px; transition: 0.2s; }
        .btn-order:hover { background: #5865F2; color: #fff; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛒 متجر LTB الإعلاني المباشر</h1>
        <p>تصفح الحسابات المتوفرة حالياً، وافتح تذكرة في السيرفر لطلب الشراء الفوري برقم الحساب</p>
    </div>
    <div class="grid">
        {% for acc_id, data in accounts.items() %}
        <div class="card">
            <img src="{{ data.img_url }}" alt="Account Image">
            <div class="card-body">
                <span class="card-id">🆔 الحساب: #{{ acc_id }}</span>
                <div class="card-title">{{ data.title }}</div>
                <div class="card-price">💰 السعر: {{ data.price }}</div>
                <a href="#" class="btn-order">📩 توجّه للسيرفر للشراء</a>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

# -------------------------------------------------------------------
# ⚙️ [الموقع 2]: لوحة التحكم الشاملة والسحرية (تصميم احترافي داكن)
# -------------------------------------------------------------------
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>LTB Dashboard - لوحة الإدارة ⚙️</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #36393f; color: #dcddde; margin: 0; padding: 40px; }
        .container { max-width: 1100px; margin: 0 auto; }
        .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 1px solid #202225; padding-bottom: 20px; }
        h2 { color: #fff; margin: 0; font-weight: 700; }
        .nav-links { display: flex; align-items: center; gap: 20px; }
        .nav-links a { color: #5865F2; text-decoration: none; font-weight: 600; transition: 0.2s; }
        .nav-links a:hover { color: #fff; }
        .logout-btn { background: #ed4245; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; font-weight: bold; }
        .logout-btn:hover { background: #c0392b; }
        .card { background: #2f3136; border-radius: 8px; padding: 25px; margin-bottom: 30px; border: 1px solid #202225; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .card h3 { margin-top: 0; color: #fff; border-bottom: 1px solid #202225; padding-bottom: 12px; font-size: 16px; font-weight: 600; }
        .form-row { display: flex; gap: 15px; margin-bottom: 20px; }
        .form-group { display: flex; flex-direction: column; flex: 1; }
        label { font-size: 13px; color: #b9bbbe; margin-bottom: 8px; font-weight: 600; }
        input[type="text"] { padding: 12px; background: #202225; border: 1px solid #202225; color: #dcddde; border-radius: 4px; font-size: 14px; transition: 0.2s; }
        input[type="text"]:focus { border-color: #5865F2; outline: none; }
        .btn-add { background: #5865F2; color: white; border: none; padding: 12px 24px; font-weight: bold; border-radius: 4px; cursor: pointer; font-size: 14px; transition: 0.2s; }
        .btn-add:hover { background: #4752c4; }
        .acc-table { width: 100%; border-collapse: collapse; margin-top: 15px; background: #202225; border-radius: 6px; overflow: hidden; }
        .acc-table th { padding: 14px; text-align: right; color: #b9bbbe; font-size: 13px; font-weight: 600; border-bottom: 1px solid #2f3136; background: #2f3136; }
        .acc-table td { padding: 14px; text-align: right; color: #fff; font-size: 14px; border-bottom: 1px solid #2f3136; }
        .btn-danger { background: #ed4245; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-size: 12px; font-weight: bold; transition: 0.2s; }
        .btn-danger:hover { background: #c0392b; }
        .wallet-box { background: #202225; padding: 15px; border-radius: 4px; color: #fff; font-family: monospace; font-size: 14px; margin-top: 10px; border: 1px solid #2f3136; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h2>⚙️ إدارة مخزن الحسابات والخيارات السرية</h2>
            <div class="nav-links">
                <a href="/ai_hub_secret_station">🧠 محطة الذكاء الاصطناعي (Site 3)</a>
                <a href="/" target="_blank">🛒 المتجر العام</a>
                <a href="/logout" class="logout-btn">🚪 تسجيل خروج</a>
            </div>
        </div>

        <div class="card">
            <h3>📦 إضافة وتعديل كروت الحسابات في المتجر العام</h3>
            <form method="POST" action="/add_account">
                <div class="form-row">
                    <div class="form-group"><label>رقم الحساب (ID):</label><input type="text" name="acc_id" placeholder="مثال: 45" required></div>
                    <div class="form-group"><label>وصف الحساب وعنوانه:</label><input type="text" name="acc_title" placeholder="حساب ستيم، ليفيل..." required></div>
                    <div class="form-group"><label>السعر المعروض:</label><input type="text" name="acc_price" placeholder="مثال: 10 USDT" required></div>
                    <div class="form-group"><label>رابط الصورة المباشر:</label><input type="text" name="acc_img" placeholder="https://..." required></div>
                </div>
                <button type="submit" class="btn-add">➕ إضافة الحساب فوراً في الكتالوج</button>
            </form>
            
            <table class="acc-table">
                <thead>
                    <tr><th>رقم الحساب</th><th>الوصف</th><th>السعر</th><th>التحكم بالحساب</th></tr>
                </thead>
                <tbody>
                    {% for acc_id, data in accounts.items() %}
                    <tr>
                        <td><code>#{{ acc_id }}</code></td>
                        <td>{{ data.title }}</td>
                        <td><b style="color:#3ba55d;">{{ data.price }}</b></td>
                        <td><a href="/delete_account/{{ acc_id }}" class="btn-danger">❌ حذف الحساب نهائياً</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="card">
            <h3>🪙 عناوين محافظ الدفع الثابتة</h3>
            <label>محفظة USDT (BEP20):</label>
            <div class="wallet-box">{{ config.wallet_bep20 }}</div>
            <br>
            <label>محفظة USDT (TRC20):</label>
            <div class="wallet-box">{{ config.wallet_trc20 }}</div>
        </div>
    </div>
</body>
</html>
"""

# -------------------------------------------------------------------
# 🧠 [الموقع 3]: بوابة الشات المنفصلة (AI HUB)
# -------------------------------------------------------------------
AI_HUB_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>LTB AI Hub - شات المساعد الذكي</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #36393f; color: #dcddde; margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh; }
        .header { background: #2f3136; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #202225; }
        .header h2 { color: #fff; margin: 0; font-size: 18px; }
        .chat-container { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }
        .msg { max-width: 80%; padding: 14px 18px; border-radius: 8px; line-height: 1.5; font-size: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .user-msg { background: #5865F2; align-self: flex-start; color: #fff; }
        .ai-msg { background: #2f3136; border: 1px solid #202225; align-self: flex-end; color: #dcddde; }
        .input-area { background: #2f3136; padding: 20px; border-top: 1px solid #202225; }
        form { display: flex; gap: 12px; max-width: 1200px; margin: 0 auto; width: 100%; }
        textarea { flex: 1; background: #40444b; border: 1px solid #202225; border-radius: 6px; color: #fff; padding: 12px; height: 40px; font-family: inherit; resize: none; }
        textarea:focus { outline: none; border-color: #5865F2; }
        .btn-send { background: #3ba55d; color: white; border: none; padding: 12px 28px; font-weight: bold; border-radius: 4px; cursor: pointer; transition: 0.2s; }
        .btn-send:hover { background: #2e854b; }
    </style>
</head>
<body>
    <div class="header">
        <h2>🧠 محطة الذكاء الاصطناعي المنفصلة الثالثة (AI HUB)</h2>
        <div>
            <a href="/admin_panel_ltb_7392_x8q" style="color: #5865F2; text-decoration: none; margin-left: 15px; font-weight:600;">⚙️ لوحة الإدارة</a>
            <a href="/" style="color: #b9bbbe; text-decoration: none; font-weight:600;">🛒 المتجر العام</a>
        </div>
    </div>
    <div class="chat-container" id="chatContainer">
        <div class="msg ai-msg">مرحباً بك يا سيدي في الموقع الثالث. أنا هنا مجهز بالكامل لقراءة طلباتك وتعديل ملف المتجر. اكتب لي أي شيء أو اطلب معالجة الحسابات الكبيرة.</div>
        {% for chat in history %}
            <div class="msg user-msg"><b>أنت:</b><br>{{ chat.user }}</div>
            <div class="msg ai-msg"><b>Gemini:</b><br>{{ chat.ai }}</div>
        {% endfor %}
    </div>
    <div class="input-area">
        <form method="POST" action="/ai_chat_submit">
            <textarea name="prompt" placeholder="اكتب استفسارك أو بياناتك هنا للتحاور مع الذكاء الاصطناعي..." required></textarea>
            <button type="submit" class="btn-send">إرسال للموقع الثالث ⚡</button>
        </form>
    </div>
    <script>
        var objDiv = document.getElementById("chatContainer");
        objDiv.scrollTop = objDiv.scrollHeight;
    </script>
</body>
</html>
"""

# 🔒 صفحة تسجيل الدخول الآمنة
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>🔒 تسجيل الدخول - LTB الإدارة</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #2f3136; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #36393f; padding: 35px; border-radius: 8px; text-align: center; border: 1px solid #202225; width: 330px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        h2 { color: #fff; margin-bottom: 25px; font-size: 20px; font-weight: 700; }
        input { width: 100%; padding: 12px; background: #202225; border: 1px solid #202225; color: #dcddde; margin-bottom: 18px; border-radius: 4px; box-sizing: border-box; transition: 0.2s; }
        input:focus { border-color: #5865F2; outline: none; }
        button { width: 100%; padding: 12px; background: #5865F2; border: none; color: white; font-weight: bold; border-radius: 4px; cursor: pointer; font-size: 15px; transition: 0.2s; }
        button:hover { background: #4752c4; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔒 تسجيل دخول الإدارة</h2>
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="اسم المستخدم السري" required>
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <button type="submit">دخول آمن</button>
        </form>
    </div>
</body>
</html>
"""

# --- مسارات الويب والتوجيهات المستقرة ---
@app.route('/')
def public_store(): 
    return render_template_string(STORE_FRONT_HTML, accounts=DB_ACCOUNTS)

@app.route('/admin_panel_ltb_7392_x8q')
def admin_panel():
    if 'logged_in' in session: 
        return render_template_string(DASHBOARD_HTML, accounts=DB_ACCOUNTS, config=BOT_CONFIG)
    return render_template_string(LOGIN_HTML)

@app.route('/ai_hub_secret_station')
def ai_hub_station():
    if 'logged_in' not in session: 
        return render_template_string(LOGIN_HTML)
    return render_template_string(AI_HUB_HTML, history=AI_CHAT_HISTORY)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('username') == BOT_CONFIG['web_user'] and request.form.get('password') == BOT_CONFIG['web_pass']:
        session['logged_in'] = True
        return redirect(url_for('admin_panel'))
    return render_template_string(LOGIN_HTML)

# حل مشكلة تشغيل الأسيانك (الخطأ 500)
@app.route('/ai_chat_submit', methods=['POST'])
def ai_chat_submit():
    if 'logged_in' not in session: 
        return redirect(url_for('public_store'))
    prompt = request.form.get('prompt')
    
    # حلقة تشغيل معزولة وآمنة لمنع انهيار موقع Flask
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ai_response = loop.run_until_complete(ask_gemini_ai(prompt))
    loop.close()

    AI_CHAT_HISTORY.append({"user": prompt, "ai": ai_response})
    with open(AI_HISTORY_FILE, "w", encoding="utf-8") as f: 
        json.dump(AI_CHAT_HISTORY, f, ensure_ascii=False, indent=4)
        
    return redirect(url_for('ai_hub_station'))

@app.route('/add_account', methods=['POST'])
def add_account():
    if 'logged_in' not in session: return redirect(url_for('public_store'))
    aid = request.form.get('acc_id').strip()
    DB_ACCOUNTS[aid] = {
        "id": aid, 
        "title": request.form.get('acc_title'), 
        "price": request.form.get('acc_price'), 
        "img_url": request.form.get('acc_img')
    }
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f: json.dump(DB_ACCOUNTS, f, ensure_ascii=False, indent=4)
    return redirect(url_for('admin_panel'))

@app.route('/delete_account/<aid>')
def delete_account(aid):
    if 'logged_in' not in session: return redirect(url_for('public_store'))
    if aid in DB_ACCOUNTS: 
        del DB_ACCOUNTS[aid]
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f: json.dump(DB_ACCOUNTS, f, ensure_ascii=False, indent=4)
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout(): 
    session.pop('logged_in', None)
    return redirect(url_for('public_store'))

def run_http_server(): 
    app.run(host='0.0.0.0', port=8080, threaded=True)


# 🤖 محرك اتصال جوجل المحدث والمصلح تماماً (إصلاح خطأ الـ 404)
async def ask_gemini_ai(prompt_text):
    # استخدام المسار الرسمي والمباشر لموديل gemini-1.5-flash لحل مشكلة الروابط القديمة الموقوفة
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=15) as response:
                if response.status == 200:
                    res_json = await response.json()
                    return res_json['candidates'][0]['content']['parts'][0]['text']
                else:
                    return f"❌ خطأ في الاتصال بخادم جوجل الذكي: {response.status}"
    except Exception as e:
        return f"⚠️ لم يتمكن البوت من الاتصال بخادم جوجل: {str(e)}"


# --- إعدادات وتكامل بوت الديسكورد ---
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.id == AI_CHANNEL_ID:
        async with message.channel.typing():
            user_content = message.content
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.filename.endswith('.txt'):
                        file_bytes = await attachment.read()
                        user_content += f"\n\n[الملف المرفق]:\n{file_bytes.decode('utf-8')}"
            
            ai_response = await ask_gemini_ai(user_content)
            
            if len(ai_response) > 2000:
                for chunk in [ai_response[i:i+1900] for i in range(0, len(ai_response), 1900)]:
                    await message.channel.send(chunk)
            else:
                await message.channel.send(ai_response)
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print("⚡ الكود الكامل متصل وجاهز للعمل بالتصميم الجديد الفخم والروابط المستقرة!")

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN: 
        bot.run(TOKEN)