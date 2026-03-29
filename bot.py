import os
import html
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# --- 1. הגדרת שרת Flask כדי להחזיק את Render בחיים ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running and healthy", 200

def run_flask():
    # Render משתמש בפורט 10000 או מה שמוגדר ב-PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. מילון שמות המקורות (הנבחרת שלך) ---
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
        # חילוץ הטקסט (מהודעות בערוץ או בקבוצה)
        msg = update.channel_post or update.message
        if not msg or not msg.text:
            return

        # ניקוי ג'יבריש (HTML Entities)
        clean_text = html.unescape(msg.text)
        
        # זיהוי מקור ותרגום לעברית
        chat_username = update.effective_chat.username
        source_name = SOURCE_MAPPING.get(chat_username, chat_username or "מקור לא ידוע")

        # עיצוב ההודעה הסופי
        final_message = f"**מקור:** {source_name}\n\n{clean_text}"

        # שליחה לקבוצת הצוות שלך (החלף ב-ID האמיתי של הקבוצה)
        # אם אין לך ID, הבוט ידפיס אותו ללוג כשתשלח לו הודעה
        target_group_id = "-1002476906236" # דוגמה ל-ID, וודא שזה שלך
        
        await context.bot.send_message(
            chat_id=target_group_id, 
            text=final_message, 
            parse_mode='Markdown'
        )
        
    except Exception as e:
        print(f"Error processing message: {e}")

# --- 4. התנעת המערכת ---
async def main():
    # הכנס כאן את ה-TOKEN שלך
    token = "YOUR_BOT_TOKEN_HERE"
    
    application = ApplicationBuilder().token(token).build()
    
    # מאזין לכל סוגי ההודעות טקסט
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_update))
    
    # הפעלת הבוט
    async with application:
        await application.initialize()
        await application.start()
        print("Bot started successfully")
        await application.updater.start_polling()
        # מחזיק את הלולאה בחיים
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    # הפעלת שרת ה-Web בשרשור נפרד
    threading.Thread(target=run_flask, daemon=True).start()
    
    # הפעלת לולאת הטלגרם
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
