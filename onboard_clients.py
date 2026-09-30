"""
Alta de clientes desde el formulario https://hosperai-onboarding.netlify.app
(Netlify Forms) → clients.json, que review_monitor.py carga solo.

  python3 onboard_clients.py                 # descarga respuestas nuevas y lista clientes
  python3 onboard_clients.py --approve slug  # activa un cliente (empieza a monitorizar y le llega el WhatsApp de bienvenida)
  python3 onboard_clients.py --pause slug    # lo desactiva
"""
import json, re, subprocess, argparse, requests, warnings, hmac, hashlib, os, urllib.parse
from pathlib import Path
warnings.filterwarnings("ignore")
from review_monitor import SERPAPI_KEY  # noqa: E402

FORM_ID = "6abd2e3ba00054000889f57c"
SITE = "https://hosperai-onboarding.netlify.app"
from dotenv import load_dotenv
load_dotenv(Path.home() / "hospera" / ".env")
CHECKIN_SECRET = os.getenv("CHECKIN_SECRET", "")


def checkin_link(c):
    t = hmac.new(CHECKIN_SECRET.encode(), c["slug"].encode(), hashlib.sha256).hexdigest()[:16]
    return f"{SITE}/checkin/?h={c['slug']}&t={t}&n={urllib.parse.quote(c['name'])}"


def publish_review_page(c):
    """Página hosperai.es/r/<slug>.html (elige Google/TripAdvisor) → se publica con git push."""
    if not c.get("place_id"):
        print("  ⚠️  Sin place_id: no puedo crear el enlace de reseña de Google")
        return
    google = f"https://search.google.com/local/writereview?placeid={c['place_id']}"
    lang = "es" if c["notify_lang"] == "es" else "en"
    home = Path.home() / "hospera"
    subprocess.run(["python3", "generate_choice_page.py", c["name"], google, "--lang", lang, "--slug", c["slug"]], cwd=home, check=True)
    subprocess.run(["git", "add", f"r/{c['slug']}.html"], cwd=home, check=True)
    subprocess.run(["git", "commit", "-q", "-m", f"Página de reseña para {c['name']}"], cwd=home)
    subprocess.run(["git", "push", "-q", "origin", "HEAD"], cwd=home, capture_output=True)
    print(f"  🔗 Página de reseña: https://hosperai.es/r/{c['slug']}.html")
FILE = Path.home() / "hospera" / "clients.json"
LANG = {"English": "en", "Español": "es", "Català": "es"}


def fetch_submissions():
    r = requests.get(f"{SITE}/api/onboarding", params={"key": CHECKIN_SECRET}, timeout=30)
    r.raise_for_status()
    return r.json()


def email_me(c):
    """Aviso a hosperai.app@gmail.com con los datos del hotel nuevo (Gmail SMTP del .env)."""
    import smtplib
    from email.mime.text import MIMEText
    user, pwd = os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_APP_PASSWORD")
    if not (user and pwd):
        return
    lines = [f"{k}: {v if not isinstance(v, list) else ', '.join(v)}" for k, v in c.items() if k not in ("submission_id",)]
    body = "Nuevo cliente desde el formulario de alta:\n\n" + "\n".join(lines) + \
           f"\n\nPara activarlo:\n  cd ~/hospera && python3 onboard_clients.py --approve {c['slug']}"
    msg = MIMEText(body)
    msg["Subject"] = f"🆕 Nuevo cliente Hosperai: {c['name']}"
    msg["From"] = user
    msg["To"] = "hosperai.app@gmail.com"
    with smtplib.SMTP("smtp.gmail.com", 587) as srv:
        srv.starttls(); srv.login(user, pwd); srv.send_message(msg)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def find_place(d):
    """data_id (para leer reseñas) y place_id (para el enlace 'escribir reseña'), con 1 búsqueda de SerpAPI."""
    url_id = None
    try:
        url = requests.get(d.get("google_url") or "", timeout=15, allow_redirects=True).url
        m = re.search(r"(0x[0-9a-f]+:0x[0-9a-f]+)", url)
        url_id = m.group(1) if m else None
    except requests.RequestException:
        pass
    q = f"{d.get('business_name', '')} {d.get('address', '')}".strip()
    r = requests.get("https://serpapi.com/search", params={"engine": "google_maps", "type": "search", "q": q,
                     "api_key": SERPAPI_KEY}, timeout=30).json()
    place = r.get("place_results") or (r.get("local_results") or [{}])[0]
    return url_id or place.get("data_id"), place.get("place_id")


