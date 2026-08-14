import io
import requests
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
import db
import scraper
import ai_translator
import vibe_lessons
from telegraph_api import create_telegraph_page
from config import TARGET_CHANNEL_ID, CHANNEL_LINK, ADMIN_ID
from datetime import datetime
import pytz

scheduler = BackgroundScheduler(timezone='Asia/Tashkent')
_process_lock = threading.Lock()

def get_tashkent_now():
    """O'zbekiston (Toshkent) vaqti bilan hozirgi vaqtni qaytaradi."""
    tz = pytz.timezone('Asia/Tashkent')
    return datetime.now(tz)

def is_nighttime():
    """Toshkent vaqti bo'yicha 23:00 va 07:00 oralig'i."""
    now = get_tashkent_now()
    return now.hour >= 23 or now.hour < 7

def download_file_stream(url, timeout=15):
    """Media faylni URL dan byte stream sifatiga yuklab oladi (Telegram API uchun)."""
    if not url or not isinstance(url, str):
        return None
    try:
        r = requests.get(url, stream=True, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })
        if r.status_code == 200:
            bio = io.BytesIO(r.content)
            bio.name = url.split("?")[0].split("/")[-1] or "media_file"
            return bio
    except Exception as e:
        print(f"Media yuklash xatosi ({url}): {e}")
    return None

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

