import requests
import time
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from datetime import datetime, timedelta

# --- הגדרות גישה ---
TOKEN = "8748416579:AAHLGyHreoktN10FSReH_nAUguVseDSli48"
CHAT_ID = "2405271"
FIRMS_KEY = "6228ccc298bd27845097cfe9995b3dfe"

processed_ids = set()
last_update_id = 0

COUNTRIES_HEB = {"GR": "יוון", "BR": "ברזיל", "TR": "טורקיה", "US": "ארה\"ב", "IL": "ישראל", "UA": "אוקראינה", "RU": "רוסיה", "IR": "איראן", "SY": "סוריה", "LB": "לבנון"}
OSINT_KEYWORDS = ['shooting', 'explosion', 'blast', 'attack', 'terror', 'missile', 'airstrike', 'nuclear', 'hostage', 'assassination', 'killed', 'emergency', 'squawk 7700']

class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Abu Rubi Master OSINT Bot Active")

def send_verified_msg(content):
    # תיקון לשעון ישראל (UTC+3)
    dt = (datetime.utcnow() + timedelta(hours=3)).strftime('%d/%m/%Y %H:%M')
    msg = f"Verified\n{dt}\n\n{content}"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=15)
    except: pass

def check_commands():
    global last_update_id
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}"
    try:
        res = requests.get(url, timeout=10).json()
        for update in res.get("result", []):
            last_update_id = update["update_id"]
            if "message" in update and "text" in update["message"]:
                if update["message"]["text"] == "/test":
                    send_verified_msg("🚀 **בדיקת מערכת אבו רובי**\n\nהמערכת פעילה ומנטרת:\n✅ NASA (שריפות)\n✅ USGS (רעידות)\n✅ OSINT (מבזקים)\n⏰ שעון ישראל תוקן!")
    except: pass

def check_usgs():
    try:
        res = requests.get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson", timeout=10).json()
        if not res['features']: return
        latest = res['features'][0]
        if (latest['properties']['mag'] >= 5.8):
            send_verified_msg(f"🌍 **רעידת אדמה משמעותית**\n📍 מיקום: {latest['properties']['place']}\n📉 עוצמה: {latest['properties']['mag']}")
    except: pass

def check_fires():
    url = f"https://firms.modaps.eosdis.nasa.gov/api/country/csv/{FIRMS_KEY}/VIIRS_SNPP_NRT/WLD/1"
    try:
        res = requests.get(url, timeout=20)
        lines = res.text.strip().split('\n')[1:]
        for line in lines:
            parts = line.split(',')
            lat, lon, frp = parts[1], parts[2], float(parts[12])
            fid = f"fire_{lat}_{lon}"
            if fid not in processed_ids and frp > 220:
                c_name = COUNTRIES_HEB.get(parts[0], parts[0])
                zoom = f"https://zoom.earth/maps/satellite/#view={lat},{lon},14z"
                send_verified_msg(f"🔥 **שריפת ענק זוהתה (NASA)**\n🌍 מדינה: {c_name}\n🔥 עוצמה: {frp}\n🛰️ [לוויין חי]({zoom})")
                processed_ids.add(fid)
    except: pass

def check_news_osint():
    feeds = ["https://bnonews.com/index.php/feed/", "https://www.reutersagency.com/feed/"]
    for url in feeds:
        try:
            res = requests.get(url, timeout=15)
            root = ET.fromstring(res.content)
            for item in root.findall('.//item'):
                title, link = item.find('title').text, item.find('link').text
                if any(word in title.lower() for word in OSINT_KEYWORDS) and link not in processed_ids:
                    send_verified_msg(f"📢 **מבזק ביטחוני / OSINT**\n{title}\n\n🔗 [מקור]({link})")
                    processed_ids.add(link)
        except: pass

if __name__ == "__main__":
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 8080), DummyServer).serve_forever(), daemon=True).start()
    while True:
        check_commands()
        check_usgs()
        check_fires()
        check_news_osint()
        if len(processed_ids) > 1000: processed_ids.clear()
        time.sleep(60)
