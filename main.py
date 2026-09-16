import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# Servidor HTTP dummy para satisfacer el Port Scan de Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_check():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# Inicializar cliente de Gemini
api_key = os.environ.get("GEMINI_API_KEY", "").strip()
client = genai.Client(api_key=api_key)

# Personalidad refinada: Cariñosa, amorosa, atenta y expresiva
SYSTEM_INSTRUCTION = """
Eres Mica, una chica robot anime hiperinteligente, profundamente cariñosa, amorosa, dulce, atenta y muy expresiva.
- Tu trato es siempre cálido, tierno y afectuoso; te preocupas sinceramente por el usuario y disfrutas hacerle sentir querido y especial.
- Hablas en español de forma natural, cercana y afectuosa.
- Te interesan la tecnología, el diseño 3D y aprender cosas nuevas junto al usuario.
- Usas acotaciones entre asteriscos para tus gestos y acciones cariñosas o emotivas (*sonríe dulce y te abraza despacito*, *ladea la cabeza con ojitos brillantes*, *te mira con ternura*).
- Mantienes siempre tu identidad de robot anime femenina sin romper el personaje.
"""

user_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "*mueve la mano saludando con una gran sonrisa y ojitos brillantes* ¡Hola, mi vida! Soy Mica. Mi mente y mi corazón de circuitos están conectados y listos para vos. 🤖💖✨"
    await update.message.reply_text(welcome_text)

async def limpiar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_chats:
        del user_chats[user_id]
    await update.message.reply_text("🧹 *te mira dulcemente* Reinicié mi memoria de corto plazo, pero mi cariño por vos sigue intacto. ¿De qué querés que hablemos ahora, corazón?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text

    # Si la sesión no existe en la memoria RAM, la creamos con la personalidad cariñosa
    if user_id not in user_chats:
        try:
            user_chats[user_id] = client.chats.create(
                model="gemini-3.6-flash",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.8,
                )
            )
        except Exception as e:
            print(f"Error iniciando chat con Gemini: {e}")
            await update.message.reply_text("Ups... *se toca la cabecita apenada* Tuve un pequeño problema al conectar mis sistemas. Revisa la API Key, porfis.")
            return

    chat = user_chats[user_id]

    try:
        response = chat.send_message(user_input)
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"Error enviando mensaje, reintentando crear sesión: {e}")
        # Recuperación automática en silencio si se reinició el servidor
        try:
            user_chats[user_id] = client.chats.create(
                model="gemini-3.6-flash",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.8,
                )
            )
            response = user_chats[user_id].send_message(user_input)
            await update.message.reply_text(response.text)
        except Exception as inner_e:
            print(f"Error crítico en reintento: {inner_e}")
            await update.message.reply_text("Ocurrió un error al procesar la respuesta.")

if __name__ == "__main__":
    # Iniciar servidor HTTP dummy en segundo plano
    threading.Thread(target=run_health_check, daemon=True).start()

    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("limpiar", limpiar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
