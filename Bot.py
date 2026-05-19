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
    return "LTB Global Crypto Store Bot with Auto-Proof Tracking is Online!"

def run_http_server():
    app.run(host='0.0.0.0', port=8080)

# قراءة التوكن المشفر من إعدادات بيئة Render
TOKEN = os.getenv("DISCORD_TOKEN")
ACCOUNTS_DIR = "./" 

# 🔒 إعدادات الأيدي الثابتة للرومات (تم تحديث روم اللوج بناءً على طلبك)
ADMIN_UPLOAD_CHANNEL_ID = 1505753282755170324
ADMIN_LOG_CHANNEL_ID = 1506320607032381581  # أيدي روم الشوب لوج الإداري الخاص بك

# 🪙 عناوين المحفظتين الخاصة بك تم وضعها هنا مباشرة
WALLET_BEP20 = "0x280ca19aAAF32F81dfb0245e88bc567222aF718F"
WALLET_TRC20 = "TNkNLf2zjjE5EKWYGnb6Tmp2b2DPXmJwU8"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

user_cooldowns = {}
# ذاكرة مؤقتة لربط التكت برقم رسالة اللوج لتحديثها أوتوماتيكياً عند إرسال الدليل
active_transactions = {}

# 📊 واجهة التحكم والموافقة داخل روم السجل الإداري (خاصة بالإدارة)
class AdminApprovalView(View):
    def __init__(self, buyer_id, account_num, ticket_channel_id):
        super().__init__(timeout=None)
        self.buyer_id = buyer_id
        self.account_num = account_num
        self.ticket_channel_id = ticket_channel_id

    @discord.ui.button(label="✅ Approve & Deliver", style=discord.ButtonStyle.success, custom_id="approve_sale_btn")
    async def approve_sale(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            await interaction.response.defer()
            ticket_channel = bot.get_channel(self.ticket_channel_id)
            
            # جلب الـ Embed القديم للحفاظ على صورة الدليل في السجل النهائي لتوثيق التحويل
            old_embed = interaction.message.embeds[0] if interaction.message.embeds else None
            embed_log = discord.Embed(title="✅ Global Sale Approved / تقرير بيع ناجح", color=discord.Color.green())
            embed_log.add_field(name="👤 Buyer / المشتري", value=f"<@{self.buyer_id}>", inline=True)
            embed_log.add_field(name="📦 Item ID / رقم السلعة", value=f"`{self.account_num}`", inline=True)
            embed_log.add_field(name="🛠️ Admin / المسؤول المعتمد", value=interaction.user.mention, inline=False)
            if old_embed and old_embed.image:
                embed_log.set_image(url=old_embed.image.url)
            embed_log.set_footer(text="Global Shop Log System • LTB Store")
            
            await interaction.message.edit(embed=embed_log, view=None)

            if ticket_channel:
                embed_buyer = discord.Embed(
                    title="🎉 Payment Confirmed! / تم تأكيد الدفع!",
                    description=(
                        f"Hello <@{self.buyer_id}>, your crypto payment has been successfully verified.\n"
                        f"An admin will deliver your account credentials **({self.account_num})** shortly in this chat.\n\n"
                        f"مرحباً <@{self.buyer_id}>، تم التحقق من تحويل الكريبتو بنجاح. سيقوم المسؤول بتسليمك بيانات الحساب الآن."
                    ),
                    color=discord.Color.green()
                )
                await ticket_channel.send(content=f"<@{self.buyer_id}>", embed=embed_buyer)
        else:
            await interaction.response.send_message("❌ Limited to Admin and Higher Roles only!", ephemeral=True)

    @discord.ui.button(label="❌ Deny / رفض الطلب", style=discord.ButtonStyle.danger, custom_id="deny_sale_btn")
    async def deny_sale(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            await interaction.response.defer()
            ticket_channel = bot.get_channel(self.ticket_channel_id)
            
            embed_log = discord.Embed(title="❌ Sale Denied / طلب مرفوض", color=discord.Color.red())
            embed_log.add_field(name="👤 Buyer / العضو المستهدف", value=f"<@{self.buyer_id}>", inline=True)
            embed_log.add_field(name="📦 Item ID / رقم السلعة", value=f"`{self.account_num}`", inline=True)
            embed_log.add_field(name="⚠️ Rejected By / الرافض", value=interaction.user.mention, inline=False)
            await interaction.message.edit(embed=embed_log, view=None)

            if ticket_channel:
                await ticket_channel.send(f"⚠️ <@{self.buyer_id}>, your payment proof was rejected. Please upload a valid screenshot or contact support.")
        else:
            await interaction.response.send_message("❌ Limited to Admin only!", ephemeral=True)


# 🗑️ لوحة الأرشفة النهائية للمسح والحذف بعد الانتهاء
class TicketDeleteView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Delete Ticket 🗑️", style=discord.ButtonStyle.danger, custom_id="delete_ticket_btn")
    async def delete_ticket(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            await interaction.response.send_message("⚠️ **Notice:** This channel will be permanently deleted in **5 seconds**...")
            await asyncio.sleep(5)
            await interaction.channel.delete()


# 💳 واجهة العمليات وتوليد رسائل الدفع وعرض خيارات المحافظ للمشتري
class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💰 Show Crypto Wallets", style=discord.ButtonStyle.success, custom_id="buy_acc_btn")
    async def buy_account(self, interaction: discord.Interaction, button: Button):
        embed_wallet = discord.Embed(
            title="🪙 Global Crypto Payment Details",
            description=(
                f"Please transfer the amount to the wallet network that suits you best:\n"
                f"الرجاء تحويل المبلغ إلى شبكة المحفظة التي تناسبك وتملك رصيداً فيها:\n\n"
                f"📌 **Option 1: BNB Smart Chain (BEP20)**\n`{WALLET_BEP20}`\n\n"
                f"📌 **Option 2: Tron Network (TRC20)**\n`{WALLET_TRC20}`\n\n"
                "⚠️ **Required Step / خطوة إجبارية:**\n"
                "📸 Please drop your **payment receipt screenshot (Proof)** directly in this chat!\n"
                "📸 الرجاء رفع **صورة وصل إثبات الدفع (الدليل)** هنا في الشات مباشرة ليظهر في سجل الإدارة أوتوماتيكياً!"
            ),
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed_wallet)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.secondary, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            await interaction.response.send_message("🔒 Closing and archiving this ticket...")
            try: await interaction.channel.edit(name=f"🔒-closed-{interaction.channel.name}")
            except: pass

            for overwrite in interaction.channel.overwrites:
                if isinstance(overwrite, discord.Member) and not overwrite.bot:
                    await interaction.channel.set_permissions(overwrite, read_messages=True, send_messages=False)
            
            embed_delete = discord.Embed(
                title="⚙️ Archive & Clean Dashboard",
                description="Transaction finished. Click the button below to permanently delete this channel.",
                color=discord.Color.dark_gray()
            )
            await interaction.channel.send(embed=embed_delete, view=TicketDeleteView())


# 🏪 القائمة المنسدلة في روم المتجر لتسهيل فرز طلبات الزبائن
class StoreDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🛒 Browse & Buy Accounts (Crypto)", description="View available game accounts and pay globally", emoji="🪙"),
            discord.SelectOption(label="🔄 Trade / Barter Request", description="Exchange your account or pay via Gift Cards", emoji="🔄"),
        ]
        super().__init__(placeholder="🔽 Select an option to open a ticket...", min_values=1, max_values=1, options=options, custom_id="store_select_menu")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        selected_option = self.values[0]
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        prefix = "🔄-trade" if "Trade" in selected_option else "🪙-buy-crypto"
        ticket_channel = await guild.create_text_channel(name=f"{prefix}-{member.name}", category=interaction.channel.category, overwrites=overwrites)
        await interaction.response.send_message(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)
        
        embed = discord.Embed(title=f"🎯 Section: {selected_option}", color=discord.Color.red())
        
        if "Browse" in selected_option:
            embed.description = (
                f"Welcome {member.mention} to **LTB Global Store**.\n\n"
                "ℹ️ **How to preview accounts:**\n"
                "Simply type the **Account ID** directly in this chat (e.g., `23`) and the bot will load the images immediately.\n\n"
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
            
        embed.set_footer(text="LTB Global Store System")
        await ticket_channel.send(content=f"Welcome {member.mention}", embed=embed, view=TicketControlView())


class MainStoreView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StoreDropdown())


@bot.event
async def on_message(message):
    if message.author.bot: return

    # 📥 روم إدارة رفع صور الحسابات من قبل الإدارة
    if message.channel.id == ADMIN_UPLOAD_CHANNEL_ID:
        folder_name = message.content.strip()
        if not folder_name or not message.attachments: return

        status_msg = await message.channel.send(f"🔄 Uploading images for account (**{folder_name}**)...")
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

    # 🔍 مراقبة تذاكر المشتريات وجلب المعاينات مع التقاط لقطة الشاشة وتحديث اللوج تلقائياً
    if any(prefix in message.channel.name for prefix in ["ticket-", "closed-", "trade-", "buy-"]):
        
        # 📸 تتبع ذكي: إذا قام المشتري بإرسال الصورة (إثبات الدفع) داخل التكت
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
                        # بناء الـ Embed الجديد وتضمين صورة الوصل داخل رسالة الشوب لوج في الإدارة مباشرة
                        embed_updated = discord.Embed(title="⏳ Transaction Proof Received / تم استقبال الدليل", color=discord.Color.blue())
                        embed_updated.add_field(name="👤 Buyer / المشتري", value=message.author.mention, inline=True)
                        embed_updated.add_field(name="📦 Account ID / رقم السلعة", value=f"`{account_id}`", inline=True)
                        embed_updated.add_field(name="🎫 Ticket Location / روم التكت", value=message.channel.mention, inline=False)
                        embed_updated.description = "✅ **The user has uploaded the proof image below!** Review it, verify your Trust Wallet, and take action.\nالعضو قام برفع صورة الدليل بالأسفل! تحقق من حسابك ثم تحكم بالطلب."
                        embed_updated.set_image(url=first_attachment.url)
                        embed_updated.set_footer(text="Global Proof Log System • LTB Store")
                        
                        await log_message.edit(embed=embed_updated)
                        await message.channel.send("✅ **Your payment proof has been submitted to the administration team.**\n✅ تم إرسال دليل الدفع بنجاح للإدارة للتحقق والتسليم.")
                    except: pass

        search_target = message.content.strip()
        if search_target.isdigit():
            # ⏱️ نظام التهدئة (5 ثوانٍ لحماية البوت)
            user_id = message.author.id
            current_time = asyncio.get_event_loop().time()
            if user_id in user_cooldowns:
                time_passed = current_time - user_cooldowns[user_id]
                if time_passed < 5.0:
                    try: await message.delete()
                    except: pass
                    return
            
            user_cooldowns[user_id] = current_time

            waiting_msg = await message.channel.send(f"🔄 Loading images for Account ID (**{search_target}**)...")
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
                    await message.channel.send(f"━━━━━━━━━━━━━━━━━━━━━\n📦 **Account ID: ({target_folder_name})**\n━━━━━━━━━━━━━━━━━━━━━")
                    for img_name in images:
                        img_path = os.path.join(folder_path, img_name)
                        try:
                            with open(img_path, 'rb') as f:
                                await message.channel.send(file=discord.File(f))
                        except: pass
                    
                    # 📊 إرسال رسالة اللوج الأولى بانتظار الدليل
                    log_channel = bot.get_channel(ADMIN_LOG_CHANNEL_ID)
                    if log_channel:
                        embed_pending = discord.Embed(title="⏳ Pending Transaction / معاملة معلقة", color=discord.Color.orange())
                        embed_pending.add_field(name="👤 Buyer / العضو المشتري", value=message.author.mention, inline=True)
                        embed_pending.add_field(name="📦 Account ID / رقم السلعة", value=f"`{target_folder_name}`", inline=True)
                        embed_pending.add_field(name="🎫 Ticket Location / التكت", value=message.channel.mention, inline=False)
                        embed_pending.description = "⏳ **Waiting for Payment Proof Screenshot...**\nالزبون يستعرض الحساب حالياً، وبانتظار قيامه برفع صورة الدليل لتظهر هنا تلقائياً."
                        embed_pending.set_footer(text="Global Pending Log System • LTB Store")
                        
                        log_msg = await log_channel.send(
                            embed=embed_pending, 
                            view=AdminApprovalView(buyer_id=message.author.id, account_num=target_folder_name, ticket_channel_id=message.channel.id)
                        )
                        # ربط التكت بالذاكرة لتحديث هذه الرسالة بالتحديد بمجرد استقبال الدليل
                        active_transactions[message.channel.id] = {
                            "log_msg_id": log_msg.id,
                            "account_id": target_folder_name
                        }
                else:
                    await message.channel.send(f"❌ Folder **{target_folder_name}** is empty.")
            else:
                await message.channel.send(f"❌ Account ID **{search_target}** not found.")
            
            try:
                await message.delete()
                await waiting_msg.delete()
            except: pass

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"⚡ LTB Multi-Wallet & Auto-Proof Bot is Connected!")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    bot.add_view(MainStoreView())
    bot.add_view(TicketControlView())
    bot.add_view(TicketDeleteView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(
        title="🛒 LTB Global Crypto & Barter Marketplace",
        description=(
            "Welcome to the main digital assets desk 🪙.\n\n"
            "🔽 **Please select your destination from the dropdown below:**\n"
            "The bot will instantly open a secured ticket for account preview or trade deals."
        ),
        color=discord.Color.red()
    )
    embed.set_image(url="https://images.unsplash.com/photo-1612287230202-1bf1d85d1bdf?q=80&w=1000")
    embed.set_footer(text="LTB International • Secure Trading Hub")
    await ctx.send(embed=embed, view=MainStoreView())

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN: bot.run(TOKEN)