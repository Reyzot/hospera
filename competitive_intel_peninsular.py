import sys
sys.path.insert(0, '/Users/andreurey/Library/Python/3.9/lib/python/site-packages')

from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import anthropic
import requests
import time
import re
import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.expanduser('~/hospera/.env'))

TWILIO_SID    = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_TOKEN  = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_FROM   = os.getenv('TWILIO_WHATSAPP_FROM')
MANAGER_PHONE = os.getenv('MANAGER_WHATSAPP')
ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY')

TARGET = {
    "name": "Hotel Peninsular",
    "slug": "peninsular",
    "stars": "1★",
    "price": 125  # precio actual del hotel — actualizar según tarifa
}

COMPETITORS = [
    {"name": "Hotel España",       "slug": "espana-barcelona",      "stars": "3★"},
    {"name": "Hotel Gaudí",        "slug": "gaudi-barcelona",       "stars": "3★"},
    {"name": "Hotel Continental",  "slug": "continental-barcelona", "stars": "3★"},
    {"name": "Hostal Centric",     "slug": "centric-barcelona",     "stars": "2★"},
    {"name": "Hostal Goya",        "slug": "hostal-goya",           "stars": "2★"},
]

TOMORROW     = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
DAY_AFTER    = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
TODAY_LABEL  = datetime.now().strftime('%A %d %B %Y')


def get_price(page, slug):
    url = f"https://www.booking.com/hotel/es/{slug}.es.html?checkin={TOMORROW}&checkout={DAY_AFTER}&group_adults=2&no_rooms=1"
    try:
        page.goto(url, timeout=25000, wait_until="domcontentloaded")
        time.sleep(3)

        for sel in ['#onetrust-accept-btn-handler', "[aria-label='Dismiss sign-in info.']", "[aria-label='Cerrar']"]:
            try:
                page.click(sel, timeout=1500)
                time.sleep(0.5)
            except:
                pass

        for sel in [
            '[data-testid="price-and-discounted-price"]',
            '.prco-valign-middle-helper',
            '.bui-price-display__value',
        ]:
            try:
                text = page.locator(sel).first.inner_text(timeout=4000)
                match = re.search(r'[\d]+', text.replace(',', '').replace('.', ''))
                if match:
                    price = int(match.group())
                    if 20 < price < 2000:
                        return price
            except:
                pass

        content = page.content()
        matches = re.findall(r'€\s*(\d{2,4})', content)
        prices = [int(p) for p in matches if 30 < int(p) < 1500]
        if prices:
            mn, mx = min(prices), max(prices)
            return (mn, mx) if mx > mn + 10 else mn

    except:
        pass
    return None


def get_google_rating(name, location="Barcelona, Spain"):
    """Busca el negocio por nombre en Google Maps y devuelve su rating/nº de
    reseñas actuales. No hace falta guardar un data_id fijo por competidor —
    esto es solo una foto rápida de reputación, no seguimiento de reseña a
    reseña como en review_monitor.py."""
    key = os.getenv('SERPAPI_KEY')
    if not key:
        return None
    try:
        params = {"engine": "google_maps", "q": f"{name} {location}", "type": "search", "api_key": key}
        r = requests.get("https://serpapi.com/search", params=params, timeout=10)
        data = r.json()
        results = data.get("local_results", [])
        top = results[0] if results else data.get("place_results", {})
        if top.get("rating"):
            return {"rating": top["rating"], "reviews": top.get("reviews", 0)}
    except Exception:
        pass
    return None


def get_barcelona_events():
    key = os.getenv('SERPAPI_KEY')
    if not key:
        return []
    try:
        params = {
            "engine": "google_events",
            "q": f"concierto festival congreso feria Barcelona {TOMORROW}",
            "location": "Barcelona, Spain",
            "hl": "es",
            "api_key": key
        }
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        data = response.json()
        events = []
        for event in data.get("events_results", [])[:4]:
            name = event.get("title", "")
            date = event.get("date", {}).get("start_date", TOMORROW)
            link = event.get("link", "")
            if name:
                events.append({"name": name, "date": date, "link": link})
        return events
    except:
        return []


