import requests
import time
import threading
import re
import hashlib
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- הגדרות מערכת ---
TOKEN = "8748416579:AAHLGyHreoktN10FSReH_nAUguVseDSli48"
CHAT_ID = "2405271"
RENDER_URL = "https://abu-rubi-bot-1.onrender.com"
FIRMS_KEY = "6228ccc298bd27845097cfe9995b3dfe"

# --- נבחרת הברזל ---
CHANNELS = [
    'Yair_Altman_channel14', 'US2020US', 'AlmogBoker', 
    'yosiyehoshua', 'HallelBittonRosen', 'arielidan14', 
    'noam_amir_news', 'Intellinews'
]

# --- מילות מפתח (מחולקות לפי דחיפות) ---
CRITICAL_KEYWORDS = [
    'פח"ע', 'פיגוע', 'שיגור', 'יציאה', 'טיל', 'רקטה', 
    'חדירה', 'פרש טורקי', 'קוד פגיון', 'יירוט', 'נפילה'
]
GENERAL_KEYWORDS = [
    'איראן', 'לבנון', 'דמשק', 'ביירות', 'טהרן', 'רצח', 'ירי'
]

processed_hashes = set()

class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Abu Rubi Master Engine is LIVE")
    def log_message(self, format, *args):
        pass

def get_israel_time():
    """מחזיר את הזמן המדויק בישראל (UTC+3 שעון קיץ)"""
    return datetime.utcnow() + timedelta(hours=3)

def send_telegram_alert(source, text, is_critical=False, is_disaster=False):
    """שליחת הדיווח בתבנית החדשות המחמירה"""
    dt_str = get_israel_time().strftime('%d/%m/%Y %H:%M')
    
    words = text.split()
    headline = " ".join(words[:6]) + "..." if len(words) > 6 else text
    continuous_text = " ".join(text.splitlines())
    
    icon = "🚨" if is_critical else "🌍" if is_disaster else "⚠️"
    msg = f"Verified\n{dt_str}\n\n**{icon} {headline}**\n\nמקור: {source}\n{continuous_text}"
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": msg, 
        "parse_mode": "Markdown",
        "disable_notification": not is_critical # התראה קולית רק באירועים קריטיים
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Send Error: {e}")

def check_disasters():
    """סריקת רעידות אדמה משמעותיות (>5.5)"""
    try:
        res = requests.get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson", timeout=10).json()
        if not res['features']: return
        
        for eq in res['features']:
            mag = eq['properties']['mag']
            place = eq['properties']['place']
            eq_id = eq['id']
            
            if mag and mag >= 5.5 and eq_id not in processed_hashes:
                processed_hashes.add(eq_id)
                alert_text = f"רעידת אדמה בעוצמה {mag} הורגשה באזור {place}. המערכות בודקות נתונים נוספים."
                send_telegram_alert("USGS Global", alert_text, is_critical=True, is_disaster=True)
    except:
        pass

def scrape_telegram_channels():
    """סורק את נבחרת הברזל"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    for channel in CHANNELS:
        try:
            url = f"https://t.me/s/{channel}"
            res = requests.get(url, headers=headers, timeout=10)
            msgs = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', res.text)
            
            for msg_html in msgs[-2:]: # סורק רק את ה-2 האחרונות למניעת עומס
                clean_text = re.sub(r'<[^>]+>', ' ', msg_html).strip()
                msg_hash = hashlib.md5(clean_text.encode('utf-8')).hexdigest()
                
                if msg_hash not in processed_hashes:
                    processed_hashes.add(msg_hash)
                    
                    is_critical = any(kw in clean_text for kw in CRITICAL_KEYWORDS)
                    is_general = any(kw in clean_text for kw in GENERAL_KEYWORDS)
                    
                    if is_critical or is_general:
                        send_telegram_alert(channel, clean_text, is_critical)
                        
        except:
            pass
        time.sleep(1)

def keep_alive():
    while True:
        try:
            requests.get(RENDER_URL, timeout=5)
        except:
            pass
        time.sleep(240)

if __name__ == "__main__":
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 8080), DummyServer).serve_forever(), daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    
    print("Master Engine Started. Monitoring Security & Disasters...")
    
    while True:
        scrape_telegram_channels()
        check_disasters()
        
        if len(processed_hashes) > 2000:
            processed_hashes.clear()
            
        time.sleep(30)
