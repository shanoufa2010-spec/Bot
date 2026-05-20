import discord
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
import os
import asyncio
import json
from threading import Thread
from flask import Flask, render_template_string, request, redirect, url_for, session

# 🌐 إعداد خادم الويب والموقع المتطور
app = Flask('')
app.secret_key = os.getenv("FLASK_SECRET", "LTB_SUPER_SECRET_KEY_9988")

# 🔒 قاعدة بيانات الإعدادات الشاملة (تمت إعادة الحقول كاملة بناءً على طلبك)
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

# 💾 نظام الحفظ الذكي والمستمر للحسابات والطلبات
ACCOUNTS_FILE = "accounts.json"
TRANSACTIONS_FILE = "transactions.json"
DB_ACCOUNTS = {}
DB_TRANSACTIONS = []

def load_data():
    global DB_ACCOUNTS, DB_TRANSACTIONS
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f: DB_ACCOUNTS = json.load(f)
        except: DB_ACCOUNTS = {}
    else:
        DB_ACCOUNTS = {
            "45": {"id": "45", "title": "حساب ستيم بريميوم - قراند V", "img_url": "https://i.imgur.com/example.png", "price": "5 USDT"},
            "10": {"id": "10", "title": "حساب بوبجي ليفيل 70 مشحون", "img_url": "https://i.imgur.com/example2.png", "price": "12 USDT"}
        }
        save_accounts()
        
    if os.path.exists(TRANSACTIONS_FILE):
        try:
            with open(TRANSACTIONS_FILE, "r", encoding="utf-8") as f: DB_TRANSACTIONS = json.load(f)
        except: DB_TRANSACTIONS = []

def save_accounts():
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(DB_ACCOUNTS, f, ensure_ascii=False, indent=4)

