from apscheduler.schedulers.background import BackgroundScheduler
import telebot
import db
import scraper
import ai_translator
from telegraph_api import create_telegraph_page
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TARGET_CHANNEL_ID, CHANNEL_LINK, ADMIN_ID
from datetime import datetime

scheduler = BackgroundScheduler(timezone='Asia/Tashkent')

def fetch_and_queue_posts(bot=None, force=False):
    """
    Saytdan yangi postlarni topadi va navbatga qo'shadi.
    force=True bo'lganda yoki navbat bo'm-bo'sh bo'lsa, avtomatik ravishda eng yangi postlarni navbatga joylaydi.
    """
    donor = db.get_donor_url()
    last_id = db.get_last_id()
    
    print(f"[{datetime.now()}] Skraping kuting... ({donor})")
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
        
    # 1. Yangi ko'rilmagan postlarni topish
    new_count = 0
    for post in all_posts:
        pid = post.get("id")
        if not pid or db.is_post_seen(pid):
            continue

        db.mark_as_seen(pid)
        db.set_last_id(pid)

        if post.get("text"):
            db.add_queued_post(post)
            new_count += 1
            print(f"Yangi post navbatga tushdi: {pid}")

    # 2. Agar navbat hali ham BO'SH bo'lsa (yoki /force_fetch bosilgan bo'lsa):
    # Eng so'nggi 3 ta postni majburiy navbatga qo'shamiz (bot 'Bazada post yo'q' deb to'xtab qolmasligi uchun)
    if (force or db.get_queued_count() == 0) and all_posts:
        print("Navbat bo'sh bo'lgani uchun eng so'nggi postlar navbatga kiritilmoqda...")
        latest_posts = all_posts[-3:] if len(all_posts) >= 3 else all_posts
        for post in latest_posts:
            if post.get("text"):
                db.add_queued_post(post)
                db.mark_as_seen(post["id"])
                db.set_last_id(post["id"])
                new_count += 1
                print(f"Navbatga majburiy post qo'shildi: {post['id']}")

    if new_count > 0:
        print(f"Jami {new_count} ta post navbatga joylandi (Navbatda jami: {db.get_queued_count()} ta).")

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
    """Ertalab soat 07:00 da uyg'onib salomlashish layfxaki tashlaydi."""
    print(f"[{datetime.now()}] TONGGI MAXSUS POST YARATILMOQDA...")
    text = ai_translator.generate_morning_lifehack()
    if not text:
        return
        
    main_post, batafsil_post = parse_telegraph_response(text)
    
    telegraph_url = None
    if batafsil_post:
        telegraph_url = create_telegraph_page(title="Xayrli tong!", html_content=batafsil_post)
        
    markup = get_post_markup(telegraph_url)
            
    try:
        send_post_to_channel(bot, TARGET_CHANNEL_ID, main_post, markup=markup)
        print("✅ Tonggi salomlashuv post kanalga ketdi!")
    except Exception as e:
        print(f"Tonggi post jo'natish xatosi: {e}")

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
    Navbatda turgan eng birinchi postni olib, filtrdan o'tkazadi va chiqaradi.
    """
    if not TARGET_CHANNEL_ID:
        return

    post = db.get_next_post()
    if not post:
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

    # Agar AI baribir yulduzchalardan foydalangan bo'lsa, xato bermasligi uchun qolgan * ni olib tashlash ham mumkin:
    translated_text = translated_text.replace('**', '').replace('*', '')

    main_post, batafsil_post = parse_telegraph_response(translated_text)

    try:
        video_url = post.get('video')
        image_url = post.get('image')
        
        # Telegraph linkni va Inline tugmalarni tayyorlash
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
    # Saytdan 10 minutda yangilikni bazaga yig'ib turadi (24/7 ishlaydi)
    scheduler.add_job(
        fetch_and_queue_posts,
        trigger="interval",
        minutes=10,
        kwargs={"bot": bot}
    )
    
    # 07:00 dagi xayrli tong AI posti
    scheduler.add_job(send_morning_greeting, trigger="cron", hour=7, minute=0, kwargs={"bot": bot})
    
    # Odamlar passiv vaqtida, eng ko'p o'qiladigan Prime-Time vaqtlardagi rejali nashr (15 ta)
    post_times = [
        (8, 15), (9, 30), (11, 0), (12, 30), 
        (13, 15), (14, 0), (15, 30), (17, 0), 
        (18, 0), (19, 0), (20, 0), (20, 45), 
        (21, 30), (22, 15), (23, 15)
    ]
    for h, m in post_times:
        scheduler.add_job(process_queue_and_post, trigger="cron", hour=h, minute=m, kwargs={"bot": bot})
        
    fetch_and_queue_posts(bot)
