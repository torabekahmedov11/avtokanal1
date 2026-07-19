import db
import scraper
import ai_translator
import telegraph_api
from config import BOT_TOKEN, TARGET_CHANNEL_ID
import telebot

print("--- 1. DATABASE TESTING ---")
db.init_db()
print(f"Donor: {db.get_donor_url()}")
print(f"Last ID: {db.get_last_id()}")
print(f"Queued initial: {db.get_queued_count()}")

print("\n--- 2. SCRAPER TESTING ---")
posts = scraper.scrape_telegram_channel(db.get_donor_url(), db.get_last_id())
print(f"Found posts: {len(posts) if posts else 0}")
if posts:
    print(f"Sample Post ID: {posts[0]['id']}")

print("\n--- 3. AI TRANSLATOR TESTING ---")
test_text = "This is a lifehack about how to save battery on your phone by turning off background apps."
translated = ai_translator.translate_and_spice_up(test_text)
if translated:
    print("AI Translation: SUCCESS (length > 0)")
    print(f"Preview: {translated[:100]}...")
else:
    print("AI Translation: FAILED (Returned None/Empty)")

print("\n--- 4. TELEGRAPH TESTING ---")
url = telegraph_api.create_telegraph_page("Test", "<p>Hello</p>")
print(f"Telegraph URL: {url}")

print("\n--- 5. TELEGRAM BOT TESTING ---")
bot = telebot.TeleBot(BOT_TOKEN)
try:
    me = bot.get_me()
    print(f"Bot connected: @{me.username}")
    if TARGET_CHANNEL_ID:
        try:
            bot.send_message(TARGET_CHANNEL_ID, "🔧 Bot test tizimidan xabar!")
            print("Telegram Post: SUCCESS")
        except Exception as e:
            print(f"Telegram Post FAILED (Channel issue?): {e}")
except Exception as e:
    print(f"Bot get_me FAILED (Token issue?): {e}")
