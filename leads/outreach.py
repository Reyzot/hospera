"""
Envío de la campaña de emails a hoteles (Zoho SMTP andreu@gethosperai.com), sin prisas y sin repetir.

launchd lo ejecuta cada 10 min. En cada pasada:
  1. Lee la bandeja (IMAP): quien ha respondido sale de la secuencia (y se avisa a Andreu); rebotes → "Rebotó".
  2. Si es día laborable, 9:00–16:00 (hora del Mac = Miami), no se ha llegado al máximo de hoy y ya pasó
     el hueco aleatorio desde el último envío (20–40 min): manda UN email.
     Primero los seguimientos que tocan (email 2 a los 3 días laborables, email 3 a los 7), luego hoteles nuevos.
  3. Actualiza outreach_state.json (fuente de verdad) y ~/Desktop/Hosperai_Envios.xlsx.

Máximo diario (nuevos + seguimientos), subida progresiva para calentar el dominio:
  semana 1: 10 · semana 2: 15 · semana 3: 25 · desde la 4: 35

  python3 outreach.py            # una pasada normal
  python3 outreach.py --status   # resumen
  python3 outreach.py --pause / --resume
"""
import os, re, json, random, smtplib, imaplib, email, argparse, sys
from email.mime.text import MIMEText
from email.utils import formataddr, make_msgid, parseaddr
from email.header import decode_header, make_header
from datetime import datetime, date, timedelta
from pathlib import Path
from dotenv import load_dotenv

D = Path(__file__).parent
load_dotenv(D.parent / ".env")
sys.path.insert(0, str(D))
import outreach_excel

STATE, META = D / "outreach_state.json", D / "outreach_meta.json"
USER, PWD = os.getenv("ZOHO_EMAIL"), os.getenv("ZOHO_APP_PASSWORD")
NOTIFY_TO = "andreurey7@gmail.com"
FOOTER = "\n\n—\nNot the right person, or not interested? Just reply \"no\" and I won't email again."
DAILY_CAP = [10, 15, 25, 35]          # por semana desde el primer envío
HOURS = (9, 16)                        # ventana de envío (hora local del Mac)
GAP_MIN = (20, 40)                     # minutos entre envíos
FOLLOWUP_DAYS = {2: 3, 3: 7}           # email 2 a los 3 días laborables del 1; email 3 a los 7
STOP_WORDS = re.compile(r"\b(no|not interested|unsubscribe|remove|stop|not now|no thanks|no gracias)\b", re.I)


def load(p, default):
    return json.loads(p.read_text()) if p.exists() else default


def save(state, meta):
    STATE.write_text(json.dumps(state, indent=1, ensure_ascii=False))
    META.write_text(json.dumps(meta, indent=1))
    try:
        outreach_excel.build()
    except Exception as e:
        print("⚠️ Excel no actualizado:", e)


def add_business_days(d, n):
    while n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def cap_today(meta):
    if not meta.get("first_send"):
        return DAILY_CAP[0]
    weeks = (date.today() - date.fromisoformat(meta["first_send"])).days // 7
    return DAILY_CAP[min(weeks, len(DAILY_CAP) - 1)]


def send(to, subject, body, reply_to_id=None):
    msg = MIMEText(body + FOOTER, "plain", "utf-8")
    msg["Subject"], msg["From"], msg["To"] = subject, formataddr(("Andreu Rey", USER)), to
    mid = make_msgid(domain="gethosperai.com")
    msg["Message-ID"] = mid
    if reply_to_id:
        msg["In-Reply-To"] = msg["References"] = reply_to_id
    with smtplib.SMTP_SSL("smtppro.zoho.com", 465, timeout=60) as s:
        s.login(USER, PWD)
        s.send_message(msg)
    return mid


def notify(subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"], msg["From"], msg["To"] = subject, formataddr(("Hosperai Envíos", USER)), NOTIFY_TO
    with smtplib.SMTP_SSL("smtppro.zoho.com", 465, timeout=60) as s:
        s.login(USER, PWD)
        s.send_message(msg)


def text_of(m):
    if m.is_multipart():
        for part in m.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "ignore")
        return ""
    return m.get_payload(decode=True).decode(m.get_content_charset() or "utf-8", "ignore")