SCENARIOS = {
    "1": ("Nice location but the room was really small for the price.", {
        "A": "Thank you, Maria! We're sorry the room felt small — our rooms are cozy by design, and next time just ask us about our larger categories.",
        "B": "Dear Ms. Thompson, thank you for your feedback. We apologise for not meeting your expectations and have shared your comments with our team.",
        "C": "Thanks for staying with us, Maria — noted, and we hope to welcome you back soon."}),
    "2": ("Amazing stay, the staff were so kind and the breakfast was delicious!", {
        "A": "Maria, this made our day! 🙌 We'll pass your kind words to the team — see you next time!",
        "B": "Dear Ms. Thompson, thank you for your wonderful review. It was a pleasure to host you, and we look forward to welcoming you again.",
        "C": "Thank you, Maria! So glad you enjoyed it."}),
    "3": ("Couldn't sleep, very noisy street at night.", {
        "A": "We're sorry, Maria — the street can get lively. Next time ask for one of our courtyard rooms, they're much quieter, and we have earplugs at reception.",
        "B": "Dear Ms. Thompson, we sincerely apologise for the disturbance. Your feedback has been forwarded to our management team.",
        "C": "Thanks for the feedback, Maria — we'll keep working on it."}),
}


def to_client(sub):
    d = sub["data"]
    name = d.get("business_name", "").strip()
    lang = LANG.get(d.get("notify_lang"), "en")
    phone = re.sub(r"[^\d+]", "", d.get("whatsapp", ""))
    if phone and not phone.startswith("+"):
        phone = "+1" + phone if len(phone) == 10 else "+" + phone
    return {
        "submission_id": sub["id"], "status": "pending", "slug": slugify(name),
        "name": name, "tripadvisor_id": None,
        "type": (d.get("business_type") or "negocio").lower(), "location": d.get("address", ""),
        "signature": d.get("signature") or (f"The team at {name}" if lang == "en" else f"El equipo de {name}"),
        "phone": f"whatsapp:{phone}", "notify_lang": lang,
        "tone": d.get("tone", ""), "always_mention": d.get("always_mention", ""), "never_say": d.get("never_say", ""),
        "style": {k: d.get(k, "") for k in ("formality", "length", "use_name", "emojis", "apologise", "take_offline",
                                             "complaint_contact", "compensation", "highlights", "recurring_complaints", "not_offered")},
        "voice_examples": [{"review": SCENARIOS[n][0], "reply": SCENARIOS[n][1][d[f"scenario_{n}"]]}
                           for n in SCENARIOS if d.get(f"scenario_{n}") in SCENARIOS[n][1]],
        "manager_email": d.get("contact_email", ""), "contact_name": d.get("contact_name", ""),
        "services": d.get("services") or [], "pms": d.get("pms", ""), "notes": d.get("notes", ""),
        "google_url": d.get("google_url", ""), "created": sub.get("created_at", ""),
        "data_id": None, "place_id": None,
    } | dict(zip(("data_id", "place_id"), find_place(d)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--approve"); ap.add_argument("--pause")
    a = ap.parse_args()
    clients = json.loads(FILE.read_text()) if FILE.exists() else []
    known = {c["submission_id"] for c in clients}

    for sub in fetch_submissions():
        if sub["id"] not in known:
            c = to_client(sub)
            clients.append(c)
            print(f"🆕 {c['name']} ({c['phone']}) — data_id: {c['data_id'] or '⚠️ NO ENCONTRADO'}")
            try:
                email_me(c)
            except Exception as e:
                print(f"  ⚠️  No pude mandarte el email: {e}")

    for slug, status in ((a.approve, "active"), (a.pause, "paused")):
        if slug:
            c = next((c for c in clients if c["slug"] == slug), None)
            if not c:
                raise SystemExit(f"No existe el cliente '{slug}'")
            if status == "active" and not c["data_id"]:
                raise SystemExit(f"'{slug}' no tiene data_id de Google Maps — añádelo a mano en clients.json")
            c["status"] = status
            print(f"{'✅ Activado' if status == 'active' else '⏸️  Pausado'}: {c['name']}")
            if status == "active":
                publish_review_page(c)
                print(f"  🛎️  Enlace de check-in para recepción:\n     {checkin_link(c)}")

    FILE.write_text(json.dumps(clients, indent=2, ensure_ascii=False))
    print(f"\n{len(clients)} clientes del formulario:")
    for c in clients:
        print(f"  [{c['status']:7}] {c['slug']:30} {c['phone']:22} {c['notify_lang']}  {', '.join(c['services'])}")
        if c["status"] == "active":
            print(f"            check-in: {checkin_link(c)}")


if __name__ == "__main__":
    main()
