"""
Hospera Reports — resumen semanal + comparativa mes actual vs mes anterior, por email.

Uso:
  python3 reports.py          # genera y manda el informe a los clientes con manager_email
  python3 reports.py --test   # genera el informe pero no manda el email (solo imprime)
"""
import sys
sys.path.insert(0, '/Users/andreurey/Library/Python/3.9/lib/python/site-packages')

import os, json, argparse, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
from dotenv import load_dotenv

from review_monitor import CLIENTS, SERPAPI_KEY, load_seen, LOW_RATING_THRESHOLD
from pdf_report import render_weekly_html, render_monthly_html, html_to_pdf
import requests

load_dotenv(dotenv_path=os.path.expanduser('~/hospera/.env'))

EMAIL_ADDRESS      = os.getenv('EMAIL_ADDRESS')
EMAIL_APP_PASSWORD = os.getenv('EMAIL_APP_PASSWORD')
MINUTES_PER_REVIEW = 8  # estimación: lo que tarda un manager en leer + redactar una respuesta a mano

MONTHLY_CACHE_PATH = Path.home() / 'hospera' / 'monthly_stats_cache.json'


# ── Resumen semanal (gratis — usa solo el histórico local, no gasta cuota) ──

def weekly_digest(client):
    seen   = load_seen(client['state'])
    cutoff = datetime.now() - timedelta(days=7)
    week   = []

    for info in seen.values():
        if not isinstance(info, dict):
            continue  # entradas viejas en formato antiguo (solo string), se ignoran
        try:
            date = datetime.fromisoformat(info['date'])
        except (KeyError, ValueError, TypeError):
            continue
        if date >= cutoff:
            week.append(info)

    notified = [e for e in week if e.get('notified')]
    ratings  = [e['rating'] for e in week if e.get('rating')]
    negative = [r for r in ratings if r <= LOW_RATING_THRESHOLD]

    return {
        "total":         len(week),
        "notified":      len(notified),
        "avg_rating":    round(sum(ratings) / len(ratings), 1) if ratings else None,
        "negative":      len(negative),
        "minutes_saved": len(notified) * MINUTES_PER_REVIEW,
    }


# ── Comparativa mensual (gasta cuota SerpAPI — se cachea 6 días) ──

def fetch_reviews_covering_months(data_id, n_months=2, max_pages=6):
    """Pagina hasta cubrir el mes actual + los (n_months-1) anteriores, o hasta
    max_pages como límite de seguridad. Devuelve (reviews, covered, place_info) —
    covered=False significa que no llegamos a cubrir todo el rango pedido (dato
    incompleto). place_info trae el rating/nº de reseñas oficial de Google (histórico
    completo, no solo el rango analizado) — viene gratis en la primera página, sin
    gastar una llamada aparte."""
    now = datetime.now()
    year, month = now.year, now.month
    for _ in range(n_months - 1):
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    boundary = f"{year:04d}-{month:02d}-01"

    all_reviews = []
    place_info = {}
    params = {
        "engine": "google_maps_reviews", "data_id": data_id,
        "api_key": SERPAPI_KEY, "hl": "es", "sort_by": "newestFirst",
    }
    covered = False
    for _ in range(max_pages):
        r = requests.get("https://serpapi.com/search", params=params, timeout=15)
        data = r.json()
        if "error" in data:
            raise Exception(f"SerpAPI error: {data['error']}")
        if not place_info:
            place_info = data.get("place_info", {})
        batch = data.get("reviews", [])
        if not batch:
            covered = True
            break
        all_reviews.extend(batch)
        oldest_iso = batch[-1].get("iso_date", "")
        if oldest_iso and oldest_iso[:10] < boundary:
            covered = True
            break
        next_token = data.get("serpapi_pagination", {}).get("next_page_token")
        if not next_token:
            covered = True
            break
        params = {**params, "next_page_token": next_token}
    return all_reviews, covered, place_info


def load_monthly_cache():
    if MONTHLY_CACHE_PATH.exists():
        return json.loads(MONTHLY_CACHE_PATH.read_text())
    return {}

def save_monthly_cache(cache):
    MONTHLY_CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False))


