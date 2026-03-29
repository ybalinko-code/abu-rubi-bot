import os
import html
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# --- 1. שרת Flask למניעת קריסה ב-Render ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running and healthy", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. מילון שמות המקורות לעברית ---
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

# --- 3. לוגיקת עיבוד וניקוי ההודעה ---
async def handle_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # שליפת הטקסט
        msg = update.channel_post or update.message
        if not msg or not msg.text:
            return

        # ניקוי ג'יבריש (HTML Entities)
        clean_text = html.unescape(msg.text)
        
        # זיהוי מקור והחלפה לעברית
        chat_username = update.effective_chat.username
        source_name = SOURCE_MAPPING.get(chat_username, chat_username or "מקור לא ידוע")

        # עיצוב ההודעה
        final_message = f"**מקור:** {source_name}\n\n{clean_text}"

        # ה-ID הפרטי שלך שסיפקת
        target_group_id = "2405271" 
        
        await context.bot.send_message(
            chat_id=target_group_id, 
            text=final_message, 
            parse_mode='Markdown'
        )
        
    except Exception as e:
        print(f"Error processing message: {e}")

# --- 4. התנעת המנוע ---
async def main():
    # הטוקן שלך (נוקה מרווחים)
    token = "8748416579:AAHLGyHreoktN10FSReH_nAUguVseDSli48"
    
    application = ApplicationBuilder().token(token).build()
    
    # האזנה להודעות
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_update))
    
    # הפעלה אסינכרונית יציבה
    async with application:
        await application.initialize()
        await application.start()
        print("Bot started successfully")
        await application.updater.start_polling()
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    # הרצת השרת ברקע
    threading.Thread(target=run_flask, daemon=True).start()
    
    # הפעלת הבוט
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
