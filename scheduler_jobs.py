from apscheduler.schedulers.background import BackgroundScheduler
import telebot
import db
import scraper
import ai_translator
from config import TARGET_CHANNEL_ID, CHANNEL_LINK, ADMIN_ID, COMMENT_CHANNEL_ID
from datetime import datetime
import threading

scheduler = BackgroundScheduler(timezone='Asia/Tashkent')

def fetch_and_queue_posts(bot=None):
    """
    Saytdan yangi postlarni topadi va navbatga qo'shadi.
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
        
    new_posts = []
    start_index = 0
    if last_id:
        for idx, post in enumerate(all_posts):
            if post["id"] == last_id:
                start_index = idx + 1
                break
        else:
            # Agar last_id topilmasa (masalan yangi sayt), faqat oxirgi 3 tasini olamiz
            start_index = max(0, len(all_posts) - 3)
            
    for i in range(start_index, len(all_posts)):
        if not db.is_post_seen(all_posts[i]["id"]):
            new_posts.append(all_posts[i])
        
    highest_id = last_id
    for post in new_posts:
        highest_id = post["id"] # xronologik
        if post["text"]:
            db.add_queued_post(post)
            db.set_last_id(highest_id) # Set seen as soon as queued
            print(f"Yangi post navbatga tushdi: {post['id']}")
            
    if new_posts:
        db.set_last_id(highest_id)

def chunk_text(text, max_len=4096):
    """Matnni ko'rsatilgan uzunlikka moslab ajratadi."""
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # oxirgi probel yoki newline orqali kesamiz
        split_at = text.rfind('\n', 0, max_len)
        if split_at == -1:
            split_at = text.rfind(' ', 0, max_len)
        if split_at == -1:
            split_at = max_len
            
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    return chunks

def parse_ai_response(text):
    """Matnni [XABAR] va [KOMMENT] qismlariga ajratadi."""
    xabar = text
    komment = ""
    
    if "[XABAR]" in text and "[KOMMENT]" in text:
        parts = text.split("[KOMMENT]")
        xabar = parts[0].replace("[XABAR]", "").strip()
        komment = parts[1].strip()
    elif "[KOMMENT]" in text:
        parts = text.split("[KOMMENT]")
        xabar = parts[0].strip()
        komment = parts[1].strip()
        
    return xabar, komment

def fallback_comment_delivery(bot, msg_id, text, delay=20):
    import time
    import db
    time.sleep(delay)
    # Agar oradan 20 soniya o'tsa ham main.py dagi handler qabul qilolmagan bo'lsa (Privacy mode ehtiyotidan)
    if db.get_pending_comment(msg_id):
        try:
            if COMMENT_CHANNEL_ID:
                header = f"👆 <b>Yuqoridagi maqola bo'yicha batafsil izoh:</b>\n\n"
                chunks = chunk_text(text, 3900)
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        bot.send_message(COMMENT_CHANNEL_ID, header + chunk, parse_mode="HTML")
                    else:
                        bot.send_message(COMMENT_CHANNEL_ID, chunk, parse_mode="HTML")
        except Exception as e:
            try: bot.send_message(ADMIN_ID, f"⚠️ Izohni sug'urta zaxirasidan (Fallback) yuborishda xato: {e}")
            except: pass
        finally:
            db.delete_pending_comment(msg_id)

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

    main_post, comment_post = parse_ai_response(translated_text)

    # Post oxiriga kanal shiori va ssilkasini biriktirish
    slogan = f"\n\n🚀 Obuna bo'lish esdan chiqmasin: bizda har kuni qaynoq layfxaklar va yangiliklar!\n👉 Kanalimiz: {CHANNEL_LINK}"
    # Foydalanuvchi talabi bilan asosiy postni o'zida shior va manzil yoziladi
    main_post += slogan

    try:
        video_url = post.get('video')
        image_url = post.get('image')
        
        sent_msg = None
        if video_url:
            sent_msg = bot.send_video(TARGET_CHANNEL_ID, video_url, caption=main_post, parse_mode="HTML")
        elif image_url:
            sent_msg = bot.send_photo(TARGET_CHANNEL_ID, image_url, caption=main_post, parse_mode="HTML")
        else:
            sent_msg = bot.send_message(TARGET_CHANNEL_ID, main_post, parse_mode="HTML")
            
        if comment_post and sent_msg:
            # Kommentni xotiraga yozamiz. main.py uni ushlab olib guruhdagi forward ostiga javob yozadi!
            db.add_pending_comment(sent_msg.message_id, comment_post)
            # Yana bir kafolat uchun timer (fallback) ishga tushiramiz:
            threading.Thread(target=fallback_comment_delivery, args=(bot, sent_msg.message_id, comment_post)).start()
                
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
    scheduler.add_job(
        fetch_and_queue_posts,
        trigger="interval",
        minutes=10,
        kwargs={"bot": bot}
    )
    
    scheduler.add_job(
        process_queue_and_post,
        trigger="interval",
        minutes=15,
        kwargs={"bot": bot}
    )
    
    fetch_and_queue_posts(bot)
