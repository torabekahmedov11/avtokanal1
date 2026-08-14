import requests
import io
import base64
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
from config import OPENROUTER_API_KEY

SYSTEM_PROMPT = """Siz O'zbekistondagi eng mashhur IT va Vibe Coding texnologik Telegram kanalining tajribali, o'tkir va o'ta samimiy kontent-muharririsiz. Sizning vazifangiz shunchaki so'zma-so'z tarjima qilish emas, balki berilgan texnologik xabar, yangilik yoki rasmlardagi ma'lumotni xuddi Jonli Real Odam (tajribali bloger / do'st) o'z obunachilariga aytib berayotgandek jonli, tushunarli, jozibali va qiziqarli qilib O'zbek tilida qayta yozishdir.

Qat'iy Talablar:
1. Quruq, mashina tarjimasidan QAT'IY VOZ KECHING. So'zlarni o'zbek tilining tabiiy sozi, jargon va jonli iboralari bilan ravon yozing.
2. Senzura: Agar matnda alkogol, qimor, 18+ behayo mazmun, firibgarlik bo'lsa, MUTLAQO YAZMANG! Faqat "[FILTERED]" deb qaytaring.

Formatlash Qoidalari:
Matnni MAJBURAN 2 qismga ajrating:
[XABAR]
(Bu yerda Telegram postining jonli va o'tkir qismi: birinchi qatorda e'tiborni tortuvchi <b>Sarlavha</b> (emojilar bilan), davomida 2-3 ta juda qiziqarli va ixcham abzas. Tugatishda: <i>(Barchasini bilish uchun quyidagi tugmani bosing 👇)</i>)

[BATAFSIL]
(Bu yerda Telegraph sahifasi uchun maqolaning to'liq sirlari, imkoniyatlari va qadamma-qadam tushuntirilgan batafsil ma'lumotlari)

Faqat <b> va <i> HTML teglardan foydalaning. Yulduzcha (*) yoki Markdown ishlatmang.
"""

OPENROUTER_MODELS = [
    "google/gemma-4-31b-it:free",
    "openrouter/free",
    "nvidia/nemotron-3.5-lightning:free",
    "liquid/lfm-2.5-2.6b:free"
]

# Vision-capable modellar (rasmni tahlil qila oladigan)
VISION_MODELS = [
    "google/gemma-4-31b-it:free",
    "openrouter/free",
    "meta-llama/llama-4-maverick:free",
]

def parse_telegraph_response(text):
    if not text:
        return "", ""
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

def convert_image_url_to_base64_jpeg(image_url):
    """Rasm URL dan sifatli base64 JPEG tayyorlaydi. Hajmi cheklangan."""
    try:
        r = requests.get(image_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code != 200:
            print(f"Rasm yuklab bo'lmadi, status: {r.status_code}")
            return None
        if HAS_PIL:
            img = Image.open(io.BytesIO(r.content)).convert('RGB')
            # Katta rasmlarni kichiklashtirish (API payload limiti uchun)
            max_side = 1024
            if max(img.size) > max_side:
                img.thumbnail((max_side, max_side), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=80)
            b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        else:
            # Pillow o'rnatilmagan bo'lsa, xom baytlarni ishlatamiz
            b64_str = base64.b64encode(r.content).decode('utf-8')
        return f"data:image/jpeg;base64,{b64_str}"
    except Exception as e:
        print(f"Rasm konvertatsiyasida xato: {e}")
    return None

def translate_image_with_vision(image_url, raw_text=""):
    """
    Rasm ichidagi ruscha/inglizcha matn yoki skrinshotni Vision AI orqali tahlil qilib, o'zbek tilida post tayyorlaydi.
    """
    if not OPENROUTER_API_KEY:
        return None

    data_uri = convert_image_url_to_base64_jpeg(image_url)
    if not data_uri:
        return None

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://telegram.org",
        "X-Title": "Telegram Auto Channel Bot"
    }

    user_prompt = f"Ushbu rasmdagi ruscha yoki inglizcha matn hamda axborotni to'liq tahlil qilib, o'zbek auditoriyasi uchun jozibali, ishonchli va aniq post tayyorlang."
    if raw_text and len(raw_text.strip()) > 5:
        user_prompt += f"\n\nQo'shimcha post matni: {raw_text}"

    for model in VISION_MODELS:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": data_uri}}
                    ]
                }
            ],
            "temperature": 0.5
        }
        try:
            print(f"Vision AI ({model}) orqali rasm tahlili yuborilmoqda...")
            r = requests.post(url, headers=headers, json=payload, timeout=25)
            if r.status_code == 200:
                res = r.json()
                if 'choices' in res and len(res['choices']) > 0:
                    content = res['choices'][0]['message']['content'].strip()
                    content = content.replace('**', '').replace('*', '')
                    print(f"OK: Vision AI ({model}) rasm tahlili va tarjimasi muvaffaqiyatli!")
                    return content
        except Exception as e:
            print(f"Vision AI ({model}) xatosi: {e}")

    return None

def translate_with_openrouter(text):
    if not OPENROUTER_API_KEY:
        print("OPENROUTER_API_KEY sozlanmagan! .env fayliga kalitni kiriting.")
        return None

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://telegram.org",
        "X-Title": "Telegram Auto Channel Bot"
    }

    for model in OPENROUTER_MODELS:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            "temperature": 0.5
        }
        try:
            print(f"OpenRouter ({model}) orqali tarjima so'rovi yuborilmoqda...")
            r = requests.post(url, headers=headers, json=payload, timeout=20)
            if r.status_code == 200:
                res = r.json()
                if 'choices' in res and len(res['choices']) > 0:
                    content = res['choices'][0]['message']['content'].strip()
                    content = content.replace('**', '').replace('*', '')
                    print(f"OK: OpenRouter AI ({model}) tarjimasi muvaffaqiyatli!")
                    return content
            else:
                print(f"OpenRouter ({model}) javob kodi: {r.status_code} - {r.text[:150]}")
        except Exception as e:
            print(f"OpenRouter ({model}) tarjima xatosi: {e}")

    return None

def translate_and_spice_up(text, photo_url=None):
    if not text and not photo_url:
        return ""

    ad_keywords = ['deal', 'sale', 'sponsor', 'promoted', 'amazon', 'aliexpress', 'discount', '% off', 'coupon', 'woot']
    text_lower = (text or "").lower()
    for kw in ad_keywords:
        if kw in text_lower:
            return "[FILTERED]"

    # Agar post faqat rasm bo'lsa yoki qisqa matn bo'lsa -> Vision AI orqali rasmni tahlil qilamiz
    if photo_url and (not text or len(text.strip()) < 100):
        print("Rasm bor post: Vision AI orqali rasmdagi ruscha/inglizcha matn va axborot tahlil qilinmoqda...")
        vision_res = translate_image_with_vision(photo_url, raw_text=text)
        if vision_res:
            return vision_res

    # Odatiy matn bo'lsa
    res = translate_with_openrouter(text)
    if res:
        return res

    print("OpenRouter AI javob bermadi yoki kalit yo'q.")
    return None