def check_inbox(state, meta):
    """Respuestas y rebotes. Solo mira correos nuevos desde el último UID revisado."""
    by_email = {r["email"].lower(): r for r in state}
    by_domain = {r["email"].split("@")[1].lower(): r for r in state
                 if r["email"].split("@")[1].lower() not in ("gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "msn.com", "icloud.com", "bellsouth.net", "comcast.net")}
    try:
        im = imaplib.IMAP4_SSL("imappro.zoho.com", 993, timeout=60)
        im.login(USER, PWD)
    except Exception as e:
        print("⚠️ IMAP no disponible:", e)
        return False
    im.select("INBOX", readonly=True)
    last = meta.get("last_uid", 0)
    _, data = im.uid("search", None, f"UID {last + 1}:*")
    for uid in [int(x) for x in data[0].split()] if data and data[0] else []:
        if uid <= last:
            continue
        _, msgdata = im.uid("fetch", str(uid), "(RFC822)")
        m = email.message_from_bytes(msgdata[0][1])
        sender = parseaddr(m.get("From", ""))[1].lower()
        subj = str(make_header(decode_header(m.get("Subject", ""))))
        body = text_of(m)
        meta["last_uid"] = uid
        if sender.startswith(("mailer-daemon", "postmaster")) or "undeliver" in subj.lower() or "delivery status" in subj.lower():
            for addr in re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", body):
                r = by_email.get(addr.lower())
                if r and r["status"] not in ("Respondió", "No interesado"):
                    r["status"], r["notes"], r["next_due"] = "Rebotó", "Email no existe", ""
                    print("↩️  Rebote:", r["name"])
                    break
            continue
        r = by_email.get(sender) or by_domain.get(sender.split("@")[-1])
        if not r or r["status"] in ("Respondió", "No interesado"):
            continue
        first_line = body.strip().split("\n")[0][:200]
        r["replied"] = date.today().isoformat()
        r["next_due"] = ""
        if STOP_WORDS.search(first_line) and len(first_line) < 60:
            r["status"], r["notes"] = "No interesado", first_line
        else:
            r["status"], r["notes"] = "Respondió", first_line
        print(f"💬 {r['name']} ha respondido: {first_line}")
        try:
            notify(f"💬 {r['name']} ha respondido ({r['status']})",
                   f"Hotel: {r['name']} ({r['city']})\nEmail: {r['email']}\nTeléfono: {r['phone']}\nWeb: {r['website']}\n"
                   f"Nota Google: {r['rating']}★ · {r['reviews']} reseñas\n\nSu respuesta:\n{body[:1500]}\n\n"
                   f"Contéstale desde andreu@gethosperai.com (o dile a Claude que te prepare la respuesta).")
        except Exception as e:
            print("⚠️ No pude avisarte por email:", e)
    im.logout()
    return True


def next_job(state):
    today = date.today().isoformat()
    for r in state:  # seguimientos que ya tocan
        if r["status"] in ("Email 1 enviado", "Email 2 enviado") and r["next_due"] and r["next_due"] <= today:
            return r, 2 if r["status"] == "Email 1 enviado" else 3
    for r in state:
        if r["status"] == "Pendiente":
            return r, 1
    return None, None


def run():
    state, meta = load(STATE, []), load(META, {})
    if meta.get("paused"):
        print("⏸️  Envíos en pausa"); return
    inbox_ok = check_inbox(state, meta)
    now = datetime.now()
    today = date.today().isoformat()
    if meta.get("day") != today:
        meta.update(day=today, sent_today=0, gap=random.randint(*GAP_MIN))
    if now.weekday() >= 5 or not (HOURS[0] <= now.hour < HOURS[1]):
        save(state, meta); print("🕘 Fuera de horario"); return
    if not inbox_ok:
        save(state, meta); print("⏳ Sin IMAP no envío (no sabría quién ha respondido)"); return
    if meta["sent_today"] >= cap_today(meta):
        save(state, meta); print(f"✅ Máximo de hoy alcanzado ({meta['sent_today']})"); return
    last = meta.get("last_send")
    if last and (now - datetime.fromisoformat(last)).total_seconds() < meta["gap"] * 60:
        save(state, meta); print("⏳ Esperando hueco entre envíos"); return

    r, step = next_job(state)
    if not r:
        save(state, meta); print("🎉 No queda nadie por contactar"); return
    subject = r["subject"] if step == 1 else f"Re: {r['subject']}"
    try:
        mid = send(r["email"], subject, r[f"email_{step}"], r.get("message_id") if step > 1 else None)
    except smtplib.SMTPRecipientsRefused:
        r["status"], r["notes"] = "Rebotó", "Dirección rechazada"
        save(state, meta); return
    if step == 1:
        r["message_id"] = mid
    r[f"sent_{step}"] = today
    r["status"] = f"Email {step} enviado"
    r["next_due"] = add_business_days(date.today(), FOLLOWUP_DAYS[step + 1] - (FOLLOWUP_DAYS[step] if step > 1 else 0)).isoformat() if step < 3 else ""
    meta["first_send"] = meta.get("first_send") or today
    meta["sent_today"] += 1
    meta["last_send"] = now.isoformat(timespec="seconds")
    meta["gap"] = random.randint(*GAP_MIN)
    save(state, meta)
    print(f"📤 Email {step} → #{r['n']} {r['name']} ({r['email']}) · hoy {meta['sent_today']}/{cap_today(meta)}")


def status():
    state, meta = load(STATE, []), load(META, {})
    from collections import Counter
    print(Counter(r["status"] for r in state))
    print("Hoy:", meta.get("sent_today", 0), "/", cap_today(meta), "· pausa:", bool(meta.get("paused")), "· primer envío:", meta.get("first_send"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true"); ap.add_argument("--pause", action="store_true"); ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    if a.status: status()
    elif a.pause or a.resume:
        meta = load(META, {}); meta["paused"] = a.pause; META.write_text(json.dumps(meta, indent=1)); print("⏸️ Pausado" if a.pause else "▶️ Reanudado")
    else: run()
