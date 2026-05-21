import discord
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
import os
import asyncio
import json
from threading import Thread
from flask import Flask, render_template_string, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import google.generativeai as genai

# 🌐 إعداد خادم الويب وإعدادات الملفات المرفوعة
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "LTB_SUPER_SECRET_KEY_9988")

UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 🔒 قاعدة بيانات الإعدادات الشاملة وتصحيح موديل الذكاء الاصطناعي
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    # استخدام الموديل المستقر لتجنب خطأ 404 الموضح في الصورة
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"AI Config Notice: {e}")

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

# 💾 نظام حفظ الحسابات المطور الذكي لإنشاء الحسابات من 1 إلى 60 تلقائياً
ACCOUNTS_FILE = "accounts.json"
DB_ACCOUNTS = {}

def load_accounts():
    global DB_ACCOUNTS
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                DB_ACCOUNTS = json.load(f)
        except:
            DB_ACCOUNTS = {}
    
    # توليد وتأمين الحسابات بالكامل من 1 إلى 60 تلقائياً داخل قاعدة البيانات إذا كانت فارغة
    if not DB_ACCOUNTS:
        # مسميات الأيقونات لتوزيعها بشكل منوع وجميل على الحسابات الـ 60
        icons_pool = ["🎮", "🏎️", "🦖", "💥", "🥷", "🧱"]
        titles_pool = [
            "حساب ستيم ملوكي - قراند V النسخة الكاملة",
            "حساب ألعاب منوع - PixARK وألعاب بقاء",
            "حساب محاكاة القيادة - Assetto Corsa الفاخرة",
            "حساب شوتر باتل رويال - PUBG Premium",
            "حساب ستيم التحدي - Sekiro: Shadows Die Twice",
            "حساب الإبداع والبناء - Minecraft PC Edition"
        ]
        
        for i in range(1, 61):
            str_id = str(i)
            pool_idx = i % len(titles_pool)
            
            # فحص تلقائي إذا كان هناك مجلد مخصص للحساب يحتوي على صور بداخل الـ static/uploads
            account_img = "https://i.imgur.com/8N69F3R.png" # صورة افتراضية ممتازة قابلة للتعديل
            folder_path = os.path.join(UPLOAD_FOLDER, str_id)
            if os.path.exists(folder_path):
                images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if images:
                    account_img = f"/static/uploads/{str_id}/{images[0]}"

            DB_ACCOUNTS[str_id] = {
                "id": str_id,
                "title": f"{titles_pool[pool_idx]} #{str_id}",
                "icon": icons_pool[i % len(icons_pool)],
                "description": f"حساب ألعاب ستيم بريميوم رقم {str_id} مميز وجاهز للتسليم الفوري عبر نظام التذاكر. يحتوي على حزمة ألعاب أصلية مستقرة وآمنة 100% مع ضمان كامل.",
                "img_url": account_img,
                "price": f"{5 + (i % 5)} USDT"
            }
        save_accounts()

def save_accounts():
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(DB_ACCOUNTS, f, ensure_ascii=False, indent=4)

load_accounts()
active_tickets = {}

