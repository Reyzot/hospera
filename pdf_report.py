"""
Genera los informes de Hospera como PDF (diseño con logo y marca), vía Chrome headless.
"""
import subprocess, tempfile, os

LOGO_PATH = os.path.expanduser('~/hospera/assets/logo-icon.png')
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

BLUE      = "#2563eb"
BLUE_50   = "#eff6ff"
GRAY_900  = "#111827"
GRAY_500  = "#6b7280"
GRAY_200  = "#e5e7eb"
GREEN     = "#059669"
RED       = "#dc2626"

BASE_CSS = f"""
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Inter', -apple-system, sans-serif; color:{GRAY_900}; padding:48px 56px; }}
  .header {{ display:flex; align-items:center; justify-content:space-between; border-bottom:2px solid {GRAY_200}; padding-bottom:20px; margin-bottom:32px; }}
  .brand {{ display:flex; align-items:center; gap:10px; }}
  .brand img {{ height:34px; }}
  .brand-name {{ font-size:19px; font-weight:800; letter-spacing:-0.3px; }}
  .brand-name span {{ color:{BLUE}; }}
  .header-meta {{ text-align:right; }}
  .report-kind {{ font-size:11px; font-weight:700; color:{BLUE}; text-transform:uppercase; letter-spacing:1px; }}
  .report-date {{ font-size:12px; color:{GRAY_500}; margin-top:2px; }}
  h1 {{ font-size:26px; font-weight:900; letter-spacing:-0.5px; margin-bottom:4px; }}
  .subtitle {{ font-size:14px; color:{GRAY_500}; margin-bottom:32px; }}
  .stats-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:36px; }}
  .stat-card {{ background:{BLUE_50}; border:1px solid #dbeafe; border-radius:12px; padding:18px 16px; }}
  .stat-num {{ font-size:26px; font-weight:900; color:{BLUE}; letter-spacing:-1px; }}
  .stat-label {{ font-size:11px; color:{GRAY_500}; font-weight:600; margin-top:4px; line-height:1.4; }}
  .section-title {{ font-size:15px; font-weight:800; margin:32px 0 14px; }}
  .compare-table {{ width:100%; border-collapse:collapse; border:1px solid {GRAY_200}; border-radius:12px; overflow:hidden; }}
  .compare-table th {{ background:#f9fafb; text-align:left; font-size:11px; font-weight:700; color:{GRAY_500}; text-transform:uppercase; letter-spacing:0.5px; padding:12px 16px; border-bottom:1px solid {GRAY_200}; }}
  .compare-table td {{ padding:14px 16px; font-size:14px; border-bottom:1px solid {GRAY_200}; }}
  .compare-table tr:last-child td {{ border-bottom:none; }}
  .delta-up {{ color:{GREEN}; font-weight:700; }}
  .delta-down {{ color:{RED}; font-weight:700; }}
  .note {{ font-size:11.5px; color:{GRAY_500}; font-style:italic; margin-top:14px; }}
  .footer {{ margin-top:48px; padding-top:20px; border-top:1px solid {GRAY_200}; display:flex; justify-content:space-between; align-items:center; }}
  .footer-tag {{ font-size:11px; color:{GRAY_500}; }}
  .footer-brand {{ font-size:12px; font-weight:700; color:{BLUE}; }}
"""

def _header(kind_label, date_str):
    return f"""
    <div class="header">
      <div class="brand">
        <img src="file://{LOGO_PATH}">
        <div class="brand-name">Hosperai<span>.es</span></div>
      </div>
      <div class="header-meta">
        <div class="report-kind">{kind_label}</div>
        <div class="report-date">{date_str}</div>
      </div>
    </div>
    """

def _footer():
    return f"""
    <div class="footer">
      <div class="footer-tag">Hosperai — reseñas e inteligencia competitiva, automatizadas por IA</div>
      <div class="footer-brand">hosperai.es</div>
    </div>
    """

def render_weekly_html(client, weekly, date_str):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>{BASE_CSS}</style></head><body>
{_header("Informe semanal", date_str)}
<h1>{client['name']}</h1>
<div class="subtitle">Actividad de los últimos 7 días</div>
<div class="stats-grid">
  <div class="stat-card"><div class="stat-num">{weekly['total']}</div><div class="stat-label">Reseñas procesadas</div></div>
  <div class="stat-card"><div class="stat-num">{f"{weekly['avg_rating']}⭐" if weekly['avg_rating'] is not None else '—'}</div><div class="stat-label">Puntuación media</div></div>
  <div class="stat-card"><div class="stat-num">{weekly['negative']}</div><div class="stat-label">Reseñas negativas (≤3⭐)</div></div>
  <div class="stat-card"><div class="stat-num">~{weekly['minutes_saved']}m</div><div class="stat-label">Tiempo estimado ahorrado</div></div>
