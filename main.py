import telebot
import db
import ai_moderator
from config import BOT_TOKEN, ADMIN_ID
from scheduler_jobs import setup_scheduler, scheduler, fetch_and_queue_posts, process_queue_and_post

db.init_db()

bot = telebot.TeleBot(BOT_TOKEN)

def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID)

@bot.message_handler(commands=['start'])
def cmd_start(message):
    if not is_admin(message.from_user.id):
        text = f"🔒 Siz admin emassiz.\n\nSizning Telegram ID raqamingiz: `{message.from_user.id}`\n\nIltimos, ushbu ID ni `.env` faylidagi `ADMIN_ID` qatoriga yozing va botni qayta ishga tushiring."
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
        return
        
    text = (
        "👋 Assalomu alaykum, Admin!\n\n"
        "Bu bot o'zbek tiliga xorijiy kanallardan postlarni 'o'g'irlab', "
        "Gemini AI yordamida 'virusli' formatda kanalingizga joylab beradi.\n\n"
        "🛠 /settings - Donor kanalni o'zgartirish\n"
        "📊 /status - Hozirgi holatni ko'rish\n"
        "🚀 /force_fetch - Hozirning o'zida postlarni yig'ish\n"
        "📨 /force_post - Hozirning o'zida bitta post chiqarib ko'rish"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['status'])
def cmd_status(message):
    if not is_admin(message.from_user.id):
        return
    donor = db.get_donor_url()
    q_count = db.get_queued_count()
    last_id = db.get_last_id()
    
    text = (
        "📈 **Bot Holati:**\n\n"
        f"🎯 RSS Manba (Sayt): {donor}\n"
        f"📦 Navbatdagi postlar soni: {q_count} ta\n"
        f"🔍 Oxirgi o'qilgan xabar URL: {last_id}"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['force_fetch'])
def cmd_force_fetch(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "Sikraping ishga tushirildi... Kutib turing.")
    fetch_and_queue_posts()
    bot.send_message(message.chat.id, f"Skraping tugadi! Navbatda {db.get_queued_count()} ta post yig'ildi.")

@bot.message_handler(commands=['force_post'])
def cmd_force_post(message):
    if not is_admin(message.from_user.id):
        return
    if db.get_queued_count() == 0:
        bot.send_message(message.chat.id, "Bazada post yo'q. Oldin /force_fetch qilib postlarni yig'ing.")
        return
    
    bot.send_message(message.chat.id, "Tarjima qilinmoqda va kanalga jo'natilmoqda...")
    process_queue_and_post(bot)
    bot.send_message(message.chat.id, "Urinish tugadi. Kanalni tekshiring.")

@bot.message_handler(commands=['settings'])
def cmd_settings(message):
    if not is_admin(message.from_user.id):
        return
    donor = db.get_donor_url()
    text = (
        f"Hozirgi RSS Manba (Sayt): {donor}\n\n"
        "Yangi RSS manbalarini to'liq havolasi (URL) bilan jo'nating:\n"
        "Misollar:\n"
        "- https://lifehacker.com/rss\n"
        "- https://www.reddit.com/r/BeAmazed/.rss\n"
        "(Bekor qilish uchun /cancel)"
    )
    msg = bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(msg, process_new_donor)

@bot.message_handler(commands=['cancel'])
def cmd_cancel(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "Bekor qilindi.")
    bot.clear_step_handler_by_chat_id(message.chat.id)

def process_new_donor(message):
    if not is_admin(message.from_user.id):
        return
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Sozlamalarni o'zgartirish bekor qilindi.")
        return
        
    new_url = message.text.strip()
    db.set_donor_url(new_url)
    bot.send_message(message.chat.id, f"✅ Muvaffaqiyatli! Yangi RSS Manba ulandi: {new_url} \n"
                         f"Endi yangi ma'lumotlarni yig'ib olish uchun /force_fetch ni bosing.")

@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'], content_types=['text'])
def handle_group_messages(message):
    text = message.text.lower()
    
    # Agar foydalanuvchi to'ppa-to'g'ri bot_username so'rasa yoki botga reply qilsa
    try:
        bot_info = bot.get_me()
        is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot_info.id
        mentioned_admin = ("admin" in text) or ("adminka" in text) or (f"@{bot_info.username}".lower() in text)
        
        if is_reply_to_bot or mentioned_admin:
            bot.send_chat_action(message.chat.id, 'typing')
            
            # Gemini-Ali funksiyasi ishga tushadi
            reply_text = ai_moderator.generate_admin_reply(message.text, message.from_user.first_name)
            
            if not reply_text:
                return
                
            if reply_text == "[FORWARD]":
                # Adminga jo'natish (ADMIN_ID db da o'rnatilmagan env da bor)
                try:
                    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
                    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
                    bot.send_message(ADMIN_ID, f"🚨 **Izohlardan murojaat / Reklama so'rovi:**\nKimdan: {username}")
                except Exception as ex:
                    print(f"Rahbarga xabarni forward qilishda xato: {ex}")
                
                bot.reply_to(message, "Bu murojaatingiz muhim, shuning uchun shaxsan kanal rahbariga (bosh adminga) yetkazdim. Sizga tez orada aloqaga chiqishadi! 🤝")
            else:
                bot.reply_to(message, reply_text)
                
    except Exception as e:
        print(f"Guruh xabarlarida xato: {e}")

if __name__ == "__main__":
    from keep_alive import keep_alive
    keep_alive()
    
    setup_scheduler(bot)
    scheduler.start()
    print("Taymer (Scheduler) ishga tushdi!")
    
    print("Bot polling boshlandi...")
    bot.infinity_polling()
