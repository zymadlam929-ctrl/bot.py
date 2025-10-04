import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv('TOKEN')

if not TOKEN:
    print("❌ ERROR: TOKEN not found!")
    exit(1)

print(f"✅ Token loaded: {TOKEN[:10]}...")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('البوت يعمل! ✅')

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'مرحباً {update.effective_user.first_name}')

async def main():
    # استخدام Application الحديثة
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hello", hello))
    
    print("🤖 البوت يبدأ التشغيل...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
