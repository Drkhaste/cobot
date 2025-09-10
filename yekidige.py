from telethon import TelegramClient, events,Button
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PasswordHashInvalidError
import os
import asyncio
import mysql.connector
import re
import subprocess
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --------------------------
HOST = "localhost"
USERNAME = "root"
PASSWORD = "Ab01f@33e1#[1"
DATABASE = "copybot"
# --------------------------



API_ID = 29953680
API_HASH = "78d69d4f1e8876f9cf400bfffcf96ad8"


MAIN_ADMIN_ID = 145501461



bot_token='8388800817:AAFyPGfYGNskFnphCrBjH7v_wGEe_b_5fx8'

bot_client = TelegramClient("yeki", API_ID, API_HASH)
user_client = TelegramClient('Asli', API_ID, API_HASH)
# -----------------------------------------------------------------------------------

clients=[]
cos=""
kir=""
list_map={}
user_step={}
user_client_running = False


photos_folder = "photos"
os.makedirs(photos_folder, exist_ok=True)

def create_db_connection():
    connection = mysql.connector.connect(
        host=HOST, user=USERNAME, password=PASSWORD, database=DATABASE ,charset="utf8mb4"
    )
    return connection

def initialize_database():
    conn = create_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY_KEY,
            user_id BIGINT UNIQUE NOT NULL
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized and 'admins' table checked/created.")

async def is_admin(user_id):
    if user_id == MAIN_ADMIN_ID:
        return True

    conn = create_db_connection()
    cursor = conn.cursor()
    query = "SELECT user_id FROM admins WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    return result is not None

async def get_other_admins():
    conn = create_db_connection()
    cursor = conn.cursor(dictionary=True) # Use dictionary cursor to get column names
    query = "SELECT * FROM admins"
    cursor.execute(query)
    admins = cursor.fetchall()
    cursor.close()
    conn.close()
    return admins

def get_main_menu_buttons(user_id):
    buttons = [
        [Button.text("🗂Add token🗂"), Button.text("⭕Delete token⭕️")],
        [Button.text("🤖manage_bots🤖")],
        [Button.text("📞 Login to Account 📞"), Button.text("📤 Logout 📤")],
        [Button.text(" راهنما")]
    ]
    if user_id == MAIN_ADMIN_ID:
        buttons.insert(2, [Button.text(" مدیریرت ادمین ها")])
    return buttons

def get_target_channels(tokenusername):
    conn = create_db_connection()
    cursor = conn.cursor()
    query = f"SELECT * FROM channels2 WHERE typechannel='destination' AND tokenusername='{tokenusername}';"
    cursor.execute(query)
    myresult = cursor.fetchall()
    cursor.close()
    target_channels = []
    print(f"{myresult}---------")
    for i in myresult:
        if i[6] == 1:
            target_channels.append(i)
    return target_channels

def get_my_channels(tokenusername):
    conn = create_db_connection()
    cursor = conn.cursor()
    query = f"SELECT * FROM channels2 WHERE typechannel='source' AND tokenusername='{tokenusername}';"
    cursor.execute(query)
    myresult = cursor.fetchall()
    cursor.close()
    my_channels = []
    for i in myresult:

        if i[6] == 1:
            my_channels.append(f"{i[5]}")
    return my_channels

def remove_links(text):
    site_link_pattern = re.compile(
        r"https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(),]|%[0-9a-fA-F][0-9a-fA-F])+"
    )
    channel_link_pattern = re.compile(r"https?://t.me/([A-Za-z0-9_]+)")
    telegram_id_pattern = re.compile(r".*@([A-Za-z0-9_]+)")
    other_link_pattern = re.compile(r".*Eror05")
    cleaned_text = channel_link_pattern.sub("", text)  # حذف لینک‌های کانال
    cleaned_text = telegram_id_pattern.sub("", cleaned_text)  # حذف آیدی‌های تلگرام
    cleaned_text = other_link_pattern.sub("", cleaned_text)  # حذف لینک های متفرقه
    cleaned_text = site_link_pattern.sub("", cleaned_text)  # حذف لینک‌های سایت
    return cleaned_text


async def add_profit_to_image(image_path, profit_values,size):
    # بارگذاری تصویر با PIL
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    # بارگذاری فونت Arial
    font_path = "ARIALBD.TTF"  # مسیر فونت Arial
    font_size = int(size.split(":")[2])
    font = ImageFont.truetype(font_path, font_size)

    text_color = (255, 255, 255)  # سفید خالص
    glow_color = (200, 200, 200)

    # موقعیت قرارگیری متن‌ها
    positions = (int(size.split(":")[0]), int(size.split(":")[1]))  # موقعیت‌های تقریبی
    text = f"{profit_values}%"

    glow_offset = 5  # افزایش مقدار نوردهی
    for dx in range(-glow_offset, glow_offset + 1, 1):
        for dy in range(-glow_offset, glow_offset + 1, 1):
            if dx != 0 or dy != 0:
                draw.text((positions[0] + dx, positions[1] + dy), text, fill=glow_color, font=font)

    # اضافه کردن متن سفید در مرکز برای جلوه نورانی
    draw.text(positions, text, fill=text_color, font=font)

    # ذخیره تصویر جدید
    output_path = "output.jpg"
    image.save(output_path)
    print(f"Image saved as {output_path}")
    return output_path

async def load_clients():
    conn = create_db_connection()
    cursor = conn.cursor()
    query = f"SELECT * FROM tokens2"
    cursor.execute(query)
    myresult = cursor.fetchall()
    cursor.close()
    if myresult!=[]:
        return [
            (TelegramClient(f'session_{token[1].split(":")[0]}', API_ID, API_HASH), token[1])
            for token in myresult
        ]
    return []


async  def find_profit(text,nn):
    lines = text.split('\n')
    l=[]
    for line in lines:
        if f'{nn}' in line:
            numbers = re.findall(r'\d+\.\d+|\d+', line)
            l.append(int(float(numbers[0])))
    return l

