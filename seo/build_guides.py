"""Genera las guías SEO (EN /guides/..., ES /es/...) + sitemap.xml. Ejecutar tras editar contenidos."""
import json, html, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
SITE = "https://hosperai.es"
CAL = "https://calendly.com/hosperai-app"

CSS = """
:root{--bg:#0b0d12;--card:#12151c;--text:#e5e7eb;--muted:#9ca3af;--blue:#3b82f6;--line:#232734;--soft:#151a24}
html[data-theme=light]{--bg:#f7f8fb;--card:#fff;--text:#111827;--muted:#6b7280;--blue:#2563eb;--line:#e5e7eb;--soft:#eff6ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,-apple-system,Helvetica,Arial,sans-serif;line-height:1.7;font-size:17px}
a{color:var(--blue)}header{border-bottom:1px solid var(--line)}header .in{max-width:860px;margin:0 auto;padding:14px 20px;display:flex;justify-content:space-between;align-items:center}
.logo{display:flex;align-items:center;gap:9px;color:var(--text);text-decoration:none;font-weight:800}.logo img{width:28px}
.btn{display:inline-block;background:#2563eb;color:#fff;text-decoration:none;font-weight:700;padding:11px 18px;border-radius:10px;font-size:15px}
main{max-width:760px;margin:0 auto;padding:40px 20px 60px}.crumb{font-size:13px;color:var(--muted)}h1{font-size:clamp(30px,5vw,42px);line-height:1.15;letter-spacing:-1px;margin:10px 0 14px}
.lead{font-size:19px;color:var(--muted)}h2{font-size:25px;letter-spacing:-.4px;margin:40px 0 10px}h3{font-size:19px;margin:26px 0 6px}
.tpl{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--blue);border-radius:10px;padding:14px 16px;margin:12px 0;font-size:15.5px}
.tpl b{display:block;font-size:12px;text-transform:uppercase;letter-spacing:.8px;color:var(--blue);margin-bottom:4px}
.cta{background:var(--soft);border:1px solid var(--line);border-radius:16px;padding:24px;margin:40px 0;text-align:center}.cta h3{margin-top:0}
.cta p{color:var(--muted);margin:6px 0 16px}.more{display:grid;gap:10px;margin-top:14px}.more a{display:block;padding:12px 14px;border:1px solid var(--line);border-radius:10px;text-decoration:none;color:var(--text);font-weight:600}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:13px;text-align:center;padding:24px 20px}ul,ol{padding-left:22px}li{margin:6px 0}
"""

def page(lang, slug, title, desc, h1, lead, body, faqs, related):
    url = f"{SITE}/{'es/' if lang=='es' else 'guides/'}{slug}/"
    home = SITE + ("/index-es.html" if lang == "es" else "/")
    t = {"en": dict(home="Home", guides="Guides", cta_t="Get more reviews without lifting a finger",
                     cta_p="Hosperai sends every customer a thank-you on WhatsApp with one-tap review links, and drafts a reply to every new review in your tone. Live in 48 hours, from $99/month.",
                     b1="See how it works", b2="Book a 15-min call", rel="Keep reading", faq="Frequently asked questions"),
         "es": dict(home="Inicio", guides="Guías", cta_t="Más reseñas sin mover un dedo",
                     cta_p="Hosperai envía a cada cliente un agradecimiento por WhatsApp con enlaces directos para dejar reseña, y te prepara la respuesta a cada reseña nueva en tu tono. En marcha en 48 horas, desde 99 $/mes.",
                     b1="Mira cómo funciona", b2="Reservar llamada de 15 min", rel="Sigue leyendo", faq="Preguntas frecuentes")}[lang]
    faq_html = "".join(f"<h3>{html.escape(q)}</h3><p>{a}</p>" for q, a in faqs)
    rel_html = "".join(f'<a href="{u}">{html.escape(n)} →</a>' for n, u in related)
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": h1, "description": desc, "inLanguage": lang,
           "author": {"@type": "Person", "name": "Andreu Rey"}, "publisher": {"@type": "Organization", "name": "Hosperai", "logo": {"@type": "ImageObject", "url": SITE + "/assets/logo-icon-clean.png"}},
           "datePublished": "2026-10-01", "dateModified": "2026-10-01", "mainEntityOfPage": url, "image": SITE + "/media/og-hosperai.jpg"},
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in faqs]},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": t["home"], "item": home},
              {"@type": "ListItem", "position": 2, "name": h1, "item": url}]}]
    return f"""<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="article"><meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}/media/og-hosperai.jpg"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon.png"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<script>try{{var t=localStorage.getItem('hospera-theme')||'dark';document.documentElement.setAttribute('data-theme',t)}}catch(e){{}}</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-5FF36XXR3L"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-5FF36XXR3L');</script>
<style>{CSS}</style><script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script></head><body>
<header><div class="in"><a class="logo" href="{home}"><img src="/assets/logo-icon-clean.png" alt="Hosperai">Hosperai</a><a class="btn" href="{CAL}" onclick="gtag('event','book_call_click')">{t['b2']}</a></div></header>
<main><div class="crumb"><a href="{home}">{t['home']}</a> › {t['guides']}</div><h1>{h1}</h1><p class="lead">{lead}</p>
{body}
<div class="cta"><h3>{t['cta_t']}</h3><p>{t['cta_p']}</p><a class="btn" href="{home}#calculator">{t['b1']}</a> &nbsp; <a class="btn" style="background:transparent;color:var(--blue);border:1px solid var(--line)" href="{CAL}">{t['b2']}</a></div>
<h2>{t['faq']}</h2>{faq_html}
<h2>{t['rel']}</h2><div class="more">{rel_html}</div></main>
<footer>© 2026 Hosperai · 1935 Park Ave #1, Miami Beach, FL · <a href="/privacy">Privacy</a> · <a href="/terms">Terms</a></footer></body></html>"""

from guides_content import GUIDES  # noqa: E402

urls = [(SITE + "/", "1.0"), (SITE + "/index-es.html", "1.0"), (SITE + "/demo", "0.6"), (SITE + "/demo-clinic", "0.6"),
        (SITE + "/privacy", "0.2"), (SITE + "/terms", "0.2")]
for g in GUIDES:
    folder = ROOT / ("es" if g["lang"] == "es" else "guides") / g["slug"]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "index.html").write_text(page(**g))
    urls.append((f"{SITE}/{'es' if g['lang']=='es' else 'guides'}/{g['slug']}/", "0.8"))
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + \
     "".join(f"  <url><loc>{u}</loc><lastmod>2026-10-01</lastmod><priority>{p}</priority></url>\n" for u, p in urls) + "</urlset>\n"
(ROOT / "sitemap.xml").write_text(sm)
print(len(GUIDES), "guías ·", len(urls), "URLs en sitemap")
