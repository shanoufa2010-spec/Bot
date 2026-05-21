import os
import asyncio
import json
from threading import Thread
from flask import Flask, render_template_string, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import discord
from discord.ext import commands

# 🌐 إعداد خادم الويب وإعدادات المجلدات
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "LTB_SUPER_SECRET_KEY_9988")

UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 🔒 قاعدة بيانات الإعدادات الشاملة (لوحة التحكم الكاملة)
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

# 📂 دالة قراءة الحسابات وترتيبها حسابياً بشكل صحيح (1، 2، 3... إلى 60)
def load_accounts():
    global DB_ACCOUNTS
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                DB_ACCOUNTS = json.load(f)
        except:
            DB_ACCOUNTS = {}
            
    # توليد وضمان وجود الحسابات من 1 إلى 60 مرتبة عددياً
    for i in range(1, 61):
        str_id = str(i)
        if str_id not in DB_ACCOUNTS:
            account_img = "https://i.imgur.com/8N69F3R.png" # صورة افتراضية
            folder_path = os.path.join(UPLOAD_FOLDER, str_id)
            if os.path.exists(folder_path):
                images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if images:
                    account_img = f"/static/uploads/{str_id}/{images[0]}"
            
            DB_ACCOUNTS[str_id] = {
                "id": str_id,
                "title": f"حساب ألعاب احترافي #{str_id}",
                "icon": "🎮",
                "description": f"حساب ألعاب بريميوم رقم {str_id} جاهز للتسليم الفوري عبر نظام التذاكر.",
                "img_url": account_img,
                "price": "10 USDT"
            }
    save_accounts()

def save_accounts():
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(DB_ACCOUNTS, f, ensure_ascii=False, indent=4)

load_accounts()

