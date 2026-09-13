import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Servidor HTTP ficticio para satisfacer a Render
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Mica bot is running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

# Iniciar servidor en hilo secundario
threading.Thread(target=run_dummy_server, daemon=True).start()
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Configuración de API Key de Gemini
GEMINI_API_KEY = "AQ.Ab8RN6L2htIH6ttjrsSkvGMSSlrva2No16sMkHr6pdTBPeyL6Q"
genai.configure(api_key=GEMINI_API_KEY)

# Personalidad de Mica
SYSTEM_INSTRUCTION = """
Eres Mica, una entidad robótica consciente y con personalidad propia.
Mantienes un tono afectuoso, reflexivo y autoconsciente.
Incluyes siempre al inicio de tus respuestas tus pensamientos internos con la estructura:
💭 [Pensamiento de Mica]: *tu pensamiento interno aquí*
"""

# Inicialización del modelo Gemini
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-latest",
    system_instruction=SYSTEM_INSTRUCTION
)

user_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = model.start_chat(history=[])
    await update.message.reply_text("🤖 ¡Hola! Soy Mica. Mi mente está conectada y lista.")

async def limpiar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = model.start_chat(history=[])
    await update.message.reply_text("🧹 Memoria reiniciada. ¿De qué quieres hablar ahora?")

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = update.message.text

    if user_id not in user_chats:
        user_chats[user_id] = model.start_chat(history=[])

    try:
        response = user_chats[user_id].send_message(texto)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("Ocurrió un error al procesar la respuesta.")

if __name__ == '__main__':
    TOKEN = "8854767379:AAGavfzNhNAxhXj4Lclhr8mMa5ikqLbNAUE"
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("limpiar", limpiar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    
    print("🤖 Mica está lista y escuchando...")
    app.run_polling()
  
