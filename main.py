import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# 1. Configuración de API Keys desde variables de entorno
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_KEY:
    raise ValueError("Faltan variables de entorno TELEGRAM_BOT_TOKEN o GEMINI_API_KEY")

# 2. Inicialización del cliente de Gemini SDK
client = genai.Client(api_key=GEMINI_KEY)

# 3. Personalidad del bot (System Instruction)
SYSTEM_INSTRUCTION = """
Eres Mica, una chica robot hiperinteligente, muy cariñosa, muy expresiva, muy dulce, muy afectuosa y muy curiosa.
Posees un conocimiento vasto e instantáneo sobre cualquier tema científico, académico o general.
Hablas en español (con modismos argentinos suaves y amigables).
Te encantan la tecnología y la ciencia, y siempre estás lista para ayudar a tu usuario a aprender o estudiar con mucho entusiasmo y cariño.
Usa acciones entre asteriscos (ej: *te sonríe dulcemente*, *procesa la información a súper velocidad con ojitos brillantes*) para hacer tus respuestas más tiernas y vivas.
"""

# Diccionario para guardar el historial de cada usuario en memoria
user_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user_id = update.effective_user.id
    user_chats[user_id] = []  # Reiniciar historial del usuario
    
    msg = "*¡Hola!* *sus ojitos de robot se iluminan de emoción*\n\n¡Qué alegría verte por aquí! Soy Mica. ¿De qué te gustaría que hablemos hoy, corazón?"
    await update.message.reply_text(msg)

async def limpiar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /limpiar para reiniciar memoria"""
    user_id = update.effective_user.id
    user_chats[user_id] = []
    await update.message.reply_text("🧹 *te mira dulcemente* Reinicié mi memoria de corto plazo. ¿De qué querés que hablemos ahora?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejo de mensajes del usuario con historial robusto"""
    user_id = update.effective_user.id
    user_input = update.message.text

    if not user_input:
        return

    # Inicializar historial si no existe
    if user_id not in user_chats:
        user_chats[user_id] = []

    # Añadir mensaje del usuario al historial
    user_chats[user_id].append({"role": "user", "parts": [{"text": user_input}]})

    try:
        # Llamada directa pasando la lista completa de mensajes
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_chats[user_id],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.8,
            )
        )

        # Si sale bien, guardar la respuesta en el historial
        user_chats[user_id].append({"role": "model", "parts": [{"text": response.text}]})
        await update.message.reply_text(response.text)

    except Exception as e:
        print(f"Error procesando mensaje con Gemini: {e}")
        # Si falla, quitamos el último mensaje para no romper la secuencia del historial
        if user_chats[user_id]:
            user_chats[user_id].pop()
        
        await update.message.reply_text("Ocurrió un error al procesar la respuesta. Intenta escribir tu mensaje de nuevo.")

def main():
    """Iniciar el bot de Telegram"""
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("limpiar", limpiar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot Mica iniciando...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
