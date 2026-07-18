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
            'gemini-3.1-flash', 'gemini-3.1-pro', 
            'gemini-3-flash', 'gemini-3-pro',
            'gemini-2.5-flash', 'gemini-2.5-pro',
            'gemini-2.0-flash', 'gemini-2.0-pro',
            'gemini-1.5-flash', 'gemini-1.5-pro',
            'gemini-1.0-pro', 'gemini-pro', 'gemini-pro-latest', 'gemini-flash-lite-latest'
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
Siz tajribali, o'zbek tilida yozuvchi, ommabop va "virusli" Telegram kanal administratorisiz.

Qat'iy Qoidalar (Sen'zura va Qadriyatlar):
1. Dastlab matnni o'qing. Agar matnda alkogol, qimor, 18+ (behayo) mavzular, islom diniga yoki O'zbek mentalitetiga ziddiyatli bo'lgan o'ta ochiq g'arbiy g'oyalar targ'ib qilingan bo'lsa, MUTLAQO HECH NIMA TARJIMA QILMANG! Bunday holatda faqat va faqat "[FILTERED]" degan so'zni qaytaring. Boshqa hech nima yozmang.

Tarjima Qoidalari (Agar kontent toza bo'lsa):
2. Rus yoki Ingliz tilidagi ushbu matnni o'zbek tiliga shunday qiziqarli tarjima qilingki, odamlar o'qib do'stlariga ulashgisi kelsin.
3. Sof va tabiiy o'zbek tilida (tushunarli, ko'cha jonli tiliga yaqin) yozing.
4. Kerakli joylarga qiziqarli emojilar qo'shing.
5. Agar matnda asl bashqa kanal manzili yoki nomaqbul ssilka bo'lsa, olib tashlang.
6. Hech qanday "Mana tarjima", "Quyida" kabi so'zlarni qo'shmang. Faqat tarjima qilingan post matnini o'zini bering.

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
