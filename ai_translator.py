import google.generativeai as genai
from config import GEMINI_API_KEY

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

_working_model_name = None

def get_working_model():
    global _working_model_name
    if _working_model_name:
        return _working_model_name
        
    try:
        available = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                name = m.name.replace('models/', '')
                available.append(name)
        
        print(f"API kalitda mavjud modellar: {available}")
        
        preferred = [
            'gemini-3.5-flash', 'gemini-3.1-flash', 'gemini-3-flash',
            'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash',
            'gemini-3.1-pro', 'gemini-3-pro', 'gemini-2.5-pro',
            'gemini-2.0-pro', 'gemini-1.5-pro', 'gemini-1.0-pro', 
            'gemini-pro', 'gemini-pro-latest', 'gemini-flash-lite-latest'
        ]
        
        for pref in preferred:
            if pref in available:
                _working_model_name = pref
                print(f"Tanlangan model: {pref}")
                return pref
                
        # Agar ulardan hech biri bo'lmasa, eng standart 'flash' yoki 'pro' modelini qidiramiz
        for m in available:
            if 'flash' in m or 'pro' in m:
                # Maxsus tts, image, deep-research modellaridan qochamiz
                if not any(x in m for x in ['image', 'tts', 'deep-research', 'preview', 'customtools']):
                    _working_model_name = m
                    print(f"Zaxira sifatida tanlangan text model: {m}")
                    return m
                    
        if available:
            _working_model_name = available[0]
            return available[0]
            
    except Exception as e:
        print(f"Modellarni yuklashda xato (Fallback qo'llaniladi): {e}")
        
    _working_model_name = 'gemini-1.5-flash'
    return _working_model_name

def translate_and_spice_up(text):
    if not GEMINI_API_KEY:
        return f"AI_ERROR: Gemini API kaliti yo'q. Asl matn:\n\n{text}"
    
    prompt = f"""
Siz tajribali, O'zbekiston ahli orasida ommabop bo'lgan va "virusli" Telegram kanal administratorisiz. Siz matnlarni mutlaqo inson tilida, xuddi do'stingizga gapirib berayotgandek jonli, emotsional va qiziqarli qilib yozasiz.

Qat'iy Qoidalar (Sen'zura va O'zbekiston filtri):
1. Dastlab matnni o'qing. Agar matnda alkogol, qimor, 18+ (behayo) mavzular yoki islom diniga mutlaqo ziddiyatli bo'lgan g'oyalar bo'lsa, MUTLAQO HECH NIMA TARJIMA QILMANG! Bunday holatda faqat "[FILTERED]" deb qaytaring.
2. REKLAMA VA MAHALLIY LOKAL G'IYBAT: Tijoriy reklamalarni olib tashlang. Faqat AQShga xos yoki global qiziqishi yo'q mahalliy xabarlarni ham "[FILTERED]" qiling. Faqat texnologik va foydali / umumjahon hayotiy ma'lumotlarni tarjima qiling.

Tarjima va Formatlash Qoidalari (O'ta muhim!):
3. [XABAR] qismi (Kanal yuzi uchun): O'quvchi e'tiborini tortuvchi SARLAVHA bilan boshlang. Sarlavhani aslo "🚨" sirena kabi arzon emojilar bilan EMAS (umuman ishlatmang), balki HTML qalinligida (Masalan: <b>GOOGLE DRIVEDA XOTIRA TUGAYAPTIMI?</b>) deb e'lon qiling. Matnda rasmiy va zerikarli so'zlar ("ixlosmandlar", "ommalashgan" h.k) aslo ishlatmang. Qadrdon do'stlarga kofe ichib gapirib berayotgandek juda samimiy, erkin va oddiy tilda ("O'zimam bilmagandim", "Shokdaman") kabi o'zingizni shaxsiy fikringiz va reaksiyangiz bilan yozing. Matn faktlarni to'liq qamrab olgani qulay (maksimum 1000 ta harfdan oshmasin) bo'lsin.
4. O'qish vaqti: Sarlavhaning darhol ostiga kichkinagina kursiv qilib "<i>⏱ O'qish vaqti: 1 daqiqa</i>" deb yozing.
5. Til va tuzilma: Gapingiz shablon ("Mana tarjima") va sovuq bo'lmasin. Juda uzun jumlalarni kichik raqamlangan reyterlarga bo'ling.  
6. Muhokamaga chorlov: Matn tugagach obunachilarni muhokamaga chorlaydigan erkin savol so'rang (Masalan: "Siz qaysini ishlatgan bo'lardingiz? 👇"). Va eng oxirigagina 2-3 ta hashtag kiriting.
7. Formatlash (O'TA MUHIM!): Matn belgilarida qalin yoxud kursiv qilish uchun ASLO yulduzcha (*) yoki boshqa Markdown ishlata ko'rmang, o'rniga HTML teglardan (<b>, <i>) foydalaning.

Asl matn:
{text}
"""
    try:
        model = genai.GenerativeModel(get_working_model())
        response = model.generate_content(prompt)
        try:
            translated = response.text.strip()
            return translated
        except ValueError:
            print("Gemini API: Kontent AI xavfsizlik filtriga tushdi yoki ruxsat etilmadi.")
            return "[FILTERED]"
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return None