@bot_client.on(events.NewMessage())
async def help(event):
    global user_step,clients,cos,kir, user_client_running

    if not await is_admin(event.sender_id):
        return

    conn = create_db_connection()
    user = event.sender_id
    text = event.text
    if text == "/start":
        user_step[user] = {'step': "home","token":"","channel":"","client":"","message":"","file":"","txt":"","size":"","phone": "", "code_hash": ""}
        buttons = get_main_menu_buttons(user)
        await event.respond("🔥Copy bot🔥" , buttons=buttons)

    elif text == '🏠بازگشت به خانه🏠':
        user_step[user] = {'step': "home","token":"","channel":"","client":"","message":"","file":"","txt":"","size":"","phone": "", "code_hash": ""}
        buttons = get_main_menu_buttons(user)
        await event.respond("🏠به خانه برگشتیم🏠", buttons=buttons)

    elif text == " راهنما":
        help_text = """
راهنمای کامل ربات کپی

این ربات به شما اجازه می‌دهد پیام‌ها را از کانال‌های مبدأ به کانال‌های مقصد کپی کنید.

**منوی اصلی:**
- **🗂 Add token 🗂**: برای اضافه کردن یک ربات جدید (کلاینت) با استفاده از توکن آن.
- **⭕ Delete token ⭕️**: برای حذف یک ربات (کلاینت) از لیست.
- **🤖 manage_bots 🤖**: برای مدیریت کانال‌های مبدأ و مقصد هر ربات.
- **📞 Login to Account 📞**: برای ورود به حساب کاربری اصلی خودتان جهت کپی کردن پست‌ها از کانال‌های خصوصی.
- **📤 Logout 📤**: برای خروج از حساب کاربری.
- ** مدیریرت ادمین ها**: (فقط برای ادمین اصلی) برای افزودن یا حذف ادمین‌های دیگر.

**مراحل کار:**
1.  **لاگین**: ابتدا با زدن دکمه `Login to Account` و ارسال شماره تلفن، کد تایید و رمز عبور دو مرحله‌ای (در صورت وجود) وارد حساب خود شوید.
2.  **اضافه کردن توکن**: با زدن `Add token` و ارسال توکن ربات، یک کلاینت جدید اضافه کنید. این کلاینت‌ها برای ارسال پیام به کانال‌های مقصد استفاده می‌شوند.
3.  **مدیریت ربات‌ها**:
    - با زدن `manage_bots`، لیستی از ربات‌های فعال نمایش داده می‌شود.
    - با انتخاب هر ربات، وارد منوی مدیریت آن می‌شوید.
    - در این منو می‌توانید کانال‌های مبدأ (`☑️اضافه کردن مبدا☑️`) و مقصد (`✅اضافه کردن مقصد✅`) را با ارسال آیدی عددی یا یوزرنیم آن‌ها اضافه کنید.
    - با کلیک روی آیدی هر کانال در لیست، می‌توانید آن را مدیریت کنید (فعال/غیرفعال کردن، حذف، تعیین متن یا تصویر سفارشی).

**نکات مهم:**
- برای کپی از کانال‌های خصوصی، حتماً باید با حساب کاربری خودتان (`Login to Account`) لاگین کرده باشید.
- ادمین اصلی می‌تواند ادمین‌های دیگری را برای دسترسی به ربات اضافه کند.
"""
        await event.respond(help_text, buttons=[[Button.text('🏠بازگشت به خانه🏠')]])

    elif text == " مدیریرت ادمین ها" and event.sender_id == MAIN_ADMIN_ID:
        admin_buttons = [
            [Button.text("➕ Add Admin"), Button.text("➖ Remove Admin")],
            [Button.text("🏠بازگشت به خانه🏠")]
        ]
        await event.respond("لطفاً یک گزینه را انتخاب کنید:", buttons=admin_buttons)

    elif text == "➕ Add Admin" and event.sender_id == MAIN_ADMIN_ID:
        user_step[user]['step'] = 'add_admin'
        await event.respond("لطفاً شناسه کاربری (User ID) ادمین جدید را ارسال کنید.", buttons=[[Button.text('🏠بازگشت به خانه🏠')]])

    elif user_step.get(user) and user_step[user].get('step') == 'add_admin' and event.sender_id == MAIN_ADMIN_ID:
        try:
            new_admin_id = int(text)
            conn = create_db_connection()
            cursor = conn.cursor()
            query = "INSERT INTO admins (user_id) VALUES (%s)"
            cursor.execute(query, (new_admin_id,))
            conn.commit()
            cursor.close()
            conn.close()
            await event.respond(f"ادمین با شناسه {new_admin_id} با موفقیت اضافه شد.", buttons=[[Button.text('🏠بازگشت به خانه🏠')]])
            user_step[user]['step'] = 'home'
        except ValueError:
            await event.respond("شناسه کاربری باید یک عدد باشد. لطفاً دوباره تلاش کنید.")
        except mysql.connector.Error as err:
            if err.errno == 1062: # Error for duplicate entry
                await event.respond("این کاربر قبلاً به عنوان ادمین ثبت شده است.")
            else:
                await event.respond(f"خطای دیتابیس: {err}")
            user_step[user]['step'] = 'home'

    elif text == "➖ Remove Admin" and event.sender_id == MAIN_ADMIN_ID:
        other_admins = await get_other_admins()
        if not other_admins:
            await event.respond("هیچ ادمین دیگری برای حذف وجود ندارد.", buttons=[[Button.text('🏠بازگشت به خانه🏠')]])
            return

        admin_list_text = "لیست ادمین‌ها:\n\n"
        for admin in other_admins:
            admin_list_text += f"ID: `{admin['user_id']}` (ردیف: {admin['id']})\n"

        admin_list_text += "\nلطفاً **ردیف (id)** ادمینی که می‌خواهید حذف کنید را ارسال کنید."

        user_step[user]['step'] = 'remove_admin'
        await event.respond(admin_list_text, buttons=[[Button.text('🏠بازگشت به خانه🏠')]])

    elif user_step.get(user) and user_step[user].get('step') == 'remove_admin' and event.sender_id == MAIN_ADMIN_ID:
        try:
            admin_db_id = int(text)
            conn = create_db_connection()
            cursor = conn.cursor()
            # Check if admin with this db id exists before deleting
            check_query = "SELECT * FROM admins WHERE id = %s"
            cursor.execute(check_query, (admin_db_id,))
            if not cursor.fetchone():
                 await event.respond("هیچ ادمینی با این ردیف یافت نشد.", buttons=[[Button.text('🏠بازگشت به خانه🏠')]])
                 user_step[user]['step'] = 'home'
                 return

            query = "DELETE FROM admins WHERE id = %s"
            cursor.execute(query, (admin_db_id,))
            conn.commit()
            cursor.close()
            conn.close()
            await event.respond(f"ادمین با ردیف {admin_db_id} با موفقیت حذف شد.", buttons=[[Button.text('🏠بازگشت به خانه🏠')]])
            user_step[user]['step'] = 'home'
        except ValueError:
            await event.respond("ردیف باید یک عدد باشد. لطفاً دوباره تلاش کنید.")
        except Exception as e:
            await event.respond(f"خطایی رخ داد: {e}")
            user_step[user]['step'] = 'home'

    elif text == "📞 Login to Account 📞":
        if await user_client.is_user_authorized():
            await event.respond("شما قبلاً با موفقیت وارد شده اید.", buttons=[[Button.text("🗂Add token🗂"),Button.text("⭕Delete token⭕️")],[Button.text("🤖manage_bots🤖")],[Button.text("📞 Login to Account 📞")]])
        else:
            await event.respond("لطفاً شماره تلفن خود را برای ورود ارسال کنید (مثال: +989123456789)", buttons=[[Button.text('🏠بازگشت به خانه🏠')]])
            user_step[user]['step'] = 'login_phone'

    elif user_step.get(user) and user_step[user].get('step') == 'login_phone':
        try:
            phone_number = text
            user_step[user]['phone'] = phone_number
            # Start the client if it's not already running
            if not user_client.is_connected():
                await user_client.connect()
            result = await user_client.send_code_request(phone_number)
            user_step[user]['code_hash'] = result.phone_code_hash
            await event.respond("کد تایید به تلگرام شما ارسال شد. لطفاً کد را وارد کنید.")
            user_step[user]['step'] = 'login_code'
        except Exception as e:
            await event.respond(f"خطایی رخ داد: {e}")
            user_step[user]['step'] = 'home'

    elif user_step.get(user) and user_step[user].get('step') == 'login_code':
        try:
            code = text
            phone_number = user_step[user]['phone']
            code_hash = user_step[user]['code_hash']
            await user_client.sign_in(phone_number, code, phone_code_hash=code_hash)
            await event.respond("شما با موفقیت وارد شدید!", buttons=[[Button.text("🗂Add token🗂"),Button.text("⭕Delete token⭕️")],[Button.text("🤖manage_bots🤖")],[Button.text("📞 Login to Account 📞")]])
            user_step[user]['step'] = 'home'
            if not user_client_running:
                print("Starting user client event loop after login...")
                asyncio.create_task(user_client.run_until_disconnected())
                user_client_running = True
        except SessionPasswordNeededError:
            await event.respond("رمز عبور دو مرحله‌ای شما مورد نیاز است. لطفاً آن را وارد کنید.")
            user_step[user]['step'] = 'login_password'
        except PhoneCodeInvalidError:
            await event.respond("کد وارد شده اشتباه است. لطفاً دوباره تلاش کنید.", buttons=[[Button.text('🏠بازگشت به خانه🏠')]])
            user_step[user]['step'] = 'home'
        except Exception as e:
            await event.respond(f"خطایی رخ داد: {e}", buttons=[[Button.text('🏠بازگشت به خانه🏠')]])
            user_step[user]['step'] = 'home'

    elif user_step.get(user) and user_step[user].get('step') == 'login_password':
        try:
            password = text
            await user_client.sign_in(password=password)
            await event.respond("شما با موفقیت وارد شدید!", buttons=[[Button.text("🗂Add token🗂"),Button.text("⭕Delete token⭕️")],[Button.text("🤖manage_bots🤖")],[Button.text("📞 Login to Account 📞"), Button.text("📤 Logout 📤")]])
            user_step[user]['step'] = 'home'
            if not user_client_running:
                print("Starting user client event loop after 2FA login...")
                asyncio.create_task(user_client.run_until_disconnected())
                user_client_running = True
        except PasswordHashInvalidError:
            await event.respond("رمز عبور وارد شده اشتباه است. لطفاً دوباره تلاش کنید.", buttons=[[Button.text('🏠بازگشت به خانه🏠')]])
            user_step[user]['step'] = 'home'
        except Exception as e:
            await event.respond(f"خطایی رخ داد: {e}", buttons=[[Button.text('🏠بازگشت به خانه🏠')]])
            user_step[user]['step'] = 'home'

    elif text == "📤 Logout 📤":
        if await user_client.is_user_authorized():
            await user_client.log_out()
            user_client_running = False
            print("User client logged out and flag reset.")
            await event.respond("شما با موفقیت از حساب کاربری خارج شدید.", buttons=[[Button.text("🗂Add token🗂"),Button.text("⭕Delete token⭕️")],[Button.text("🤖manage_bots🤖")],[Button.text("📞 Login to Account 📞"), Button.text("📤 Logout 📤")]])
        else:
            await event.respond("هیچ حساب کاربری برای خروج وجود ندارد.", buttons=[[Button.text("🗂Add token🗂"),Button.text("⭕Delete token⭕️")],[Button.text("🤖manage_bots🤖")],[Button.text("📞 Login to Account 📞"), Button.text("📤 Logout 📤")]])

    elif text == "🗂Add token🗂":
        await event.respond(' لطفاً توکن تلگرام خود را ارسال کنید تا کلاینت جدیدی بسازم.', buttons=[[Button.text('🏠بازگشت به خانه🏠')]])
        user_step[event.sender_id]['step'] = "token"

    elif text=="⭕Delete token⭕️":
        print(clients)
        user_step[event.sender_id]["step"]="delettoken"
        cursor = conn.cursor()
        query = f"SELECT * FROM tokens2"
        cursor.execute(query)
        myresult = cursor.fetchall()
        cursor.close()
        token_list=[]
        for i in myresult:
            for client in clients:
                if client.session.filename == f'session_{i[1].split(":")[0]}.session':
                    print(f"-----------{i}------------")
                    me=await client.get_me()
                    print(me)
                    token_list.append(f"{i[0]} : {i[1]} : @{me.username}")
                    break
        cos="\n\n".join(token_list)
        await event.respond("لیست توکن های فعال شما:" "\n"f"{cos}\n""برای حذف توکن مورد نظر شماره ان را بفرستید",
                            buttons=[[Button.text('🏠بازگشت به خانه🏠')]])


    elif text=="🤖manage_bots🤖":
        user_step[event.sender_id]["step"]="managetoken"
        cursor = conn.cursor()
        query = f"SELECT * FROM tokens2"
        cursor.execute(query)
        myresult = cursor.fetchall()
        cursor.close()
        token_list=[]
        for i in myresult:
            for client in clients:
                if client.session.filename == f'session_{i[1].split(":")[0]}.session':
                    me=await client.get_me()
                    token_list.append(f"/{i[0]} : {i[1]} : @{me.username}")
                    break
        cos="\n\n".join(token_list)
        await event.respond("لیست ربات های فعال شما:" "\n"f"{cos}\n""برای مدیریت ربات مورد نظر شماره ان را بفرستید",buttons=[[Button.text('🏠بازگشت به خانه🏠')]])

    elif text == '☑️اضافه کردن مبدا☑️':
        user_step[event.sender_id]["step"] = "source"
        await event.respond("ایدی عددی و یا یوزرنیم گروه مبدا را وارد کنید", buttons=[[Button.text('🏠بازگشت به خانه🏠')]])
    elif text == "✅اضافه کردن مقصد✅":
        user_step[event.sender_id]["step"] = "destination"
        await event.respond("ایدی عددی و یا یوزرنیم گروه مقصد را وارد کنید", buttons=[[Button.text('🏠بازگشت به خانه🏠')]])

    elif text == "⭕️غیر فعال کردن⭕️":
        if user_step[user]['channel']!="":
            mycursor = conn.cursor()
            sql = f"UPDATE channels2 SET status = '0' WHERE channel_id = '{user_step[user]['channel']}' AND tokenusername='{user_step[user]['token']}';"
            mycursor.execute(sql)
            conn.commit()
            mycursor.close()
            print(mycursor.rowcount, "record(s) affected.")
            await event.respond(f"❌ غیر فعال شد ❌",
                                    buttons=[
                                    [Button.text("✅فعال کردن✅"), Button.text("🗑حذف گروه🗑")],
                                    [Button.text('تعیین متن'), Button.text('🖼تعیین تصویر🖼'), Button.text('حذف تصویر'),Button.text('جایگزینی متن')],
                                    [Button.text("🗂گروه ها🗂"),Button.text('🏠بازگشت به خانه🏠')]])
        else:
            await event.respond("⭕️ابتدا گروه مورد نظر را انتخاب کنید⭕️",
                                buttons=[[Button.text("🤖manage_bots🤖"),Button.text("🗂گروه ها🗂")],[Button.text('🏠بازگشت به خانه🏠')]])

    elif text == "✅فعال کردن✅":
        if user_step[user]["channel"]!="":
            mycursor = conn.cursor()
            sql = f"UPDATE channels2 SET status = '1' WHERE channel_id = '{user_step[user]['channel']}' AND tokenusername='{user_step[user]['token']}';"
            mycursor.execute(sql)
            conn.commit()
            mycursor.close()
            print(mycursor.rowcount, "record(s) affected.")
            await event.respond(f"✅ فعال شد ✅",
                                    buttons=[
                                    [Button.text("⭕️غیر فعال کردن⭕️"), Button.text("🗑حذف گروه🗑")],
                                    [Button.text("تعیین متن"), Button.text("🖼تعیین تصویر🖼"), Button.text("حذف تصویر"),Button.text("جایگزینی متن")],
                                    [Button.text("🗂گروه ها🗂"),Button.text('🏠بازگشت به خانه🏠')]])
        else:
            await event.respond("⭕️ابتدا گروه مورد نظر را انتخاب کنید⭕️",
                                buttons=[[Button.text("🤖manage_bots🤖"),Button.text("🗂گروه ها🗂")],[Button.text('🏠بازگشت به خانه🏠')]])

    elif text == "🗑حذف گروه🗑":
        mycursor = conn.cursor()
        sql = f"DELETE FROM channels2 WHERE channel_id = '{user_step[user]['channel']}' AND tokenusername='{user_step[user]['token']}';"
        mycursor.execute(sql)
        conn.commit()
        mycursor.close()
        if mycursor.rowcount!=0:
            user_step[user]["channel"] = ""
            await event.respond("❌گروه مورد نظر با موفقیت حذف شد❌",
                                buttons=[[Button.text("🤖manage_bots🤖"),Button.text("🗂گروه ها🗂")],[Button.text('🏠بازگشت به خانه🏠')]])
        else:
            await event.respond("⭕️گروهی یافت نشد⭕️",
                                buttons=[[Button.text("🤖manage_bots🤖"),Button.text("🗂گروه ها🗂")],[Button.text('🏠بازگشت به خانه🏠')]])


    elif text == "تعیین متن":
        user_step[event.sender_id]['step'] = "text"
        await event.respond("متن مورد نظر خود را بفرستید", buttons=[[Button.text('🏠بازگشت به خانه🏠')]])

    elif text == "🖼تعیین تصویر🖼":
        user_step[event.sender_id]['step'] = "photo"
        await event.respond("تصویر مورد نظر خود را بفرستید", buttons=[[Button.text('🏠بازگشت به خانه🏠')]])

    elif text=="جایگزینی متن":
        user_step[event.sender_id]['step'] = "txt"
        await event.respond("ابتدا متنی که میخواهید تغییر یابد را نوشته سپس = گذاشته و متن جایگزین را بنویسید", buttons=[[Button.text('🏠بازگشت به خانه🏠')]])

    elif text == "حذف تصویر":
        mycursor = conn.cursor()
        sql = f"UPDATE channels2 SET fileid = '0' WHERE channel_id = '{user_step[user]['channel']}' AND tokenusername='{user_step[user]['token']}';"
        mycursor.execute(sql)
        conn.commit()
        mycursor.close()
        print(mycursor.rowcount, "record(s) affected.")
        if mycursor.rowcount!=0:
            await event.respond("❌تصویر مورد نظر با موفقیت حذف شد❌",
                                buttons=[
                                    [Button.text("⭕️غیر فعال کردن⭕️"), Button.text("✅فعال کردن✅"),
                                     Button.text("🗑حذف گروه🗑")],
                                    [Button.text("تعیین متن"), Button.text("🖼تعیین تصویر🖼"),
                                     Button.text("جایگزینی متن")],
                                    [Button.text("🗂گروه ها🗂"), Button.text('🏠بازگشت به خانه🏠')]])
        else:
            await event.respond("⭕️تصویری برای گروه تنظیم نشده است⭕️",
                                buttons=[
                                    [Button.text("⭕️غیر فعال کردن⭕️"), Button.text("✅فعال کردن✅"),
                                     Button.text("🗑حذف گروه🗑")],
                                    [Button.text("تعیین متن"), Button.text("🖼تعیین تصویر🖼"),
                                     Button.text("جایگزینی متن")],
                                    [Button.text("🗂گروه ها🗂"), Button.text('🏠بازگشت به خانه🏠')]])



    elif user_step[event.sender_id]['step'] == "token":
        try:
            new_client = TelegramClient(f'session_{text.split(":")[0]}', API_ID, API_HASH)
            await new_client.start(bot_token=text)
            clients.append(new_client)
            await event.respond(f'کلاینت با توکن {text} با موفقیت ساخته شد و به لیست اضافه شد.',buttons=[[Button.text('🏠بازگشت به خانه🏠')]])
            cursor = conn.cursor()
            sql = "INSERT INTO tokens2 (token) VALUES (%s)"
            val = (text,)
            cursor.execute(sql, val)
            conn.commit()
            cursor.close()
            asyncio.create_task(new_client.run_until_disconnected())
        except Exception as e:
            await event.respond(f'متاسفم، نتوانستم با این توکن اتصال برقرار کنم: {e}',buttons=[[Button.text('🏠بازگشت به خانه🏠')]])




    elif user_step[user]["step"] == "delettoken":
        try:
            cursor = conn.cursor()
            query = f"SELECT * FROM tokens2 WHERE id='{text}';"
            cursor.execute(query)
            myresult = cursor.fetchall()
            cursor.close()
            mycursor = conn.cursor()
            for client in clients:
                if client.session.filename == f'session_{myresult[0][1].split(":")[0]}.session':
                    client_to_remove = client
                    await client_to_remove.disconnect()
                    clients.remove(client_to_remove)
                    sql = f"DELETE FROM tokens2 WHERE id ='{text}';"
                    mycursor.execute(sql)
                    conn.commit()
                    mycursor.close()
                    os.remove(client.session.filename)
                    await event.respond(
                        "توکن و کلاینت مربوطه با موفقیت حذف شدند.", buttons=[[Button.text('🏠بازگشت به خانه🏠')]]
                    )
                    break

        except Exception as e:
            print(e)



    elif user_step[user]["step"] == "managetoken":
        try:
            if text != "🗂گروه ها🗂":
                print(text.split("/")[1])
                cursor = conn.cursor()
                query = f"SELECT * FROM tokens2 WHERE id='{text.split('/')[1]}';"
                cursor.execute(query)
                myresult = cursor.fetchall()
                cursor.close()
                print(myresult)
                for client in clients:
                    if client.session.filename == f"session_{myresult[0][1].split(':')[0]}.session":
                        me = await client.get_me()
                        user_step[user]["token"]=me.username
                        user_step[user]["client"]=client

                        cursor = conn.cursor()
                        query = f"SELECT * FROM channels2 where tokenusername='{me.username}';"
                        cursor.execute(query)
                        myresult = cursor.fetchall()
                        cursor.close()
                        source_list = []
                        dest_list=[]
                        print(myresult)
                        if len(myresult)==0:
                            user_step[user]["step"]="home"
                            await event.respond("هیچ گروه مبدا یا مقصدی ثبت نشده است", buttons=[[Button.text('☑️اضافه کردن مبدا☑️'), Button.text("✅اضافه کردن مقصد✅")],[Button.text("🤖manage_bots🤖"),Button.text('🏠بازگشت به خانه🏠')]])
                        else:
                            for list in myresult:
                                if list[2]=="source":
                                    source_list.append(f"{len(source_list)+1} : {list[3]} : /{list[5].split('-')[1]}")
                                elif list[2]=="destination":
                                    dest_list.append(f"{len(dest_list)+1} : {list[3]} : /{list[5].split('-')[1]}")
                            cos = "\n\n".join(source_list)
                            kir = "\n\n".join(dest_list)
                            await event.respond( f"🕹ربات {me.username}🕹" "\n\n" "📥لیست کانال های مبدا:📥" "\n" f"{cos}" "\n\n" "📤لیست گروه های مقصد:📤" "\n" f"{kir}" "\n" "⭕️برای مدیریت هر گروه بر روی ایدی ان کلیک کنید⭕️",
                                                 buttons=[[Button.text('☑️اضافه کردن مبدا☑️'), Button.text("✅اضافه کردن مقصد✅")],[Button.text("🤖manage_bots🤖"), Button.text('🏠بازگشت به خانه🏠')]])
                            user_step[user]["step"] = "managegroup"
                        break
            elif text=="🗂گروه ها🗂":
                cursor = conn.cursor()
                query = f"SELECT * FROM channels2 where tokenusername='{user_step[user]['token']}';"
                cursor.execute(query)
                myresult = cursor.fetchall()
                cursor.close()
                source_list = []
                dest_list = []
                if len(myresult) == 0:
                    user_step[user]["step"] = "home"
                    await event.respond("هیچ گروه مبدا یا مقصدی ثبت نشده است",
                                        buttons=[[Button.text('☑️اضافه کردن مبدا☑️'), Button.text("✅اضافه کردن مقصد✅")],
                                                 [Button.text("🤖manage_bots🤖"), Button.text('🏠بازگشت به خانه🏠')]])
                else:
                    for list in myresult:
                        if list[2] == "source":
                            source_list.append(f"{len(source_list) + 1} : {list[3]} : /{list[5].split('-')[1]}")
                        elif list[2] == "destination":
                            dest_list.append(f"{len(dest_list) + 1} : {list[3]} : /{list[5].split('-')[1]}")
                    cos = "\n\n".join(source_list)
                    kir = "\n\n".join(dest_list)
                await event.respond(
                    f"🕹ربات {user_step[user]['token']}🕹" "\n\n" "📥لیست کانال های مبدا:📥" "\n" f"{cos}" "\n\n" "📤لیست گروه های مقصد:📤" "\n" f"{kir}" "\n" "⭕️برای مدیریت هر گروه بر روی ایدی ان کلیک کنید⭕️",
                    buttons=[[Button.text("🤖manage_bots🤖"), Button.text('🏠بازگشت به خانه🏠')]])
                user_step[user]["step"] = "managegroup"
        except Exception as e:
            print(e)

    elif user_step[user]["step"] == "managegroup" and user_step[user]["token"] != "":
        user_step[user]["step"]="managetoken"
        cursor = conn.cursor()
        query = f"SELECT * FROM channels2 where tokenusername='{user_step[user]['token']}' AND channel_id='-{text.split('/')[1]}';"
        cursor.execute(query)
        myresult = cursor.fetchall()
        cursor.close()
        if len(myresult)==0:
            await event.respond("⭕️هیچ گروهی با این مشخصات ثبت نشده است⭕️",
                                buttons=[[Button.text("🤖manage_bots🤖"),Button.text("🗂گروه ها🗂")],[Button.text('🏠بازگشت به خانه🏠')]])
        else:
            user_step[user]["channel"] = f"-{text.split('/')[1]}"
            await event.respond("📄اطلاعات گروه مورد نظر:"
                            "\n\n"
                            f"نام گروه :{myresult[0][3]}"
                            "\n"
                            f"ایدی گروه : {myresult[0][4]}"
                            "\n"
                            f"نوع گروه : {myresult[0][2]}"
                            "\n"
                            f"وضعیت :{myresult[0][6]}"
                            "\n"
                            f"متن تنظیمی {myresult[0][7]}"
                            "\n"
                                ,
                                buttons=[
                                    [Button.text("⭕️غیر فعال کردن⭕️"), Button.text("✅فعال کردن✅"), Button.text("🗑حذف گروه🗑")],
                                    [Button.text("تعیین متن"), Button.text("🖼تعیین تصویر🖼"), Button.text("حذف تصویر"),Button.text("جایگزینی متن")],
                                    [Button.text("🗂گروه ها🗂"),Button.text('🏠بازگشت به خانه🏠')]])


    elif user_step[user]['step'] == "text":

        mycursor = conn.cursor()
        sql = f"UPDATE channels2 SET text = '{text}' WHERE channel_id = '{user_step[user]['channel']}' AND tokenusername='{user_step[user]['token']}';"
        mycursor.execute(sql)
        conn.commit()
        print(mycursor.rowcount, "record(s) affected")
        mycursor.close()
        if mycursor.rowcount!=0:
            user_step[user]['step'] = "managetoken"
            await event.respond("✅متن مورد نظر با موفقیت تنظیم شد✅",
                                buttons=[
                                    [Button.text("⭕️غیر فعال کردن⭕️"), Button.text("✅فعال کردن✅"),
                                     Button.text("🗑حذف گروه🗑")],
                                    [Button.text("تعیین متن"), Button.text("🖼تعیین تصویر🖼"),
                                     Button.text("جایگزینی متن")],
                                    [Button.text("🗂گروه ها🗂"), Button.text('🏠بازگشت به خانه🏠')]])
        else:
            await event.respond("⭕️متن تنظیم نشد⭕️",
                                buttons=[[Button.text("🤖manage_bots🤖"),Button.text('🏠بازگشت به خانه🏠')]])

    elif user_step[event.sender_id]['step'] == "photo":
        if event.message.photo:
            print("1")
            file_path = os.path.join( f"{event.photo.id}.jpg")
            print("2")
            await event.download_media(file_path)
            print("3")
            botton = [[Button.inline("📋افزودن متن📋", b'1'), Button.inline("✅تایید عکس بدون تعیین متن✅", b'0')]]
            message = await bot_client.send_file(entity=event.sender_id,file=file_path, caption="عکس انتخابی شما📷"+ "\n",buttons=botton)
            print("4")
            user_step[user]["message"]=message
            user_step[user]["file"]=file_path

            # mycursor = conn.cursor()
            # sql = f"UPDATE channels SET fileid = '{file_path}' WHERE channel_id = '{user_step[user]['channel']}' AND tokenusername='{user_step[user]['token']}';"
            # mycursor.execute(sql)
            # conn.commit()
            # mycursor.close()
            # print(mycursor.rowcount, "record(s) affected.")
            # if mycursor.rowcount != 0:
            #     user_step[user]['step'] = "managetoken"
            #     await event.respond("✅عکس با موفقیت تنظیم شد✅"   ,
            #                         buttons=[
            #                             [Button.text("⭕️غیر فعال کردن⭕️"), Button.text("✅فعال کردن✅"),
            #                              Button.text("🗑حذف گروه🗑")],
            #                             [Button.text("تعیین متن"), Button.text("🖼تعیین تصویر🖼"),
            #                              Button.text("جایگزینی متن")],
            #                             [Button.text("🗂گروه ها🗂"), Button.text('🏠بازگشت به خانه🏠')]])
            # else:
            #     await event.respond("⭕️عکس تنظیم نشد⭕️",
            #                         buttons=[[Button.text("🤖manage_bots🤖"), Button.text('🏠بازگشت به خانه🏠')]])



        else:
            user_step[user]['step'] = "managetoken"
            await event.respond("⭕️پیام ارسالی حاوی عکس نیست⭕️",
                                buttons=[
                                    [Button.text("⭕️غیر فعال کردن⭕️"), Button.text("✅فعال کردن✅"),
                                     Button.text("🗑حذف گروه🗑")],
                                    [Button.text("تعیین متن"), Button.text("🖼تعیین تصویر🖼"),
                                     Button.text("جایگزینی متن")],
                                    [Button.text("🗂گروه ها🗂"), Button.text('🏠بازگشت به خانه🏠')]])


    elif user_step[user]['step'] == "txt":
        txt_list=[]
        cursor = conn.cursor()
        query = f"SELECT * FROM channels2 WHERE channel_id = '{user_step[user]['channel']}' AND tokenusername='{user_step[user]['token']}';"
        cursor.execute(query)
        myresult = cursor.fetchall()
        cursor.close()
        txt_list.append(myresult[0][9])
        txt_list.append(text)
        con=",".join(txt_list)
        mycursor = conn.cursor()
        sql = f"UPDATE channels2 SET txt = '{con}' WHERE channel_id = '{user_step[user]['channel']}' AND tokenusername='{user_step[user]['token']}';"
        mycursor.execute(sql)
        conn.commit()
        print(mycursor.rowcount, "record(s) affected")
        mycursor.close()
        if mycursor.rowcount!=0:
            user_step[user]['step'] = "managetoken"
            await event.respond("✅متن جایگزین مورد نظر با موفقیت تنظیم شد✅",
                                buttons=[
                                    [Button.text("⭕️غیر فعال کردن⭕️"), Button.text("✅فعال کردن✅"),
                                     Button.text("🗑حذف گروه🗑")],
                                    [Button.text("تعیین متن"), Button.text("🖼تعیین تصویر🖼"),
                                     Button.text("جایگزینی متن")],
                                    [Button.text("🗂گروه ها🗂"), Button.text('🏠بازگشت به خانه🏠')]])
        else:
            await event.respond("⭕️متن تنظیم نشد⭕️",buttons=[[Button.text("🤖manage_bots🤖"),Button.text('🏠بازگشت به خانه🏠')]])


    elif user_step[user]['step'] == "source":
        x = re.search("^@.*", text)
        user_step[user]['step']="managetoken"
        if x:
            channel = await user_step[user]['client'].get_entity(text)
            cursor = conn.cursor()
            sql = "INSERT INTO channels2 (tokenusername,typechannel,channel_name,username,channel_id,status) VALUES (%s, %s, %s,%s,%s,%s)"
            val = (user_step[user]["token"],"source",f"{channel.title}", text,f"-100{channel.id}", "1")
            cursor.execute(sql, val)
            conn.commit()
            cursor.close()
            print(cursor.rowcount, "record inserted.")
            await event.respond(
                f"کانال {channel.title} با موفقیت ثبت شد و به صورت پیش فرض فعال است. ",buttons=[[Button.text("🗂گروه ها🗂")],[Button.text("🤖manage_bots🤖"), Button.text('🏠بازگشت به خانه🏠')]]
            )
        else:

            channel = await user_client.get_entity(int(text))
            print(channel.title)
            cursor = conn.cursor()
            sql = "INSERT INTO channels2 (tokenusername,typechannel,channel_name,username,channel_id,status) VALUES (%s, %s, %s,%s,%s,%s)"
            val = (user_step[user]["token"],"source",f"{channel.title}",f"-100{channel.id}" ,f"-100{channel.id}", "1")
            cursor.execute(sql, val)
            conn.commit()
            cursor.close()
            await event.respond(
                f"کانال {channel.title} با موفقیت ثبت شد و به صورت پیش فرض فعال است. ",buttons=[[Button.text("🗂گروه ها🗂")],[Button.text("🤖manage_bots🤖"), Button.text('🏠بازگشت به خانه🏠')]]
            )

    elif user_step[event.sender_id]['step'] == "destination":

        x = re.search("^@.*", text)
        user_step[user]['step'] = "managetoken"
        print(f"---------{user_step[user]['token']}------")
        if x:
            channel = await user_step[user]['client'].get_entity(text)
            cursor = conn.cursor()
            sql = "INSERT INTO channels2 (tokenusername,typechannel,channel_name,username,channel_id,status,text,fileid,txt,size,nn) VALUES (%s, %s, %s,%s,%s,%s,%s,%s,%s,%s,%s)"
            val = (user_step[user]["token"],"destination",channel.title,text ,f"-100{channel.id}", "1","0","0","0","0","0")
            cursor.execute(sql, val)
            conn.commit()
            cursor.close()
            await event.respond(
                f"کانال {channel.title} با موفقیت ثبت شد و به صورت پیش فرض فعال است. ",buttons=[[Button.text("🗂گروه ها🗂")],[Button.text("🤖manage_bots🤖"), Button.text('🏠بازگشت به خانه🏠')]]
            )
        else:
            channel = await user_step[user]['client'].get_entity(int(text))
            cursor = conn.cursor()
            sql = "INSERT INTO channels2 (tokenusername,typechannel,channel_name,username,channel_id,status,text,fileid,txt,size,nn) VALUES (%s, %s, %s,%s,%s,%s,%s,%s,%s,%s,%s)"
            val = (user_step[user]["token"],"destination",channel.title, f"-100{channel.id}",f"-100{channel.id}" ,"1","0","0","0","0","0")
            cursor.execute(sql, val)
            conn.commit()
            cursor.close()
            await event.respond(
                f"کانال {channel.title} با موفقیت ثبت شد و به صورت پیش فرض فعال است. ",buttons=[[Button.text("🗂گروه ها🗂")],[Button.text("🤖manage_bots🤖"), Button.text('🏠بازگشت به خانه🏠')]]
            )

    elif user_step[event.sender_id]["step"]=="selecttext":
        user_step[event.sender_id]["step"] = "settingtext"
        user_step[event.sender_id]["txt"] = f"{text}"
        user_step[event.sender_id]["size"] = "750:290:450"


    if user_step[event.sender_id]["step"] == "settingtext":
        try:
            int(text.split(":")[0])
            print("عدد بود")
            user_step[event.sender_id]["size"]=text
        except:
            print("عدد نبود")
            pass

        await bot_client.delete_messages(event.chat_id, user_step[user]['message'].id)
        botton2 = [[Button.inline("✅تایید✅", b'ok'), Button.inline("❌کنسل❌", b'cancel')]]
        print(user_step[event.sender_id]["size"])
        print(user_step[event.sender_id]["txt"].split(":")[1])

        new = await add_profit_to_image(image_path=f"{user_step[user]['file']}",
            profit_values=user_step[event.sender_id]["txt"].split(":")[1],size=user_step[event.sender_id]["size"])
        message = await bot_client.send_file(entity=event.sender_id ,file=new,
            caption=f"موقعیت تقریبی متن تنظیمی را به صورت مقابل بفرستید:" "\n" f"{user_step[event.sender_id]['size']}" "\n"   "اندازه فونت:عرض:طول"  "\n" "+راست تر/ پایین تر" "\n"  "-چپ تر/بالاتر" "\n",buttons=botton2)
        user_step[user]['message']=message


