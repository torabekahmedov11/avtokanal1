from apscheduler.schedulers.background import BackgroundScheduler
import telebot
import db
import scraper
import ai_translator
from telegraph_api import create_telegraph_page
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TARGET_CHANNEL_ID, CHANNEL_LINK, ADMIN_ID
from datetime import datetime
import pytz

scheduler = BackgroundScheduler(timezone='Asia/Tashkent')

def get_tashkent_now():
    """O'zbekiston (Toshkent) vaqti bilan hozirgi vaqtni qaytaradi."""
    tz = pytz.timezone('Asia/Tashkent')
    return datetime.now(tz)

def is_nighttime():
    """Toshkent vaqti bo'yicha 23:00 va 07:00 oralig'i (Tungi sukunat)."""
    now = get_tashkent_now()
    return now.hour >= 23 or now.hour < 7

def fetch_and_queue_posts(bot=None, force=False):
    """
    Saytdan yangiliklarni tekshiradi.
    - Kunduzi (07:00 - 23:00): Yangi post topilsa, DARHOL kanalga joylaydi!
    - Tunda (23:00 - 07:00): Yangi postlarni yig'adi va ertalab uchun navbatda saqlaydi.
    - force=True (Admin bosganda): Majburiy ravishda post yig'adi.
    """
    donor = db.get_donor_url()
    last_id = db.get_last_id()
    
    print(f"[{get_tashkent_now().strftime('%Y-%m-%d %H:%M:%S')}] Skraping kuting... ({donor})")
    try:
        all_posts = scraper.scrape_telegram_channel(donor, last_id)
    except Exception as e:
        print(f"Skraping xatosi: {e}")
        if bot:
            try:
                bot.send_message(ADMIN_ID, f"⚠️ **Skraping (Xabar o'g'irlash) bo'limida XATOLIK:**\n\n`{str(e)}`", parse_mode="Markdown")
            except: pass
        return
    
    if not all_posts:
        return
        
    # 1. Ko'rilmagan yangi postlarni topish
    new_posts = []
    for post in all_posts:
        pid = post.get("id")
        if not pid or db.is_post_seen(pid):
            continue

        db.mark_as_seen(pid)
        db.set_last_id(pid)

        if post.get("text"):
            new_posts.append(post)
            print(f"Yangi post topildi: {pid}")

    # 2. Force fetch bo'lsa
    if force:
        posts_to_add = new_posts if new_posts else (all_posts[-3:] if len(all_posts) >= 3 else all_posts)
        for p in posts_to_add:
            db.add_queued_post(p)
            db.mark_as_seen(p["id"])
            db.set_last_id(p["id"])
        print(f"Force fetch: {len(posts_to_add)} ta post navbatga majburan joylandi.")
        return

    if not new_posts:
        return

    # 3. Tunda bo'lsa navbatga saqlaymiz, kunduzi bo'lsa navbatga joylab DARHOL bittasini chiqarishga beramiz
    for p in new_posts:
        db.add_queued_post(p)

    if is_nighttime():
        print(f"Tungi rejim (23:00-07:00): {len(new_posts)} ta yangi post ertalabki nashr uchun navbatga olindi.")
    else:
        print(f"Kunduzgi rejim: {len(new_posts)} ta yangi post topildi! DARHOL kanalga chiqarilmoqda...")
        if bot:
            process_queue_and_post(bot)

def parse_telegraph_response(text):
    xabar = text
    batafsil = ""
    
    if "[XABAR]" in text and "[BATAFSIL]" in text:
        parts = text.split("[BATAFSIL]")
        xabar = parts[0].replace("[XABAR]", "").strip()
        batafsil = parts[1].strip()
    elif "[BATAFSIL]" in text:
        parts = text.split("[BATAFSIL]")
        xabar = parts[0].strip()
        batafsil = parts[1].strip()
        
    return xabar, batafsil

def get_post_markup(telegraph_url=None):
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    if telegraph_url:
        buttons.append(InlineKeyboardButton("👉 Batafsil o'qish", url=telegraph_url))
    if CHANNEL_LINK:
        ch_link = CHANNEL_LINK if CHANNEL_LINK.startswith("http") else f"https://t.me/{CHANNEL_LINK.replace('@', '')}"
        buttons.append(InlineKeyboardButton("➕ Obuna bo'lish", url=ch_link))
    if buttons:
        markup.add(*buttons)
        return markup
    return None

def send_morning_greeting(bot: telebot.TeleBot):
    """Ertalabki yoki navbat bo'shaganda chiqariladigan sun'iy AI Layfxak po'sti."""
    print(f"[{datetime.now()}] MAXSUS AI LAYFXAK POST YARATILMOQDA...")
    text = ai_translator.generate_morning_lifehack()
    if not text:
        return
        
    main_post, batafsil_post = parse_telegraph_response(text)
    
    slogan = f"\n\n🚀 Obuna bo'lish esdan chiqmasin: bizda har kuni qaynoq layfxaklar va yangiliklar!\n👉 Kanalimiz: {CHANNEL_LINK}"
    main_post += slogan

    telegraph_url = None
    if batafsil_post:
        telegraph_url = create_telegraph_page(title="Foydali Layfxak", html_content=batafsil_post)
        
    markup = get_post_markup(telegraph_url)
            
    try:
        send_post_to_channel(bot, TARGET_CHANNEL_ID, main_post, markup=markup)
        print("✅ Special AI Layfxak post kanalga ketdi!")
    except Exception as e:
        print(f"Layfxak post jo'natish xatosi: {e}")

