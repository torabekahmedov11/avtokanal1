import telebot
import db
import ai_translator
import scheduler_jobs
import vibe_lessons
from config import BOT_TOKEN, ADMIN_ID, TARGET_CHANNEL_ID
from scheduler_jobs import setup_scheduler, scheduler, fetch_and_queue_posts, process_queue_and_post, check_and_post_instantly

db.init_db()

bot = telebot.TeleBot(BOT_TOKEN)

def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID)

def get_main_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton("📊 Holat"),
        telebot.types.KeyboardButton("🚀 Yangiliklar yig'ish"),
        telebot.types.KeyboardButton("📨 Post chiqarish"),
        telebot.types.KeyboardButton("📚 Darslik"),
        telebot.types.KeyboardButton("⚙️ Donor sozlash")
    )
    return markup

@bot.message_handler(commands=['start'])
def cmd_start(message):
    if not is_admin(message.from_user.id):
        text = f"🔒 Siz admin emassiz.\n\nSizning Telegram ID raqamingiz: `{message.from_user.id}`\n\nIltimos, ushbu ID ni `.env` faylidagi `ADMIN_ID` qatoriga yozing va botni qayta ishga tushiring."
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
        return
        
    text = (
        "👋 Assalomu alaykum, Admin!\n\n"
        "Boshqaruv menyusidan foydalanib botni to'liq nazorat qilishingiz mumkin:\n\n"
        "📊 **Holat** - Bot va baza haqida barcha live ma'lumotlar\n"
        "🚀 **Yangiliklar yig'ish** - Hozirning o'zida post yig'ish\n"
        "📨 **Post chiqarish** - Kanalga bitta post chiqarish\n"
        "📚 **Darslik** - Vibe Coding darsini hozir joylash\n"
        "⚙️ **Donor sozlash** - Donor RSS manbasini o'zgartirish"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda msg: is_admin(msg.from_user.id) and msg.text == "📊 Holat")
@bot.message_handler(commands=['status'])
def cmd_status(message):
    if not is_admin(message.from_user.id):
        return
    donor = db.get_donor_url()
    seen_count = db.get_seen_count()
    last_id = db.get_last_id()
    
    tashkent_now_str = scheduler_jobs.get_tashkent_now().strftime("%Y-%m-%d %H:%M:%S")
    
    text = (
        "📊 **BOT NIZOMI VA LIVE HOLATI:**\n\n"
        f"🤖 **Bot holati:** 🟢 FAOL (Online)\n"
        f"🇺🇿 **Toshkent vaqti:** `{tashkent_now_str}`\n"
        f"⚡️ **Rejim:** Instant Auto-Forward (Real-vaqt)\n\n"
        f"🎯 **Donor RSS Telegram Manba:** `{donor}`\n"
        f"👁 **Eslab qolingan postlar (Baza):** {seen_count} ta\n"
        f"🔍 **Oxirgi o'qilgan post:** `{last_id}`\n\n"
        f"📚 **Vibe Coding darsligi:** {db.get_lesson_number()}-dars tugatilgan\n"
        f"⏰ **Keyingi darslik:** Har kuni 20:00 da\n\n"
        f"✨ **Qo'llab-quvvatlanadigan media:** Matn, Rasm(lar), Video, GIF, Hujjatlar"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda msg: is_admin(msg.from_user.id) and msg.text == "🚀 Yangiliklar yig'ish")
@bot.message_handler(commands=['force_fetch'])
def cmd_force_fetch(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "🔍 Donor Telegram manbasidan skraping ishga tushirildi... Kutib turing.")
    check_and_post_instantly(bot, force=True)
    bot.send_message(message.chat.id, f"✅ Skraping tugadi va post kanalga joylandi!", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda msg: is_admin(msg.from_user.id) and msg.text == "📨 Post chiqarish")
@bot.message_handler(commands=['force_post'])
def cmd_force_post(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "⏳ Tarjima qilinmoqda va kanalga jo'natilmoqda...")
    check_and_post_instantly(bot, force=True)
    bot.send_message(message.chat.id, "✅ Jarayon tugadi. Kanalni tekshiring.", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda msg: is_admin(msg.from_user.id) and msg.text == "📚 Darslik")
@bot.message_handler(commands=['lesson'])
def cmd_lesson(message):
    if not is_admin(message.from_user.id):
        return
    current = db.get_lesson_number()
    next_num = current + 1
    lesson_info = vibe_lessons.get_lesson_info(next_num)
    bot.send_message(message.chat.id, 
        f"📚 Hozirgi dars: #{current} tugatilgan\n"
        f"Navbatdagi dars: #{next_num} — {lesson_info['title']}\n\n"
        f"⏳ Dars generatsiya qilinmoqda va kanalga joylanmoqda..."
    )
    success = vibe_lessons.post_daily_lesson(bot)
    if success:
        bot.send_message(message.chat.id, f"✅ {next_num}-Dars kanalga joylandi!", reply_markup=get_main_keyboard())
    else:
        bot.send_message(message.chat.id, "❌ Dars joylanmadi. Loglarni tekshiring.", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda msg: is_admin(msg.from_user.id) and msg.text == "⚙️ Donor sozlash")
@bot.message_handler(commands=['settings'])
def cmd_settings(message):
    if not is_admin(message.from_user.id):
        return
    donor = db.get_donor_url()
    text = (
        f"Hozirgi RSS Donor Manba (Telegram Channel): {donor}\n\n"
        "Yangi RSS manbalarini to'liq havolasi (URL) bilan jo'nating:\n"
        "Misollar:\n"
        "- https://t.me/vibecoding_tg\n"
        "- @vibecoding_tg\n"
        "(Bekor qilish uchun /cancel)"
    )
    msg = bot.send_message(message.chat.id, text, reply_markup=get_main_keyboard())
    bot.register_next_step_handler(msg, process_new_donor)

@bot.message_handler(commands=['cancel'])
def cmd_cancel(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "Bekor qilindi.", reply_markup=get_main_keyboard())
    bot.clear_step_handler_by_chat_id(message.chat.id)

def process_new_donor(message):
    if not is_admin(message.from_user.id):
        return
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Sozlamalarni o'zgartirish bekor qilindi.", reply_markup=get_main_keyboard())
        return
        
    new_url = message.text.strip()
    db.set_donor_url(new_url)
    bot.send_message(message.chat.id, f"✅ Muvaffaqiyatli! Yangi RSS Manba ulandi: {new_url} \n"
                         f"Endi yangi ma'lumotlarni yig'ib olish uchun /force_fetch ni bosing.", reply_markup=get_main_keyboard())

if __name__ == "__main__":
    from keep_alive import keep_alive
    keep_alive()
    
    setup_scheduler(bot)
    scheduler.start()
    print("Taymer (Scheduler) ishga tushdi!")
    
    print("Bot polling boshlandi...")
    bot.infinity_polling()
