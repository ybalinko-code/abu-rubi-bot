import os, html, asyncio, threading, requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# --- 1. שרת Flask בסיסי ---
app = Flask(__name__)
@app.route('/')
def health(): return "OK", 200
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- 2. פונקציית תרגום חסינה (ללא ספריות חיצוניות) ---
def translate_text(text):
    try:
        # שימוש ב-API חופשי ומהיר שלא דורש התקנה
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=iw&dt=t&q={text}"
        r = requests.get(url)
        return "".join([s[0] for s in r.json()[0]])
    except: return text

# --- 3. לוגיקת הבוט ---
SOURCE_MAPPING = {"arielidan14": "אריאל עידן", "HallelBittonRosen": "הלל ביטון רוזן"}

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post or update.message
    if not msg or not (msg.text or msg.caption): return
    
    raw = msg.text or msg.caption
    source = SOURCE_MAPPING.get(update.effective_chat.username, update.effective_chat.username or "מקור חוץ")
    
    # תרגום אוטומטי
    translated = translate_text(raw)
    final = f"**מקור:** {source}\n\n{translated}"
    if translated != raw: final += "\n\n*(תרגום אוטומטי)*"

    await context.bot.send_message(chat_id="2405271", text=final, parse_mode='Markdown')

# --- 4. התנעה ---
async def main():
    token = "8748416579:AAF1ljRu-D2DWoTlxlZ254a0a8YPk_ZYmeo"
    app_bot = ApplicationBuilder().token(token).build()
    app_bot.add_handler(MessageHandler(filters.ALL, handle_msg))
    async with app_bot:
        await app_bot.initialize()
        await app_bot.start()
        await app_bot.updater.start_polling()
        await asyncio.Event().wait()

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