@bot_client.on(events.CallbackQuery)
async def callback(event):
    global  user_step

    conn=create_db_connection()
    if event.data == b'1':
        user_step[event.sender_id]["step"]="selecttext"
        await event.respond("متن انتخابی در کپشن و یک مقدار نمونه بفرستید" "\n" "نمونه" "Profit:133",
                            buttons=[[Button.text('🏠بازگشت به خانه🏠')]])


    elif event.data == b'0':
        mycursor = conn.cursor()
        print(user_step[event.sender_id]['file'])
        print(user_step[event.sender_id]['channel'])
        print(user_step[event.sender_id]['token'])
        sql = f"UPDATE channels2 SET fileid = '{user_step[event.sender_id]['file']}' WHERE channel_id = '{user_step[event.sender_id]['channel']}' AND tokenusername='{user_step[event.sender_id]['token']}';"
        mycursor.execute(sql)
        conn.commit()
        print(mycursor.rowcount, "record(s) affected.")
        if mycursor.rowcount != 0:
            user_step[event.sender_id]['step'] = "managetoken"
            await event.respond("✅عکس با موفقیت تنظیم شد✅",
                                buttons=[
                                    [Button.text("⭕️غیر فعال کردن⭕️"), Button.text("✅فعال کردن✅"),
                                     Button.text("🗑حذف گروه🗑")],
                                    [Button.text("تعیین متن"), Button.text("🖼تعیین تصویر🖼"),
                                     Button.text("جایگزینی متن")],
                                    [Button.text("🗂گروه ها🗂"), Button.text('🏠بازگشت به خانه🏠')]])
        else:
            await event.respond("⭕️عکس تنظیم نشد⭕️",
                                buttons=[[Button.text("🤖manage_bots🤖"), Button.text('🏠بازگشت به خانه🏠')]])
        mycursor.close()
    elif event.data ==b"ok":
        mycursor = conn.cursor()
        sql = f"UPDATE channels2 SET fileid = '{user_step[event.sender_id]['file']}', nn='{user_step[event.sender_id]['txt'].split(':')[0]}' , size='{user_step[event.sender_id]['size']}' WHERE channel_id = '{user_step[event.sender_id]['channel']}' AND tokenusername='{user_step[event.sender_id]['token']}';"
        mycursor.execute(sql)
        conn.commit()
        mycursor.close()
        print(mycursor.rowcount, "record(s) affected.")
        if mycursor.rowcount != 0:
            user_step[event.sender_id]['step'] = "managetoken"
            await event.respond("✅عکس با موفقیت تنظیم شد✅",
                                buttons=[
                                    [Button.text("⭕️غیر فعال کردن⭕️"), Button.text("✅فعال کردن✅"),
                                     Button.text("🗑حذف گروه🗑")],
                                    [Button.text("تعیین متن"), Button.text("🖼تعیین تصویر🖼"),
                                     Button.text("جایگزینی متن")],
                                    [Button.text("🗂گروه ها🗂"), Button.text('🏠بازگشت به خانه🏠')]])
        else:
            await event.respond("⭕️عکس تنظیم نشد⭕️",
                                buttons=[[Button.text("🤖manage_bots🤖"), Button.text('🏠بازگشت به خانه🏠')]])

        user_step[event.sender_id]["txt"] = ""
        user_step[event.sender_id]["size"] = ""

    elif event.data==b"cancel":
        user_step[event.sender_id]['step'] = "managetoken"
        await event.respond("❌تعیین عکس کنصل شد❌",
                            buttons=[
                                [Button.text("⭕️غیر فعال کردن⭕️"), Button.text("✅فعال کردن✅"),
                                 Button.text("🗑حذف گروه🗑")],
                                [Button.text("تعیین متن"), Button.text("🖼تعیین تصویر🖼"),
                                 Button.text("جایگزینی متن")],
                                [Button.text("🗂گروه ها🗂"), Button.text('🏠بازگشت به خانه🏠')]])