def get_ai_recommendation(target_price, comp_results, events):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    valid = [c for c in comp_results if c['price']]
    avg = round(sum(c['price'] for c in valid) / len(valid)) if valid else 0

    prompt = f"""Eres un asesor de revenue management para hoteles pequeños independientes en Barcelona.
Hotel: {TARGET['name']} ({TARGET['stars']}, zona Ramblas) — precio actual: {target_price}€
Competidores directos mañana: {', '.join([f"{c['name']}: {c['price']}€" for c in valid])}
Media competencia: {avg}€
Eventos relevantes: {events if events else 'ninguno destacable'}

Da una recomendación práctica y realista en 1-2 frases cortas. Sé conservador — solo sugiere subir precio si hay una razón clara. No exageres. Menciona una cifra concreta si aplica."""

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()


def send_whatsapp(msg):
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    client.messages.create(body=msg, from_=TWILIO_FROM, to=MANAGER_PHONE)
    print("✅ WhatsApp enviado.")


def main():
    print(f"\n🔍 Competitive Intel — {TODAY_LABEL}")
    print(f"📅 Analizando precios para: {TOMORROW}\n")

    comp_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 900},
            locale='es-ES'
        )
        page = context.new_page()

        for comp in COMPETITORS:
            print(f"Scraping: {comp['name']}...")
            price = get_price(page, comp['slug'])
            comp_results.append({**comp, 'price': price})
            print(f"  → €{price}" if price else "  → Sin precio")
            time.sleep(2)

        browser.close()

    print("\nConsultando reputación en Google...")
    target_rating = get_google_rating(TARGET['name'])
    for c in comp_results:
        c['google'] = get_google_rating(c['name'])
        time.sleep(1)

    target_price = TARGET['price']
    valid_comps = [c for c in comp_results if c['price']]
    avg_comp = round(sum(c['price'] for c in valid_comps) / len(valid_comps)) if valid_comps else 0

    # Buscar eventos reales con SerpAPI
    events = get_barcelona_events()

    print("\nGenerando recomendación IA...")
    rec = get_ai_recommendation(target_price, comp_results, events)

    # Construir mensaje
    lines = []
    lines.append(f"📊 *Informe diario — Hosperai*")
    lines.append(f"_{TODAY_LABEL}_\n")
    lines.append(f"🏨 *Competidores mañana ({TOMORROW}):*")

    for c in comp_results:
        if c['price']:
            search_url = f"https://www.booking.com/hotel/es/{c['slug']}.es.html?checkin={TOMORROW}&checkout={DAY_AFTER}&group_adults=2&no_rooms=1"
            price_data = c['price']
            if isinstance(price_data, tuple):
                price_str = f"{price_data[0]}€–{price_data[1]}€"
                diff = price_data[0] - target_price
            else:
                price_str = f"{price_data}€"
                diff = price_data - target_price
            emoji = "🔴" if diff > 30 else "🟡" if diff > 0 else "🟢"
            lines.append(f"{emoji} *{c['name']}* {c['stars']} — {price_str} → {search_url}")
        else:
            lines.append(f"⚫ *{c['name']}* {c['stars']} — sin datos")

    lines.append(f"\n💰 *Tú estás a:* {target_price}€")
    lines.append(f"📈 *Media competencia:* {avg_comp}€\n")
    lines.append(f"💡 *Recomendación IA:*")
    lines.append(f"_{rec}_")

    rated_comps = [c for c in comp_results if c.get('google')]
    if target_rating or rated_comps:
        lines.append(f"\n⭐ *Tu reputación vs. la competencia:*")
        if target_rating:
            lines.append(f"🏨 *{TARGET['name']}:* {target_rating['rating']}⭐ ({target_rating['reviews']} reseñas)")
        for c in rated_comps:
            lines.append(f"   {c['name']}: {c['google']['rating']}⭐ ({c['google']['reviews']} reseñas)")
        if target_rating and rated_comps:
            comp_avg_rating = round(sum(c['google']['rating'] for c in rated_comps) / len(rated_comps), 1)
            if target_rating['rating'] < comp_avg_rating:
                lines.append(f"   ⚠️ Vas por debajo de la media de la zona ({comp_avg_rating}⭐)")
            else:
                lines.append(f"   ✅ Vas por encima de la media de la zona ({comp_avg_rating}⭐)")

    if events:
        lines.append(f"\n🗓️ *Eventos en Barcelona ({TOMORROW}):*")
        for e in events:
            link_part = f" → {e['link']}" if e['link'] else ""
            lines.append(f"📍 *{e['name']}* — {e['date']}{link_part}")

    msg = '\n'.join(lines)
    print(f"\n{'='*50}")
    print(msg)
    print(f"{'='*50}\n")

    send_whatsapp(msg)


if __name__ == '__main__':
    main()
