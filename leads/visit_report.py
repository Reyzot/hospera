"""Carta al GM + informe completo de reseñas (varias páginas) para entregar en mano.
Lee leads/visitas_miami_beach.json (reseñas recientes + ranking Maps) y genera
~/Desktop/Visitas Miami Beach/<Hotel> - carta e informe.pdf"""
import json, csv, re, html, base64, sys
from collections import Counter
from pathlib import Path
D = Path(__file__).parent
sys.path.insert(0, str(D.parent))
from pdf_report import html_to_pdf
import review_monitor as rm
import anthropic, os

E = html.escape
LOGO = base64.b64encode((D.parent / "assets/logo-icon-clean.png").read_bytes()).decode()
OUT = Path.home() / "Desktop" / "Visitas Miami Beach"
SKIP = re.compile(r"lennox|aqua hotel|aqua beach|jordan|uma house|uma suites|yurbban|crest hotel|crest suites|casa boutique|casa hotel|colectia|the spot|cando", re.I)
import qrcode, io
PHOTO = base64.b64encode((D.parent / "andreu.jpg").read_bytes()).decode()
def qr_b64(url):
    img = qrcode.make(url, box_size=8, border=1); buf = io.BytesIO(); img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()
CAL_URL = "https://calendly.com/hosperai-app"
AI = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY") or rm.ANTHROPIC_KEY)


def themes(reviews):
    """% de reseñas que mencionan cada tema (elogios y quejas), con Claude."""
    numbered = "\n".join(f"{i}. ({r['rating']:.0f}★) {r['text'][:500]}" for i, r in enumerate(reviews) if r["text"])
    prompt = f"""These are recent Google reviews of a hotel. Identify the main themes guests PRAISE and COMPLAIN about.
Return ONLY JSON: {{"praise": [{{"theme": "short English label (max 4 words)", "ids": [review numbers]}}], "complaints": [same]}}
Max 5 themes each, ordered by frequency. Only include a theme if at least 2 reviews mention it (for complaints, 1 is ok if serious).

Reviews:
{numbered}"""
    raw = AI.messages.create(model="claude-haiku-4-5", max_tokens=900, messages=[{"role": "user", "content": prompt}]).content[0].text
    data = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
    n = len([r for r in reviews if r["text"]]) or 1
    out = {}
    for k in ("praise", "complaints"):
        out[k] = [(t["theme"], len(set(t["ids"])), round(len(set(t["ids"])) / n * 100)) for t in data.get(k, []) if t.get("ids")]
    return out, n


def cut(t, n):
    """Corta en el final de frase más cercano por debajo de n caracteres."""
    if len(t) <= n: return t
    part = t[:n]; i = max(part.rfind(". "), part.rfind("! "), part.rfind("? "))
    return part[:i + 1] if i > n * 0.5 else part.rsplit(" ", 1)[0] + "…"


def strip_sig(reply):
    return re.sub(r"\s*(The|El equipo de|L'équipe de|Das) .{2,40}(Team)?\s*$", "", reply.strip()).strip()


def poss(n):
    return n + ("'" if n.endswith("s") else "'s")


def short(name):
    return re.sub(r"\s+(Miami Beach|South Beach Hotel|South Beach|Hotel)$", "", name).strip()


