"""
Hospera Boost Review — pide la reseña al huésped el día de salida, y si la
estancia dura más de una noche, manda un aviso a mitad de estancia para
detectar problemas antes de que se vaya (nunca selecciona a quién escribir
según lo contento que esté — se manda a todos, ver docs/formulario_checkin.md).

Lee el CSV publicado de la Sheet de check-ins de cada cliente (ver
docs/formulario_checkin.md para cómo publicarla), calcula qué huéspedes
tocan hoy, y manda el mensaje por SMS si tenemos su teléfono, o por email
si solo tenemos su email de la reserva.

Uso:
  python3 guest_followup.py          # corre de verdad
  python3 guest_followup.py --test   # no manda nada, solo imprime qué mandaría
"""
import sys
sys.path.insert(0, '/Users/andreurey/Library/Python/3.9/lib/python/site-packages')

import os, csv, io, json, argparse, smtplib
from datetime import datetime, date, timedelta
from pathlib import Path
from email.mime.text import MIMEText

import requests
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.expanduser('~/hospera/.env'))

TWILIO_SID         = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_TOKEN       = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_SMS_FROM    = os.getenv('TWILIO_SMS_FROM')  # número propio de SMS — pendiente de Twilio
EMAIL_ADDRESS      = os.getenv('EMAIL_ADDRESS')
EMAIL_APP_PASSWORD = os.getenv('EMAIL_APP_PASSWORD')

STATE_DIR = Path.home() / 'hospera' / 'guest_state'
STATE_DIR.mkdir(exist_ok=True)

# ── Clientes con Boost Review activado ──────────────────────────────────────
# Cada uno necesita su Sheet de check-ins publicada como CSV (ver
# docs/formulario_checkin.md) y la página de elección de plataforma ya
# generada con generate_choice_page.py (carpeta r/, desplegada en Netlify).
# Todavía no hay ningún cliente real dado de alta — se añade así en cuanto
# lo haya:
#
# CHECKIN_CLIENTS = [
#     {
#         "name":             "Uma House",
#         "slug":              "uma-house",           # r/uma-house.html
#         "checkin_sheet_url": "https://docs.google.com/.../pub?output=csv",
#         "hotel_whatsapp":    "13055551234",           # para el enlace de "algo va mal", sin '+'
#         "state":             STATE_DIR / "uma-house.json",
#     },
# ]
CHECKIN_CLIENTS = []

REVIEW_LINK_BASE = "https://hosperai.es/r"

LANG_ALIASES = {
    "español": "es", "espanol": "es", "castellano": "es",
    "english": "en",
    "català": "ca", "catala": "ca",
}

MESSAGES = {
    "departure": {
        "es": "¡Hola {name}! Gracias por tu estancia en {business}. Si tienes un minuto, nos encantaría leer tu opinión: {link}",
        "en": "Hi {name}! Thanks for staying at {business}. If you have a minute, we'd love to hear your feedback: {link}",
    },
    "midstay": {
        "es": "Hola {name}, esperamos que tu estancia en {business} esté yendo genial. Si algo no está siendo perfecto, dínoslo aquí y lo arreglamos ahora mismo: {link}",
        "en": "Hi {name}, hope your stay at {business} is going great so far. If anything isn't quite right, let us know here and we'll fix it right away: {link}",
    },
}

EMAIL_SUBJECTS = {
    "departure": {"es": "¿Qué tal tu estancia en {business}?", "en": "How was your stay at {business}?"},
    "midstay":   {"es": "¿Va todo bien en {business}?", "en": "Is everything going well at {business}?"},
}


def normalize_lang(raw):
    key = (raw or "").strip().lower()
    return LANG_ALIASES.get(key, key if key in ("es", "en", "ca") else "en")


def parse_date(raw):
    raw = (raw or "").strip()
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def fetch_checkins(sheet_url):
    r = requests.get(sheet_url, timeout=15)
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO(r.text))
    guests = []
    for row in reader:
        def get_field(*needles):
            for key, val in row.items():
                if key and any(n in key.lower() for n in needles):
                    return val
            return ""

        name = get_field("nombre")
        phone = get_field("teléfono", "telefono", "phone")
        email = get_field("email", "correo", "e-mail")
        lang = normalize_lang(get_field("idioma", "language"))
        checkin = parse_date(get_field("entrada", "check-in", "checkin"))
        checkout = parse_date(get_field("salida", "check-out", "checkout"))

        if not (name and checkout and (phone or email)):
            continue
        guests.append({
            "name": name.strip(),
            "phone": phone.strip(),
            "email": email.strip(),
            "lang": lang,
            "checkin": checkin,
            "checkout": checkout,
        })
    return guests


