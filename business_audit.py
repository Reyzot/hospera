"""
Auditoría de reputación online — PDF con el histórico real de reseñas de Google
de CUALQUIER negocio (cliente o prospecto), como gancho de venta.

No hace falta que el negocio use Hospera para generar esto — es una foto de
cómo está su reputación online ahora mismo, sacada de Google Maps vía SerpAPI.

Uso:
  python3 business_audit.py "<data_id>" "Nombre del negocio" [--months 6] [--out ruta.pdf]

Cómo sacar el data_id: mismo proceso que para añadir un cliente nuevo —
ver ARRANCAR_SISTEMA.md, se extrae de la URL de Google Maps del negocio.
"""
import sys
sys.path.insert(0, '/Users/andreurey/Library/Python/3.9/lib/python/site-packages')

import argparse
from datetime import datetime
from collections import defaultdict

from reports import fetch_reviews_covering_months
from pdf_report import render_audit_html, html_to_pdf

MESES_ES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# Palabras que descartan una reseña como "ejemplo" en el PDF — acusaciones graves
# (agresión, robo, delito, acoso, discriminación, salud/seguridad) no son un
# problema de "reseñas sin contestar", son una crisis aparte. Nunca se usan
# como gancho de venta, aunque sean la más reciente o la más citable.
SEVERE_KEYWORDS = [
    "assault", "assaulted", "rob", "robbed", "robbery", "steal", "stole", "stolen",
    "theft", "police", "lawsuit", "legal action", "sue", "sued", "attorney", "lawyer",
    "racist", "racism", "discriminat", "harass", "abuse", "abused", "violent", "violence",
    "threat", "threatened", "crime", "criminal", "bed bug", "bedbug", "roach", "infestation",
    "mold", "sexual", "groped", "assaulting",
    "agres", "robo", "robar", "polic", "demanda", "abogado", "acoso", "racis",
    "discrimina", "chinches", "cucarach", "moho", "delito", "denuncia",
]

def _is_severe(text):
    lowered = text.lower()
    return any(kw in lowered for kw in SEVERE_KEYWORDS)


MONTHS_EN = ["", "January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]

def month_label(yyyymm, lang="es"):
    year, month = yyyymm.split("-")
    names = MONTHS_EN if lang == "en" else MESES_ES
    return f"{names[int(month)]} {year}"


def last_n_months(n):
    now = datetime.now()
    year, month = now.year, now.month
    months = []
    for _ in range(n):
        months.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    return list(reversed(months))  # más antiguo primero


def analyze(data_id, months=6, lang="es"):
    reviews, covered, place_info = fetch_reviews_covering_months(data_id, n_months=months, max_pages=30)

    by_month = defaultdict(list)
    answered_by_month = defaultdict(int)
    total = 0
    unanswered = 0
    negative = 0
    negative_unanswered = 0
    all_ratings = []
    example_unanswered_negative = None  # la más reciente, para citar textualmente

    target_months = set(last_n_months(months))

    for r in reviews:
        iso = r.get('iso_date', '')
        rating = r.get('rating')
        ym = iso[:7]
        if ym not in target_months or not rating:
            continue
        rating = float(rating)
        total += 1
        all_ratings.append(rating)
        by_month[ym].append(rating)
        has_response = bool(r.get('response'))
        if has_response:
            answered_by_month[ym] += 1
        else:
            unanswered += 1
        if rating <= 3:
            negative += 1
            if not has_response:
                negative_unanswered += 1
            if not has_response and example_unanswered_negative is None:
                text = (r.get('snippet') or r.get('extracted_snippet', {}).get('original', '') or '').strip()
                if text and 15 <= len(text) <= 300 and not _is_severe(text):
                    example_unanswered_negative = {
                        "author": r.get('user', {}).get('name', 'Anónimo'),
                        "rating": int(rating),
                        "date": iso[:10],
                        "text": text,
                    }

    monthly_rows = []
    for ym in last_n_months(months):
        ratings = by_month.get(ym, [])
        count = len(ratings)
        answered = answered_by_month.get(ym, 0)
        monthly_rows.append({
            "label": month_label(ym, lang),
            "count": count,
            "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
            "answered_pct": round(100 * answered / count) if count else None,
        })

    stats = {
        "total": total,
        "avg_rating": round(sum(all_ratings) / len(all_ratings), 2) if all_ratings else None,
        "unanswered": unanswered,
        "unanswered_pct": round(100 * unanswered / total) if total else 0,
        "negative": negative,
        "negative_unanswered": negative_unanswered,
        "negative_unanswered_pct": round(100 * negative_unanswered / negative) if negative else 0,
        "months_analyzed": months,
        "covered": covered,
        "example_unanswered_negative": example_unanswered_negative,
        "google_overall_rating": place_info.get('rating'),
        "google_overall_reviews": place_info.get('reviews'),
    }
    return stats, monthly_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('data_id')
    parser.add_argument('business_name')
    parser.add_argument('--months', type=int, default=6)
    parser.add_argument('--lang', choices=['es', 'en'], default='es')
    parser.add_argument('--out', default=None)
    args = parser.parse_args()

    print(f"Analizando {args.business_name}...")
    stats, monthly_rows = analyze(args.data_id, months=args.months, lang=args.lang)
    print(f"  {stats['total']} reseñas en los últimos {args.months} meses, "
          f"media {stats['avg_rating']}⭐, {stats['unanswered_pct']}% sin contestar, "
          f"{stats['negative_unanswered']}/{stats['negative']} negativas sin contestar")
    if not stats['covered']:
        print("  ⚠️  No se llegó a cubrir todo el rango de meses pedido (negocio con mucho volumen) "
              "— los meses más antiguos de la tabla pueden estar incompletos. Sube --months o revisa max_pages.")

    date_str = datetime.now().strftime('%d/%m/%Y')
    html = render_audit_html(args.business_name, stats, monthly_rows, date_str, lang=args.lang)

    out_path = args.out or f"/tmp/auditoria_{args.business_name.replace(' ', '_')}.pdf"
    html_to_pdf(html, out_path)
    print(f"✅ PDF generado: {out_path}")


if __name__ == '__main__':
    main()
