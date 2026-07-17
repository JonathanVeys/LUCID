import time
import requests
from datetime import datetime

URL = "https://lucid-6kv9.onrender.com/health"
INTERVAL = 600  

while True:
    try:
        r = requests.get(URL, timeout=120)
        print(f"{datetime.now():%H:%M:%S} - pinged, status {r.status_code}")
    except Exception as e:
        print(f"{datetime.now():%H:%M:%S} - ping failed: {e}")
    time.sleep(INTERVAL)