async def copy_isreplay(event,i,reply_to_msg,clientvalue):
    conn=create_db_connection()
    cleaned_text = remove_links(event.message.message)
    cursor = conn.cursor()
    query = f"SELECT * FROM ids2 where channel='{i[5]}';"
    cursor.execute(query)
    myresult = cursor.fetchall()
    cursor.close()

    print("replay")
    print(myresult)


    new_message_id = None

    print(reply_to_msg)
    print(type(reply_to_msg))

    for u in myresult:
        if reply_to_msg.id == int(u[2].split("_")[0]):
            new_message_id = int(u[2].split("_")[1])
    total = i[9].split(",")
    for t in total:
        chain = t.split("=")
        try:
            cleaned_text = re.sub(chain[0], chain[1], cleaned_text)
        except:
            pass
    if event.message.text and new_message_id != None:
        text = event.message.text
        if event.message.photo:
            match = await find_profit(text, i[11])
            if len(match)!=0 and i[11]!="0":
                numbers = sorted(match, key=float)
                print(numbers)
                new = await add_profit_to_image(image_path=i[8], profit_values=numbers[-1],size=i[10])
                message = await clientvalue.send_file(entity=int(i[5]), file=new,
                                                      caption=cleaned_text + "\n" + str(
                                                          i[7] + "\n"), reply_to=new_message_id)
                cursor = conn.cursor()
                sql = "INSERT INTO ids2 (channel,dict) VALUES (%s,%s)"
                val = (i[5], f"{event.message.id}_{message.id}")
                cursor.execute(sql, val)
                conn.commit()
                cursor.close()
            elif i[8]!="0":
                message = await clientvalue.send_file(entity=int(i[5]), file=i[8],
                                                      caption=cleaned_text + "\n" + str(
                                                          i[7] + "\n"),reply_to=new_message_id)
                cursor = conn.cursor()
                sql = "INSERT INTO ids2 (channel,dict) VALUES (%s,%s)"
                val = (i[5], f"{event.message.id}_{message.id}")
                cursor.execute(sql, val)
                conn.commit()
                cursor.close()

            else:
                try:
                    message = await clientvalue.send_message(int(i[5]), cleaned_text + "\n" + str(
                        i[7] + "\n"), reply_to=new_message_id, )
                    cursor = conn.cursor()
                    sql = "INSERT INTO ids2 (channel,dict) VALUES (%s,%s)"
                    val = (i[5], f"{event.message.id}_{message.id}")
                    cursor.execute(sql, val)
                    conn.commit()
                    cursor.close()

                except Exception as e:
                    print(e, i[4])

        else:
            match = await find_profit(text, i[11])
            if len(match) != 0 and i[11] != "0":
                numbers = sorted(match, key=float)
                print(numbers)
                new = await add_profit_to_image(image_path=i[8], profit_values=numbers[-1],size=i[10])
                message = await clientvalue.send_file(entity=int(i[5]), file=new,
                                                      caption=cleaned_text + "\n" + str(
                                                          i[7] + "\n"), reply_to=new_message_id)
                cursor = conn.cursor()
                sql = "INSERT INTO ids2 (channel,dict) VALUES (%s,%s)"
                val = (i[5], f"{event.message.id}_{message.id}")
                cursor.execute(sql, val)
                conn.commit()
                cursor.close()
            else:
                try:
                    message = await clientvalue.send_message(int(i[5]), cleaned_text + "\n" + str(
                        i[7] + "\n"), reply_to=new_message_id)

                    cursor = conn.cursor()
                    sql = "INSERT INTO ids2 (channel,dict) VALUES (%s,%s)"
                    val = (i[5], f"{event.message.id}_{message.id}")
                    cursor.execute(sql, val)
                    conn.commit()
                    cursor.close()
                    print(cursor.rowcount, "record inserted.")

                except Exception as e:
                    print(f"{e}\n{i[5]}")