</div>
<div class="note">Estimación basada en {weekly['notified']} reseñas notificadas al manager, 8 min/reseña de referencia (tiempo medio de leer y redactar una respuesta a mano).</div>
{_footer()}
</body></html>"""

def render_monthly_html(client, current, previous, covered, date_str):
    delta_count_html = ""
    delta_rating_html = ""
    if covered and previous['count']:
        delta = current['count'] - previous['count']
        pct = round(100 * delta / previous['count'])
        cls = "delta-up" if delta >= 0 else "delta-down"
        arrow = "▲" if delta >= 0 else "▼"
        delta_count_html = f'<span class="{cls}">{arrow} {"+" if delta >= 0 else ""}{delta} ({"+" if pct >= 0 else ""}{pct}%)</span>'
    if covered and previous['avg_rating'] and current['avg_rating']:
        dr = round(current['avg_rating'] - previous['avg_rating'], 2)
        cls = "delta-up" if dr >= 0 else "delta-down"
        arrow = "▲" if dr >= 0 else "▼"
        delta_rating_html = f'<span class="{cls}">{arrow} {"+" if dr >= 0 else ""}{dr}⭐</span>'

    note = "" if covered else '<div class="note">Histórico aún insuficiente para una comparación completa — se irá completando en los próximos informes.</div>'

    complaints = current.get('complaints_summary') or []
    complaints_html = ""
    if complaints:
        items = "".join(f"<li>{c}</li>" for c in complaints)
        complaints_html = f"""
<div class="section-title">Quejas que se repiten este mes</div>
<ul class="complaints-list">{items}</ul>
<div class="note">Solo se listan quejas que aparecen en más de una reseña — no reseñas puntuales aisladas.</div>
"""

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>{BASE_CSS}
  .complaints-list {{ list-style:none; }}
  .complaints-list li {{ background:#fef2f2; border:1px solid #fecaca; color:#991b1b; font-size:13.5px; font-weight:600; padding:10px 14px; border-radius:8px; margin-bottom:8px; }}
</style></head><body>
{_header("Informe mensual", date_str)}
<h1>{client['name']}</h1>
<div class="subtitle">Comparativa del mes actual frente al mes anterior</div>
<div class="section-title">Reseñas y puntuación</div>
<table class="compare-table">
  <tr><th>Periodo</th><th>Reseñas</th><th>Puntuación media</th></tr>
  <tr><td><strong>Mes actual</strong></td><td>{current['count']}</td><td>{current['avg_rating'] or '—'}⭐</td></tr>
  <tr><td>Mes anterior</td><td>{previous['count']}</td><td>{previous['avg_rating'] or '—'}⭐</td></tr>
</table>
<div class="section-title">Variación</div>
<table class="compare-table">
  <tr><th>Volumen de reseñas</th><th>Puntuación media</th></tr>
  <tr><td>{delta_count_html or '—'}</td><td>{delta_rating_html or '—'}</td></tr>
</table>
{complaints_html}
{note}
{_footer()}
</body></html>"""


