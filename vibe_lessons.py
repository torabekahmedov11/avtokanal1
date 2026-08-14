"""
Vibe Coding Kunlik Darslik Moduli
=================================
Har kuni soat 20:00 da Vibe Coding haqida noldan boshlab tartibli darslik joylaydi.
Darslar hech qachon qaytarilmaydi — bot qaysi darsda turganini eslab boradi.
Har bir dars rasm, GIF yoki video bilan birga chiqadi.
"""
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import db
import ai_translator
import media_fetcher
from telegraph_api import create_telegraph_page
from config import TARGET_CHANNEL_ID, CHANNEL_LINK, OPENROUTER_API_KEY
import requests

# ============================================================
# DARSLAR KURSI — Noldan Professional Vibe Coderga!
# ============================================================
LESSON_CURRICULUM = [
    # === BOSQICH 1: Vibe Coding nima? (1-10) ===
    {
        "title": "Vibe Coding nima? Yangi davr dasturlash falsafasi",
        "topic": "vibe coding philosophy AI assisted programming future",
        "keywords": "vibe coding, AI, dasturlash, kelajak"
    },
    {
        "title": "AI yordamchi nima? ChatGPT, Claude, Gemini — farqi va kuchi",
        "topic": "ChatGPT Claude Gemini AI assistants comparison",
        "keywords": "ChatGPT, Claude, Gemini, AI yordamchi"
    },
    {
        "title": "Prompt nima? AI bilan to'g'ri gaplashish san'ati",
        "topic": "prompt engineering AI communication tips",
        "keywords": "prompt, AI, so'rov yozish"
    },
    {
        "title": "Cursor Editor — Vibe Coderning asosiy quroli",
        "topic": "Cursor IDE AI code editor features",
        "keywords": "Cursor, IDE, AI editor"
    },
    {
        "title": "Birinchi loyihangiz: AI bilan oddiy veb-sahifa yaratish",
        "topic": "first web project HTML CSS with AI help",
        "keywords": "veb-sahifa, HTML, birinchi loyiha"
    },
    {
        "title": "HTML va CSS — AI bilan tushunish va o'rganish",
        "topic": "HTML CSS basics learn with AI",
        "keywords": "HTML, CSS, dizayn"
    },
    {
        "title": "JavaScript asoslari — AI sizga qanday yordam beradi",
        "topic": "JavaScript basics AI assisted learning",
        "keywords": "JavaScript, dasturlash tili"
    },
    {
        "title": "Git va GitHub — Kodingizni saqlash va ulashish",
        "topic": "Git GitHub version control basics",
        "keywords": "Git, GitHub, versiya nazorati"
    },
    {
        "title": "Terminal va buyruqlar — Dasturchi sifatida yo'l boshlash",
        "topic": "terminal command line basics for developers",
        "keywords": "terminal, buyruqlar, CLI"
    },
    {
        "title": "Birinchi real loyiha: Shaxsiy portfolio sayt",
        "topic": "portfolio website project build with AI",
        "keywords": "portfolio, loyiha, veb-sayt"
    },
    # === BOSQICH 2: AI bilan real loyihalar (11-20) ===
    {
        "title": "API nima? Tashqi xizmatlar bilan ishlash",
        "topic": "API basics REST integration web services",
        "keywords": "API, REST, xizmatlar"
    },
    {
        "title": "Telegram Bot yaratish — noldan AI yordamida",
        "topic": "Telegram bot development Python AI",
        "keywords": "Telegram bot, Python"
    },
    {
        "title": "Ma'lumotlar bazasi (Database) tushunchasi",
        "topic": "database SQL NoSQL basics for beginners",
        "keywords": "database, SQL, ma'lumotlar bazasi"
    },
    {
        "title": "Python asoslari — AI bilan tez o'rganish",
        "topic": "Python programming basics AI learning",
        "keywords": "Python, dasturlash"
    },
    {
        "title": "Veb-scraping — internetdan ma'lumot yig'ish",
        "topic": "web scraping Python BeautifulSoup data",
        "keywords": "scraping, ma'lumot yig'ish"
    },
    {
        "title": "REST API yaratish — backend dunyosiga kirish",
        "topic": "REST API backend development Flask FastAPI",
        "keywords": "backend, API yaratish"
    },
    {
        "title": "Deploy qilish — loyihangizni internetga chiqarish",
        "topic": "deployment hosting Render Vercel cloud",
        "keywords": "deploy, hosting, bulut"
    },
    {
        "title": "Environment variables va xavfsizlik",
        "topic": "environment variables security secrets management",
        "keywords": "xavfsizlik, env, parollar"
    },
    {
        "title": "Debugging — xatolarni topish va tuzatish san'ati",
        "topic": "debugging techniques error fixing coding",
        "keywords": "debugging, xatolar, tuzatish"
    },
    {
        "title": "Real loyiha: Ob-havo bot yaratish",
        "topic": "weather bot project API Python Telegram",
        "keywords": "ob-havo bot, loyiha"
    },
    # === BOSQICH 3: Achchiq Haqiqatlar va Real Muammolar (21-30) ===
    {
        "title": "AI sizning o'rningizga o'ylamaydi — eng katta xatolik",
        "topic": "AI limitations critical thinking programming",
        "keywords": "AI cheklovlari, xatolik"
    },
    {
        "title": "Context Window limiti — nega kod 500 qatordan keyin sinadi",
        "topic": "context window limits AI coding large projects",
        "keywords": "context window, limit, katta loyiha"
    },
    {
        "title": "Kodni tushunmasdan nusxalash — kelajakdagi fojialar manbai",
        "topic": "copy paste coding dangers understanding code",
        "keywords": "nusxalash, tushunish, xatolik"
    },
    {
        "title": "Xavfsizlik: API kalitlarni ochiq qoldirish real oqibatlari",
        "topic": "API key security leak consequences real stories",
        "keywords": "xavfsizlik, API kalit, oqibatlar"
    },
    {
        "title": "AI gallyutsinatsiyasi — mavjud bo'lmagan kutubxonalar",
        "topic": "AI hallucination fake libraries packages",
        "keywords": "gallyutsinatsiya, soxta kutubxona"
    },
    {
        "title": "Arxitekturani AI bera olmaydi — rejalashtirish san'ati",
        "topic": "software architecture planning AI limitations design",
        "keywords": "arxitektura, rejalashtirish"
    },
    {
        "title": "Technical debt — tez yozilgan kodning narxi",
        "topic": "technical debt code quality refactoring",
        "keywords": "technical debt, kod sifati"
    },
    {
        "title": "Testing — nega test yozish vaqt tejalaydi",
        "topic": "unit testing importance software quality",
        "keywords": "test, sifat nazorati"
    },
    {
        "title": "Code Review — boshqalarning kodini o'qish mahorati",
        "topic": "code review best practices team coding",
        "keywords": "code review, jamoa"
    },
    {
        "title": "Freelance va ish topish — Vibe Coder sifatida daromad",
        "topic": "freelance developer income career vibe coding",
        "keywords": "freelance, daromad, karyera"
    },
    # === BOSQICH 4: Professional Darajaga Chiqish (31-40) ===
    {
        "title": "React/Next.js — zamonaviy frontend dunyosi",
        "topic": "React Next.js modern frontend development",
        "keywords": "React, frontend, zamonaviy"
    },
    {
        "title": "Docker — loyihangizni konteynerga solish",
        "topic": "Docker containers DevOps basics",
        "keywords": "Docker, konteyner, DevOps"
    },
    {
        "title": "CI/CD — avtomatik deploy tizimi",
        "topic": "CI CD continuous integration deployment automation",
        "keywords": "CI/CD, avtomatlashtirish"
    },
    {
        "title": "Serverless — serversiz arxitektura",
        "topic": "serverless computing cloud functions AWS Lambda",
        "keywords": "serverless, bulut funksiyalar"
    },
    {
        "title": "WebSocket va real-vaqt ilovalar",
        "topic": "WebSocket real-time applications chat",
        "keywords": "WebSocket, real-vaqt"
    },
    {
        "title": "OAuth va autentifikatsiya tizimlari",
        "topic": "OAuth authentication authorization security",
        "keywords": "OAuth, autentifikatsiya"
    },
    {
        "title": "AI Agent yaratish — o'z sun'iy aql yordamchingiz",
        "topic": "AI agent development autonomous coding assistant",
        "keywords": "AI agent, avtonom yordamchi"
    },
    {
        "title": "Prompt Engineering pro-darajada",
        "topic": "advanced prompt engineering techniques AI",
        "keywords": "prompt engineering, pro daraja"
    },
    {
        "title": "Microservices arxitekturasi",
        "topic": "microservices architecture distributed systems",
        "keywords": "microservices, taqsimlangan tizim"
    },
    {
        "title": "System Design asoslari",
        "topic": "system design scalability load balancing",
        "keywords": "system design, masshtablash"
    },
    # === BOSQICH 5: O'z Yo'lingni Top (41-50) ===
    {
        "title": "SaaS loyiha yaratish va monetizatsiya",
        "topic": "SaaS business model monetization startup",
        "keywords": "SaaS, biznes, daromad"
    },
    {
        "title": "Open Source dunyosiga kirish",
        "topic": "open source contribution GitHub community",
        "keywords": "open source, hamjamiyat"
    },
    {
        "title": "Mobile dastur yaratish (React Native/Flutter)",
        "topic": "mobile app development React Native Flutter",
        "keywords": "mobil dastur, Flutter"
    },
    {
        "title": "AI modellarni fine-tuning qilish",
        "topic": "AI model fine-tuning training custom models",
        "keywords": "AI fine-tuning, model o'rgatish"
    },
    {
        "title": "Startup texnik asosi — MVP yaratish",
        "topic": "MVP minimum viable product startup tech",
        "keywords": "MVP, startup, texnik asos"
    },
    {
        "title": "Jamoa bilan ishlash — Git branching strategiyalari",
        "topic": "Git branching strategies team collaboration",
        "keywords": "Git branching, jamoa"
    },
    {
        "title": "Performance optimization — tezlik san'ati",
        "topic": "performance optimization speed caching",
        "keywords": "tezlik, optimizatsiya"
    },
    {
        "title": "Monitoring va logging — ishlab turgan tizimni kuzatish",
        "topic": "monitoring logging observability production",
        "keywords": "monitoring, kuzatuv"
    },
    {
        "title": "Karyera yo'l xaritasi — junior dan senior gacha",
        "topic": "developer career path junior to senior growth",
        "keywords": "karyera, o'sish, senior"
    },
    {
        "title": "Vibe Coding manifesti — kelajak sizning qo'lingizda",
        "topic": "vibe coding manifesto future of programming AI",
        "keywords": "manifest, kelajak, yakuniy dars"
    },
]

