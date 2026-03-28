import telebot
import requests
import time
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = "8748416579:AAHLGyHreoktN10FSReH_nAUguVseDSli48"
CHAT_ID = "2405271"

bot = telebot.TeleBot(TOKEN)
last_disaster = None

def check_disasters():
    global last_disaster
    print("Sourcing disaster data...")
    try:
        response = requests.get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson", timeout=10)
        data = response.json()
        if data['features']:
            latest = data['features'][0]['properties']
            event_id = data['features'][0]['id']
            
            if event_id != last_disaster:
                last_disaster = event_id
                
                place = str(latest.get('place', ''))
                mag = float(latest.get('mag', 0.0))
                
                # מסנן העוצמה
                is_israel = "Israel" in place or "israel" in place.lower()
                
                if (is_israel and mag >= 4.0) or (not is_israel and mag >= 5.8):
                    msg = f"⚠️ התראת רעידת אדמה!\n\nמקום: {place}\nעוצמה: {mag}\nזמן: {time.ctime(latest['time']/1000)}"
                    bot.send_message(CHAT_ID, msg)
                else:
                    print(f"Filtered out (Too weak): {place} - Mag: {mag}")
    except Exception as e:
        print(f"Error: {e}")

@bot.message_handler(commands=['start', 'test'])
def send_welcome(message):
    bot.reply_to(message, "הבוט פעיל ומחובר אליך, אבו רובי! סריקת האסונות רצה ברקע ומוגדרת לפי מסנן עוצמות.")

def run_scanner():
    while True:
        check_disasters()
        time.sleep(300)

# שרת דמה עבור Render
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_scanner, daemon=True).start()
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("Bot is starting...")
    bot.infinity_polling()
