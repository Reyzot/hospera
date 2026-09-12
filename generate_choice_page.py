"""
Genera la página estática "elige dónde dejar tu reseña" (Google o TripAdvisor)
para un cliente. Se sube al repo de la web (carpeta r/) y se despliega con el
resto del sitio en Netlify.

Uso:
  python3 generate_choice_page.py "Uma House" "https://g.page/r/.../review" "https://www.tripadvisor.com/UserReviewEdit-..." --lang es
"""
import argparse
from pathlib import Path

GOOGLE_ICON = '<svg viewBox="0 0 24 24" fill="#4285F4" xmlns="http://www.w3.org/2000/svg"><path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/></svg>'
TRIPADVISOR_ICON = '<svg viewBox="0 0 24 24" fill="#34E0A1" xmlns="http://www.w3.org/2000/svg"><path d="M12.006 4.295c-2.67 0-5.338.784-7.645 2.353H0l1.963 2.135a5.997 5.997 0 0 0 4.04 10.43 5.976 5.976 0 0 0 4.075-1.6L12 19.705l1.922-2.09a5.972 5.972 0 0 0 4.072 1.598 6 6 0 0 0 6-5.998 5.982 5.982 0 0 0-1.957-4.432L24 6.648h-4.35a13.573 13.573 0 0 0-7.644-2.353zM12 6.255c1.531 0 3.063.303 4.504.903C13.943 8.138 12 10.43 12 13.1c0-2.671-1.942-4.962-4.504-5.942A11.72 11.72 0 0 1 12 6.256zM6.002 9.157a4.059 4.059 0 1 1 0 8.118 4.059 4.059 0 0 1 0-8.118zm11.992.002a4.057 4.057 0 1 1 .003 8.115 4.057 4.057 0 0 1-.003-8.115zm-11.992 1.93a2.128 2.128 0 0 0 0 4.256 2.128 2.128 0 0 0 0-4.256zm11.992 0a2.128 2.128 0 0 0 0 4.256 2.128 2.128 0 0 0 0-4.256z"/></svg>'

STRINGS = {
    "es": {"title": "¿Dónde prefieres dejar tu opinión?", "sub": "Gracias por tu tiempo — elige la plataforma que prefieras.", "thanks": "Se abrirá en una pestaña nueva."},
    "en": {"title": "Where would you like to leave your review?", "sub": "Thanks for your time — pick whichever platform you prefer.", "thanks": "It'll open in a new tab."},
}

def render(business_name, google_link, tripadvisor_link, lang="es"):
    t = STRINGS.get(lang, STRINGS["es"])
    buttons = ""
    if google_link:
        buttons += f'<a href="{google_link}" target="_blank" class="choice-btn">{GOOGLE_ICON}<span>Google</span></a>'
    if tripadvisor_link:
        buttons += f'<a href="{tripadvisor_link}" target="_blank" class="choice-btn">{TRIPADVISOR_ICON}<span>TripAdvisor</span></a>'

    return f"""<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{business_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@600;700;800&display=swap" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Inter',-apple-system,sans-serif; background:#f9fafb; min-height:100vh; display:flex; align-items:center; justify-content:center; padding:24px; }}
  .card {{ background:#fff; border-radius:20px; padding:36px 28px; max-width:360px; width:100%; text-align:center; box-shadow:0 4px 20px rgba(0,0,0,0.08); }}
  h1 {{ font-size:19px; font-weight:800; color:#111827; margin-bottom:8px; }}
  p {{ font-size:13.5px; color:#6b7280; margin-bottom:24px; }}
  .biz-name {{ font-size:12px; font-weight:700; color:#2563eb; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px; }}
  .choice-btn {{ display:flex; align-items:center; gap:12px; background:#f9fafb; border:1px solid #e5e7eb; border-radius:12px; padding:16px 18px; margin-bottom:12px; text-decoration:none; color:#111827; font-weight:700; font-size:15px; transition:border-color .2s,background .2s; }}
  .choice-btn:hover {{ border-color:#2563eb; background:#eff6ff; }}
  .choice-btn svg {{ width:26px; height:26px; flex-shrink:0; }}
  .footnote {{ font-size:11px; color:#9ca3af; margin-top:18px; }}
</style></head><body>
  <div class="card">
    <div class="biz-name">{business_name}</div>
    <h1>{t['title']}</h1>
    <p>{t['sub']}</p>
    {buttons}
    <div class="footnote">{t['thanks']} · hosperai.es</div>
  </div>
</body></html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('business_name')
    parser.add_argument('google_link', nargs='?', default='')
    parser.add_argument('tripadvisor_link', nargs='?', default='')
    parser.add_argument('--lang', default='es', choices=['es', 'en'])
    parser.add_argument('--slug', default=None, help='nombre del archivo, por defecto se deriva del nombre del negocio')
    args = parser.parse_args()

    slug = args.slug or args.business_name.lower().replace(' ', '-').replace("'", '')
    out_dir = Path.home() / 'hospera' / 'r'
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f'{slug}.html'
    out_path.write_text(render(args.business_name, args.google_link, args.tripadvisor_link, args.lang))
    print(f"✅ Página generada: {out_path}")
    print(f"   Se subirá a: https://hosperai.es/r/{slug}.html (tras hacer git push)")


if __name__ == '__main__':
    main()
