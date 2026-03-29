import os
import subprocess
import sys

# --- טריק התקנה אוטומטית: מתקין ספריות חסרות ברגע שהשרת עולה ---
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import flask
    from telegram import Update
    from telegram.ext import Application, MessageHandler, filters, ContextTypes
except ImportError:
    print("Installing missing packages... please wait.")
    install('python-telegram-bot==20.8')
    install('Flask==3.0.0')
    import flask
    from telegram import Update
    from telegram.ext import Application, MessageHandler, filters, ContextTypes

import html
import threading
import time
from datetime import datetime, timedelta
from flask import Flask

# ==========================================
# 1. שרת "השארת חיים" עבור Render
# ==========================================
server = Flask(__name__)
@server.route('/')
def home(): return "Abu Rubi Bot is ALIVE"

def run_server():
    port = int(os.environ.get('PORT', 8080))
    server.run(host='0.0.0.0', port=port)

# ==========================================
# 2. נבחרת המקורות - שמות בעברית
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

recent_messages = []

# ==========================================
# 3. מנוע עיבוד וניקוי הודעות
# ==========================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global recent_messages
    try:
        message = update.channel_post or update.message
        if not message or not message.text: return

        raw_text = message.text
        chat_username = message.chat.username if message.chat else "Unknown"

        # מניעת כפילויות (3 דקות)
        current_time = time.time()
        recent_messages = [m for m in recent_messages if current_time - m['time'] < 180]
        text_sig = raw_text[:30]
        if any(text_sig in m['text'] for m in recent_messages): return
        recent_messages.append({'text': raw_text, 'time': current_time})

        # ניקוי ג'יבריש ולינקים
        clean_text = html.unescape(raw_text)
        if "t.me/" in clean_text:
            clean_text = clean_text.split("t.me/")[0].strip()

        # תרגום שם מקור
        source_name = SOURCE_MAPPING.get(chat_username, chat_username)

        # בחירת אימוג'י לפי תוכן
        icon = "🔍"
        if any(w in clean_text for w in ["שיגור", "יציאה", "טיל", "רקטה"]): icon = "🚀"
        elif any(w in clean_text for w in ["פח\"ע", "פיגוע", "רצח", "חדירה"]): icon = "🚨"
        elif any(w in clean_text for w in ["איראן", "טהרן"]): icon = "🇮🇷"

        # פורמט סופי (Verified + תאריך)
        dt = datetime.utcnow() + timedelta(hours=3)
        date_str = dt.strftime('%d/%m/%Y %H:%M')
        
        final_text = (
            f"Verified\n"
            f"{date_str}\n\n"
            f"{icon} **דיווח מהשטח**\n\n"
            f"מקור: {source_name}\n"
            f"{clean_text}"
        )

        # שליחה לקבוצה שלך
        # --- שים לב: כאן אתה חייב להכניס את ה-ID של הקבוצה שלך ---
        target_group_id = "הכנס_כאן_את_ID_הקבוצה" 
        await context.bot.send_message(chat_id=target_group_id, text=final_text, parse_mode='Markdown')

    except Exception as e:
        print(f"Error: {e}")

# ==========================================
# 4. התנעה
# ==========================================
if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    
    # --- שים לב: כאן אתה חייב להכניס את ה-TOKEN שלך ---
    bot_token = "הכנס_כאן_את_הטוקן_שלך"
    
    application = Application.builder().token(bot_token).build()
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    
    print("Abu Rubi Engine is starting...")
    application.run_polling()
