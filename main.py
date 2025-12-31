import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters
)
from contextlib import asynccontextmanager

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Validation
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN manquant")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL manquant")

telegram_app = Application.builder().token(BOT_TOKEN).build()


# --- Commandes ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "👋 Bienvenue ! Je suis votre assistant Bconnect.\n\n"
        "Commandes disponibles :\n"
        "/start - Démarrer le bot\n"
        "/aide - Obtenir de l'aide\n"
        "/info - Informations\n\n"
        "Envoyez-moi un message !"
    )
    await update.message.reply_text(welcome_message)


async def aide_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = (
        "ℹ️ **Guide d'utilisation**\n\n"
        "• Dites 'bonjour' ou 'salut'\n"
        "• Posez vos questions\n"
        "• Utilisez /info pour plus d'infos"
    )
    await update.message.reply_text(help_message)


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info_message = (
        "🤖 **Bconnect AI Assistant**\n\n"
        "Version : 1.0\n"
        "Status : En ligne ✅\n"
        "Propulsé par FastAPI + Telegram"
    )
    await update.message.reply_text(info_message)


# --- Messages ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message.text.lower()
        user_name = update.effective_user.first_name
        
        if any(word in user_message for word in ["bonjour", "salut", "hello", "hi"]):
            reply = f"👋 Bonjour {user_name} ! Comment puis-je vous aider ?"
        
        elif any(word in user_message for word in ["aide", "help"]):
            reply = "ℹ️ Utilisez /aide pour voir toutes les commandes disponibles."
        
        elif any(word in user_message for word in ["merci", "thanks"]):
            reply = "😊 De rien ! À votre service !"
        
        elif any(word in user_message for word in ["info", "infos", "information"]):
            reply = "📋 Pour obtenir des informations, utilisez la commande /info"
        
        elif "?" in user_message:
            reply = f"🤔 Bonne question ! Je note : '{user_message}'"
        
        else:
            reply = f"📝 Message reçu : '{user_message}'\n\nComment puis-je vous assister ?"
        
        await update.message.reply_text(reply)
        logger.info(f"✅ Message traité de {user_name}: {user_message}")
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        await update.message.reply_text("❌ Une erreur s'est produite. Réessayez.")


# Handlers
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(CommandHandler("aide", aide_command))
telegram_app.add_handler(CommandHandler("info", info_command))
telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)


# --- Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        await telegram_app.initialize()
        await telegram_app.bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook: {webhook_url}")
        await telegram_app.start()
        logger.info("✅ Bot démarré")
    except Exception as e:
        logger.error(f"❌ Erreur démarrage: {e}")
        raise
    
    yield
    
    try:
        await telegram_app.bot.delete_webhook()
        await telegram_app.stop()
        await telegram_app.shutdown()
        logger.info("✅ Bot arrêté proprement")
    except Exception as e:
        logger.error(f"❌ Erreur arrêt: {e}")


app = FastAPI(
    title="Bconnect AI Assistant",
    description="Bot Telegram intelligent",
    version="1.0.0",
    lifespan=lifespan
)


# --- Endpoints ---
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"❌ Erreur webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Support GET et HEAD pour le health check
@app.get("/")
@app.head("/")
async def root():
    return JSONResponse({
        "status": "online",
        "message": "Bot Telegram actif 🚀",
        "version": "1.0.0"
    })


@app.get("/health")
@app.head("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "bot": "active",
        "webhook": "configured"
    })


# Endpoint de ping pour garder le service actif
@app.get("/ping")
async def ping():
    return {"ping": "pong", "timestamp": "ok"}