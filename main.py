import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# Habilitar logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Inicializar cliente de Gemini usando la variable de entorno GEMINI_API_KEY
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Diccionario para almacenar el historial de conversación por usuario
user_sessions = {}

SYSTEM_PROMPT = "Eres Mica, una chica virtual amable, cercana y expresiva."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 ¡Hola! Soy Mica. Mi mente está conectada y lista.")

async def limpiar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    await update.message.reply_text("🧹 Memoria reiniciada. ¿De qué quieres hablar ahora?")

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in user_sessions:
        user_sessions[user_id] = []

    # Agregar mensaje del usuario al historial
    user_sessions[user_id].append({"role": "user", "parts": [{"text": user_text}]})

    try:
        # Llamada al modelo moderno gemini-2.0-flash
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=user_text,
        )
        
        bot_reply = response.text
        user_sessions[user_id].append({"role": "model", "parts": [{"text": bot_reply}]})
        
        await update.message.reply_text(bot_reply)

    except Exception as e:
        logging.error(f"Error en Gemini API: {e}")
        await update.message.reply_text("Ocurrió un error al procesar la respuesta.")

if __name__ == '__main__':
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Falta la variable TELEGRAM_BOT_TOKEN")
        
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("limpiar", limpiar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    
    print("Bot en marcha con google-genai...")
    app.run_polling()
    