def save_transactions():
    with open(TRANSACTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(DB_TRANSACTIONS, f, ensure_ascii=False, indent=4)

load_data()
active_tickets = {}

# 📂 القوالب البرمجية للوحة التحكم المقسمة والمنظمة بشكل احترافي
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>LTB Dashboard - لوحة الإدارة</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #0f0c1b; color: #f2f1f5; margin: 0; padding: 0; display: flex; }
        .sidebar { width: 280px; background: #17122b; height: 100vh; position: fixed; padding: 20px; box-sizing: border-box; border-left: 1px solid #2c254a; }
        .sidebar h2 { color: #5865F2; text-align: center; margin-bottom: 30px; font-size: 22px; }
        .sidebar a { display: block; padding: 12px; color: #a2a0b6; text-decoration: none; border-radius: 6px; margin-bottom: 12px; font-weight: 500; transition: 0.2s; }
        .sidebar a:hover { background: #231b3e; color: #fff; }
        .sidebar a.active { background: #5865F2; color: #fff; border-right: 4px solid #fff; }
        .main-content { margin-right: 280px; padding: 40px; width: 100%; box-sizing: border-box; min-height: 100vh; }
        .card { background: #17122b; border-radius: 8px; padding: 25px; margin-bottom: 25px; border: 1px solid #2c254a; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .card h3 { margin-top: 0; color: #5865F2; border-bottom: 1px solid #2c254a; padding-bottom: 10px; font-size: 18px; }
        .form-group { display: flex; flex-direction: column; margin-bottom: 15px; }
        .form-row { display: flex; gap: 20px; margin-bottom: 15px; }
        .form-row .form-group { flex: 1; }
        label { font-size: 14px; color: #a2a0b6; margin-bottom: 8px; font-weight: bold; }
        input[type="text"], input[type="password"], select { padding: 12px; background: #0f0c1b; border: 1px solid #2c254a; color: #fff; border-radius: 6px; font-size: 14px; }
        input:focus { border-color: #5865F2; outline: none; }
        .btn-save { background: #43b581; color: white; border: none; padding: 14px; font-weight: bold; border-radius: 6px; cursor: pointer; width: 100%; font-size: 16px; transition: 0.2s; }
        .btn-save:hover { background: #3ca374; }
        .btn-danger { background: #ed4245; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-size: 13px; font-weight: bold; }
        .acc-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .acc-table th, .acc-table td { padding: 14px; text-align: right; border-bottom: 1px solid #2c254a; }
        .acc-table th { color: #5865F2; font-weight: bold; }
        .logout { background: #ed4245; color: white; text-align: center; padding: 12px; text-decoration: none; border-radius: 6px; display: block; margin-top: 40px; font-weight: bold; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .badge-success { background: #43b581; color: white; }
        .badge-pending { background: #faa61a; color: white; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>⚙️ لوحة تحكم LTB</h2>
        <a href="/admin_panel_ltb_7392_x8q" class="{% if active_tab == 'settings' %}active{% endif %}">🎛️ الإعدادات العامة والرتب</a>
        <a href="/admin_panel_ltb_7392_x8q/accounts" class="{% if active_tab == 'accounts' %}active{% endif %}">📦 إدارة مخزن الحسابات</a>
        <a href="/admin_panel_ltb_7392_x8q/orders" class="{% if active_tab == 'orders' %}active{% endif %}">🧾 سجل الطلبات والتذاكر</a>
        <a href="/logout" class="logout">🚪 تسجيل الخروج الآمن</a>
    </div>
    <div class="main-content">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

STORE_FRONT_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>LTB Store - تصفح الحسابات المتوفرة</title>
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

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>🔒 بوابة الإدارة السرية</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f0c1b; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: #17122b; padding: 40px; border-radius: 12px; box-shadow: 0 8px 25px rgba(0,0,0,0.6); width: 100%; max-width: 400px; text-align: center; border: 1px solid #2c254a; }
        h2 { color: #5865F2; margin-bottom: 25px; }
        .input-group { margin-bottom: 20px; text-align: right; }
        label { display: block; margin-bottom: 8px; color: #a2a0b6; font-size: 14px; }
        input { width: 100%; padding: 12px; background: #0f0c1b; border: 1px solid #2c254a; color: #fff; border-radius: 6px; box-sizing: border-box; }
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
    return render_template_string(STORE_FRONT_HTML, accounts=DB_ACCOUNTS)

# 🎛️ الصفحة الأولى: الإعدادات العامة ورتب الأوامر كاملة
@app.route('/admin_panel_ltb_7392_x8q')
def admin_settings():
    if 'logged_in' not in session: return render_template_string(LOGIN_HTML)
    SETTINGS_CONTENT = """
    {% extends "base" %}
    {% block content %}
    <h2>🎛️ الإعدادات العامة وتخصيص رتب الأوامر</h2>
    <form method="POST" action="/save_settings">
        <div class="card">
            <h3>🪙 عناوين محافظ الدفع</h3>
            <div class="form-group"><label>محفظة USDT (BEP20):</label><input type="text" name="wallet_bep20" value="{{ config.wallet_bep20 }}"></div>
            <div class="form-group"><label>محفظة USDT (TRC20):</label><input type="text" name="wallet_trc20" value="{{ config.wallet_trc20 }}"></div>
        </div>
        
        <div class="card">
            <h3>🛠️ قنوات النظام المعتمدة (IDs)</h3>
            <div class="form-row">
                <div class="form-group"><label>ID روم اللوج والتدقيق (Log Channel):</label><input type="text" name="log_channel_id" value="{{ config.log_channel_id }}"></div>
                <div class="form-group"><label>ID روم الترحيب:</label><input type="text" name="welcome_channel_id" value="{{ config.welcome_channel_id }}"></div>
                <div class="form-group"><label>ID روم التقييمات والمراجعات:</label><input type="text" name="reviews_channel_id" value="{{ config.reviews_channel_id }}"></div>
            </div>
        </div>

        <div class="card">
            <h3>⚔️ تخصيص رتب الأوامر وصلاحيات البوت (افصل بين الرتب بفاصلة ,)</h3>
            <div class="form-group"><label>رتب إنشاء واجهة المتجر الرئيسية (!setup):</label><input type="text" name="perm_setup_cmd" value="{{ config.perm_setup_cmd }}"></div>
            <div class="form-group"><label>رتب مسح وتنظيف الغرف (!clear):</label><input type="text" name="perm_clear_cmd" value="{{ config.perm_clear_cmd }}"></div>
            <div class="form-group"><label>رتب أزرار التحكم بالتذاكر (الموافقة والتسليم التلقائي):</label><input type="text" name="perm_approve_action" value="{{ config.perm_approve_action }}"></div>
            <div class="form-group"><label>رتب إغلاق وأرشفة تذاكر المشترين:</label><input type="text" name="perm_close_ticket" value="{{ config.perm_close_ticket }}"></div>
        </div>
        <button type="submit" class="btn-save">💾 حفظ التغييرات وتحديث البوت فوراً</button>
    </form>
    {% endblock %}
    """
    return render_template_string(BASE_LAYOUT + SETTINGS_CONTENT, active_tab='settings', config=BOT_CONFIG)

# 📦 الصفحة الثانية: إدارة مخزن الحسابات (إضافة وحذف)
@app.route('/admin_panel_ltb_7392_x8q/accounts')
def admin_accounts():
    if 'logged_in' not in session: return redirect(url_for('admin_settings'))
    ACCOUNTS_CONTENT = """
    {% extends "base" %}
    {% block content %}
    <h2>📦 إدارة مخزن كروت الحسابات (محفوظة دائماً)</h2>
    <div class="card">
        <h3>➕ إضافة كارت حساب جديد للمتجر العام</h3>
        <form method="POST" action="/add_account">
            <div class="form-row">
                <div class="form-group"><label>رقم الحساب (ID):</label><input type="text" name="acc_id" placeholder="مثال: 45" required></div>
                <div class="form-group"><label>وصف الحساب وعنوانه:</label><input type="text" name="acc_title" placeholder="حساب ستيم، ليفيل.." required></div>
                <div class="form-group"><label>السعر المعروض:</label><input type="text" name="acc_price" placeholder="مثال: 10 USDT" required></div>
                <div class="form-group"><label>رابط الصورة المباشر:</label><input type="text" name="acc_img" placeholder="https://..." required></div>
            </div>
            <button type="submit" class="btn-save" style="background:#5865F2;">➕ إضافة الحساب في الكتالوج</button>
        </form>
    </div>

    <div class="card">
        <h3>📋 الحسابات المعروضة حالياً</h3>
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
                    <td><a href="/delete_account/{{ acc_id }}" class="btn-danger">❌ حذف الحساب</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endblock %}
    """
    return render_template_string(BASE_LAYOUT + ACCOUNTS_CONTENT, active_tab='accounts', accounts=DB_ACCOUNTS)

# 🧾 الصفحة الثالثة: سجل ومراقبة الطلبات المباشرة والتذاكر
@app.route('/admin_panel_ltb_7392_x8q/orders')
def admin_orders():
    if 'logged_in' not in session: return redirect(url_for('admin_settings'))
    ORDERS_CONTENT = """
    {% extends "base" %}
    {% block content %}
    <h2>🧾 سجل مراقبة عمليات الشراء والطلبات</h2>
    <div class="card">
        <h3>📋 طلبات الشراء الواردة من الديسكورد</h3>
        <table class="acc-table">
            <thead>
                <tr><th>المشتري</th><th>رقم الحساب المطلوب</th><th>الحالة</th></tr>
            </thead>
            <tbody>
                {% for order in transactions %}
                <tr>
                    <td><span style="color:#5865F2;">@{{ order.username }}</span></td>
                    <td><code>#{{ order.account_id }}</code></td>
                    <td>
                        {% if order.status == 'Completed' %}
                        <span class="badge badge-success">✅ تم التسليم والموافقة</span>
                        {% else %}
                        <span class="badge badge-pending">⏳ قيد الانتظار</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
                {% if not transactions %}
                <tr><td colspan="3" style="text-align:center; color:#a2a0b6;">لا توجد طلبات مسجلة حتى الآن.</td></tr>
                {% endif %}
            </tbody>
        </table>
    </div>
    {% endblock %}
    """
    return render_template_string(BASE_LAYOUT + ORDERS_CONTENT, active_tab='orders', transactions=DB_TRANSACTIONS)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('username') == BOT_CONFIG['web_user'] and request.form.get('password') == BOT_CONFIG['web_pass']:
        session['logged_in'] = True
        return redirect(url_for('admin_settings'))
    return render_template_string(LOGIN_HTML, error="❌ خطأ في بيانات الأدمن السرية!")

@app.route('/save_settings', methods=['POST'])
def save_settings():
    if 'logged_in' not in session: return redirect(url_for('public_store'))
    for key in BOT_CONFIG.keys():
        if key in request.form: BOT_CONFIG[key] = request.form.get(key)
    return redirect(url_for('admin_settings'))

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
    save_accounts()
    return redirect(url_for('admin_accounts'))

@app.route('/delete_account/<aid>')
def delete_account(aid):
    if 'logged_in' not in session: return redirect(url_for('public_store'))
    if aid in DB_ACCOUNTS: 
        del DB_ACCOUNTS[aid]
        save_accounts()
    return redirect(url_for('admin_accounts'))

@app.route('/logout')
def logout(): 
    session.pop('logged_in', None)
    return redirect(url_for('public_store'))

def run_http_server(): app.run(host='0.0.0.0', port=8080)


# 🤖 برمجة وهيكلة بوت الديسكورد الاحترافي
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
                embed.set_thumbnail(url=acc_data['img_url'])
                
            await interaction.response.send_message(embed=embed)
            
            DB_TRANSACTIONS.append({"username": interaction.user.name, "account_id": target_acc, "status": "Pending"})
            save_transactions()
            
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
            
            for t in DB_TRANSACTIONS:
                if t["account_id"] == self.account_num and t["status"] == "Pending":
                    t["status"] = "Completed"
                    break
            save_transactions()
            
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
    print("⚡ LTB Web Manager Engine Enabled successfully with Multi-Tab JSON Database!")

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN: bot.run(TOKEN)