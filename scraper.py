import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def format_telegram_url(channel_url):
    if not channel_url:
        return "https://t.me/s/vibecoding_tg"
    channel_url = channel_url.strip()
    if channel_url.startswith("@"):
        channel_url = channel_url[1:]
    if channel_url.startswith("https://t.me/s/"):
        return channel_url
    if channel_url.startswith("https://t.me/"):
        username = channel_url.split("https://t.me/")[1].split("/")[0]
        return f"https://t.me/s/{username}"
    if channel_url.startswith("t.me/s/"):
        return f"https://{channel_url}"
    if channel_url.startswith("t.me/"):
        username = channel_url.split("t.me/")[1].split("/")[0]
        return f"https://t.me/s/{username}"
    if not channel_url.startswith("http://") and not channel_url.startswith("https://"):
        return f"https://t.me/s/{channel_url}"
    return channel_url

def scrape_telegram_channel(rss_url, last_id=""):
    """
    Telegram kanalining web-preview (t.me/s/username) sahifasidan postlarni o'qiydi.
    Matn, rasm, video, GIF va fayllarni (documents) ajratib oladi.
    """
    target_url = format_telegram_url(rss_url)
    print(f"Scraping Telegram channel: {target_url}")
    
    try:
        r = requests.get(target_url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            print(f"Telegram scraping error, HTTP status: {r.status_code}")
            return []
    except Exception as e:
        print(f"Scraper network error: {e}")
        return []

    soup = BeautifulSoup(r.content, 'html.parser')
    messages = soup.find_all('div', class_='tgme_widget_message')
    
    posts = []
    
    for m in messages:
        post_id = m.get('data-post')
        if not post_id:
            continue
            
        # 1. Matn
        text_elem = m.find('div', class_='tgme_widget_message_text')
        text = text_elem.get_text('\n', strip=True) if text_elem else ""
        
        # 2. Rasmlar
        photos = []
        for p in m.find_all('a', class_='tgme_widget_message_photo_wrap'):
            style = p.get('style', '')
            if 'background-image:url(' in style:
                try:
                    img_url = style.split("background-image:url('")[1].split("')")[0]
                    photos.append(img_url)
                except IndexError:
                    pass
                    
        # 3. Videolar va GIF lar
        videos = []
        is_gif = False
        video_elems = m.find_all('video')
        for v in video_elems:
            v_src = v.get('src')
            if v_src:
                videos.append(v_src)
            if v.has_attr('autoplay') or v.has_attr('loop'):
                is_gif = True
                
        # 4. Hujjatlar / Fayllar
        docs = []
        doc_wraps = m.find_all('a', class_='tgme_widget_message_document_wrap')
        for d in doc_wraps:
            doc_href = d.get('href')
            doc_title_elem = d.find('div', class_='tgme_widget_message_document_title')
            doc_title = doc_title_elem.get_text(strip=True) if doc_title_elem else "fayl"
            docs.append({'href': doc_href, 'title': doc_title})

        # Hech qanday kontentsiz servis xabar bo'lsa o'tkazib yuborish
        if not text and not photos and not videos and not docs:
            continue

        # Reklama filtri
        text_lower = text.lower()
        ad_keywords = ['promoted', 'sponsor', 'reklama', 'skidka', 'coupon', '% off', 'woot']
        if any(kw in text_lower for kw in ad_keywords):
            print(f"Reklama po'sti o'tkazib yuborildi: {post_id}")
            continue

        posts.append({
            "id": post_id,
            "text": text,
            "photos": photos,
            "videos": videos,
            "is_gif": is_gif,
            "docs": docs,
            "image": photos[0] if photos else None,
            "video": videos[0] if videos else None
        })
        
    return posts
