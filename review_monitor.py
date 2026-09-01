"""
Hospera Review Monitor — Detecta reseñas nuevas via SerpAPI y manda respuesta IA al WhatsApp
Sin necesidad de Google Business Profile API. Soporta múltiples clientes.

Uso:
  python3 review_monitor.py          # corre en bucle
  python3 review_monitor.py --once   # ejecuta una vez y sale
  python3 review_monitor.py --test   # busca reseñas sin mandar WhatsApp
"""
import sys
sys.path.insert(0, '/Users/andreurey/Library/Python/3.9/lib/python/site-packages')

import os, json, time, argparse, requests
from datetime import datetime
from pathlib import Path

import anthropic
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.expanduser('~/hospera/.env'))

SERPAPI_KEY   = os.getenv('SERPAPI_KEY')
TWILIO_SID    = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_TOKEN  = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_FROM   = os.getenv('TWILIO_WHATSAPP_FROM')
ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY')

POLL_MINUTES  = 60
MAPS_URL      = "https://business.google.com/reviews"

PLATFORM_LABEL = {"google": "Google", "tripadvisor": "TripAdvisor"}

# ── Lista de clientes ───────────────────────────────────────────────────────
# "tripadvisor_id" es opcional — el place_id de TripAdvisor (se saca vía
# engine=tripadvisor buscando el nombre del negocio). Si no está, ese cliente
# solo se monitoriza en Google.
CLIENTS = [
    {
        "name":      "Arreu Begur",
        "data_id":   "0x12ba5310555fc1dd:0x8ce823369100106f",
        "tripadvisor_id": None,
        "type":      "restaurante",
        "signature": "El equipo de Arreu",
        "phone":     "whatsapp:+34670090382",
        "state":     Path.home() / 'hospera/seen_arreu.json',
        "notify_lang": "es",
        "manager_email": "andreurey7@gmail.com",
    },
    {
        "name":      "Racó'ns Chiringuito",
        "data_id":   "0x12ba515784b6cf7d:0x1327c62177a28f30",
        "tripadvisor_id": None,
        "type":      "chiringuito",
        "signature": "El equipo de Racó'ns",
        "phone":     "whatsapp:+34670090382",
        "state":     Path.home() / 'hospera/seen_racons.json',
        "notify_lang": "es",
        "manager_email": "andreurey7@gmail.com",
    },
]


def load_seen(path):
    if path.exists():
        return json.loads(path.read_text())
    return {}

def save_seen(path, seen):
    path.write_text(json.dumps(seen, indent=2, ensure_ascii=False))

def mark_seen(seen, uid, rating=None, notified=False):
    seen[uid] = {
        "date":     datetime.now().isoformat(),
        "rating":   float(rating) if rating else None,
        "notified": notified,
    }

def get_reviews(data_id):
    params = {
        "engine":    "google_maps_reviews",
        "data_id":   data_id,
        "api_key":   SERPAPI_KEY,
        "hl":        "es",
        "sort_by":   "newestFirst"
    }
    r = requests.get("https://serpapi.com/search", params=params, timeout=15)
    data = r.json()
    if "error" in data:
        raise Exception(f"SerpAPI error: {data['error']}")
    return data.get("reviews", [])

def get_reviews_paginated(data_id, max_pages=2):
    """Trae varias páginas de reseñas (más gasto de cuota SerpAPI) para poder
    comparar meses. Usar con moderación — pensado para el informe mensual, no el sondeo diario."""
    all_reviews = []
    params = {
        "engine":    "google_maps_reviews",
        "data_id":   data_id,
        "api_key":   SERPAPI_KEY,
        "hl":        "es",
        "sort_by":   "newestFirst"
    }
    for _ in range(max_pages):
        r = requests.get("https://serpapi.com/search", params=params, timeout=15)
        data = r.json()
        if "error" in data:
            raise Exception(f"SerpAPI error: {data['error']}")
        all_reviews.extend(data.get("reviews", []))
        next_token = data.get("serpapi_pagination", {}).get("next_page_token")
        if not next_token:
            break
        params = {**params, "next_page_token": next_token}
    return all_reviews

def get_tripadvisor_reviews(place_id):
    params = {
        "engine":   "tripadvisor_reviews",
        "place_id": place_id,
        "api_key":  SERPAPI_KEY,
    }
    r = requests.get("https://serpapi.com/search", params=params, timeout=15)
    data = r.json()
    if "error" in data:
        raise Exception(f"SerpAPI error: {data['error']}")
    return data.get("reviews", [])

def normalize_review(raw, platform):
    """Homogeneiza reseñas de Google y TripAdvisor a un formato común."""
    if platform == "google":
        uid = raw.get("review_id") or (
            raw.get("iso_date", "") + "_" + raw.get("user", {}).get("name", "")
        )
        author = raw.get("user", {}).get("name", "Anónimo")
        text = (
            raw.get("snippet")
            or raw.get("extracted_snippet", {}).get("original", "")
            or ""
        ).strip()
    else:  # tripadvisor
        review_id = raw.get("review_id")
        uid = f"tripadvisor_{review_id}" if review_id else None
        author = raw.get("author", {}).get("display_name", "Anónimo")
        text = (raw.get("snippet") or "").strip()

    return {
        "uid":      uid,
        "rating":   raw.get("rating"),
        "text":     text,
        "author":   author,
        "response": raw.get("response"),
        "link":     raw.get("link"),
        "platform": platform,
    }

