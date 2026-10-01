"""PDF de una página para llevar en mano a un hotel: sus datos de Google, reseñas sin responder y
una respuesta sugerida (con traducción si la reseña está en otro idioma).

  python3 leads/visit_audit.py            # genera los PDF de leads/visitas_miami_beach.json en ~/Desktop/Visitas Miami Beach
"""
import json, csv, base64, html, re, sys
from pathlib import Path
D = Path(__file__).parent
sys.path.insert(0, str(D.parent))
from pdf_report import html_to_pdf
import review_monitor as rm

E = html.escape
LOGO = base64.b64encode((D.parent / "assets/logo-icon-clean.png").read_bytes()).decode()
OUT = Path.home() / "Desktop" / "Visitas Miami Beach"
CSS = """
@page { size:A4; margin:10mm 13mm; }
body { font-family:-apple-system,Helvetica,Arial,sans-serif; color:#111827; font-size:10pt; line-height:1.4; }
.head { display:flex; align-items:center; gap:12px; border-bottom:3px solid #2563eb; padding-bottom:8px; margin-bottom:12px; }
.head img { width:38px; } h1 { font-size:19pt; margin:0; letter-spacing:-.4px; } .sub { color:#6b7280; margin:2px 0 0; font-size:9.5pt; }
h3 { font-size:11pt; margin:10px 0 5px; }
.kpis { display:flex; gap:8px; margin:6px 0 4px; } .kpi { flex:1; border:1px solid #e5e7eb; border-radius:8px; padding:9px; text-align:center; }
.kpi b { display:block; font-size:19pt; color:#2563eb; line-height:1.1; } .kpi.red b { color:#dc2626; } .kpi small { color:#6b7280; font-size:8.5pt; }
table { width:100%; border-collapse:collapse; } td,th { padding:4px 7px; border-bottom:1px solid #f0f1f3; font-size:9.5pt; text-align:left; }
.bar { display:inline-block; height:9px; background:#93c5fd; border-radius:3px; margin-right:7px; vertical-align:middle; } .bar.me { background:#2563eb; }
tr.me td { background:#eff6ff; font-weight:700; } .yes { color:#15803d; font-weight:700; } .no { color:#dc2626; font-weight:700; } .dim { color:#d1d5db; }
.cols { display:flex; gap:14px; } .cols > div { flex:1; }
.rv { background:#fef2f2; border:1px solid #fecaca; border-radius:8px; padding:8px 10px; } .rvh { font-size:9pt; color:#6b7280; } .rvt { margin-top:3px; }
.tr { color:#6b7280; font-style:italic; margin-top:3px; font-size:9pt; }
.rp { background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px; padding:8px 10px; margin-top:6px; } .rph { font-size:9pt; font-weight:700; color:#2563eb; margin-bottom:3px; }
.how { background:#f9fafb; border-radius:8px; padding:7px 12px; margin-top:9px; font-size:9.5pt; } .how ol { margin:4px 0 0 16px; padding:0; }
.foot { display:flex; justify-content:space-between; align-items:center; margin-top:12px; border-top:1px solid #e5e7eb; padding-top:8px; font-size:9.5pt; }
.foot b { color:#2563eb; } .tiny { color:#9ca3af; font-size:8pt; margin-top:6px; }
"""


def short(name):
    return re.sub(r"\s+(Miami Beach|South Beach Hotel|South Beach|Hotel)$", "", name).strip()