def monthly_comparison(client, cache):
    key = client['name']
    entry = cache.get(key, {})
    now = datetime.now()

    fetched_at = entry.get('_fetched_at')
    is_stale = True
    if fetched_at:
        is_stale = (now - datetime.fromisoformat(fetched_at)).days >= 6

    if is_stale:
        reviews, covered, _place_info = fetch_reviews_covering_months(client['data_id'], n_months=2)
        by_month = defaultdict(list)
        for r in reviews:
            iso = r.get('iso_date', '')
            rating = r.get('rating')
            if iso and rating:
                by_month[iso[:7]].append(float(rating))
        entry = {
            month: {"count": len(ratings), "avg_rating": round(sum(ratings) / len(ratings), 2)}
            for month, ratings in by_month.items()
        }
        entry['_fetched_at'] = now.isoformat()
        entry['_covered']    = covered
        cache[key] = entry

    current_month = now.strftime('%Y-%m')
    prev_month    = (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
    current  = entry.get(current_month, {"count": 0, "avg_rating": None})
    previous = entry.get(prev_month, {"count": 0, "avg_rating": None})
    return current, previous, entry.get('_covered', False)


# ── Email (con el PDF adjunto) ──

def send_email_with_pdf(to_addr, subject, body, pdf_path, pdf_name):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From']    = EMAIL_ADDRESS
    msg['To']      = to_addr
    msg.attach(MIMEText(body))

    with open(pdf_path, 'rb') as f:
        part = MIMEApplication(f.read(), _subtype='pdf')
    part.add_header('Content-Disposition', 'attachment', filename=pdf_name)
    msg.attach(part)

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.send_message(msg)


def run_weekly(test_mode=False):
    date_str = datetime.now().strftime('%d/%m/%Y')
    for client in CLIENTS:
        to_addr = client.get('manager_email')
        if not to_addr:
            print(f"  ⏭️  {client['name']}: sin manager_email configurado, se salta")
            continue

        print(f"\n  📍 {client['name']} — informe semanal")
        weekly = weekly_digest(client)
        html = render_weekly_html(client, weekly, date_str)
        pdf_path = f"/tmp/hospera_semanal_{client['name'].replace(' ', '_')}.pdf"
        html_to_pdf(html, pdf_path)
        print(f"  📄 PDF generado: {pdf_path}")

        body = f"Hola,\n\nAdjunto el informe semanal de {client['name']}.\n\n— Hospera"
        if not test_mode:
            send_email_with_pdf(to_addr, f"Informe semanal Hospera — {client['name']}", body, pdf_path, "informe_semanal.pdf")
            print(f"  ✅ Email enviado a {to_addr}")
        else:
            print(f"  [TEST] Email no enviado")


def run_monthly(test_mode=False):
    date_str = datetime.now().strftime('%d/%m/%Y')
    cache = load_monthly_cache()
    for client in CLIENTS:
        to_addr = client.get('manager_email')
        if not to_addr:
            print(f"  ⏭️  {client['name']}: sin manager_email configurado, se salta")
            continue

        print(f"\n  📍 {client['name']} — informe mensual")
        current, previous, covered = monthly_comparison(client, cache)
        html = render_monthly_html(client, current, previous, covered, date_str)
        pdf_path = f"/tmp/hospera_mensual_{client['name'].replace(' ', '_')}.pdf"
        html_to_pdf(html, pdf_path)
        print(f"  📄 PDF generado: {pdf_path}")

        body = f"Hola,\n\nAdjunto la comparativa mensual de {client['name']} frente al mes anterior.\n\n— Hospera"
        if not test_mode:
            send_email_with_pdf(to_addr, f"Informe mensual Hospera — {client['name']}", body, pdf_path, "informe_mensual.pdf")
            print(f"  ✅ Email enviado a {to_addr}")
        else:
            print(f"  [TEST] Email no enviado")

    save_monthly_cache(cache)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--weekly', action='store_true')
    parser.add_argument('--monthly', action='store_true')
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()

    if not args.weekly and not args.monthly:
        parser.error("especifica --weekly o --monthly")

    if args.weekly:
        run_weekly(test_mode=args.test)
    if args.monthly:
        run_monthly(test_mode=args.test)
