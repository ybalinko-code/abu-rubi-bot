import os
import html
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# --- 1. שרת Flask ליציבות ב-Render ---
app = Flask(__name__)
@app.route('/')
def health_check(): return "Bot is running", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. נבחרת הכתבים (שמות בעברית) ---
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

# --- 3. עיבוד הודעה וניקוי ג'יבריש ---
async def handle_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = update.channel_post or update.message
        if not msg or not msg.text: return

        # ניקוי ג'יבריש וסימני HTML
        clean_text = html.unescape(msg.text)
        
        # זיהוי מקור ותרגום לעברית
        chat_username = update.effective_chat.username
        source_name = SOURCE_MAPPING.get(chat_username, chat_username or "מקור לא ידוע")

        # בניית ההודעה בפורמט Verified
        final_message = f"**Verified**\n{source_name}\n\n{clean_text}"

        # שליחה לקבוצת הצוות שלך (ה-ID כבר בפנים)
        await context.bot.send_message(
            chat_id="-1002476906236", 
            text=final_message, 
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error: {e}")

# --- 4. הרצה ---
async def main():
    token = "כאן_הטוקן_שלך" # שים פה את ה-TOKEN מה-BotFather
    application = ApplicationBuilder().token(token).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_update))
    
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
