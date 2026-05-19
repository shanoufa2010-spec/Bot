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
    return "LTB Pro Store Bot with Advanced Ticket Management is Online!"

def run_http_server():
    app.run(host='0.0.0.0', port=8080)

# قراءة التوكن المشفر من إعدادات بيئة Render
TOKEN = os.getenv("DISCORD_TOKEN")
ACCOUNTS_DIR = "./" 

# 🔒 الاعتماد على الأيدي الثابت للروم لمنع أي تداخل أو أخطاء
ADMIN_UPLOAD_CHANNEL_ID = 1505753282755170324

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 🗑️ واجهة التحكم بعد إغلاق التذكرة (تظهر للإدارة فقط)
class TicketDeleteView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="حذف التكت نهائياً 🗑️", style=discord.ButtonStyle.danger, custom_id="delete_ticket_btn")
    async def delete_ticket(self, interaction: discord.Interaction, button: Button):
        # التحقق من صلاحيات المشرف
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            await interaction.response.send_message("⚠️ **تنبيه:** سيتم حذف هذه التذكرة وتنظيف السيرفر خلال **5 ثوانٍ**...")
            await asyncio.sleep(5)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("❌ عذراً، هذا الزر مخصص لأعضاء الإدارة والمشرفين فقط!", ephemeral=True)


# 💳 واجهة التحكم أثناء عمل التذكرة (شراء وإغلاق)
class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💳 طلب شراء / مقايضة فوري", style=discord.ButtonStyle.danger, custom_id="buy_acc_btn")
    async def buy_account(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            f"🔔 {interaction.user.mention} يطلب إتمام العملية الآن!\n"
            "👤 سيقوم أحد المشرفين بالرد عليك فوراً لتسليمك حسابك، أو مراجعة حساب المقايضة الخاص بك وبطاقات الشحن بسلام."
        )

    @discord.ui.button(label="🔒 إغلاق التذكرة", style=discord.ButtonStyle.secondary, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            await interaction.response.send_message("🔒 **تم قفل التذكرة بنجاح.**\n📥 جاري سحب صلاحيات العضو وتحويل الروم للوضع المغلق...")
            
            # تغيير اسم الروم
            try:
                await interaction.channel.edit(name=f"🔒-مغلقة-{interaction.channel.name}")
            except: pass

            # سحب صلاحيات الكتابة من الجميع باستثناء الإدارة
            for overwrite in interaction.channel.overwrites:
                if isinstance(overwrite, discord.Member) and not overwrite.bot:
                    await interaction.channel.set_permissions(overwrite, read_messages=True, send_messages=False)
            
            # إرسال رسالة زر الحذف النهائي الجديد للإدارة
            embed_delete = discord.Embed(
                title="⚙️ لوحة تحكم الأرشفة والتنظيف",
                description="تم إنهاء المعاملة وتجميد الشات. اضغط على الزر أدناه لمسح القناة نهائياً من السيرفر.",
                color=discord.Color.dark_gray()
            )
            await interaction.channel.send(embed=embed_delete, view=TicketDeleteView())
        else:
            await interaction.response.send_message("❌ عذراً، هذا الزر مخصص لأعضاء الإدارة والمشرفين فقط!", ephemeral=True)


# 🏪 القائمة المنسدلة الاحترافية في الروم الرئيسي للمتجر
class StoreDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="معاينة وشراء حسابات ألعاب", description="تصفح حسابات ستيم، فورتنايت وغيرها بالرقم", emoji="🛒"),
            discord.SelectOption(label="طلب مقايضة (حسابات بيس / جيفت كارد)", description="لمقايضة حسابك أو الشراء ببطاقات علي إكسبريس", emoji="🔄"),
            discord.SelectOption(label="خدمات تسريع حواسب (PC Optimization)", description="لرفع الفريمات وويندوز LTSC للألعاب", emoji="⚡"),
        ]
        super().__init__(placeholder="🔽 اختر القسم المناسب لفتح تذكرة...", min_values=1, max_values=1, options=options, custom_id="store_select_menu")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        selected_option = self.values[0]
        
        # إنشاء الصلاحيات للتكت
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # تسمية الروم بناءً على الخيار المحدد ليكون منظم جداً
        prefix = "تذكرة"
        if "مقايضة" in selected_option: prefix = "🔄-مقايضة"
        elif "تسريع" in selected_option: prefix = "⚡-تحسين-فريمات"
        
        ticket_channel = await guild.create_text_channel(name=f"{prefix}-{member.name}", category=interaction.channel.category, overwrites=overwrites)
        await interaction.response.send_message(f"✅ تم فتح تذكرتك بنجاح في قسم ({selected_option}): {ticket_channel.mention}", ephemeral=True)
        
        # تخصيص رسالة الـ Embed بناءً على طلب المشتري لإعطاء لمسة فخمة
        embed = discord.Embed(
            title=f"🎯 قسم: {selected_option}",
            color=discord.Color.red()
        )
        
        if "معاينة" in selected_option:
            embed.description = (
                f"أهلاً بك {member.mention} في قسم المعاينة الذكي الخاص بـ **LTB Store**.\n\n"
                "ℹ️ **طريقة الاستعراض الفوري:**\n"
                "اكتب **رقم الحساب** المراد استعراضه هنا في الشات مباشرة (مثال: `23`) وسيقوم البوت بجلب صوره فوراً.\n\n"
                "💳 **طرق الدفع المدعومة بأمان:**\n"
                "• تحويل بريدي محلي (CCP الورقي).\n"
                "• رصيد هاتف فليكسي (Flexy) للمبالغ الصغيرة."
            )
        elif "مقايضة" in selected_option:
            embed.description = (
                f"أهلاً بك {member.mention} في قسم المقايضة الموثوق.\n\n"
                "📝 **الشروط والقوانين لضمان حقك:**\n"
                "• نحن نقبل المقايضة بحسابات **eFootball (بيس)** ليفل عالي، أو بطاقات هدايا **AliExpress Gift Cards** دولية مسبقة الدفع.\n"
                "• يرجى تجهيز معلومات حسابك أو كود البطاقة بانتظار دخول المشرف لفحصه وتأكيده يدوياً يداً بيد."
            )
        else:
            embed.description = (
                f"أهلاً بك {member.mention} في قسم صيانة ورفع كفاءة الحواسب والألعاب.\n\n"
                "⚙️ **الخدمات المتوفرة حالياً:**\n"
                "• تحسين الفريمات وإزالة اللاق (PC Optimization Tweaks).\n"
                "• توجيهك لتحميل وتثبيت ويندوز 10 LTSC الأسرع للألعاب.\n\n"
                "👤 انتظر دخول المشرف لمساعدتك خطوة بخطوة عبر تطبيقات التحكم (AnyDesk)."
            )
            
        embed.set_footer(text="نظام المتجر الاحترافي المطور • LTB")
        await ticket_channel.send(content=f"مرحباً بك {member.mention} في تذكرتك المخصصة.", embed=embed, view=TicketControlView())


