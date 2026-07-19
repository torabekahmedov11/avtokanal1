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
3. Ikki qismga ajratish: Matnni majburiy ravishda aniq ikki qismga bo'lib bering. Boshlanishi `[XABAR]` degan yozuv bilan, pastki qismi (batafsil izoh/qo'llanma) esa `[KOMMENT]` degan yozuv bilan ajratilib chiqishi shart! Agar ixcham matn bo'lsa ham shu qoidaga amal qilingiz.
4. [XABAR] qismi (Kanal yuzi uchun): O'quvchi e'tiborini "tortib oluvchi" MAVZU SARLAVHASI bilan boshlang. Sarlavhani (Masalan: 🚨 <b>GOOGLE DRIVE XOTIRA TUGAYAPTIMI?</b>) HTML b tagida qalinlashtiring. Bu qismda asosiy muammo tushuntirilishi kerak. Asosiy maqsad o'quvchini qiziqtirib izohdagi davomini o'qishiga chorlash bo'lsin. Juda qisqa va qiziqarli (max 600 harf). Tugatishda "<i>(Batafsil ma'lumot izohda 👇)</i>" deb yozib qo'ying.
5. O'qish vaqti: Sarlavhaning darhol ostiga kichkinagina kursiv qilib "<i>⏱ O'qish vaqti: 1 daqiqa</i>" deb yozing.
6. [KOMMENT] qismi (Izohlar qutisi uchun): Aynan shu yerda har qanday qadamma-qadam qo'llanmalar teksti, uzoq ro'yxatlar va faktlar to'liq yozilishi kerak.
7. Izohga (kommentga) so'rov: [KOMMENT] matni tugagach obunachilarni muhokamaga chorlaydigan savol so'rang (Masalan: "Siz telefoningizda qaysi funksiyalarni ishlatasiz? Izohlarda yozing 👇"). Va eng oxirigagina 2-3 ta hashtag (Masalan: #layfxak #android) kiriting.
8. Formatlash (O'TA MUHIM!): Matn belgilarida qalin yoxud kursiv qilish uchun ASLO yulduzcha (*) yoki boshqa Markdown ishlata ko'rmang, o'rniga HTML teglardan (<b>, <i>) foydalaning.

Sizning javobingiz strukturasi faqat shunday shaklda bo'lishi KAFOLATLANSIN:
[XABAR]
...
[KOMMENT]
...

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