AUDIT_STRINGS = {
    "es": {
        "kind_label": "Auditoría de reputación online",
        "subtitle": lambda n: f"Análisis de las reseñas de Google de los últimos {n} meses",
        "stat_total": "Reseñas analizadas",
        "stat_avg": "Puntuación media",
        "stat_unanswered": "Reseñas sin contestar",
        "stat_negative": "Negativas (≤3⭐) sin contestar",
        "unanswered_note": lambda s: f"⚠️ {s['unanswered']} de {s['total']} reseñas analizadas ({s['unanswered_pct']}%) siguen sin respuesta del negocio.",
        "why_title": "Por qué esto importa",
        "example_title": "Un ejemplo real, sin contestar",
        "evolution_title": "Evolución mes a mes",
        "google_note": lambda s: (
            f"Esta media ({s['avg_rating']}⭐) es solo de las {s['total']} reseñas de los últimos {s['months_analyzed']} meses. "
            f"Tu perfil de Google muestra {s['google_overall_rating']}⭐ sobre el histórico completo ({s['google_overall_reviews']} reseñas) — no son la misma cifra."
        ) if s.get('google_overall_rating') else "",
        "growth_title": "Oportunidad de crecimiento",
        "growth_text": lambda s: (
            f"Muchos huéspedes satisfechos simplemente no dejan reseña si nadie se lo pide en el momento adecuado. "
            f"Con una tarjeta NFC en el check-out (toca y escribe la reseña en segundos) y un WhatsApp automático al huésped "
            f"el día de salida pidiéndosela si aún no la ha dejado, se recogen más reseñas de gente que ya se fue contenta. "
            f"Más volumen reciente y positivo desplaza poco a poco la media histórica de Google "
            f"({s['google_overall_rating']}⭐ hoy) hacia arriba — sin inventar nada, solo facilitando que cuenten los huéspedes que ya estaban satisfechos."
        ) if s.get('google_overall_rating') else "",
        "how_title": "Así se vería, en la práctica",
        "how_caption": "Reseña nueva → la IA redacta la respuesta → tú apruebas desde WhatsApp con un toque. Nada que instalar, nada que aprender.",
        "th_month": "Mes", "th_reviews": "Reseñas", "th_avg": "Puntuación media", "th_answered": "% Contestado",
        "footer_note": "Datos extraídos directamente de Google Maps. Este análisis es gratuito y no requiere que uses Hosperai — te lo enviamos porque creemos que te va a ser útil.",
        "footer_tag": "Esto se puede automatizar — reseñas respondidas por IA, sin dashboards, todo en WhatsApp.",
        "key_points": lambda s: [
            f"<strong>1 de cada {round(100/s['unanswered_pct']) if s['unanswered_pct'] else '—'} huéspedes que deja una reseña no recibe ninguna respuesta.</strong> Para quien está decidiendo reservar, una reseña sin contestar pesa más que una bien gestionada — sobre todo si es negativa.",
            f"<strong>{s['negative_unanswered']} de las {s['negative']} reseñas negativas ({s['negative_unanswered_pct']}%) no tienen ninguna respuesta.</strong> Son justo las que más pesan en la decisión de un huésped nuevo — y las más urgentes de resolver.",
            f"<strong>Con ~{round(s['total']/s['months_analyzed'])} reseñas al mes</strong>, mantenerse al día a mano exige tiempo real de alguien del equipo cada semana — tiempo que podría ir a otras prioridades.",
            "<strong>No es un problema de mala gestión, es un problema de volumen y tiempo.</strong> Automatizarlo no cambia cómo suena la marca — solo hace que nadie se quede sin respuesta.",
        ],
    },
    "en": {
        "kind_label": "Online Reputation Audit",
        "subtitle": lambda n: f"Analysis of Google reviews over the last {n} months",
        "stat_total": "Reviews analyzed",
        "stat_avg": "Average rating",
        "stat_unanswered": "Unanswered reviews",
        "stat_negative": "Negative (≤3⭐) unanswered",
        "unanswered_note": lambda s: f"⚠️ {s['unanswered']} of {s['total']} reviews analyzed ({s['unanswered_pct']}%) still have no response from the business.",
        "why_title": "Why this matters",
        "example_title": "A real example, unanswered",
        "evolution_title": "Month-by-month trend",
        "google_note": lambda s: (
            f"This average ({s['avg_rating']}⭐) covers only the {s['total']} reviews from the last {s['months_analyzed']} months. "
            f"Your Google profile shows {s['google_overall_rating']}⭐ over its full history ({s['google_overall_reviews']} reviews) — these aren't the same number."
        ) if s.get('google_overall_rating') else "",
        "growth_title": "Growth opportunity",
        "growth_text": lambda s: (
            f"Plenty of satisfied guests simply never leave a review unless someone asks at the right moment. "
            f"With an NFC card at check-out (tap and write the review in seconds) and an automatic WhatsApp to the guest "
            f"on their departure day asking for a review if they haven't left one, you collect more reviews from people "
            f"who already left happy. More recent, positive volume gradually pulls the overall Google rating "
            f"(currently {s['google_overall_rating']}⭐) upward — nothing invented, just making it easy for already-satisfied guests to be counted."
        ) if s.get('google_overall_rating') else "",
        "how_title": "What this would look like",
        "how_caption": "New review comes in → AI drafts the reply → you approve from WhatsApp with one tap. Nothing to install, nothing to learn.",
        "th_month": "Month", "th_reviews": "Reviews", "th_avg": "Average rating", "th_answered": "% Answered",
        "footer_note": "Data pulled directly from Google Maps. This analysis is free and doesn't require using Hosperai — we're sending it because we think it'll be useful to you.",
        "footer_tag": "This can be automated — reviews answered by AI, no dashboards, all on WhatsApp.",
        "key_points": lambda s: [
            f"<strong>1 in {round(100/s['unanswered_pct']) if s['unanswered_pct'] else '—'} guests who leave a review get no response at all.</strong> For someone deciding whether to book, an unanswered review weighs more than a well-handled one — especially if it's negative.",
            f"<strong>{s['negative_unanswered']} of the {s['negative']} negative reviews ({s['negative_unanswered_pct']}%) have zero response.</strong> These are exactly the ones that weigh most on a new guest's decision — and the most urgent to fix.",
            f"<strong>With ~{round(s['total']/s['months_analyzed'])} reviews a month</strong>, keeping up manually takes real time from someone on the team every week — time that could go toward other priorities.",
            "<strong>This isn't a mismanagement problem, it's a volume-and-time problem.</strong> Automating it doesn't change how the brand sounds — it just makes sure no one goes unanswered.",
        ],
    },
}


