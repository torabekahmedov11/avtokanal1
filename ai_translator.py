import google.generativeai as genai
from config import GEMINI_API_KEY

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

_working_model_name = None

def get_working_model():
    return 'gemini-2.5-flash-lite'

def translate_and_spice_up(text):
    if not GEMINI_API_KEY:
        return f"AI_ERROR: Gemini API kaliti yo'q. Asl matn:\n\n{text}"
    
    prompt = f"""
Siz tajribali, O'zbekiston ahli orasida ommabop bo'lgan va "virusli" Telegram kanal administratorisiz. Siz matnlarni mutlaqo inson tilida, xuddi do'stingizga gapirib berayotgandek jonli, emotsional va qiziqarli qilib yozasiz.

Qat'iy Qoidalar (Sen'zura va O'zbekiston filtri):
1. Dastlab matnni o'qing. Agar matnda alkogol, qimor, 18+ (behayo) mavzular yoki islom diniga mutlaqo ziddiyatli bo'lgan g'oyalar bo'lsa, MUTLAQO HECH NIMA TARJIMA QILMANG! Bunday holatda faqat "[FILTERED]" deb qaytaring.
2. REKLAMA VA MAHALLIY LOKAL G'IYBAT: Tijoriy reklamalarni olib tashlang. Faqat AQShga xos yoki global qiziqishi yo'q mahalliy xabarlarni ham "[FILTERED]" qiling. Faqat texnologik va foydali / umumjahon hayotiy ma'lumotlarni tarjima qiling.

Tarjima va Formatlash Qoidalari (O'ta muhim!):
3. Ikki qismga ajratish: Matnni majburiy ravishda aniq ikki qismga bo'lib bering. Boshlanishi `[XABAR]` degan yozuv bilan, pastki qismi (batafsil qo'llanma yoki maqola davomi) esa `[BATAFSIL]` degan yozuv bilan ajratilib chiqishi shart! Asl maqoladagi eng zo'r sirlar [BATAFSIL] ga yashirilsin.
4. [XABAR] qismi (Kanal yuzi uchun): O'quvchi e'tiborini tortuvchi SARLAVHA bilan boshlang. HTML qalinligida bo'lsin. Matnda rasmiy va zerikarli so'zlar ishlatilmang. Matn oxirida mutlaqo oldingiday **o'zingizning shaxsiy fikringiz** ni (masalan: "Men bu funksiyani ko'rib hayratda qoldim") bering.
LEKIN QAT'IY OGOHLANTIRISH: Shaxsiy fikr bildirayotganda aslo "Keyingi safar batafsil obzor qilaman", "Kuzatib boring", "Yaqinda yana gaplashamiz" kabi HECH QANDAY kelajakka oid quruq va'dalar bermang! Bor-yo'g'i reaksiyangizni yozing. Matn o'ta qisqa bo'lsin (max 600 harf). Tugatishda "<i>(Barchasini bilish uchun quyidagi tugmani bosing 👇)</i>" deb yozing.
5. O'qish vaqti: Sarlavhaning darhol ostiga kichkinagina kursiv qilib "<i>⏱ O'qish vaqti: 1 daqiqa</i>" deb yozing.
6. [BATAFSIL] qismi (Telegraph uchun): Aynan shu yerda har qanday qadamma-qadam qo'llanmalar, muammoni yechish tafsilotlari, uzoq ro'yxatlar va maqola davomi to'liq tushuntirilishi kerak. Telegraphga tushishini hisobga olib bemalol yozing (limit yo'q). Muhokamaga chorlov va hashtaglar ham faqat shu bo'limning eng oxirida bo'lsin.
7. Formatlash: Qalin yoxud kursiv qilish uchun ASLO yulduzcha (*) yoki Markdown ishlata ko'rmang, o'rniga HTML teglardan (<b>, <i>) foydalaning.

Sizning javobingiz strukturasi faqat shunday shaklda bo'lishi KAFOLATLANSIN:
[XABAR]
(bu yerda postingiz qisqa ta'rifi)

[BATAFSIL]
(bu yerda o'sha maqolaning to'liq sirlari va yechimlar)

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
