import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)

# قراءة التوكن
TOKEN = os.getenv('TOKEN')

if not TOKEN:
    print("❌ ERROR: TOKEN not found!")
    exit(1)

print(f"✅ Token loaded: {TOKEN[:10]}...")

def start(update: Update, context: CallbackContext):
    update.message.reply_text('البوت يعمل! ✅')

def hello(update: Update, context: CallbackContext):
    update.message.reply_text(f'مرحباً {update.effective_user.first_name}')

try:
    # استخدام Updater بدلاً من ApplicationBuilder
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("hello", hello))
    
    print("🤖 البوت يبدأ التشغيل...")
    updater.start_polling()
    updater.idle()
    
except Exception as e:
    print(f"❌ Error: {e}")
