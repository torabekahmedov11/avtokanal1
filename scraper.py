import feedparser
from bs4 import BeautifulSoup

def is_valid_image_url(url):
    if not url or not isinstance(url, str):
        return False
    url_lower = url.lower().strip()
    if not (url_lower.startswith('http://') or url_lower.startswith('https://')):
        return False
    if url_lower.startswith('data:') or '.svg' in url_lower:
        return False
    return True

def extract_video_url(soup, entry):
    video_url = None
    
    # 1. Media content yoki enclosures
    if 'media_content' in entry:
        for media in entry.media_content:
            m_type = media.get('type', '')
            m_url = media.get('url', '')
            if 'video' in m_type or m_url.lower().endswith(('.mp4', '.webm', '.mov', '.m4v')):
                video_url = m_url
                break

    if not video_url and getattr(entry, 'enclosures', None):
        for enc in entry.enclosures:
            enc_type = getattr(enc, 'type', '') or enc.get('type', '')
            enc_href = getattr(enc, 'href', '') or enc.get('href', '')
            if 'video' in enc_type or enc_href.lower().endswith(('.mp4', '.webm', '.mov', '.m4v')):
                video_url = enc_href
                break

    # 2. HTML video va source teglari
    if not video_url:
        video_tag = soup.find('video')
        if video_tag:
            if video_tag.get('src'):
                video_url = video_tag.get('src')
            else:
                source_tag = video_tag.find('source')
                if source_tag and source_tag.get('src'):
                    video_url = source_tag.get('src')

    # 3. HTML iframe teglari (YouTube, Vimeo yoki mp4)
    if not video_url:
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            if not src:
                continue
            if src.startswith('//'):
                src = 'https:' + src
            if any(k in src.lower() for k in ['youtube.com', 'youtu.be', 'vimeo.com']) or src.lower().endswith(('.mp4', '.webm', '.mov')):
                video_url = src
                break

    # 4. Direct video havolalari <a> teglarida
    if not video_url:
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.lower().endswith(('.mp4', '.webm', '.mov', '.m4v')):
                video_url = href
                break

    if video_url and video_url.startswith('//'):
        video_url = 'https:' + video_url

    if video_url and (video_url.startswith('http://') or video_url.startswith('https://')):
        return video_url
        
    return None

def scrape_telegram_channel(rss_url, last_id):
    """
    Saytning RSS Feed zanjiridan postlarni o'qiydi.
    (Funksiya formati eski nomida qoldirildi, barcha qismlar ishlashi uchun)
    """
    try:
        feed = feedparser.parse(rss_url)
    except Exception as e:
        print(f"Scraper error (RSS o'qishda): {e}")
        return []

    new_posts = []
    
    # Eng yangi postlarni eng oxiridan ko'rib chiqish kerak zanjir odatda reverse-chrono bo'ladi
    # Bizga esa xronologik tarzda kerak.
    entries = reversed(feed.entries)
    
    for entry in entries:
        post_id = entry.get('link', '') or entry.get('id', '')
        if not post_id:
            continue
            
        text = entry.get('title', '') + "\n\n"
        
        # Summary ichida HTML bo'lishi mumkin, ba'zan esa 'content' ichida bo'ladi
        content_html = entry.get('summary', '') or entry.get('description', '')
        if 'content' in entry and len(entry.content) > 0:
            content_html = entry.content[0].value
            
        soup = BeautifulSoup(content_html, 'html.parser')
        
        # Rasmni topish (agar bo'lsa)
        image_url = None
        img_tag = soup.find('img')
        if img_tag and img_tag.get('src'):
            image_url = img_tag.get('src')
            
        if not image_url:
            # Ba'zi RSS larda rasm (media) atributida, enclosure'da bo'lishi mumkin
            if 'media_content' in entry and len(entry.media_content) > 0:
                image_url = entry.media_content[0].get('url')
            elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                image_url = entry.media_thumbnail[0].get('url')
            elif getattr(entry, 'enclosures', None):
                for enc in entry.enclosures:
                    if 'image' in getattr(enc, 'type', '') or 'image' in enc.get('type', ''):
                        image_url = enc.get('href')
                        break
        
        if not is_valid_image_url(image_url):
            image_url = None

        # Video topish (agar bo'lsa)
        video_url = extract_video_url(soup, entry)
        
        # Matnni tozalash (yangi qatorlarni saqlab qolish yaxshi)
        clean_summary = soup.get_text('\n', strip=True)
        if clean_summary and clean_summary != entry.get('title', ''):
            text += clean_summary
            
        # ---------------- REKLAMA FILTRI ----------------
        title_lower = entry.get('title', '').lower()
        link_lower = post_id.lower()
        
        ad_keywords = ['deal', 'sale', 'sponsor', 'promoted', 'amazon', 'aliexpress', 'discount', '% off', 'coupon', 'woot']
        is_ad = False
        for kw in ad_keywords:
            if kw in title_lower or kw in link_lower:
                is_ad = True
                break
                
        if is_ad:
            print(f"Reklama po'sti o'tkazib yuborildi: {title_lower}")
            continue
        # ------------------------------------------------
            
        new_posts.append({
            "id": post_id,
            "text": text,
            "image": image_url,
            "video": video_url
        })
        
    return new_posts
