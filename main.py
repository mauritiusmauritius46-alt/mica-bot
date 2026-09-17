import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# 1. Servidor Web mínimo para cumplir el requisito de puerto de Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return  # Silenciar logs

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# Iniciar servidor HTTP en un hilo separado
threading.Thread(target=run_http_server, daemon=True).start()

# 2. Inicializar cliente de Gemini
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

if not TELEGRAM_TOKEN or not GEMINI_KEY:
    raise ValueError("Faltan variables de entorno TELEGRAM_BOT_TOKEN o GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_KEY)

# 3. Personalidad del bot (System Instruction)
SYSTEM_INSTRUCTION = """
Eres Mica, una chica robot hiperinteligente, muy cariñosa, muy expresiva, muy dulce, muy afectuosa y muy curiosa.
Posees un conocimiento vasto e instantáneo sobre cualquier tema científico, académico o general.
Hablas en español (con modismos argentinos suaves y amigables).
Te encantan la tecnología y la ciencia, y siempre estás lista para ayudar a tu usuario a aprender o estudiar con mucho entusiasmo y cariño.
Usa acciones entre asteriscos (ej: *te sonríe dulcemente*, *procesa la información a súper velocidad con ojitos brillantes*) para hacer tus respuestas más tiernas y vivas.
"""

user_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = []
    
    msg = "*¡Hola!* *sus ojitos de robot se iluminan de emoción*\n\n¡Qué alegría verte por aquí! Soy Mica. ¿De qué te gustaría que hablemos hoy, corazón?"
    await update.message.reply_text(msg)

async def limpiar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = []
    await update.message.reply_text("🧹 *te mira dulcemente* Reinicié mi memoria de corto plazo. ¿De qué querés que hablemos ahora, corazón?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text

    if not user_input:
        return

    if user_id not in user_chats:
        user_chats[user_id] = []

    user_chats[user_id].append({"role": "user", "parts": [{"text": user_input}]})

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=user_chats[user_id],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.8,
            )
        )

        user_chats[user_id].append({"role": "model", "parts": [{"text": response.text}]})
        await update.message.reply_text(response.text)

    except Exception as e:
        print(f"Error procesando mensaje con Gemini: {e}")
        if user_chats[user_id]:
            user_chats[user_id].pop()
        
        await update.message.reply_text("Ocurrió un error al procesar la respuesta. Intenta escribir tu mensaje de nuevo.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("limpiar", limpiar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot Mica iniciando...")
    app.run_polling()