def client_platforms(client):
    platforms = [("google", client["data_id"])]
    if client.get("tripadvisor_id"):
        platforms.append(("tripadvisor", client["tripadvisor_id"]))
    return platforms

def fetch_platform_reviews(platform, pid):
    raw = get_reviews(pid) if platform == "google" else get_tripadvisor_reviews(pid)
    return [normalize_review(r, platform) for r in raw]

def infer_onboarded_platforms(seen):
    """Los seen.json de clientes ya activos antes de añadir TripAdvisor no
    tienen '_meta' — si ya hay claves de Google sin prefijo, asumimos que
    Google ya pasó por onboarding para no repetir el resumen de bienvenida."""
    onboarded = set(seen.get("_meta", {}).get("onboarded_platforms", []))
    if "google" not in onboarded and any(
        k != "_meta" and not k.startswith("tripadvisor_") for k in seen
    ):
        onboarded.add("google")
    return onboarded

def mark_platform_onboarded(seen, platform):
    meta = seen.setdefault("_meta", {})
    onboarded = set(meta.get("onboarded_platforms", []))
    onboarded.add(platform)
    meta["onboarded_platforms"] = sorted(onboarded)

def generate_response(client, author, rating, text, platform="google"):
    ai = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    notify_lang = client.get('notify_lang')

    translate_instructions = ""
    if notify_lang:
        translate_instructions = f"""

Después de la respuesta, si la reseña NO está ya en el idioma '{notify_lang}', añade dos bloques (si ya está en ese idioma, no los añadas):
---TRADUCCION_RESEÑA---
(traducción de la reseña original al idioma '{notify_lang}')
---TRADUCCION_RESPUESTA---
(traducción de tu respuesta al idioma '{notify_lang}')"""

    prompt = f"""Eres el responsable de {client['name']}, un {client['type']} en Begur, Costa Brava.
Responde a esta reseña de {PLATFORM_LABEL.get(platform, 'Google')} de forma profesional, cálida y personalizada.
Escribe la respuesta en el mismo idioma que la reseña original (esto no cambia). Máximo 3 frases. No empieces con frases genéricas.
Firma como: {client['signature']}{translate_instructions}

Autor: {author}
Valoración: {int(rating) if rating else 5}/5
Reseña: {text}"""

    response = ai.messages.create(
        model="claude-haiku-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text.strip()

    reply, review_translated, reply_translated = raw, None, None
    if "---TRADUCCION_RESEÑA---" in raw:
        reply, rest = raw.split("---TRADUCCION_RESEÑA---", 1)
        reply = reply.strip()
        if "---TRADUCCION_RESPUESTA---" in rest:
            review_translated, reply_translated = rest.split("---TRADUCCION_RESPUESTA---", 1)
            review_translated, reply_translated = review_translated.strip(), reply_translated.strip()
        else:
            review_translated = rest.strip()

    return reply, review_translated, reply_translated

LOW_RATING_THRESHOLD = 3  # ⭐ y por debajo se marca como urgente

def send_whatsapp(client, author, rating, text, response_text, review_translated=None, reply_translated=None, review_link=None, platform="google"):
    twilio = Client(TWILIO_SID, TWILIO_TOKEN)
    rating_val = float(rating) if rating else 0
    stars = "⭐" * int(rating) if rating else "—"
    text_short     = text[:400] + "..." if len(text) > 400 else text
    response_short = response_text[:500] + "..." if len(response_text) > 500 else response_text
    platform_label = PLATFORM_LABEL.get(platform, "Google")

    review_block = f"_{text_short}_"
    if review_translated:
        review_block += f"\n🇪🇸 _{review_translated[:400]}_"

    response_block = f"_{response_short}_"
    if reply_translated:
        response_block += f"\n🇪🇸 _{reply_translated[:500]}_"

    reply_url = review_link or MAPS_URL

    is_urgent = rating_val and rating_val <= LOW_RATING_THRESHOLD
    header = (
        f"🚨 *Hospera* · reseña negativa en *{client['name']}* ({platform_label}) — requiere atención"
        if is_urgent else
        f"✨ *Hospera* · nueva reseña en *{client['name']}* ({platform_label})"
    )

    msg = f"""{header}
────────────────
{stars}  *{author}*
{review_block}

💬 *Respuesta sugerida:*
{response_block}
────────────────
👉 Copia y pega la respuesta aquí para publicarla:
{reply_url}

_Hospera responde por ti — tú solo confirmas._"""

    twilio.messages.create(body=msg, from_=TWILIO_FROM, to=client['phone'])
    print(f"  ✅ WhatsApp enviado a {client['phone']}{' [URGENTE]' if is_urgent else ''}")

def send_onboarding_summary(client, platform, total, backlog, negative_backlog):
    twilio = Client(TWILIO_SID, TWILIO_TOKEN)
    platform_label = PLATFORM_LABEL.get(platform, "Google")
    msg = f"""✨ *Hospera* activado en *{client['name']}* ({platform_label})
────────────────
He revisado el histórico de reseñas recientes:
📋 {total} reseñas encontradas
✍️ {backlog} sin respuesta del negocio
{"🚨 " + str(negative_backlog) + " de ellas son negativas (≤" + str(LOW_RATING_THRESHOLD) + "⭐)" if negative_backlog else "🎉 ninguna negativa pendiente"}
────────────────
No te voy a avisar una por una de este histórico para no saturarte. A partir de ahora, te aviso solo de las reseñas nuevas que vayan llegando."""

    twilio.messages.create(body=msg, from_=TWILIO_FROM, to=client['phone'])
    print(f"  ✅ Resumen de bienvenida ({platform_label}) enviado a {client['phone']}")

def run_platform(client, platform, reviews, seen, onboarded, test_mode=False, max_new=None):
    """Procesa las reseñas normalizadas de una plataforma para un cliente.
    Devuelve cuántas se notificaron. Modifica seen y onboarded in-place."""
    found = 0

    if platform not in onboarded:
        print(f"  🆕 Primer run en {PLATFORM_LABEL.get(platform, platform)} — modo onboarding")
        backlog, negative_backlog = 0, 0
        for review in reviews:
            uid = review["uid"]
            if not uid:
                continue
            rating = review["rating"] or 0
            mark_seen(seen, uid, rating=rating, notified=False)
            if not review["response"]:
                backlog += 1
                if float(rating) and float(rating) <= LOW_RATING_THRESHOLD:
                    negative_backlog += 1
        mark_platform_onboarded(seen, platform)
        save_seen(client['state'], seen)
        print(f"  📋 {len(reviews)} reseñas en el histórico, {backlog} sin responder ({negative_backlog} negativas)")
        if not test_mode:
            send_onboarding_summary(client, platform, len(reviews), backlog, negative_backlog)
        else:
            print(f"  [TEST] Resumen de bienvenida no enviado")
        return 0

    for review in reviews:
        uid = review["uid"]
        if not uid or uid in seen:
            continue

        if review["response"]:
            # Ya respondida por el negocio (a mano, o en un canal externo) — no notificar
            mark_seen(seen, uid, rating=review["rating"], notified=False)
            save_seen(client['state'], seen)
            continue

        author, rating, text = review["author"], review["rating"] or 5, review["text"]

        if not text:
            mark_seen(seen, uid, rating=rating, notified=False)
            save_seen(client['state'], seen)
            continue

        print(f"  → [{PLATFORM_LABEL.get(platform, platform)}] {author} ({rating}⭐): {text[:70]}...")
        response_text, review_tr, reply_tr = generate_response(client, author, rating, text, platform)
        print(f"  → IA: {response_text[:70]}...")
        if review_tr:
            print(f"  → Traducción reseña: {review_tr[:70]}...")

        if not test_mode:
            send_whatsapp(client, author, rating, text, response_text, review_tr, reply_tr, review["link"], platform)
        else:
            print(f"  [TEST] WhatsApp no enviado")

        mark_seen(seen, uid, rating=rating, notified=True)
        save_seen(client['state'], seen)
        found += 1
        time.sleep(2)
        if max_new and found >= max_new:
            break

    return found

def run_client(client, test_mode=False, max_new=None):
    print(f"\n  📍 {client['name']}")
    seen = load_seen(client['state'])
    onboarded = infer_onboarded_platforms(seen)
    if onboarded != set(seen.get('_meta', {}).get('onboarded_platforms', [])):
        for platform in onboarded:
            mark_platform_onboarded(seen, platform)
        save_seen(client['state'], seen)
    total_found = 0

    for platform, pid in client_platforms(client):
        try:
            reviews = fetch_platform_reviews(platform, pid)
        except Exception as e:
            print(f"  ⚠️  Error en {PLATFORM_LABEL.get(platform, platform)}: {e}")
            continue
        total_found += run_platform(client, platform, reviews, seen, onboarded, test_mode, max_new)

    if total_found == 0:
        print(f"  Sin reseñas nuevas.")
    return total_found

def run(test_mode=False):
    print(f"[{datetime.now().strftime('%H:%M')}] Revisando {len(CLIENTS)} negocios...")
    for client in CLIENTS:
        try:
            run_client(client, test_mode, max_new=3)
        except Exception as e:
            print(f"  ⚠️  Error en {client['name']}: {e}")
        time.sleep(3)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()

    print(f"\n🏨 Hospera Review Monitor — {len(CLIENTS)} clientes")
    print(f"⏱️  Revisando cada {POLL_MINUTES} min\n")

    if args.once or args.test:
        run(test_mode=args.test)
        return

    while True:
        try:
            run()
        except Exception as e:
            print(f"⚠️  Error: {e}")
        print(f"\nPróxima revisión en {POLL_MINUTES} min...")
        time.sleep(POLL_MINUTES * 60)

if __name__ == '__main__':
    main()
