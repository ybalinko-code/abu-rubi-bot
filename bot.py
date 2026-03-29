import requests
import time
import threading
import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- הגדרות מערכת ---
TOKEN = "8748416579:AAHLGyHreoktN10FSReH_nAUguVseDSli48"
CHAT_ID = "2405271"
RENDER_URL = "https://abu-rubi-bot-1.onrender.com"

# --- נבחרת הברזל ---
CHANNELS = [
    'Yair_Altman_channel14', 'US2020US', 'AlmogBoker', 
    'yosiyehoshua', 'HallelBittonRosen', 'arielidan14', 
    'noam_amir_news', 'Intellinews'
]

# --- מילות מפתח ---
KEYWORDS = [
    'שיגור', 'יציאה', 'טיל', 'רקטה', 'פח"ע', 'פיגוע', 
    'חדירה', 'פרש טורקי', 'פגיון', 'יירוט', 'נפילה', 
    'איראן', 'לבנון', 'דמשק', 'ביירות', 'טהרן', 'רצח', 'ירי'
]

processed_msgs = set()

class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Abu Rubi Pro Engine is LIVE")
    # העלמת לוגים של השרת כדי לשמור על טרמינל נקי
    def log_message(self, format, *args):
        pass

def send_telegram_alert(source, text):
    """שליחת הדיווח בתבנית החדשות המחמירה"""
    # תאריך האירוע
    event_date = datetime.now().strftime('%d/%m/%Y')
    
    # יצירת כותרת חדה (6 המילים הראשונות)
    words = text.split()
    headline = " ".join(words[:6]) + "..." if len(words) > 6 else text
    
    # טקסט עיתונאי רציף (מחיקת ירידות שורה ורשימות)
    continuous_text = " ".join(text.splitlines())
    
    # הרכבת ההודעה
    msg = f"Verified\n{event_date}\n\n**{headline}**\n\nמקור: {source}\n{continuous_text}"
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Send Error: {e}")

def scrape_telegram_channel(channel):
    """סורק את הערוץ הפתוח ושולף דיווחים אחרונים"""
    url = f"https://t.me/s/{channel}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=10)
        
        # זיהוי בלוקים של טקסט בתוך ה-HTML של טלגרם
        msgs = re.findall(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', res.text)
        
        # בדיקת 3 ההודעות האחרונות בערוץ
        for msg_html in msgs[-3:]:
            # ניקוי תגיות HTML
            clean_text = re.sub(r'<[^>]+>', ' ', msg_html).strip()
            
            # יצירת מזהה ייחודי להודעה כדי למנוע כפילויות
            msg_hash = hash(clean_text)
            if msg_hash not in processed_msgs:
                processed_msgs.add(msg_hash)
                
                # בדיקה אם אחת ממילות המפתח קיימת בדיווח
                if any(kw in clean_text for kw in KEYWORDS):
                    send_telegram_alert(channel, clean_text)
                    print(f"[!] Alert Sent from {channel}")
                    
    except Exception as e:
        pass # התעלמות משגיאות רשת זמניות כדי שהלולאה לא תקרוס

def keep_alive():
    """פינג עצמי למניעת כיבוי ב-Render"""
    while True:
        try:
            requests.get(RENDER_URL, timeout=5)
        except:
            pass
        time.sleep(240) # כל 4 דקות

if __name__ == "__main__":
    # 1. הדלקת שרת ה-Dummy ל-Render
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 8080), DummyServer).serve_forever(), daemon=True).start()
    
    # 2. הדלקת מנגנון השרידות
    threading.Thread(target=keep_alive, daemon=True).start()
    
    print("Abu Rubi Pro Engine Started. Monitoring channels...")
    
    # 3. לולאת הניטור הראשית
    while True:
        for channel in CHANNELS:
            scrape_telegram_channel(channel)
            time.sleep(2) # השהייה קטנה בין ערוץ לערוץ כדי לא להיחסם
        
        # ניקוי זיכרון למניעת קריסה ארוכת טווח
        if len(processed_msgs) > 1000:
            processed_msgs.clear()
            
        time.sleep(30) # המתנה לפני סבב סריקה חדש
