"""
Hosperai Boost Review — mensajes a huéspedes de los hoteles activos con "Get more reviews".

Recepción registra a cada huésped en https://app.hosperai.es/checkin/?h=<hotel>&t=<token>.
Este script (launchd, cada 30 min de 9:00 a 21:00) lee esos huéspedes y manda:
  - día de salida (desde las 11:00): agradecimiento + enlace de reseña (VIP: con el mensaje VIP del hotel)
  - estancias de más de 2 noches: a mitad de estancia, "¿va todo bien?" con el WhatsApp del hotel
Canal: WhatsApp (plantilla aprobada por Meta) → email si el número no tiene WhatsApp.
Solo se marca "enviado" cuando WhatsApp confirma la entrega; si no, se reintenta (hasta 2 días después).

  python3 guest_followup.py          # corre de verdad
  python3 guest_followup.py --test   # no manda nada, solo imprime qué mandaría
"""
import sys
sys.path.insert(0, '/Users/andreurey/Library/Python/3.9/lib/python/site-packages')

import os, json, re, time, argparse, smtplib
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
TWILIO_WA_FROM     = os.getenv('TWILIO_GUEST_WHATSAPP_FROM')  # WhatsApp Business de Hosperai
WA_TEMPLATES = json.loads((Path.home() / 'hospera' / 'whatsapp_templates.json').read_text()) if (Path.home() / 'hospera' / 'whatsapp_templates.json').exists() else {}
WA_TEMPLATE_BY_KIND = {"departure": "hosperai_thanks", "midstay": "hosperai_midstay"}
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
CHECKIN_API = "https://app.hosperai.es/api/checkin"
CHECKIN_SECRET = os.getenv('CHECKIN_SECRET', '')
_CLIENTS_FILE = Path.home() / 'hospera' / 'clients.json'
CHECKIN_CLIENTS = [
    {"name": c["name"], "slug": c["slug"], "hotel_whatsapp": c["phone"].replace("whatsapp:+", ""), "vip_message": c.get("vip_message", ""),
     "review_links": c.get("review_links") or {},
     "state": STATE_DIR / f"{c['slug']}.json"}
    for c in (json.loads(_CLIENTS_FILE.read_text()) if _CLIENTS_FILE.exists() else [])
    if c.get("status") == "active" and "Get more reviews" in (c.get("services") or [])
]
SEND_AFTER_HOUR = 11  # el mensaje de salida no se manda antes de las 11:00 (hora del Mac)

REVIEW_LINK_BASE = "https://hosperai.es/r"

