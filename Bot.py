import discord
from discord.ext import commands
import os
import asyncio
import json
import aiohttp
from threading import Thread
from flask import Flask, render_template_string, request, redirect, url_for, session

# 🌐 إعداد خادم الويب
app = Flask('')
app.secret_key = os.getenv("FLASK_SECRET", "LTB_SUPER_SECRET_KEY_9988")

# 🔒 الإعدادات الافتراضية
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
        # قمنا بتحديث الروابط الافتراضية لكي لا تظهر مكسورة أو مكتئبة
        DB_ACCOUNTS = {
            "45": {"id": "45", "title": "حساب ستيم بريميوم - قراند V", "img_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=500", "price": "5 USDT"},
            "10": {"id": "10", "title": "حساب بوبجي ليفيل 70 مشحون", "img_url": "https://images.unsplash.com/photo-1553481187-be93c21490a9?w=500", "price": "12 USDT"}
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
# 🛒 [الموقع 1]: المتجر العام للزبائن (تصميم فخم، حيوي ومشرق بألوان ديسكورد)
# -------------------------------------------------------------------
STORE_FRONT_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>متجر LTB الإعلاني المباشر 🛒</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1a1c1e; color: #f0f2f5; margin: 0; padding: 40px 20px; }
        .header { text-align: center; margin-bottom: 60px; padding: 20px; background: linear-gradient(135deg, #5865F2, #404eed); border-radius: 16px; box-shadow: 0 10px 30px rgba(88,101,242,0.3); max-width: 1160px; margin: 0 auto 50px auto; }
        .header h1 { color: #fff; margin: 0 0 10px 0; font-size: 32px; font-weight: 800; text-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        .header p { color: #e3e5e8; font-size: 18px; margin: 0; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 30px; max-width: 1200px; margin: 0 auto; }
        .card { background: #2b2d31; border-radius: 14px; overflow: hidden; border: 1px solid #3f4248; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 6px 18px rgba(0,0,0,0.25); }
        .card:hover { transform: translateY(-8px); box-shadow: 0 15px 30px rgba(0,0,0,0.5); border-color: #5865F2; }
        .card img { width: 100%; height: 200px; object-fit: cover; background: #1e1f22; border-bottom: 2px solid #232428; }
        .card-body { padding: 25px; display: flex; flex-direction: column; gap: 12px; }
        .card-id { background: #5865F2; color: #fff; padding: 5px 12px; border-radius: 6px; font-size: 12px; font-weight: bold; align-self: flex-start; }
        .card-title { font-size: 18px; color: #fff; font-weight: 700; margin: 5px 0; line-height: 1.5; min-height: 54px; }
        .card-price { color: #23a55a; font-weight: 800; font-size: 18px; display: flex; align-items: center; gap: 6px; border-top: 1px solid #35373c; padding-top: 15px; margin-top: 5px; }
        .btn-order { display: block; text-align: center; background: #5865F2; color: #fff; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 15px; transition: background 0.2s, transform 0.1s; box-shadow: 0 4px 12px rgba(88,101,242,0.3); }
        .btn-order:hover { background: #4752c4; transform: scale(1.02); }
        .btn-order:active { transform: scale(0.98); }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛒 متجر LTB الإعلاني المباشر</h1>
        <p>تصفح الحسابات المتاحة الفخمة، وافتح تذكرة مباشرة للشراء السريع</p>
    </div>
    <div class="grid">
        {% for acc_id, data in accounts.items() %}
        <div class="card">
            <img src="{{ data.img_url }}" alt="Account Image" onerror="this.src='https://images.unsplash.com/photo-1542751371-adc38448a05e?w=500'">
            <div class="card-body">
                <span class="card-id">🆔 الحساب: #{{ acc_id }}</span>
                <div class="card-title">{{ data.title }}</div>
                <div class="card-price">💰 السعر: {{ data.price }}</div>
                <a href="https://discord.gg/j8pmYgnYJd" target="_blank" class="btn-order">📩 توجّه للسيرفر للشراء</a>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

# -------------------------------------------------------------------
# ⚙️ [الموقع 2]: لوحة التحكم الشاملة (تصميم مشرق، احترافي ومرتب)
# -------------------------------------------------------------------
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>LTB Dashboard - لوحة الإدارة ⚙️</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #1e1f22; color: #dbdee1; margin: 0; padding: 40px; }
        .container { max-width: 1140px; margin: 0 auto; }
        .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; border-bottom: 2px solid #2b2d31; padding-bottom: 25px; }
        h2 { color: #fff; margin: 0; font-weight: 800; font-size: 26px; }
        .nav-links { display: flex; align-items: center; gap: 25px; }
        .nav-links a { color: #5865F2; text-decoration: none; font-weight: 700; font-size: 15px; transition: color 0.2s; }
        .nav-links a:hover { color: #fff; }
        .logout-btn { background: #da373c; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: bold; box-shadow: 0 4px 12px rgba(218,55,60,0.2); }
        .logout-btn:hover { background: #a92b2f; }
        .card { background: #2b2d31; border-radius: 12px; padding: 30px; margin-bottom: 35px; border: 1px solid #3f4248; box-shadow: 0 6px 20px rgba(0,0,0,0.2); }
        .card h3 { margin-top: 0; color: #fff; border-bottom: 1px solid #35373c; padding-bottom: 15px; font-size: 18px; font-weight: 700; }
        .form-row { display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }
        .form-group { display: flex; flex-direction: column; flex: 1; min-width: 200px; }
        label { font-size: 14px; color: #949ba4; margin-bottom: 10px; font-weight: 700; }
        input[type="text"] { padding: 14px; background: #1e1f22; border: 1px solid #3f4248; color: #fff; border-radius: 6px; font-size: 14px; transition: border-color 0.2s; }
        input[type="text"]:focus { border-color: #5865F2; outline: none; }
        .btn-add { background: #23a55a; color: white; border: none; padding: 14px 28px; font-weight: bold; border-radius: 6px; cursor: pointer; font-size: 15px; transition: background 0.2s; box-shadow: 0 4px 12px rgba(35,165,90,0.2); margin-top: 10px; }
        .btn-add:hover { background: #1a7a42; }
        .acc-table { width: 100%; border-collapse: collapse; margin-top: 25px; background: #1e1f22; border-radius: 8px; overflow: hidden; border: 1px solid #3f4248; }
        .acc-table th { padding: 16px; text-align: right; color: #949ba4; font-size: 14px; font-weight: 700; border-bottom: 2px solid #2b2d31; background: #232428; }
        .acc-table td { padding: 16px; text-align: right; color: #fff; font-size: 15px; border-bottom: 1px solid #2b2d31; }
        .btn-danger { background: #da373c; color: white; padding: 8px 14px; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: bold; transition: background 0.2s; }
        .btn-danger:hover { background: #a92b2f; }
        .wallet-box { background: #1e1f22; padding: 16px; border-radius: 6px; color: #23a55a; font-family: 'Courier New', monospace; font-size: 15px; margin-top: 8px; border: 1px solid #3f4248; font-weight: bold; letter-spacing: 0.5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h2>⚙️ إدارة المتجر والخزنة السرية</h2>
            <div class="nav-links">
                <a href="/ai_hub_secret_station">🧠 محطة الذكاء الاصطناعي (Site 3)</a>
                <a href="/" target="_blank">🛒 المتجر العام الحالي</a>
                <a href="/logout" class="logout-btn">🚪 تسجيل خروج</a>
            </div>
        </div>

        <div class="card">
            <h3>📦 إضافة وتحديث كروت المنتجات والحسابات</h3>
            <form method="POST" action="/add_account">
                <div class="form-row">
                    <div class="form-group"><label>رقم الحساب (ID):</label><input type="text" name="acc_id" placeholder="مثال: 45" required></div>
                    <div class="form-group"><label>وصف الحساب وعنوانه الحقيقي:</label><input type="text" name="acc_title" placeholder="حساب ستيم، قراند..." required></div>
                    <div class="form-group"><label>السعر المطلوب مع العملة:</label><input type="text" name="acc_price" placeholder="مثال: 10 USDT" required></div>
                    <div class="form-group"><label>رابط الصورة المباشر المعبر:</label><input type="text" name="acc_img" placeholder="https://..." required></div>
                </div>
                <button type="submit" class="btn-add">➕ نشر المنتج فوراً في المتجر</button>
            </form>
            
            <table class="acc-table">
                <thead>
                    <tr><th>رقم الحساب</th><th>الوصف الحالي</th><th>القيمة المالية</th><th>إجراءات التعديل</th></tr>
                </thead>
                <tbody>
                    {% for acc_id, data in accounts.items() %}
                    <tr>
                        <td><code>#{{ acc_id }}</code></td>
                        <td>{{ data.title }}</td>
                        <td><b style="color:#23a55a;">{{ data.price }}</b></td>
                        <td><a href="/delete_account/{{ acc_id }}" class="btn-danger">❌ حذف المنتج</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="card">
            <h3>🪙 قنوات التلقي المالي الفوري</h3>
            <label>عنوان محفظة USDT (BEP20):</label>
            <div class="wallet-box">{{ config.wallet_bep20 }}</div>
            <br>
            <label>عنوان محفظة USDT (TRC20):</label>
            <div class="wallet-box">{{ config.wallet_trc20 }}</div>
        </div>
    </div>
</body>
</html>
"""

# -------------------------------------------------------------------
# 🧠 [الموقع 3]: محطة الذكاء الاصطناعي
# -------------------------------------------------------------------
AI_HUB_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>LTB AI Hub - شات المساعد الذكي</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #1e1f22; color: #dbdee1; margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh; }
        .header { background: #2b2d31; padding: 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1f2023; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .header h2 { color: #fff; margin: 0; font-size: 20px; font-weight: 700; }
        .chat-container { flex: 1; padding: 30px; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; background: #313338; }
        .msg { max-width: 75%; padding: 15px 20px; border-radius: 12px; line-height: 1.6; font-size: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); }
        .user-msg { background: #5865F2; align-self: flex-start; color: #fff; border-bottom-left-radius: 2px; }
        .ai-msg { background: #2b2d31; border: 1px solid #3f4248; align-self: flex-end; color: #dbdee1; border-bottom-right-radius: 2px; }
        .input-area { background: #2b2d31; padding: 20px 30px; border-top: 1px solid #1f2023; }
        form { display: flex; gap: 15px; max-width: 1200px; margin: 0 auto; width: 100%; }
        textarea { flex: 1; background: #383a40; border: 1px solid #1f2023; border-radius: 8px; color: #fff; padding: 15px; height: 44px; font-family: inherit; font-size: 15px; resize: none; }
        textarea:focus { outline: none; border-color: #5865F2; }
        .btn-send { background: #23a55a; color: white; border: none; padding: 0 30px; font-weight: bold; border-radius: 8px; cursor: pointer; font-size: 15px; transition: background 0.2s; }
        .btn-send:hover { background: #1a7a42; }
    </style>
</head>
<body>
    <div class="header">
        <h2>🧠 محطة معالجة البيانات والذكاء الاصطناعي (AI HUB)</h2>
        <div>
            <a href="/admin_panel_ltb_7392_x8q" style="color: #5865F2; text-decoration: none; margin-left: 20px; font-weight:700;">⚙️ العودة للوحة</a>
            <a href="/" style="color: #949ba4; text-decoration: none; font-weight:700;">🛒 واجهة الزوار</a>
        </div>
    </div>
    <div class="chat-container" id="chatContainer">
        <div class="msg ai-msg">أهلاً بك يا رئيس المتجر في محطة المعالجة الشاملة. أنا مجهز بشكل كامل لمساعدتك الآن في إدارة النصوص والحسابات بكفاءة تامة دون انقطاع.</div>
        {% for chat in history %}
            <div class="msg user-msg"><b>أنت:</b><br>{{ chat.user }}</div>
            <div class="msg ai-msg"><b>Gemini:</b><br>{{ chat.ai }}</div>
        {% endfor %}
    </div>
    <div class="input-area">
        <form method="POST" action="/ai_chat_submit">
            <textarea name="prompt" placeholder="اطلب تعديل البيانات، أو اكتب أي استفسار برمجى هنا..." required></textarea>
            <button type="submit" class="btn-send">إرسال واستجابة ⚡</button>
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
    <meta charset="UTF-8"><title>🔒 تسجيل الدخول - الخزنة</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #1e1f22; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #2b2d31; padding: 40px; border-radius: 12px; text-align: center; border: 1px solid #3f4248; width: 340px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); }
        h2 { color: #fff; margin-bottom: 25px; font-size: 22px; font-weight: 700; }
        input { width: 100%; padding: 14px; background: #1e1f22; border: 1px solid #1f2023; color: #fff; margin-bottom: 20px; border-radius: 6px; box-sizing: border-box; transition: border-color 0.2s; }
        input:focus { border-color: #5865F2; outline: none; }
        button { width: 100%; padding: 14px; background: #5865F2; border: none; color: white; font-weight: bold; border-radius: 6px; cursor: pointer; font-size: 16px; transition: background 0.2s; }
        button:hover { background: #4752c4; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔒 تسجيل دخول الإدارة السري</h2>
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="اسم المستخدم" required>
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <button type="submit">دخول فوري</button>
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

# حل مشكلة تشغيل الأسيانك (الخطأ 500) بشكل قطعي وجذري
@app.route('/ai_chat_submit', methods=['POST'])
def ai_chat_submit():
    if 'logged_in' not in session: 
        return redirect(url_for('public_store'))
    prompt = request.form.get('prompt')
    
    # حلقة تشغيل معزولة وآمنة تماماً تمنع قفل أو انهيار خادم الفلاسك
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


# 🤖 محرك اتصال جوجل المحدث بالكامل لمنع الـ 404
async def ask_gemini_ai(prompt_text):
    # استخدام المسار الدقيق والكامل لإصلاح مشكلة الـ 404 التي تظهر في الديسكورد
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    # هيكل بيانات JSON الصارم لتلقي الطلب من خوادم جوجل بشكل سليم
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt_text
            }]
        }]
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
    print("⚡ الكود متصل وشغال 100% بدون أي أخطاء وبألوان حيوية وفخمة!")

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN: 
        bot.run(TOKEN)