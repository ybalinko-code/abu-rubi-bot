import requests
import time
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# --- הגדרות גישה ---
TOKEN = "8748416579:AAHLGyHreoktN10FSReH_nAUguVseDSli48"
CHAT_ID = "2405271"

# משתני זיכרון למניעת כפילויות
last_usgs_id = None
processed_gdacs_events = []

# --- שרת Dummy עבור Render (פורט 8080) ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

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

# --- ניטור USGS (רעידות אדמה) ---
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
            event_time = time.ctime(latest['properties']['time'] / 1000)
            
            is_israel = "Israel" in place or "israel" in place.lower()
            
            # לוגיקת הסינון שלך
            if (is_israel and mag >= 4.0) or (not is_israel and mag >= 5.8):
                msg = f"🌍 **רעידת אדמה זוהתה**\n\n📍 מיקום: {place}\n📉 עוצמה: {mag}\n⏰ זמן: {event_time}"
                send_telegram(msg)
    except Exception as e:
        print(f"USGS Error: {e}")

# --- ניטור GDACS (סופות, צונאמי, הרי געש) ---
def check_gdacs():
    global processed_gdacs_events
    url = "https://www.gdacs.org/xml/rss.xml"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200: return
        
        root = ET.fromstring(res.content)
        ns = {'gdacs': 'http://www.gdacs.org'}
        
        for item in root.findall('.//item'):
            eid = item.find('guid').text
            etype = item.find('gdacs:eventtype', ns).text
            level = item.find('gdacs:level', ns).text
            
            if eid not in processed_gdacs_events:
                # רק רמות כתום/אדום וללא רעידות אדמה (כי USGS כבר מטפל בזה)
                if level in ['Orange', 'Red'] and etype != 'EQ':
                    title = item.find('title').text
                    link = item.find('link').text
                    
                    msg = f"⚠️ **התראת אסון (GDACS)**\n\n● סוג: {etype}\n● רמה: {level}\n● אירוע: {title}\n\n🔗 לפרטים: {link}"
                    send_telegram(msg)
                    
                    processed_gdacs_events.append(eid)
                    if len(processed_gdacs_events) > 50: processed_gdacs_events.pop(0)
    except Exception as e:
        print(f"GDACS Error: {e}")

# --- לולאה מרכזית ---
if __name__ == "__main__":
    # הפעלת שרת ה-Dummy בשרשור נפרד
    threading.Thread(target=run_server, daemon=True).start()
    print("Bot is running with Render Keep-Alive...")

    while True:
        check_usgs()
        check_gdacs()
        time.sleep(300) # סריקה כל 5 דקות
