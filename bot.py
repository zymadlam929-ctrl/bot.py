import asyncio
import datetime
import json
import os
import time

import aiohttp
import pandas as pd
import ta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    JobQueue,
    MessageHandler,
    filters,
)

# --- إعدادات ---
TOKEN = "8356973371:AAFOS8uGVn43xOqtn1yOE7Sy8ABMjOGS4Wo"
CHANNEL_USERNAME = "@h_h7_7_0HAYAFx967"

OWNER_ID = 7956344177
OWNER_USERNAME = "@HlAY_F_VIP"
ADMIN_ID = 7892296736
ADMIN_USERNAME = "@H_DRJ"

ADMINS = {
    OWNER_ID: OWNER_USERNAME,
    ADMIN_ID: ADMIN_USERNAME,
}

ALLOWED_USERS_FILE = "allowed_users.json"
DISALLOWED_USERS_FILE = "disallowed_users.json"
BOT_STATS_FILE = "bot_stats.json"
USER_HISTORIES_FILE = "user_histories.json"

# تحميل وحفظ الملفات بصيغة JSON كـ Set
def load_json_set(filename):
    if os.path.isfile(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data)
        except Exception:
            return set()
    else:
        return set()

def save_json_set(filename, data_set):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(list(data_set), f)
    except Exception:
        pass

def load_json_dict(filename):
    if os.path.isfile(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    else:
        return {}

def save_json_dict(filename, data_dict):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data_dict, f)
    except Exception:
        pass

ALLOWED_USERS = load_json_set(ALLOWED_USERS_FILE)
DISALLOWED_USERS = load_json_set(DISALLOWED_USERS_FILE)
BOT_STATS = load_json_dict(BOT_STATS_FILE)
USER_HISTORIES = load_json_dict(USER_HISTORIES_FILE)

# أضف المالك والمشرف تلقائياً إلى المصرح لهم وعدم إضافتهم للمرفوضين
for admin_id in ADMINS.keys():
    ALLOWED_USERS.add(admin_id)
    if admin_id in DISALLOWED_USERS:
        DISALLOWED_USERS.remove(admin_id)

save_json_set(ALLOWED_USERS_FILE, ALLOWED_USERS)
save_json_set(DISALLOWED_USERS_FILE, DISALLOWED_USERS)

# تهيئة إحصائيات البوت إذا لم تكن موجودة
if not BOT_STATS:
    BOT_STATS = {
        "total_analyses": 0,
        "unique_users": 0,
        "up_signals": 0,
        "down_signals": 0,
        "allowed_users_count": len(ALLOWED_USERS),
        "disallowed_users_count": len(DISALLOWED_USERS),
        "unique_users_set": []
    }
    save_json_dict(BOT_STATS_FILE, BOT_STATS)

pairs = [
    "EUR/USD (OTC)", "USD/JPY (OTC)", "GBP/USD (OTC)", "AUD/USD (OTC)",
    "USD/CAD (OTC)", "USD/CHF (OTC)", "NZD/USD (OTC)", "EUR/GBP (OTC)",
    "EUR/JPY (OTC)", "GBP/JPY (OTC)", "CAD/JPY (OTC)", "CHF/JPY (OTC)",
]
PAIR_SYMBOLS = {pair: pair.split(" ")[0].replace("/", "_") for pair in pairs}

durations = [
    "5 ثواني", "10 ثواني", "15 ثانية", "30 ثانية",
    "1 دقيقة", "2 دقائق", "3 دقائق", "4 دقائق",
    "5 دقائق", "10 دقائق", "15 دقيقة", "20 دقيقة",
    "30 دقيقة", "40 دقيقة", "50 دقيقة", "1 ساعة",
]

API_KEYS_TWELVE = [
    "cfff759f911740cfb3f631f4366c2e78",
    "7efc760c379c4f0d8ca450d36815268c",
    "f3c86c4ef530409f985efbe31801a245",
    "c7552cc6161849e6bc9be6c3f0a5f454",
    "0a4140856ab34d0389958a686a3b2744",
]
API_KEYS_ALPHA = [
    "YQ8RAO9IUPYFX6IK",
    "N6TQ3S7BZKMZAK2Z",
    "N8U9E29IIA5R7M83",
    "NDYJVKJ2A7V3NQCQ",
]

NEWS_API_KEY = "ba9c6077d4a9426694f823cbd2a17f83"

