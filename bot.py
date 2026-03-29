import os
import html
import asyncio
import threading
import re
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from googletrans import Translator

# --- 1. הגדרות שרת ומנוע תרגום ---
app = Flask(__name__)
translator = Translator()

@app.route('/')
def health_check():
    return "Abu Rubi Intelligence System is Online", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. ספריית המכמונות המאוחדת (112 מופעים) ---
KEYWORDS = {
    "SECURITY": ["شهيد", "تسلل", "انفجار", "تصفية", "اغتيال", "كمين", "أسرى", "Infiltration", "Explosion", "Martyr", "Assassination"],
    "DISASTER": ["زلزال", "تسونامي", "فيضان", "إعصار", "Earthquake", "Tsunami", "Flood", "Hurricane", "Magnitude", "Epicenter"],
    "AVIA_BALISTIC": ["إطلاق", "صاروخ", "قذيفة", "تحطم", "مسيرة", "Launch", "Missile", "Rocket", "Crash", "UAV", "Drone", "צעדה", "שיגור", "רקטה"],
    "STRATEGIC": ["هرمز", "المندب", "فيلادلفيا", "نووية", "Hormuz", "Mandeb", "Philadelphi", "Nuclear"],
    "GLOBAL": ["Mass Shooting", "Active Shooter", "MCI", "Lockdown", "ירי המוני"]
}

# --- 3. לוגיקת עיבוד, תרגום וניקוי ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = update.channel_post or update.message
        if not msg or not msg.text: return

        text = msg.text
        # זיהוי אם ההודעה רלוונטית לפי המכמונות
        is_relevant = any(key.lower() in text.lower() for cat in KEYWORDS.values() for key in cat)
        
        if not is_relevant: return # אם אין מילת מפתח, הבוט לא "מפריע" לך בנהיגה

        # תרגום אוטומטי אם הטקסט בערבית או אנגלית
        detected = translator.detect(text)
        if detected.lang != 'he':
            translated = translator.translate(text, dest='he')
            final_text = f"**[תרגום אוטומטי]**\n{translated.text}"
        else:
            final_text = text

        # ניקוי לינקים ופרסומות (Regex)
        final_text = re.sub(r'http\S+', '', final_text)
        final_text = re.sub(r'@\S+', '', final_text)

        # כותרת מקור
        chat_title = update.effective_chat.title or "מקור חוץ"
        output = f"🔴 **מקור:** {chat_title}\n\n{final_text}"

        # שליחה ל-ID הפרטי שלך (2405271)
        await context.bot.send_message(chat_id="2405271", text=output, parse_mode='Markdown')

    except Exception as e:
        print(f"Error: {e}")

# --- 4. התנעה ---
async def main():
    token = "8748416579:AAF1ljRu-D2DWoTlxlZ254a0a8YPk_ZYmeo"
    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    async with application:
        await application.initialize()
        await application.start()
        print("--- Abu Rubi Bot System V3.0 Started ---")
        await application.updater.start_polling()
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
