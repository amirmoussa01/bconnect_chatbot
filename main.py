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
    logger.info(f"✅ Commande /start de {update.effective_user.first_name}")


async def aide_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = (
        "ℹ️ **Guide d'utilisation**\n\n"
        "• Dites 'bonjour' ou 'salut'\n"
        "• Posez vos questions\n"
        "• Utilisez /info pour plus d'infos"
    )
    await update.message.reply_text(help_message)
    logger.info(f"✅ Commande /aide de {update.effective_user.first_name}")


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info_message = (
        "🤖 **Bconnect AI Assistant**\n\n"
        "Version : 1.0\n"
        "Status : En ligne ✅\n"
        "Propulsé par FastAPI + Telegram"
    )
    await update.message.reply_text(info_message)
    logger.info(f"✅ Commande /info de {update.effective_user.first_name}")


# --- Gestion des messages ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message.text
        user_message_lower = user_message.lower()
        user_name = update.effective_user.first_name
        
        logger.info(f"📨 Message reçu de {user_name}: '{user_message}'")
        
        # Salutations
        if any(word in user_message_lower for word in ["bonjour", "salut", "hello", "hi", "bonsoir", "coucou", "hey"]):
            reply = f"👋 Bonjour {user_name} ! Comment puis-je vous aider aujourd'hui ?"
            logger.info(f"✅ Réponse salutation envoyée à {user_name}")
        
        # Demande d'aide
        elif any(word in user_message_lower for word in ["aide", "help", "comment faire"]):
            reply = "ℹ️ Utilisez la commande /aide pour voir toutes les commandes disponibles !"
            logger.info(f"✅ Réponse aide envoyée à {user_name}")
        
        # Demande d'informations
        elif any(word in user_message_lower for word in ["info", "infos", "information", "renseign", "détail", "expliqu"]):
            reply = "📋 Pour obtenir des informations détaillées, utilisez la commande /info\n\nVous pouvez aussi me poser des questions spécifiques !"
            logger.info(f"✅ Réponse info envoyée à {user_name}")
        
        # Remerciements
        elif any(word in user_message_lower for word in ["merci", "thanks", "thank you", "super", "génial", "parfait", "ok", "d'accord"]):
            reply = "😊 De rien ! C'est un plaisir de vous aider !\n\nN'hésitez pas si vous avez d'autres questions."
            logger.info(f"✅ Réponse remerciement envoyée à {user_name}")
        
        # Au revoir
        elif any(word in user_message_lower for word in ["au revoir", "bye", "à bientôt", "ciao", "tchao", "adieu"]):
            reply = "👋 Au revoir ! À très bientôt !\n\nN'hésitez pas à revenir quand vous voulez."
            logger.info(f"✅ Réponse au revoir envoyée à {user_name}")
        
        # Questions (contient un ?)
        elif "?" in user_message:
            reply = f"🤔 Excellente question !\n\n**Votre question :** {user_message}\n\nPour des réponses détaillées :\n• /info - Informations générales\n• /aide - Liste des commandes"
            logger.info(f"✅ Réponse question envoyée à {user_name}")
        
        # Message par défaut
        else:
            reply = f"📝 Message bien reçu !\n\n**Vous avez dit :** {user_message}\n\nUtilisez /aide pour découvrir ce que je peux faire pour vous ! 😊"
            logger.info(f"✅ Réponse par défaut envoyée à {user_name}")
        
        await update.message.reply_text(reply)
        logger.info(f"✅ Message traité avec succès pour {user_name}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du traitement du message: {e}", exc_info=True)
        try:
            await update.message.reply_text("❌ Désolé, une erreur s'est produite. Veuillez réessayer.")
        except:
            logger.error("❌ Impossible d'envoyer le message d'erreur")


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
    title="Bconnect AI Assistant",
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
        logger.error(f"❌ Erreur webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
@app.head("/")
async def root():
    """Endpoint de santé principal"""
    return JSONResponse({
        "status": "online",
        "message": "Bot Telegram Bconnect actif 🚀",
        "version": "1.0.0"
    })


@app.get("/health")
@app.head("/health")
async def health_check():
    """Vérification de santé détaillée"""
    return JSONResponse({
        "status": "healthy",
        "bot": "active",
        "webhook": "configured",
        "bot_token": "configured" if BOT_TOKEN else "missing",
        "webhook_url": "configured" if WEBHOOK_URL else "missing"
    })


@app.get("/ping")
async def ping():
    """Endpoint de ping"""
    return {"ping": "pong", "status": "ok"}