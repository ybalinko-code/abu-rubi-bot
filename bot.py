import requests
import time
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from datetime import datetime

# --- הגדרות גישה ---
TOKEN = "8748416579:AAHLGyHreoktN10FSReH_nAUguVseDSli48"
CHAT_ID = "2405271"
FIRMS_KEY = "6228ccc298bd27845097cfe9995b3dfe"

processed_gdacs_events = []
processed_fires = set()
last_usgs_id = None

class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Global Disaster Bot Active")

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=15)
    except: pass

def check_usgs():
    global last_usgs_id
    try:
        data = requests.get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson", timeout=10).json()
        if not data['features']: return
        latest = data['features'][0]
        if latest['id'] != last_usgs_id:
            last_usgs_id = latest['id']
            place, mag = latest['properties']['place'], latest['properties']['mag']
            dt = datetime.fromtimestamp(latest['properties']['time']/1000).strftime('%d/%m/%Y %H:%M')
            is_israel = "Israel" in place or "israel" in place.lower()
            if (is_israel and mag >= 4.0) or (not is_israel and mag >= 5.8):
                send_telegram(f"🌍 **רעידת אדמה זוהתה**\n\n📍 מיקום: {place}\n📉 עוצמה: {mag}\n⏰ זמן: {dt}")
    except: pass

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
                    dt = datetime.now().strftime('%d/%m/%Y %H:%M')
                    msg = f"🚨 **התראת אסון (GDACS)**\n\n● סוג: {etype}\n● רמה: {level}\n● אירוע: {item.find('title').text}\n⏰ זמן: {dt}\n🔗 [לפרטים]({item.find('link').text})"
                    send_telegram(msg)
                    processed_gdacs_events.append(eid)
                    if len(processed_gdacs_events) > 50: processed_gdacs_events.pop(0)
    except: pass

def check_fires():
    global processed_fires
    # שימוש ב-API של FIRMS שכולל מדינות (Country CSV)
    url = f"https://firms.modaps.eosdis.nasa.gov/api/country/csv/{FIRMS_KEY}/VIIRS_SNPP_NRT/WLD/1"
    try:
        res = requests.get(url, timeout=20)
        lines = res.text.strip().split('\n')[1:]
        for line in lines:
            parts = line.split(',')
            country_code = parts[0]
            lat, lon = parts[1], parts[2]
            frp = float(parts[12])
            fire_id = f"{lat}_{lon}"
            
            if fire_id not in processed_fires and frp > 200: # רף עוצמה גבוה לשריפות ענק
                dt = datetime.now().strftime('%d/%m/%Y %H:%M')
                # קישור ללוויין חי (Zoom Earth)
                zoom_link = f"https://zoom.earth/maps/satellite/#view={lat},{lon},14z"
                
                msg = (f"🔥 **שריפת ענק זוהתה (NASA)**\n\n"
                       f"🌍 מדינה: {country_code}\n"
                       f"🔥 עוצמה תרמית: {frp}\n"
                       f"⏰ זמן זיהוי: {dt}\n\n"
                       f"🛰️ [צפייה בלוויין חי]({zoom_link})\n"
                       f"📍 [מיקום במפה](http://maps.google.com/?q={lat},{lon})")
                
                send_telegram(msg)
                processed_fires.add(fire_id)
                if len(processed_fires) > 200: processed_fires.clear()
    except: pass

if __name__ == "__main__":
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 8080), DummyServer).serve_forever(), daemon=True).start()
    while True:
        check_usgs()
        check_gdacs()
        check_fires()
        time.sleep(300)
