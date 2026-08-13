import telebot
import db
import ai_translator
import scheduler_jobs
from config import BOT_TOKEN, ADMIN_ID, TARGET_CHANNEL_ID
from scheduler_jobs import setup_scheduler, scheduler, check_and_post_instantly

db.init_db()

bot = telebot.TeleBot(BOT_TOKEN)

def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID)

def get_main_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton("📊 Holat"),
        telebot.types.KeyboardButton("⚡️ Yangiliklarni tekshirish"),
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
        "📊 **Holat** - Bot va baza haqida barcha ma'lumotlar\n"
        "⚡️ **Yangiliklarni tekshirish** - Donor Telegram kanaldan darhol yangi postlarni tekshirish va joylash\n"
        "⚙️ **Donor sozlash** - Donor Telegram kanalini o'zgartirish"
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
        f"⚡️ **Rejim:** Instant Auto-Forward & Translate (Real-vaqt)\n\n"
        f"🎯 **Donor Telegram Kanal:** `{donor}`\n"
        f"👁 **Eslab qolingan postlar (Baza):** {seen_count} ta\n"
        f"🔍 **Oxirgi o'qilgan post:** `{last_id}`\n\n"
        f"✨ **Qo'llab-quvvatlanadigan media:** Matn, Rasm(lar), Video, GIF, Hujjatlar"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda msg: is_admin(msg.from_user.id) and (msg.text == "⚡️ Yangiliklarni tekshirish" or msg.text == "🚀 Yangiliklar yig'ish"))
@bot.message_handler(commands=['force_fetch', 'force_check'])
def cmd_force_check(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "🔍 Donor Telegram kanali tekshirilmoqda va yangi postlar joylanmoqda...")
    check_and_post_instantly(bot, force=True)
    bot.send_message(message.chat.id, "✅ Tekshiruv va auto-post tugadi! Kanalni tekshiring.", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda msg: is_admin(msg.from_user.id) and msg.text == "⚙️ Donor sozlash")
@bot.message_handler(commands=['settings'])
def cmd_settings(message):
    if not is_admin(message.from_user.id):
        return
    donor = db.get_donor_url()
    text = (
        f"Hozirgi Donor Telegram Kanal: {donor}\n\n"
        "Yangi donor kanal havolasini yoki username'ini yuboring:\n"
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
    formatted = db.get_donor_url()
    bot.send_message(message.chat.id, f"✅ Muvaffaqiyatli! Yangi Donor Kanal ulandi: {formatted} \n"
                         f"Endi yangi postlarni tekshirish uchun ⚡️ Yangiliklarni tekshirish ni bosing.", reply_markup=get_main_keyboard())

if __name__ == "__main__":
    from keep_alive import keep_alive
    keep_alive()
    
    setup_scheduler(bot)
    scheduler.start()
    print("Avto-post Taymeri (Scheduler 1-minutlik interval) ishga tushdi!")
    
    print("Bot polling boshlandi...")
    bot.infinity_polling()
