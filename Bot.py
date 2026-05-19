import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
from threading import Thread
from flask import Flask
import asyncio

# خادم ويب مصغر لمنع وضع خمول السيرفر المجاني
app = Flask('')

@app.route('/')
def home():
    return "LTB Crypto Store Bot with Admin Approval System is Online!"

def run_http_server():
    app.run(host='0.0.0.0', port=8080)

# قراءة التوكن المشفر من إعدادات بيئة Render
TOKEN = os.getenv("DISCORD_TOKEN")
ACCOUNTS_DIR = "./" 

# 🔒 إعدادات الأيدي الثابتة للرومات (تأكد من مطابقتها لسيرفرك)
ADMIN_UPLOAD_CHANNEL_ID = 1505753282755170324
ADMIN_LOG_CHANNEL_ID = 1506320607032381581  # روم السجل الإداري والشوب لوج الخاص بك

# 🪙 ضع هنا عنوان محفظتك الشخصية ليرسلها البوت تلقائياً
CRYPTO_WALLET_ADDRESS = "ضع_عنوان_محفظتك_هنا_USDT_TRC20"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

user_cooldowns = {}

# 📊 واجهة التحكم والموافقة داخل روم السجل الإداري (خاصة بالملّاك فقط)
class AdminApprovalView(View):
    def __init__(self, buyer_id, account_num, ticket_channel_id):
        super().__init__(timeout=None)
        self.buyer_id = buyer_id
        self.account_num = account_num
        self.ticket_channel_id = ticket_channel_id

    @discord.ui.button(label="✅ موافقة وتسليم الحساب", style=discord.ButtonStyle.success, custom_id="approve_sale_btn")
    async def approve_sale(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            await interaction.response.defer()
            
            buyer = await bot.fetch_user(self.buyer_id)
            ticket_channel = bot.get_channel(self.ticket_channel_id)
            
            # تحديث رسالة السجل الإداري (شوب لوج كامل في رسالة واحدة)
            embed_log = discord.Embed(title="✅ تقرير بيع ناجح (تم التسليم)", color=discord.Color.green())
            embed_log.add_field(name="👤 المشتري", value=f"<@{self.buyer_id}>", inline=True)
            embed_log.add_field(name="📦 رقم السلعة", value=f"`{self.account_num}`", inline=True)
            embed_log.add_field(name="🛠️ المسؤول المعتمد", value=interaction.user.mention, inline=False)
            embed_log.set_footer(text="نظام الشوب لوج المطور • LTB Store")
            await interaction.message.edit(embed=embed_log, view=None)

            # إرسال إشعار للمشتري داخل التكت
            if ticket_channel:
                embed_buyer = discord.Embed(
                    title="🎉 تم تأكيد الدفع بنجاح!",
                    description=f"مرحباً <@{self.buyer_id}>، تم التحقق من تحويل الكريبتو الخاص بك بنجاح.\n👤 سيقوم المسؤول بتسليمك بيانات الحساب رقم (**{self.account_num}**) الآن داخل الشات.",
                    color=discord.Color.green()
                )
                await ticket_channel.send(content=f"<@{self.buyer_id}>", embed=embed_buyer)
        else:
            await interaction.response.send_message("❌ عذراً، هذا الإجراء مخصص للإدارة العليا فقط!", ephemeral=True)

    @discord.ui.button(label="❌ رفض الطلب (إلغاء)", style=discord.ButtonStyle.danger, custom_id="deny_sale_btn")
    async def deny_sale(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            await interaction.response.defer()
            
            ticket_channel = bot.get_channel(self.ticket_channel_id)
            
            embed_log = discord.Embed(title="❌ تقرير طلب مرفوض / ملغى", color=discord.Color.red())
            embed_log.add_field(name="👤 المشتري المستهدف", value=f"<@{self.buyer_id}>", inline=True)
            embed_log.add_field(name="📦 رقم السلعة", value=f"`{self.account_num}`", inline=True)
            embed_log.add_field(name="⚠️ الرافض", value=interaction.user.mention, inline=False)
            embed_log.set_footer(text="نظام الشوب لوج المطور • LTB Store")
            await interaction.message.edit(embed=embed_log, view=None)

            if ticket_channel:
                await ticket_channel.send(f"⚠️ <@{self.buyer_id}>، تم رفض طلب الدفع الحالي من قبل الإدارة. يرجى مراجعة المسؤول أو إعادة إرسال دليل دفع صحيح.")
        else:
            await interaction.response.send_message("❌ عذراً، هذا الإجراء مخصص للإدارة العليا فقط!", ephemeral=True)


# 🗑️ واجهة التحكم بعد إغلاق التذكرة
class TicketDeleteView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="حذف التكت نهائياً 🗑️", style=discord.ButtonStyle.danger, custom_id="delete_ticket_btn")
    async def delete_ticket(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            await interaction.response.send_message("⚠️ **تنبيه:** سيتم حذف هذه التذكرة وتنظيف السيرفر خلال **5 ثوانٍ**...")
            await asyncio.sleep(5)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("❌ عذراً، هذا الزر مخصص لأعضاء الإدارة والمشرفين فقط!", ephemeral=True)


# 💳 واجهة التحكم داخل التذكرة (إرسال المحفظة أوتو)
class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💰 إظهار محفظة الكريبتو التلقائية", style=discord.ButtonStyle.success, custom_id="buy_acc_btn")
    async def buy_account(self, interaction: discord.Interaction, button: Button):
        # إرسال المحفظة تلقائياً للزبون بناءً على رغبتك
        embed_wallet = discord.Embed(
            title="🪙 تفاصيل الدفع التلقائي بالـ USDT",
            description=(
                f"يرجى تحويل قيمة الحساب المتفق عليها إلى العنوان التالي:\n\n"
                f"📌 **عنوان المحفظة (Network: TRC20):**\n`{CRYPTO_WALLET_ADDRESS}`\n\n"
                "⚠️ **خطوة هامة جداً:**\n"
                "بعد إتمام التحويل من حسابك، قم بتصوير **وصل إثبات الدفع (Screenshot)** وإرساله هنا في الشات فوراً، ثم انتظر تأكيد الإدارة وسحب السجل المالي."
            ),
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed_wallet)

    @discord.ui.button(label="🔒 إغلاق التذكرة", style=discord.ButtonStyle.secondary, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            await interaction.response.send_message("🔒 **تم قفل التذكرة بنجاح.**\n📥 جاري سحب صلاحيات العضو...")
            try:
                await interaction.channel.edit(name=f"🔒-مغلقة-{interaction.channel.name}")
            except: pass

            for overwrite in interaction.channel.overwrites:
                if isinstance(overwrite, discord.Member) and not overwrite.bot:
                    await interaction.channel.set_permissions(overwrite, read_messages=True, send_messages=False)
            
            embed_delete = discord.Embed(
                title="⚙️ لوحة تحكم الأرشفة والتنظيف",
                description="تم إنهاء المعاملة وتجميد الشات. اضغط على الزر أدناه لمسح القناة نهائياً من السيرفر.",
                color=discord.Color.dark_gray()
            )
            await interaction.channel.send(embed=embed_delete, view=TicketDeleteView())
        else:
            await interaction.response.send_message("❌ عذراً، هذا الزر مخصص لأعضاء الإدارة والمشرفين فقط!", ephemeral=True)


# 🏪 القائمة المنسدلة في الروم الرئيسي للمتجر
class StoreDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="معاينة وشراء حسابات ألعاب (Crypto)", description="تصفح الحسابات بالرقم والدفع بالعملات الرقمية", emoji="🪙"),
            discord.SelectOption(label="طلب مقايضة (حسابات بيس / جيفت كارد)", description="لمقايضة حسابك أو الدفع ببطاقات AliExpress", emoji="🔄"),
        ]
        super().__init__(placeholder="🔽 اختر القسم المناسب لفتح تذكرة...", min_values=1, max_values=1, options=options, custom_id="store_select_menu")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        selected_option = self.values[0]
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        prefix = "🔄-مقايضة" if "مقايضة" in selected_option else "🪙-شراء-كريبتو"
        ticket_channel = await guild.create_text_channel(name=f"{prefix}-{member.name}", category=interaction.channel.category, overwrites=overwrites)
        await interaction.response.send_message(f"✅ تم فتح تذكرتك بنجاح: {ticket_channel.mention}", ephemeral=True)
        
        embed = discord.Embed(title=f"🎯 قسم: {selected_option}", color=discord.Color.red())
        
        if "معاينة" in selected_option:
            embed.description = (
                f"أهلاً بك {member.mention} في قسم المعاينة والدفع بالعملات المشفرة.\n\n"
                "ℹ️ **طريقة الاستعراض الفوري:**\n"
                "اكتب **رقم الحساب** المراد استعراضه هنا في الشات مباشرة (مثال: `23`) وسيجلب البوت صوره فوراً.\n\n"
                "🪙 اضغط على الزر الأخضر بالأسفل لعرض عنوان محفظة الاستقبال المباشرة عند استقرارك على حساب."
            )
        else:
            embed.description = (
                f"أهلاً بك {member.mention} في قسم المقايضة الفوري للحسابات والبطاقات.\n\n"
                "📝 **الأشياء المقبولة حالياً:**\n"
                "• حسابات لعبة **eFootball (بيس)** ليفل وسكنات عالية قوية.\n"
                "• بطاقات شحن ومشتريات موقع **AliExpress Gift Cards** الفعالة دولياً.\n\n"
                "⚠️ ارسل بياناتك وصور عرضك بانتظار دخول المسؤول لفحصها والمقايضة يدوياً."
            )
            
        embed.set_footer(text="نظام المتجر الدولي المطور • LTB")
        await ticket_channel.send(content=f"مرحباً بك {member.mention}", embed=embed, view=TicketControlView())


class MainStoreView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StoreDropdown())


