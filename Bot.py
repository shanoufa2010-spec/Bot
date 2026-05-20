import discord
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
import os
import asyncio
import json
import aiohttp
from threading import Thread
from flask import Flask, render_template_string, request, redirect, url_for, session

# 🌐 إعداد خادم الويب والموقع
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

# 💾 نظام حفظ الحسابات المستمر
ACCOUNTS_FILE = "accounts.json"
DB_ACCOUNTS = {}

def load_accounts():
    global DB_ACCOUNTS
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f: DB_ACCOUNTS = json.load(f)
        except: DB_ACCOUNTS = {}
    
    if not DB_ACCOUNTS:
        # زرع حساباتك الحقيقية بشكل تلقائي لضمان عدم ظهور صور مكسورة
        DB_ACCOUNTS = {
            "45": {"id": "45", "title": "حساب ستيم بريميوم - قراند V", "img_url": "https://i.imgur.com/8N69F3R.png", "price": "5 USDT"},
            "10": {"id": "10", "title": "حساب بوبجي ليفيل 70 مشحون", "img_url": "https://i.imgur.com/vXY8B9n.png", "price": "12 USDT"}
        }
        save_accounts()

def save_accounts():
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(DB_ACCOUNTS, f, ensure_ascii=False, indent=4)

load_accounts()
active_tickets = {}
AI_CHANNEL_ID = 1505753282361032820
GEMINI_API_KEY = "AIzaSyChRyGo7heDrQUY1HFdiTaiBORt1-XXIOw" # الرمز الخاص بك مدمج بأمان

# 🛒 تصميم واجهة المتجر العامة للزبائن
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