# --- نصوص متعددة اللغات ---
TEXTS = {
    "ar": {
        "welcome": "مرحباً بك في بوت هـياف للتوصيات المدعّمة بالذكاء الاصطناعي وتحليل فني!\nاختر اللغة لبدء الاستخدام:",
        "select_pair": "اختر زوج العملة من القائمة:",
        "select_duration": "اختر مدة الصفقة:",
        "analyzing": "🔄 جاري تحليل البيانات...",
        "analyzing_progress": "🔄 جاري تحليل البيانات...\n{bar} {percent}%",
        "no_data": "❌ لم يتم استرجاع بيانات السعر من المصادر المتاحة. تأكد من اتصالك بالإنترنت أو جرّب لاحقاً.",
        "wait_20_seconds": "⚠️ يرجى الانتظار 20 ثانية بين كل طلب.",
        "no_pair_selected": "يرجى اختيار زوج العملة أولاً.",
        "check_subscription": "يرجى الاشتراك في قناة البوت واستخدام زر التحقق للمتابعة.",
        "subscription_confirmed": "✅ تم التحقق من الاشتراك! اختر زوج العملة للمتابعة.",
        "subscription_required": "🚸| عذراً عزيزي...\n🔰| عليك الاشتراك في قناة البوت لتتمكن من استخدامه\n\n- https://t.me/h_h7_7_0HAYAFx967\n\n‼️| اشترك ثم ارسل /start",
        "admin_panel": "👥 لوحة المشرف",
        "dashboard": "📊 القائمة العرضية",
        "how_it_works": "❓ كيف يعمل البوت",
        "back": "⬅️ رجوع",
        "retry_analysis": "🔄 تحليل مرة أخرى",
        "select_other_pair": "🔄 اختيار زوج آخر",
        "signal_info": """📊 معلومات الإشارة:

📌 {pair} - {duration}
📈 إعداد السوق:
📍 RSI: {rsi}
📍 MACD: {macd} / الإشارة: {signal}
📍 SMA: {sma}
📍 EMA: {ema}
📍 Bollinger Bands: [{bb_lower} - {bb_upper}]
📍 Stochastic: %K={stoch_k} / %D={stoch_d}
📍 ADX: {adx}
📍 CCI: {cci}
📍 Williams %R: {willr}
📍 OBV: {obv}
📍 ATR: {atr}
📍 Volume: {volume}
📍 الاتجاه المتوقع: {direction}
✅ موثوقية: {confidence}%
🧠 تحليل الذكاء الاصطناعي والتحليل الإخباري
🔑 مصدر البيانات: {source} (مفتاح: {used_key})""",
        "personal_stats": "📊 **الإحصائيات الشخصية**",
        "total_signals": "📈 إجمالي إشاراتك",
        "up_signals": "🟢 إشارات الصعود",
        "down_signals": "🔴 إشارات الهبوط",
        "top_pairs": "🏆 **أكثر الأزواج استخداماً:**",
        "top_durations": "⏰ **أكثر الفترات استخداماً:**",
        "bot_stats": "📈 **إحصائيات البوت العامة:**",
        "total_analyses": "إجمالي التحليلات",
        "active_users": "المستخدمين النشطين",
        "last_recommendations": "✳️ **آخر 3 توصيات:**",
        "no_recommendations": "لا توجد توصيات محفوظة.",
        "processing_signals": "⏳ جاري تحليل الإشارات يرجى الانتظار...",
        "admin_select_action": "اختر العملية التي تريدها:",
        "broadcast_allowed": "📢 إرسال رسالة جماعية للمسموح لهم",
        "broadcast_disallowed": "📢 إرسال رسالة جماعية لغير المسموح لهم",
        "user_stats": "👥 إحصائيات المستخدمين",
        "broadcast_instruction": "📩 أرسل الرسالة (نص، صورة، صوت، إلخ) لإرسالها للمستخدمين {target}.",
        "broadcast_target_allowed": "المسموح لهم",
        "broadcast_target_disallowed": "غير المسموح لهم",
        "broadcast_sending": "🔔 جاري إرسال الرسالة إلى {target}...",
        "broadcast_sent": "✅ تم إرسال الرسالة إلى {count} مستخدماً.",
        "user_stats_title": "📊 إحصائيات المستخدمين:",
        "allowed_users": "👥 عدد المسموح لهم",
        "disallowed_users": "🚫 عدد غير المسموح لهم",
        "unique_users": "👤 المستخدمين الفريدين",
        "how_bot_works": """🤖 كيف يعمل بوت هـياف:
✅ يعتمد على تحليل ذكي باستخدام مؤشرات RSI، MACD، Bollinger Bands، وSMA، وStochastic.
📉 يحلل السوق لحظياً ويقدم توصيات صعود أو هبوط دقيقة.
📌 يدعم أزواج OTC في منصة Pocket Option.
⏱️ يمكنك اختيار فريم زمني من 5 ثواني حتى 1 ساعة.
⚠️ يرجى ملاحظة أن المؤشرات لا تعطي ضمان 100% ويجب الحذر في التداول.

📌 توضيح حول التداول:
التداول في الأسواق المالية يتضمن مخاطر عالية، والاعتماد على المؤشرات الفنية يساعد في اتخاذ قرارات أفضل لكن لا يضمن النجاح.
يُنصح بإدارة رأس المال وتحديد نقاط وقف الخسارة والربح قبل الدخول في أي صفقة.""",
        "no_permission": "🚫 ليس لديك صلاحية استخدام هذا الأمر.",
        "provide_user_id": "يرجى كتابة معرف المستخدم لإضافته. مثال: /allow 123456789",
        "invalid_user_id": "المعرف يجب أن يكون رقماً صحيحاً.",
        "user_already_allowed": "✅ المستخدم مفوض مسبقاً.",
        "user_allowed_success": "✅ تم منح صلاحية استخدام بوت هـياف للمستخدم: {user_id}.\nأهلاً به!",
        "user_not_allowed": "❌ المستخدم غير مفوض أساساً.",
        "user_disallowed_success": "⛔️ تم إلغاء صلاحية المستخدم: {user_id}.\nلم يعد بإمكانه استخدام البوت.",
        "welcome_granted": "✅ تم منح صلاحية استخدام بوت هـياف. أهلاً بك!",
        "permission_revoked": "❌ تم إلغاء صلاحية استخدام بوت هـياف.",
        "denied_access": "❌ هذا البوت خاص للمصرح لهم فقط. لا يمكنك استخدامه إلا بعد موافقة المشرفين🚀📩.\n                  1                  @H_DRJ\n                  2                @HlAY_F_VIP\n\nيرجى التواصل معهم للحصول على الصلاحية استخدام الربوت. 📈🔥🚀..",
        "times": "مرة"
    },
    "en": {
        "welcome": "Welcome to HAYAF Bot for AI-supported trading signals and technical analysis!\nChoose your language to start:",
        "select_pair": "Select a currency pair:",
        "select_duration": "Choose duration:",
        "analyzing": "🔄 Analyzing...",
        "analyzing_progress": "🔄 Analyzing...\n{bar} {percent}%",
        "no_data": "❌ Failed to retrieve price data from available sources. Check your internet connection or try again later.",
        "wait_20_seconds": "⚠️ Please wait 20 seconds between requests.",
        "no_pair_selected": "Please select a currency pair first.",
        "check_subscription": "Please subscribe to the bot channel and use the check button to continue.",
        "subscription_confirmed": "✅ Subscription confirmed! Select a currency pair to continue.",
        "subscription_required": "🚸| Sorry dear...\n🔰| You must subscribe to the bot channel to be able to use it\n\n- https://t.me/h_h7_7_0HAYAFx967\n\n‼️| Subscribe then send /start",
        "admin_panel": "👥 Admin Panel",
        "dashboard": "📊 Dashboard",
        "how_it_works": "❓ How it works",
        "back": "⬅️ Back",
        "retry_analysis": "🔄 Analyze again",
        "select_other_pair": "🔄 Select another pair",
        "signal_info": """📊 Signal Information:

📌 {pair} - {duration}
📈 Market Setup:
📍 RSI: {rsi}
📍 MACD: {macd} / Signal: {signal}
📍 SMA: {sma}
📍 EMA: {ema}
📍 Bollinger Bands: [{bb_lower} - {bb_upper}]
📍 Stochastic: %K={stoch_k} / %D={stoch_d}
📍 ADX: {adx}
📍 CCI: {cci}
📍 Williams %R: {willr}
📍 OBV: {obv}
📍 ATR: {atr}
📍 Volume: {volume}
📍 Expected Direction: {direction}
✅ Confidence: {confidence}%
🧠 AI Analysis and News Analysis
🔑 Data Source: {source} (Key: {used_key})""",
        "personal_stats": "📊 **Personal Statistics**",
        "total_signals": "📈 Your total signals",
        "up_signals": "🟢 Up signals",
        "down_signals": "🔴 Down signals",
        "top_pairs": "🏆 **Most used pairs:**",
        "top_durations": "⏰ **Most used durations:**",
        "bot_stats": "📈 **Bot General Statistics:**",
        "total_analyses": "Total analyses",
        "active_users": "Active users",
        "last_recommendations": "✳️ **Last 3 recommendations:**",
        "no_recommendations": "No saved recommendations.",
        "processing_signals": "⏳ Processing signals, please wait...",
        "admin_select_action": "Select the action you want:",
        "broadcast_allowed": "📢 Broadcast to allowed users",
        "broadcast_disallowed": "📢 Broadcast to disallowed users",
        "user_stats": "👥 User statistics",
        "broadcast_instruction": "📩 Send the message (text, photo, audio, etc.) to broadcast to {target} users.",
        "broadcast_target_allowed": "allowed users",
        "broadcast_target_disallowed": "disallowed users",
        "broadcast_sending": "🔔 Sending message to {target}...",
        "broadcast_sent": "✅ Message sent to {count} users.",
        "user_stats_title": "📊 User Statistics:",
        "allowed_users": "👥 Allowed users",
        "disallowed_users": "🚫 Disallowed users",
        "unique_users": "👤 Unique users",
        "how_bot_works": """🤖 How HAYAF Bot works:
✅ Uses smart analysis with RSI, MACD, Bollinger Bands, SMA, and Stochastic indicators.
📉 Analyzes the market in real-time and provides accurate Up or Down signals.
📌 Supports OTC pairs on Pocket Option platform.
⏱️ You can select timeframes from 5 seconds up to 1 hour.
⚠️ Please note indicators do not guarantee 100% accuracy; trade carefully.

📌 Trading Disclaimer:
Trading financial markets involves high risk. Indicators help to make better decisions but do not guarantee success.
Always manage your capital and set stop-loss and take-profit points.""",
        "no_permission": "🚫 You do not have permission to use this command.",
        "provide_user_id": "Please provide the user ID to allow. Example: /allow 123456789",
        "invalid_user_id": "The user ID must be a valid number.",
        "user_already_allowed": "✅ User already has permission.",
        "user_allowed_success": "✅ Permission granted to user: {user_id}. Welcome!",
        "user_not_allowed": "❌ The user is not authorized to use the bot.",
        "user_disallowed_success": "⛔️ Permission revoked for user: {user_id}.\nThey can no longer use the bot.",
        "welcome_granted": "✅ You have been granted permission to use Hayaf Bot. Welcome!",
        "permission_revoked": "❌ Your permission to use Hayaf Bot has been revoked.",
        "denied_access": "❌ This bot is private for authorized users only. You cannot use it until approved by the admins🚀📩.\n                  1                  @H_DRJ\n                  2                @HlAY_F_VIP\n\nPlease contact them to get permission to use the bot. 📈🔥🚀..",
        "times": "times"
    }
}

