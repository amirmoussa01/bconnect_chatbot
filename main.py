import os
import logging
from fastapi import FastAPI, Request, HTTPException
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

# Validation des variables d'environnement
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN manquant dans les variables d'environnement")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL manquant dans les variables d'environnement")

# Application Telegram
telegram_app = Application.builder().token(BOT_TOKEN).build()


# --- Gestionnaires de commandes ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start"""
    welcome_message = (
        "👋 Bienvenue ! Je suis votre assistant intelligent.\n\n"
        "Commandes disponibles :\n"
        "/start - Démarrer le bot\n"
        "/aide - Obtenir de l'aide\n"
        "/info - Informations sur le bot\n\n"
        "Vous pouvez aussi m'envoyer n'importe quel message !"
    )
    await update.message.reply_text(welcome_message)


async def aide_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /aide"""
    help_message = (
        "ℹ️ **Guide d'utilisation**\n\n"
        "• Envoyez 'bonjour' ou 'salut' pour me saluer\n"
        "• Posez vos questions sur l'application\n"
        "• Utilisez /info pour en savoir plus sur moi\n"
    )
    await update.message.reply_text(help_message)


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /info"""
    info_message = (
        "🤖 **À propos du bot**\n\n"
        "Je suis un chatbot intelligent propulsé par FastAPI.\n"
        "Version : 1.0\n"
        "Status : En ligne ✅"
    )
    await update.message.reply_text(info_message)


# --- Gestion des messages ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Traite les messages texte"""
    try:
        user_message = update.message.text.lower()
        user_name = update.effective_user.first_name
        
        # IA légère avec réponses contextuelles
        if any(word in user_message for word in ["bonjour", "salut", "hello", "hi"]):
            reply = f"👋 Bonjour {user_name} ! Comment puis-je vous aider aujourd'hui ?"
        
        elif any(word in user_message for word in ["aide", "help", "comment"]):
            reply = "ℹ️ Je peux répondre à vos questions. Utilisez /aide pour voir toutes les commandes disponibles."
        
        elif any(word in user_message for word in ["merci", "thanks"]):
            reply = "😊 De rien ! N'hésitez pas si vous avez d'autres questions !"
        
        elif "?" in user_message:
            reply = f"🤔 Bonne question ! Pour '{user_message}', je vous suggère de consulter notre documentation ou de contacter le support."
        
        else:
            reply = f"📝 J'ai bien reçu votre message : '{user_message}'\n\nComment puis-je vous assister ?"
        
        await update.message.reply_text(reply)
        logger.info(f"Message traité de {user_name}: {user_message}")
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du message: {e}")
        await update.message.reply_text("❌ Désolé, une erreur s'est produite. Réessayez plus tard.")


# Ajout des handlers
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(CommandHandler("aide", aide_command))
telegram_app.add_handler(CommandHandler("info", info_command))
telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)


# --- Lifecycle management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application"""
    # Startup
    try:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        await telegram_app.initialize()
        await telegram_app.bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook configuré : {webhook_url}")
        await telegram_app.start()
        logger.info("✅ Application Telegram démarrée")
    except Exception as e:
        logger.error(f"❌ Erreur au démarrage : {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        await telegram_app.bot.delete_webhook()
        await telegram_app.stop()
        await telegram_app.shutdown()
        logger.info("✅ Application arrêtée proprement")
    except Exception as e:
        logger.error(f"❌ Erreur à l'arrêt : {e}")


# Création de l'application FastAPI
app = FastAPI(
    title="Telegram AI Bot",
    description="Bot Telegram intelligent avec FastAPI",
    version="1.0.0",
    lifespan=lifespan
)


# --- Endpoints API ---
@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Reçoit les mises à jour de Telegram"""
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Erreur webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    """Endpoint de santé"""
    return {
        "status": "online",
        "message": "Bot Telegram actif 🚀",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Vérification de santé détaillée"""
    return {
        "status": "healthy",
        "bot_token": "configured" if BOT_TOKEN else "missing",
        "webhook_url": "configured" if WEBHOOK_URL else "missing"
    }