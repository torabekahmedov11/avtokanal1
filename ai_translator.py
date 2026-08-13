import requests
import re
from config import OPENROUTER_API_KEY

SYSTEM_PROMPT = """Siz Telegramdagi eng mashhur va jozibali texnologik va hayotiy yangiliklar kanalining professional va o'tkir muharririsiz. Siz matnlarni mutlaqo insoniy til samimiyatida o'zbek tiliga jozibador tarjima qilasiz.

Qoidalaringiz:
1. Agar matnda alkogol, qimor, 18+ behayo mazmun, firibgarlik bo'lsa, MUTLAQO TARJIMA QILMANG! Faqat "[FILTERED]" deb qaytaring.
2. Eng birinchi qatorda e'tiborni tortuvchi jozibador SARLAVHA (HTML qalin <b>Sarlavha</b> formatida).
3. Matn telegram posti ko'rinishida ixcham, o'qishga qulay va insoniy tilda ravon bo'lsin. Robot tilida quruq tarjima qilmang!
4. Format uchun faqat <b> va <i> HTML teglardan foydalaning. Yulduzcha (*) yoki Markdown umuman ishlatmang.
5. Post oxirida: <i>(Barchasini bilish uchun quyidagi manbani ko'ring 👇)</i>"""

OPENROUTER_MODELS = [
    "openrouter/free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
    "liquid/lfm-2.5-2.6b:free"
]

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

    # Reklama filtri
    ad_keywords = ['deal', 'sale', 'sponsor', 'promoted', 'amazon', 'aliexpress', 'discount', '% off', 'coupon', 'woot']
    text_lower = text.lower()
    for kw in ad_keywords:
        if kw in text_lower:
            return "[FILTERED]"

    # Faqat OpenRouter AI ishlatamiz
    res = translate_with_openrouter(text)
    if res:
        return res

    print("⚠️ OpenRouter AI javob bermadi yoki kalit yo'q.")
    return None