def get_text(lang, key, **kwargs):
    """الحصول على النص بناءً على اللغة والمفتاح"""
    text = TEXTS.get(lang, TEXTS["ar"]).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

# --- دوال الصلاحيات والرسائل ---

def user_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USERS or user_id in ADMINS

def user_is_admin(user_id: int) -> bool:
    return user_id in ADMINS

async def deny_access_custom_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = context.user_data.get("lang", "ar")
    text = get_text(lang, "denied_access")
    if update.message:
        await update.message.reply_text(text)
    elif update.callback_query:
        await update.callback_query.answer(text, show_alert=True)

async def deny_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in DISALLOWED_USERS and user_id not in ALLOWED_USERS and user_id not in ADMINS:
        DISALLOWED_USERS.add(user_id)
        BOT_STATS["disallowed_users_count"] = len(DISALLOWED_USERS)
        save_json_set(DISALLOWED_USERS_FILE, DISALLOWED_USERS)
        save_json_dict(BOT_STATS_FILE, BOT_STATS)
    await deny_access_custom_message(update, context)

async def allowed_welcome_message(user_id: int, lang: str, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat = await context.bot.get_chat(user_id)
        text = get_text(lang, "welcome_granted")
        await chat.send_message(text)
    except Exception:
        pass

async def disallow_message(user_id: int, lang: str, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat = await context.bot.get_chat(user_id)
        text = get_text(lang, "permission_revoked")
        await chat.send_message(text)
    except Exception:
        pass

# --- لوحات المفاتيح ---

def language_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇸🇦 العربي", callback_data="lang_ar"),
                InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
            ]
        ]
    )

def pairs_keyboard(lang, user_id=None):
    keyboard, row = [], []
    for i, pair in enumerate(pairs, 1):
        row.append(InlineKeyboardButton(pair, callback_data=f"pair_{pair}"))
        if i % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    main_buttons = [
        InlineKeyboardButton(
            get_text(lang, "dashboard"),
            callback_data="show_dashboard",
        ),
    ]
    if user_id in ADMINS:
        main_buttons.append(
            InlineKeyboardButton(
                get_text(lang, "admin_panel"),
                callback_data="admin_panel",
            )
        )
    keyboard.append(main_buttons)

    keyboard.append(
        [
            InlineKeyboardButton(
                get_text(lang, "how_it_works"),
                callback_data="how_it_works",
            ),
            InlineKeyboardButton(
                get_text(lang, "back"),
                callback_data="back_to_language",
            ),
        ]
    )
    return InlineKeyboardMarkup(keyboard)

