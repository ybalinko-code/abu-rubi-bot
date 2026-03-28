import requests
import time
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# --- הגדרות גישה ---
TOKEN = "8748416579:AAHLGyHreoktN10FSReH_nAUguVseDSli48"
CHAT_ID = "2405271"
FIRMS_KEY = "6228ccc298bd27845097cfe9995b3dfe"

# משתני זיכרון למניעת כפילויות
last_usgs_id = None
processed_gdacs_events = []
processed_fires = set()

# --- שרת Dummy עבור Render (פורט 8080) ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Global Disaster Bot is active")

def run_server():
    server = HTTPServer(('0.0.0.0', 8080), DummyServer)
    server.serve_forever()

# --- פונקציית שליחה לטלגרם ---
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": False}
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Telegram Error: {e}")

# --- ניטור USGS (רעידות אדמה) ---
def check_usgs():
    global last_usgs_id
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if not data['features']: return
        latest = data['features'][0]
        if latest['id'] != last_usgs_id:
            last_usgs_id = latest['id']
            place, mag = latest['properties']['place'], latest['properties']['mag']
            is_israel = "Israel" in place or "israel" in place.lower()
            if (is_israel and mag >= 4.0) or (not is_israel and mag >= 5.8):
                msg = f"🌍 **רעידת אדמה זוהתה**\n\n📍 מיקום: {place}\n📉 עוצמה: {mag}"
                send_telegram(msg)
    except: pass

# --- ניטור GDACS (צונאמי, סופות, הרי געש) ---
def check_gdacs():
    global processed_gdacs_events
    try:
        res = requests.get("https://www.gdacs.org/xml/rss.xml", timeout=10)
        root = ET.fromstring(res.content)
        ns = {'gdacs': 'http://www.gdacs.org'}
        for item in root.findall('.//item'):
            eid = item.find('guid').text
            if eid not in processed_gdacs_events:
                level = item.find('gdacs:level', ns).text
                etype = item.find('gdacs:eventtype', ns).text
                if level in ['Orange', 'Red'] and etype != 'EQ':
                    title = item.find('title').text
                    link = item.find('link').text
                    msg = f"🚨 **התראת אסון (GDACS)**\n\n● סוג: {etype}\n● רמה: {level}\n● אירוע: {title}\n\n🔗 [לפרטים]({link})"
                    send_telegram(msg)
                    processed_gdacs_events.append(eid)
                    if len(processed_gdacs_events) > 50: processed_gdacs_events.pop(0)
    except: pass

# --- ניטור FIRMS (שריפות יער משמעותיות) ---
def check_fires():
    global processed_fires
    # סריקה של שריפות ב-24 שעות האחרונות (לוויין VIIRS SNPP)
    url = f"https://firms.modaps.eosdis.nasa.gov/api/country/csv/{FIRMS_KEY}/VIIRS_SNPP_NRT/WLD/1"
    try:
        res = requests.get(url, timeout=20)
        lines = res.text.strip().split('\n')[1:]
        for line in lines:
            parts = line.split(',')
            lat, lon = parts[1], parts[2]
            frp = float(parts[12]) # עוצמה תרמית
            fire_id = f"{lat}_{lon}"
            
            # דיווח רק על שריפות חזקות מאוד (FRP > 150) למניעת הצפה
            if fire_id not in processed_fires and frp > 150:
                msg = f"🔥 **שריפת ענק זוהתה (NASA)**\n\n● עוצמה תרמית: {frp}\n● מיקום: {lat}, {lon}\n\n📍 [צפייה במפה](https://www.google.com/maps?q={lat},{lon})"
                send_telegram(msg)
                processed_fires.add(fire_id)
                if len(processed_fires) > 200: processed_fires.clear()
    except: pass

# --- לולאה מרכזית ---
if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    print("Bot is starting with NASA FIRMS integration...")
    while True:
        try:
            check_usgs()
            check_gdacs()
            check_fires()
            time.sleep(300) # סריקה כל 5 דקות
        except Exception as e:
            print(f"Main Loop Error: {e}")
            time.sleep(60)