CSS = """
@page { size:A4; margin:14mm 15mm; }
body { font-family:-apple-system,Helvetica,Arial,sans-serif; color:#111827; font-size:10.5pt; line-height:1.5; }
.pb { page-break-before:always; } .head { display:flex; align-items:center; gap:12px; border-bottom:3px solid #2563eb; padding-bottom:8px; margin-bottom:12px; }
.head img { width:36px; } h1 { font-size:19pt; margin:0; letter-spacing:-.4px; } h2 { font-size:13pt; margin:16px 0 6px; color:#2563eb; }
.sub { color:#6b7280; margin:2px 0 0; font-size:9.5pt; } .letter { font-size:11.5pt; line-height:1.65; } .letter p { margin:0 0 12px; }
.kpis { display:flex; gap:8px; margin:6px 0 4px; } .kpi { flex:1; border:1px solid #e5e7eb; border-radius:8px; padding:9px; text-align:center; }
.kpi b { display:block; font-size:19pt; color:#2563eb; line-height:1.1; } .kpi.red b { color:#dc2626; } .kpi small { color:#6b7280; font-size:8.5pt; }
table { width:100%; border-collapse:collapse; } td,th { padding:4px 7px; border-bottom:1px solid #f0f1f3; font-size:9.5pt; text-align:left; }
th { background:#f9fafb; } tr.me td { background:#eff6ff; font-weight:700; }
.bar { display:inline-block; height:9px; border-radius:3px; margin-right:7px; vertical-align:middle; } .g { background:#22c55e; } .r { background:#ef4444; } .b { background:#93c5fd; }
.cols { display:flex; gap:16px; } .cols > div { flex:1; }
.rv { background:#fef2f2; border:1px solid #fecaca; border-radius:8px; padding:8px 10px; margin-top:6px; } .rvh { font-size:9pt; color:#6b7280; }
.tr { color:#6b7280; font-style:italic; margin-top:3px; font-size:9pt; }
.rp { background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px; padding:8px 10px; margin-top:5px; } .rph { font-size:9pt; font-weight:700; color:#2563eb; }
.hero1 { display:flex; gap:22px; align-items:center; margin:28px 0 18px; } .hero1 img.ph { width:150px; height:190px; object-fit:cover; border-radius:14px; }
.big { font-size:24pt; font-weight:800; letter-spacing:-.6px; line-height:1.15; margin:0 0 8px; } .blue { color:#2563eb; }
.pill { display:inline-block; background:#eff6ff; color:#1d4ed8; border-radius:20px; padding:3px 10px; font-size:9pt; font-weight:700; margin:0 4px 4px 0; }
.plans { display:flex; gap:10px; margin:10px 0; } .plan { flex:1; border:1px solid #e5e7eb; border-radius:10px; padding:10px 12px; font-size:9.5pt; }
.plan.pro { border:2px solid #2563eb; } .plan h3 { margin:0; font-size:12pt; } .plan .pr { font-size:17pt; font-weight:800; color:#111827; margin:2px 0 6px; } .plan ul { margin:0; padding-left:15px; }
.p2 td, .p2 th { font-size:9pt; padding:3px 6px; } .p2 h2 { margin:10px 0 4px; font-size:12pt; } .p2 .rv, .p2 .rp { font-size:9.5pt; }
.cta { background:#0b1020; color:#fff; border-radius:16px; padding:22px; text-align:center; margin-top:14px; display:flex; align-items:center; gap:20px; }
.cta .lk { font-size:30pt; font-weight:900; letter-spacing:-1px; color:#60a5fa; } .cta p { margin:4px 0; color:#cbd5e1; }
.box { background:#f9fafb; border-radius:8px; padding:9px 12px; margin-top:10px; } .note { color:#9ca3af; font-size:8pt; margin-top:8px; }
"""