@bot.event
async def on_message(message):
    if message.author.bot: return

    # 📥 روم إدارة رفع الصور
    if message.channel.id == ADMIN_UPLOAD_CHANNEL_ID:
        folder_name = message.content.strip()
        if not folder_name or not message.attachments: return

        status_msg = await message.channel.send(f"🔄 جاري إنشاء المجلد (**{folder_name}**) وتحميل الصور...")
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
                except Exception as e:
                    await message.channel.send(f"❌ فشل حفظ الصورة {attachment.filename}: {e}")

        if success_count > 0:
            await status_msg.edit(content=f"✅ تم بنجاح إنشاء الحساب رقم (**{folder_name}**) وحفظ عدد ({success_count}) صور داخله!")
        else:
            await status_msg.edit(content="❌ فشل تحميل الصور.")
        return

    # 🔍 معاينة الحسابات ونظام التحقق والتهدئة وبناء تقارير الـ Shop Log المعلقة
    if any(prefix in message.channel.name for prefix in ["تذكرة-", "🔒-مغلقة-", "مقايضة-", "شراء-"]):
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
                    warn_msg = await message.channel.send(f"⚠️ {message.author.mention}، يرجى الانتظار {int(5.0 - time_passed)} ثانية قبل طلب حساب آخر.")
                    await asyncio.sleep(3)
                    try: await warn_msg.delete()
                    except: pass
                    return
            
            user_cooldowns[user_id] = current_time

            waiting_msg = await message.channel.send(f"🔄 جاري البحث وجلب صور الحساب رقم (**{search_target}**)... يرجى الانتظار.")
            try:
                all_items = os.listdir(ACCOUNTS_DIR)
            except Exception as e:
                await message.channel.send(f"❌ خطأ في النظام: {e}")
                return

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
                    await message.channel.send(f"━━━━━━━━━━━━━━━━━━━━━\n📦 **صور الحساب رقم: ({target_folder_name})**\n━━━━━━━━━━━━━━━━━━━━━")
                    for img_name in images:
                        img_path = os.path.join(folder_path, img_name)
                        try:
                            with open(img_path, 'rb') as f:
                                await message.channel.send(file=discord.File(f))
                        except: pass
                    
                    # 📊 إرسال تقرير شوب لوج معلق في رسالة واحدة منسقة مع أزرار التحكم للإدارة
                    log_channel = bot.get_channel(ADMIN_LOG_CHANNEL_ID)
                    if log_channel:
                        embed_pending = discord.Embed(title="⏳ تقرير معاملة معلقة (بانتظار المراجعة)", color=discord.Color.orange())
                        embed_pending.add_field(name="👤 العضو المشتري", value=message.author.mention, inline=True)
                        embed_pending.add_field(name="📦 رقم السلعة المطلوبة", value=f"`{target_folder_name}`", inline=True)
                        embed_pending.add_field(name="🎫 موقع التذكرة", value=message.channel.mention, inline=False)
                        embed_pending.description = "الزبون يستعرض الصور حالياً. راجع محفظتك وتأكد من وصول الدفع والوصل، ثم اضغط على الأزرار بالأسفل للتحكم بالتسليم."
                        embed_pending.set_footer(text="نظام الشوب لوج المعلق • LTB Store")
                        
                        await log_channel.send(
                            embed=embed_pending, 
                            view=AdminApprovalView(buyer_id=message.author.id, account_num=target_folder_name, ticket_channel_id=message.channel.id)
                        )
                else:
                    await message.channel.send(f"❌ المجلد **{target_folder_name}** فارغ.")
            else:
                await message.channel.send(f"❌ لم يتم العثور على حساب يحمل الرقم **{search_target}**.")
            
            try:
                await message.delete()
                await waiting_msg.delete()
            except: pass

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"⚡ بوت الموافقة الشامل متصل ومربوط بالروم {ADMIN_LOG_CHANNEL_ID}!")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    bot.add_view(MainStoreView())
    bot.add_view(TicketControlView())
    bot.add_view(TicketDeleteView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(
        title="🛒 إمبراطورية متجر LTB للمقايضة والكريبتو الدولي",
        description=(
            "مرحباً بك في المنصة المخصصة للشراء بالعملات الرقمية والمقايضة الآمنة 🪙.\n\n"
            "🔽 **الرجاء تحديد طلبك بدقة من القائمة المنسدلة بالأسفل:**\n"
            "سيقوم البوت بفتح تذكرة مستقلة ومشفرة لتصفح حسابات الألعاب أو الاتفاق على المقايضات بخصوصية تامة."
        ),
        color=discord.Color.red()
    )
    embed.set_image(url="https://images.unsplash.com/photo-1612287230202-1bf1d85d1bdf?q=80&w=1000")
    embed.set_footer(text="متجر LTB الدولي • نظام تحكم يدوي آمن")
    await ctx.send(embed=embed, view=MainStoreView())

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN: bot.run(TOKEN)