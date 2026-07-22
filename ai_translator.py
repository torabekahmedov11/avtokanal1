import google.generativeai as genai
from config import GEMINI_API_KEY

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

_working_model_name = None

def get_working_model():
    global _working_model_name
    if _working_model_name:
        return _working_model_name

    candidates = [
        'gemini-flash-lite-latest',
        'gemini-2.5-flash',
        'gemini-2.0-flash-lite',
        'gemini-pro-latest'
    ]
    
    # Eng zo'ri: haqiqatda ishlayotganini jonli test qilib izlash
    for cand in candidates:
        try:
            m = genai.GenerativeModel(cand)
            resp = m.generate_content("ping", request_options={"timeout": 5.0})
            if resp.text:
                print(f"JONLI SINOVDA ISHLADI: {cand}")
                _working_model_name = cand
                return cand
        except Exception as e:
            print(f"{cand} sinovda ishlamadi: {e}")
            continue
            
    # Agar hech biri ishlamasa eng standardini qaytaramiz baribir
    return 'gemini-flash-lite-latest'

def translate_and_spice_up(text):
    if not GEMINI_API_KEY:
        return f"AI_ERROR: Gemini API kaliti yo'q. Asl matn:\n\n{text}"
    
    prompt = f"""
Siz Telegramdagi eng mashhur va qiziqarli texnologik va hayotiy loyihalar kanalining professional va o'tkir muharririsiz. Siz matnlarni mutlaqo insoniy til samimiyatida, har gal har xil jonli iboralardan foydalanib yozasiz.

Qat'iy Senzura Qoidalari:
1. Agar matnda alkogol, qimor, 18+ behayo mazmun, firibgarlik yoki islom diniga mutlaqo ziddiyatli g'oyalar bo'lsa, MUTLAQO TARJIMA QILMANG! Faqat "[FILTERED]" deb qaytaring.
2. Reklamalar va faqat mahalliy chet el g'iybatlarini olib tashlang ("[FILTERED]"). Faqat foydali texnologiya, gadjet va hayotiy maslahatlarni tayyorlang.

Formatlash va Uslub Qoidalari:
3. Matnni MAJBURAN 2 qismga ajrating:
[XABAR]
(bu yerda Telegram postining qisqa, sarlavhali ko'rinishi)

[BATAFSIL]
(bu yerda esa Telegraph uchun maqolaning to'liq sirlari va qadamma-qadam qo'llanmasi)

4. [XABAR] qismi talablari:
- Eng birinchi qatorda e'tiborni tortuvchi jozibador SARLAVHA (HTML qalin <b>Sarlavha</b> formatida).
- Sarlavha ostida darhol: <i>⏱ O me'yordagi o'qish vaqti: 1 daqiqa</i>
- Qisqa va lochin: Maksimum 2-3 ta ixcham abzas (jami 300-400 harfdan oshmasin).
- Mantiq va Xolislik: Aslo bir postda "o'rnatmang!", ikkinchi postda "o'rnating!" deb ziddiyatli yoki mantiqsiz vahima ko'tarib sun'iy emotsiyalarga berilmang. Muharrir sifatida xolis, muvozanatli va foydali ma'lumot bering (masalan: beta versiyaning imkoniyatlarini va xavfini xolis tushuntiring).
- Har safar BIR XIL "shokka tushdim", "maza qildim" kabi sun'iy va takroriy shablon iboralarni ISHLATMANG!
- Boshida aslo "H", "A" kabi ortiqcha adashgan harflar yoki bir xil salomlashuvlar ishlatmang.
- Tugatishda majburiy ravishda: <i>(Barchasini bilish uchun quyidagi tugmani bosing 👇)</i>

5. [BATAFSIL] qismi:
- Telegraph sahifasi uchun qadamma-qadam ko'rsatmalar va to'liq ma'lumotlar.

6. Format uchun faqat <b> va <i> html teglardan foydalaning. Yulduzcha (*) yoki Markdown umuman ishlatmang.

Asl matn:
{text}
"""
    try:
        model = genai.GenerativeModel(get_working_model())
        response = model.generate_content(prompt)
        try:
            translated = response.text.strip()
            # Boshdagi adashgan belgi yoki harflarni tozalash
            lines = translated.split('\n')
            cleaned_lines = []
            for line in lines:
                l_str = line.strip()
                # Agar [XABAR] dan keyin bitta alohida harf bo'lsa
                if len(l_str) == 1 and l_str.isalpha():
                    continue
                cleaned_lines.append(line)
            return '\n'.join(cleaned_lines)
        except ValueError:
            print("Gemini API: Kontent AI xavfsizlik filtriga tushdi yoki ruxsat etilmadi.")
            return "[FILTERED]"
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None

def generate_morning_lifehack():
    """Tongi xayrli tong po'sti uchun manbasiz generatsiya (AI o'zi o'ylaydi)."""
    if not GEMINI_API_KEY:
        return None
    
    prompt = """
    Siz Telegramdagi "Avtokanal" (yoki foydali layfxaklar) kanalining samimiy va do'stona adminisiz. Obunachilaringizga yaxshi kayfiyat ulashish obro'yingiz uchun juda muhim.
    
    Sizning vazifangiz:
    Roppa-rosa ertalab soat 07:00 uchun bitta bomba, sinalgan haqiqiy "layfxak" (hayotni yengillashtiruvchi maslahat yoxud maxfiy funksiya) o'ylab topish. Bu tarjima emas, o'zingiz bilgan mukammal texnologik fakt bo'lsin.
    
    Format:
    1. Albatta qiziqarli usulda Salomlashish bilan boshlang (Masalan: "Xayrli tong, qadrdonlar!", "Yangi kun muborak, texnomanlar!" h.k).
    2. Yana o'sha qoidalarga muvofiq, [XABAR] va [BATAFSIL] degan ikki qismga bo'ling.
    3. [XABAR] qismining MAVZUSI qalin HTML (<b></b>) bo'lsin, davomida ertalab ishga ketayotgan odamning kayfiyatini ko'taradigan do'stona gap jumlasi, sirlarga boy bitta fakt va o'zingizni Shaxsiy Fikringizni qisqa yozing. LEKIN "Keyingi safar", "Tez orada obzor qilaman" degan hech qanday va'da bermang! Matn 1000 belgidan oshmasin! Sirena(🚨) umuman ishlatmang. Tugatishda "<i>(Barchasini bilish yoxud o'rnatish uchun quyidagi tugmani bosing 👇)</i>" deb yozing.
    4. Sarlavhaning darhol ostiga kichkinagina kursiv qilib "<i>⏱ O'qish vaqti: 1 daqiqa</i>" deb yozing.
    5. [BATAFSIL] qismiga o'sha layfxakning qadamma qadam qanday yasalishini tushuntiring.
    6. Format uchun faqat <b> va <i> html ishlating. Hech qanday yulduzchalar yo'q.
    
    Shablon:
    [XABAR]
    ...
    [BATAFSIL]
    ...
    """
    try:
        model = genai.GenerativeModel(get_working_model())
        response = model.generate_content(prompt)
        text = response.text.strip().replace('**', '').replace('*', '')
        return text
    except Exception as e:
        print(f"Ertalabki layfxak xatosi: {e}")
        return None
