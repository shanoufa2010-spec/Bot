import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
import asyncio
from threading import Thread
from flask import Flask, render_template_string, request, redirect, url_for, session

# 🌐 إعداد خادم الويب والموقع المتطور
app = Flask('')
app.secret_key = os.getenv("FLASK_SECRET", "LTB_SUPER_SECRET_KEY_9988")

# 🔒 قاعدة بيانات الإعدادات الافتراضية (تُعدل بالكامل من لوحة التحكم)
BOT_CONFIG = {
    # الحماية (بيانات الدخول التي طلبتها)
    "web_user": "admin",
    "web_pass": "LTB_Owner_2026",
    
    # المحافظ الرقمية
    "wallet_bep20": "0x280ca19aAAF32F81dfb0245e88bc567222aF718F",
    "wallet_trc20": "TNkNLf2zjjE5EKWYGnb6Tmp2b2DPXmJwU8",
    
    # تخصيص رومات السيرفر (الأيدي)
    "log_channel_id": "1506320607032381581",      # روم #shop-log
    "welcome_channel_id": "1505753282755170324",  # روم الترحيب
    "reviews_channel_id": "1505753282755170324",  # روم التقييمات والآراء
    
    # حالات تشغيل الميزات (On / Off)
    "enable_welcome": "on",
    "enable_reviews": "on",
    
    # صلاحيات الأوامر المستقلة (تخصيص الرتب لكل أمر)
    "perm_setup_cmd": "Mega Owner, Sellers Leader, Admin",
    "perm_clear_cmd": "Mega Owner, Admin",
    "perm_approve_action": "Mega Owner, Sellers Leader",
    "perm_close_ticket": "Mega Owner, Sellers Leader, Staff"
}

ACCOUNTS_DIR = "./"
active_transactions = {}
user_cooldowns = {}