# 🛒 واجهة عرض المتجر العام للمشترين
STORE_FRONT_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LTB MEGA STORE | المتجر 🛒</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #07050c; color: #fff; padding: 40px 20px; }
        .header { text-align: center; max-width: 850px; margin: 0 auto 50px auto; background: rgba(19, 15, 36, 0.7); padding: 30px; border-radius: 16px; border: 1px solid #3d2f6d; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 30px; max-width: 1200px; margin: 0 auto; }
        .card { background: rgba(19, 15, 36, 0.7); border-radius: 16px; border: 1px solid #3d2f6d; overflow: hidden; position: relative; text-align: right; }
        .card img { width: 100%; height: 180px; object-fit: cover; }
        .card-body { padding: 20px; }
        .card-id { background: #5865F2; color: #fff; padding: 4px 10px; border-radius: 6px; font-size: 12px; position: absolute; top: 10px; right: 10px; }
        .card-title { font-size: 18px; font-weight: bold; margin: 10px 0; }
        .card-price { color: #00ff87; font-weight: bold; font-size: 18px; }
    </style>
</head>
<body>
    <div class="header">
        <h2>⚡ LTB GLOBAL HUB | المتجر الشامل</h2>
    </div>
    <div class="grid">
        {% for acc_id in accounts.keys()|map('int')|sort %}
        {% set data = accounts[acc_id|string] %}
        <div class="card">
            <span class="card-id">#{{ acc_id }}</span>
            <img src="{{ data.img_url }}" onerror="this.src='https://i.imgur.com/8N69F3R.png'">
            <div class="card-body">
                <div class="card-title">{{ data.icon }} {{ data.title }}</div>
                <div class="card-price">🪙 {{ data.price }}</div>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

# ⚙️ لوحة الإدارة الكاملة المحدثة (ترتيب رقمي صحيح + رفع ملفات الصور مباشرة + باقي الإعدادات)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>لوحة تحكم LTB الكاملة</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #07050c; color: #f2f1f5; margin: 0; padding: 30px; }
        .container { max-width: 1300px; margin: 0 auto; }
        .header-bar { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #231b3e; padding-bottom: 20px; margin-bottom: 30px; }
        h2, h3 { color: #5865F2; margin-top: 0; }
        .logout-btn { background: #ed4245; color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .card { background: #130f24; border-radius: 16px; padding: 25px; margin-bottom: 35px; border: 1px solid #231b3e; }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .form-group { display: flex; flex-direction: column; }
        .form-group label { margin-bottom: 5px; color: #b4b2ca; font-size: 14px; }
        input[type="text"], input[type="file"] { padding: 10px; background: #07050c; border: 1px solid #231b3e; color: #fff; border-radius: 6px; }
        .btn-save { background: #5865F2; color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .btn-update { background: #43b581; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 13px; }
        .acc-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .acc-table th, .acc-table td { padding: 12px; text-align: right; border-bottom: 1px solid #231b3e; }
        .thumb { width: 50px; height: 50px; object-fit: cover; border-radius: 6px; border: 1px solid #5865F2; }
        .file-input-wrapper { display: flex; align-items: center; gap: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h2>⚙️ لوحة التحكم والإدارة الشاملة لـ LTB</h2>
            <a href="/logout" class="logout-btn">🚪 خروج آمن</a>
        </div>

        <div class="card">
            <h3>🔒 إعدادات البوت والمنصة العامة</h3>
            <form method="POST" action="/update_config">
                <div class="form-grid">
                    <div class="form-group">
                        <label>رابط محفظة BEP20 (USDT):</label>
                        <input type="text" name="wallet_bep20" value="{{ config.wallet_bep20 }}">
                    </div>
                    <div class="form-group">
                        <label>رابط محفظة TRC20 (USDT):</label>
                        <input type="text" name="wallet_trc20" value="{{ config.wallet_trc20 }}">
                    </div>
                    <div class="form-group">
                        <label>ID قناة السجلات (Logs):</label>
                        <input type="text" name="log_channel_id" value="{{ config.log_channel_id }}">
                    </div>
                </div>
                <div class="form-grid">
                    <div class="form-group">
                        <label>رتب إعداد الأوامر (تفصل بفاصلة):</label>
                        <input type="text" name="perm_setup_cmd" value="{{ config.perm_setup_cmd }}">
                    </div>
                    <div class="form-group">
                        <label>رتب إغلاق التذاكر:</label>
                        <input type="text" name="perm_close_ticket" value="{{ config.perm_close_ticket }}">
                    </div>
                    <div class="form-group">
                        <label>اسم مستخدم اللوحة:</label>
                        <input type="text" name="web_user" value="{{ config.web_user }}">
                    </div>
                </div>
                <button type="submit" class="btn-save">💾 حفظ إعدادات النظام الموحد</button>
            </form>
        </div>

        <div class="card">
            <h3>📋 إدارة ورفع صور الحسابات (من 1 إلى 60 بالترتيب)</h3>
            <table class="acc-table">
                <thead>
                    <tr>
                        <th>صورة العرض</th>
                        <th>رقم المنتج</th>
                        <th>بيانات وعنوان الحساب الحالية</th>
                        <th>السعر</th>
                        <th>إجراء رفع ملف الصورة المباشر وتحديث البيانات</th>
                    </tr>
                </thead>
                <tbody>
                    {# ترتيب الحسابات عددياً بشكل صحيح 1، 2، 3...60 #}
                    {% for acc_id in accounts.keys()|map('int')|sort %}
                    {% set data = accounts[acc_id|string] %}
                    <tr>
                        <td><img src="{{ data.img_url }}" class="thumb" onerror="this.src='https://i.imgur.com/8N69F3R.png'"></td>
                        <td><code>#{{ acc_id }}</code></td>
                        <td><b>{{ data.title }}</b></td>
                        <td><b style="color:#00ff87;">{{ data.price }}</b></td>
                        <td>
                            <form method="POST" action="/update_account_full/{{ acc_id }}" enctype="multipart/form-data" class="file-input-wrapper">
                                <input type="text" name="u_title" value="{{ data.title }}" style="width: 180px;" placeholder="اسم وعنوان المنتج" required>
                                <input type="text" name="u_price" value="{{ data.price }}" style="width: 70px;" placeholder="السعر" required>
                                <input type="file" name="u_file" accept="image/*" style="width: 160px;">
                                <button type="submit" class="btn-update">⚡ رفع وحفظ</button>
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
    return render_template_string(STORE_FRONT_HTML, accounts=DB_ACCOUNTS)

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

@app.route('/update_config', methods=['POST'])
def update_config():
    if 'logged_in' not in session: return redirect(url_for('admin_panel'))
    for key in BOT_CONFIG.keys():
        if key in request.form:
            BOT_CONFIG[key] = request.form.get(key).strip()
    return redirect(url_for('admin_panel'))

@app.route('/update_account_full/<aid>', methods=['POST'])
def update_account_full(aid):
    if 'logged_in' not in session: return redirect(url_for('admin_panel'))
    if aid in DB_ACCOUNTS:
        DB_ACCOUNTS[aid]['title'] = request.form.get('u_title').strip()
        DB_ACCOUNTS[aid]['price'] = request.form.get('u_price').strip()
        
        # معالجة ورفع ملف الصورة مباشرة للمجلد الخاص بالحساب
        file = request.files.get('u_file')
        if file and file.filename != '':
            acc_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(aid))
            os.makedirs(acc_folder, exist_ok=True)
            
            # مسح الصور القديمة داخل المجلد لتوفير المساحة ومنع التداخل
            for f in os.listdir(acc_folder):
                try: os.remove(os.path.join(acc_folder, f))
                except: pass
                
            filename = secure_filename(file.filename)
            file_path = os.path.join(acc_folder, filename)
            file.save(file_path)
            
            # تحديث مسار الصورة المرفوعة داخل الكود
            DB_ACCOUNTS[aid]['img_url'] = f"/static/uploads/{aid}/{filename}"
            
        save_accounts()
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout(): 
    session.pop('logged_in', None)
    return redirect(url_for('admin_panel'))

def run_http_server(): 
    app.run(host='0.0.0.0', port=8080)

# 🤖 تشغيل البوت الأساسي
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("⚡ LTB Dashboard Engine Active. 1-60 Ordered With File Upload Feature!")

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN: bot.run(TOKEN)