def send_post_to_channel(bot: telebot.TeleBot, channel_id, main_post, video_url=None, image_url=None, markup=None):
    """
    Postni Telegram kanalga xavfsiz yuboradi.
    Video/Rasm URL telegram tomonidan rad etilsa (400 Bad Request: wrong type of web page content)
    yoki HTML formatlashda xato bo'lsa, avtomatik ravishda navbatdagi xavfsiz variantga fallback qiladi.
    """
    if video_url:
        try:
            return bot.send_video(channel_id, video_url, caption=main_post, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            print(f"Video jo'natish feyl bo'ldi ({e}), foto/matnga o'tilmoqda...")

    if image_url:
        try:
            return bot.send_photo(channel_id, image_url, caption=main_post, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            print(f"Rasm jo'natish feyl bo'ldi ({e}), oddiy matnga o'tilmoqda...")

    try:
        return bot.send_message(channel_id, main_post, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        print(f"HTML parse mode xatosi ({e}), oddiy tekis matnda jo'natilmoqda...")
        clean_text = main_post.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
        return bot.send_message(channel_id, clean_text, reply_markup=markup)

def process_queue_and_post(bot: telebot.TeleBot):
    """
    Navbatdagi postni kanalga joylaydi.
    1. Tunda bo'lsa (23:00 - 07:00): Sukunat saqlanadi.
    2. Navbatda post bo'lsa: Uni chiqaradi.
    3. Navbatda post ham bo'lmasa: AI Livehack yaratib joylaydi.
    """
    if not TARGET_CHANNEL_ID:
        return

    if is_nighttime():
        print("Tungi rejim (23:00 - 07:00): Avto-nashr to'xtatilgan.")
        return

    post = db.get_next_post()
    if not post:
        print("Navbat bo'sh: AI Livehack generatsiya qilib kanalga chiqarilmoqda...")
        send_morning_greeting(bot)
        return
        
    print(f"Postga ishlov berilmoqda ({post['id']})...")
    translated_text = ai_translator.translate_and_spice_up(post['text'])
    
    if not translated_text:
        print("API yoki tarjimon xatoligi yuz berdi. Post qayta navbatga qo'shilmoqda...")
        post['retries'] = post.get('retries', 0) + 1
        if post['retries'] <= 3:
            db.requeue_post(post)
        else:
            print(f"Post 3 marta urinishdan so'ng ham o'tmadi. Bekor qilindi: {post['id']}")
        return

    # Senzura testi
    if "[FILTERED]" in translated_text:
        print(f"Post SENZURAdan o'tmadi! Bloklandi.")
        return

    translated_text = translated_text.replace('**', '').replace('*', '')
    main_post, batafsil_post = parse_telegraph_response(translated_text)

    # Shior va kanal manzilini post oxiriga biriktirish
    slogan = f"\n\n🚀 Obuna bo'lish esdan chiqmasin: bizda har kuni qaynoq layfxaklar va yangiliklar!\n👉 Kanalimiz: {CHANNEL_LINK}"
    main_post += slogan

    try:
        video_url = post.get('video')
        image_url = post.get('image')
        
        telegraph_url = None
        if batafsil_post:
            telegraph_url = create_telegraph_page(title=post.get('title', 'Batafsil Qo\'llanma'), html_content=batafsil_post)
            
        markup = get_post_markup(telegraph_url)
        
        send_post_to_channel(bot, TARGET_CHANNEL_ID, main_post, video_url=video_url, image_url=image_url, markup=markup)
            
        print(f"✅ Kanalga POST yuborildi! (Qoldi: {db.get_queued_count()})")
    except Exception as e:
        print(f"Jo'natishda xato: {e}")
        try:
            bot.send_message(ADMIN_ID, f"⚠️ **DIQQAT! Post kanalga jo'natishda xatolik yuz berdi:**\n\n`{str(e)}`", parse_mode="Markdown")
        except:
            pass
            
        post['retries'] = post.get('retries', 0) + 1
        if post['retries'] <= 3:
            db.requeue_post(post)
        else:
            print(f"Kanalga yuborish 3 marta feyl bo'ldi. Tashlab yuborildi: {post['id']}")

def setup_scheduler(bot: telebot.TeleBot):
    # 1. Saytdan har 10 minutda yangilikni tekshirib turadi (Kunduzi darhol joylaydi, tunda yig'adi)
    scheduler.add_job(
        fetch_and_queue_posts,
        trigger="interval",
        minutes=10,
        kwargs={"bot": bot}
    )
    
    # 2. 07:00 da uyg'onganda tunda yig'ilgan postlarni yoki xayrli tong AI posti joylaydi
    scheduler.add_job(process_queue_and_post, trigger="cron", hour=7, minute=0, kwargs={"bot": bot})
    
    # 3. Kunduzi 60 - 90 minut oralig'ida avtomatik navbatdan post (yoki Livehack) chiqarish jadvali
    # Soat 08:15, 09:30, 10:45, 12:00, 13:15, 14:30, 15:45, 17:00, 18:15, 19:30, 20:45, 22:00
    post_times = [
        (8, 15), (9, 30), (10, 45), (12, 0), 
        (13, 15), (14, 30), (15, 45), (17, 0), 
        (18, 15), (19, 30), (20, 45), (22, 0)
    ]
    for h, m in post_times:
        scheduler.add_job(process_queue_and_post, trigger="cron", hour=h, minute=m, kwargs={"bot": bot})
        
    fetch_and_queue_posts(bot)
