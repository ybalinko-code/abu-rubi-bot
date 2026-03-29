import os
import subprocess
import sys
import html
import threading
import time
from datetime import datetime, timedelta

# --- התקנה אוטומטית של ספריות חסרות ---
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import flask
    from telegram import Update
    from telegram.ext import Application, MessageHandler, filters, ContextTypes
except ImportError:
    install('python-telegram-bot==20.8')
    install('Flask==3.0.0')
    import flask
    from telegram import Update
    from telegram.ext import Application, MessageHandler, filters, ContextTypes

from flask import Flask

# ==========================================
# 1. הגדרות המערכת (הפרטים שלך)
# ==========================================
BOT_TOKEN = "7547012373:AAHkC5T08vO_Yw0P5I9G1K7S8R9Z0X1Y2Z3" # הטוקן שלך
TARGET_GROUP_ID = "-1002484433680" # ה-ID של קבוצת הצוות

# ==========================================
# 2. שרת "השארת חיים" עבור Render
# ==========================================
server = Flask(__name__)
@server.route('/')
def home(): return "Abu Rubi Bot is ALIVE and Monitoring"

def run_server():
    port = int(os.environ.get('PORT', 8080))
    server.run(host='0.0.0.0', port=port)

# ==========================================
# 3. נבחרת המקורות - שמות בעברית
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
# 4. מנוע עיבוד וניקוי הודעות
# ==========================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global recent_messages
    try:
        # שליפת ההודעה
        message = update.channel_post or update.message
        if not message or not message.text: return

        raw_text = message.text
        chat_username = message.chat.username if message.chat else "Unknown"

        # א. מניעת כפילויות (3 דקות)
        current_time = time.time()
        recent_messages = [m for m in recent_messages if current_time - m['time'] < 180]
        text_sig = raw_text[:30]
        if any(text_sig in m['text'] for m in recent_messages): return
        recent_messages.append({'text': raw_text, 'time': current_time})

        # ב. ניקוי ג'יבריש (HTML Entities) ו
