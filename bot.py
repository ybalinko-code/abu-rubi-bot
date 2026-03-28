import requests
import time
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# --- הגדרות גישה (אל תשנה את הטוקן וה-ID) ---
TOKEN = "8748416579:AAHLGyHreoktN10FSReH_nAUguVseDSli48"
CHAT_ID = "2405271"

# משתני זיכרון למניעת כפילויות
last_usgs_id = None
processed_gdacs_events = []
processed_news_ids = []

# --- תשתית שרת Dummy (Keep-Alive ל-Render) ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Global Disaster Bot is Operational")
    def do_HEAD(self): # פתרון לשגיאת ה-501 שראינו בלוגים
        self.send_response(200)
        self.end_headers()

def run_server():
    server = HTTPServer(('0.0.0.0', 8080), DummyServer)
    server.serve_forever()

# --- פונקציית שליחה לטלגרם ---
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

# --- חיישן 1: רעידות אדמה (USGS) ---
def check_usgs():
    global last_usgs_id
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if not data['features']: return
        latest = data['features'][0]
        event_id = latest['id']
        if event_id != last_usgs_id:
            last_usgs_id = event_id
            place = latest['properties']['place'] or ""
            mag = latest['properties']['mag'] or 0.0
            is_israel = "Israel" in place or "israel" in place.lower()
            if (is_israel and mag >= 4.0) or (not is_israel and mag >= 5.8):
                msg = f"🌍 **רעידת אדמה זוהתה**\n\n📍 מיקום: {place}\n📉 עוצמה: {mag}"
                send_telegram(msg)
    except Exception as e: print(f"USGS Error: {e}")

# --- חיישן 2: אסונות עולם (GDACS) ---
def check_gdacs():
    global processed_gdacs_events
    try:
        res = requests.get("https://www.gdacs.org/xml/rss.xml", timeout=10)
        if res.status_code != 200: return
        root = ET.fromstring(res.content)
        ns = {'gdacs': 'http://www.gdacs.org'}
        for item in root.findall('.//item'):
            eid = item.find('guid').text
            level = item.find('gdacs:level', ns).text
            etype = item.find('gdacs:eventtype', ns).text
            if eid not in processed_gdacs_events:
                if level in ['Orange', 'Red'] and etype != 'EQ':
                    title = item.find('title').text
                    link = item.find('link').text
                    msg = f"🚨 **התראת אסון (GDACS)**\n\n● סוג: {etype}\n● רמה: {level}\n● אירוע: {title}\n\n🔗 לפרטים: {link}"
                    send_telegram(msg)
                    processed_gdacs_events.append(eid)
                    if len(processed_gdacs_events) > 50: processed_gdacs_events.pop(0)
    except Exception as e: print(f"GDACS Error: {e}")

# --- חיישן 3: חדשות אסטרטגיות (FBI & World News) ---
def check_strategic_news():
    global processed_news_ids
    feeds = [
        "https://www.fbi.gov/news/pressrel/press-releases/rss.xml",
        "https://www.reutersagency.com/feed/?best-topics=world-news&post_type=best"
    ]
    critical_keywords = ["Sanctions", "Explosion", "Attack", "Cyber", "Emergency", "Nuclear", "Military", "Oil", "Border"]
    for url in feeds:
        try:
            res = requests.get(url, timeout=10)
            root = ET.fromstring(res.content)
            for item in root.findall('.//item'):
                guid = item.find('guid').text if item.find('guid') is not None else item.find('link').text
                title = item.find('title').text
                if guid not in processed_news_ids:
                    if any(key.lower() in title.lower() for key in critical_keywords):
                        link = item.find('link').text
                        msg = f"📡 **עדכון אסטרטגי גולמי**\n\n● {title}\n\n🔗 מקור: {link}"
                        send_telegram(msg)
                        processed_news_ids.append(guid)
                        if len(processed_news_ids) > 100: processed_news_ids.pop(0)
        except Exception as e: print(f"News Sensor Error: {e}")

# --- לולאת הרצה מרכזית ---
if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    print("All Sensors Active. Monitoring...")
    while True:
        try:
            check_usgs()
            check_gdacs()
            check_strategic_news()
            time.sleep(300) # סריקה כל 5 דקות
        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(60)