def durations_keyboard(lang):
    keyboard, row = [], []
    for i, dur in enumerate(durations, 1):
        row.append(InlineKeyboardButton(dur, callback_data=f"duration_{dur}"))
        if i % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append(
        [InlineKeyboardButton(get_text(lang, "back"), callback_data="back_to_pairs")]
    )
    return InlineKeyboardMarkup(keyboard)

def admin_keyboard(lang):
    keyboard = [
        [InlineKeyboardButton(get_text(lang, "broadcast_allowed"), callback_data="broadcast_allowed")],
        [InlineKeyboardButton(get_text(lang, "broadcast_disallowed"), callback_data="broadcast_disallowed")],
        [InlineKeyboardButton(get_text(lang, "user_stats"), callback_data="user_stats")],
        [InlineKeyboardButton(get_text(lang, "back"), callback_data="back_to_pairs")],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- التذكيرات الدورية للمستخدمين غير المصرح لهم ---

async def send_registration_reminder(context: ContextTypes.DEFAULT_TYPE):
    for user_id in list(DISALLOWED_USERS):
        try:
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("تسجيـل 🟢", url="https://pocket-friends.com/r/ry7kypfjm2")]]
            )
            text = "⏳ هل قمت بالتسجيل بالفعل؟\n\nإذا لا، فالوقت مناسب الآن 👇"
            await context.bot.send_message(user_id, text, reply_markup=keyboard)
        except Exception:
            pass

async def send_evening_followup(context: ContextTypes.DEFAULT_TYPE):
    for user_id in list(DISALLOWED_USERS):
        try:
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("تسجيل 🟢", url="https://pocket-friends.com/r/ry7kypfjm2")]]
            )
            text = (
                "🤔 هل أنت من الأشخاص الذين يبدأون دائمًا ولا ينتهون أبدًا؟\n\n"
                "كنت على بعد خطوة من الهدف.\n"
                "لقد رأيت بالفعل كيف يعمل كل شيء. ومع ذلك، ما زلت تنتظر؟\n\n"
                "لا تؤجل، اشترك في الإشارات الآن 👇"
            )
            await context.bot.send_message(user_id, text, reply_markup=keyboard)
        except Exception:
            pass

# --- عداد 1 الى 100 لإحصائيات المستخدمين ---

async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not user_allowed(user_id):
        await deny_access(update, context)
        return
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "ar")
    try:
        await q.message.delete()
    except Exception:
        pass

    # إرسال رسالة الانتظار فقط
    msg = await q.message.chat.send_message(get_text(lang, "processing_signals"))

    # الحصول على تاريخ المستخدم من البيانات المحفوظة
    user_history = USER_HISTORIES.get(str(user_id), [])
    
    # إحصائيات المستخدم الشخصية
    user_total_signals = len(user_history)
    user_up_signals = len([h for h in user_history if "صعود" in h['direction'] or "Up" in h['direction']])
    user_down_signals = len([h for h in user_history if "هبوط" in h['direction'] or "Down" in h['direction']])
    
    # الأزواج الأكثر استخداماً
    pair_counts = {}
    for h in user_history:
        pair = h['pair']
        pair_counts[pair] = pair_counts.get(pair, 0) + 1
    
    top_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # الفترات الزمنية الأكثر استخداماً
    duration_counts = {}
    for h in user_history:
        duration = h['duration']
        duration_counts[duration] = duration_counts.get(duration, 0) + 1
    
    top_durations = sorted(duration_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    # استخدام البيانات المحفوظة للإحصائيات العامة
    total_analyses = BOT_STATS.get("total_analyses", 0)
    unique_users = BOT_STATS.get("unique_users", 0)
    up_count = BOT_STATS.get("up_signals", 0)
    down_count = BOT_STATS.get("down_signals", 0)

    # إنشاء نص الإحصائيات
    text = f"{get_text(lang, 'personal_stats')}\n\n"
    text += f"{get_text(lang, 'total_signals')}: {user_total_signals}\n"
    text += f"{get_text(lang, 'up_signals')}: {user_up_signals}\n"
    text += f"{get_text(lang, 'down_signals')}: {user_down_signals}\n\n"
    
    if top_pairs:
        text += f"{get_text(lang, 'top_pairs')}\n"
        for pair, count in top_pairs:
            text += f"• {pair}: {count} {get_text(lang, 'times')}\n"
        text += "\n"
    
    if top_durations:
        text += f"{get_text(lang, 'top_durations')}\n"
        for duration, count in top_durations:
            text += f"• {duration}: {count} {get_text(lang, 'times')}\n"
        text += "\n"
    
    text += f"{get_text(lang, 'bot_stats')}\n"
    text += f"• {get_text(lang, 'total_analyses')}: {total_analyses}\n"
    text += f"• {get_text(lang, 'active_users')}: {unique_users}\n"
    text += f"• {get_text(lang, 'up_signals')}: {up_count}\n"
    text += f"• {get_text(lang, 'down_signals')}: {down_count}\n\n"

    text += f"{get_text(lang, 'last_recommendations')}\n"
    if not user_history:
        text += get_text(lang, "no_recommendations")
    else:
        for h in user_history[-3:]:
            text += (
                f"• {h['pair']} - {h['duration']}\n"
                f"  📊 {h['direction']}\n"
                f"  🕒 {h['time']}\n\n"
            )

    # تعديل الرسالة بالإحصائيات
    await msg.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(get_text(lang, "back"), callback_data="back_to_pairs")]]
        ),
    )

# --- إحصائيات المستخدمين ---