def send_post_with_media(bot: telebot.TeleBot, channel_id, caption, post_data, markup=None):
    """
    Postni barcha turdagi media bilan birga Telegram kanalga xavfsiz va dublikatsiz yuboradi.
    """
    photos = post_data.get('photos', [])
    videos = post_data.get('videos', [])
    is_gif = post_data.get('is_gif', False)
    docs = post_data.get('docs', [])

    # Telegram caption chegarasi: 1024 belgi (media postlar uchun)
    has_media = bool(photos or videos or docs)
    if has_media and len(caption) > 1024:
        caption = caption[:1020] + "..."

    # 1. Ko'p rasmlar (Media group)
    if len(photos) > 1:
        try:
            media_group = []
            for idx, p_url in enumerate(photos[:10]):
                p_caption = caption if idx == 0 else ""
                media_group.append(InputMediaPhoto(media=p_url, caption=p_caption, parse_mode="HTML"))
            return bot.send_media_group(channel_id, media=media_group)
        except Exception as e:
            print(f"MediaGroup yuborishda xato ({e}), bitta rasmga o'tilmoqda...")
            # Agar media group feyl bo'lsa, faqat birinchi rasmga urinib ko'ramiz
            # (keyingi 'if photos:' branchiga tushadi)

    # 2. Bitta rasm
    if photos:
        p_url = photos[0]
        try:
            return bot.send_photo(channel_id, p_url, caption=caption, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            print(f"Rasm URL bilan yuborish feyl ({e}), stream yuklanmoqda...")
            stream = download_file_stream(p_url)
            if stream:
                try:
                    return bot.send_photo(channel_id, stream, caption=caption, parse_mode="HTML", reply_markup=markup)
                except Exception as e2:
                    print(f"Rasm stream yuborish ham feyl: {e2}")
        # Rasm mavjud bo'lsa va yuborilgan bo'lsa (yoki feyl bo'lsa), takroriy text yubormaymiz!
        return

    # 3. Video yoki GIF
    if videos:
        v_url = videos[0]
        if is_gif:
            try:
                return bot.send_animation(channel_id, v_url, caption=caption, parse_mode="HTML", reply_markup=markup)
            except Exception as e:
                print(f"GIF URL feyl ({e}), stream ga o'tilmoqda...")
                stream = download_file_stream(v_url)
                if stream:
                    try:
                        return bot.send_animation(channel_id, stream, caption=caption, parse_mode="HTML", reply_markup=markup)
                    except Exception: pass
            return

        try:
            return bot.send_video(channel_id, v_url, caption=caption, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            print(f"Video URL feyl ({e}), video stream yuklanmoqda...")
            stream = download_file_stream(v_url)
            if stream:
                try:
                    return bot.send_video(channel_id, stream, caption=caption, parse_mode="HTML", reply_markup=markup)
                except Exception as e2:
                    print(f"Video stream yuborish ham feyl: {e2}")
        return

    # 4. Fayllar (Documents)
    if docs:
        d_href = docs[0].get('href')
        if d_href:
            try:
                return bot.send_document(channel_id, d_href, caption=caption, parse_mode="HTML", reply_markup=markup)
            except Exception as e:
                print(f"Document URL feyl ({e}), document stream yuklanmoqda...")
                stream = download_file_stream(d_href)
                if stream:
                    try:
                        return bot.send_document(channel_id, stream, caption=caption, parse_mode="HTML", reply_markup=markup)
                    except Exception: pass
        return

    # 5. Faqat Matn (Mediasiz postlar uchun)
    try:
        return bot.send_message(channel_id, caption, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        print(f"HTML parse mode xatosi ({e}), oddiy tekis matnda jo'natilmoqda...")
        clean_text = caption.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
        return bot.send_message(channel_id, clean_text, reply_markup=markup)

def check_and_post_instantly(bot: telebot.TeleBot, force=False):
    """
    Telegram donor kanaldan yangi postlarni tekshiradi va DARHOL tarjima qilib bizning kanalga joylaydi.
    """
    global _process_lock
    if not _process_lock.acquire(blocking=False):
        print("Boshqa tekshiruv jarayoni bajarilmoqda, o'tkazib yuborildi.")
        return

    try:
        donor_url = db.get_donor_url()
        last_id = db.get_last_id()
        now_str = get_tashkent_now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{now_str}] Donor Telegram kanal tekshirilmoqda... ({donor_url})")

        try:
            all_posts = scraper.scrape_telegram_channel(donor_url, last_id)
        except Exception as e:
            print(f"Scraping xatosi: {e}")
            if bot and ADMIN_ID:
                try:
                    bot.send_message(ADMIN_ID, f"⚠️ **Telegram Donor Skrapingida XATOLIK:**\n\n`{str(e)}`", parse_mode="Markdown")
                except: pass
            return

        if not all_posts:
            print(f"[{now_str}] Yangi postlar topilmadi.")
            return

        # Birinchi marta ulanayotganda (agar baza yangi bo'lsa), eski postlarni belgilab olamiz
        if not last_id and db.get_seen_count() == 0 and not force:
            print("Birinchi marta ulanmoqda: Donor kanaldagi mavjud postlar eslab qolindi.")
            for p in all_posts:
                db.mark_as_seen(p["id"])
                db.set_last_id(p["id"])
            return

        # Ko'rilmagan yangi postlarni topish
        new_posts = []
        for post in all_posts:
            pid = post.get("id")
            if not pid or db.is_post_seen(pid):
                continue
            new_posts.append(post)

        if force and not new_posts:
            # Majburiy bosganda oxirgi postni jo'natadi
            new_posts = [all_posts[-1]]

        if not new_posts:
            print(f"[{now_str}] Yangi post yo'q.")
            return

        print(f"🔥 {len(new_posts)} ta YANGI POST topildi! Darhol tarjima qilinib joylanmoqda...")

        for post in new_posts:
            pid = post.get("id")
            db.mark_as_seen(pid)
            db.set_last_id(pid)

            raw_text = post.get("text", "")
            photos = post.get("photos", [])
            photo_url = photos[0] if photos else None

            # Vision AI bilan rasmli hamda matnli postlarga ishlov berish
            translated_text = ai_translator.translate_and_spice_up(raw_text, photo_url=photo_url)

            if not translated_text or "[FILTERED]" in translated_text:
                print(f"Post filtrlandi: {pid}")
                continue

            main_post, batafsil_post = ai_translator.parse_telegraph_response(translated_text)

            slogan = f"\n\n🔥 Vibe Coding sari har kuni bir qadam!\n👉 Kanalimiz: {CHANNEL_LINK}" if CHANNEL_LINK else "\n\n🔥 Vibe Coding sari har kuni bir qadam!"
            caption = main_post + slogan

            telegraph_url = None
            if batafsil_post:
                telegraph_url = create_telegraph_page(title="Batafsil Qo'llanma", html_content=batafsil_post)

            markup = get_post_markup(telegraph_url)

            if TARGET_CHANNEL_ID:
                try:
                    send_post_with_media(bot, TARGET_CHANNEL_ID, caption, post, markup=markup)
                    print(f"✅ POST KANALGA JOYLANDI: {pid}")
                except Exception as e:
                    print(f"Post joylashda xatolik ({pid}): {e}")
            else:
                print(f"⚠️ TARGET_CHANNEL_ID sozlanmagan! Post joylanmadi: {pid}")

    finally:
        _process_lock.release()

def fetch_and_queue_posts(bot=None, force=False):
    """Admin menyusidagi 'Yangiliklar yig'ish' tugmasi uchun."""
    check_and_post_instantly(bot, force=force)

def process_queue_and_post(bot: telebot.TeleBot):
    """Admin menyusidagi 'Post chiqarish' tugmasi uchun."""
    check_and_post_instantly(bot, force=True)

def setup_scheduler(bot: telebot.TeleBot):
    """
    Donor Telegram kanalni har 1 daqiqada tekshiradigan avto-post tizimi
    + Har kuni 20:00 da Vibe Coding darsligi.
    """
    # RSS kanaldan yangiliklar — har 1 daqiqada
    scheduler.add_job(
        check_and_post_instantly,
        trigger="interval",
        minutes=1,
        kwargs={"bot": bot},
        id="rss_checker"
    )
    
    # Vibe Coding kunlik darslik — har kuni 20:00 Toshkent vaqtida
    scheduler.add_job(
        vibe_lessons.post_daily_lesson,
        trigger=CronTrigger(hour=20, minute=0, timezone='Asia/Tashkent'),
        kwargs={"bot": bot},
        id="daily_lesson"
    )
    print("Kunlik darslik taymeri sozlandi: Har kuni 20:00 (Toshkent vaqti)")
    
    try:
        check_and_post_instantly(bot)
    except Exception as e:
        print(f"Boshlang'ich tekshiruvda xatolik: {e}")
