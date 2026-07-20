import traceback

try:
    print("Starting import...")
    import requests
    print("Imported requests.")
    import db
    print("Imported db.")
    
    print("\n--- TEST: LIFEHACKER RSS ---")
    r = requests.get('https://lifehacker.com/rss', timeout=5)
    print("RSS Length:", len(r.text))
    print("RSS Status:", r.status_code)
except Exception as e:
    print("ERROR:")
    traceback.print_exc()
