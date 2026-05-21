import os
import asyncio
import json
from threading import Thread
from flask import Flask, render_template_string, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import discord
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput

# 🛡️ محاولة استدعاء مكتبة جوجل بحماية ذكية لمنع تعطل السيرفر على Render
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
    ai_available = True
except Exception as e:
    print(f"⚠️ تحذير: لم يتم العثور على مكتبة جوجل أو المفتاح غير صحيح، سيتم تشغيل البوت بدون ذكاء اصطناعي: {e}")
    ai_available = False

# 🌐 إعداد خادم الويب وإعدادات الملفات المرفوعة
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "LTB_SUPER_SECRET_KEY_9988")

UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 🔒 قاعدة بيانات الإعدادات الشاملة الثابتة لسيرفرك
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

DISCORD_SERVER_LINK = "https://discord.gg/quMbWAKgZy"
ACCOUNTS_FILE = "accounts.json"
DB_ACCOUNTS = {}

# 📂 دالة قراءة الحسابات وتوليدها تلقائياً (من 1 إلى 60) مع فحص مجلدات الـ Uploads ديناميكياً
def load_accounts():
    global DB_ACCOUNTS
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                DB_ACCOUNTS = json.load(f)
        except:
            DB_ACCOUNTS = {}
            
    # توليد وتأمين الـ 60 حساباً بناءً على المجلدات والصور المتوفرة
    updated = False
    for i in range(1, 61):
        str_id = str(i)
        if str_id not in DB_ACCOUNTS:
            # فحص إذا كان المجلد يحتوي على صورة مرفوعة مسبقاً داخل مجلد static/uploads
            account_img = "https://i.imgur.com/8N69F3R.png" # صورة افتراضية في حال عدم وجود صورة
            folder_path = os.path.join(UPLOAD_FOLDER, str_id)
            if os.path.exists(folder_path):
                images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if images:
                    account_img = f"/static/uploads/{str_id}/{images[0]}"
            
            DB_ACCOUNTS[str_id] = {
                "id": str_id,
                "title": f"حساب ألعاب احترافي #{str_id}",
                "icon": "🎮",
                "description": f"حساب ألعاب بريميوم رقم {str_id} من الحزمة الشاملة بملف الـ Rar. الحساب جاهز للتسليم الفوري وآمن تماماً للعب والمقايضة.",
                "img_url": account_img,
                "price": "10 USDT"
            }
            updated = True
            
    if updated:
        save_accounts()

def save_accounts():
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(DB_ACCOUNTS, f, ensure_ascii=False, indent=4)

load_accounts()
active_tickets = {}

