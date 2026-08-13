import requests
import io
import base64
from PIL import Image
import re
from config import OPENROUTER_API_KEY

SYSTEM_PROMPT = """Siz Telegramdagi eng mashhur va jozibali texnologik va hayotiy yangiliklar kanalining professional va o'tkir muharririsiz. Siz matnlarni va rasmlardagi axborotlarni mutlaqo insoniy til samimiyatida o'zbek tiliga jozibador va tushunarli tarjima qilasiz.

Qat'iy Senzura Qoidalari:
1. Agar matnda alkogol, qimor, 18+ behayo mazmun, firibgarlik bo'lsa, MUTLAQO TARJIMA QILMANG! Faqat "[FILTERED]" deb qaytaring.

Formatlash va Uslub Qoidalari:
2. Matnni MAJBURAN 2 qismga ajrating:
[XABAR]
(bu yerda Telegram postining qisqa, sarlavhali ko'rinishi: eng birinchi qatorda e'tiborni tortuvchi <b>Sarlavha</b>, davomida 2-3 ta ixcham abzas. Tugatishda: <i>(Barchasini bilish uchun quyidagi tugmani bosing 👇)</i>)

[BATAFSIL]
(bu yerda esa Telegraph sahifasi uchun maqolaning to'liq sirlari va qadamma-qadam batafsil ma'lumotlari)

3. Format uchun faqat <b> va <i> HTML teglardan foydalaning. Yulduzcha (*) yoki Markdown umuman ishlatmang.
"""

OPENROUTER_MODELS = [
    "openrouter/free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
    "liquid/lfm-2.5-2.6b:free"
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
    """Rasm URL dan sifatli base64 JPEG tayyorlaydi."""
    try:
        r = requests.get(image_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code == 200:
            img = Image.open(io.BytesIO(r.content)).convert('RGB')
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
            return f"data:image/jpeg;base64,{b64_str}"
    except Exception as e:
        print(f"Rasm kovertatsiyasida xato: {e}")
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

    for model in OPENROUTER_MODELS:
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
                    print(f"✅ Vision AI ({model}) rasm tahlili va tarjimasi muvaffaqiyatli!")
                    return content
        except Exception as e:
            print(f"Vision AI ({model}) xatosi: {e}")

    return None

def translate_with_openrouter(text):
    if not OPENROUTER_API_KEY:
        print("⚠️ OPENROUTER_API_KEY sozlanmagan! .env fayliga kalitni kiriting.")
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
                    print(f"✅ OpenRouter AI ({model}) tarjimasi muvaffaqiyatli!")
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

    print("⚠️ OpenRouter AI javob bermadi yoki kalit yo'q.")
    return None