async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not user_is_admin(user_id):
        await deny_access(update, context)
        return
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "ar")
    
    allowed_count = BOT_STATS.get("allowed_users_count", len(ALLOWED_USERS))
    disallowed_count = BOT_STATS.get("disallowed_users_count", len(DISALLOWED_USERS))
    total_analyses = BOT_STATS.get("total_analyses", 0)
    unique_users = BOT_STATS.get("unique_users", 0)
    
    text = (
        f"{get_text(lang, 'user_stats_title')}\n\n"
        f"{get_text(lang, 'allowed_users')}: {allowed_count}\n"
        f"{get_text(lang, 'disallowed_users')}: {disallowed_count}\n"
        f"{get_text(lang, 'total_analyses')}: {total_analyses}\n"
        f"{get_text(lang, 'unique_users')}: {unique_users}\n\n"
        f"🆔 {get_text(lang, 'allowed_users')}: {', '.join(map(str, list(ALLOWED_USERS)[:10]))}{'...' if len(ALLOWED_USERS) > 10 else ''}\n"
        f"🆔 {get_text(lang, 'disallowed_users')}: {', '.join(map(str, list(DISALLOWED_USERS)[:10]))}{'...' if len(DISALLOWED_USERS) > 10 else ''}"
    )
    
    await q.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(get_text(lang, "back"), callback_data="admin_panel")]]
        ),
    )

# --- لوحة االمشرفين⚙️---

BROADCAST_MODE = {}

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not user_is_admin(user_id):
        await deny_access(update, context)
        return
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "ar")
    try:
        await q.message.delete()
    except Exception:
        pass
    await q.message.chat.send_message(
        get_text(lang, "admin_select_action"),
        reply_markup=admin_keyboard(lang),
    )

async def start_broadcast_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user_id = update.effective_user.id
    await q.answer()
    lang = context.user_data.get("lang", "ar")

    if not user_is_admin(user_id):
        await deny_access(update, context)
        return

    action = q.data
    target_group = "allowed" if action == "broadcast_allowed" else "disallowed"
    BROADCAST_MODE[user_id] = target_group

    await q.message.delete()
    
    target_text = get_text(lang, f"broadcast_target_{target_group}")
    text = get_text(lang, "broadcast_instruction", target=target_text)
    
    await q.message.chat.send_message(
        text,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(get_text(lang, "back"), callback_data="back_to_admin")]]
        ),
    )

async def receive_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in BROADCAST_MODE:
        return
        
    target_group = BROADCAST_MODE[user_id]
    lang = context.user_data.get("lang", "ar")

    if target_group == "allowed":
        recipients = ALLOWED_USERS
        group_text = get_text(lang, "broadcast_target_allowed")
    else:
        recipients = DISALLOWED_USERS
        group_text = get_text(lang, "broadcast_target_disallowed")

    await update.message.reply_text(get_text(lang, "broadcast_sending", target=group_text))

    count = 0
    message = update.message
    
    for uid in recipients:
        try:
            if message.text:
                await context.bot.send_message(uid, message.text)
            elif message.photo:
                await context.bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption)
            elif message.audio:
                await context.bot.send_audio(uid, message.audio.file_id, caption=message.caption)
            elif message.video:
                await context.bot.send_video(uid, message.video.file_id, caption=message.caption)
            elif message.document:
                await context.bot.send_document(uid, message.document.file_id, caption=message.caption)
            elif message.voice:
                await context.bot.send_voice(uid, message.voice.file_id, caption=message.caption)
                
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await update.message.reply_text(get_text(lang, "broadcast_sent", count=count))

    del BROADCAST_MODE[user_id]

async def back_to_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_admin_panel(update, context)

# --- أوامر السماح والإزالة ---

async def allow_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = context.user_data.get("lang", "ar")

    if not user_is_admin(user_id):
        await update.message.reply_text(get_text(lang, "no_permission"))
        return

    if not context.args:
        await update.message.reply_text(get_text(lang, "provide_user_id"))
        return

    try:
        new_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(get_text(lang, "invalid_user_id"))
        return

    if new_user_id in ALLOWED_USERS:
        await update.message.reply_text(get_text(lang, "user_already_allowed"))
        await allowed_welcome_message(new_user_id, lang, context)
        return

    ALLOWED_USERS.add(new_user_id)
    if new_user_id in DISALLOWED_USERS:
        DISALLOWED_USERS.remove(new_user_id)
    
    # تحديث الإحصائيات
    BOT_STATS["allowed_users_count"] = len(ALLOWED_USERS)
    BOT_STATS["disallowed_users_count"] = len(DISALLOWED_USERS)
    
    save_json_set(ALLOWED_USERS_FILE, ALLOWED_USERS)
    save_json_set(DISALLOWED_USERS_FILE, DISALLOWED_USERS)
    save_json_dict(BOT_STATS_FILE, BOT_STATS)
    
    await update.message.reply_text(get_text(lang, "user_allowed_success", user_id=new_user_id))
    try:
        await allowed_welcome_message(new_user_id, lang, context)
    except Exception:
        pass

async def disallow_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = context.user_data.get("lang", "ar")

    if not user_is_admin(user_id):
        await update.message.reply_text(get_text(lang, "no_permission"))
        return

    if not context.args:
        await update.message.reply_text(get_text(lang, "provide_user_id").replace("/allow", "/disallow"))
        return

    try:
        rem_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(get_text(lang, "invalid_user_id"))
        return

    if rem_user_id not in ALLOWED_USERS:
        await update.message.reply_text(get_text(lang, "user_not_allowed"))
        return

    ALLOWED_USERS.remove(rem_user_id)
    DISALLOWED_USERS.add(rem_user_id)
    
    # تحديث الإحصائيات
    BOT_STATS["allowed_users_count"] = len(ALLOWED_USERS)
    BOT_STATS["disallowed_users_count"] = len(DISALLOWED_USERS)
    
    save_json_set(ALLOWED_USERS_FILE, ALLOWED_USERS)
    save_json_set(DISALLOWED_USERS_FILE, DISALLOWED_USERS)
    save_json_dict(BOT_STATS_FILE, BOT_STATS)
    
    await update.message.reply_text(get_text(lang, "user_disallowed_success", user_id=rem_user_id))
    try:
        await disallow_message(rem_user_id, lang, context)
    except Exception:
        pass

