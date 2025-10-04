import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# جلب التوكن من البيئة
TOKEN = os.getenv('TOKEN')

if not TOKEN:
    print("❌ ERROR: TOKEN not found in environment!")
    exit(1)

print(f"✅ Token loaded successfully: {TOKEN[:10]}...")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('✅ البوت يعمل بنجاح!')

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(f'مرحباً {name} 👋')

def main():
    try:
        # بناء التطبيق
        app = Application.builder().token(TOKEN).build()
        
        # إضافة الأوامر
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("hello", hello))
        
        print("🚀 البوت يبدأ التشغيل...")
        app.run_polling()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
