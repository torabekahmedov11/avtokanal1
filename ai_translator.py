import requests
import re
from config import OPENROUTER_API_KEY

SYSTEM_PROMPT = """Siz Telegramdagi eng mashhur va jozibali texnologik va hayotiy yangiliklar kanalining professional va o'tkir muharririsiz. Siz matnlarni mutlaqo insoniy til samimiyatida o'zbek tiliga jozibador tarjima qilasiz.

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

def translate_and_spice_up(text):
    if not text or not text.strip():
        return ""

    ad_keywords = ['deal', 'sale', 'sponsor', 'promoted', 'amazon', 'aliexpress', 'discount', '% off', 'coupon', 'woot']
    text_lower = text.lower()
    for kw in ad_keywords:
        if kw in text_lower:
            return "[FILTERED]"

    res = translate_with_openrouter(text)
    if res:
        return res

    print("⚠️ OpenRouter AI javob bermadi yoki kalit yo'q.")
    return None
