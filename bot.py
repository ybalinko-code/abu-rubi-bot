import sys
import types
# עקיפת בעיית imghdr בגרסאות פייתון חדשות
sys.modules['imghdr'] = types.ModuleType('imghdr')

import os
import html
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from googletrans import Translator

# --- 1. שרת Flask למניעת קריסה ---
app = Flask(__name__)
translator = Translator()

@app.route('/')
def health_check():
    return "Abu Rubi Intelligence System is Online", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. מילון מקורות (עברית וערבית) ---
SOURCE_MAPPING = {
    # ישראלים
    "arielidan14": "אריאל עידן",
    "Intellinews": "אינטליניוז",
    "HallelBittonRosen": "הלל ביטון רוזן",
    "AlmogBoker": "אלמוג בוקר",
    "yosiyehoshua": "יוסי יהושוע",
    # מקורות ערביים (דוגמאות)
    "AJA_Palestine": "אל-ג'זירה פלסטין",
    "GazaNowNewsletter": "עזה עכשיו",
    "shehabagency": "סוכנות שהאב",
    "hamasps": "חמאס (רשמי)"
}

# --- 3. לוגיקת עיבוד, תרגום וניקוי ---
async def handle_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = update.channel_post or update.message
        if not msg or not (msg.text or msg.caption):
            return

        original_text = msg.text or msg.caption
        clean_text = html.unescape(original_text)
        
        # זיהוי מקור
        chat_username = update.effective_chat.username
        source_name = SOURCE_MAPPING.get(chat_username, chat_username or "מקור חוץ")

        # מנגנון תרגום אוטומטי מערבית
        final_text = clean_text
        try:
            detection = translator.detect(clean_text)
            if detection.lang == 'ar':
                translation = translator.translate(clean_text, dest='he')
                final_text = f"{translation.text}\n\n*(תרגום אוטומטי מערבית)*"
        except Exception as e:
            print(f"Translation error: {e}")

        # עיצוב הודעה סופי
        final_message = f"**מקור:** {source_name}\n\n{final_text}"

        # שליחה ל-ID שלך (תשנה ל-ID של הקבוצה כשתרצה)
        await context.bot.send_message(
            chat_id="2405271", 
            text=final_message, 
            parse_mode='Markdown'
        )
        
    except Exception as e:
        print(f"Error: {e}")

# --- 4. התנעה ---
async def main():
    token = "8748416579:AAF1ljRu-D2DWoTlxlZ254a0a8YPk_ZYmeo"
    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(MessageHandler(filters.ALL, handle_update))
    
    async with application:
        await application.initialize()
        await application.start()
        print("--- Abu Rubi Bot is Live with Translation Support ---")
        await application.updater.start_polling()
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
