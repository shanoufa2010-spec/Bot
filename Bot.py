import discord
from discord.ext import commands
from discord.ui import Button, View
import os
from threading import Thread
from flask import Flask

# خادم ويب مصغر لمنع وضع خمول السيرفر المجاني
app = Flask('')

@app.route('/')
def home():
    return "LTB Store Bot with Admin Upload is Online!"

def run_http_server():
    app.run(host='0.0.0.0', port=8080)

# قراءة التوكن المشفر من إعدادات بيئة Render
TOKEN = os.getenv("DISCORD_TOKEN")
ACCOUNTS_DIR = "./" 

# 🛠️ اسم الروم المخفية المخصصة للإدارة لإضافة الحسابات (يمكنك تغيير الاسم كما تحب)
ADMIN_UPLOAD_CHANNEL_NAME = "إضافة-الحسابات"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💳 طلب شراء الحساب", style=discord.ButtonStyle.danger, custom_id="buy_acc_btn")
    async def buy_account(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(f"🔔 {interaction.user.mention} يطلب شراء حساب الآن! سيقوم أحد المشرفين بالرد عليك فوراً لتسليمك طرق الدفع.")

    @discord.ui.button(label="🔒 إغلاق التذكرة (للإدارة)", style=discord.ButtonStyle.secondary, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if interaction.user.guild_permissions.manage_channels or any(role.name in ["Mega Owner", "Sellers Leader"] for role in interaction.user.roles):
            await interaction.response.send_message("🔒 جاري إغلاق التذكرة وأرشفة الروم...")
            await interaction.channel.edit(name=f"🔒-مغلقة-{interaction.channel.name}")
            for overwrite in interaction.channel.overwrites:
                if isinstance(overwrite, discord.Member):
                    await interaction.channel.set_permissions(overwrite, read_messages=True, send_messages=False)
        else:
            await interaction.response.send_message("❌ عذراً، هذا الزر مخصص لأعضاء الإدارة والمشرفين فقط!", ephemeral=True)

class MainStoreView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 فتح تذكرة معاينة وشراء", style=discord.ButtonStyle.danger, custom_id="open_main_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        member = interaction.user
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        ticket_channel = await guild.create_text_channel(name=f"تذكرة-{member.name}", category=interaction.channel.category, overwrites=overwrites)
        await interaction.response.send_message(f"✅ تم فتح تذكرتك بنجاح: {ticket_channel.mention}", ephemeral=True)
        
        embed = discord.Embed(
            title="🎯 قسم معاينة الحسابات المتوفرة",
            description=(
                f"أهلاً بك {member.mention} في قسم المعاينة الخاص بـ **LTB Store**.\n\n"
                "ℹ️ **طريقة الاستعراض الفوري:**\n"
                "كل ما عليك فعله الآن هو **كتابة رقم الحساب** الذي ترغب في استعراضه هنا في الشات مباشرة (مثال: `23` أو `54`) وسيقوم النظام التلقائي برفه صوره ومواصفاته لك فوراً.\n\n"
                "⚠️ **قوانين وشروط التذكرة (عدم الإزعاج):**\n"
                "• يُمنع كتابة أرقام عشوائية متتالية بشكل سريع لتجنب حظر البوت الفوري.\n"
                "• يُرجى كتابة الرقم المُراد معاينته فقط في الرسالة دون أي نصوص جانبية.\n"
                "• بعد الاستقرار على الحساب المناسب، اضغط على زر الشراء بالأسفل لتنبيه المشرف.\n\n"
                "⚙️ *الأزرار بالأسفل مخصصة لتسهيل طلبك وإنهاء عملية الشراء.*"
            ),
            color=discord.Color.red()
        )
        embed.set_footer(text="نظام المعاينة التلقائي والمؤمن • LTB")
        await ticket_channel.send(content=f"مرحباً بك {member.mention}", embed=embed, view=TicketControlView())

@bot.event
async def on_message(message):
    if message.author.bot: return

    # 📥 أولاً: نظام إضافة الحسابات الذكي من الروم المخفية
    if ADMIN_UPLOAD_CHANNEL_NAME in message.channel.name:
        folder_name = message.content.strip()
        
        # التأكد من أن المشرف كتب رقم أو اسم للمجلد وأنه أرسل صوراً
        if not folder_name:
            return
            
        if not message.attachments:
            await message.channel.send("⚠️ تنبيه: يرجى كتابة رقم الحساب وإرفاق الصور معه في نفس الرسالة.")
            return

        status_msg = await message.channel.send(f"🔄 جاري إنشاء المجلد (**{folder_name}**) وتحميل الصور بيئياً...")
        
        # إنشاء المجلد إذا لم يكن موجوداً
        target_dir = os.path.join(ACCOUNTS_DIR, folder_name)
        os.makedirs(target_dir, exist_ok=True)

        success_count = 0
        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
        
        for index, attachment in enumerate(message.attachments):
            if attachment.filename.lower().endswith(valid_extensions):
                # تسمية الصور بشكل منظم وتفادي المشاكل الإملائية
                ext = os.path.splitext(attachment.filename)[1]
                file_path = os.path.join(target_dir, f"image_{index+1}{ext}")
                try:
                    await attachment.save(file_path)
                    success_count += 1
                except Exception as e:
                    await message.channel.send(f"❌ فشل حفظ الصورة {attachment.filename}: {e}")

        if success_count > 0:
            await status_msg.edit(content=f"✅ تم بنجاح إنشاء الحساب رقم (**{folder_name}**) وحفظ عدد ({success_count}) صور داخله بنجاح! جاهز للمعاينة الفورية الآن.")
        else:
            await status_msg.edit(content="❌ فشل تحميل الصور. تأكد من أن الملفات المرفقة هي صور فقط.")
        return

    # 🔍 ثانياً: نظام جلب ومعاينة الحسابات داخل التذاكر للزبائن
    if "تذكرة-" in message.channel.name or "🔒-مغلقة-" in message.channel.name:
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
    print(f"⚡ البوت متصل ومحدث بنظام الإضافة السحابية الفورية!")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    bot.add_view(MainStoreView())
    bot.add_view(TicketControlView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(
        title="🛒 متجر LTB لبيع حسابات ستيم",
        description="اضغط على الزر أدناه لفتح تذكرة خاصة، وتصفح الحسابات المتوفرة عن طريق نظام الاستعراض الذكي والمباشر.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed, view=MainStoreView())

if __name__ == "__main__":
    Thread(target=run_http_server).start()
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ خطأ: لم يتم العثور على التوكن!")