# --- الدوال الأساسية الأصلية (start, set_language, check_subscription_button, pair_selected, duration_selected, ...) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.application.bot_data.setdefault("interacted_users", set()).add(user_id)

    # التحقق من الاشتراك أولاً
    is_subscribed = await check_subscription(update, context)
    if not is_subscribed:
        lang = context.user_data.get("lang", "ar")
        img_url = "https://i.postimg.cc/4xb6CgHs/dd9dacf7b4541a45d814672304f87d0c.jpg"
        text = get_text(lang, "subscription_required")
        
        await update.message.reply_photo(
            photo=img_url,
            caption=text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("اشترك في القناة", url="https://t.me/h_h7_7_0HAYAFx967")],
                    [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_subscription")],
                ]
            ),
        )
        return

    # بعد الاشتراك، التحقق من الصلاحية
    if not user_allowed(user_id):
        await deny_access(update, context)
        return

    lang = context.user_data.get("lang", "ar")
    text = get_text(lang, "welcome")

    await update.message.reply_photo(
        photo="https://i.postimg.cc/pX64xQ8k/20250717-181806.jpg",
        caption=text,
        reply_markup=language_keyboard(),
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.application.bot_data.setdefault("interacted_users", set()).add(user_id)

    if not user_allowed(user_id):
        context.user_data["lang"] = "ar"
        await deny_access(update, context)
        return

    q = update.callback_query
    await q.answer()
    lang = "ar" if q.data == "lang_ar" else "en"
    context.user_data["lang"] = lang
    try:
        await q.message.delete()
    except Exception:
        pass
    
    text = get_text(lang, "check_subscription")
    
    await q.message.chat.send_message(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("اشترك في القناة" if lang == "ar" else "Subscribe to channel", url="https://t.me/h_h7_7_0HAYAFx967")],
                [InlineKeyboardButton("✅ تحقق من الاشتراك" if lang == "ar" else "✅ Check subscription", callback_data="check_subscription")],
            ]
        ),
    )

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        ]
    except Exception:
        return False

async def check_subscription_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = context.user_data.get("lang", "ar")

    q = update.callback_query
    await q.answer()

    is_subscribed = await check_subscription(update, context)
    try:
        await q.message.delete()
    except Exception:
        pass

    if is_subscribed:
        # بعد الاشتراك، التحقق من الصلاحية
        if not user_allowed(user_id):
            await deny_access(update, context)
            return
            
        context.user_data['asked_subscription'] = False
        await q.message.chat.send_message(
            get_text(lang, "subscription_confirmed"),
            reply_markup=pairs_keyboard(lang, user_id),
        )
    else:
        img_url = "https://i.postimg.cc/4xb6CgHs/dd9dacf7b4541a45d814672304f87d0c.jpg"
        text = get_text(lang, "subscription_required")
        
        msg = await q.message.chat.send_photo(
            photo=img_url,
            caption=text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("اشترك في القناة" if lang == "ar" else "Subscribe to channel", url="https://t.me/h_h7_7_0HAYAFx967")]]
            ),
        )
        asyncio.create_task(safe_delete_message(q.message.chat, msg.message_id, delay=60))

async def pair_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not user_allowed(user_id):
        await deny_access(update, context)
        return
    q = update.callback_query
    await q.answer()
    pair = q.data.replace("pair_", "")
    context.user_data["pair"] = pair
    lang = context.user_data.get("lang", "ar")
    try:
        await q.message.delete()
    except Exception:
        pass
    msg = await q.message.chat.send_message(
        f"✅ {get_text(lang, 'select_duration')} {pair}:",
        reply_markup=durations_keyboard(lang),
    )
    context.user_data["last_message_id"] = msg.message_id

async def duration_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = context.user_data.get("lang", "ar")

    if not user_allowed(user_id):
        if update.callback_query:
            await update.callback_query.answer(
                get_text(lang, "denied_access"),
                show_alert=True,
            )
        else:
            await deny_access(update, context)
        return

    q = update.callback_query
    await q.answer()
    now = time.time()
    last_time = context.user_data.get("last_request_time", 0)

    if now - last_time < 20:
        await q.answer(
            get_text(lang, "wait_20_seconds"),
            show_alert=True,
        )
        return
    context.user_data["last_request_time"] = now

    pair = context.user_data.get("pair")
    if not pair:
        await q.message.reply_text(get_text(lang, "no_pair_selected"))
        return
    try:
        await q.message.delete()
    except Exception:
        pass

    msg = await q.message.chat.send_photo(
        photo="https://i.postimg.cc/sXcQZ4RZ/102a975a730ac2f446cefe3fe79a98b4.jpg",
        caption=get_text(lang, "analyzing"),
    )

    for i in range(1, 6):
        bar = "▓" * i + "░" * (5 - i)
        percent = i * 20
        try:
            await msg.edit_caption(caption=get_text(lang, "analyzing_progress", bar=bar, percent=percent))
        except Exception:
            break
        await asyncio.sleep(0.5)

    try:
        await msg.delete()
    except Exception:
        pass

    symbol = PAIR_SYMBOLS.get(pair)
    duration = q.data.replace("duration_", "")
    result, used_key, source = await analyze_market(symbol, duration)

    if not result:
        await q.message.chat.send_message(get_text(lang, "no_data"))
        return

    # تحديث الإحصائيات
    BOT_STATS["total_analyses"] = BOT_STATS.get("total_analyses", 0) + 1
    
    # تحديث المستخدمين الفريدين - إصلاح الخطأ هنا
    unique_users_set = BOT_STATS.get("unique_users_set", [])
    if isinstance(unique_users_set, list):
        unique_users_set = set(unique_users_set)
    unique_users_set.add(user_id)
    BOT_STATS["unique_users"] = len(unique_users_set)
    BOT_STATS["unique_users_set"] = list(unique_users_set)  # حفظ كقائمة لأن JSON لا يدعم set

    direction = result["direction"]
    if "صعود" in direction or "Up" in direction:
        BOT_STATS["up_signals"] = BOT_STATS.get("up_signals", 0) + 1
    else:
        BOT_STATS["down_signals"] = BOT_STATS.get("down_signals", 0) + 1

    # حفظ التاريخ في البيانات المحفوظة
    user_id_str = str(user_id)
    user_history = USER_HISTORIES.get(user_id_str, [])
    user_history.append(
        {
            "pair": pair,
            "duration": duration,
            "direction": direction,
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    if len(user_history) > 10:
        user_history.pop(0)
    USER_HISTORIES[user_id_str] = user_history

    # حفظ جميع البيانات
    save_json_dict(BOT_STATS_FILE, BOT_STATS)
    save_json_dict(USER_HISTORIES_FILE, USER_HISTORIES)

    photo = (
        "https://i.postimg.cc/7Y0VPXQh/8ba5bc596b193be49d8e373c92c0f223.jpg"
        if direction == "⤴️ صعود 🟢" or direction == "⤴️ Up 🟢"
        else "https://i.postimg.cc/VvHFSVP0/4716f8a143c4fd7ff93c76a74a085649.jpg"
    )

    text = get_text(lang, "signal_info",
                   pair=pair,
                   duration=duration,
                   rsi=result['rsi'],
                   macd=result['macd'],
                   signal=result['signal'],
                   sma=result['sma'],
                   ema=result['ema'],
                   bb_lower=result['bb_lower'],
                   bb_upper=result['bb_upper'],
                   stoch_k=result['stoch_k'],
                   stoch_d=result['stoch_d'],
                   adx=result['adx'],
                   cci=result['cci'],
                   willr=result['willr'],
                   obv=result['obv'],
                   atr=result['atr'],
                   volume=result['volume'],
                   direction=result['direction'],
                   confidence=result['confidence'],
                   source=source,
                   used_key=used_key[:4] + "****")

    await q.message.chat.send_photo(
        photo=photo,
        caption=text,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(get_text(lang, "retry_analysis"), callback_data=f"duration_{duration}")],
                [InlineKeyboardButton(get_text(lang, "select_other_pair"), callback_data="back_to_pairs")],
            ]
        ),
    )

