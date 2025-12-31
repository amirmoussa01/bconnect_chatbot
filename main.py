import os
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

app = FastAPI(title="Telegram AI Bot")

telegram_app = Application.builder().token(BOT_TOKEN).build()


# --- Gestion des messages ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()

    # IA légère (règles simples)
    if "bonjour" in user_message or "salut" in user_message:
        reply = "👋 Bonjour ! Je suis le chatbot de l’application."
    elif "aide" in user_message:
        reply = "ℹ️ Je peux répondre aux questions sur l’application."
    else:
        reply = f"🤖 Tu as dit : {user_message}"

    await update.message.reply_text(reply)


telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)


# --- Endpoint Webhook ---
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}


@app.get("/")
def root():
    return {"status": "Bot Telegram actif 🚀"}


# --- Lancement webhook au démarrage ---
@app.on_event("startup")
async def on_startup():
    if WEBHOOK_URL and WEBHOOK_URL.startswith("https://"):
        await telegram_app.bot.set_webhook(WEBHOOK_URL + "/webhook")
        print("✅ Webhook Telegram configuré")
    else:
        print("ℹ️ Mode local : webhook non configuré")

# import os

# LOCAL_MODE = os.getenv("LOCAL_MODE") == "1"

# if __name__ == "__main__" and LOCAL_MODE:
#     print("🧪 Mode local (polling)")
#     telegram_app.run_polling()