def guest_key(guest):
    return f"{guest['phone']}_{guest['email']}_{guest['checkin']}_{guest['checkout']}"


def load_state(path):
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_state(path, state):
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def send_sms(to_phone, body, test_mode=False):
    if test_mode or not TWILIO_SMS_FROM:
        reason = "[TEST]" if test_mode else "[SIN NÚMERO SMS CONFIGURADO]"
        print(f"    {reason} SMS a {to_phone}: {body}")
        return
    twilio = Client(TWILIO_SID, TWILIO_TOKEN)
    twilio.messages.create(body=body, from_=TWILIO_SMS_FROM, to=to_phone)
    print(f"    ✅ SMS enviado a {to_phone}")


def send_email(to_addr, subject, body, test_mode=False):
    if test_mode or not (EMAIL_ADDRESS and EMAIL_APP_PASSWORD):
        reason = "[TEST]" if test_mode else "[SIN CREDENCIALES DE EMAIL CONFIGURADAS]"
        print(f"    {reason} Email a {to_addr}: {subject} — {body}")
        return
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_addr
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.send_message(msg)
    print(f"    ✅ Email enviado a {to_addr}")


def notify_guest(guest, kind, body, lang, business_name, test_mode=False):
    """Manda por SMS si hay teléfono; si no, por email si lo hay. Si no hay
    ninguno de los dos, no se manda nada (no debería pasar, fetch_checkins
    ya exige al menos uno)."""
    if guest['phone']:
        send_sms(guest['phone'], body, test_mode)
    elif guest['email']:
        subject = EMAIL_SUBJECTS[kind][lang].format(business=business_name)
        send_email(guest['email'], subject, body, test_mode)
    else:
        print(f"    ⚠️  {guest['name']}: sin teléfono ni email, no se puede avisar")


def run_client(client, test_mode=False):
    print(f"\n  📍 {client['name']}")
    try:
        guests = fetch_checkins(client['checkin_sheet_url'])
    except Exception as e:
        print(f"  ⚠️  Error leyendo la hoja de check-ins: {e}")
        return

    state = load_state(client['state'])
    today = date.today()
    review_link = f"{REVIEW_LINK_BASE}/{client['slug']}.html"
    sent = 0

    for guest in guests:
        key = guest_key(guest)
        record = state.setdefault(key, {})
        lang = guest['lang'] if guest['lang'] in ("es", "en") else "en"

        if guest['checkout'] == today and not record.get('departure_sent'):
            body = MESSAGES['departure'][lang].format(name=guest['name'], business=client['name'], link=review_link)
            notify_guest(guest, 'departure', body, lang, client['name'], test_mode)
            record['departure_sent'] = True
            sent += 1

        nights = (guest['checkout'] - guest['checkin']).days if guest['checkin'] else 0
        if nights > 1:
            midpoint = guest['checkin'] + timedelta(days=nights // 2)
            if midpoint == today and not record.get('midstay_sent'):
                contact_link = f"https://wa.me/{client['hotel_whatsapp']}" if client.get('hotel_whatsapp') else review_link
                body = MESSAGES['midstay'][lang].format(name=guest['name'], business=client['name'], link=contact_link)
                notify_guest(guest, 'midstay', body, lang, client['name'], test_mode)
                record['midstay_sent'] = True
                sent += 1

    save_state(client['state'], state)
    if sent == 0:
        print("  Nadie que avisar hoy.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()

    print(f"\n🌱 Hospera Boost Review — {len(CHECKIN_CLIENTS)} clientes con check-in activado")
    if not CHECKIN_CLIENTS:
        print("  (todavía no hay ningún cliente configurado en CHECKIN_CLIENTS)")
        return

    for client in CHECKIN_CLIENTS:
        run_client(client, test_mode=args.test)


if __name__ == '__main__':
    main()