async def copy_nonreplay(event,i,clientvalue):
    conn=create_db_connection()
    cleaned_text = remove_links(event.message.message)
    total = i[9].split(",")
    for t in total:
        chain = t.split("=")
        try:
            cleaned_text = re.sub(chain[0], chain[1], cleaned_text)
        except:
            pass
    if event.message.text:
        text = event.message.text
        if event.message.photo:

            print(i[11])
            match = await find_profit(text, i[11])
            print(match)
            print("photo")

            if len(match)!=0 and i[11]!="0":
                numbers = sorted(match, key=float)
                print(numbers)
                new = await add_profit_to_image(image_path=i[8], profit_values=numbers[-1],size=i[10])
                message = await clientvalue.send_file(entity=int(i[5]), file=new,
                                                      caption=cleaned_text + "\n" + str(
                                                          i[7] + "\n"))
                cursor = conn.cursor()
                sql = "INSERT INTO ids2 (channel,dict) VALUES (%s,%s)"
                val = (i[5], f"{event.message.id}_{message.id}")
                cursor.execute(sql, val)
                conn.commit()
                cursor.close()
            elif i[8]!="0":
                message = await clientvalue.send_file(entity=int(i[5]), file=i[8],
                                                      caption=cleaned_text + "\n" + str(
                                                          i[7] + "\n"))
                cursor = conn.cursor()
                sql = "INSERT INTO ids2 (channel,dict) VALUES (%s,%s)"
                val = (i[5], f"{event.message.id}_{message.id}")
                cursor.execute(sql, val)
                conn.commit()
                cursor.close()

            else:
                try:
                    message = await clientvalue.send_message(int(i[5]), cleaned_text + "\n" + str(
                        i[7] + "\n"))
                    cursor = conn.cursor()
                    sql = "INSERT INTO ids2 (channel,dict) VALUES (%s,%s)"
                    val = (i[5], f"{event.message.id}_{message.id}")
                    cursor.execute(sql, val)
                    conn.commit()
                    cursor.close()
                    print(cursor.rowcount, "record inserted.")

                except Exception as e:
                    print(f"{e}\n{i[5]}")

        else:

            match = await find_profit(text, i[11])

            print("message")

            if len(match)!=0 and i[11]!="0":
                numbers = sorted(match, key=float)
                print(numbers)
                new = await add_profit_to_image(image_path=i[8], profit_values=numbers[-1],size=i[10])
                print("اومد")
                message = await clientvalue.send_file(entity=int(i[5]), file=new,
                                                      caption=cleaned_text + "\n" + str(
                                                          i[7] + "\n"))
                cursor = conn.cursor()
                sql = "INSERT INTO ids2 (channel,dict) VALUES (%s,%s)"
                val = (i[5], f"{event.message.id}_{message.id}")
                cursor.execute(sql, val)
                conn.commit()
                cursor.close()
            else:
                try:
                    message = await clientvalue.send_message(int(i[5]), cleaned_text + "\n" + str(
                        i[7] + "\n"))
                    cursor = conn.cursor()
                    sql = "INSERT INTO ids2 (channel,dict) VALUES (%s,%s)"
                    val = (i[5], f"{event.message.id}_{message.id}")
                    cursor.execute(sql, val)
                    conn.commit()
                    cursor.close()
                    print(cursor.rowcount, "record inserted.")
                except Exception as e:
                    print(f"{e}\n{i[5]}")

    else:
        print("نوع پیام ناشناخته است.")