# ============================================================
# AI DARS GENERATSIYA QILISH
# ============================================================
LESSON_SYSTEM_PROMPT = """Siz "Vibe Coding" harakati bo'yicha eng tajribali o'zbek IT-ustozisiz. Siz o'z shogirdlaringizga xuddi do'stingizga gapirgandek samimiy, jonli va qiziqarli tarzda dars berasiz.

Muhim qoidalar:
1. Hamma narsani NOLDAN, oddiy tilda tushuntiring — o'quvchi hech narsa bilmaydi deb hisoblang.
2. Har bir tushunchani REAL HAYOTIY MISOL bilan tushuntiring (masalan: "API — bu restoranda ofitsiantga buyurtma berish, ofitsiant esa oshxonaga yetkazadi").
3. Quruq, mashina tarjimasiga o'xshash matn YOZMANG. Xuddi jonli odam yozgandek bo'lsin.
4. Har bir darsda kamida 1 ta ACHCHIQ HAQIQAT yoki REAL TAJRIBA bo'lsin.
5. O'zbek IT-jargonlarni ishlatish ruhsatli (commit, push, deploy, bug, API kabi so'zlar).

Formatlash:
Matnni MAJBURAN 2 qismga ajrating:

[XABAR]
(Telegram post uchun: qisqa, o'tkir, 2-3 abzas.
Birinchi qator: dars raqami va sarlavha <b> tegida.
Oxiri: <i>(Darsni to'liq o'qish uchun quyidagi tugmani bosing 👇)</i>)

[BATAFSIL]
(Telegraph maqola uchun: to'liq dars matni, qadamma-qadam tushuntirish,
kod misollari, amaliy topshiriq yoki mashq. 800-1500 so'z.)

Faqat <b> va <i> HTML teglardan foydalaning. Markdown ishlatmang.
"""