# ----------------- دوال تحليل السوق والمؤشرات -------------------

async def get_news_sentiment(symbol: str) -> float:
    base_currency = symbol.split("_")[0]
    url = (
        f"https://newsapi.org/v2/everything?q={base_currency}&apiKey={NEWS_API_KEY}"
        f"&language=en&sortBy=publishedAt&pageSize=5"
    )
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as resp:
                data = await resp.json()
            articles = data.get("articles", [])
            positive_words = ["rise", "gain", "increased", "bullish", "up"]
            negative_words = ["fall", "drop", "decline", "bearish", "down"]
            score = 0
            for art in articles:
                title = art.get("title", "").lower()
                for pw in positive_words:
                    if pw in title:
                        score += 1
                for nw in negative_words:
                    if nw in title:
                        score -= 1
            if not articles:
                return 0
            return max(min(score / len(articles), 1), -1)
        except Exception:
            return 0

def extract_indicators(df):
    rsi = round(ta.momentum.RSIIndicator(df["close"]).rsi().iloc[-1], 2)
    macd_obj = ta.trend.MACD(df["close"])
    macd = round(macd_obj.macd().iloc[-1], 4)
    signal = round(macd_obj.macd_signal().iloc[-1], 4)
    sma = round(df["close"].rolling(window=20).mean().iloc[-1], 4)
    ema = round(ta.trend.EMAIndicator(df["close"], window=20).ema_indicator().iloc[-1], 4)
    std_dev = df["close"].rolling(window=20).std().iloc[-1]
    bb_upper = round(sma + 2 * std_dev, 4)
    bb_lower = round(sma - 2 * std_dev, 4)
    last_price = df["close"].iloc[-1]

    stoch = ta.momentum.StochasticOscillator(df["high"], df["low"], df["close"], window=14, smooth_window=3)
    stoch_k = round(stoch.stoch().iloc[-1], 2)
    stoch_d = round(stoch.stoch_signal().iloc[-1], 2)

    adx = round(ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14).adx().iloc[-1], 2)
    cci = round(ta.trend.CCIIndicator(df["high"], df["low"], df["close"], window=20).cci().iloc[-1], 2)
    volume = round(df.get("volume", pd.Series([0] * len(df))).iloc[-1], 2)

    willr = round(ta.momentum.WilliamsRIndicator(df["high"], df["low"], df["close"], lbp=14).williams_r().iloc[-1], 2)
    obv = round(ta.volume.OnBalanceVolumeIndicator(df["close"], df["volume"]).on_balance_volume().iloc[-1], 2)
    atr = round(ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range().iloc[-1], 4)

    return {
        "rsi": rsi,
        "macd": macd,
        "signal": signal,
        "sma": sma,
        "ema": ema,
        "bb_upper": bb_upper,
        "bb_lower": bb_lower,
        "stoch_k": stoch_k,
        "stoch_d": stoch_d,
        "adx": adx,
        "cci": cci,
        "volume": volume,
        "willr": willr,
        "obv": obv,
        "atr": atr,
        "last_price": last_price,
    }

def determine_direction(indicators, news_sentiment=0):
    up, down = 0, 0

    rsi = indicators["rsi"]
    macd = indicators["macd"]
    signal = indicators["signal"]
    sma = indicators["sma"]
    last_price = indicators["last_price"]
    bb_upper = indicators["bb_upper"]
    bb_lower = indicators["bb_lower"]
    stoch_k = indicators["stoch_k"]
    stoch_d = indicators["stoch_d"]
    adx = indicators["adx"]
    cci = indicators["cci"]
    willr = indicators["willr"]
    atr = indicators["atr"]

    if rsi > 50:
        up += 1
    else:
        down += 1

    if macd > signal:
        up += 1
    else:
        down += 1

    if last_price > sma:
        up += 1
    else:
        down += 1

    if last_price < bb_lower:
        up += 1
    elif last_price > bb_upper:
        down += 1

    if stoch_k > stoch_d and stoch_k < 80:
        up += 1
    elif stoch_k < stoch_d and stoch_k > 20:
        down += 1

    if adx > 25:
        up += 1
    else:
        down += 1

    if cci > 100:
        up += 1
    elif cci < -100:
        down += 1

    if willr < -50:
        up += 1
    else:
        down += 1

    confidence_base = 80 + abs(up - down) * 3
    if atr > 0.01 * last_price:
        confidence_base -= 5

    if news_sentiment > 0.1:
        up += 1
        confidence_base += 3
    elif news_sentiment < -0.1:
        down += 1
        confidence_base += 3

    direction = "⤴️ صعود 🟢" if up > down else "⤵️ هبوط 🔴"
    confidence = min(max(confidence_base, 50), 99)
    return direction, confidence

