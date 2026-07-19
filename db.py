import json
import os
import threading

DB_FILE = "db.json"
_db_lock = threading.Lock()

def init_db():
    with _db_lock:
        if not os.path.exists(DB_FILE):
            default_data = {
                "donor_url": "https://lifehacker.com/rss",  # dunyodagi eng mashhur foydali maslahatlar sayti
                "last_scraped_id": "",
                "seen_ids": [],
                "queued_posts": []
            }
            _save_unlocked(default_data)

def _load_unlocked():
    if not os.path.exists(DB_FILE):
        return {"donor_url": "https://lifehacker.com/rss", "last_scraped_id": "", "seen_ids": [], "queued_posts": []}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_unlocked(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_donor_url():
    with _db_lock:
        return _load_unlocked().get("donor_url", "https://lifehacker.com/rss")

def set_donor_url(url):
    with _db_lock:
        data = _load_unlocked()
        data["donor_url"] = url
        data["last_scraped_id"] = ""  # yangi saytdan yangi postlarni eslab qolish uchun
        data["queued_posts"] = []     # eski navbatni tozalaymiz
        _save_unlocked(data)

def get_last_id():
    with _db_lock:
        return _load_unlocked().get("last_scraped_id", "")

def set_last_id(msg_id):
    with _db_lock:
        data = _load_unlocked()
        data["last_scraped_id"] = msg_id
        if "seen_ids" not in data:
            data["seen_ids"] = []
        if msg_id and msg_id not in data["seen_ids"]:
            data["seen_ids"].append(msg_id)
            # 50 tadan oshib ketmasligi uchun
            if len(data["seen_ids"]) > 50:
                data["seen_ids"] = data["seen_ids"][-50:]
        _save_unlocked(data)

def is_post_seen(post_id):
    with _db_lock:
        data = _load_unlocked()
        return post_id in data.get("seen_ids", [])

def add_queued_post(post_data):
    with _db_lock:
        data = _load_unlocked()
        data["queued_posts"].append(post_data)
        _save_unlocked(data)

def requeue_post(post_data):
    """
    Xatoga uchragan yoxud jo'natish xatolikka tushgan po'stni qayta o'qish uchun navbatning boshiga qo'shadi.
    """
    with _db_lock:
        data = _load_unlocked()
        data["queued_posts"].insert(0, post_data)
        _save_unlocked(data)

def get_next_post():
    with _db_lock:
        data = _load_unlocked()
        if data["queued_posts"]:
            post = data["queued_posts"].pop(0)
            _save_unlocked(data)
            return post
        return None

def get_queued_count():
    with _db_lock:
        return len(_load_unlocked().get("queued_posts", []))

def get_backup_data():
    """Bot zaxirasini bitta matn string ko'rinishida generatsiya qiladi."""
    with _db_lock:
        data = _load_unlocked()
        import base64
        import copy
        # Biz faqat last_scraped_id ni zaxiralashimiz muhim, queued posts yangitdan yuklanadi
        # Lekin tunda ishlab navbatga yig'ilganlarni ham saqlab qolish yaxshi!
        safe_data = copy.deepcopy(data)
        # Barchasini json qilib Base64 ga aylantiramiz, matn xato ketmasligi uchun
        encoded_bytes = base64.b64encode(json.dumps(safe_data).encode("utf-8"))
        return f"💾 #BACKUP_DATA\n{encoded_bytes.decode('utf-8')}"

def restore_backup(backup_string):
    """Base64 stringdan datani olib db.json ga yozadi."""
    try:
        lines = backup_string.split('\n')
        if len(lines) >= 2:
            base64_str = lines[1].strip()
            import base64
            decoded_bytes = base64.b64decode(base64_str)
            data = json.loads(decoded_bytes.decode("utf-8"))
            with _db_lock:
                _save_unlocked(data)
            return True
    except Exception as e:
        print(f"Xotirani tiklash xatosi: {e}")
    return False
