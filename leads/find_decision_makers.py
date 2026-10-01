"""Busca en la web de cada negocio emails de quien decide (dirección, operaciones, ventas, dueño)
y los prioriza sobre los genéricos (info@, reservations@, frontdesk@) que suele borrar recepción.

  python3 leads/find_decision_makers.py          # hoteles + clínicas pendientes
Actualiza outreach_state.json / outreach_clinics_state.json: email = el mejor encontrado,
email_generic = el genérico de antes (por si rebota), email_role = tipo de contacto.
"""
import json, re, requests, warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
warnings.filterwarnings("ignore")
D = Path(__file__).parent
H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
EMRE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PATHS = ["", "/contact", "/contact-us", "/about", "/about-us", "/our-team", "/team", "/staff", "/meet-the-team",
         "/our-story", "/management", "/sales", "/groups", "/group-sales", "/meetings", "/events", "/weddings",
         "/careers", "/press", "/media", "/partners", "/meet-our-team", "/our-staff", "/doctors", "/meet-the-doctor"]
BAD = re.compile(r"\.(png|jpe?g|gif|svg|webp|css|js)$|example\.|sentry|wixpress|domain\.|yourname|email\.com|@2x|godaddy|"
                 r"squarespace|schema\.org|u00|privacy@|abuse@|webmaster@|noreply|no-reply|careers@|jobs@|hr@|recruit", re.I)
# rango: menor = mejor
ROLE = [(0, "Dirección", r"^(gm|generalmanager|general\.manager|owner|owners|ceo|president|director|md|managingdirector|principal|innkeeper|proprietor|hotelmanager|manager)\b"),
        (1, "Operaciones", r"^(operations|ops|opsmanager|operationsmanager|hotelops|admin|administrator|officemanager|office\.manager|practicemanager|practice\.manager)\b"),
        (2, "Ventas / marketing", r"^(sales|dos|directorofsales|groups|groupsales|events|marketing|revenue|partnerships|business)\b"),
        (3, "Persona", None),
        (5, "Genérico", r".*")]
GENERIC = re.compile(r"^(info|information|reservations?|reserve|frontdesk|front\.desk|desk|stay|hello|hi|contact|contactus|office|booking|bookings|"
                     r"concierge|support|guestservices|guest|guests|inquiry|inquiries|enquiries|welcome|mail|email|team|general|reception|"
                     r"rooms|hotel|inn|resort|appointments?|schedule|scheduling|front|patients?|care|smile|dental|dentist|clinic|spa)$", re.I)


NOT_PERSON = re.compile(r"^(accessibility|press|media|pr|production|privacy|billing|accounting|accounts|finance|legal|security|maintenance|"
                        r"housekeeping|it|tech|web|inquires|enquire|feedback|reviews|newsletter|news|orders|shop|store|gift|giftcards|"
                        r"jobs|careers|hr|lostandfound|lost|valet|parking|restaurant|bar|dining|diningroom|kitchen|chef|catering|"
                        r"weddings?|spa|fitness|pool|beach|tours?|activities|transport|shuttle|groupsales)$", re.I)
NAMES = set("""aaron adam adrian alex alexander alice alicia allison amanda amber amy ana andrea andrew angela anna anne anthony ashley barbara ben benjamin beth
betty bill bob bonnie brad brandon brenda brian brittany brooke bruce carl carla carlos carol caroline carolyn catherine charles chris christina christine
christopher cindy claire colleen courtney craig crystal cynthia dan dana daniel danielle david dawn deb debbie deborah debra denise dennis diana diane donna
doug douglas dylan ed edward elena elizabeth ellen emily emma eric erica erin eva evan frank gary george gina greg gregory hannah heather helen holly
jack jacob james jamie jan jane janet jason jay jean jeff jeffrey jen jenna jennifer jenny jeremy jerry jessica jill jim jo joan joe john jon jonathan
jordan jose joseph josh joshua joy joyce juan judy julia julie justin karen kate katherine kathleen kathy katie kay keith kelly ken kevin kim kimberly
kristen kristin kyle laura lauren lee leslie linda lindsay lisa liz lori luis lynn maria marie marilyn mark martha martin mary matt matthew megan
melissa michael michele michelle mike molly monica nancy natalie nathan nicholas nick nicole pam pamela pat patricia patrick paul peter rachel ray
rebecca richard rick rob robert robin ron ronald rose ruth ryan sam samantha sandra sandy sara sarah scott sean sharon shawn stephanie stephen steve
steven sue susan tammy tara teresa terri terry thomas tim timothy tina todd tom tony tracy travis tyler valerie vanessa victoria vincent walter wendy
william zach kiya gary brooke ana sofia carmen javier miguel pedro pablo laura lucia marta""".split())


def is_person(local):
    parts = re.split(r"[._-]", local)
    if parts[0] in NAMES and all(p.isalpha() for p in parts) and len(parts) <= 2:
        return True
    return bool(re.fullmatch(r"[a-z][a-z]{3,14}", local) and local[1:] in NAMES) or (len(parts) == 2 and parts[0] in NAMES)


def rank(email):
    local = email.split("@")[0].lower()
    if GENERIC.match(local):
        return 5, "Genérico"
    if NOT_PERSON.match(local):
        return 9, "Otro"
    for r, name, pat in ROLE:
        if pat is None:
            if is_person(local):
                return r, name
            continue
        if re.match(pat, local):
            return r, name
    return 9, "Otro"


def crawl(url):
    base = re.match(r"https?://[^/]+", url)
    base = base.group(0) if base else url.rstrip("/")
    dom = re.sub(r"^www\.", "", base.split("//")[-1]).lower()
    root = dom.split(".")[-2] if "." in dom else dom
    found = set()
    for p in PATHS:
        try:
            r = requests.get(base + p, headers=H, timeout=8, verify=False)
            if r.status_code != 200:
                continue
            t = r.text.replace("&#64;", "@").replace("[at]", "@").replace("%40", "@").replace("(at)", "@")
        except Exception:
            continue
        for e in EMRE.findall(t):
            e = e.strip(".").lower()
            d = e.split("@")[1]
            if not BAD.search(e) and (root in d or d in dom):
                found.add(e)
    return sorted(found, key=lambda e: rank(e)[0])


def run(fname):
    path = D / fname
    rows = json.loads(path.read_text())
    todo = [r for r in rows if r["status"] == "Pendiente" and r.get("website")]
    with ThreadPoolExecutor(24) as ex:
        res = list(ex.map(lambda r: crawl(r["website"]), todo))
    changed = 0
    for r, emails in zip(todo, res):
        cur_rank = rank(r["email"])[0]
        best = next((e for e in emails if rank(e)[0] < min(cur_rank, 5)), None)
        if cur_rank == 9:   # el email que teníamos no es ni persona ni genérico claro: lo dejamos como estaba
            cur_rank = 5
        if best and best != r["email"]:
            r.setdefault("email_generic", r["email"])
            r["email"], r["email_role"] = best, rank(best)[1]
            changed += 1
        else:
            r["email_role"] = {"Otro": "Genérico"}.get(rank(r["email"])[1], rank(r["email"])[1])
    path.write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    from collections import Counter
    print(fname, "· mejorados:", changed, "·", dict(Counter(r.get("email_role", "?") for r in rows)))


if __name__ == "__main__":
    run("outreach_state.json")
    run("outreach_clinics_state.json")