def build(name, h, pool):
    rec = h["recent"]; n_rec = len(rec)
    rev, rat = int(float(h["reviews"])), float(h["rating"])
    unans = [r for r in rec if not r["replied"]]
    reply_rate = round((n_rec - len(unans)) / n_rec * 100) if n_rec else 0
    stars = Counter(int(r["rating"]) for r in rec)
    neg = [r for r in rec if r["rating"] <= 2]; neg_un = [r for r in neg if not r["replied"]]
    th, n_txt = themes(rec)
    mr = h.get("maps_rank") or {}
    pos = mr.get("position"); checked = mr.get("checked", 60); kw = mr.get("keyword", "boutique hotel Miami Beach")
    top = [t for t in mr.get("top", []) if not SKIP.search(t["title"] or "")][:4]
    peers = [p for p in pool if p["name"] != name and 0.7 * rev <= int(float(p["reviews"])) <= 3 * rev + 200]
    peers = sorted(peers, key=lambda p: (-float(p["rating"]), -int(float(p["reviews"]))))[:4]
    rows = peers + [h]; mx = max(int(float(p["reviews"])) for p in rows)
    nm = lambda x: re.sub(r"[\s,~]+(By At Mine Hospitality|Miami Beach|South Beach Hotel|South Beach)?[\s,~]*$", "", re.sub(r"\s*[,~].*$", "", x)).strip()
    cmp = "".join(f'<tr class="{"me" if p is h else ""}"><td>{E(nm(p["name"]))}</td><td>{float(p["rating"]):.1f}★</td>'
                  f'<td><span class="bar b" style="width:{int(float(p["reviews"])) / mx * 90:.0f}px"></span>{int(float(p["reviews"])):,}</td></tr>'
                  for p in sorted(rows, key=lambda p: -int(float(p["reviews"]))))
    dist = "".join(f'<tr><td>{"★" * s}</td><td><span class="bar {"g" if s >= 4 else "r" if s <= 2 else "b"}" style="width:{stars.get(s, 0) / max(n_rec, 1) * 220:.0f}px"></span>{stars.get(s, 0)} {"review" if stars.get(s, 0) == 1 else "reviews"}</td></tr>' for s in (5, 4, 3, 2, 1))
    pr = "".join(f'<tr><td><span style="color:#16a34a;font-weight:800">{i}.</span> {E(t)}</td></tr>' for i, (t, c, p) in enumerate(sorted(th["praise"], key=lambda x: -x[1]), 1)) or '<tr><td style="color:#9ca3af">Not enough data</td></tr>'
    co = "".join(f'<tr><td><span style="color:#dc2626;font-weight:800">{i}.</span> {E(t)}</td></tr>' for i, (t, c, p) in enumerate(sorted(th["complaints"], key=lambda x: -x[1]), 1)) or '<tr><td style="color:#9ca3af">No repeated complaints</td></tr>'
    rank_txt = (f"#{pos} of {checked}" if pos else f"Not in the top {checked}")
    client = {"name": name, "type": "hotel", "location": "Miami Beach, FL", "signature": (short(name) if short(name).startswith("The ") else "The " + short(name)) + " Team", "notify_lang": "en"}
    top_html = "".join(f"<li>{E(t['title'])} · {t['rating']}★ · {t['reviews']:,} reviews</li>" for t in top) if top else ""

    first = sorted([r for r in unans if r["text"]], key=lambda r: r["rating"])[:1]
    exhtml = ""
    for t in first:
        reply, rtr, reptr = rm.generate_response(client, "the guest", t["rating"], t["text"])
        txt = cut(t["text"], 170)
        exhtml = (f'<div class="rv"><div class="rvh">{"★" * int(t["rating"])}{"☆" * (5 - int(t["rating"]))} · {E(t["date"])} · <b style="color:#dc2626">no reply</b></div>“{E(txt)}”'
                  + (f'<div class="tr">🌐 {E(cut(rtr, 170))}</div>' if rtr else "") + '</div>'
                  f'<div class="rp"><div class="rph">Suggested reply, ready to post</div>{E(cut(strip_sig(reply), 330))}<br><i>{E(client["signature"])}</i>'
                  + (f'<div class="tr">🌐 {E(cut(reptr, 200))}</div>' if reptr else "") + '</div>')

    rank_sentence = (f'for "<i>{E(kw)}</i>" you rank <b>#{pos}</b> on Google Maps' if pos
                     else f'you don&#39;t appear in the top {checked} Google Maps results for "<i>{E(kw)}</i>"')
    page1 = f"""
<div class="head"><img src="data:image/png;base64,{LOGO}"><div><h1>Hosperai</h1><p class="sub">Google reviews on autopilot · hosperai.es</p></div></div>
<div class="hero1"><img class="ph" src="data:image/jpeg;base64,{PHOTO}"><div>
<p class="big">Hi, I'm Andreu Rey.</p>
<p style="font-size:12pt;color:#374151;margin:0 0 10px">A hospitality professional living here in Miami Beach, a few blocks from {E(short(name))}.</p>
<span class="pill">Hotel Management · UAB Barcelona</span><span class="pill">Front-desk &amp; hotel ops experience</span><span class="pill">Miami Beach local</span>
</div></div>
<div class="letter">
<p><b>To the General Manager, {E(name)}</b></p>
<p>Working in hotels, I saw the same thing every day: guests leave happy, but very few leave a review. And the reviews that do come in, especially the negative ones, often stay unanswered because the team simply has no time.</p>
<p>So I built <b>Hosperai</b>. After checkout, every guest gets a personal thank-you on WhatsApp with one-tap links to your Google and Tripadvisor page. And every new review reaches you with a reply already written in your tone and in the guest's language. You just copy and paste it.</p>
<p>I prepared the next page for you, free and with no commitment: a snapshot of {E(poss(short(name)))} Google reviews. <b>{len(unans)} of your last {n_rec} reviews have no reply</b>{f", {len(neg_un)} of them negative" if neg_un else ""}, and {rank_sentence}.</p>
<p>If it's useful, I'd love to show you how it works in 15 minutes. I'm just around the corner.</p>
<p style="margin-top:18px"><b>Andreu Rey</b><br>Founder, Hosperai<br>andreu@gethosperai.com · hosperai.es</p>
</div>"""

    page2 = f"""
<div class="pb"></div><div class="p2">
<div class="head"><img src="data:image/png;base64,{LOGO}"><div><h1>{E(name)}</h1><p class="sub">Google review report · October 2026 · your {n_rec} most recent Google reviews</p></div></div>
<div class="kpis"><div class="kpi"><b>{rat:.1f}★</b><small>Google rating</small></div><div class="kpi"><b>{rev:,}</b><small>total reviews</small></div>
<div class="kpi {"red" if reply_rate < 80 else ""}"><b>{reply_rate}%</b><small>recent reviews answered</small></div>
<div class="kpi {"red" if not pos or pos > 5 else ""}"><b>{("#" + str(pos)) if pos else "60+"}</b><small>Maps: "{E(kw)}"</small></div></div>
<div class="cols"><div><h2>What guests love most</h2><table>{pr}</table></div><div><h2>What they complain about most</h2><table>{co}</table></div></div>
<div class="cols"><div><h2>Recent ratings</h2><table>{dist}</table></div><div><h2>You vs. similar hotels nearby</h2><table><tr><th>Hotel</th><th>★</th><th>Reviews</th></tr>{cmp}</table></div></div>
<h2>An unanswered review, and the reply we'd draft</h2>{exhtml or '<p>All your recent reviews have a reply. Well done!</p>'}
<p class="note">Public Google Maps data, October 2026. Themes ordered by how often they appear in your recent reviews.</p></div>"""

    page3 = f"""
<div class="pb"></div>
<div class="head"><img src="data:image/png;base64,{LOGO}"><div><h1>Work with Hosperai</h1><p class="sub">More 5★ reviews. Every reply written for you.</p></div></div>
<h2>How it works</h2>
<div class="cols" style="gap:10px">
<div class="box" style="margin:0"><b>1 · Guests check out</b><br>Your front desk adds each guest in 10 seconds from a private link. No app, no dashboard.</div>
<div class="box" style="margin:0"><b>2 · They get a thank-you</b><br>A personal WhatsApp with one-tap Google &amp; Tripadvisor links, plus one reminder email.</div>
<div class="box" style="margin:0"><b>3 · You get the reply</b><br>Every new review on your WhatsApp, reply already written in your tone and the guest's language.</div></div>
<h2>Plans · no setup fee · no lock-in</h2>
<div class="plans">
<div class="plan"><h3>Basic</h3><div class="pr">$99<span style="font-size:10pt;color:#6b7280">/mo</span></div><ul><li>Thank-you + review links</li><li>Reminder email</li><li>AI replies on WhatsApp</li><li>Any language</li></ul></div>
<div class="plan pro"><h3>Pro <span class="pill" style="font-size:8pt">Most popular</span></h3><div class="pr">$149<span style="font-size:10pt;color:#6b7280">/mo</span></div><ul><li>Everything in Basic</li><li>NFC review cards</li><li>Mid-stay check-in</li><li>VIP messages</li><li>Monthly report like this one</li></ul></div>
<div class="plan"><h3>Business</h3><div class="pr">$199<span style="font-size:10pt;color:#6b7280">/mo</span></div><ul><li>Everything in Pro</li><li>PMS integration</li><li>Competitor report</li><li>Dedicated manager</li></ul></div></div>
<div class="box" style="text-align:center;font-size:11pt"><b>Founding partners:</b> the first 5 hotels in Miami Beach get Pro for <b>$79/month for life</b>, in exchange for an honest testimonial after 30 days.</div>
<div class="cta"><img src="data:image/png;base64,{qr_b64(CAL_URL)}" style="width:120px;height:120px;border-radius:8px;background:#fff;padding:6px">
<div style="text-align:left"><p style="font-size:12pt;color:#fff;margin:0">Book a 15-minute demo, or just say hi:</p><div class="lk">hosperai.es</div>
<p>andreu@gethosperai.com · Scan the code to pick a time</p></div></div>
<p style="text-align:center;margin-top:12px;font-size:10pt;color:#6b7280">Live in 48 hours · Works with Google, Tripadvisor &amp; WhatsApp</p>"""
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{page1}{page2}{page3}</body></html>"


if __name__ == "__main__":
    from dotenv import load_dotenv; load_dotenv(D.parent / ".env")
    data = json.loads((D / "visitas_miami_beach.json").read_text())
    pool = [r for r in csv.DictReader(open(D / "florida_hotels_independientes.csv"))
            if "33139" in r["address"] and r["reviews"] and r["type"] in ("Hotel", "Bed & breakfast", "Inn", "Resort hotel") and not SKIP.search(r["name"])]
    OUT.mkdir(exist_ok=True)
    for name, h in data.items():
        if SKIP.search(name):
            continue
        out = OUT / f"{name} - Hosperai.pdf"
        html_to_pdf(build(name, h, pool), str(out))
        print("✓", out.name)
