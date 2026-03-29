import sys
import types
sys.modules['imghdr'] = types.ModuleType('imghdr')

import os
import html
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from googletrans import Translator

app = Flask(__name__)
translator = Translator()

@app.route('/')
def health_check():
    return "Abu Rubi Online", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

SOURCE_MAPPING = {
    "arielidan14": "אריאל עידן",
    "Intellinews": "אינטליניוז",
    "HallelBittonRosen": "הלל ביטון רוזן",
    "AlmogBoker": "אלמוג בוקר",
    "AJA_Palestine": "אל-ג'זירה פלסטין"
}

async def handle_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = update.channel_post or update.message
        if not msg or not (msg.text or msg.caption): return
        original_text = msg.text or msg.caption
        clean_text = html.unescape(original_text)
        chat_username = update.effective_chat.username
        source_name = SOURCE_MAPPING.get(chat_username, chat_username or "מקור חוץ")
        final_text = clean_text
        try:
            detection = translator.detect(clean_text)
            if detection.lang == 'ar':
                translation = translator.translate(clean_text, dest='he')
                final_text = f"{translation.text}\n\n*(תרגום אוטומטי)*"
        except: pass
        final_message = f"**מקור:** {source_name}\n\n{final_text}"
        await context.bot.send_message(chat_id="2405271", text=final_message, parse_mode='Markdown')
    except Exception as e: print(f"Error: {e}")

async def main():
    token = "8748416579:AAF1ljRu-D2DWoTlxlZ254a0a8YPk_ZYmeo"
    application = ApplicationBuilder().token(token).build()
    application.add_handler(MessageHandler(filters.ALL, handle_update))
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