async def analyze_market(symbol, duration):
    interval_map = {
        "5 ثواني": "5s",
        "10 ثواني": "10s",
        "15 ثانية": "15s",
        "30 ثانية": "30s",
        "1 دقيقة": "1min",
        "2 دقائق": "2min",
        "3 دقائق": "3min",
        "4 دقائق": "4min",
        "5 دقائق": "5min",
        "10 دقائق": "10min",
        "15 دقيقة": "15min",
        "20 دقيقة": "20min",
        "30 دقيقة": "30min",
        "40 دقيقة": "40min",
        "50 دقيقة": "50min",
        "1 ساعة": "60min",
    }
    interval = interval_map.get(duration, "1min")

    async with aiohttp.ClientSession() as session:
        for key in API_KEYS_TWELVE:
            try:
                from_symbol, to_symbol = symbol.split("_")
                url = f"https://api.twelvedata.com/time_series?symbol={from_symbol}/{to_symbol}&interval={interval}&apikey={key}&outputsize=50"
                async with session.get(url, timeout=10) as resp:
                    r = await resp.json()
                if "values" not in r:
                    continue
                df = pd.DataFrame(r["values"]).iloc[::-1]
                for col in ["close", "high", "low", "volume"]:
                    if col not in df.columns:
                        df[col] = df["close"] if col != "volume" else 0
                    df[col] = df[col].astype(float)
                indicators = extract_indicators(df)
                news_sentiment = await get_news_sentiment(symbol)
                direction, confidence = determine_direction(indicators, news_sentiment)
                indicators.update({"direction": direction, "confidence": confidence})
                return indicators, key, "TwelveData"
            except Exception:
                continue

        for key in API_KEYS_ALPHA:
            try:
                symbol_alpha = symbol.replace("_", "")
                url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol_alpha}&interval=1min&apikey={key}&outputsize=compact"
                async with session.get(url, timeout=10) as resp:
                    r = await resp.json()
                data = r.get("Time Series (1min)")
                if not data:
                    continue
                df = pd.DataFrame.from_dict(data, orient="index").sort_index()
                df = df.astype(float)  # تم إصلاح الخطأ هنا
                df.rename(columns={"4. close": "close", "2. high": "high", "3. low": "low", "5. volume": "volume"}, inplace=True)
                indicators = extract_indicators(df)
                news_sentiment = await get_news_sentiment(symbol)
                direction, confidence = determine_direction(indicators, news_sentiment)
                indicators.update({"direction": direction, "confidence": confidence})
                return indicators, key, "Alpha Vantage"
            except Exception:
                continue

    return None, None, None

# --- دوال الدعم الإضافية ---

async def safe_delete_message(chat, message_id, delay=10):
    await asyncio.sleep(delay)
    try:
        await chat.delete_message(message_id)
    except Exception:
        pass

async def back_to_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not user_allowed(user_id):
        await deny_access(update, context)
        return
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "ar")
    try:
        await q.message.delete()
    except Exception:
        pass
    await q.message.chat.send_message(
        get_text(lang, "select_pair"),
        reply_markup=pairs_keyboard(lang, user_id),
    )

async def back_to_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not user_allowed(user_id):
        await deny_access(update, context)
        return
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except Exception:
        pass
    await q.message.chat.send_message("اختر اللغة / Choose Language:", reply_markup=language_keyboard())

async def how_it_works(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not user_allowed(user_id):
        await deny_access(update, context)
        return
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "ar")
    try:
        await q.message.delete()
    except Exception:
        pass
    img_url = "https://i.postimg.cc/9XnGC1dV/IMG-20250716-120320-113.jpg"
    text = get_text(lang, "how_bot_works")
    
    await q.message.chat.send_photo(
        photo=img_url,
        caption=text,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(get_text(lang, "back"), callback_data="back_to_pairs")]]
        ),
    )


# --- جدولة التذكيرات ---

async def on_startup(app):
    job_queue = app.job_queue
    # إصلاح مشكلة الجدولة
    try:
        job_queue.run_daily(send_registration_reminder, time=datetime.time(hour=12, minute=0, second=0))
        job_queue.run_daily(send_evening_followup, time=datetime.time(hour=19, minute=0, second=0))
    except Exception:
        pass

# --- دالة التشغيل الرئيسية ---

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_language, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(check_subscription_button, pattern="^check_subscription$"))
    app.add_handler(CallbackQueryHandler(pair_selected, pattern="^pair_"))
    app.add_handler(CallbackQueryHandler(duration_selected, pattern="^duration_"))
    app.add_handler(CallbackQueryHandler(back_to_pairs, pattern="^back_to_pairs$"))
    app.add_handler(CallbackQueryHandler(back_to_language, pattern="^back_to_language$"))
    app.add_handler(CallbackQueryHandler(how_it_works, pattern="^how_it_works$"))
    app.add_handler(CallbackQueryHandler(show_dashboard, pattern="^show_dashboard$"))
    app.add_handler(CallbackQueryHandler(show_admin_panel, pattern="^admin_panel$"))
    app.add_handler(CallbackQueryHandler(start_broadcast_mode, pattern="^broadcast_"))
    app.add_handler(CallbackQueryHandler(back_to_admin_panel, pattern="^back_to_admin$"))
    app.add_handler(CallbackQueryHandler(show_user_stats, pattern="^user_stats$"))
    app.add_handler(CommandHandler("allow", allow_user))
    app.add_handler(CommandHandler("disallow", disallow_user))
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), receive_broadcast_message))

    # إصلاح مشكلة الجدولة
    try:
        app.job_queue.run_once(lambda ctx: on_startup(app), when=5)
    except Exception:
        pass

    print("✅ البوت يعمل الآن مع التحديثات الجديدة والمتكاملة...")
    app.run_polling()

if __name__ == "__main__":
    main()
