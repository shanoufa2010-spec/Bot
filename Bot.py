import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
import asyncio
from threading import Thread
from flask import Flask, render_template_string, request, redirect, url_for

# 🌐 إعداد خادم الويب ولوحة التحكم (Dashboard)
app = Flask('')

# إعدادات النظام القابلة للتعديل عبر الموقع مباشرة
BOT_CONFIG = {
    "admin_password": "admin1234",  # كلمة مرور لوحة التحكم الخاصة بك
    "wallet_bep20": "0x280ca19aAAF32F81dfb0245e88bc567222aF718F",
    "wallet_trc20": "TNkNLf2zjjE5EKWYGnb6Tmp2b2DPXmJwU8",
    "allowed_roles": ["Mega Owner", "Sellers Leader"]  # الرتب المسموح لها بالإدارة
}

# الرومات الثابتة المأخوذة من سيرفرك
ADMIN_LOG_CHANNEL_ID = 1506320607032381581  # روم #shop-log
ACCOUNTS_DIR = "./"
active_transactions = {}
user_cooldowns = {}

# واجهة موقع الويب (HTML/CSS) للوحة التحكم
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LTB Store - لوحة التحكم</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1a1a2e; color: #fff; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: #16162a; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h1 { color: #e94560; text-align: center; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #bbb; }
        input[type="text"], input[type="password"] { width: 100%; padding: 12px; border: 1px solid #30475e; background: #222831; color: #fff; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #e94560; border: none; color: white; font-size: 16px; font-weight: bold; border-radius: 6px; cursor: pointer; transition: 0.3s; }
        button:hover { background: #b83148; }
        .alert { padding: 10px; background: #4e9f3d; color: white; border-radius: 6px; text-align: center; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚙️ لوحة تحكم متجر LTB</h1>
        {% if success %}
            <div class="alert">✅ تم تحديث الإعدادات والمحافظ بنجاح داخل البوت!</div>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label>🔒 كلمة مرور اللوحة الحالية:</label>
                <input type="password" name="password" required placeholder="أدخل كلمة المرور للتعديل">
            </div>
            <hr style="border-color: #30475e; margin: 25px 0;">
            <div class="form-group">
                <label>🪙 محفظة USDT (BEP20):</label>
                <input type="text" name="bep20" value="{{ config.wallet_bep20 }}">
            </div>
            <div class="form-group">
                <label>🪙 محفظة USDT (TRC20):</label>
                <input type="text" name="trc20" value="{{ config.wallet_trc20 }}">
            </div>
            <div class="form-group">
                <label>🛠️ الرتب الإدارية المسموحة (مفصولة بفاصلة):</label>
                <input type="text" name="roles" value="{{ roles_string }}">
            </div>
            <button type="submit">💾 حفظ التغييرات وتحديث البوت فوراً</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    success = False
    if request.method == 'POST':
        entered_pass = request.form.get('password')
        if entered_pass == BOT_CONFIG['admin_password']:
            BOT_CONFIG['wallet_bep20'] = request.form.get('bep20')
            BOT_CONFIG['wallet_trc20'] = request.form.get('trc20')
            raw_roles = request.form.get('roles', '')
            BOT_CONFIG['allowed_roles'] = [r.strip() for r in raw_roles.split(',') if r.strip()]
            success = True
            
    roles_string = ", ".join(BOT_CONFIG['allowed_roles'])
    return render_template_string(DASHBOARD_HTML, config=BOT_CONFIG, roles_string=roles_string, success=success)

def run_http_server():
    app.run(host='0.0.0.0', port=8080)

# 🤖 إعدادات ومراقبة بوت الديسكورد
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class AdminApprovalView(View):
    def __init__(self, buyer_id, account_num, ticket_channel_id, lang="ar"):
        super().__init__(timeout=None)
        self.buyer_id = buyer_id
        self.account_num = account_num
        self.ticket_channel_id = ticket_channel_id
        self.lang = lang

    @discord.ui.button(label="✅ موافقة وتسليم / Approve", style=discord.ButtonStyle.success, custom_id="approve_sale_btn")
    async def approve_sale(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in BOT_CONFIG['allowed_roles'] for role in interaction.user.roles):
            await interaction.response.defer()
            ticket_channel = bot.get_channel(self.ticket_channel_id)
            
            old_embed = interaction.message.embeds[0] if interaction.message.embeds else None
            embed_log = discord.Embed(title="✅ تقرير بيع ناجح / Sale Approved", color=discord.Color.green())
            embed_log.add_field(name="👤 المشتري / Buyer", value=f"<@{self.buyer_id}>", inline=True)
            embed_log.add_field(name="📦 رقم الحساب / Item ID", value=f"`{self.account_num}`", inline=True)
            embed_log.add_field(name="🛠️ المسؤول / Admin", value=interaction.user.mention, inline=False)
            if old_embed and old_embed.image:
                embed_log.set_image(url=old_embed.image.url)
            
            await interaction.message.edit(embed=embed_log, view=None)

            if ticket_channel:
                title = "🎉 تم تأكيد الدفع بنجاح!" if self.lang == "ar" else "🎉 Payment Confirmed!"
                msg = f"مرحباً <@{self.buyer_id}>، تم التحقق من تحويلك. سيتم تسليمك البيانات الآن." if self.lang == "ar" else f"Hello <@{self.buyer_id}>, payment verified. Credentials will be sent shortly."
                await ticket_channel.send(embed=discord.Embed(title=title, description=msg, color=discord.Color.green()))
        else:
            await interaction.response.send_message("❌ غير مصرح لك!", ephemeral=True)

class TicketDeleteView(View):
    def __init__(self, lang="ar"):
        super().__init__(timeout=None)
        self.lang = lang

    @discord.ui.button(label="🗑️ حذف التذكرة / Delete", style=discord.ButtonStyle.danger, custom_id="delete_ticket_btn")
    async def delete_ticket(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in BOT_CONFIG['allowed_roles'] for role in interaction.user.roles):
            msg = "⚠️ جاري حذف الروم خلال 5 ثوانٍ..." if self.lang == "ar" else "⚠️ Deleting channel in 5 seconds..."
            await interaction.response.send_message(msg)
            await asyncio.sleep(5)
            await interaction.channel.delete()

class TicketControlView(View):
    def __init__(self, lang="ar"):
        super().__init__(timeout=None)
        self.lang = lang
        self.children[0].label = "💰 إظهار محفظة الدفع" if lang == "ar" else "💰 Show Wallets"
        self.children[1].label = "🔒 إغلاق التذكرة" if lang == "ar" else "🔒 Close Ticket"

    @discord.ui.button(label="💰 Wallet", style=discord.ButtonStyle.success, custom_id="buy_acc_btn")
    async def buy_account(self, interaction: discord.Interaction, button: Button):
        if self.lang == "ar":
            title = "🪙 تفاصيل الدفع الذكي (USDT)"
            desc = f"📌 **شبكة Smart Chain (BEP20):**\n`{BOT_CONFIG['wallet_bep20']}`\n\n📌 **شبكة Tron (TRC20):**\n`{BOT_CONFIG['wallet_trc20']}`\n\n📸 **ارفع صورة الوصل مباشرة هنا لتأكيد طلبك أوتوماتيكياً!**"
        else:
            title = "🪙 Crypto Payment Details (USDT)"
            desc = f"📌 **BNB Smart Chain (BEP20):**\n`{BOT_CONFIG['wallet_bep20']}`\n\n📌 **Tron Network (TRC20):**\n`{BOT_CONFIG['wallet_trc20']}`\n\n📸 **Upload your screenshot proof directly here to notify admins!**"
            
        await interaction.response.send_message(embed=discord.Embed(title=title, description=desc, color=discord.Color.gold()))

    @discord.ui.button(label="🔒 Close", style=discord.ButtonStyle.secondary, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in BOT_CONFIG['allowed_roles'] for role in interaction.user.roles):
            await interaction.response.send_message("🔒 Closing ticket...")
            try: await interaction.channel.edit(name=f"🔒-closed-{interaction.channel.name}")
            except: pass
            for o in interaction.channel.overwrites:
                if isinstance(o, discord.Member) and not o.bot:
                    await interaction.channel.set_permissions(o, read_messages=True, send_messages=False)
            await interaction.channel.send(view=TicketDeleteView(lang=self.lang))

class StoreDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🇩🇿 شراء واستعراض الحسابات (بالعربية)", value="ar_crypto", emoji="🛒"),
            discord.SelectOption(label="🔄 طلب مقايضة حساب أو بطاقات AliExpress", value="ar_trade", emoji="🔄"),
            discord.SelectOption(label="🇬🇧 Browse & Buy Accounts (English)", value="en_crypto", emoji="🪙"),
            discord.SelectOption(label="🔀 Trade Accounts / Gift Cards (English)", value="en_trade", emoji="🔀")
        ]
        super().__init__(placeholder="🔽 اختر لغتك والقسم المناسب / Choose Language & Section...", min_values=1, max_values=1, options=options, custom_id="store_select_menu")

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
            embed.title = "🎯 متجر LTB الذكي"
            embed.description = f"مرحباً {member.mention}، اكتب **رقم الحساب** لاستعراض الصور فوراً، أو اكتب تفاصيل مقايضتك هنا."
        else:
            embed.title = "🎯 LTB Global Store"
            embed.description = f"Welcome {member.mention}, enter the **Account ID** to preview photos instantly, or leave your trade details here."
            
        await ticket_channel.send(embed=embed, view=TicketControlView(lang=lang))

class MainStoreView(View):
    def __init__(self): super().__init__(timeout=None); self.add_item(StoreDropdown())

@bot.event
async def on_message(message):
    if message.author.bot: return
    channel_name = message.channel.name.lower()
    
    if any(p in channel_name for p in ["تذكرة", "مقايضة", "شراء", "buy", "trade", "closed"]):
        current_lang = "ar" if any(x in channel_name for x in ["تذكرة", "مقايضة", "شراء"]) else "en"
        
        # التقاط صور إثبات التحويل تلقائياً
        if message.attachments and message.channel.id in active_transactions:
            if message.attachments[0].filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                log_channel = bot.get_channel(ADMIN_LOG_CHANNEL_ID)
                if log_channel:
                    try:
                        log_msg = await log_channel.fetch_message(active_transactions[message.channel.id]["log_msg_id"])
                        emb = discord.Embed(title="⏳ تم تلقي وصل إثبات الدفع!", color=discord.Color.blue())
                        emb.set_image(url=message.attachments[0].url)
                        await log_msg.edit(embed=emb)
                        await message.channel.send("✅ **تم إرسال لقطة الوصل للإدارة بنجاح وجاري المراجعة.**")
                    except: pass

        # نظام تصفح الحسابات بالرقم
        search_target = message.content.strip()
        if search_target.isdigit():
            user_id = message.author.id
            current_time = asyncio.get_event_loop().time()
            if user_id in user_cooldowns and current_time - user_cooldowns[user_id] < 4.0:
                try: await message.delete()
                except: pass
                return
            user_cooldowns[user_id] = current_time

            waiting_msg = await message.channel.send("🔄 Searching...")
            try:
                all_items = os.listdir(ACCOUNTS_DIR)
                target_folder = next((i for i in all_items if os.path.isdir(os.path.join(ACCOUNTS_DIR, i)) and (i == search_target or i.startswith(f"{search_target} "))), None)
                if target_folder:
                    f_path = os.path.join(ACCOUNTS_DIR, target_folder)
                    images = [img for img in os.listdir(f_path) if img.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                    if images:
                        await message.channel.send(f"📦 **Account: {target_folder}**")
                        for img in images:
                            with open(os.path.join(f_path, img), 'rb') as f: await message.channel.send(file=discord.File(f))
                        
                        log_channel = bot.get_channel(ADMIN_LOG_CHANNEL_ID)
                        if log_channel:
                            embed_p = discord.Embed(title="⏳ طلب معلق جديد", description=f"المشتري: {message.author.mention}\nالحساب: `{target_folder}`", color=discord.Color.orange())
                            l_msg = await log_channel.send(embed=embed_p, view=AdminApprovalView(buyer_id=message.author.id, account_num=target_folder, ticket_channel_id=message.channel.id, lang=current_lang))
                            active_transactions[message.channel.id] = {"log_msg_id": l_msg.id, "account_id": target_folder}
                else:
                    await message.channel.send("❌ Not Found / غير موجود")
            except: pass
            try: await message.delete(); await waiting_msg.delete()
            except: pass

    await bot.process_commands(message)

@bot.event
async def on_ready():
    bot.add_view(MainStoreView()); bot.add_view(TicketControlView()); bot.add_view(TicketDeleteView())
    print("⚡ LTB Ultimate Bot & Dashboard is Online!")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(title="🛒 LTB Global Marketplace", description="اختر لغتك والقسم المناسب لفتح تذكرة فورية / Select language to start", color=discord.Color.red())
    await ctx.send(embed=embed, view=MainStoreView())

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN: bot.run(TOKEN)