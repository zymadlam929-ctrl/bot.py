import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv('TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('✅ البوت يعمل بنجاح!')

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'مرحباً {update.effective_user.first_name}')

def main():
    # استخدم Application بدلاً من Updater
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hello", hello))
    
    print("🚀 البوت يبدأ التشغيل...")
    app.run_polling()

if __name__ == "__main__":
    main()
