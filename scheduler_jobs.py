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

def fetch_and_queue_posts(bot=None):
    """
    Saytdan yangi postlarni topadi va navbatga qo'shadi.
    Eski postlar hech qachon qayta yuborilmaydi (seen_ids tekshiruvi orqali).
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
        
    # Birinchi marta ishga tushganda barcha eski postlarni "ko'rilgan" deb belgilaymiz,
    # faqat eng oxirgi 1 ta postni navbatga olamiz (eski 70 ta post tiqilib qolmasligi uchun)
    if not last_id:
        print("Birinchi skraping: barcha eski postlar bazada ko'rilgan deb belgilandi.")
        all_ids = [p["id"] for p in all_posts]
        db.mark_multiple_as_seen(all_ids)
        latest_post = all_posts[-1]
        if latest_post.get("text"):
            db.add_queued_post(latest_post)
            db.set_last_id(latest_post["id"])
            print(f"Birinchi yangi post navbatga qo'shildi: {latest_post['id']}")
        return

    # Keyingi barcha skrapinglarda: faqat ilgari KO'RILMAGAN yangi postlarni olamiz
    new_count = 0
    for post in all_posts:
        pid = post.get("id")
        if not pid or db.is_post_seen(pid):
            continue

        # Postni darhol ko'rilgan deb belgilaymiz
        db.mark_as_seen(pid)
        db.set_last_id(pid)

        if post.get("text"):
            db.add_queued_post(post)
            new_count += 1
            print(f"Yangi post navbatga tushdi: {pid}")

    if new_count > 0:
        print(f"Jami {new_count} ta yangi post navbatga joylandi.")

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

def send_morning_greeting(bot: telebot.TeleBot):
    """Ertalab soat 07:00 da uyg'onib salomlashish layfxaki tashlaydi."""
    print(f"[{datetime.now()}] TONGGI MAXSUS POST YARATILMOQDA...")
    text = ai_translator.generate_morning_lifehack()
    if not text:
        return
        
    main_post, batafsil_post = parse_telegraph_response(text)
    slogan = f"\n\n🚀 Obuna bo'lish esdan chiqmasin: bizda har kuni qaynoq layfxaklar va yangiliklar!\n👉 Kanalimiz: {CHANNEL_LINK}"
    main_post += slogan
    
    markup = None
    if batafsil_post:
        telegraph_url = create_telegraph_page(title="Xayrli tong!", html_content=batafsil_post)
        if telegraph_url:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("👉 Batafsil o'qish", url=telegraph_url))
            
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

    # Post oxiriga kanal shiori va ssilkasini biriktirish
    slogan = f"\n\n🚀 Obuna bo'lish esdan chiqmasin: bizda har kuni qaynoq layfxaklar va yangiliklar!\n👉 Kanalimiz: {CHANNEL_LINK}"
    main_post += slogan

    try:
        video_url = post.get('video')
        image_url = post.get('image')
        
        # Telegraph linkni tayyorlash
        markup = None
        if batafsil_post:
            telegraph_url = create_telegraph_page(title=post.get('title', 'Batafsil Qo\'llanma'), html_content=batafsil_post)
            if telegraph_url:
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("👉 Batafsil o'qish", url=telegraph_url))
        
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
