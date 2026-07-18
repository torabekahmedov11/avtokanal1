import google.generativeai as genai
from config import GEMINI_API_KEY

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Use gemini-1.5-flash since it's the fastest and available in the free tier
# For backward compatibility, maybe gemini-1.0-pro or gemini-pro is safer if 1.5 is constrained, 
# but 1.5-flash is currently default on AI studio. Let's use gemini-1.5-flash.
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    pass # will be handled on usage

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
