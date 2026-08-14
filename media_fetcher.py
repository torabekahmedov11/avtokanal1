"""
Media Fetcher — Darslik uchun avtomatik rasm, GIF va video topish moduli.
Hech qanday API key talab qilmaydi. Hammasi bepul va avtomatik.
"""
import requests
import io
import random

# ============================================================
# 1. POLLINATIONS.AI — Bepul AI Rasm Generatsiya
# ============================================================
def fetch_ai_image(topic, lesson_num=1):
    """
    Pollinations.ai orqali dars mavzusiga mos noyob AI rasm generatsiya qiladi.
    API key KERAK EMAS. Bepul va cheksiz.
    Rasm URL va BytesIO stream qaytaradi.
    """
    prompt = f"Modern futuristic tech illustration about {topic}, coding, programming, digital art, vibrant neon colors, dark background, 4k quality"
    
    # Pollinations.ai — GET so'rov bilan rasm generatsiya
    encoded_prompt = requests.utils.quote(prompt)
    seed = (lesson_num * 7919 + 42) % 100000  # Har bir dars uchun unikal seed
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=576&seed={seed}&nologo=true"
    
    try:
        print(f"Pollinations.ai dan AI rasm generatsiya qilinmoqda: dars #{lesson_num}...")
        r = requests.get(image_url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code == 200 and len(r.content) > 1000:
            bio = io.BytesIO(r.content)
            bio.name = f"lesson_{lesson_num}.jpg"
            print(f"OK: AI rasm generatsiya qilindi ({len(r.content)} bytes)")
            return bio, image_url
    except Exception as e:
        print(f"Pollinations.ai rasm xatosi: {e}")
    
    return None, None


# ============================================================
# 2. GIPHY — Bepul GIF qidirish (API key'siz)
# ============================================================
def fetch_gif(query):
    """
    GIPHY'dan mavzuga mos GIF qidiradi.
    Bepul public beta API key ishlatiladi.
    """
    # GIPHY public beta key (rasmiy docs dan — hamma foydalanishi mumkin)
    api_key = "dc6zaTOxFJmzC"
    url = f"https://api.giphy.com/v1/gifs/search"
    params = {
        "api_key": api_key,
        "q": f"{query} coding programming",
        "limit": 10,
        "rating": "g",
        "lang": "en"
    }
    
    try:
        print(f"GIPHY dan GIF qidirilmoqda: '{query}'...")
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json().get("data", [])
            if data:
                gif = random.choice(data[:5])  # Top 5 dan random tanlash
                gif_url = gif.get("images", {}).get("original", {}).get("url", "")
                if gif_url:
                    # GIF ni yuklab olish
                    gr = requests.get(gif_url, timeout=15)
                    if gr.status_code == 200:
                        bio = io.BytesIO(gr.content)
                        bio.name = "lesson.gif"
                        print(f"OK: GIF topildi va yuklandi ({len(gr.content)} bytes)")
                        return bio, gif_url
    except Exception as e:
        print(f"GIPHY GIF qidirish xatosi: {e}")
    
    return None, None


# ============================================================
# 3. PIXABAY — Bepul video qidirish (API key'siz)
# ============================================================
def fetch_video(query):
    """
    Pixabay'dan mavzuga mos qisqa bepul video qidiradi.
    Pixabay public API key ishlatiladi.
    """
    api_key = "47268944-950060e69539e22e7e1e4bbbb"
    url = "https://pixabay.com/api/videos/"
    params = {
        "key": api_key,
        "q": f"{query} technology coding",
        "per_page": 5,
        "safesearch": "true",
        "video_type": "animation"
    }
    
    try:
        print(f"Pixabay dan video qidirilmoqda: '{query}'...")
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            hits = r.json().get("hits", [])
            if hits:
                video = random.choice(hits[:3])
                # Eng kichik (tiny) versiyasini olish — tez yuklanadi
                video_url = video.get("videos", {}).get("tiny", {}).get("url", "")
                if not video_url:
                    video_url = video.get("videos", {}).get("small", {}).get("url", "")
                if video_url:
                    vr = requests.get(video_url, timeout=20)
                    if vr.status_code == 200:
                        bio = io.BytesIO(vr.content)
                        bio.name = "lesson.mp4"
                        print(f"OK: Video topildi va yuklandi ({len(vr.content)} bytes)")
                        return bio, video_url
    except Exception as e:
        print(f"Pixabay video qidirish xatosi: {e}")
    
    return None, None


# ============================================================
# 4. ASOSIY FUNKSIYA — Dars raqamiga qarab media turini aylantirish
# ============================================================
def get_lesson_media(topic, lesson_num):
    """
    Dars raqamiga qarab media turini avtomatik aylantiradi:
    - Har 3 darsda 1 marta: GIF
    - Har 5 darsda 1 marta: Video
    - Qolgan darslar: AI generatsiya qilingan rasm
    
    Returns: (media_stream, media_type, media_url)
        media_type: 'photo', 'animation', 'video'
    """
    # Har 5-darsda video sinab ko'rish
    if lesson_num % 5 == 0:
        stream, url = fetch_video(topic)
        if stream:
            return stream, "video", url
    
    # Har 3-darsda GIF sinab ko'rish
    if lesson_num % 3 == 0:
        stream, url = fetch_gif(topic)
        if stream:
            return stream, "animation", url
    
    # Asosiy variant: AI rasm (eng ishonchli)
    stream, url = fetch_ai_image(topic, lesson_num)
    if stream:
        return stream, "photo", url
    
    # Agar hech narsa ishlamasa, GIF orqali fallback
    stream, url = fetch_gif(topic)
    if stream:
        return stream, "animation", url
    
    return None, None, None
