import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN manquant")

# --- Bot Telegram ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🤖 Tu as dit : {update.message.text}"
    )

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("🤖 Bot Telegram lancé...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())