import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
from threading import Thread
from flask import Flask
import asyncio

# خادم ويب مصغر لمنع وضع خمول السيرفر المجاني على Render
app = Flask('')

@app.route('/')
def home():
    return "LTB Multi-Language Crypto Store Bot is Online!"

def run_http_server():
    app.run(host='0.0.0.0', port=8080)

# قراءة التوكن المشفر من إعدادات بيئة Render
TOKEN = os.getenv("DISCORD_TOKEN")
ACCOUNTS_DIR = "./" 

# 🔒 إعدادات الأيدي الثابتة للرومات الخاصة بسيرفرك
ADMIN_UPLOAD_CHANNEL_ID = 1505753282755170324
ADMIN_LOG_CHANNEL_ID = 1506320607032381581  # روم سجل المبيعات (الشوب لوج)

# 🪙 عناوين المحافظ الرقمية الخاصة بك
WALLET_BEP20 = "0x280ca19aAAF32F81dfb0245e88bc567222aF718F"
WALLET_TRC20 = "TNkNLf2zjjE5EKWYGnb6Tmp2b2DPXmJwU8"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

user_cooldowns = {}
active_transactions = {}

# 📊 واجهة التحكم والموافقة داخل روم السجل الإداري (خاصة بالإدارة)
class AdminApprovalView(View):
    def __init__(self, buyer_id, account_num, ticket_channel_id, lang="ar"):
        super().__init__(timeout=None)
        self.buyer_id = buyer_id
        self.account_num = account_num
        self.ticket_channel_id = ticket_channel_id
        self.lang = lang

    @discord.ui.button(label="✅ موافقة وتسليم / Approve", style=discord.ButtonStyle.success, custom_id="approve_sale_btn")
    async def approve_sale(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            await interaction.response.defer()
            ticket_channel = bot.get_channel(self.ticket_channel_id)
            
            old_embed = interaction.message.embeds[0] if interaction.message.embeds else None
            embed_log = discord.Embed(title="✅ تقرير بيع ناجح / Sale Approved", color=discord.Color.green())
            embed_log.add_field(name="👤 المشتري / Buyer", value=f"<@{self.buyer_id}>", inline=True)
            embed_log.add_field(name="📦 رقم الحساب / Item ID", value=f"`{self.account_num}`", inline=True)
            embed_log.add_field(name="🛠️ المسؤول / Admin", value=interaction.user.mention, inline=False)
            if old_embed and old_embed.image:
                embed_log.set_image(url=old_embed.image.url)
            embed_log.set_footer(text="نظام سجل المبيعات • LTB Store")
            
            await interaction.message.edit(embed=embed_log, view=None)

            if ticket_channel:
                if self.lang == "ar":
                    msg = f"مرحباً <@{self.buyer_id}>، تم التحقق من تحويل الكريبتو الخاص بك بنجاح. سيقوم المسؤول بتسليمك البيانات الآن."
                    title = "🎉 تم تأكيد الدفع بنجاح!"
                else:
                    msg = f"Hello <@{self.buyer_id}>, your crypto payment has been verified. An admin will deliver your account credentials shortly."
                    title = "🎉 Payment Confirmed!"

                embed_buyer = discord.Embed(title=title, description=msg, color=discord.Color.green())
                await ticket_channel.send(content=f"<@{self.buyer_id}>", embed=embed_buyer)
        else:
            await interaction.response.send_message("❌ Limited to Admin only!", ephemeral=True)

    @discord.ui.button(label="❌ رفض الطلب / Deny", style=discord.ButtonStyle.danger, custom_id="deny_sale_btn")
    async def deny_sale(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            await interaction.response.defer()
            ticket_channel = bot.get_channel(self.ticket_channel_id)
            
            embed_log = discord.Embed(title="❌ طلب شراء مرفوض / Sale Denied", color=discord.Color.red())
            embed_log.add_field(name="👤 العضو / Buyer", value=f"<@{self.buyer_id}>", inline=True)
            embed_log.add_field(name="📦 رقم الحساب / Item ID", value=f"`{self.account_num}`", inline=True)
            embed_log.add_field(name="⚠️ الرافض / Rejected By", value=interaction.user.mention, inline=False)
            await interaction.message.edit(embed=embed_log, view=None)

            if ticket_channel:
                if self.lang == "ar":
                    await ticket_channel.send(f"⚠️ <@{self.buyer_id}>، تم رفض إثبات الدفع المرسل من قبلك. يرجى إعادة رفع لقطة صحيحة.")
                else:
                    await ticket_channel.send(f"⚠️ <@{self.buyer_id}>, your payment proof was rejected. Please upload a valid screenshot.")
        else:
            await interaction.response.send_message("❌ Limited to Admin only!", ephemeral=True)


# 🗑️ لوحة حذف وتصفية التكت بعد الانتهاء
class TicketDeleteView(View):
    def __init__(self, lang="ar"):
        super().__init__(timeout=None)
        self.lang = lang
        # تحديث نص الزر حسب لغة التكت
        self.children[0].label = "🗑️ حذف التذكرة نهائياً" if lang == "ar" else "🗑️ Delete Ticket"

    @discord.ui.button(label="🗑️ حذف التذكرة", style=discord.ButtonStyle.danger, custom_id="delete_ticket_btn")
    async def delete_ticket(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            msg = "⚠️ **تنبيه:** سيتم حذف هذه الروم نهائياً خلال **5 ثوانٍ**..." if self.lang == "ar" else "⚠️ **Notice:** This channel will be deleted in **5 seconds**..."
            await interaction.response.send_message(msg)
            await asyncio.sleep(5)
            await interaction.channel.delete()


# 💳 واجهة العمليات داخل تكت المشتري (تتغير لغتها تلقائياً)
class TicketControlView(View):
    def __init__(self, lang="ar"):
        super().__init__(timeout=None)
        self.lang = lang
        if lang == "ar":
            self.children[0].label = "💰 إظهار محفظة الدفع الرقمية"
            self.children[1].label = "🔒 إغلاق التذكرة"
        else:
            self.children[0].label = "💰 Show Crypto Wallets"
            self.children[1].label = "🔒 Close Ticket"

    @discord.ui.button(label="💰 Wallet", style=discord.ButtonStyle.success, custom_id="buy_acc_btn")
    async def buy_account(self, interaction: discord.Interaction, button: Button):
        if self.lang == "ar":
            title = "🪙 تفاصيل تحويل الكريبتو (USDT)"
            desc = (
                f"يرجى تحويل المبلغ إلى شبكة المحفظة التي تناسبك وتملك رصيداً فيها:\n\n"
                f"📌 **الخيار الأول: شبكة BNB Smart Chain (BEP20)**\n`{WALLET_BEP20}`\n\n"
                f"📌 **الخيار الثاني: شبكة Tron Network (TRC20)**\n`{WALLET_TRC20}`\n\n"
                "⚠️ **خطوة إجبارية ومهمة جداً:**\n"
                "📸 يرجى رفع **صورة وصل إثبات الدفع (اللقطة)** هنا في الشات مباشرة ليتم التقاطها وإرسالها أوتوماتيكياً إلى سجل الإدارة!"
            )
        else:
            title = "🪙 Crypto Payment Details (USDT)"
            desc = (
                f"Please transfer the amount to your preferred network wallet:\n\n"
                f"📌 **Option 1: BNB Smart Chain (BEP20)**\n`{WALLET_BEP20}`\n\n"
                f"📌 **Option 2: Tron Network (TRC20)**\n`{WALLET_TRC20}`\n\n"
                "⚠️ **Required Step:**\n"
                "📸 Please upload your **payment receipt screenshot (Proof)** directly in this chat! The bot will sync it automatically with the admin log."
            )
            
        embed_wallet = discord.Embed(title=title, description=desc, color=discord.Color.gold())
        await interaction.response.send_message(embed=embed_wallet)

    @discord.ui.button(label="🔒 Close", style=discord.ButtonStyle.secondary, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            msg = "🔒 جاري إغلاق وأرشفة التذكرة..." if self.lang == "ar" else "🔒 Closing and archiving this ticket..."
            await interaction.response.send_message(msg)
            
            try: 
                prefix = "🔒-مغلقة" if self.lang == "ar" else "🔒-closed"
                await interaction.channel.edit(name=f"{prefix}-{interaction.channel.name}")
            except: pass

            for overwrite in interaction.channel.overwrites:
                if isinstance(overwrite, discord.Member) and not overwrite.bot:
                    await interaction.channel.set_permissions(overwrite, read_messages=True, send_messages=False)
            
            if self.lang == "ar":
                title, desc, btn_label = "⚙️ لوحة الأرشفة", "انتهت المعاملة بنجاح، اضغط لإنهاء وحذف الروم.", "🗑️ حذف التذكرة نهائياً"
            else:
                title, desc, btn_label = "⚙️ Archive Dashboard", "Transaction finished. Click below to permanently delete this channel.", "🗑️ Delete Ticket"

            embed_delete = discord.Embed(title=title, description=desc, color=discord.Color.dark_gray())
            await interaction.channel.send(embed=embed_delete, view=TicketDeleteView(lang=self.lang))


# 🏪 القائمة المنسدلة الذكية لدعم اختيار اللغة
class StoreDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🇩🇿 تصفح وشراء الحسابات باللغة العربية", value="ar_crypto", description="لمعاينة الحسابات والدفع بالكريبتو واجهة عربية", emoji="🛒"),
            discord.SelectOption(label="🔄 طلب مقايضة أو دفع ببطاقات AliExpress", value="ar_trade", description="لمقايضة حسابك أو الدفع عبر بطاقات الهدايا", emoji="🔄"),
            discord.SelectOption(label="🇬🇧 Browse & Buy Accounts (English)", value="en_crypto", description="Preview accounts and pay globally via Crypto", emoji="🪙"),
            discord.SelectOption(label="🔀 Account Trade / Gift Cards (English)", value="en_trade", description="Exchange your game account or pay via AliExpress GC", emoji="🔀"),
        ]
        super().__init__(placeholder="🔽 Select your preferred language & section / اختر لغتك والقسم...", min_values=1, max_values=1, options=options, custom_id="store_select_menu")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        choice = self.values[0]
        
        lang = "ar" if choice.startswith("ar_") else "en"
        is_trade = "_trade" in choice
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # تسمية الروم بناء على اللغة والقسم выбранного
        if lang == "ar":
            prefix = "مقايضة" if is_trade else "شراء-كريبتو"
        else:
            prefix = "trade" if is_trade else "buy-crypto"

        ticket_channel = await guild.create_text_channel(name=f"{prefix}-{member.name}", category=interaction.channel.category, overwrites=overwrites)
        
        alert_msg = f"✅ تم إنشاء تذكرتك بنجاح: {ticket_channel.mention}" if lang == "ar" else f"✅ Ticket created successfully: {ticket_channel.mention}"
        await interaction.response.send_message(alert_msg, ephemeral=True)
        
        embed = discord.Embed(color=discord.Color.red())
        
        if lang == "ar":
            embed.title = f"🎯 القسم الحالي: {'المقايضات والبطاقات' if is_trade else 'استعراض وشراء الحسابات'}"
            if not is_trade:
                embed.description = (
                    f"مرحباً بك {member.mention} في **متجر LTB**.\n\n"
                    "ℹ️ **طريقة معاينة الحسابات:**\n"
                    "اكتب **رقم الحساب** مباشرة هنا في الشات (مثال: `45`) وسيقوم البوت بسحب وعرض الصور فوراً.\n\n"
                    "🪙 اضغط على الزر الأخضر بالأسفل لإظهار عناوين محافظنا عندما تقرر الشراء."
                )
            else:
                embed.description = (
                    f"مرحباً بك {member.mention} في قسم المقايضات.\n\n"
                    "📝 **المعاملات المقبولة:**\n"
                    "• مقايضة حسابات **eFootball (PES)**.\n"
                    "• بطاقات هدايا موقع **AliExpress**.\n\n"
                    "⚠️ يرجى كتابة تفاصيل عرضك وإرفاق الصور، وانتظار رد المشرف."
                )
            footer_text = "نظام متجر LTB العربي"
        else:
            embed.title = f"🎯 Section: {'Trade & Gift Cards' if is_trade else 'Browse & Buy Accounts'}"
            if not is_trade:
                embed.description = (
                    f"Welcome {member.mention} to **LTB Global Store**.\n\n"
                    "ℹ️ **How to preview accounts:**\n"
                    "Simply type the **Account ID** directly in this chat (e.g., `45`) and the bot will load the images immediately.\n\n"
                    "🪙 Click the green button below to show our secure crypto addresses once you find the right account."
                )
            else:
                embed.description = (
                    f"Welcome {member.mention} to the global trading desk.\n\n"
                    "📝 **We accept:**\n"
                    "• High-level **eFootball (PES)** accounts.\n"
                    "• Active **AliExpress Gift Cards**.\n\n"
                    "⚠️ Post your offer details and screenshots, then wait for an administrator."
                )
            footer_text = "LTB Global Store System"
            
        embed.set_footer(text=footer_text)
        await ticket_channel.send(content=f"Welcome / مرحباً بك {member.mention}", embed=embed, view=TicketControlView(lang=lang))


class MainStoreView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StoreDropdown())


@bot.event
async def on_message(message):
    if message.author.bot: return

    # 📥 روم إدارة رفع صور الحسابات من قبل المشرفين
    if message.channel.id == ADMIN_UPLOAD_CHANNEL_ID:
        folder_name = message.content.strip()
        if not folder_name or not message.attachments: return

        status_msg = await message.channel.send(f"🔄 جاري تحميل وحفظ صور الحساب رقم (**{folder_name}**)...")
        target_dir = os.path.join(ACCOUNTS_DIR, folder_name)
        os.makedirs(target_dir, exist_ok=True)

        success_count = 0
        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
        
        for index, attachment in enumerate(message.attachments):
            if attachment.filename.lower().endswith(valid_extensions):
                ext = os.path.splitext(attachment.filename)[1]
                file_path = os.path.join(target_dir, f"image_{index+1}{ext}")
                try:
                    await attachment.save(file_path)
                    success_count += 1
                except: pass

        if success_count > 0:
            await status_msg.edit(content=f"✅ Account (**{folder_name}**) created with {success_count} images!")
        return

    # 🔍 مراقبة التذاكر باللغتين وجلب الصور والتقاط الإثباتات
    channel_name = message.channel.name.lower()
    if any(prefix in channel_name for prefix in ["تذكرة", "مغلقة", "مقايضة", "شراء", "buy-", "trade", "closed"]):
        
        # تحديد لغة التكت الحالية من اسم القناة تلقائياً لتخصيص الردود
        current_lang = "ar" if any(x in channel_name for x in ["تذكرة", "مقايضة", "شراء", "مغلقة"]) else "en"

        # 📸 التقاط إثبات الدفع فور قيام المشتري برفع اللقطة داخل التكت
        if message.attachments and message.channel.id in active_transactions:
            valid_image_ext = ('.png', '.jpg', '.jpeg', '.webp')
            first_attachment = message.attachments[0]
            
            if first_attachment.filename.lower().endswith(valid_image_ext):
                log_msg_id = active_transactions[message.channel.id]["log_msg_id"]
                account_id = active_transactions[message.channel.id]["account_id"]
                log_channel = bot.get_channel(ADMIN_LOG_CHANNEL_ID)
                
                if log_channel:
                    try:
                        log_message = await log_channel.fetch_message(log_msg_id)
                        embed_updated = discord.Embed(title="⏳ تم استلام دليل التحويل / Proof Received", color=discord.Color.blue())
                        embed_updated.add_field(name="👤 المشتري / Buyer", value=message.author.mention, inline=True)
                        embed_updated.add_field(name="📦 رقم السلعة / Item ID", value=f"`{account_id}`", inline=True)
                        embed_updated.add_field(name="🎫 الروم / Ticket", value=message.channel.mention, inline=False)
                        embed_updated.description = "✅ **العضو قام برفع صورة الدليل بالأسفل!** تحقق من حسابك ثم تحكم بالطلب بالتحكم الإداري.\n✅ **The user has uploaded the proof image below!** Review and take action."
                        embed_updated.set_image(url=first_attachment.url)
                        embed_updated.set_footer(text="نظام تتبع الدلائل التلقائي • LTB Store")
                        
                        await log_message.edit(embed=embed_updated)
                        
                        thanks = "✅ **تم إرسال لقطة إثبات الدفع تلقائياً للإدارة وجاري التحقق الآن.**" if current_lang == "ar" else "✅ **Your payment proof has been submitted to the administration team successfully.**"
                        await message.channel.send(thanks)
                    except: pass

        search_target = message.content.strip()
        if search_target.isdigit():
            # ⏱️ نظام التهدئة (5 ثوانٍ لحماية البوت من السبام)
            user_id = message.author.id
            current_time = asyncio.get_event_loop().time()
            if user_id in user_cooldowns:
                time_passed = current_time - user_cooldowns[user_id]
                if time_passed < 5.0:
                    try: await message.delete()
                    except: pass
                    return
            
            user_cooldowns[user_id] = current_time

            load_msg = f"🔄 جاري جلب صور الحساب (**{search_target}**)..." if current_lang == "ar" else f"🔄 Loading images for Account ID (**{search_target}**)..."
            waiting_msg = await message.channel.send(load_msg)
            try:
                all_items = os.listdir(ACCOUNTS_DIR)
            except: return

            target_folder_name = None
            for item in all_items:
                item_path = os.path.join(ACCOUNTS_DIR, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    if item == search_target or item.startswith(f"{search_target} ") or f"({search_target})" in item:
                        target_folder_name = item
                        break

            if target_folder_name:
                folder_path = os.path.join(ACCOUNTS_DIR, target_folder_name)
                valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
                try:
                    images = [img for img in os.listdir(folder_path) if img.lower().endswith(valid_extensions)]
                except: return

                if images:
                    header = f"━━━━━━━━━━━━━━━━━━━━━\n📦 **صور السلعة: ({target_folder_name})**\n━━━━━━━━━━━━━━━━━━━━━" if current_lang == "ar" else f"━━━━━━━━━━━━━━━━━━━━━\n📦 **Account ID: ({target_folder_name})**\n━━━━━━━━━━━━━━━━━━━━━"
                    await message.channel.send(header)
                    for img_name in images:
                        img_path = os.path.join(folder_path, img_name)
                        try:
                            with open(img_path, 'rb') as f:
                                await message.channel.send(file=discord.File(f))
                        except: pass
                    
                    # 📊 إنشاء تقرير معلق فوري في الشوب لوج الإداري المشترك
                    log_channel = bot.get_channel(ADMIN_LOG_CHANNEL_ID)
                    if log_channel:
                        embed_pending = discord.Embed(title="⏳ معاملة معلقة / Pending Transaction", color=discord.Color.orange())
                        embed_pending.add_field(name="👤 العضو / Buyer", value=message.author.mention, inline=True)
                        embed_pending.add_field(name="📦 رقم الحساب / Item ID", value=f"`{target_folder_name}`", inline=True)
                        embed_pending.add_field(name="🎫 الروم / Ticket", value=message.channel.mention, inline=False)
                        embed_pending.description = "⏳ **في انتظار قيام الزبون بالتحويل وإرفاق لقطة شاشة الوصل لتظهر هنا تلقائياً...**\n⏳ Waiting for payment proof screenshot..."
                        embed_pending.set_footer(text="سجل الانتظار التلقائي • LTB Store")
                        
                        log_msg = await log_channel.send(
                            embed=embed_pending, 
                            view=AdminApprovalView(buyer_id=message.author.id, account_num=target_folder_name, ticket_channel_id=message.channel.id, lang=current_lang)
                        )
                        active_transactions[message.channel.id] = {
                            "log_msg_id": log_msg.id,
                            "account_id": target_folder_name
                        }
                else:
                    err_empty = f"❌ المجلد **{target_folder_name}** فارغ حالياً." if current_lang == "ar" else f"❌ Folder **{target_folder_name}** is empty."
                    await message.channel.send(err_empty)
            else:
                err_none = f"❌ عذراً، لم نجد الحساب رقم **{search_target}**." if current_lang == "ar" else f"❌ Account ID **{search_target}** not found."
                await message.channel.send(err_none)
            
            try:
                await message.delete()
                await waiting_msg.delete()
            except: pass

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"⚡ LTB Smart Multi-Language Bot Connected Successfully!")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    bot.add_view(MainStoreView())
    bot.add_view(TicketControlView())
    bot.add_view(TicketDeleteView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(
        title="🛒 متجر وسوق LTB الرقمي العالمي / LTB Global Marketplace",
        description=(
            "مرحباً بكم في المتجر المعتمد لبيع الحسابات الرقمية والمقايضة 🪙.\n"
            "🔽 **الرجاء فتح القائمة أدناه واختيار لغتك والقسم المناسب لطلبك:**\n\n"
            "Welcome to the certified digital marketplace.\n"
            "🔽 **Please open the menu below to choose your language & preferred section:**"
        ),
        color=discord.Color.red()
    )
    embed.set_image(url="https://images.unsplash.com/photo-1612287230202-1bf1d85d1bdf?q=80&w=1000")
    embed.set_footer(text="LTB Hub • Secure Trading / تداول آمن وموثوق")
    await ctx.send(embed=embed, view=MainStoreView())

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN: bot.run(TOKEN)