LANG_ALIASES = {
    "español": "es", "espanol": "es", "castellano": "es", "català": "es", "catala": "es",
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


def fetch_checkins(slug):
    r = requests.get(CHECKIN_API, params={"h": slug, "key": CHECKIN_SECRET}, timeout=20)
    r.raise_for_status()
    guests = []
    for g in r.json():
        checkout = parse_date(g.get("checkout"))
        if not (g.get("name") and checkout and (g.get("phone") or g.get("email"))):
            continue
        guests.append({
            "name": (lambda n: n.capitalize() if n.islower() else n)(g["name"].strip().split(" ")[0]),
            "phone": re.sub(r"[^\d+]", "", g.get("phone") or ""),
            "email": (g.get("email") or "").strip(),
            "lang": normalize_lang(g.get("lang")),
            "checkin": parse_date(g.get("checkin")),
            "checkout": checkout,
            "id": g.get("id"),
            "vip": bool(g.get("vip")),
            "departure_sent": g.get("departure_sent"),
            "midstay_sent": g.get("midstay_sent"),
        })
    return guests


def mark_sent(slug, guest_id, field, via):
    """Lo marca como enviado en la lista que ve recepción (pestaña Guests → Sent)."""
    try:
        requests.post(CHECKIN_API, json={"action": "mark", "key": CHECKIN_SECRET, "h": slug, "id": guest_id,
                                         "field": field, "via": via}, timeout=20).raise_for_status()
    except Exception as e:
        print(f"    ⚠️  No pude marcarlo como enviado en la web: {e}")


def guest_key(guest):
    return guest.get('id') or f"{guest['phone']}_{guest['email']}_{guest['checkin']}_{guest['checkout']}"


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


_APPROVED = None


def template_approved(sid):
    """Solo se envía con plantillas que Meta ya ha aprobado (si no, Twilio las acepta y luego no las entrega)."""
    global _APPROVED
    if _APPROVED is None:
        try:
            r = requests.get("https://content.twilio.com/v1/ContentAndApprovals", auth=(TWILIO_SID, TWILIO_TOKEN), timeout=20).json()
            _APPROVED = {c["sid"] for c in r.get("contents", []) if (c.get("approval_requests") or {}).get("status") == "approved"}
        except Exception:
            _APPROVED = set()
    return sid in _APPROVED


NO_WHATSAPP_ERRORS = {63003, 63024}  # el número no tiene WhatsApp


def send_whatsapp(to_phone, kind, lang, variables, test_mode=False, template=None):
    """Devuelve "sent", "no_whatsapp" (probar email) o "retry" (plantilla sin aprobar / fallo temporal: no marcar, reintentar)."""
    template = template or f"{WA_TEMPLATE_BY_KIND[kind]}_{lang}"
    sid = WA_TEMPLATES.get(template)
    if not (TWILIO_WA_FROM and sid):
        return "retry"
    if test_mode:
        print(f"    [TEST] WhatsApp a {to_phone}: {template} {variables}")
        return "sent"
    if not template_approved(sid):
        print(f"    ⏳ Plantilla {template} aún sin aprobar por Meta — reintento más tarde ({to_phone})")
        return "retry"
    try:
        tw = Client(TWILIO_SID, TWILIO_TOKEN)
        msg = tw.messages.create(from_=TWILIO_WA_FROM, to=f"whatsapp:{to_phone}", content_sid=sid,
                                 content_variables=json.dumps({k: re.sub(r"\s+", " ", str(v)).strip() or "—" for k, v in variables.items()}))
        for _ in range(12):  # esperamos hasta ~36 s a saber si se ha entregado
            time.sleep(3)
            msg = tw.messages(msg.sid).fetch()
            if msg.status in ("delivered", "read"):
                break
            if msg.status in ("failed", "undelivered"):
                print(f"    ⚠️  WhatsApp no entregado a {to_phone} (error {msg.error_code})")
                return "no_whatsapp" if msg.error_code in NO_WHATSAPP_ERRORS else "retry"
        print(f"    ✅ WhatsApp {msg.status} a {to_phone}")
        return "sent"
    except Exception as e:
        print(f"    ⚠️  WhatsApp falló ({e})")
        return "retry"


SMS_ENABLED = os.getenv('SMS_ENABLED') == '1'  # activar cuando Twilio apruebe el registro A2P (SMS en EE. UU.)


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


def notify_guest(guest, kind, body, lang, business_name, test_mode=False, link="", vip_message="", links=None):
    """WhatsApp → (SMS si está activado) → email. Devuelve el canal usado, o None si hay que reintentar más tarde.
    Salida: plantilla hosperai_review_[vip_]{g|gt}_{lang} con enlaces directos de Google (y Tripadvisor si lo hay);
    si Meta aún no la ha aprobado, la antigua hosperai_thanks_{lang} con el enlace de Google."""
    links = links or {}
    vip = kind == "departure" and guest.get("vip") and vip_message
    if kind == "departure" and links.get("google"):
        link = links["google"]
        extra = f"\nTripadvisor: {links['tripadvisor']}" if links.get("tripadvisor") else ""
        body = MESSAGES['departure'][lang].format(name=guest['name'], business=business_name, link=f"\nGoogle: {link}{extra}")
    if vip:
        body = body + f"\n\n{vip_message}"
    if guest['phone']:
        tpl, wa_vars = None, {"1": guest['name'], "2": business_name, "3": link}
        if kind == "departure" and links.get("google"):
            gt = "gt" if links.get("tripadvisor") else "g"
            name = f"hosperai_review_{'vip_' if vip else ''}{gt}_{lang}"
            v = {"1": guest['name'], "2": business_name}
            v.update({"3": vip_message, "4": links["google"]} if vip else {"3": links["google"]})
            if links.get("tripadvisor"):
                v[str(len(v) + 1)] = links["tripadvisor"]
            if test_mode or template_approved(WA_TEMPLATES.get(name, "")):
                tpl, wa_vars = name, v
        res = send_whatsapp(guest['phone'], kind, lang, wa_vars, test_mode, tpl)
        if res == "sent":
            return "WhatsApp"
        if res == "retry":
            return None
        if SMS_ENABLED:
            send_sms(guest['phone'], body, test_mode)
            return "SMS"
    if guest['email']:
        subject = EMAIL_SUBJECTS[kind][lang].format(business=business_name)
        send_email(guest['email'], subject, body, test_mode)
        return "Email"
    print(f"    ⚠️  {guest['name']}: no se ha podido avisar (sin WhatsApp y sin email)")
    return "Not delivered"


def run_client(client, test_mode=False):
    print(f"\n  📍 {client['name']}")
    try:
        guests = fetch_checkins(client['slug'])
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

        due = guest['checkout'] < today or (guest['checkout'] == today and datetime.now().hour >= SEND_AFTER_HOUR)
        if due and (today - guest['checkout']).days <= 2 and not (record.get('departure_sent') or guest.get('departure_sent')):
            body = MESSAGES['departure'][lang].format(name=guest['name'], business=client['name'], link=review_link)
            via = notify_guest(guest, 'departure', body, lang, client['name'], test_mode, review_link, client.get('vip_message', ''), client.get('review_links'))
            if via and not test_mode:
                record['departure_sent'] = True
                if guest.get('id'):
                    mark_sent(client['slug'], guest['id'], 'departure_sent', via)
            sent += 1

        nights = (guest['checkout'] - guest['checkin']).days if guest['checkin'] else 0
        if nights > 1:
            midpoint = guest['checkin'] + timedelta(days=nights // 2)
            if midpoint == today and datetime.now().hour >= SEND_AFTER_HOUR and not (record.get('midstay_sent') or guest.get('midstay_sent')):
                contact_link = f"https://wa.me/{client['hotel_whatsapp']}" if client.get('hotel_whatsapp') else review_link
                body = MESSAGES['midstay'][lang].format(name=guest['name'], business=client['name'], link=contact_link)
                via = notify_guest(guest, 'midstay', body, lang, client['name'], test_mode, contact_link)
                if via and not test_mode:
                    record['midstay_sent'] = True
                    if guest.get('id'):
                        mark_sent(client['slug'], guest['id'], 'midstay_sent', via)
                sent += 1

    save_state(client['state'], state)
    if sent == 0:
        print("  Nadie que avisar hoy.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()

    print(f"\n🌱 Hosperai Boost Review — {len(CHECKIN_CLIENTS)} clientes con check-in activado")
    if not CHECKIN_CLIENTS:
        print("  (todavía no hay ningún cliente configurado en CHECKIN_CLIENTS)")
        return

    for client in CHECKIN_CLIENTS:
        run_client(client, test_mode=args.test)


if __name__ == '__main__':
    main()
