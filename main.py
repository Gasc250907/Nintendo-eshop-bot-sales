import os, sys, asyncio, requests, re
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
session = requests.Session()

# Mapa conversión monedas
MONEDAS = {
    "Japan": "JPY", "Hong Kong": "HKD", "Taiwan": "TWD", 
    "South Korea": "KRW", "Republic of Korea": "KRW",
    "Malaysia": "MYR", "Thailand": "THB", "Poland": "PLN",
    "South Africa": "ZAR", "New Zealand": "NZD", "Australia": "AUD",
    "United States": "USD", "Canada": "CAD", "Mexico": "MXN", 
    "Brazil": "BRL", "Colombia": "COP", "Peru": "PEN", 
    "Chile": "CLP", "Argentina": "ARS", "Norway": "NOK", 
    "Sweden": "SEK", "Switzerland": "CHF"
}

TASAS = {}

def actualizar_tasas():
    global TASAS
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        TASAS = r.json().get('rates', {})
        print("✅ Tasas sincronizadas.")
    except:
        print("⚠️ Error en tasas.")

def limpiar_precio_pro(monto_str, codigo_moneda):
    # si hay ofertas solo pone ultimo bloque
    bloques = re.findall(r'[\d,.]+', monto_str)
    if not bloques: return 0.0
    valor_raw = bloques[-1] 

    # logica decimal
    # En estas, 6,500 SIEMPRE es seis mil quinientos. Borramos comas y puntos.
    sin_decimales = ["JPY", "KRW", "CLP", "COP"]
    
    if codigo_moneda in sin_decimales:
        valor_final = valor_raw.replace(',', '').replace('.', '')
    else:
        # Para monedas con decimales (USD, MXN, EUR, BRL)
        # Si tiene coma y punto (1.200,50), quitamos el punto y la coma es el decimal
        if ',' in valor_raw and '.' in valor_raw:
            if valor_raw.find('.') < valor_raw.find(','): # Formato 1.200,50
                valor_final = valor_raw.replace('.', '').replace(',', '.')
            else: # Formato 1,200.50
                valor_final = valor_raw.replace(',', '')
        elif ',' in valor_raw:
            # Si solo tiene coma, ¿es miles o decimal? 
            # Si hay 3 dígitos después, suele ser miles (ej: 1,500)
            partes = valor_raw.split(',')
            if len(partes[-1]) == 3:
                valor_final = valor_raw.replace(',', '')
            else:
                valor_final = valor_raw.replace(',', '.')
        else:
            valor_final = valor_raw

    return float(valor_final)

def convertir_a_usd(monto_str, pais):
    try:
        moneda_local = MONEDAS.get(pais, "USD")
        monto_num = limpiar_precio_pro(monto_str, moneda_local)
        
        if moneda_local == "USD":
            return f"${monto_num:.2f}"
        
        tasa = TASAS.get(moneda_local)
        if tasa:
            usd_val = monto_num / tasa
            return f"${usd_val:.2f} USD"
        return "N/A"
    except:
        return "N/A"

def obtener_precios_globales(nombre_juego):
    url_base = "https://eshop-prices.com"
    url_busqueda = f"{url_base}/games?q={nombre_juego.replace(' ', '+')}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    try:
        r = session.get(url_busqueda, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        enlaces = [a['href'] for a in soup.find_all('a', href=True) if '/games/' in a['href'] and any(c.isdigit() for c in a['href'])]
        
        link_juego = ""
        for link in enlaces:
            if not any(x in link for x in ['on-sale', 'popular', 'new-releases']):
                link_juego = url_base + link if not link.startswith('http') else link
                break
        
        if not link_juego: return None, "❌ No encontré el juego."

        r_p = session.get(link_juego, headers=headers, timeout=10)
        soup_p = BeautifulSoup(r_p.text, 'html.parser')
        
        precios = []
        tabla = soup_p.find('table', class_='prices-table')
        if not tabla: return (soup_p.find('h1').text.strip() if soup_p.find('h1') else nombre_juego), ["🎁 Juego gratuito."]

        filas = tabla.find_all('tr', class_='pointer')
        for fila in filas:
            tds = fila.find_all('td')
            if len(tds) >= 4:
                pais = tds[1].get_text(strip=True)
                precio_td = fila.find('td', class_='price-value')
                if precio_td:
                    raw = precio_td.get_text(strip=True)
                    usd = convertir_a_usd(raw, pais)
                    precios.append(f"● {pais}: <b>{raw}</b> (≈ {usd})")
            if len(precios) >= 4: break

        return (soup_p.find('h1').text.strip() if soup_p.find('h1') else nombre_juego), precios
    except Exception as e:
        return None, f"⚠️ Error: {e}"

# Handlers
async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    espera = await update.message.reply_text(f"🔍 Jester analizando divisas para '{query}'...")
    loop = asyncio.get_event_loop()
    nombre, ofertas = await loop.run_in_executor(None, obtener_precios_globales, query)
    if nombre:
        mensaje = f"<b>{nombre}</b>\n\n" + "\n".join(ofertas)
        await espera.edit_text(mensaje, parse_mode='HTML')
    else:
        await espera.edit_text(ofertas)

if __name__ == "__main__":
    actualizar_tasas()
    app = ApplicationBuilder().token(TOKEN).read_timeout(60).build()
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Jester v5.7 (Fixed Formats) listo.")))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), buscar))
    app.run_polling()
