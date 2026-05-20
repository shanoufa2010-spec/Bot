import discord
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
import os
import asyncio
import json
import aiohttp
from threading import Thread
from flask import Flask, render_template_string, request, redirect, url_for, session

# 🌐 إعداد خادم الويب والمواقع الثلاثة
app = Flask('')
app.secret_key = os.getenv("FLASK_SECRET", "LTB_SUPER_SECRET_KEY_9988")

# 🔒 قاعدة بيانات الإعدادات الشاملة (المستقرة من صورك)
BOT_CONFIG = {
    "web_user": "admin",
    "web_pass": "LTB_Owner_2026",
    "wallet_bep20": "0x280ca19aAAF32F81dfb0245e88bc567222aF718F",
    "wallet_trc20": "TNkNLf2zjjE5EKWYGnb6Tmp2b2DPXmJwU8",
    "log_channel_id": "1506320607032381581",
    "welcome_channel_id": "1505753282755170324",
    "reviews_channel_id": "1505753282755170324",
    "perm_setup_cmd": "Mega Owner, Sellers Leader, Admin",
    "perm_clear_cmd": "Mega Owner, Admin",
    "perm_approve_action": "Mega Owner, Sellers Leader",
    "perm_close_ticket": "Mega Owner, Sellers Leader, Staff"
}

# 💾 نظام حفظ الحسابات المستمر (منع الحذف)
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
        save_data(ACCOUNTS_FILE, DB_ACCOUNTS)
        
    if os.path.exists(AI_HISTORY_FILE):
        try:
            with open(AI_HISTORY_FILE, "r", encoding="utf-8") as f: AI_CHAT_HISTORY = json.load(f)
        except: AI_CHAT_HISTORY = []

