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
    return "LTB Crypto Store Bot with Advanced Logs & Cooldown is Online!"

def run_http_server():
    app.run(host='0.0.0.0', port=8080)

# قراءة التوكن المشفر من إعدادات بيئة Render
TOKEN = os.getenv("DISCORD_TOKEN")
ACCOUNTS_DIR = "./" 

# 🔒 إعدادات الأيدي الثابتة للرومات لمنع التداخل
ADMIN_UPLOAD_CHANNEL_ID = 1505753282755170324
ADMIN_LOG_CHANNEL_ID = 1506320607032381581  # روم السجل الإداري الخاص بك

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# قاموس لتخزين أوقات آخر رسالة لكل مستخدم (نظام التهدئة)
user_cooldowns = {}

# دالة مساعدة لإرسال السجلات الإدارية تلقائياً
async def send_log(title, description, color=discord.Color.blue()):
    log_channel = bot.get_channel(ADMIN_LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="نظام الرقابة والسجلات التلقائي • LTB")
        await log_channel.send(embed=embed)

# 🗑️ واجهة التحكم بعد إغلاق التذكرة (تظهر للإدارة فقط)
class TicketDeleteView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="حذف التكت نهائياً 🗑️", style=discord.ButtonStyle.danger, custom_id="delete_ticket_btn")
    async def delete_ticket(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            await interaction.response.send_message("⚠️ **تنبيه:** سيتم حذف هذه التذكرة وتنظيف السيرفر خلال **5 ثوانٍ**...")
            
            # إرسال سجل إداري بالبند قبل الحذف
            await send_log(
                "🗑️ تصفية وحذف تذكرة", 
                f"قام المسؤول {interaction.user.mention} بحذف التذكرة الحالية: **{interaction.channel.name}** نهائياً.",
                discord.Color.red()
            )
            
            await asyncio.sleep(5)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("❌ عذراً، هذا الزر مخصص لأعضاء الإدارة والمشرفين فقط!", ephemeral=True)


# 💳 واجهة التحكم أثناء عمل التذكرة (شراء وإغلاق)
class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💰 طلب الدفع بالـ Crypto / المقايضة", style=discord.ButtonStyle.success, custom_id="buy_acc_btn")
    async def buy_account(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            f"🔔 {interaction.user.mention} يطلب إتمام الدفع بالعملات الرقمية الآن!\n"
            "👤 انتظر دخول المسؤول لتزويدك بـ **عنوان محفظة الاستقبال (USDT)** وفحص حساب المقايضة يداً بيد بسلام."
        )
        await send_log(
            "🔔 طلب دفع جديد",
            f"العضو {interaction.user.mention} ضغط على زر الشراء/المقايضة داخل تذكرته: {interaction.channel.mention}",
            discord.Color.green()
        )

    @discord.ui.button(label="🔒 إغلاق التذكرة", style=discord.ButtonStyle.secondary, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            await interaction.response.send_message("🔒 **تم قفل التذكرة بنجاح.**\n📥 جاري سحب صلاحيات العضو وتحويل الروم للوضع المغلق...")
            
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
            
            await send_log(
                "🔒 تجميد وقفل تذكرة",
                f"قام المسؤول {interaction.user.mention} بإغلاق التذكرة: {interaction.channel.mention} وسحب صلاحيات الكتابة.",
                discord.Color.orange()
            )
        else:
            await interaction.response.send_message("❌ عذراً، هذا الزر مخصص لأعضاء الإدارة والمشرفين فقط!", ephemeral=True)


# 🏪 القائمة المنسدلة الاحترافية في الروم الرئيسي للمتجر (معدلة حسب طلبك الجديد)
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
        
        prefix = "تذكرة"
        if "مقايضة" in selected_option: prefix = "🔄-مقايضة"
        else: prefix = "🪙-شراء-كريبتو"
        
        ticket_channel = await guild.create_text_channel(name=f"{prefix}-{member.name}", category=interaction.channel.category, overwrites=overwrites)
        await interaction.response.send_message(f"✅ تم فتح تذكرتك بنجاح في قسم ({selected_option}): {ticket_channel.mention}", ephemeral=True)
        
        embed = discord.Embed(
            title=f"🎯 قسم: {selected_option}",
            color=discord.Color.red()
        )
        
        if "معاينة" in selected_option:
            embed.description = (
                f"أهلاً بك {member.mention} في قسم المعاينة الذكي والدفع الرقمي.\n\n"
                "ℹ️ **طريقة الاستعراض الفوري:**\n"
                "اكتب **رقم الحساب** المراد استعراضه هنا في الشات مباشرة (مثال: `23`) وسيقوم البوت بجلب صوره فوراً.\n\n"
                "🪙 **طرق الدفع العالمية المدعومة وبقوة:**\n"
                "• الدفع عبر العملات الرقمية المشرة: **USDT (TRC20 / BEP20)**.\n"
                "• نظام آمن ومباشر لحفظ وتجميع رصيدك الدولي."
            )
        else:
            embed.description = (
                f"أهلاً بك {member.mention} في قسم المقايضة الفوري والآمن للبطاقات والحسابات.\n\n"
                "📝 **الأشياء التي نقبل المقايضة بها حالياً:**\n"
                "• حسابات لعبة **eFootball (بيس)** ذات مستويات وسكنات عالية وقوية.\n"
                "• بطاقات هدايا الشحن ومشتريات موقع **AliExpress Gift Cards** الفعالة دولياً.\n\n"
                "⚠️ جهز بياناتك والأكواد بانتظار دخول الإدارة لمراجعة العرض وتسليمك طلبك."
            )
            
        embed.set_footer(text="نظام المتجر الدولي المطور • LTB")
        await ticket_channel.send(content=f"مرحباً بك {member.mention} في تذكرتك المخصصة.", embed=embed, view=TicketControlView())

        # تسجيل فتح التكت في روم السجلات الإدارية
        await send_log(
            "🎫 فتح تذكرة جديدة",
            f"قام العضو {member.mention} بفتح تذكرة جديدة باسم {ticket_channel.mention} في قسم: **{selected_option}**.",
            discord.Color.blue()
        )


class MainStoreView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StoreDropdown())


@bot.event
async def on_message(message):
    if message.author.bot: return

    # 📥 أولاً: الفحص عن طريق الـ ID الصارم للروم المخصصة للإدارة
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
            await status_msg.edit(content=f"✅ تم بنجاح إنشاء الحساب رقم (**{folder_name}**) وحفظ عدد ({success_count}) صور داخله! جاهز للمعاينة الفورية الآن.")
            await send_log("📥 رفع سلع جديدة للمخزن", f"تم إنشاء مجلد حساب جديد بالرقم: (**{folder_name}**) وتم شحن عدد ({success_count}) صور داخله بنجاح عبر الإدارة.", discord.Color.purple())
        else:
            await status_msg.edit(content="❌ فشل تحميل الصور. تأكد من أن الملفات المرفقة هي صور فقط.")
        return

    # 🔍 ثانياً: نظام جلب ومعاينة الحسابات ونظام التهدئة (Cooldown) داخل التذاكر
    if any(prefix in message.channel.name for prefix in ["تذكرة-", "🔒-مغلقة-", "مقايضة-", "شراء-"]):
        search_target = message.content.strip()
        
        if search_target.isdigit():
            # ⏱️ تطبيق نظام التهدئة (5 ثوانٍ بين الرسائل لحماية البوت)
            user_id = message.author.id
            current_time = asyncio.get_event_loop().time()
            if user_id in user_cooldowns:
                time_passed = current_time - user_cooldowns[user_id]
                if time_passed < 5.0:
                    try:
                        await message.delete()
                    except: pass
                    warn_msg = await message.channel.send(f"⚠️ {message.author.mention}، يرجى التمهل! هناك نظام حماية يمنع إرسال الأرقام بكثافة (انتظر {int(5.0 - time_passed)} ثانية).")
                    await asyncio.sleep(3)
                    try:
                        await warn_msg.delete()
                    except: pass
                    return
            
            # تحديث وقت آخر رسالة للمستخدم
            user_cooldowns[user_id] = current_time

            waiting_msg = await message.channel.send(f"🔄 جاري البحث وجلب صور الحساب رقم (**{search_target}**)... يرجى الانتظار.")
            try:
                all_items = os.listdir(ACCOUNTS_DIR)
            except Exception as e:
                await message.channel.send(f"❌ خطأ في الوصول لمجلدات النظام: {e}")
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
                except Exception as e:
                    await message.channel.send(f"❌ خطأ في قراءة ملفات المجلد: {e}")
                    return

                if images:
                    await message.channel.send(f"━━━━━━━━━━━━━━━━━━━━━\n📦 **صور الحساب رقم: ({target_folder_name})**\n━━━━━━━━━━━━━━━━━━━━━")
                    for img_name in images:
                        img_path = os.path.join(folder_path, img_name)
                        try:
                            with open(img_path, 'rb') as f:
                                await message.channel.send(file=discord.File(f))
                        except Exception as e:
                            print(f"خطأ في إرسال الصورة: {e}")
                    
                    # تسجيل عملية البحث الناجحة
                    await send_log("🔍 عملية معاينة سلع", f"قام العضو {message.author.mention} باستعراض صور الحساب رقم: (**{target_folder_name}**) داخل القناة {message.channel.mention}")
                else:
                    await message.channel.send(f"❌ المجلد **{target_folder_name}** فارغ من الصور.")
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
    print(f"⚡ بوت الكريبتو الدولي جاهز ومتصل، ومربوط بروم السجلات {ADMIN_LOG_CHANNEL_ID}!")
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
    embed.set_footer(text="متجر LTB الدولي • خيارك الآمن للمستقبل الرقمي")
    await ctx.send(embed=embed, view=MainStoreView())

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ خطأ: لم يتم العثور على التوكن!")