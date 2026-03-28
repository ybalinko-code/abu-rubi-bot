import telebot
import requests
import time
import threading

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
                msg = f"⚠️ התראת רעידת אדמה!\n\nמקום: {latest['place']}\nעוצמה: {latest['mag']}\nזמן: {time.ctime(latest['time']/1000)}"
                bot.send_message(CHAT_ID, msg)
    except Exception as e:
        print(f"Error: {e}")

@bot.message_handler(commands=['start', 'test'])
def send_welcome(message):
    bot.reply_to(message, "הבוט פעיל ומחובר אליך, אבו רובי! סריקת האסונות רצה ברקע.")

def run_scanner():
    while True:
        check_disasters()
        time.sleep(300)

if __name__ == "__main__":
    threading.Thread(target=run_scanner, daemon=True).start()
    print("Bot is starting...")
    bot.infinity_polling()
