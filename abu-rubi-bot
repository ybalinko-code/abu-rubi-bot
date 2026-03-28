import telebot
import requests
import feedparser
import time

# הגדרות הבוט - הטוקן החדש שלך
TOKEN = "8748416579:AAHLGyHreoktN10FSReH_nAUguVseDSli48"
# ה-ID של הערוץ Global Disaster
CHAT_ID = "-1002405271427" 

bot = telebot.TeleBot(TOKEN)

# זיכרון זמני למניעת כפילויות
sent_reports = set()

def check_disasters():
    print("סורק אירועים...")
    
    # 1. סריקת רעידות אדמה (USGS)
    try:
        earthquake_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.atom"
        feed = feedparser.parse(earthquake_url)
        for entry in feed.entries:
            if entry.id not in sent_reports:
                msg = f"🌍 **דיווח על רעידת אדמה**\n\n📍 מיקום: {entry.title}\n📅 זמן: {entry.updated}\n🔗 פרטים נוספים: {entry.link}"
                bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                sent_reports.add(entry.id)
    except Exception as e:
        print(f"שגיאה בסריקת רעידות אדמה: {e}")

    # 2. סריקת אסונות טבע כלליים (GDACS)
    try:
        gdacs_url = "https://www.gdacs.org/xml/rss.xml"
        feed = feedparser.parse(gdacs_url)
        for entry in feed.entries:
            if entry.id not in sent_reports:
                msg = f"⚠️ **התראה על אסון טבע בעולם**\n\n🚨 אירוע: {entry.title}\n🔗 לפרטים ב-Global Disaster: {entry.link}"
                bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                sent_reports.add(entry.id)
    except Exception as e:
        print(f"שגיאה בסריקת אסונות טבע: {e}")

# לולאת ריצה
if __name__ == "__main__":
    print("הבוט של אבו-רובי התחיל לעבוד!")
    while True:
        check_disasters()
        time.sleep(300)  # סריקה כל 5 דקות