async def copy(event,clientkey,clientvalue):
    my_channels=get_my_channels(clientkey)
    try:

        if f"-100{event.message.peer_id.channel_id}" in my_channels:

            if event.is_reply:
                reply_to_msg = await event.get_reply_message()
                target_channels = get_target_channels(clientkey)
                mytasks = []
                for x, i in enumerate(target_channels):
                    task = copy_isreplay(event,i,reply_to_msg,clientvalue)
                    mytasks.append(task)
                await asyncio.gather(*mytasks)

            else:

                target_channels = get_target_channels(clientkey)


                print(f"{target_channels}----------------")
                mitasks = []
                for x, i in enumerate(target_channels):
                    task = copy_nonreplay(event,i,clientvalue)
                    mitasks.append(task)
                await asyncio.gather(*mitasks)

    except Exception as e:
        print("چیزی نیست")
        print(e)


async def edit(event,clientkey,clientvalue):
    global list_map
    conn=create_db_connection()
    cursor = conn.cursor()
    query = f"SELECT * FROM ids2;"
    cursor.execute(query)
    myresult = cursor.fetchall()
    cursor.close()

    for ids in myresult:
        if event.message.id == int(ids[2].split("_")[0]):
            new_message_id = int(ids[2].split("_")[1])
            caption = remove_links(event.message.text)
            await clientvalue.edit_message(int(ids[1]), new_message_id, caption)