def get_lesson_info(lesson_num):
    """Dars raqamiga mos mavzu ma'lumotlarini qaytaradi."""
    if lesson_num <= 0:
        lesson_num = 1
    
    if lesson_num <= len(LESSON_CURRICULUM):
        lesson = LESSON_CURRICULUM[lesson_num - 1]
        return lesson
    else:
        # 50-darsdan keyin AI kreativ rejimda yangi mavzu generatsiya qiladi
        return {
            "title": f"Vibe Coding ilg'or mavzu #{lesson_num}",
            "topic": "advanced vibe coding AI programming modern tech",
            "keywords": "ilg'or, yangi texnologiya"
        }


def generate_lesson_text(lesson_num, lesson_info):
    """OpenRouter AI orqali dars matnini generatsiya qiladi."""
    if not OPENROUTER_API_KEY:
        print("OPENROUTER_API_KEY yo'q! Darslik generatsiya qilib bo'lmaydi.")
        return None

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://telegram.org",
        "X-Title": "Vibe Coding Darslik Bot"
    }

    user_prompt = (
        f"Quyidagi mavzu bo'yicha {lesson_num}-DARS yozing:\n\n"
        f"Mavzu: {lesson_info['title']}\n"
        f"Kalit so'zlar: {lesson_info['keywords']}\n\n"
        f"Bu Vibe Coding kursining {lesson_num}-darsi. "
    )

    if lesson_num <= 10:
        user_prompt += "O'quvchi mutlaqo yangi boshlovchi — hamma narsani eng oddiy tilda tushuntiring."
    elif lesson_num <= 20:
        user_prompt += "O'quvchi asosiy tushunchalarni biladi — endi amaliy loyihalar orqali o'rgating."
    elif lesson_num <= 30:
        user_prompt += "O'quvchi tajribali — real muammolar, achchiq haqiqatlar va professional maslahatlar bering."
    elif lesson_num <= 40:
        user_prompt += "O'quvchi professional darajaga chiqmoqda — chuqur texnik bilimlar ulashing."
    else:
        user_prompt += "O'quvchi tajribali dasturchi — ilg'or mavzular va karyera bo'yicha maslahat bering."

    models = [
        "google/gemma-4-31b-it:free",
        "openrouter/free",
        "nvidia/nemotron-3.5-lightning:free",
    ]

    for model in models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": LESSON_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 3000
        }
        try:
            print(f"Dars #{lesson_num} generatsiya qilinmoqda ({model})...")
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200:
                res = r.json()
                if 'choices' in res and len(res['choices']) > 0:
                    content = res['choices'][0]['message']['content'].strip()
                    content = content.replace('**', '').replace('*', '')
                    print(f"OK: Dars #{lesson_num} matni generatsiya qilindi ({model})")
                    return content
            else:
                print(f"Model {model} javob: {r.status_code}")
        except Exception as e:
            print(f"Dars generatsiya xatosi ({model}): {e}")

    return None