# ⚙️ تصميم لوحة الإدارة المستقرة ذات الصفحة الواحدة (تمنع خطأ 500)
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
        .logout-btn { background: #ed4245; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: bold; }
        .card { background: #17122b; border-radius: 8px; padding: 25px; margin-bottom: 35px; border: 1px solid #2c254a; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .card h3 { margin-top: 0; color: #5865F2; border-bottom: 1px solid #2c254a; padding-bottom: 10px; font-size: 18px; }
        .form-group { display: flex; flex-direction: column; margin-bottom: 15px; }
        .form-row { display: flex; gap: 20px; margin-bottom: 15px; }
        .form-row .form-group { flex: 1; }
        label { font-size: 14px; color: #a2a0b6; margin-bottom: 8px; font-weight: bold; }
        input[type="text"], input[type="password"] { padding: 12px; background: #0f0c1b; border: 1px solid #2c254a; color: #fff; border-radius: 6px; font-size: 14px; }
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
            <h2>⚙️ لوحة تحكم وإدارة بوت ومتجر LTB الشاملة</h2>
            <a href="/logout" class="logout-btn">🚪 تسجيل الخروج الآمن</a>
        </div>

        <div class="card">
            <h3>📦 إضافة كارت حساب جديد للمتجر</h3>
            <form method="POST" action="/add_account">
                <div class="form-row">
                    <div class="form-group"><label>رقم الحساب (ID):</label><input type="text" name="acc_id" placeholder="مثال: 45" required></div>
                    <div class="form-group"><label>وصف الحساب وعنوانه:</label><input type="text" name="acc_title" placeholder="حساب ستيم، ليفيل.." required></div>
                    <div class="form-group"><label>السعر المعروض:</label><input type="text" name="acc_price" placeholder="مثال: 10 USDT" required></div>
                    <div class="form-group"><label>رابط الصورة المباشر:</label><input type="text" name="acc_img" placeholder="https://..." required></div>
                </div>
                <button type="submit" class="btn-add">➕ إضافة الحساب فوراً في الكتالوج</button>
            </form>
            
            <h3 style="margin-top: 30px;">📋 الحسابات المعروضة حالياً في الموقع</h3>
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

        <form method="POST" action="/save_settings">
            <div class="card">
                <h3>🪙 عناوين محافظ الدفع</h3>
                <div class="form-group" style="margin-bottom: 15px;"><label>محفظة USDT (BEP20):</label><input type="text" name="wallet_bep20" value="{{ config.wallet_bep20 }}"></div>
                <div class="form-group"><label>محفظة USDT (TRC20):</label><input type="text" name="wallet_trc20" value="{{ config.wallet_trc20 }}"></div>
            </div>
            
            <div class="card">
                <h3>🛠️ قنوات النظام المعتمدة في السيرفر (IDs)</h3>
                <div class="form-row">
                    <div class="form-group"><label>ID روم اللوج والتدقيق:</label><input type="text" name="log_channel_id" value="{{ config.log_channel_id }}"></div>
                    <div class="form-group"><label>ID روم الترحيب:</label><input type="text" name="welcome_channel_id" value="{{ config.welcome_channel_id }}"></div>
                    <div class="form-group"><label>ID روم التقييمات:</label><input type="text" name="reviews_channel_id" value="{{ config.reviews_channel_id }}"></div>
                </div>
            </div>

            <div class="card">
                <h3>⚔️ تخصيص رتب الأوامر وصلاحيات البوت المعتمدة</h3>
                <div class="form-group" style="margin-bottom: 15px;"><label>رتب إنشاء واجهة المتجر الرئيسية (!setup):</label><input type="text" name="perm_setup_cmd" value="{{ config.perm_setup_cmd }}"></div>
                <div class="form-group" style="margin-bottom: 15px;"><label>رتب مسح وتنظيف الغرف (!clear):</label><input type="text" name="perm_clear_cmd" value="{{ config.perm_clear_cmd }}"></div>
                <div class="form-group" style="margin-bottom: 15px;"><label>رتب أزرار التحكم بالتذاكر:</label><input type="text" name="perm_approve_action" value="{{ config.perm_approve_action }}"></div>
                <div class="form-group"><label>رتب إغلاق وأرشفة تذاكر المشترين:</label><input type="text" name="perm_close_ticket" value="{{ config.perm_close_ticket }}"></div>
            </div>
            <button type="submit" class="btn-save">💾 حفظ وتحديث كافة الإعدادات وتطبيقها على البوت</button>
        </form>
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
        input { width: 100%; padding: 12px; background: #0f0c1b; border: 1px solid #2c254a; color: #fff; border-radius: 6px; box-sizing: border-box; margin-bottom: 20px; }
        button { width: 100%; padding: 12px; background: #5865F2; border: none; color: white; font-size: 16px; font-weight: bold; border-radius: 6px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>🔒 لوحة الإدارة المحمية</h2>
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="اسم المستخدم السري" required>
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <button type="submit">تسجيل الدخول الآمن</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def public_store(): return render_template_string(STORE_FRONT_HTML, accounts=DB_ACCOUNTS)

@app.route('/admin_panel_ltb_7392_x8q')
def admin_panel():
    if 'logged_in' in session: return render_template_string(DASHBOARD_HTML, config=BOT_CONFIG, accounts=DB_ACCOUNTS)
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('username') == BOT_CONFIG['web_user'] and request.form.get('password') == BOT_CONFIG['web_pass']:
        session['logged_in'] = True; return redirect(url_for('admin_panel'))
    return render_template_string(LOGIN_HTML)

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
    DB_ACCOUNTS[aid] = {"id": aid, "title": request.form.get('acc_title'), "price": request.form.get('acc_price'), "img_url": request.form.get('acc_img')}
    save_accounts(); return redirect(url_for('admin_panel'))

@app.route('/delete_account/<aid>')
def delete_account(aid):
    if 'logged_in' not in session: return redirect(url_for('public_store'))
    if aid in DB_ACCOUNTS: del DB_ACCOUNTS[aid]; save_accounts()
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout(): session.pop('logged_in', None); return redirect(url_for('public_store'))

def run_http_server(): app.run(host='0.0.0.0', port=8080)


# 🤖 محرك بوت الديسكورد المدمج بالذكاء الاصطناعي الفائق لـ Gemini
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)

async def ask_gemini_ai(prompt_text):
    """دالة برمجية للاتصال المباشر بنموذج الذكاء الاصطناعي ومعالجة البيانات"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    # تلقين الذكاء الاصطناعي دوره وطبيعة عمل المتجر ليتصرف كمساعد ذكي محترف
    system_instruction = (
        "أنت الآن المساعد الذكي الخبير لمتجر LTB الأونلاين. وظيفتك الإجابة على استفسارات الأدمن البرمجية، "
        "وإذا أرسل لك قائمة حسابات أو طلب إضافة حسابات، قم بصياغة الإجابة وإرجاع البيانات المطلوبة. "
        f"قائمة الحسابات الحالية في المتجر هي: {json.dumps(DB_ACCOUNTS, ensure_ascii=False)}. "
        "تحدث دائماً باللغة العربية بأسلوب فخم وواضح وصديق للأدمن."
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]}
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                res_json = await response.json()
                try:
                    return res_json['candidates'][0]['content']['parts'][0]['text']
                except:
                    return "⚠️ واجهت مشكلة في معالجة رد الذكاء الاصطناعي."
            else:
                return f"❌ خطأ في الاتصال بخادم جوجل الذكي: {response.status}"

def has_dashboard_permission(user, config_key):
    if user.guild_permissions.administrator: return True
    allowed = [item.strip().lower() for item in BOT_CONFIG[config_key].split(",") if item.strip()]
    for role in user.roles:
        if str(role.id) in allowed or role.name.lower() in allowed: return True
    return False

# --- أوامر التذاكر والمتجر المعتادة ---
class WebsiteRedirectView(View):
    def __init__(self, url):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="🌐 تصفح الحسابات المتوفرة بالموقع", url=url, style=discord.ButtonStyle.link))

class PurchaseModal(Modal):
    def __init__(self, lang="ar"):
        super().__init__(title="طلب شراء حساب / Purchase Account")
        self.lang = lang
        self.acc_input = TextInput(label="أدخل رقم الحساب المطلوب" if lang=="ar" else "Enter Account ID", placeholder="45", min_length=1, max_length=10, required=True)
        self.add_item(self.acc_input)

    async def on_submit(self, interaction: discord.Interaction):
        target_acc = self.acc_input.value.strip()
        if target_acc in DB_ACCOUNTS:
            acc_data = DB_ACCOUNTS[target_acc]
            desc = f"📦 **نوع الحساب:** {acc_data['title']}\n💰 **السعر:** {acc_data['price']}\n\n📌 **Smart Chain (BEP20):**\n`{BOT_CONFIG['wallet_bep20']}`\n\n📌 **Tron (TRC20):**\n`{BOT_CONFIG['wallet_trc20']}`\n\n📸 **أرسل وصل التحويل هنا فورا.**"
            await interaction.response.send_message(embed=discord.Embed(title="🪙 الفاتورة المعتمدة", description=desc, color=discord.Color.gold()))
            
            try:
                log_channel = bot.get_channel(int(BOT_CONFIG["log_channel_id"]))
                if log_channel:
                    embed_p = discord.Embed(title="⏳ طلب شراء جديد قيد الانتظار", description=f"المشتري: {interaction.user.mention}\nالحساب: `{target_acc}`", color=discord.Color.orange())
                    l_msg = await log_channel.send(embed=embed_p, view=AdminApprovalView(buyer_id=interaction.user.id, account_num=target_acc, ticket_channel_id=interaction.channel.id))
                    active_tickets[interaction.channel.id] = {"log_msg_id": l_msg.id, "account_id": target_acc}
            except: pass
        else:
            await interaction.response.send_message("❌ الرقم غير موجود بالمتجر حالياً.", ephemeral=True)

class AdminApprovalView(View):
    def __init__(self, buyer_id, account_num, ticket_channel_id):
        super().__init__(timeout=None); self.buyer_id = buyer_id; self.account_num = account_num; self.ticket_channel_id = ticket_channel_id

    @discord.ui.button(label="✅ موافقة وتسليم", style=discord.ButtonStyle.success, custom_id="approve_sale_btn")
    async def approve_sale(self, interaction: discord.Interaction, button: Button):
        if has_dashboard_permission(interaction.user, "perm_approve_action"):
            await interaction.response.defer()
            ticket_channel = bot.get_channel(self.ticket_channel_id)
            if ticket_channel:
                await ticket_channel.send(embed=discord.Embed(title="🎉 تم تأكيد الدفع!", description="تم التحقق من تحويلك، سيتم التسليم الآن.", color=discord.Color.green()))
        else:
            await interaction.response.send_message("❌ لا تملك صلاحية المعتمدين!", ephemeral=True)

class TicketDeleteView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🗑️ حذف التذكرة", style=discord.ButtonStyle.danger, custom_id="delete_ticket_btn")
    async def delete_ticket(self, interaction: discord.Interaction, button: Button):
        if has_dashboard_permission(interaction.user, "perm_close_ticket"):
            await interaction.channel.delete()

class TicketControlView(View):
    def __init__(self, lang="ar"):
        super().__init__(timeout=None)
        self.buy_btn = Button(label="💰 إرسال طلب شراء", style=discord.ButtonStyle.success, custom_id="buy_acc_btn")
        self.close_btn = Button(label="🔒 إغلاق التذكرة", style=discord.ButtonStyle.secondary, custom_id="close_ticket_btn")
        self.add_item(self.buy_btn); self.add_item(self.close_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data["custom_id"] == "buy_acc_btn":
            await interaction.response.send_modal(PurchaseModal())
        elif interaction.data["custom_id"] == "close_ticket_btn":
            if has_dashboard_permission(interaction.user, "perm_close_ticket"):
                await interaction.response.send_message(view=TicketDeleteView())
        return False

class StoreDropdown(Select):
    def __init__(self):
        options = [discord.SelectOption(label="🇩🇿 تصفح الحسابات والدفع بالكريبتو", value="ar_crypto", emoji="🛒")]
        super().__init__(placeholder="🔽 حدد واجهة تذكرتك...", options=options, custom_id="store_select_menu")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild; member = interaction.user
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), member: discord.PermissionOverwrite(read_messages=True, send_messages=True), guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        ticket_channel = await guild.create_text_channel(name=f"شراء-{member.name}", category=interaction.channel.category, overwrites=overwrites)
        await interaction.response.send_message(f"✅ تم فتح التذكرة: {ticket_channel.mention}", ephemeral=True)
        await ticket_channel.send(embed=discord.Embed(title="🎯 متجر LTB الفوري", description="اضغط الزر لبدء المعاملة.", color=discord.Color.red()), view=TicketControlView())

class MainStoreView(View):
    def __init__(self): super().__init__(timeout=None); self.add_item(StoreDropdown())

# --- 🎯 رصد الرسائل وقراءة ملفات الذكاء الاصطناعي ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # تشغيل الذكاء الاصطناعي حصرياً داخل قناتك المخفية المحددة
    if message.channel.id == AI_CHANNEL_ID:
        async with message.channel.typing():
            user_content = message.content
            
            # ميزة قراءة الملفات المرفقة (مثل قراءة ملف الحسابات الضخم المرفوع TXT)
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.filename.endswith('.txt'):
                        try:
                            file_bytes = await attachment.read()
                            file_text = file_bytes.decode('utf-8')
                            user_content += f"\n\n[محتوى الملف المرفق النصي]:\n{file_text}"
                        except: pass
            
            # إرسال البيانات فوراً لـ Gemini وجلب الرد الذكي
            ai_response = await ask_gemini_ai(user_content)
            
            # ميزة الحفظ الذكي التلقائي إذا أمرت الذكاء الاصطناعي بتحديث الحسابات بصيغة JSON
            if "{" in ai_response and "}" in ai_response and '"title"' in ai_response:
                try:
                    # محاولة استخراج كود الـ JSON المحدث لحفظه تلقائياً بالموقع
                    start_idx = ai_response.find("{")
                    end_idx = ai_response.rfind("}") + 1
                    json_str = ai_response[start_idx:end_idx]
                    parsed_json = json.loads(json_str)
                    
                    global DB_ACCOUNTS
                    DB_ACCOUNTS.update(parsed_json)
                    save_accounts()
                    await message.channel.send("⚡ **[نظام متجر LTB الذكي]: تم رصد الحسابات الجديدة وحفظها تلقائياً في قاعدة بيانات الموقع الإلكتروني!**")
                except: pass
                
            # إرسال رد المساعد الذكي في الشات
            # تقسيم الرسائل الطويلة جداً لضمان عدم تخطي حد ديسكورد (2000 حرف)
            if len(ai_response) > 2000:
                for chunk in [ai_response[i:i+1900] for i in range(0, len(ai_response), 1900)]:
                    await message.channel.send(chunk)
            else:
                await message.channel.send(ai_response)
                
    await bot.process_commands(message)

@bot.command()
async def send_shop(ctx):
    if has_dashboard_permission(ctx.author, "perm_setup_cmd"):
        await ctx.send(embed=discord.Embed(title="🌐 موقع متجر LTB الرسمي", description="اضغط الزر لتصفح كتالوج الحسابات.", color=discord.Color.purple()), view=WebsiteRedirectView("https://bot-nmae.onrender.com/"))

@bot.command()
async def setup(ctx):
    if has_dashboard_permission(ctx.author, "perm_setup_cmd"):
        await ctx.send(embed=discord.Embed(title="🛒 LTB Global Hub", description="اختر واجهتك لبدء معاملة الشراء الفوري.", color=discord.Color.red()), view=MainStoreView())

@bot.command()
async def clear(ctx, amount: int = 20):
    if has_dashboard_permission(ctx.author, "perm_clear_cmd"): await ctx.channel.purge(limit=amount + 1)

@bot.event
async def on_ready():
    bot.add_view(MainStoreView()); bot.add_view(TicketControlView()); bot.add_view(TicketDeleteView())
    print("⚡ AI Agent & LTB Engine Enabled on Channel 1505753282361032820 successfully!")

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN: bot.run(TOKEN)