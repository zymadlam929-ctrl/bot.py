import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# طريقة أفضل لقراءة التوكن
TOKEN = os.getenv('TOKEN')

# تحقق إذا التوكن موجود
if not TOKEN:
    print("❌ ERROR: TOKEN not found in environment variables!")
    print("Available environment variables:", list(os.environ.keys()))
    exit(1)

print(f"✅ Token loaded: {TOKEN[:10]}...")  # طباعة جزء من التوكن للتأكد

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('البوت يعمل! ✅')

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'مرحباً {update.effective_user.first_name}')

try:
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hello", hello))
    
    print("🤖 البوت يبدأ التشغيل...")
    app.run_polling()
    
except Exception as e:
    print(f"❌ Error: {e}")
