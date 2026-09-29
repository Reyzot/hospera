"""
Hospera Health Check — revisa semanalmente que todo el sistema esté sano:
cuota de SerpAPI, y errores recientes en los logs de review_monitor y
guest_followup. Si algo va mal, manda un email de aviso. Si todo está bien,
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


def send_alert(problems, test_mode=False):
    body = "Hospera Health Check encontró lo siguiente:\n\n" + "\n\n".join(problems)
    if test_mode:
        print(body)
        return
    if not (EMAIL_ADDRESS and EMAIL_APP_PASSWORD):
        print("[SIN CREDENCIALES DE EMAIL] " + body)
        return
    msg = MIMEText(body)
    msg['Subject'] = "⚠️ Hospera — algo necesita tu atención"
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

    problems = check_serpapi() + check_logs()

    if not problems:
        print("✅ Todo sano — SerpAPI con cuota de sobra, sin errores recientes.")
        return

    send_alert(problems, test_mode=args.test)


if __name__ == '__main__':
    main()