async def delete(event,clientkey,clientvalue):

    conn=create_db_connection()

    cursor = conn.cursor()
    query = f"SELECT * FROM ids2;"
    cursor.execute(query)
    myresult = cursor.fetchall()
    cursor.close()
    for ids in myresult:
       for g in event.deleted_ids:
            if g == int(ids[2].split("_")[0]):
                new_message_id = int(ids[2].split("_")[1])
                await clientvalue.delete_messages(int(ids[1]), new_message_id)
                break


@user_client.on(events.NewMessage(incoming=True))
async def message(event):
    global messages_map, list_map,clientstruncate,clients
    conn=create_db_connection()
    client_dict={}
    print(clients)
    for client in clients:
        me = await client.get_me()
        client_dict[me.username]=client
    tasks = []
    print(client_dict)
    for clientkey in client_dict.keys():
        client_value = client_dict[clientkey]
        task = copy(event, clientkey, client_value)
        tasks.append(task)
    await asyncio.gather(*tasks)

@user_client.on(events.MessageEdited())
async def edit_message(event):
    global list_map,clients
    client_dict={}
    print(clients)
    for client in clients:
        me = await client.get_me()
        client_dict[me.username]=client
    tasks_edit = []
    for clientkey in client_dict.keys():
        client_value = client_dict[clientkey]
        task = edit(event, clientkey, client_value)
        tasks_edit.append(task)
    await asyncio.gather(*tasks_edit)

