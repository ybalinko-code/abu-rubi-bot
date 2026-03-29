import os
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from googletrans import Translator

# הגדרת שרת Flask עבור Render
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!", 200

# מילון שמות המקורות (אנגלית לעברית)
SOURCE_MAPPING = {
    "arielidan14": "אריאל עידן",
    "Intellinews": "אינטליניוז",
    "HallelBittonRosen": "הלל ביטון רוזן",
    "AlmogBoker": "אלמוג בוקר",
    "yosiyehoshua": "יוסי יהושוע",
    "AJA_Palestine": "אל-ג'זירה פלסטין",
    "GazaNowNewsletter": "עזה עכשיו",
    "shehabagency": "סוכנות שהאב",
    "hamasps": "חמאס (רשמי)"
}

translator = Translator()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    original_text = update.message.text
    
    # זיהוי המקור (מתוך הודעה מועברת או שם המשתמש)
    raw_source = "מקור לא ידוע"
    if update.message.forward_from_chat:
        raw_source = update.message.forward_from_chat.username or update.message.forward_from_chat.title
    elif update.message.forward_from:
        raw_source = update.message.forward_from.username or update.message.forward_from.first_name
    
    # החלפת השם לעברית לפי המילון
    display_source = SOURCE_MAPPING.get(raw_source, raw_source)

    try:
        # תרגום אוטומטי לעברית
        detection = translator.detect(original_text)
        if detection.lang != 'he':
            translation = translator.translate(original_text, dest='he')
            final_text = f"**מקור: {display_source}**\n\n{translation.text}\n\n(תרגום אוטומטי)"
        else:
            final_text = f"**מקור: {display_source}**\n\n{original_text}"
        
        await update.message.reply_text(final_text, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"**מקור: {display_source}**\n\n{original_text}")

async def main():
    # שים כאן את ה-Token שלך
    TOKEN = "7724103132:AAH9E9v1u_j8_G09Z9Z9Z9Z9Z9Z9Z9Z9Z9Z" # וודא שזה הטוקן הנכון
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # הפעלת Flask בפורט ש-Render דורש
    import threading
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port)).start()
    
    # השארת הבוט רץ
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())