# ============================================================
# ASOSIY FUNKSIYA — Kunlik darsni tayyorlab kanalga joylash
# ============================================================
def post_daily_lesson(bot: telebot.TeleBot):
    """
    Kunlik Vibe Coding darsini tayyorlab kanalga joylaydi.
    1. DB dan navbatdagi dars raqamini oladi
    2. AI orqali dars matnini generatsiya qiladi
    3. Avtomatik media (rasm/GIF/video) topadi
    4. Telegraph maqola yaratadi
    5. Telegram kanalga joylaydi
    6. Dars raqamini +1 qilib saqlaydi
    """
    if not TARGET_CHANNEL_ID or TARGET_CHANNEL_ID == "@sizning_kanalingiz":
        print("TARGET_CHANNEL_ID sozlanmagan! Darslik joylanmaydi.")
        return False

    # 1. Navbatdagi dars raqamini olish
    lesson_num = db.get_lesson_number() + 1
    lesson_info = get_lesson_info(lesson_num)
    
    print(f"\n{'='*50}")
    print(f"VIBE CODING DARSLIK #{lesson_num}: {lesson_info['title']}")
    print(f"{'='*50}")

    # 2. AI orqali dars matni generatsiya qilish
    lesson_text = generate_lesson_text(lesson_num, lesson_info)
    if not lesson_text:
        print(f"Dars #{lesson_num} matni generatsiya qilinmadi!")
        return False

    # 3. Matn va Telegrafni ajratish
    main_post, batafsil = ai_translator.parse_telegraph_response(lesson_text)
    
    if not main_post:
        main_post = lesson_text[:500]

    # 4. Shior qo'shish
    slogan = f"\n\n🔥 Vibe Coding sari har kuni bir qadam!\n👉 Kanalimiz: {CHANNEL_LINK}" if CHANNEL_LINK else "\n\n🔥 Vibe Coding sari har kuni bir qadam!"
    caption = main_post + slogan

    # 5. Telegraph maqola yaratish
    telegraph_url = None
    if batafsil:
        telegraph_url = create_telegraph_page(
            title=f"Vibe Coding | {lesson_num}-Dars: {lesson_info['title']}",
            html_content=batafsil
        )
        if telegraph_url:
            print(f"OK: Telegraph maqola yaratildi: {telegraph_url}")

    # 6. Tugmalar
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    if telegraph_url:
        buttons.append(InlineKeyboardButton("📖 Darsni to'liq o'qish", url=telegraph_url))
    if CHANNEL_LINK:
        ch_link = CHANNEL_LINK if CHANNEL_LINK.startswith("http") else f"https://t.me/{CHANNEL_LINK.replace('@', '')}"
        buttons.append(InlineKeyboardButton("➕ Obuna bo'lish", url=ch_link))
    if buttons:
        markup.add(*buttons)

    # 7. Media topish (rasm / GIF / video)
    media_stream, media_type, media_url = media_fetcher.get_lesson_media(
        lesson_info['topic'], lesson_num
    )

    # 8. Telegram caption chegarasi (media bilan 1024, matnsiz 4096)
    if media_stream and len(caption) > 1024:
        caption = caption[:1020] + "..."

    # 9. Kanalga joylash
    try:
        if media_stream and media_type == "photo":
            bot.send_photo(TARGET_CHANNEL_ID, media_stream, caption=caption, 
                          parse_mode="HTML", reply_markup=markup)
            print(f"OK: Dars #{lesson_num} RASM bilan kanalga joylandi!")
        
        elif media_stream and media_type == "animation":
            bot.send_animation(TARGET_CHANNEL_ID, media_stream, caption=caption,
                              parse_mode="HTML", reply_markup=markup)
            print(f"OK: Dars #{lesson_num} GIF bilan kanalga joylandi!")
        
        elif media_stream and media_type == "video":
            bot.send_video(TARGET_CHANNEL_ID, media_stream, caption=caption,
                          parse_mode="HTML", reply_markup=markup)
            print(f"OK: Dars #{lesson_num} VIDEO bilan kanalga joylandi!")
        
        else:
            # Media topilmagan bo'lsa — faqat matn
            bot.send_message(TARGET_CHANNEL_ID, caption, parse_mode="HTML", 
                           reply_markup=markup)
            print(f"OK: Dars #{lesson_num} faqat MATN bilan kanalga joylandi!")

    except Exception as e:
        print(f"Dars #{lesson_num} joylashda xatolik: {e}")
        # HTML xato bo'lsa oddiy matn bilan qayta urinish
        try:
            clean = caption.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
            bot.send_message(TARGET_CHANNEL_ID, clean, reply_markup=markup)
            print(f"OK: Dars #{lesson_num} oddiy matn bilan kanalga joylandi (fallback)")
        except Exception as e2:
            print(f"Dars #{lesson_num} umuman joylanmadi: {e2}")
            return False

    # 10. Dars raqamini saqlash — keyingi safar qaytarilmaydi!
    db.set_lesson_number(lesson_num)
    print(f"OK: Dars #{lesson_num} bazaga saqlandi. Keyingi dars: #{lesson_num + 1}")
    
    return True