# 🎨 تصميم واجهات الموقع (صفحة الدخول + لوحة التحكم مثل ProBot)
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LTB Store - تسجيل الدخول الآمن</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f0c1b; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: #17122b; padding: 40px; border-radius: 12px; box-shadow: 0 8px 25px rgba(0,0,0,0.6); width: 100%; max-width: 400px; text-align: center; border: 1px solid #2c254a; }
        h2 { color: #5865F2; margin-bottom: 25px; }
        .input-group { margin-bottom: 20px; text-align: right; }
        label { display: block; margin-bottom: 8px; color: #a2a0b6; font-size: 14px; }
        input { width: 100%; padding: 12px; background: #0f0c1b; border: 1px solid #2c254a; color: #fff; border-radius: 6px; box-sizing: border-box; font-size: 15px; }
        input:focus { border-color: #5865F2; outline: none; }
        button { width: 100%; padding: 12px; background: #5865F2; border: none; color: white; font-size: 16px; font-weight: bold; border-radius: 6px; cursor: pointer; transition: 0.2s; }
        button:hover { background: #4752c4; }
        .error { color: #ed4245; margin-bottom: 15px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>🔒 تسجيل دخول الإدارة</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST" action="/login">
            <div class="input-group">
                <label>اسم المستخدم:</label>
                <input type="text" name="username" required>
            </div>
            <div class="input-group">
                <label>كلمة المرور:</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">تسجيل الدخول للوحة</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LTB Dashboard - لوحة التحكم الاحترافية</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #0f0c1b; color: #f2f1f5; margin: 0; padding: 0; display: flex; }
        .sidebar { width: 260px; background: #17122b; height: 100vh; position: fixed; padding: 20px; box-sizing: border-box; border-left: 1px solid #2c254a; }
        .sidebar h2 { color: #5865F2; text-align: center; font-size: 22px; margin-bottom: 30px; }
        .sidebar a { display: block; padding: 12px; color: #a2a0b6; text-decoration: none; border-radius: 6px; margin-bottom: 10px; font-weight: 500; }
        .sidebar a.active, .sidebar a:hover { background: #231b3e; color: #fff; border-right: 4px solid #5865F2; }
        .main-content { margin-right: 260px; padding: 40px; width: 100%; max-width: 1000px; box-sizing: border-box; }
        .card { background: #17122b; border-radius: 8px; padding: 25px; margin-bottom: 25px; border: 1px solid #2c254a; }
        .card h3 { margin-top: 0; color: #5865F2; border-bottom: 1px solid #2c254a; padding-bottom: 10px; }
        .form-row { display: flex; gap: 20px; margin-bottom: 15px; }
        .form-group { flex: 1; display: flex; flex-direction: column; }
        label { font-size: 14px; color: #a2a0b6; margin-bottom: 8px; }
        input[type="text"], select { padding: 12px; background: #0f0c1b; border: 1px solid #2c254a; color: #fff; border-radius: 6px; font-size: 14px; }
        input:focus, select:focus { border-color: #5865F2; outline: none; }
        .btn-save { background: #43b581; color: white; border: none; padding: 14px; font-size: 16px; font-weight: bold; border-radius: 6px; cursor: pointer; width: 100%; transition: 0.2s; }
        .btn-save:hover { background: #3ca374; }
        .logout { background: #ed4245; color: white; text-align: center; padding: 10px; text-decoration: none; border-radius: 6px; display: block; margin-top: 50px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>LTB ProBot ⚙️</h2>
        <a href="#" class="active">🎛️ الإعدادات العامة</a>
        <a href="/logout" class="logout">🚪 تسجيل الخروج</a>
    </div>
    
    <div class="main-content">
        <h2>🎛️ إدارة وتخصيص صلاحيات البوت بالكامل</h2>
        
        {% if msg %}<div style="background: #43b581; padding: 15px; border-radius: 6px; margin-bottom: 20px;">✅ تم حفظ وتحديث كافة الصلاحيات والأوامر داخل السيرفر فوراً!</div>{% endif %}
        
        <form method="POST" action="/save">
            <div class="card">
                <h3>🪙 بوابة الدفع المعتمدة (Cryptocurrency)</h3>
                <div class="form-group" style="margin-bottom: 15px;">
                    <label>محفظة USDT (شبكة BNB Smart Chain - BEP20):</label>
                    <input type="text" name="wallet_bep20" value="{{ config.wallet_bep20 }}">
                </div>
                <div class="form-group">
                    <label>محفظة USDT (شبكة Tron Network - TRC20):</label>
                    <input type="text" name="wallet_trc20" value="{{ config.wallet_trc20 }}">
                </div>
            </div>

            <div class="card">
                <h3>🎯 تعيين الرومات المخصصة (Channel Assignments)</h3>
                <div class="form-row">
                    <div class="form-group">
                        <label>روم سجل المبيعات واللوج المباشر (#shop-log ID):</label>
                        <input type="text" name="log_channel_id" value="{{ config.log_channel_id }}">
                    </div>
                    <div class="form-group">
                        <label>روم الترحيب بالأعضاء الجدد (ID):</label>
                        <input type="text" name="welcome_channel_id" value="{{ config.welcome_channel_id }}">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>روم التقييمات والآراء التلقائية (#reviews ID):</label>
                        <input type="text" name="reviews_channel_id" value="{{ config.reviews_channel_id }}">
                    </div>
                    <div class="form-group">
                        <label>نظام الترحيب ونظام التقييمات التلقائي:</label>
                        <select name="enable_welcome">
                            <option value="on" {% if config.enable_welcome == 'on' %}selected{% endif %}>تشغيل الأنظمة تلقائياً (On)</option>
                            <option value="off" {% if config.enable_welcome == 'off' %}selected{% endif %}>إيقاف وتعطيل (Off)</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>🛠️ تخصيص رتب الأوامر (Command Permissions)</h3>
                <p style="font-size: 13px; color: #a2a0b6; margin-top: -10px; margin-bottom: 15px;">* اكتب أسماء الرتب المسموح لها باستخدام كل أمر وافصل بينها بفاصلة (,)</p>
                
                <div class="form-group" style="margin-bottom: 15px;">
                    <label>رتب أمر إنشاء لوحة المتجر الرئيسي (`!setup`):</label>
                    <input type="text" name="perm_setup_cmd" value="{{ config.perm_setup_cmd }}">
                </div>
                <div class="form-group" style="margin-bottom: 15px;">
                    <label>رتب أمر مسح وتنظيف رومات الشات (`!clear`):</label>
                    <input type="text" name="perm_clear_cmd" value="{{ config.perm_clear_cmd }}">
                </div>
                <div class="form-group" style="margin-bottom: 15px;">
                    <label>رتب أزرار التحكم بالتذاكر (الموافقة والتسليم التلقائي):</label>
                    <input type="text" name="perm_approve_action" value="{{ config.perm_approve_action }}">
                </div>
                <div class="form-group">
                    <label>رتب إغلاق وأرشفة تذاكر المشترين الدبلوماسية:</label>
                    <input type="text" name="perm_close_ticket" value="{{ config.perm_close_ticket }}">
                </div>
            </div>

            <button type="submit" class="btn-save">💾 حفظ كافة التحديثات وتطبيقها على السيرفر</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    if 'logged_in' in session: return render_template_string(DASHBOARD_HTML, config=BOT_CONFIG, msg=request.args.get('msg'))
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('username')
    pw = request.form.get('password')
    if user == BOT_CONFIG['web_user'] and pw == BOT_CONFIG['web_pass']:
        session['logged_in'] = True
        return redirect(url_for('home'))
    return render_template_string(LOGIN_HTML, error="❌ خطأ في اسم المستخدم أو كلمة المرور!")

@app.route('/save', methods=['POST'])
def save_config():
    if 'logged_in' not in session: return redirect(url_for('home'))
    for key in BOT_CONFIG.keys():
        if key in request.form:
            BOT_CONFIG[key] = request.form.get(key)
    return redirect(url_for('home', msg="success"))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

def run_http_server():
    app.run(host='0.0.0.0', port=8080)


# 🤖 برمجة وهيكلة صلاحيات بوت الديسكورد
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)

def has_dashboard_permission(user, config_key):
    if user.guild_permissions.administrator:
        return True
    allowed_roles = [r.strip().lower() for r in BOT_CONFIG[config_key].split(",") if r.strip()]
    return any(role.name.lower() in allowed_roles for role in user.roles)


class AdminApprovalView(View):
    def __init__(self, buyer_id, account_num, ticket_channel_id, lang="ar"):
        super().__init__(timeout=None)
        self.buyer_id = buyer_id
        self.account_num = account_num
        self.ticket_channel_id = ticket_channel_id
        self.lang = lang

    @discord.ui.button(label="✅ موافقة وتسليم / Approve", style=discord.ButtonStyle.success, custom_id="approve_sale_btn")
    async def approve_sale(self, interaction: discord.Interaction, button: Button):
        if has_dashboard_permission(interaction.user, "perm_approve_action"):
            await interaction.response.defer()
            ticket_channel = bot.get_channel(self.ticket_channel_id)
            
            old_embed = interaction.message.embeds[0] if interaction.message.embeds else None
            embed_log = discord.Embed(title="✅ تقرير بيع ناجح ومعتمد", color=discord.Color.green())
            embed_log.add_field(name="👤 المشتري", value=f"<@{self.buyer_id}>", inline=True)
            embed_log.add_field(name="📦 رقم الحساب المعين", value=f"`{self.account_num}`", inline=True)
            embed_log.add_field(name="🛠️ المشرف المسؤول", value=interaction.user.mention, inline=False)
            if old_embed and old_embed.image: embed_log.set_image(url=old_embed.image.url)
            
            await interaction.message.edit(embed=embed_log, view=None)

            if ticket_channel:
                title = "🎉 تم تأكيد الدفع بنجاح!" if self.lang == "ar" else "🎉 Payment Confirmed!"
                msg = f"مرحباً <@{self.buyer_id}>، تم التحقق من تحويل الكريبتو الخاص بك بنجاح. سيتم تسليمك البيانات المباشرة الآن." if self.lang == "ar" else f"Hello <@{self.buyer_id}>, your payment has been verified. Check your credentials right now."
                await ticket_channel.send(embed=discord.Embed(title=title, description=msg, color=discord.Color.green()))
                
                if BOT_CONFIG["enable_welcome"] == "on":
                    try:
                        rev_channel = bot.get_channel(int(BOT_CONFIG["reviews_channel_id"]))
                        if rev_channel:
                            embed_rev = discord.Embed(title="⭐ عملية شراء جديدة ناجحة", description=f"شكرًا لك <@{self.buyer_id}> على ثقتك بمتجرنا! تم شراء الحساب بنجاح 🪙.", color=discord.Color.gold())
                            await rev_channel.send(embed=embed_rev)
                    except: pass
        else:
            await interaction.response.send_message("❌ الرتبة الخاصة بك غير مصرح لها بالموافقة من لوحة التحكم!", ephemeral=True)

class TicketDeleteView(View):
    def __init__(self, lang="ar"):
        super().__init__(timeout=None); self.lang = lang

    @discord.ui.button(label="🗑️ حذف التذكرة / Delete", style=discord.ButtonStyle.danger, custom_id="delete_ticket_btn")
    async def delete_ticket(self, interaction: discord.Interaction, button: Button):
        if has_dashboard_permission(interaction.user, "perm_close_ticket"):
            msg = "⚠️ جاري مسح الغرفة بالكامل..." if self.lang == "ar" else "⚠️ Channel absolute deletion in 5s..."
            await interaction.response.send_message(msg)
            await asyncio.sleep(5)
            await interaction.channel.delete()

class TicketControlView(View):
    def __init__(self, lang="ar"):
        super().__init__(timeout=None); self.lang = lang
        self.children[0].label = "💰 إظهار محفظة الدفع" if lang == "ar" else "💰 Show Wallets"
        self.children[1].label = "🔒 إغلاق التذكرة" if lang == "ar" else "🔒 Close Ticket"

    @discord.ui.button(label="💰 Wallet", style=discord.ButtonStyle.success, custom_id="buy_acc_btn")
    async def buy_account(self, interaction: discord.Interaction, button: Button):
        if self.lang == "ar":
            title = "🪙 بوابة الدفع المعتمدة (USDT)"
            desc = f"📌 **شبكة Smart Chain (BEP20):**\n`{BOT_CONFIG['wallet_bep20']}`\n\n📌 **شبكة Tron (TRC20):**\n`{BOT_CONFIG['wallet_trc20']}`\n\n📸 **قم برفع لقطة إثبات الدفع هنا فورًا لتنبيه المشرفين المعتمدين.**"
        else:
            title = "🪙 Secure Crypto Wallets (USDT)"
            desc = f"📌 **BNB Smart Chain (BEP20):**\n`{BOT_CONFIG['wallet_bep20']}`\n\n📌 **Tron Network (TRC20):**\n`{BOT_CONFIG['wallet_trc20']}`\n\n📸 **Upload your screenshot here to trigger immediate verification.**"
        await interaction.response.send_message(embed=discord.Embed(title=title, description=desc, color=discord.Color.gold()))

    @discord.ui.button(label="🔒 Close", style=discord.ButtonStyle.secondary, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if has_dashboard_permission(interaction.user, "perm_close_ticket"):
            await interaction.response.send_message("🔒 Closing ticket...")
            try: await interaction.channel.edit(name=f"🔒-مغلقة-{interaction.channel.name}")
            except: pass
            for o in interaction.channel.overwrites:
                if isinstance(o, discord.Member) and not o.bot:
                    await interaction.channel.set_permissions(o, read_messages=True, send_messages=False)
            await interaction.channel.send(view=TicketDeleteView(lang=self.lang))

class StoreDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🇩🇿 تصفح الحسابات والدفع بالكريبتو", value="ar_crypto", emoji="🛒"),
            discord.SelectOption(label="🔄 طلب مقايضة حساب أو بطاقة AliExpress", value="ar_trade", emoji="🔄"),
            discord.SelectOption(label="🇬🇧 Global Client - Buy via Crypto", value="en_crypto", emoji="🪙"),
            discord.SelectOption(label="🔀 Trade Account / Gift Cards", value="en_trade", emoji="🔀")
        ]
        super().__init__(placeholder="🔽 حدد لغة واجهة تذكرتك / Select language...", min_values=1, max_values=1, options=options, custom_id="store_select_menu")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        choice = self.values[0]
        lang = "ar" if choice.startswith("ar_") else "en"
        is_trade = "_trade" in choice
        
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), member: discord.PermissionOverwrite(read_messages=True, send_messages=True), guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        prefix = ("مقايضة" if is_trade else "شراء") if lang == "ar" else ("trade" if is_trade else "buy")
        
        ticket_channel = await guild.create_text_channel(name=f"{prefix}-{member.name}", category=interaction.channel.category, overwrites=overwrites)
        await interaction.response.send_message(f"✅ Created: {ticket_channel.mention}", ephemeral=True)
        
        embed = discord.Embed(color=discord.Color.red())
        if lang == "ar":
            embed.title = "🎯 متجر LTB الفوري"
            embed.description = f"مرحباً {member.mention}، اكتب **رقم الحساب** المطلوب لعرض صوره فوراً في الشات، أو وضع تفاصيل العرض الفني للمقايضة."
        else:
            embed.title = "🎯 LTB Fast Desk"
            embed.description = f"Welcome {member.mention}, send the exact **Account ID** numerical value to view details, or place your trade information."
            
        await ticket_channel.send(embed=embed, view=TicketControlView(lang=lang))

class MainStoreView(View):
    def __init__(self): super().__init__(timeout=None); self.add_item(StoreDropdown())

@bot.event
async def on_member_join(member):
    if BOT_CONFIG["enable_welcome"] == "on":
        try:
            welcome_ch = bot.get_channel(int(BOT_CONFIG["welcome_channel_id"]))
            if welcome_ch:
                await welcome_ch.send(f"🎉 مرحباً بك {member.mention} في سيرفر **LTB Store**! توجه لقسم الشراء لتصفح العروض الحية 🪙.")
        except: pass

@bot.event
async def on_message(message):
    if message.author.bot: return
    channel_name = message.channel.name.lower()
    
    if any(p in channel_name for p in ["تذكرة", "مقايضة", "شراء", "buy", "trade", "closed"]):
        current_lang = "ar" if any(x in channel_name for x in ["تذكرة", "مقايضة", "شراء"]) else "en"
        
        if message.attachments and message.channel.id in active_transactions:
            if message.attachments[0].filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                try:
                    log_channel = bot.get_channel(int(BOT_CONFIG["log_channel_id"]))
                    if log_channel:
                        log_msg = await log_channel.fetch_message(active_transactions[message.channel.id]["log_msg_id"])
                        emb = discord.Embed(title="⏳ تم تلقي وصل إثبات الدفع الفعلي!", color=discord.Color.blue())
                        emb.set_image(url=message.attachments[0].url)
                        await log_msg.edit(embed=emb)
                        await message.channel.send("✅ **تم رصد المرفق وإرساله فوراً للوحة مراجعة الإدارة الحية.**")
                except: pass

        search_target = message.content.strip()
        if search_target.isdigit():
            user_id = message.author.id
            current_time = asyncio.get_event_loop().time()
            if user_id in user_cooldowns and current_time - user_cooldowns[user_id] < 4.0:
                try: await message.delete()
                except: pass
                return
            user_cooldowns[user_id] = current_time

            waiting_msg = await message.channel.send("🔄 Loading Asset Details...")
            try:
                all_items = os.listdir(ACCOUNTS_DIR)
                target_folder = next((i for i in all_items if os.path.isdir(os.path.join(ACCOUNTS_DIR, i)) and (i == search_target or i.startswith(f"{search_target} "))), None)
                if target_folder:
                    f_path = os.path.join(ACCOUNTS_DIR, target_folder)
                    images = [img for img in os.listdir(f_path) if img.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                    if images:
                        await message.channel.send(f"📦 **Account ID: {target_folder}**")
                        for img in images:
                            with open(os.path.join(f_path, img), 'rb') as f: await message.channel.send(file=discord.File(f))
                        
                        try:
                            log_channel = bot.get_channel(int(BOT_CONFIG["log_channel_id"]))
                            if log_channel:
                                embed_p = discord.Embed(title="⏳ عملية شراء معلقة في التذاكر", description=f"المشتري: {message.author.mention}\nالحساب المستعرض: `{target_folder}`\nالروم: {message.channel.mention}", color=discord.Color.orange())
                                l_msg = await log_channel.send(embed=embed_p, view=AdminApprovalView(buyer_id=message.author.id, account_num=target_folder, ticket_channel_id=message.channel.id, lang=current_lang))
                                active_transactions[message.channel.id] = {"log_msg_id": l_msg.id, "account_id": target_folder}
                        except: pass
                else:
                    await message.channel.send("❌ الحساب غير متوفر حالياً في قاعدة البيانات.")
            except: pass
            try: await message.delete(); await waiting_msg.delete()
            except: pass

    await bot.process_commands(message)

@bot.command()
async def setup(ctx):
    if has_dashboard_permission(ctx.author, "perm_setup_cmd"):
        embed = discord.Embed(title="🛒 LTB Global Hub", description="اختر لغتك والقسم المخصص لبدء المعاملة / Choose Language & Section", color=discord.Color.red())
        await ctx.send(embed=embed, view=MainStoreView())
    else:
        await ctx.send("❌ عذراً، رتبتك الحالية لا تملك صلاحية أمر التثبيت طبقاً لإعدادات لوحة التحكم!")

@bot.command()
async def clear(ctx, amount: int = 20):
    if has_dashboard_permission(ctx.author, "perm_clear_cmd"):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"✅ تم تنظيف الشات وحذف {amount} رسالة بنجاح.", delete_after=4)
    else:
        await ctx.send("❌ لا تملك صلاحية تنظيف الشات.")

@bot.event
async def on_ready():
    bot.add_view(MainStoreView()); bot.add_view(TicketControlView()); bot.add_view(TicketDeleteView())
    print("⚡ LTB Pro Desktop Bot & Secure Advanced Dashboard Online!")

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN: bot.run(TOKEN)