class MainStoreView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StoreDropdown()) # دمج القائمة المنسدلة في الفيو الرئيسي


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
        else:
            await status_msg.edit(content="❌ فشل تحميل الصور. تأكد من أن الملفات المرفقة هي صور فقط.")
        return

    # 🔍 ثانياً: نظام جلب ومعاينة الحسابات داخل التذاكر للزبائن
    if "تذكرة-" in message.channel.name or "🔒-مغلقة-" in message.channel.name or "مقايضة-" in message.channel.name or "فريمات-" in message.channel.name:
        search_target = message.content.strip()
        if search_target.isdigit():
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
    print(f"⚡ البوت المطور متصل ومزود بأزرار الحذف التلقائي والقائمة المنسدلة!")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    bot.add_view(MainStoreView())
    bot.add_view(TicketControlView())
    bot.add_view(TicketDeleteView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(
        title="🛒 إمبراطورية متجر LTB الاحترافي",
        description=(
            "مرحباً بك في المركز الرئيسي لخدمات المتجر الرقمي والمقايضة الآمنة بالكامل 🇩🇿.\n\n"
            "🔽 **الرجاء اختيار الخدمة المطلوبة من القائمة المنسدلة بالأسفل:**\n"
            "سيقوم البوت بفتح تذكرة خاصة ومنظمة لطلبك فوراً للتحدث مع الإدارة ومعاينة سلعك بخصوصية تامة."
        ),
        color=discord.Color.red()
    )
    embed.set_image(url="https://images.unsplash.com/photo-1612287230202-1bf1d85d1bdf?q=80&w=1000") # صورة فخمة لواجهة المتجر
    embed.set_footer(text="متجر LTB • جودة، أمان، وسرعة في المعاملات")
    await ctx.send(embed=embed, view=MainStoreView())

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ خطأ: لم يتم العثور على التوكن!")