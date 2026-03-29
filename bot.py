import os
import html
import threading
import time
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# ==========================================
# 1. שרת Web מינימלי למניעת קריסה ב-Render
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Abu Rubi Bot Engine is LIVE and running."

def run_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# 2. מסד נתונים פנימי - נבחרת המקורות
# ==========================================
SOURCE_MAPPING = {
    "arielidan14": "אריאל עידן",
    "Intellinews": "אינטליניוז",
    "US2020US": "עמיחי שטיין",
    "HallelBittonRosen": "הלל ביטון רוזן",
    "AlmogBoker": "אלמוג בוקר",
    "yosiyehoshua": "יוסי יהושוע",
    "noam_amir_news": "נועם אמיר",
    "Yair_Altman_channel14": "יאיר אלטמן"
}

# זיכרון קצר למניעת כפילויות (Deduplication)
recent_messages = []

# ==========================================
# 3. מנוע עיבוד ההודעות
# ==========================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global recent_messages
    try:
        # שליפת ההודעה (מתעלות או קבוצות)
        message = update.channel_post or update.message
        if not message or not message.text:
            return

        raw_text = message.text
        chat_username = message.chat.username if message.chat else "Unknown"

        # א. מניעת הצפה: בדיקה אם הודעה זהה נשלחה ב-3 הדקות האחרונות
        current_time = time.time()
        recent_messages = [m for m in recent_messages if current_time - m['time'] < 180] # מנקה היסטוריה ישנה
        
        text_signature = raw_text[:30] # לוקח את 30 התווים הראשונים כ"תעודת זהות" לידיעה
        if any(text_signature in m['text'] for m in recent_messages):
            return # ההודעה קיימת במערכת, עוצר ביצוע
        
        recent_messages.append({'text': raw_text, 'time': current_time})

        # ב. ניקוי טקסט (ג'יבריש ולינקים של טלגרם)
        clean_text = html.unescape(raw_text)
        if "t.me/" in clean_text:
            clean_text = clean_text.split("t.me/")[0].strip()

        # ג. המרת שם המקור לעברית
        source_name = SOURCE_MAPPING.get(chat_username, chat_username)

        # ד. סיווג אוטומטי בסיסי (אימוג'י לפי תוכן)
        icon = "🔍"
        if any(word in clean_text for word in ["שיגור", "יציאה", "טיל", "רקטה"]): icon = "🚀"
        elif any(word in clean_text for word in ["פח\"ע", "פיגוע", "רצח", "חדירה"]): icon = "🚨"
        elif any(word in clean_text for word in ["איראן", "טהרן"]): icon = "🇮🇷"

        # ה. עיצוב הפורמט הסופי לשליחה
        dt = datetime.utcnow() + timedelta(hours=3) # שעון ישראל
        date_str = dt.strftime('%d/%m/%Y %H:%M')
        
        final_text = (
            f"Verified\n"
            f"{date_str}\n\n"
            f"{icon} **דיווח מעודכן**\n\n"
            f"מקור: {source_name}\n"
            f"{clean_text}"
        )

        # ו. שליחה לקבוצת הבקרה
        target_chat_id = "YOUR_GROUP_ID" # <<< הקלד כאן את ה-ID של קבוצת הצוות
        await context.bot.send_message(chat_id=target_chat_id, text=final_text)

    except Exception as e:
        print(f"Engine Error: {e}")

# ==========================================
# 4. התנעת המערכת
# ==========================================
def main():
    # הפעלת שרת החיים ברקע
    threading.Thread(target=run_server, daemon=True).start()

    # הפעלת בוט הטלגרם
    token = "YOUR_TELEGRAM_BOT_TOKEN" # <<< הקלד כאן את הטוקן של הבוט
    application = Application.builder().token(token).build()
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    
    print("System is booting... Listening to sources.")
    application.run_polling()

if __name__ == '__main__':
    main()