def build(name, h, peers_pool):
    rev, rat = int(float(h["reviews"])), float(h["rating"])
    peers = [p for p in peers_pool if p["name"] != name and 0.7 * rev <= int(float(p["reviews"])) <= 3 * rev + 200]
    peers = sorted(peers, key=lambda p: (-float(p["rating"]), -int(float(p["reviews"]))))[:4]
    rows = peers + [h]; mx = max(int(float(p["reviews"])) for p in rows)
    cmp = "".join(f'<tr class="{"me" if p is h else ""}"><td>{E(p["name"])}</td><td>{float(p["rating"]):.1f}★</td>'
                  f'<td><span class="bar{" me" if p is h else ""}" style="width:{int(float(p["reviews"])) / mx * 170:.0f}px"></span>{int(float(p["reviews"])):,}</td></tr>'
                  for p in sorted(rows, key=lambda p: -int(float(p["reviews"]))))
    rec = h["recent"]; unans = [r for r in rec if not r["replied"]]
    neg_un = [r for r in unans if r["rating"] <= 2]
    target = sorted([r for r in unans if r["text"]], key=lambda r: r["rating"])
    sugg = ""
    if target:
        t = target[0]
        client = {"name": name, "type": "hotel", "location": "Miami Beach, FL", "signature": f"The {short(name)} Team", "notify_lang": "en"}
        reply, rtr, reptr = rm.generate_response(client, "the guest", t["rating"], t["text"])
        stars = "★" * int(t["rating"]) + "☆" * (5 - int(t["rating"]))
        sugg = (f'<h3>One of your unanswered reviews, and the reply we\'d draft for you</h3>'
                f'<div class="rv"><div class="rvh">{stars} · {E(t["date"])} · <span class="no">no reply yet</span></div>'
                f'<div class="rvt">“{E(t["text"][:230].rstrip())}{"…" if len(t["text"]) > 230 else ""}”</div>' + (f'<div class="tr">🌐 {E(rtr[:260])}</div>' if rtr else "") + '</div>'
                f'<div class="rp"><div class="rph">✍️ Suggested reply' + (" (in the guest's language)" if reptr else "") + ', ready to copy &amp; paste</div>'
                f'{E(reply)}' + (f'<div class="tr">🌐 {E(reptr[:330])}{"…" if len(reptr) > 330 else ""}</div>' if reptr else "") + '</div>')
    lst = "".join(f'<tr><td>{"★" * int(r["rating"])}<span class="dim">{"★" * (5 - int(r["rating"]))}</span></td><td>{E(r["date"])}</td>'
                  f'<td>{"<span class=yes>Replied</span>" if r["replied"] else "<span class=no>No reply</span>"}</td></tr>' for r in rec)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="head"><img src="data:image/png;base64,{LOGO}"><div><h1>{E(name)}</h1><p class="sub">Google review snapshot · prepared by Hosperai · October 2026</p></div></div>
<div class="kpis"><div class="kpi"><b>{rat:.1f}★</b><small>Google rating</small></div><div class="kpi"><b>{rev:,}</b><small>Google reviews</small></div>
<div class="kpi {"red" if unans else ""}"><b>{len(unans)} of {len(rec)}</b><small>latest reviews without a reply</small></div>
<div class="kpi {"red" if neg_un else ""}"><b>{len(neg_un)}</b><small>recent negative reviews unanswered</small></div></div>
<div class="cols"><div><h3>You vs. similar hotels in South Beach</h3><table><tr><th>Hotel</th><th>Rating</th><th>Reviews</th></tr>{cmp}</table></div>
<div style="max-width:36%"><h3>Your latest reviews</h3><table><tr><th>Stars</th><th>When</th><th>Reply</th></tr>{lst}</table></div></div>
{sugg}
<div class="how"><b>How Hosperai fixes this, on autopilot</b><ol>
<li>After checkout, every guest gets a personal thank-you on WhatsApp with one-tap links to your Google &amp; Tripadvisor review page.</li>
<li>Every new review reaches your WhatsApp with the reply already written in your tone and in the guest's language, with a translation for you. Copy, paste, done.</li>
<li>Negative reviews trigger an urgent alert, so no unhappy guest goes unanswered.</li></ol>
Live in 48 hours · no app, no dashboard · from $99/month, no lock-in.</div>
<div class="foot"><div><b>Andreu Rey</b> · Hosperai · Miami Beach<br>andreu@gethosperai.com · hosperai.es</div><div style="text-align:right">See it in 38 seconds:<br><b>hosperai.es/demo</b></div></div>
<p class="tiny">Public Google Maps data as of October 2026. Latest reviews = the most recent reviews shown on Google.</p>
</body></html>"""


if __name__ == "__main__":
    data = json.loads((D / "visitas_miami_beach.json").read_text())
    OUT.mkdir(exist_ok=True)
    skip = re.compile(r"lennox|aqua hotel|aqua beach|jordan|uma house|uma suites|yurbban|crest hotel|crest suites|casa boutique|casa hotel|colectia|the spot|cando", re.I)
    pool = [r for r in csv.DictReader(open(D / "florida_hotels_independientes.csv"))
            if "33139" in r["address"] and r["reviews"] and r["type"] in ("Hotel", "Bed & breakfast", "Inn", "Resort hotel")
            and not skip.search(r["name"])]
    for name, h in data.items():
        if skip.search(name):
            continue
        html_to_pdf(build(name, h, pool), str(OUT / f"{name}.pdf"))
        print("✓", name)
