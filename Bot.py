import discord
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
import os
import asyncio
import json
from threading import Thread
from flask import Flask, render_template_string, request, redirect, url_for, session
from werkzeug.utils import secure_filename

# 🌐 إعداد خادم الويب وإعدادات الملفات المرفوعة
app = Flask('')
app.secret_key = os.getenv("FLASK_SECRET", "LTB_SUPER_SECRET_KEY_9988")

UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 🔒 قاعدة بيانات الإعدادات الشاملة
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

# 💾 نظام حفظ الحسابات الذكي
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
    
    # 🛒 تم زراعة الحسابات هنا تلقائياً داخل الموقع مع أوصافها الخاصة بناءً على طلبك
    if not DB_ACCOUNTS:
        DB_ACCOUNTS = {
            "45": {
                "id": "45", 
                "title": "حساب ستيم ملوكي - قراند V نسخة كاملة (GTA V)", 
                "description": "حساب ستيم أصلي يحتوي على اللعبة الأسطورية Grand Theft Auto V بكامل طور القصة والأونلاين جاهز للتحميل واللعب فوراً! الحساب آمن ومستقر 100% ومثالي لمن يمتلك كارت شاشة مثل GTX 1650 أو 1660 للاستمتاع بأعلى سلاسة وأفضل فريمات.",
                "img_url": "https://i.imgur.com/8N69F3R.png",
                "price": "5 USDT"
            },
            "46": {
                "id": "46", 
                "title": "حساب ألعاب منوع - PixARK وألعاب بقاء ومغامرات", 
                "description": "لعشاق المغامرات والعوالم المفتوحة والبناء! حساب يحتوي على لعبة البقاء والأنميشن الشهيرة PixARK بالإضافة إلى باقة من الألعاب الخفيفة والممتعة جداً للعب الجماعي وتجربتها مع الأصدقاء. الحساب مستقر تماماً وبضمان كامل.",
                "img_url": "https://i.imgur.com/vXY8B9n.png",
                "price": "4 USDT"
            },
            "47": {
                "id": "47", 
                "title": "حساب ستيم التحدي والسرعة - Assetto Corsa وأكشن", 
                "description": "لعشاق محاكاة القيادة والسرعة الحقيقية والأكشن! الحساب يحتوي على لعبة سباق السيارات الشهيرة Assetto Corsa مع حزم ألعاب ممتازة ومفتوحة بالكامل، جاهزة للربط وبدء التنافس واللعب الجماعي فوراً وبأفضل أداء ممكن.",
                "img_url": "https://i.imgur.com/8N69F3R.png",
                "price": "6 USDT"
            }
        }
        save_accounts()

def save_accounts():
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(DB_ACCOUNTS, f, ensure_ascii=False, indent=4)

load_accounts()
active_tickets = {}

