import requests
import time
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from datetime import datetime

# --- הגדרות גישה (TOKEN ו-ID שלך) ---
TOKEN = "8748416579:AAHLGyHreoktN10FSReH_nAUguVseDSli48"
CHAT_ID = "2405271"
FIRMS_KEY = "6228ccc298bd27845097cfe9995b3dfe"

# משתני זיכרון למניעת כפילויות
processed_ids = set()
last_usgs_id = None

# מילון תרגום מדינות לעברית (מנוע FIRMS)
COUNTRIES_HEB = {
    "GR": "יוון", "BR": "ברזיל", "TR": "טורקיה", "US": "ארה\"ב", "IT": "איטליה", 
    "ES": "ספרד", "IL": "ישראל", "LB": "לבנון", "SY": "סוריה", "EG": "מצרים", 
    "CY": "קפריסין", "JO": "ירדן", "UA": "אוקראינה", "RU": "רוסיה", "IR": "איראן"
}

# מילות מפתח לניטור ביטחוני ו-OSINT (Reuters, AP, BNO)
OSINT_KEYWORDS = [
    'shooting', 'explosion', 'blast', 'attack', 'terror', 'missile', 'airstrike', 
    'nuclear', 'hostage', 'assassination', 'killed', 'deadly', 'emergency', 
    'reconnaissance', 'refueling', 'squawk 7700', 'warship', 'deployment'
]

# --- שרת Dummy למניעת כיבוי ב-Render ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Abu Rubi OSINT System Online")

# --- פונקציית שליחה לטלגרם בפורמט Verified ---
def send_verified_msg(content):
    dt = datetime.now().strftime('%d/%m/%Y %H:%M')
    msg = f"Verified\n{dt}\n\n{content}"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": False}
    try:
        requests.post(url, json=payload, timeout=15)
    except:
        pass

# --- 1. ניטור רעידות אדמה (USGS) ---
def check_usgs():
    global last_usgs_id
    try:
        res = requests.get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson", timeout=10).json()
        if not res['features']: return
        latest = res['features'][0]
        eid = latest['id']
        if eid != last_usgs_id:
            last_usgs_id = eid
            p, m = latest['properties']['place'], latest['properties']['mag']
            if ("Israel" in p or "israel" in p.lower() and m >= 4.0) or (m >= 5.8):
                send_verified_msg(f"🌍 **רעידת אדמה משמעותית**\n📍 מיקום: {p}\n📉 עוצמה: {m}")
    except: pass

# --- 2. ניטור אסונות טבע (GDACS) ---
def check_gdacs():
    try:
        res = requests.get("https://www.gdacs.org/xml/rss.xml", timeout=10)
        root = ET.fromstring(res.content)
        ns = {'gdacs': 'http://www.gdacs.org'}
        for item in root.findall('.//item'):
            eid = item.find('guid').text
            if eid not in processed_ids:
                level = item.find('gdacs:level', ns).text
                etype = item.find('gdacs:eventtype', ns).text
                if level in ['Orange', 'Red'] and etype != 'EQ':
                    title = item.find('title').text
                    link = item.find('link').text
                    send_verified_msg(f"🚨 **התראת אסון גלובלית**\n● סוג: {etype}\n● רמה: {level}\n● אירוע: {title}\n🔗 [לפרטים]({link})")
                    processed_ids.add(eid)
    except: pass

# --- 3. ניטור שריפות ענק (NASA FIRMS) ---
def check_fires():
    url = f"https://firms.modaps.eosdis.nasa.gov/api/country/csv/{FIRMS_KEY}/VIIRS_SNPP_NRT/WLD/1"
    try:
        res = requests.get(url, timeout=20)
        lines = res.text.strip().split('\n')[1:]
        for line in lines:
            parts = line.split(',')
            c_code = parts[0]
            c_name = COUNTRIES_HEB.get(c_code, c_code)
            lat, lon, frp = parts[1], parts[2], float(parts[12])
            fid = f"fire_{lat}_{lon}"
            if fid not in processed_ids and frp > 220: # רף שריפות ענק
                zoom = f"https://zoom.earth/maps/satellite/#view={lat},{lon},14z"
                send_verified_msg(f"🔥 **שריפת ענק זוהתה (NASA)**\n🌍 מדינה: {c_name}\n🔥 עוצמה: {frp}\n🛰️ [לוויין חי]({zoom}) | 📍 [מפה](http://maps.google.com/?q={lat},{lon})")
                processed_ids.add(fid)
    except: pass

# --- 4. ניטור מבזקי ביטחון ו-OSINT (Reuters, AP, BNO) ---
def check_news_osint():
    feeds = [
        "https://bnonews.com/index.php/feed/",
        "https://www.reutersagency.com/feed/?best-types=world-news&post_type=best",
        "https://apnews.com/hub/world-news.rss"
    ]
    for url in feeds:
        try:
            res = requests.get(url, timeout=15)
            root = ET.fromstring(res.content)
            for item in root.findall('.//item'):
                title = item.find('title').text
                link = item.find('link').text
                if any(word in title.lower() for word in OSINT_KEYWORDS):
                    if link not in processed_ids:
                        send_verified_msg(f"📢 **מבזק ביטחוני / OSINT**\n{title}\n\n🔗 [למקור]({link})")
                        processed_ids.add(link)
        except: pass

# --- לולאת ניהול ---
if __name__ == "__main__":
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 8080), DummyServer).serve_forever(), daemon=True).start()
    print("Master OSINT Bot is starting...")
    while True:
        check_usgs()
        check_gdacs()
        check_fires()
        check_news_osint()
        if len(processed_ids) > 1500: processed_ids.clear()
        time.sleep(300) # סריקה כל 5 דקות
