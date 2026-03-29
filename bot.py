import os
import asyncio
from flask import Flask
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from googletrans import Translator

app = Flask(__name__)
translator = Translator()

@app.route('/')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def handle_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = update.channel_post or update.message
        if not msg or not (msg.text or msg.caption): return
        text = msg.text or msg.caption
        
        # תרגום בסיסי
        final_text = text
        try:
            detect = translator.detect(text)
            if detect.lang == 'ar':
                trans = translator.translate(text, dest='he')
                final_text = f"{trans.text}\n\n(תרגום אוטומטי)"
        except: pass
        
        await context.bot.send_message(chat_id="2405271", text=final_text)
    except: pass

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    token = "8748416579:AAF1ljRu-D2DWoTlxlZ254a0a8YPk_ZYmeo"
    app_tg = ApplicationBuilder().token(token).build()
    app_tg.add_handler(MessageHandler(filters.ALL, handle_update))
    app_tg.run_polling()
