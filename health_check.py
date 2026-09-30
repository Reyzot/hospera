"""
Hosperai Health Check — cada día a las 8:30 revisa que todo el sistema esté sano:
cuota de SerpAPI, saldo de Twilio, WhatsApp no entregados en las últimas 24 h,
que app.hosperai.es responda, altas pendientes de activar, y errores en los logs. Si algo va mal, manda un email de aviso. Si todo está bien,
no manda nada (para no llenar el correo de confirmaciones vacías).

Uso:
  python3 health_check.py          # revisa y manda email solo si hay problema
  python3 health_check.py --test   # revisa e imprime el resultado, no manda email
"""
import sys
sys.path.insert(0, '/Users/andreurey/Library/Python/3.9/lib/python/site-packages')

import os, argparse, smtplib, requests
from email.mime.text import MIMEText
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.expanduser('~/hospera/.env'))

SERPAPI_KEY   = os.getenv('SERPAPI_KEY')
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_APP_PASSWORD = os.getenv('EMAIL_APP_PASSWORD')
ALERT_TO      = os.getenv('EMAIL_ADDRESS')  # se manda a sí mismo (Andreu)

HOSPERA_DIR   = Path.home() / 'hospera'
LOG_FILES     = ['launchd_err.log', 'guestfollowup_err.log']

SERPAPI_LOW_THRESHOLD = 30  # avisar si quedan menos de estas búsquedas


def check_serpapi():
    problems = []
    try:
        r = requests.get(f"https://serpapi.com/account.json?api_key={SERPAPI_KEY}", timeout=15)
        data = r.json()
        left = data.get('total_searches_left')
        renewal = data.get('plan_renewal_date')
        if left is None:
            problems.append("No se pudo leer la cuota de SerpAPI (respuesta inesperada).")
        elif left <= SERPAPI_LOW_THRESHOLD:
            problems.append(
                f"SerpAPI se está quedando sin búsquedas: solo quedan {left} "
                f"(se renueva el {renewal}). Considera pasar a plan de pago si esto "
                f"pasa a menudo."
            )
    except Exception as e:
        problems.append(f"No se pudo comprobar SerpAPI: {e}")
    return problems


def check_logs():
    problems = []
    for fname in LOG_FILES:
        path = HOSPERA_DIR / fname
        if not path.exists():
            continue
        try:
            lines = path.read_text(errors="ignore").splitlines()
        except Exception:
            continue
        # Solo mira las últimas 30 líneas, y descarta el ruido conocido de NotOpenSSLWarning
        recent = [l for l in lines[-30:] if l.strip() and "NotOpenSSLWarning" not in l and "warnings.warn" not in l]
        real_errors = [l for l in recent if "error" in l.lower() or "traceback" in l.lower() or "exception" in l.lower()]
        if real_errors:
            problems.append(f"Errores recientes en {fname}:\n  " + "\n  ".join(real_errors[-5:]))
    return problems


def check_twilio():
    problems = []
    sid, tok = os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN')
    try:
        bal = requests.get(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Balance.json", auth=(sid, tok), timeout=15).json()
        if float(bal.get("balance", 0)) < 5:
            problems.append(f"Saldo de Twilio bajo: {bal.get('balance')} {bal.get('currency')}. Recarga para que no se paren los WhatsApp.")
        msgs = requests.get(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json", auth=(sid, tok),
                            params={"PageSize": 100, "From": os.getenv('TWILIO_WHATSAPP_FROM')}, timeout=15).json().get("messages", [])
        from email.utils import parsedate_to_datetime
        from datetime import datetime, timezone, timedelta
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        bad = [m for m in msgs if m["status"] in ("failed", "undelivered") and parsedate_to_datetime(m["date_created"]) > since]
        if bad:
            problems.append(f"{len(bad)} WhatsApp NO entregados en las últimas 24 h:\n  " +
                            "\n  ".join(f"{m['to']} error {m['error_code']}" for m in bad[:8]) +
                            "\n  (63016 = plantilla sin aprobar · 63024/63003 = el número no tiene WhatsApp)")
    except Exception as e:
        problems.append(f"No se pudo comprobar Twilio: {e}")
    return problems


def check_web_and_clients():
    problems = []
    for url in ("https://app.hosperai.es/", "https://app.hosperai.es/checkin/"):
        try:
            if requests.get(url, timeout=15).status_code != 200:
                problems.append(f"La web no responde bien: {url}")
        except Exception as e:
            problems.append(f"La web no responde: {url} ({e})")
    cf = HOSPERA_DIR / 'clients.json'
    if cf.exists():
        import json
        pending = [c["name"] for c in json.loads(cf.read_text()) if c.get("status") == "pending"]
        if pending:
            problems.append("Hoteles que rellenaron el alta y siguen sin activar: " + ", ".join(pending))
    return problems


def send_alert(problems, test_mode=False):
    body = "Hosperai Health Check encontró lo siguiente:\n\n" + "\n\n".join(problems)
    if test_mode:
        print(body)
        return
    if not (EMAIL_ADDRESS and EMAIL_APP_PASSWORD):
        print("[SIN CREDENCIALES DE EMAIL] " + body)
        return
    msg = MIMEText(body)
    msg['Subject'] = "⚠️ Hosperai — algo necesita tu atención"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ALERT_TO
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.send_message(msg)
    print("✅ Alerta enviada por email.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()

    problems = check_serpapi() + check_twilio() + check_web_and_clients() + check_logs()

    if not problems:
        print("✅ Todo sano — SerpAPI con cuota de sobra, sin errores recientes.")
        return

    send_alert(problems, test_mode=args.test)


if __name__ == '__main__':
    main()