# 🛒 واجهة المتجر الاحترافية المحدثة لعرض الأوصاف الخاصة بكل حساب في الـ Modal
STORE_FRONT_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>متجر LTB الإعلاني المباشر 🛒</title>
    <style>
        :root { --main-color: #5865F2; --bg-dark: #09070f; --card-bg: #130f24; --text-muted: #a2a0b6; --success-color: #43b581; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg-dark); color: #fff; margin: 0; padding: 40px 20px; }
        .header { text-align: center; max-width: 800px; margin: 0 auto 50px auto; background: var(--card-bg); padding: 30px; border-radius: 16px; border: 1px solid #231b3e; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .header h1 { color: var(--main-color); margin-top: 0; font-size: 32px; }
        .info-box { background: #1a1433; padding: 15px; border-radius: 10px; margin-top: 20px; border-right: 4px solid var(--main-color); text-align: right; }
        .info-box h3 { margin: 0 0 8px 0; font-size: 16px; color: #fff; }
        .info-box p { margin: 0; font-size: 14px; color: var(--text-muted); line-height: 1.6; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 30px; max-width: 1200px; margin: 0 auto; }
        .card { background: var(--card-bg); border-radius: 14px; border: 1px solid #231b3e; overflow: hidden; box-shadow: 0 8px 20px rgba(0,0,0,0.4); transition: all 0.3s ease; cursor: pointer; position: relative; }
        .card:hover { transform: translateY(-5px); border-color: var(--main-color); box-shadow: 0 12px 25px rgba(88, 101, 242, 0.2); }
        .card img { width: 100%; height: 190px; object-fit: cover; background: #0f0c1b; transition: 0.3s; }
        .card:hover img { transform: scale(1.02); }
        .card-body { padding: 20px; }
        .card-id { background: var(--main-color); color: #fff; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; position: absolute; top: 15px; right: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        .card-title { margin: 10px 0 15px 0; font-size: 18px; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .card-price { color: var(--success-color); font-weight: bold; font-size: 18px; margin-bottom: 15px; display: flex; align-items: center; gap: 5px; }
        .btn-view { display: block; text-align: center; background: #1c1635; color: var(--main-color); border: 1px solid var(--main-color); padding: 12px; border-radius: 8px; font-weight: bold; font-size: 14px; transition: 0.2s; }
        .card:hover .btn-view { background: var(--main-color); color: white; }
        
        /* النافذة المنبثقة للتفاصيل */
        .modal-overlay { display: none; position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.8); z-index: 1000; justify-content: center; align-items: center; backdrop-filter: blur(5px); }
        .modal-content { background: var(--card-bg); width: 90%; max-width: 600px; border-radius: 16px; border: 1px solid #2c254a; overflow: hidden; box-shadow: 0 15px 40px rgba(0,0,0,0.7); animation: fadeIn 0.3s ease; position: relative; }
        @keyframes fadeIn { from { transform: scale(0.9); opacity: 0; } to { transform: scale(1); opacity: 1; } }
        .modal-img { width: 100%; max-height: 300px; object-fit: cover; }
        .modal-body { padding: 25px; text-align: right; }
        .modal-close { position: absolute; top: 15px; left: 15px; background: #ed4245; color: white; border: none; width: 30px; height: 30px; border-radius: 5px; font-weight: bold; cursor: pointer; }
        .btn-buy-now { display: block; text-align: center; background: var(--success-color); color: white; padding: 14px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px; margin-top: 20px; box-shadow: 0 4px 15px rgba(67, 181, 129, 0.3); transition: 0.2s; }
        .btn-buy-now:hover { background: #3ca374; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛒 متجر LTB الإعلاني المباشر</h1>
        <div class="info-box">
            <h3>📌 نظام وطريقة التعامل الرسمية:</h3>
            <p>مرحباً بك في منصتنا! لإتمام عملية الشراء الفوري لأي حساب معروض هنا، يجب عليك **الانضمام إلى سيرفر الديسكورد الرسمي الخاص بنا**. نتعامل حصرياً عبر بوابات **الدفع بالعملات الرقمية المشفرة (Crypto - USDT)** أو عن طريق **نظام المقايضة والتبادل المعتمد** فقط لضمان أمان الطرفين والتسليم الفوري.</p>
        </div>
    </div>
    
    <div class="grid">
        {% for acc_id, data in accounts.items() %}
        <div class="card" onclick="openDetails('{{ acc_id }}', '{{ data.title }}', '{{ data.price }}', '{{ data.img_url }}', '{{ data.description|default('') }}')">
            <span class="card-id">#{{ acc_id }}</span>
            <img src="{{ data.img_url }}" alt="Account Image">
            <div class="card-body">
                <div class="card-title">{{ data.title }}</div>
                <div class="card-price">🪙 {{ data.price }}</div>
                <div class="btn-view">👀 عرض التفاصيل الكاملة</div>
            </div>
        </div>
        {% endfor %}
    </div>

    <div id="detailsModal" class="modal-overlay" onclick="closeDetails(event)">
        <div class="modal-content" onclick="event.stopPropagation()">
            <button class="modal-close" onclick="closeDetails(null)">X</button>
            <img id="m_img" src="" class="modal-img" alt="">
            <div class="modal-body">
                <h2 id="m_title" style="margin-top:0; color: var(--main-color);"></h2>
                <h3 id="m_price" style="color: var(--success-color);"></h3>
                
                <div style="background: #1a1433; padding: 15px; border-radius: 8px; border-right: 3px solid var(--main-color); margin-bottom: 15px;">
                    <strong style="color: #fff; display: block; margin-bottom: 5px;">📝 وصف ومحتويات الحساب:</strong>
                    <p id="m_desc" style="color: var(--text-muted); font-size: 14px; margin: 0; line-height: 1.6;"></p>
                </div>

                <p style="color: var(--text-muted); font-size: 13px;">لشراء هذا الحساب فوراً، يرجى الضغط على زر الشراء أدناه للانتقال إلى سيرفر الديسكورد، ثم افتح تذكرة برقم الحساب (#<span id="m_id"></span>) وسيتم تسليمك البيانات مباشرة.</p>
                <a href="{{ server_link }}" target="_blank" class="btn-buy-now">🪙 الانتقال للسيرفر للشراء والتعامل المباشر</a>
            </div>
        </div>
    </div>

    <script>
        function openDetails(id, title, price, img, desc) {
            document.getElementById('m_id').innerText = id;
            document.getElementById('m_title').innerText = title;
            document.getElementById('m_price').innerText = "السعر الحالي: " + price;
            document.getElementById('m_img').src = img;
            document.getElementById('m_desc').innerText = desc ? desc : "لا يوجد وصف إضافي متوفر حالياً لهذا الحساب.";
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

# ⚙️ لوحة التحكم الكاملة
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>LTB Dashboard - لوحة الإدارة الشاملة</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #09070f; color: #f2f1f5; margin: 0; padding: 40px; }
        .container { max-width: 1100px; margin: 0 auto; }
        .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 2px solid #2c254a; padding-bottom: 20px; }
        h2 { color: #5865F2; margin: 0; }
        .logout-btn { background: #ed4245; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: bold; }
        .card { background: #130f24; border-radius: 12px; padding: 25px; margin-bottom: 35px; border: 1px solid #231b3e; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .card h3 { margin-top: 0; color: #5865F2; border-bottom: 1px solid #231b3e; padding-bottom: 10px; font-size: 18px; }
        .form-group { display: flex; flex-direction: column; margin-bottom: 15px; }
        .form-row { display: flex; gap: 20px; margin-bottom: 15px; flex-wrap: wrap; }
        .form-row .form-group { flex: 1; min-width: 200px; }
        label { font-size: 14px; color: #a2a0b6; margin-bottom: 8px; font-weight: bold; }
        input[type="text"], input[type="file"], textarea { padding: 12px; background: #09070f; border: 1px solid #231b3e; color: #fff; border-radius: 6px; font-size: 14px; box-sizing: border-box; font-family: inherit; }
        input[type="file"] { background: #1c1635; cursor: pointer; }
        textarea { resize: vertical; min-height: 80px; }
        .btn-save { background: #43b581; color: white; border: none; padding: 14px; font-weight: bold; border-radius: 6px; cursor: pointer; width: 100%; font-size: 16px; }
        .btn-add { background: #5865F2; color: white; border: none; padding: 12px 24px; font-weight: bold; border-radius: 6px; cursor: pointer; }
        .btn-danger { background: #ed4245; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-size: 13px; font-weight: bold; }
        .acc-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .acc-table th, .acc-table td { padding: 14px; text-align: right; border-bottom: 1px solid #231b3e; }
        .acc-table th { color: #5865F2; font-weight: bold; }
        .thumb { width: 50px; height: 50px; object-fit: cover; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h2>⚙️ لوحة تحكم وإدارة بوت ومتجر LTB الشاملة</h2>
            <a href="/logout" class="logout-btn">🚪 تسجيل الخروج الآمن</a>
        </div>

        <div class="card">
            <h3>📦 إضافة كارت حساب جديد للمتجر (رفع صورة مباشر)</h3>
            <form method="POST" action="/add_account" enctype="multipart/form-data">
                <div class="form-row">
                    <div class="form-group"><label>رقم الحساب (ID):</label><input type="text" name="acc_id" placeholder="مثال: 45" required></div>
                    <div class="form-group"><label>عنوان الحساب:</label><input type="text" name="acc_title" placeholder="حساب ستيم، ليفيل.." required></div>
                    <div class="form-group"><label>السعر المعروض:</label><input type="text" name="acc_price" placeholder="مثال: 10 USDT" required></div>
                    <div class="form-group"><label>قم برفع صورة الحساب مباشرة:</label><input type="file" name="acc_file" accept="image/*" required></div>
                </div>
                <div class="form-group">
                    <label>وصف ومحتويات الحساب بالتفصيل (سيظهر داخل النافذة المنبثقة):</label>
                    <textarea name="acc_desc" placeholder="اكتب تفاصيل الألعاب، الليفل، وأهم الميزات هنا..." required></textarea>
                </div>
                <button type="submit" class="btn-add">➕ إضافة الحساب فوراً في الكتالوج</button>
            </form>
            
            <h3 style="margin-top: 30px;">📋 الحسابات المعروضة حالياً في الموقع</h3>
            <table class="acc-table">
                <thead>
                    <tr><th>الصورة</th><th>رقم الحساب</th><th>العنوان</th><th>السعر</th><th>الإجراءات</th></tr>
                </thead>
                <tbody>
                    {% for acc_id, data in accounts.items() %}
                    <tr>
                        <td><img src="{{ data.img_url }}" class="thumb"></td>
                        <td><code>#{{ acc_id }}</code></td>
                        <td>{{ data.title }}</td>
                        <td><b style="color:#43b581;">{{ data.price }}</b></td>
                        <td><a href="/delete_account/{{ acc_id }}" class="btn-danger">❌ حذف الحساب</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <form method="POST" action="/save_settings">
            <div class="card">
                <h3>🪙 عناوين محافظ الدفع</h3>
                <div class="form-group" style="margin-bottom: 15px;"><label>محفظة USDT (BEP20):</label><input type="text" name="wallet_bep20" value="{{ config.wallet_bep20 }}"></div>
                <div class="form-group"><label>محفظة USDT (TRC20):</label><input type="text" name="wallet_trc20" value="{{ config.wallet_trc20 }}"></div>
            </div>
            
            <div class="card">
                <h3>🛠️ قنوات النظام المعتمدة في السيرفر (IDs)</h3>
                <div class="form-row">
                    <div class="form-group"><label>ID روم اللوج والتدقيق (Log Channel):</label><input type="text" name="log_channel_id" value="{{ config.log_channel_id }}"></div>
                    <div class="form-group"><label>ID روم الترحيب:</label><input type="text" name="welcome_channel_id" value="{{ config.welcome_channel_id }}"></div>
                    <div class="form-group"><label>ID روم التقييمات والمراجعات:</label><input type="text" name="reviews_channel_id" value="{{ config.reviews_channel_id }}"></div>
                </div>
            </div>

            <div class="card">
                <h3>⚔️ تخصيص رتب الأوامر وصلاحيات البوت المعتمدة</h3>
                <div class="form-group" style="margin-bottom: 15px;"><label>رتب إنشاء واجهة المتجر الرئيسية (!setup):</label><input type="text" name="perm_setup_cmd" value="{{ config.perm_setup_cmd }}"></div>
                <div class="form-group" style="margin-bottom: 15px;"><label>رتب مسح وتنظيف الغرف (!clear):</label><input type="text" name="perm_clear_cmd" value="{{ config.perm_clear_cmd }}"></div>
                <div class="form-group" style="margin-bottom: 15px;"><label>رتب أزرار التحكم بالتذاكر (الموافقة والتسليم التلقائي):</label><input type="text" name="perm_approve_action" value="{{ config.perm_approve_action }}"></div>
                <div class="form-group"><label>رتب إغلاق وأرشفة تذاكر المشترين:</label><input type="text" name="perm_close_ticket" value="{{ config.perm_close_ticket }}"></div>
            </div>

            <button type="submit" class="btn-save">💾 حفظ وتحديث كافة الإعدادات وتطبيقها على البوت</button>
        </form>
    </div>
</body>
</html>
"""

# بوابة تسجيل الدخول المحمية
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>🔒 بوابة الإدارة السرية</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #09070f; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: #130f24; padding: 40px; border-radius: 12px; box-shadow: 0 8px 25px rgba(0,0,0,0.6); width: 100%; max-width: 400px; text-align: center; border: 1px solid #231b3e; }
        h2 { color: #5865F2; margin-bottom: 25px; }
        .input-group { margin-bottom: 20px; text-align: right; }
        label { display: block; margin-bottom: 8px; color: #a2a0b6; font-size: 14px; }
        input { width: 100%; padding: 12px; background: #09070f; border: 1px solid #231b3e; color: #fff; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #5865F2; border: none; color: white; font-size: 16px; font-weight: bold; border-radius: 6px; cursor: pointer; }
        .error { color: #ed4245; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>🔒 لوحة الإدارة المحمية</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST" action="/login">
            <div class="input-group"><label>اسم المستخدم السري:</label><input type="text" name="username" required></div>
            <div class="input-group"><label>كلمة المرور:</label><input type="password" name="password" required></div>
            <button type="submit">تسجيل الدخول الآمن</button>
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
    return render_template_string(LOGIN_HTML, error="❌ خطأ في بيانات الأدمن السرية!")

@app.route('/save_settings', methods=['POST'])
def save_settings():
    if 'logged_in' not in session: return redirect(url_for('public_store'))
    for key in BOT_CONFIG.keys():
        if key in request.form: BOT_CONFIG[key] = request.form.get(key)
    return redirect(url_for('admin_panel'))

@app.route('/add_account', methods=['POST'])
def add_account():
    if 'logged_in' not in session: return redirect(url_for('public_store'))
    aid = request.form.get('acc_id').strip()
    
    file = request.files.get('acc_file')
    if file and file.filename != '':
        filename = secure_filename(f"{aid}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        img_url = f"/static/uploads/{filename}"
    else:
        img_url = "https://i.imgur.com/8N69F3R.png"

    DB_ACCOUNTS[aid] = {
        "id": aid, 
        "title": request.form.get('acc_title'), 
        "description": request.form.get('acc_desc'),
        "price": request.form.get('acc_price'), 
        "img_url": img_url
    }
    save_accounts()
    return redirect(url_for('admin_panel'))

@app.route('/delete_account/<aid>')
def delete_account(aid):
    if 'logged_in' not in session: return redirect(url_for('public_store'))
    if aid in DB_ACCOUNTS: 
        del DB_ACCOUNTS[aid]
        save_accounts()
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout(): 
    session.pop('logged_in', None)
    return redirect(url_for('public_store'))

def run_http_server(): app.run(host='0.0.0.0', port=8080)


# 🤖 برمجة وهيكلة بوت الديسكورد
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

# 🌌 حدث الترحيب بنظام الإيمبد الاحترافي الجديد داخل السيرفر
@bot.event
async def on_member_join(member):
    try:
        welcome_channel = bot.get_channel(int(BOT_CONFIG["welcome_channel_id"]))
        if welcome_channel:
            embed = discord.Embed(
                title="✨ عضو جديد انضم إلى عائلة LTB!",
                description=f"أهلاً بك ومرحباً {member.mention} في سيرفرنا الرسمي لبيع ومقايضة الحسابات عبر الكريبتو! 🔥\n\n"
                            f"📌 **لتصفح الحسابات المتوفرة وأسعارها:** استخدم الأمر `!send_shop` أو تفضل بزيارة موقعنا المباشر.\n"
                            f"📌 **لبدء عملية شراء أو مقايضة:** توجه لغرفة فتح التذاكر وافتح تذكرتك الفورية.",
                color=discord.Color.purple()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"أنت العضو رقم {member.guild.member_count}", icon_url=member.guild.icon.url if member.guild.icon else None)
            await welcome_channel.send(embed=embed)
    except Exception as e:
        print(f"Error in welcome embed: {e}")

class WebsiteRedirectView(View):
    def __init__(self, url):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="🌐 تصفح الحسابات المتوفرة بالموقع", url=url, style=discord.ButtonStyle.link))

class PurchaseModal(Modal):
    def __init__(self, lang="ar"):
        super().__init__(title="طلب شراء حساب / Purchase Account")
        self.lang = lang
        self.acc_input = TextInput(label="أدخل رقم الحساب المطلوب / Account ID" if lang=="ar" else "Enter Account ID", placeholder="مثال: 45", min_length=1, max_length=10, required=True)
        self.add_item(self.acc_input)

    async def on_submit(self, interaction: discord.Interaction):
        target_acc = self.acc_input.value.strip()
        
        if target_acc in DB_ACCOUNTS:
            acc_data = DB_ACCOUNTS[target_acc]
            if self.lang == "ar":
                title = f"🪙 الفاتورة المعتمدة للحساب رقم ({target_acc})"
                desc = f"📦 **نوع الحساب:** {acc_data['title']}\n💰 **السعر:** {acc_data['price']}\n\n📌 **شبكة Smart Chain (BEP20):**\n`{BOT_CONFIG['wallet_bep20']}`\n\n📌 **شبكة Tron (TRC20):**\n`{BOT_CONFIG['wallet_trc20']}`\n\n📸 **الرجاء إرسال صورة إثبات التحويل (وصل الدفع) في هذا الشات فوراً ليتم تدقيقها من الإدارة.**"
            else:
                title = f"🪙 Invoice for Account ID ({target_acc})"
                desc = f"📦 **Product:** {acc_data['title']}\n💰 **Price:** {acc_data['price']}\n\n📌 **BNB Smart Chain (BEP20):**\n`{BOT_CONFIG['wallet_bep20']}`\n\n📌 **Tron Network (TRC20):**\n`{BOT_CONFIG['wallet_trc20']}`\n\n📸 **Please send the payment confirmation screenshot directly in this chat.**"
            
            embed = discord.Embed(title=title, description=desc, color=discord.Color.gold())
            if not acc_data['img_url'].startswith('https://i.imgur.com/example'):
                embed.set_image(url=acc_data['img_url'])
                
            await interaction.response.send_message(embed=embed)
            
            try:
                log_channel = bot.get_channel(int(BOT_CONFIG["log_channel_id"]))
                if log_channel:
                    embed_p = discord.Embed(title="⏳ طلب شراء جديد قيد الانتظار", description=f"المشتري: {interaction.user.mention}\nالحساب المطلوب: `{target_acc}` - {acc_data['title']}\nالروم: {interaction.channel.mention}", color=discord.Color.orange())
                    l_msg = await log_channel.send(embed=embed_p, view=AdminApprovalView(buyer_id=interaction.user.id, account_num=target_acc, ticket_channel_id=interaction.channel.id, lang=self.lang))
                    active_tickets[interaction.channel.id] = {"log_msg_id": l_msg.id, "account_id": target_acc}
            except: pass
        else:
            await interaction.response.send_message("❌ هذا الرقم غير موجود في قائمة المتجر حالياً، يرجى التأكد من الرقم الصحيح من الموقع.", ephemeral=True)

class AdminApprovalView(View):
    def __init__(self, buyer_id, account_num, ticket_channel_id, lang="ar"):
        super().__init__(timeout=None)
        self.buyer_id = buyer_id; self.account_num = account_num; self.ticket_channel_id = ticket_channel_id; self.lang = lang

    @discord.ui.button(label="✅ موافقة وتسليم / Approve", style=discord.ButtonStyle.success, custom_id="approve_sale_btn")
    async def approve_sale(self, interaction: discord.Interaction, button: Button):
        if has_dashboard_permission(interaction.user, "perm_approve_action"):
            await interaction.response.defer()
            ticket_channel = bot.get_channel(self.ticket_channel_id)
            
            embed_log = discord.Embed(title="✅ تقرير بيع ناجح ومعتمد من الموقع", color=discord.Color.green())
            embed_log.add_field(name="👤 المشتري", value=f"<@{self.buyer_id}>", inline=True)
            embed_log.add_field(name="📦 رقم الحساب المعين", value=f"`{self.account_num}`", inline=True)
            embed_log.add_field(name="🛠️ المشرف المسؤول", value=interaction.user.mention, inline=False)
            await interaction.message.edit(embed=embed_log, view=None)

            if ticket_channel:
                title = "🎉 تم تأكيد الدفع بنجاح!" if self.lang == "ar" else "🎉 Payment Confirmed!"
                msg = f"مرحباً <@{self.buyer_id}>، تم التحقق من تحويل الكريبتو الخاص بك بنجاح. سيتم تسليمك البيانات المباشرة الآن." if self.lang == "ar" else f"Hello <@{self.buyer_id}>, your payment has been verified. Check your credentials right now."
                await ticket_channel.send(embed=discord.Embed(title=title, description=msg, color=discord.Color.green()))
        else:
            await interaction.response.send_message("❌ غير مصرح لك بالموافقة!", ephemeral=True)

class TicketDeleteView(View):
    def __init__(self, lang="ar"): super().__init__(timeout=None); self.lang = lang
    @discord.ui.button(label="🗑️ حذف التذكرة / Delete", style=discord.ButtonStyle.danger, custom_id="delete_ticket_btn")
    async def delete_ticket(self, interaction: discord.Interaction, button: Button):
        if has_dashboard_permission(interaction.user, "perm_close_ticket"):
            await interaction.response.send_message("⚠️ جاري مسح الغرفة بالكامل...")
            await asyncio.sleep(5); await interaction.channel.delete()

class TicketControlView(View):
    def __init__(self, lang="ar"):
        super().__init__(timeout=None); self.lang = lang
        self.children[0].label = "💰 إرسال طلب شراء" if lang == "ar" else "💰 Create Purchase Order"
        self.children[1].label = "🔒 إغلاق التذكرة" if lang == "ar" else "🔒 Close Ticket"

    @discord.ui.button(label="💰 Buy", style=discord.ButtonStyle.success, custom_id="buy_acc_btn")
    async def buy_account(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(PurchaseModal(lang=self.lang))

    @discord.ui.button(label="🔒 Close", style=discord.ButtonStyle.secondary, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if has_dashboard_permission(interaction.user, "perm_close_ticket"):
            await interaction.response.send_message("🔒 Closing ticket...")
            try: await interaction.channel.edit(name=f"🔒-مغلقة-{interaction.channel.name}")
            except: pass
            await interaction.channel.send(view=TicketDeleteView(lang=self.lang))

class StoreDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🇩🇿 تصفح الحسابات والدفع بالكريبتو", value="ar_crypto", emoji="🛒"),
            discord.SelectOption(label="🇬🇧 Global Client - Buy via Crypto", value="en_crypto", emoji="🪙")
        ]
        super().__init__(placeholder="🔽 حدد لغة واجهة تذكرتك / Select language...", min_values=1, max_values=1, options=options, custom_id="store_select_menu")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild; member = interaction.user; choice = self.values[0]
        lang = "ar" if choice.startswith("ar_") else "en"
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), member: discord.PermissionOverwrite(read_messages=True, send_messages=True), guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        
        ticket_channel = await guild.create_text_channel(name=f"شراء-{member.name}" if lang=="ar" else f"buy-{member.name}", category=interaction.channel.category, overwrites=overwrites)
        await interaction.response.send_message(f"✅ Created: {ticket_channel.mention}", ephemeral=True)
        
        embed = discord.Embed(color=discord.Color.red())
        if lang == "ar":
            embed.title = "🎯 متجر LTB الفوري"
            embed.description = f"مرحباً {member.mention}، اضغط على الزر الأخضر بالأسفل لتحديد رقم الحساب الذي ترغب بشراءه عبر بوابات الكريبتو المعتمدة."
        else:
            embed.title = "🎯 LTB Fast Desk"
            embed.description = f"Welcome {member.mention}, click the green button below to provide the Account ID and proceed to checkout."
            
        await ticket_channel.send(embed=embed, view=TicketControlView(lang=lang))

class MainStoreView(View):
    def __init__(self): super().__init__(timeout=None); self.add_item(StoreDropdown())

@bot.event
async def on_message(message):
    if message.author.bot: return
    channel_name = message.channel.name.lower()
    if any(p in channel_name for p in ["شراء", "buy"]):
        if message.attachments and message.channel.id in active_tickets:
            if message.attachments[0].filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                try:
                    log_channel = bot.get_channel(int(BOT_CONFIG["log_channel_id"]))
                    if log_channel:
                        log_msg = await log_channel.fetch_message(active_tickets[message.channel.id]["log_msg_id"])
                        emb = discord.Embed(title="⏳ تم تلقي وصل إثبات الدفع الفعلي من العميل!", color=discord.Color.blue())
                        emb.set_image(url=message.attachments[0].url)
                        await log_msg.edit(embed=emb)
                        await message.channel.send("✅ **تم رصد المرفق بنجاح وتم إرفاقه في اللوج لمراجعته من المسؤولين.**")
                except: pass
    await bot.process_commands(message)

@bot.command()
async def send_shop(ctx):
    if has_dashboard_permission(ctx.author, "perm_setup_cmd"):
        site_url = "https://bot-nmae.onrender.com/" 
        embed = discord.Embed(
            title="🌐 موقع متجر LTB الرسمي معروض هنا!",
            description="اضغط على الزر بالأسفل لتصفح الكتالوج الكامل للحسابات المتوفرة (أرقامها، مواصفاتها، وأسعارها) عبر متصفحك مباشرة بشكل سريع ومنظم! بعد ذلك افتح تذكرة الشراء واكتب رقم الحساب.",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed, view=WebsiteRedirectView(url=site_url))

@bot.command()
async def setup(ctx):
    if has_dashboard_permission(ctx.author, "perm_setup_cmd"):
        embed = discord.Embed(title="🛒 LTB Global Hub", description="اختر لغتك لبدء معاملة الشراء الفوري / Choose Language to Buy", color=discord.Color.red())
        await ctx.send(embed=embed, view=MainStoreView())

@bot.command()
async def clear(ctx, amount: int = 20):
    if has_dashboard_permission(ctx.author, "perm_clear_cmd"):
        await ctx.channel.purge(limit=amount + 1)

@bot.event
async def on_ready():
    bot.add_view(MainStoreView()); bot.add_view(TicketControlView()); bot.add_view(TicketDeleteView())
    print("⚡ LTB Web Manager Engine Enabled successfully with Unified Dashboard Style!")

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN: bot.run(TOKEN)