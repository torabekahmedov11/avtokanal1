import feedparser
from bs4 import BeautifulSoup

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
            
        # last_id check (string format)
        # Assuming we just need to avoid adding already fetched. Unfortunately string comparison
        # is tricky, so we will handle "seen" IDs differently. 
        # But for simplification: if we hit the last_id while iterating (from oldest to newest), 
        # we consider everything after it as new.
        
        # We will retrieve title + summary text
        text = entry.get('title', '') + "\n\n"
        
        # Summary ichida HTML bo'lishi mumkin
        summary_html = entry.get('summary', '') or entry.get('description', '')
        
        soup = BeautifulSoup(summary_html, 'html.parser')
        
        # Rasmni topish (agar bo'lsa)
        image_url = None
        img_tag = soup.find('img')
        if img_tag and img_tag.get('src'):
            image_url = img_tag.get('src')
        else:
            # Ba'zi RSS larda rasm rasm(media) atributida bo'lishi mumkin
            if 'media_content' in entry and len(entry.media_content) > 0:
                image_url = entry.media_content[0].get('url')
        
        # Matnni tozalash
        clean_summary = soup.get_text().strip()
        if clean_summary and clean_summary != entry.get('title', ''):
            text += clean_summary
            
        new_posts.append({
            "id": post_id,
            "text": text,
            "image": image_url,
            "video": None # RSS dan video olish sal qiyinroq, odatda rasm bo'ladi
        })
        
    return new_posts