def render_audit_html(business_name, stats, monthly_rows, date_str, lang="es"):
    t = AUDIT_STRINGS[lang]

    def _pct_cell(pct):
        if pct is None:
            return '—'
        cls = "delta-up" if pct >= 80 else ("delta-down" if pct < 60 else "")
        return f'<span class="{cls}">{pct}%</span>' if cls else f'{pct}%'

    rows_html = "".join(
        f"<tr><td>{m['label']}</td><td>{m['count']}</td><td>{m['avg_rating'] or '—'}⭐</td><td>{_pct_cell(m['answered_pct'])}</td></tr>"
        for m in monthly_rows
    )
    unanswered_html = ""
    if stats['unanswered'] > 0:
        unanswered_html = f"""
        <div class="note" style="background:#fef2f2;border:1px solid #fecaca;color:{RED};padding:14px 16px;border-radius:10px;font-style:normal;font-weight:600;">
          {t['unanswered_note'](stats)}
        </div>
        """

    key_points_html = "".join(f'<li>{p}</li>' for p in t['key_points'](stats))

    example = stats.get('example_unanswered_negative')
    example_html = ""
    if example:
        example_html = f"""
        <div class="section-title" style="margin:14px 0 6px;">{t['example_title']}</div>
        <div class="quote-box">
          <div class="quote-meta">{example['author']} · {"⭐" * example['rating']} · {example['date']}</div>
          <div class="quote-text">"{example['text']}"</div>
        </div>
        """

    google_note = t['google_note'](stats)
    growth_text = t['growth_text'](stats)
    growth_html = ""
    how_it_works_html = ""
    if growth_text:
        growth_html = f"""
        <div class="section-title" style="margin:10px 0 4px;">{t['growth_title']}</div>
        <div class="note" style="background:{BLUE_50};border:1px solid #dbeafe;color:{GRAY_900};padding:9px 14px;border-radius:10px;font-style:normal;margin-top:0;">
          {growth_text}
        </div>
        """
        how_it_works_html = f"""
        <div class="section-title" style="margin:10px 0 4px;">{t['how_title']}</div>
        <div style="border:1px solid {GRAY_200};border-radius:10px;overflow:hidden;max-width:380px;">
          <div style="background:{GRAY_200};padding:6px 10px;font-size:9.5px;color:{GRAY_500};font-weight:600;">WhatsApp · Hosperai</div>
          <div style="padding:10px;background:#fff;">
            <div style="background:#e7ffd9;border-radius:10px 10px 3px 10px;padding:8px 11px;font-size:10.5px;line-height:1.45;margin-bottom:7px;color:{GRAY_900};">
              <div style="font-weight:700;color:{GREEN};font-size:8.5px;margin-bottom:3px;">NEW REVIEW — Google ★★★★☆</div>
              Maria G.: "Great location, very friendly staff..."
            </div>
            <div style="background:#fff;border:1px solid {GRAY_200};border-radius:10px 10px 10px 3px;padding:8px 11px;font-size:10.5px;color:{GRAY_900};margin-bottom:7px;">
              <strong style="font-size:8.5px;color:{GRAY_500};display:block;margin-bottom:2px;">GENERATED REPLY</strong>
              Hi Maria, thank you for staying with us — so glad you felt well taken care of!
            </div>
            <div style="display:flex;gap:6px;">
              <div style="flex:1;background:{GREEN};color:#fff;text-align:center;padding:5px;border-radius:6px;font-size:9.5px;font-weight:700;">YES</div>
              <div style="flex:1;background:{GRAY_200};color:{GRAY_500};text-align:center;padding:5px;border-radius:6px;font-size:9.5px;font-weight:700;">EDIT</div>
            </div>
          </div>
        </div>
        <div class="google-note" style="max-width:380px;margin-top:4px;">{t['how_caption']}</div>
        """

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>{BASE_CSS} body{{padding:18px 56px;}} .header{{margin-bottom:9px;padding-bottom:6px;}}
  .compare-table td {{ padding:6px 16px; }}
  .compare-table th {{ padding:8px 16px; }}
  .key-points {{ list-style:none; display:flex; flex-direction:column; gap:4px; margin:6px 0 2px; }}
  .key-points li {{ font-size:11.5px; line-height:1.4; color:{GRAY_900}; padding-left:20px; position:relative; }}
  .key-points li::before {{ content:'→'; color:{BLUE}; font-weight:700; position:absolute; left:0; }}
  .quote-box {{ background:#fafafa; border-left:3px solid {RED}; border-radius:6px; padding:8px 14px; }}
  .quote-meta {{ font-size:11px; color:{GRAY_500}; font-weight:600; margin-bottom:3px; }}
  .quote-text {{ font-size:12px; color:{GRAY_900}; font-style:italic; line-height:1.4; }}
  .google-note {{ font-size:11px; color:{GRAY_500}; font-style:italic; margin-top:4px; }}
</style></head><body>
{_header(t['kind_label'], date_str)}
<h1>{business_name}</h1>
<div class="subtitle" style="margin-bottom:4px;">{t['subtitle'](stats['months_analyzed'])}</div>
{f'<div class="google-note">{google_note}</div>' if google_note else ''}
<div class="stats-grid" style="margin-bottom:10px;margin-top:8px;">
  <div class="stat-card" style="padding:12px 16px;"><div class="stat-num">{stats['total']}</div><div class="stat-label">{t['stat_total']}</div></div>
  <div class="stat-card" style="padding:12px 16px;"><div class="stat-num">{f"{stats['avg_rating']}⭐" if stats['avg_rating'] is not None else '—'}</div><div class="stat-label">{t['stat_avg']}</div></div>
  <div class="stat-card" style="padding:12px 16px;"><div class="stat-num">{stats['unanswered_pct']}%</div><div class="stat-label">{t['stat_unanswered']}</div></div>
  <div class="stat-card" style="padding:12px 16px;"><div class="stat-num">{stats['negative_unanswered']}/{stats['negative']}</div><div class="stat-label">{t['stat_negative']}</div></div>
</div>
{unanswered_html}
<div class="section-title" style="margin:8px 0 4px;">{t['why_title']}</div>
<ul class="key-points">{key_points_html}</ul>
{example_html}
{growth_html}
{how_it_works_html}
<div class="section-title" style="margin:8px 0 4px;">{t['evolution_title']}</div>
<table class="compare-table">
  <tr><th>{t['th_month']}</th><th>{t['th_reviews']}</th><th>{t['th_avg']}</th><th>{t['th_answered']}</th></tr>
  {rows_html}
</table>
<div class="note" style="margin-top:4px;">{t['footer_note']}</div>
<div class="footer" style="margin-top:6px;padding-top:6px;">
  <div class="footer-tag">{t['footer_tag']}</div>
  <div class="footer-brand">hosperai.es</div>
</div>
</body></html>"""


def html_to_pdf(html_str, out_path):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_str)
        html_path = f.name

    subprocess.run([
        CHROME, "--headless", "--disable-gpu",
        f"--print-to-pdf={out_path}",
        "--no-pdf-header-footer",
        "--virtual-time-budget=3000",
        f"file://{html_path}",
    ], capture_output=True, timeout=30, check=True)

    os.unlink(html_path)
    return out_path
