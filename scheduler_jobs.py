from apscheduler.schedulers.background import BackgroundScheduler
import telebot
import db
import scraper
import ai_translator
from config import TARGET_CHANNEL_ID
import datetime

scheduler = BackgroundScheduler(timezone='Asia/Tashkent')

def fetch_and_queue_posts():
    """
    Saytdan yangi postlarni topadi va navbatga qo'shadi.
    """
    donor = db.get_donor_url()
    last_id = db.get_last_id()
    
    print(f"[{datetime.datetime.now()}] Skraping kuting... ({donor})")
    all_posts = scraper.scrape_telegram_channel(donor, last_id)
    
    if not all_posts:
        return
        
    new_posts = []
    # top_index is where last_id is located. By default, consider all as new.
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
        new_posts.append(all_posts[i])
        
    highest_id = last_id
    for post in new_posts:
        highest_id = post["id"] # xronologik
        if post["text"]:
            db.add_queued_post(post)
            print(f"Yangi post navbatga tushdi: {post['id']}")
            
    if new_posts:
        db.set_last_id(highest_id)

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
        return

    # Senzura testi
    if "[FILTERED]" in translated_text:
        print(f"Post SENZURAdan o'tmadi! Bloklandi.")
        return

    try:
        video_url = post.get('video')
        image_url = post.get('image')
        
        if len(translated_text) > 1000:
            if video_url:
                bot.send_video(TARGET_CHANNEL_ID, video_url)
            elif image_url:
                bot.send_photo(TARGET_CHANNEL_ID, image_url)
            bot.send_message(TARGET_CHANNEL_ID, translated_text)
        else:
            if video_url:
                bot.send_video(TARGET_CHANNEL_ID, video_url, caption=translated_text)
            elif image_url:
                bot.send_photo(TARGET_CHANNEL_ID, image_url, caption=translated_text)
            else:
                bot.send_message(TARGET_CHANNEL_ID, translated_text)
                
        print(f"✅ Kanalga POST yuborildi! (Qoldi: {db.get_queued_count()})")
    except Exception as e:
        print(f"Jo'natishda xato: {e}")

def setup_scheduler(bot: telebot.TeleBot):
    scheduler.add_job(
        fetch_and_queue_posts,
        trigger="interval",
        minutes=10
    )
    
    scheduler.add_job(
        process_queue_and_post,
        trigger="interval",
        minutes=3,
        kwargs={"bot": bot}
    )
    
    fetch_and_queue_posts()
