import json
import os

DB_FILE = "db.json"

def init_db():
    if not os.path.exists(DB_FILE):
        default_data = {
            "donor_url": "https://lifehacker.com/rss",  # dunyodagi eng mashhur foydali maslahatlar sayti
            "last_scraped_id": "",
            "queued_posts": []
        }
        _save(default_data)

def _load():
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_donor_url():
    return _load().get("donor_url", "https://lifehacker.com/rss")

def set_donor_url(url):
    data = _load()
    data["donor_url"] = url
    data["last_scraped_id"] = ""  # yangi saytdan yangi postlarni eslab qolish uchun
    data["queued_posts"] = []     # eski navbatni tozalaymiz
    _save(data)

def get_last_id():
    return _load().get("last_scraped_id", "")

def set_last_id(msg_id):
    data = _load()
    data["last_scraped_id"] = msg_id
    _save(data)

def add_queued_post(post_data):
    data = _load()
    data["queued_posts"].append(post_data)
    _save(data)

def get_next_post():
    data = _load()
    if data["queued_posts"]:
        post = data["queued_posts"].pop(0)
        _save(data)
        return post
    return None

def get_queued_count():
    return len(_load().get("queued_posts", []))
