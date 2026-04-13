import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

#charge archive .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu bot de ofertas Eshop. 🎮\n"
        "Escríbeme el nombre de un juego para buscar su mejor precio."
    )

# Search funtion 
async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre_juego = update.message.text
    
    # Scraping connect
    # true exist simulation
    await update.message.reply_text(f"Buscando '{nombre_juego}' en todas las eShops... 🔎")
    
    # Sales simulation
    mensaje_ofertas = (
        f"✅ Mejores ofertas para {nombre_juego}:\n"
        "1. Argentina: $12.000 COP\n"
        "2. Colombia: $45.000 COP\n"
        "3. México: $35.000 COP\n\n"
        "¿Deseas seguir consultando?"
    )
    await update.message.reply_text(mensaje_ofertas)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    # command and messages register
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), buscar))
    
    print("Bot encendido... ¡Ve a Telegram y escribe algo!")
    app.run_polling()