def save_data(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

load_data()
AI_CHANNEL_ID = 1505753282361032820
GEMINI_API_KEY = "AIzaSyChRyGo7heDrQUY1HFdiTaiBORt1-XXIOw"

# -------------------------------------------------------------------
# 🛒 [الموقع 1]: تصميم واجهة المتجر العامة للزبائن (/)
# -------------------------------------------------------------------
STORE_FRONT_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>متجر LTB الإعلاني المباشر 🛒</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f0c1b; color: #fff; margin: 0; padding: 40px 20px; }
        .header { text-align: center; margin-bottom: 50px; }
        .header h1 { color: #5865F2; margin-bottom: 10px; }
        .header p { color: #a2a0b6; font-size: 16px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 30px; max-width: 1200px; margin: 0 auto; }
        .card { background: #17122b; border-radius: 12px; border: 1px solid #2c254a; overflow: hidden; box-shadow: 0 8px 20px rgba(0,0,0,0.4); transition: 0.3s; }
        .card:hover { transform: translateY(-5px); border-color: #5865F2; }
        .card img { width: 100%; height: 180px; object-fit: cover; background: #0f0c1b; }
        .card-body { padding: 20px; }
        .card-id { background: #5865F2; color: #fff; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .card-title { margin: 15px 0 10px 0; font-size: 18px; color: #fff; }
        .card-price { color: #43b581; font-weight: bold; font-size: 16px; margin-bottom: 15px; }
        .btn-order { display: block; text-align: center; background: #231b3e; color: #5865F2; border: 1px solid #5865F2; padding: 10px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 14px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛒 متجر LTB الإعلاني المباشر</h1>
        <p>تصفح الحسابات المتوفرة لدينا حالياً، وافتح تذكرة في السيرفر لطلب الشراء الفوري برقم الحساب</p>
    </div>
    <div class="grid">
        {% for acc_id, data in accounts.items() %}
        <div class="card">
            <img src="{{ data.img_url }}" alt="Account Image">
            <div class="card-body">
                <span class="card-id">رقم الحساب: #{{ acc_id }}</span>
                <div class="card-title">{{ data.title }}</div>
                <div class="card-price">السعر: {{ data.price }}</div>
                <div class="btn-order">توجّه للسيرفر للشراء 🪙</div>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

# -------------------------------------------------------------------
# ⚙️ [الموقع 2]: تصميم لوحة الإدارة والخيارات السيرية (/admin_panel_ltb_7392_x8q)
# -------------------------------------------------------------------
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>LTB Dashboard - لوحة الإدارة الشاملة</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #0f0c1b; color: #f2f1f5; margin: 0; padding: 40px; }
        .container { max-width: 1100px; margin: 0 auto; }
        .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 2px solid #2c254a; padding-bottom: 20px; }
        h2 { color: #5865F2; margin: 0; }
        .nav-links a { color: #deff9a; text-decoration: none; margin-left: 20px; font-weight: bold; }
        .logout-btn { background: #ed4245; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: bold; }
        .card { background: #17122b; border-radius: 8px; padding: 25px; margin-bottom: 35px; border: 1px solid #2c254a; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .card h3 { margin-top: 0; color: #5865F2; border-bottom: 1px solid #2c254a; padding-bottom: 10px; font-size: 18px; }
        .form-group { display: flex; flex-direction: column; margin-bottom: 15px; }
        .form-row { display: flex; gap: 20px; margin-bottom: 15px; }
        .form-row .form-group { flex: 1; }
        label { font-size: 14px; color: #a2a0b6; margin-bottom: 8px; font-weight: bold; }
        input[type="text"] { padding: 12px; background: #0f0c1b; border: 1px solid #2c254a; color: #fff; border-radius: 6px; font-size: 14px; }
        .btn-save { background: #43b581; color: white; border: none; padding: 14px; font-weight: bold; border-radius: 6px; cursor: pointer; width: 100%; font-size: 16px; }
        .btn-add { background: #5865F2; color: white; border: none; padding: 12px 24px; font-weight: bold; border-radius: 6px; cursor: pointer; }
        .btn-danger { background: #ed4245; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-size: 13px; font-weight: bold; }
        .acc-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .acc-table th, .acc-table td { padding: 14px; text-align: right; border-bottom: 1px solid #2c254a; }
        .acc-table th { color: #5865F2; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h2>⚙️ لوحة تحكم وإدارة متجر LTB</h2>
            <div class="nav-links">
                <a href="/ai_hub_secret_station">🧠 محطة الذكاء الاصطناعي (الموقع الثالث)</a>
                <a href="/logout" class="logout-btn">🚪 خروج</a>
            </div>
        </div>

        <div class="card">
            <h3>📦 إضافة كارت حساب جديد للمتجر</h3>
            <form method="POST" action="/add_account">
                <div class="form-row">
                    <div class="form-group"><label>رقم الحساب (ID):</label><input type="text" name="acc_id" placeholder="45" required></div>
                    <div class="form-group"><label>الوصف:</label><input type="text" name="acc_title" placeholder="حساب ستيم.." required></div>
                    <div class="form-group"><label>السعر:</label><input type="text" name="acc_price" placeholder="10 USDT" required></div>
                    <div class="form-group"><label>رابط الصورة:</label><input type="text" name="acc_img" placeholder="https://..." required></div>
                </div>
                <button type="submit" class="btn-add">➕ إضافة الحساب</button>
            </form>
            
            <table class="acc-table">
                <thead>
                    <tr><th>رقم الحساب</th><th>الوصف والعنوان</th><th>السعر</th><th>الإجراءات</th></tr>
                </thead>
                <tbody>
                    {% for acc_id, data in accounts.items() %}
                    <tr>
                        <td><code>#{{ acc_id }}</code></td>
                        <td>{{ data.title }}</td>
                        <td><b style="color:#43b581;">{{ data.price }}</b></td>
                        <td><a href="/delete_account/{{ acc_id }}" class="btn-danger">❌ حذف</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

# -------------------------------------------------------------------
# 🧠 [الموقع 3 الجديد]: بوابة الشات المنفصلة الخاصة بالذكاء الاصطناعي ومرفقاتها (/ai_hub_secret_station)
# -------------------------------------------------------------------
AI_HUB_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LTB AI Hub - شات المساعد الذكي</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0c0914; color: #fff; margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh; }
        .header { background: #17122b; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #2c254a; }
        .header h2 { color: #deff9a; margin: 0; font-size: 20px; }
        .header a { color: #a2a0b6; text-decoration: none; font-size: 14px; }
        .chat-container { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }
        .msg { max-width: 80%; padding: 12px 16px; border-radius: 8px; line-height: 1.5; font-size: 15px; word-wrap: break-word; }
        .user-msg { background: #5865F2; align-self: flex-start; border-bottom-left-radius: 0; }
        .ai-msg { background: #1c1735; border: 1px solid #2c254a; align-self: flex-end; color: #f2f1f5; border-bottom-right-radius: 0; }
        .input-area { background: #17122b; padding: 15px; border-top: 1px solid #2c254a; }
        form { display: flex; gap: 10px; max-width: 1200px; margin: 0 auto; width: 100%; align-items: center; }
        textarea { flex: 1; background: #0c0914; border: 1px solid #2c254a; border-radius: 6px; color: #fff; padding: 12px; resize: none; height: 24px; font-family: inherit; }
        .file-label { background: #231b3e; border: 1px solid #5865F2; color: #5865F2; padding: 12px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px; }
        .btn-send { background: #43b581; color: white; border: none; padding: 12px 24px; font-weight: bold; border-radius: 6px; cursor: pointer; }
        input[type="file"] { display: none; }
    </style>
</head>
<body>
    <div class="header">
        <h2>🧠 محطة الذكاء الاصطناعي المنفصلة (Site 3)</h2>
        <div>
            <a href="/admin_panel_ltb_7392_x8q" style="margin-left:15px;">⚙️ لوحة الإدارة</a>
            <a href="/">🛒 المتجر العام</a>
        </div>
    </div>
    
    <div class="chat-container" id="chatContainer">
        <div class="msg ai-msg">مرحباً بك يا سيدي في المحطة الثالثة المنفصلة. أنا عقلك المدبر المربوط بموقع المتجر وقاعدة البيانات. يمكنك التحدث معي هنا، كتابة الأكواد، أو رفع ملفات الحسابات النصية الكبيرة لتحديث الموقع تلقائياً!</div>
        {% for chat in history %}
            <div class="msg user-msg"><b>أنت:</b><br>{{ chat.user }}</div>
            <div class="msg ai-msg"><b>Gemini:</b><br>{{ chat.ai }}</div>
        {% endfor %}
    </div>

    <div class="input-area">
        <form method="POST" action="/ai_chat_submit" enctype="multipart/form-data">
            <label class="file-label" for="fileInput">📁 ارفع ملف (TXT)</label>
            <input type="file" name="file_data" id="fileInput" accept=".txt">
            <textarea name="prompt" placeholder="اكتب استفسارك البرمجي، أو اطلب معالجة الملف المرفوع..." required></textarea>
            <button type="submit" class="btn-send">إرسال واستخراج ⚡</button>
        </form>
    </div>

    <script>
        var objDiv = document.getElementById("chatContainer");
        objDiv.scrollTop = objDiv.scrollHeight;
    </script>
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>🔒 بوابة الإدارة السرية</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f0c1b; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: #17122b; padding: 40px; border-radius: 12px; box-shadow: 0 8px 25px rgba(0,0,0,0.6); width: 100%; max-width: 400px; text-align: center; border: 1px solid #2c254a; }
        h2 { color: #5865F2; margin-bottom: 25px; }
        input { width: 100%; padding: 12px; background: #0f0c1b; border: 1px solid #2c254a; color: #fff; border-radius: 6px; box-sizing: border-box; margin-bottom: 20px; }
        button { width: 100%; padding: 12px; background: #5865F2; border: none; color: white; font-size: 16px; font-weight: bold; border-radius: 6px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>🔒 تسجيل دخول الإدارة</h2>
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="اسم المستخدم السري" required>
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <button type="submit">تسجيل الدخول</button>
        </form>
    </div>
</body>
</html>
"""

# --- مسارات خادم الويب والمواقع ---
@app.route('/')
def public_store(): return render_template_string(STORE_FRONT_HTML, accounts=DB_ACCOUNTS)

@app.route('/admin_panel_ltb_7392_x8q')
def admin_panel():
    if 'logged_in' in session: return render_template_string(DASHBOARD_HTML, accounts=DB_ACCOUNTS)
    return render_template_string(LOGIN_HTML)

@app.route('/ai_hub_secret_station')
def ai_hub_station():
    if 'logged_in' not in session: return render_template_string(LOGIN_HTML)
    return render_template_string(AI_HUB_HTML, history=AI_CHAT_HISTORY)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('username') == BOT_CONFIG['web_user'] and request.form.get('password') == BOT_CONFIG['web_pass']:
        session['logged_in'] = True; return redirect(url_for('admin_panel'))
    return render_template_string(LOGIN_HTML)

@app.route('/add_account', methods=['POST'])
def add_account():
    if 'logged_in' not in session: return redirect(url_for('public_store'))
    aid = request.form.get('acc_id').strip()
    DB_ACCOUNTS[aid] = {"id": aid, "title": request.form.get('acc_title'), "price": request.form.get('acc_price'), "img_url": request.form.get('acc_img')}
    save_data(ACCOUNTS_FILE, DB_ACCOUNTS); return redirect(url_for('admin_panel'))

@app.route('/delete_account/<aid>')
def delete_account(aid):
    if 'logged_in' not in session: return redirect(url_for('public_store'))
    if aid in DB_ACCOUNTS: del DB_ACCOUNTS[aid]; save_data(ACCOUNTS_FILE, DB_ACCOUNTS)
    return redirect(url_for('admin_panel'))

# معالجة الشات والملفات المرفوعة داخل الموقع الثالث
@app.route('/ai_chat_submit', methods=['POST'])
def ai_chat_submit():
    if 'logged_in' not in session: return redirect(url_for('public_store'))
    prompt = request.form.get('prompt')
    
    file = request.files.get('file_data')
    if file and file.filename.endswith('.txt'):
        try:
            file_content = file.read().decode('utf-8')
            prompt += f"\n\n[محتوى الملف المرفوع عبر الموقع]:\n{file_content}"
        except: pass

    # استدعاء دالة الذكاء الاصطناعي
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ai_response = loop.run_until_complete(ask_gemini_ai(prompt))
    
    # فحص تلقائي لتحديث الحسابات إذا قام بإنشائها
    if "{" in ai_response and "}" in ai_response and '"title"' in ai_response:
        try:
            start_idx = ai_response.find("{")
            end_idx = ai_response.rfind("}") + 1
            json_str = ai_response[start_idx:end_idx]
            parsed_json = json.loads(json_str)
            global DB_ACCOUNTS
            DB_ACCOUNTS.update(parsed_json)
            save_data(ACCOUNTS_FILE, DB_ACCOUNTS)
        except: pass

    AI_CHAT_HISTORY.append({"user": request.form.get('prompt'), "ai": ai_response})
    save_data(AI_HISTORY_FILE, AI_CHAT_HISTORY)
    return redirect(url_for('ai_hub_station'))

@app.route('/logout')
def logout(): session.pop('logged_in', None); return redirect(url_for('public_store'))

def run_http_server(): app.run(host='0.0.0.0', port=8080)


# 🤖 محرك الاتصال بـ Google Gemini المحدث (إصلاح خطأ 404)
async def ask_gemini_ai(prompt_text):
    # استخدام الرابط المعتمد والمحدث للنموذج الصحيح بدلاً من النسخ القديمة الموقوفة
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    system_instruction = (
        "أنت المساعد الذكي وخبير البرمجة لمتجر LTB. يمكنك مساعدة الأدمن وتعديل الحسابات بصيغة JSON "
        f"قائمة الحسابات الحالية هي: {json.dumps(DB_ACCOUNTS, ensure_ascii=False)}. "
        "أجب دائماً باللغة العربية الفصحى الواضحة والمنسقة برمجياً."
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]}
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                res_json = await response.json()
                try: return res_json['candidates'][0]['content']['parts'][0]['text']
                except: return "⚠️ واجهت مشكلة في قراءة رد الذكاء الاصطناعي."
            else:
                return f"❌ خطأ في الاتصال بخادم جوجل الذكي: {response.status}"

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
            
            if "{" in ai_response and "}" in ai_response and '"title"' in ai_response:
                try:
                    start_idx = ai_response.find("{")
                    end_idx = ai_response.rfind("}") + 1
                    parsed_json = json.loads(ai_response[start_idx:end_idx])
                    global DB_ACCOUNTS
                    DB_ACCOUNTS.update(parsed_json)
                    save_data(ACCOUNTS_FILE, DB_ACCOUNTS)
                    await message.channel.send("⚡ **[نظام LTB]: تم حفظ الحسابات بنجاح في الموقع الأول!**")
                except: pass
                
            if len(ai_response) > 2000:
                for chunk in [ai_response[i:i+1900] for i in range(0, len(ai_response), 1900)]:
                    await message.channel.send(chunk)
            else:
                await message.channel.send(ai_response)
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print("⚡ Triple-Site Architecture & Fixed Gemini Engine Online!")

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN: bot.run(TOKEN)