@user_client.on(events.MessageDeleted())
async def delete_message(event):
    global list_map
    client_dict={}
    for client in clients:
        me = await client.get_me()
        client_dict[me.username]=client
    tasks_del = []
    for clientkey in client_dict.keys():
        client_value = client_dict[clientkey]
        task = delete(event, clientkey, client_value)
        tasks_del.append(task)

    await asyncio.gather(*tasks_del)




async def run_client_loop(client):
    """
    Runs the client's event loop and handles disconnection gracefully.
    """
    try:
        await client.run_until_disconnected()
    except Exception as e:
        print(f"Client {client.session.filename} disconnected with error: {e}")


async def main():
    global clients, user_client_running
    try:
        initialize_database()
        # Start the bot client first
        await bot_client.start(bot_token=bot_token)
        print("Bot client started...")

        # Connect the user client and check for an existing session
        await user_client.connect()

        # Load and start secondary clients
        clients_with_tokens = await load_clients()

        # We use a temporary list to add clients that start successfully
        started_clients = []
        for client, token in clients_with_tokens:
            try:
                print(f"Starting client {client.session.filename}...")
                await client.start(bot_token=token)
                # If start is successful, add to list and create background task for its loop
                started_clients.append(client)
                asyncio.create_task(run_client_loop(client))
            except Exception as e:
                print(f"Error starting client {client.session.filename}: {e}. This client will be ignored.")

        # Now, update the global clients list with only the ones that started
        clients.clear()
        clients.extend(started_clients)

        print(f"Successfully started {len(clients)} secondary clients.")

        # Run main clients concurrently
        tasks = [
            bot_client.run_until_disconnected(),
        ]

        if await user_client.is_user_authorized():
            print("User client is already authorized and connected.")
            tasks.append(user_client.run_until_disconnected())
            user_client_running = True
        else:
            print("User client is not authorized. Admin needs to log in via the bot.")

        await asyncio.gather(*tasks)

    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    asyncio.run(main())
