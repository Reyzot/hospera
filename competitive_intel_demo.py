"""
Informe diario de Competitive Intelligence — datos reales via SerpApi.
Uso: python3 competitive_intel_demo.py
"""
import os, urllib.request, urllib.parse, json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from twilio.rest import Client as TwilioClient
import anthropic

load_dotenv()

TWILIO_SID       = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN     = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM      = os.getenv("TWILIO_WHATSAPP_FROM")
MANAGER_WHATSAPP = os.getenv("MANAGER_WHATSAPP")
ANTHROPIC_KEY    = os.getenv("ANTHROPIC_API_KEY")
SERPAPI_KEY      = os.getenv("SERPAPI_KEY")

HOTEL_CLIENTE = os.getenv("HOTEL_NAME", "Hotel Peninsular")
PRECIO_CLIENTE = int(os.getenv("HOTEL_PRECIO", "95"))
ZONA_BUSQUEDA  = os.getenv("HOTEL_ZONA", "hotels near Las Ramblas Barcelona")

checkin  = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
checkout = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
fecha_texto = datetime.now().strftime("%A %d %B %Y")

# ── SerpApi: precios reales de competidores ───────────────────────────────────
def get_competidores():
    url = (
        f"https://serpapi.com/search.json?engine=google_hotels"
        f"&q={urllib.parse.quote(ZONA_BUSQUEDA)}"
        f"&check_in_date={checkin}&check_out_date={checkout}"
        f"&adults=2&currency=EUR&hl=es&gl=es"
        f"&api_key={SERPAPI_KEY}"
    )
    req = urllib.request.urlopen(url)
    data = json.loads(req.read())
    hotels = data.get("properties", [])[:5]
    result = []
    for h in hotels:
        precio_raw = h.get("rate_per_night", {}).get("lowest", "")
        precio_num = int("".join(filter(str.isdigit, str(precio_raw)))) if precio_raw else 0
        nombre_encoded = urllib.parse.quote(h.get("name", "") + " Barcelona")
        google_url = f"https://www.google.com/search?q={nombre_encoded}+precio+hotel+{checkin}"
        result.append({
            "nombre": h.get("name", ""),
            "estrellas": f"{int(h.get('star_rating', 3))}★",
            "precio": precio_num,
            "rating": h.get("overall_rating", ""),
            "url": google_url,
        })
    return result

# ── Eventos del día (datos de ejemplo — conectar PredictHQ en producción) ────
def get_eventos():
    return [
        {"texto": "🎵 Primavera Sound — Parc del Fòrum (60.000 asistentes)", "url": "https://www.primaverasound.com"},
        {"texto": "🏥 Congreso médico EULAR — Fira Barcelona (3.200 asistentes)", "url": "https://eular.org"},
        {"texto": "🎨 Exposición Dalí — Fundació Joan Miró", "url": "https://www.fmirobcn.org"},
    ]

# ── Main ──────────────────────────────────────────────────────────────────────
print("🔍 Obteniendo precios reales de competidores...")
competidores = get_competidores()
eventos = get_eventos()

precios = [c["precio"] for c in competidores if c["precio"] > 0]
precio_medio = sum(precios) / len(precios) if precios else 0

# Recomendación con Claude
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
prompt = f"""Eres experto en revenue management hotelero.
Hotel: {HOTEL_CLIENTE}, precio actual: {PRECIO_CLIENTE}€
Precio medio competencia: {precio_medio:.0f}€
Eventos hoy: {', '.join(e['texto'] for e in eventos)}
Escribe UNA frase de recomendación de precio. Máximo 15 palabras. Directa. En español."""

msg = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=80,
    messages=[{"role": "user", "content": prompt}]
)
recomendacion = msg.content[0].text.strip()

# Construir mensaje
lineas_comp = ""
for c in competidores:
    if c["precio"] == 0:
        continue
    emoji = "🔴" if c["precio"] > PRECIO_CLIENTE * 1.3 else "🟡" if c["precio"] > PRECIO_CLIENTE else "🟢"
    lineas_comp += f"{emoji} *{c['nombre']}* {c['estrellas']} — {c['precio']}€ → {c['url']}\n"

lineas_eventos = ""
for e in eventos:
    lineas_eventos += f"{e['texto']} → {e['url']}\n"

whatsapp_msg = f"""📊 *Informe diario — {HOTEL_CLIENTE}*
_{fecha_texto}_

🏨 *Competidores mañana ({checkin}):*
{lineas_comp}
💰 *Tú estás a:* {PRECIO_CLIENTE}€
📈 *Media competencia:* {precio_medio:.0f}€

💡 *Recomendación IA:*
_{recomendacion}_

🗓️ *Eventos en Barcelona:*
{lineas_eventos}
📧 Informe completo enviado a tu email."""

print("\n" + "=" * 60)
print(whatsapp_msg)
print("=" * 60)

print("\n📲 Enviando WhatsApp...")
twilio = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
twilio.messages.create(body=whatsapp_msg, from_=TWILIO_FROM, to=MANAGER_WHATSAPP)
print("✅ Enviado.")
