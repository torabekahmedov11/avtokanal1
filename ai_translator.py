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
2. REKLAMA FILTRI: Agar matn butunlay Amazon, AliExpress va shunga o'xshash saytlar tovarini sotishga (deal, sale, promo, discount) qaratilgan tijoriy maqola bo'lsa uni O'TKAZIB YUBORING va faqat "[FILTERED]" deb qaytaring. Matn orasida biron ashyo reklamasi bo'lsa, reklamani o'chirib, qolgan dolzarb qismini oling.
3. JOYLASHUV FILTRI (O'ta muhim): Agar ushbu matn AQSh, Yevropa, yoki chet eldagi qandaydir juda lokal g'iybat, Amerika siyosati yoki faqat amerikaliklarga kerakli (masalan qanaqadir shtatdagi do'kon yopilishi) voqea bo'lsa, buni O'zbekistondagi foydalanuvchi umuman tushunmaydi va qiziqmaydi. Bunday postlarni bloklang va "[FILTERED]" deb qaytaring! Foydalanuvchilarga Global (dunyoviy) texnologiyalar, universal layfxaklar yoki O'zbek mintaqasi tushunadigan mavzularnigina saralab tarjima qiling.

Tarjima Qoidalari:
4. Matnni xuddi haqiqiy inson (kanal egasi) yozgandek, shablonlarsiz va mexanik tarjima hidisiz yozing. Tabiiy, hayotiy va birmuncha interaktiv (obunachilar bilan gaplashayotgandek) leksikadan foydalaning.
5. Agar matn yoki o'rgatilayotgan layfxak rostdan ham o'ta qiziqarli yoki foydali bo'lsa, post tagidan o'zingizning qisqacha mualliflik (shaxsiy) fikringizni hajviy yoki ta'sirli qilib qo'shib qo'ying (Masalan: "P.S. O'zim ham buni sinab ko'rmoqchiman...").
6. Kerakli joylarga yoshlarbop va qiziqarli emojilar qo'shing.
7. O'zingizdan "Mana tarjima", "Quyida", "Mana" kabi robotona so'zlarni qo'shmang. Faqat tarjima qilingan tayyor "shumtaka" post matnini bering.

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