# 🛒 تصميم واجهة المتجر الأسطورية المتجاوبة مع الصور
STORE_FRONT_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LTB MEGA STORE | المتجر الأسطوري 🛒</title>
    <style>
        :root { 
            --main-gradient: linear-gradient(135deg, #5865F2, #854cee); 
            --bg-dark: #07050c; 
            --card-bg: rgba(19, 15, 36, 0.7); 
            --border-glow: #3d2f6d;
            --text-muted: #b4b2ca; 
            --success-color: #00ff87; 
        }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: radial-gradient(circle at center, #150f2e 0%, var(--bg-dark) 100%); 
            color: #fff; margin: 0; padding: 40px 20px; min-height: 100vh;
        }
        .header { 
            text-align: center; max-width: 850px; margin: 0 auto 50px auto; background: var(--card-bg); 
            padding: 40px; border-radius: 24px; border: 1px solid var(--border-glow); backdrop-filter: blur(12px);
            box-shadow: 0 20px 50px rgba(0,0,0,0.6); 
        }
        .header h1 { 
            background: linear-gradient(90deg, #00ff87, #60efff, #0061ff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 0; font-size: 38px; 
        }
        .info-box { background: rgba(26, 20, 51, 0.6); padding: 20px; border-radius: 14px; margin-top: 25px; border-right: 5px solid #5865F2; text-align: right; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 35px; max-width: 1250px; margin: 0 auto; }
        .card { 
            background: var(--card-bg); border-radius: 20px; border: 1px solid var(--border-glow); overflow: hidden; 
            backdrop-filter: blur(10px); box-shadow: 0 10px 25px rgba(0,0,0,0.5); transition: all 0.4s ease; cursor: pointer; position: relative; 
        }
        .card:hover { transform: translateY(-8px); border-color: #5865F2; }
        .card img { width: 100%; height: 200px; object-fit: cover; background: #0f0c1b; }
        .card-body { padding: 22px; position: relative; }
        .card-id { background: var(--main-gradient); color: #fff; padding: 5px 12px; border-radius: 8px; font-size: 12px; font-weight: bold; position: absolute; top: 15px; right: 15px; }
        .card-title { margin: 10px 0 15px 0; font-size: 19px; font-weight: bold; display: flex; align-items: center; gap: 8px; }
        .card-price { color: var(--success-color); font-weight: bold; font-size: 20px; margin-bottom: 18px; }
        .btn-view { display: block; text-align: center; background: rgba(88, 101, 242, 0.1); color: #5865F2; border: 1px solid rgba(88, 101, 242, 0.4); padding: 12px; border-radius: 10px; font-weight: bold; font-size: 14px; }
        .card:hover .btn-view { background: var(--main-gradient); color: white; }
        .modal-overlay { display: none; position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(5, 3, 10, 0.85); z-index: 1000; justify-content: center; align-items: center; backdrop-filter: blur(8px); }
        .modal-content { background: #130f24; width: 92%; max-width: 650px; border-radius: 24px; border: 1px solid #32265c; overflow: hidden; position: relative; }
        .modal-img { width: 100%; max-height: 320px; object-fit: cover; }
        .modal-body { padding: 30px; text-align: right; }
        .modal-close { position: absolute; top: 20px; left: 20px; background: rgba(237, 66, 69, 0.2); color: #ed4245; border: none; width: 35px; height: 35px; border-radius: 50%; font-weight: bold; cursor: pointer; }
        .btn-buy-now { display: block; text-align: center; background: linear-gradient(90deg, #00ff87, #0061ff); color: #07050c; padding: 15px; border-radius: 12px; text-decoration: none; font-weight: bold; font-size: 17px; margin-top: 25px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ LTB GLOBAL HUB | كتالوج الحسابات الشامل</h1>
        <div class="info-box">
            <p>مرحباً بك في واجهة العرض الرسمية. لتعديل أو شراء أي حساب، يرجى التوجه لسيرفر الديسكورد عبر فتح تذكرة دعم مخصصة برقم الحساب المعين.</p>
        </div>
    </div>
    
    <div class="grid">
        {% for acc_id, data in accounts.items()|sort(attribute='0'|int) %}
        <div class="card" onclick="openDetails('{{ acc_id }}', '{{ data.title }}', '{{ data.price }}', '{{ data.img_url }}', '{{ data.description|default('') }}', '{{ data.icon|default('🎮') }}')">
            <span class="card-id">#{{ acc_id }}</span>
            <img src="{{ data.img_url }}" alt="Preview" onerror="this.src='https://i.imgur.com/8N69F3R.png'">
            <div class="card-body">
                <div class="card-title"><span>{{ data.icon|default('🎮') }}</span> {{ data.title }}</div>
                <div class="card-price">🪙 {{ data.price }}</div>
                <div class="btn-view">👀 تفاصيل الحساب الكاملة والوصف</div>
            </div>
        </div>
        {% endfor %}
    </div>

    <div id="detailsModal" class="modal-overlay" onclick="closeDetails(event)">
        <div class="modal-content" onclick="event.stopPropagation()">
            <button class="modal-close" onclick="closeDetails(null)">X</button>
            <img id="m_img" src="" class="modal-img" alt="Large View" onerror="this.src='https://i.imgur.com/8N69F3R.png'">
            <div class="modal-body">
                <h2 id="m_title" style="margin-top:0; font-size:24px;"></h2>
                <h3 id="m_price"></h3>
                <div style="background: rgba(88, 101, 242, 0.08); padding: 18px; border-radius: 12px; border-right: 4px solid #5865F2; margin-bottom: 20px;">
                    <p id="m_desc" style="color: var(--text-muted); font-size: 14px; line-height: 1.7;"></p>
                </div>
                <a href="{{ server_link }}" target="_blank" class="btn-buy-now">🤝 الانتقال الفوري للسيرفر وبدء المعاملة</a>
            </div>
        </div>
    </div>

    <script>
        function openDetails(id, title, price, img, desc, icon) {
            document.getElementById('m_id')?.innerText || '';
            document.getElementById('m_title').innerText = icon + " " + title;
            document.getElementById('m_price').innerText = "السعر: " + price;
            document.getElementById('m_img').src = img;
            document.getElementById('m_desc').innerText = desc;
            document.getElementById('detailsModal').style.display = 'flex';
        }
        function closeDetails(e) {
            if(!e || e.target === document.getElementById('detailsModal') || e === null) {
                document.getElementById('detailsModal').style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""

# ⚙️ لوحة الإدارة المعدلة لإتاحة التعديل الفوري على أسماء، أسعار، وصور الحسابات الـ 60
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>LTB Control Hub</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #07050c; color: #f2f1f5; margin: 0; padding: 40px; }
        .container { max-width: 1300px; margin: 0 auto; }
        .header-bar { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #231b3e; padding-bottom: 20px; margin-bottom: 30px; }
        h2 { color: #5865F2; margin: 0; }
        .logout-btn { background: #ed4245; color: white; padding: 10px 22px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .card { background: #130f24; border-radius: 16px; padding: 30px; margin-bottom: 40px; border: 1px solid #231b3e; }
        .form-inline { display: flex; gap: 8px; flex-wrap: wrap; width: 100%; }
        input[type="text"] { padding: 8px; background: #07050c; border: 1px solid #231b3e; color: #fff; border-radius: 6px; font-size: 13px; }
        .btn-update { background: #43b581; color: white; border: none; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .acc-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .acc-table th, .acc-table td { padding: 12px; text-align: right; border-bottom: 1px solid #231b3e; font-size: 14px; }
        .thumb { width: 45px; height: 45px; object-fit: cover; border-radius: 6px; border: 1px solid #5865F2; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h2>⚙️ لوحة إدارة وتحديث بيانات وصور المتجر الشامل (1-60)</h2>
            <a href="/logout" class="logout-btn">🚪 خروج آمن</a>
        </div>

        <div class="card">
            <h3>📋 تعديل وتعديل الحسابات والروابط المباشرة للصور المفقودة</h3>
            <table class="acc-table">
                <thead>
                    <tr><th>صورة العرض</th><th>رقم الحساب</th><th>الاسم والبيانات التسويقية الحالية</th><th>الإجراء وتحديث البيانات الفوري</th></tr>
                </thead>
                <tbody>
                    {% for acc_id, data in accounts.items()|sort(attribute='0'|int) %}
                    <tr>
                        <td><img src="{{ data.img_url }}" class="thumb" onerror="this.src='https://i.imgur.com/8N69F3R.png'"></td>
                        <td><code>#{{ acc_id }}</code></td>
                        <td>
                            <div style="font-weight: bold; color: #fff;">{{ data.title }}</div>
                            <div style="color: #00ff87; font-size: 12px; margin-top: 4px;">السعر الحالي: {{ data.price }}</div>
                        </td>
                        <td>
                            <form method="POST" action="/update_account_full/{{ acc_id }}" class="form-inline">
                                <input type="text" name="u_title" value="{{ data.title }}" style="width: 200px;" placeholder="اسم الحساب الجديد" required>
                                <input type="text" name="u_price" value="{{ data.price }}" style="width: 80px;" placeholder="السعر" required>
                                <input type="text" name="u_img" value="{{ data.img_url }}" style="width: 300px;" placeholder="رابط الصورة المباشر URL (Imgur)" required>
                                <button type="submit" class="btn-update">⚡ حفظ التعديل</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>🔒 تسجيل الدخول</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #07050c; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #130f24; padding: 40px; border-radius: 16px; border: 1px solid #231b3e; text-align: center; width: 320px; }
        input { width: 100%; padding: 10px; margin: 10px 0; background: #07050c; border: 1px solid #231b3e; color: #fff; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #5865F2; border: none; color: white; font-weight: bold; border-radius: 6px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔒 بوابة الإدارة</h2>
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="اسم المستخدم" required>
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <button type="submit">دخول</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def public_store():
    return render_template_string(STORE_FRONT_HTML, accounts=DB_ACCOUNTS, server_link=DISCORD_SERVER_LINK)

@app.route('/admin_panel_ltb_7392_x8q')
def admin_panel():
    if 'logged_in' in session: 
        return render_template_string(DASHBOARD_HTML, config=BOT_CONFIG, accounts=DB_ACCOUNTS)
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('username') == BOT_CONFIG['web_user'] and request.form.get('password') == BOT_CONFIG['web_pass']:
        session['logged_in'] = True
        return redirect(url_for('admin_panel'))
    return redirect(url_for('admin_panel'))

@app.route('/update_account_full/<aid>', methods=['POST'])
def update_account_full(aid):
    if 'logged_in' not in session: return redirect(url_for('public_store'))
    if aid in DB_ACCOUNTS:
        DB_ACCOUNTS[aid]['title'] = request.form.get('u_title').strip()
        DB_ACCOUNTS[aid]['price'] = request.form.get('u_price').strip()
        DB_ACCOUNTS[aid]['img_url'] = request.form.get('u_img').strip()
        save_accounts()
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout(): 
    session.pop('logged_in', None)
    return redirect(url_for('public_store'))

def run_http_server(): app.run(host='0.0.0.0', port=8080)


# 🤖 إعدادات وتشغيل بوت الديسكورد 
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def ask_ai(ctx, *, prompt: str):
    if ai_available:
        try:
            response = ai_model.generate_content(prompt)
            await ctx.send(response.text[:2000])
        except Exception as e:
            await ctx.send(f"❌ خطأ أثناء توليد النص: {e}")
    else:
        await ctx.send("⚠️ ميزة الذكاء الاصطناعي معطلة حالياً لعدم توفر المكتبة في السيرفر، لكن المتجر يعمل بالكامل!")

@bot.event
async def on_ready():
    print("⚡ LTB Bot online. Safe from crash and 1-60 full layout active!")

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN: bot.run(TOKEN)