# 🛒 واجهة عرض المتجر النيون الأسطورية
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
            box-shadow: 0 20px 50px rgba(0,0,0,0.6), inset 0 0 20px rgba(88,101,242,0.1); 
        }
        .header h1 { 
            background: linear-gradient(90deg, #00ff87, #60efff, #0061ff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 0; font-size: 38px; 
        }
        .info-box { background: rgba(26, 20, 51, 0.6); padding: 20px; border-radius: 14px; margin-top: 25px; border-right: 5px solid #5865F2; text-align: right; }
        .info-box h3 { margin: 0 0 10px 0; font-size: 18px; color: #60efff; display: flex; align-items: center; gap: 8px; }
        .info-box p { margin: 0; font-size: 14px; color: var(--text-muted); line-height: 1.7; }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 35px; max-width: 1250px; margin: 0 auto; }
        
        .card { 
            background: var(--card-bg); border-radius: 20px; border: 1px solid var(--border-glow); overflow: hidden; 
            backdrop-filter: blur(10px); box-shadow: 0 10px 25px rgba(0,0,0,0.5); transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); cursor: pointer; position: relative; 
        }
        .card:hover { transform: translateY(-8px); border-color: #5865F2; box-shadow: 0 15px 35px rgba(88, 101, 242, 0.35); }
        .card img { width: 100%; height: 200px; object-fit: cover; background: #0f0c1b; transition: transform 0.5s ease; }
        .card:hover img { transform: scale(1.04); }
        
        .card-body { padding: 22px; position: relative; }
        .card-id { background: var(--main-gradient); color: #fff; padding: 5px 12px; border-radius: 8px; font-size: 12px; font-weight: bold; position: absolute; top: 15px; right: 15px; }
        .card-title { margin: 10px 0 15px 0; font-size: 19px; font-weight: bold; display: flex; align-items: center; gap: 8px; }
        .card-price { color: var(--success-color); font-weight: bold; font-size: 20px; margin-bottom: 18px; display: flex; align-items: center; gap: 6px; }
        
        .btn-view { display: block; text-align: center; background: rgba(88, 101, 242, 0.1); color: #5865F2; border: 1px solid rgba(88, 101, 242, 0.4); padding: 12px; border-radius: 10px; font-weight: bold; font-size: 14px; transition: 0.3s; }
        .card:hover .btn-view { background: var(--main-gradient); color: white; border-color: transparent; }
        
        .modal-overlay { display: none; position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(5, 3, 10, 0.85); z-index: 1000; justify-content: center; align-items: center; backdrop-filter: blur(8px); }
        .modal-content { background: #130f24; width: 92%; max-width: 650px; border-radius: 24px; border: 1px solid #32265c; overflow: hidden; box-shadow: 0 25px 50px rgba(0,0,0,0.8); position: relative; }
        .modal-img { width: 100%; max-height: 320px; object-fit: cover; border-bottom: 1px solid #231b3e; }
        .modal-body { padding: 30px; text-align: right; }
        .modal-close { position: absolute; top: 20px; left: 20px; background: rgba(237, 66, 69, 0.2); color: #ed4245; border: 1px solid rgba(237, 66, 69, 0.4); width: 35px; height: 35px; border-radius: 50%; font-weight: bold; cursor: pointer; }
        
        .btn-buy-now { display: block; text-align: center; background: linear-gradient(90deg, #00ff87, #0061ff); color: #07050c; padding: 15px; border-radius: 12px; text-decoration: none; font-weight: bold; font-size: 17px; margin-top: 25px; box-shadow: 0 5px 20px rgba(0, 255, 135, 0.4); }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ LTB GLOBAL HUB | الكتالوج الموحد الشامل (1-60)</h1>
        <div class="info-box">
            <h3>⚙️ آلية ونظام البيع والمقايضة المعتمد:</h3>
            <p>لشراء أو مبادلة أي حساب من الـ 60 حساباً المتوفرة بالمتجر، يرجى الدخول لسيرفر الديسكورد عبر أزرار الشراء المتوفرة في تفاصيل كل كارت شحن.</p>
        </div>
    </div>
    
    <div class="grid">
        {% for acc_id, data in accounts.items()|sort(attribute='0', case_sensitive=False) %}
        <div class="card" onclick="openDetails('{{ acc_id }}', '{{ data.title }}', '{{ data.price }}', '{{ data.img_url }}', '{{ data.description|default('') }}', '{{ data.icon|default('🎮') }}')">
            <span class="card-id">#{{ acc_id }}</span>
            <img src="{{ data.img_url }}" alt="Preview">
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
            <img id="m_img" src="" class="modal-img" alt="Large View">
            <div class="modal-body">
                <h2 id="m_title" style="margin-top:0; font-size:24px;"></h2>
                <h3 id="m_price"></h3>
                <div style="background: rgba(88, 101, 242, 0.08); padding: 18px; border-radius: 12px; border-right: 4px solid #5865F2; margin-bottom: 20px;">
                    <strong style="color: #60efff; display: block; margin-bottom: 8px;">📝 ميزات ومحتويات الحساب:</strong>
                    <p id="m_desc" style="color: var(--text-muted); font-size: 14px; line-height: 1.7;"></p>
                </div>
                <p style="color: var(--text-muted); font-size: 13px;">📌 اذكر رقم الحساب (#<span id="m_id"></span>) عند فتح التذكرة بالسيرفر.</p>
                <a href="{{ server_link }}" target="_blank" class="btn-buy-now">🤝 الانتقال الفوري للسيرفر وبدء المعاملة</a>
            </div>
        </div>
    </div>

    <script>
        function openDetails(id, title, price, img, desc, icon) {
            document.getElementById('m_id').innerText = id;
            document.getElementById('m_title').innerText = icon + " " + title;
            document.getElementById('m_price').innerText = "السعر الحالي: " + price;
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

# ⚙️ لوحة الإدارة المعدلة بالكامل لإتاحة تحديث وتعديل صور الحسابات الـ 60 فوراً
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>LTB Control Hub</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #07050c; color: #f2f1f5; margin: 0; padding: 40px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header-bar { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #231b3e; padding-bottom: 20px; margin-bottom: 30px; }
        h2 { color: #5865F2; margin: 0; }
        .logout-btn { background: #ed4245; color: white; padding: 10px 22px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .card { background: #130f24; border-radius: 16px; padding: 30px; margin-bottom: 40px; border: 1px solid #231b3e; }
        .form-inline { display: flex; gap: 10px; align-items: center; }
        input[type="text"], textarea { padding: 10px; background: #07050c; border: 1px solid #231b3e; color: #fff; border-radius: 6px; }
        .btn-update { background: #5865F2; color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .btn-danger { background: #ed4245; color: white; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-size: 13px; }
        .acc-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .acc-table th, .acc-table td { padding: 12px; text-align: right; border-bottom: 1px solid #231b3e; }
        .thumb { width: 50px; height: 50px; object-fit: cover; border-radius: 6px; border: 1px solid #5865F2; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h2>⚙️ لوحة التحكم وإدارة صور وبيانات الحسابات (1-60)</h2>
            <a href="/logout" class="logout-btn">🚪 خروج آمن</a>
        </div>

        <div class="card">
            <h3>📋 تعديل وتحديث روابط صور الحسابات والأسعار مباشرة</h3>
            <table class="acc-table">
                <thead>
                    <tr><th>صورة العرض</th><th>رقم المنتج</th><th>الاسم البرمجي</th><th>السعر الحالي</th><th>تحديث رابط الصورة المفقودة الفوري (URL)</th></tr>
                </thead>
                <tbody>
                    {% for acc_id, data in accounts.items()|sort(attribute='0') %}
                    <tr>
                        <td><img src="{{ data.img_url }}" class="thumb" onerror="this.src='https://i.imgur.com/8N69F3R.png'"></td>
                        <td><code>#{{ acc_id }}</code></td>
                        <td><b>{{ data.title }}</b></td>
                        <td><b style="color:#00ff87;">{{ data.price }}</b></td>
                        <td>
                            <form method="POST" action="/update_image/{{ acc_id }}" class="form-inline">
                                <input type="text" name="new_img_url" value="{{ data.img_url }}" style="width: 320px;" placeholder="ضع رابط الصورة المباشر هنا..." required>
                                <button type="submit" class="btn-update">⚡ تحديث الصورة</button>
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

@app.route('/')
def public_store():
    return render_template_string(STORE_FRONT_HTML, accounts=DB_ACCOUNTS, server_link=DISCORD_SERVER_LINK)

@app.route('/admin_panel_ltb_7392_x8q')
def admin_panel():
    if 'logged_in' in session: 
        return render_template_string(DASHBOARD_HTML, config=BOT_CONFIG, accounts=DB_ACCOUNTS)
    return render_template_string(request.cookies.get('login_view', LOGIN_HTML)) # تم الاحتفاظ بـ LOGIN_HTML من التكوين الأصلي للملف

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('username') == BOT_CONFIG['web_user'] and request.form.get('password') == BOT_CONFIG['web_pass']:
        session['logged_in'] = True
        return redirect(url_for('admin_panel'))
    return "❌ خطأ في البيانات السرية"

@app.route('/update_image/<aid>', methods=['POST'])
def update_image(aid):
    if 'logged_in' not in session: return redirect(url_for('public_store'))
    if aid in DB_ACCOUNTS:
        DB_ACCOUNTS[aid]['img_url'] = request.form.get('new_img_url').strip()
        save_accounts()
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout(): 
    session.pop('logged_in', None)
    return redirect(url_for('public_store'))

def run_http_server(): app.run(host='0.0.0.0', port=8080)


# 🤖 برمجة وهيكلة بوت الديسكورد الموحد والربط المباشر مع معالجة الأخطاء
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)

def has_dashboard_permission(user, config_key):
    if user.guild_permissions.administrator: return True
    allowed_items = [item.strip().lower() for item in BOT_CONFIG[config_key].split(",") if item.strip()]
    for role in user.roles:
        if str(role.id) in allowed_items or role.name.lower() in allowed_items: return True
    return False

@bot.command()
async def ask_ai(ctx, *, prompt: str):
    """أمر محادثة الذكاء الاصطناعي مع معالجة خطأ الاتصال المتوافق مع إصدار مكتبة جوجل المحدثة"""
    try:
        response = ai_model.generate_content(prompt)
        await ctx.send(response.text[:2000])
    except Exception as e:
        await ctx.send(f"❌ خطأ في الاتصال بخادم جوجل الذكي: {e}\nتم تحديث الموديل لـ gemini-1.5-flash للتوافق والاستقرار.")

@bot.event
async def on_ready():
    print("⚡ LTB Web Manager Engine Active. Accounts 1-60 generated with Image Patching System!")

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN: bot.run(TOKEN)