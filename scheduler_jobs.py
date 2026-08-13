import io
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
import db
import scraper
import ai_translator
from config import TARGET_CHANNEL_ID, CHANNEL_LINK, ADMIN_ID
from datetime import datetime
import pytz

scheduler = BackgroundScheduler(timezone='Asia/Tashkent')

def get_tashkent_now():
    """O'zbekiston (Toshkent) vaqti bilan hozirgi vaqtni qaytaradi."""
    tz = pytz.timezone('Asia/Tashkent')
    return datetime.now(tz)

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

def get_post_markup(original_url=None):
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    if CHANNEL_LINK:
        ch_link = CHANNEL_LINK if CHANNEL_LINK.startswith("http") else f"https://t.me/{CHANNEL_LINK.replace('@', '')}"
        buttons.append(InlineKeyboardButton("➕ Obuna bo'lish", url=ch_link))
    if buttons:
        markup.add(*buttons)
        return markup
    return None

def send_post_with_media(bot: telebot.TeleBot, channel_id, caption, post_data, markup=None):
    """
    Postni barcha turdagi media bilan birga Telegram kanalga xavfsiz va ishonchli yuboradi.
    Rasm, Video, GIF (animatsiya) va Fayl (hujjat) larni qo'llab-quvvatlaydi.
    """
    photos = post_data.get('photos', [])
    videos = post_data.get('videos', [])
    is_gif = post_data.get('is_gif', False)
    docs = post_data.get('docs', [])

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

    # 2. Bitta rasm
    if photos:
        p_url = photos[0]
        try:
            return bot.send_photo(channel_id, p_url, caption=caption, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            print(f"Rasm URL bilan yuborish feyl ({e}), fayl strm yuklanmoqda...")
            stream = download_file_stream(p_url)
            if stream:
                try:
                    return bot.send_photo(channel_id, stream, caption=caption, parse_mode="HTML", reply_markup=markup)
                except Exception as e2:
                    print(f"Rasm stream yuborish ham feyl: {e2}")

    # 3. Video yoki GIF
    if videos:
        v_url = videos[0]
        if is_gif:
            try:
                return bot.send_animation(channel_id, v_url, caption=caption, parse_mode="HTML", reply_markup=markup)
            except Exception as e:
                print(f"GIF URL feyl ({e}), video/stream ga o'tilmoqda...")
                stream = download_file_stream(v_url)
                if stream:
                    try:
                        return bot.send_animation(channel_id, stream, caption=caption, parse_mode="HTML", reply_markup=markup)
                    except Exception: pass
        
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

    # 5. Faqat Matn (yoki media yuklash muvaffaqiyatsiz bo'lganda Fallback)
    try:
        return bot.send_message(channel_id, caption, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        print(f"HTML parse mode xatosi ({e}), oddiy tekis matnda jo'natilmoqda...")
        clean_text = caption.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
        return bot.send_message(channel_id, clean_text, reply_markup=markup)

def check_and_post_instantly(bot: telebot.TeleBot, force=False):
    """
    Telegram donor kanaldan yangi postlarni tekshiradi va DARHOL tarjima qilib bizning kanalga joylaydi.
    Rejalashtirish va kutish yo'q!
    """
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

    # Ko'rilmagan yangi postlarni xronologik (eskisidan yangisiga) saralash
    new_posts = []
    for post in all_posts:
        pid = post.get("id")
        if not pid or db.is_post_seen(pid):
            continue
        new_posts.append(post)

    if not new_posts:
        print(f"[{now_str}] Barcha postlar allaqachon kanalga joylangan.")
        return

    print(f"🔥 {len(new_posts)} ta YANGI POST topildi! Darhol tarjima qilinib joylanmoqda...")

    posted_count = 0
    for post in new_posts:
        pid = post.get("id")
        db.mark_as_seen(pid)
        db.set_last_id(pid)

        raw_text = post.get("text", "")
        # Matn bo'lmasa lekin media bo'lsa
        if not raw_text:
            if post.get("photos"):
                raw_text = "📷 Surat"
            elif post.get("videos"):
                raw_text = "🎥 Video"
            elif post.get("docs"):
                raw_text = "📁 Fayl"
            else:
                continue

        translated_text = ai_translator.translate_and_spice_up(raw_text)

        if not translated_text or "[FILTERED]" in translated_text:
            print(f"Post filtrlandi yoki tarjima qilinmadi: {pid}")
            continue

        # Kanal shiorini qo'shish
        slogan = f"\n\n🚀 Obuna bo'lish esdan chiqmasin!\n👉 Kanalimiz: {CHANNEL_LINK}" if CHANNEL_LINK else ""
        caption = translated_text + slogan

        markup = get_post_markup()

        if TARGET_CHANNEL_ID:
            try:
                send_post_with_media(bot, TARGET_CHANNEL_ID, caption, post, markup=markup)
                posted_count += 1
                print(f"✅ POST KANALGA JOYLANDI: {pid}")
            except Exception as e:
                print(f"Post joylashda xatolik ({pid}): {e}")
        else:
            print(f"⚠️ TARGET_CHANNEL_ID sozlanmagan! Post joylanmadi: {pid}")

    print(f"⚡ Jami {posted_count} ta yangi post tezkor joylandi.")

def fetch_and_queue_posts(bot=None, force=False):
    """Eski tugmalar bilan moslik uchun wrapper."""
    check_and_post_instantly(bot, force=force)

def process_queue_and_post(bot: telebot.TeleBot):
    """Eski tugmalar bilan moslik uchun wrapper."""
    check_and_post_instantly(bot)

def setup_scheduler(bot: telebot.TeleBot):
    """
    Donor Telegram kanalni har 1 daqiqada tekshiradigan tezkor avto-post tizimi.
    """
    scheduler.add_job(
        check_and_post_instantly,
        trigger="interval",
        minutes=1,
        kwargs={"bot": bot}
    )
    
    # Bot ishga tushishi bilan birinchi tekshiruv
    try:
        check_and_post_instantly(bot)
    except Exception as e:
        print(f"Boshlang'ich tekshiruvda xatolik: {e}")
