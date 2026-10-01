"""Genera ~/Desktop/Hosperai_Envios.xlsx desde outreach_state.json (la fuente de verdad).
Se regenera después de cada envío / respuesta. Ábrelo para mirar; no hace falta editarlo."""
import json, collections
from pathlib import Path
from datetime import date
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter

D = Path(__file__).parent
CAMPAIGNS = {"Hoteles": D / "outreach_state.json", "Clínicas": D / "outreach_clinics_state.json"}
OUT = Path.home() / "Desktop" / "Hosperai_Envios.xlsx"

COLORS = {  # estado → (relleno, texto)
    "Pendiente":        ("FFFFFF", "6B7280"),
    "Email 1 enviado":  ("DBEAFE", "1D4ED8"),
    "Email 2 enviado":  ("EDE9FE", "6D28D9"),
    "Email 3 enviado":  ("FFEDD5", "C2410C"),
    "Respondió":        ("DCFCE7", "15803D"),
    "No interesado":    ("FEE2E2", "B91C1C"),
    "Rebotó":           ("FEE2E2", "B91C1C"),
}
COLS = [("#", 5), ("Estado", 16), ("Negocio", 34), ("Ciudad", 16), ("Email", 32), ("Tipo / nota", 14), ("Reseñas", 8),
        ("Email 1", 11), ("Email 2", 11), ("Email 3", 11), ("Próximo envío", 13), ("Respondió", 11),
        ("Notas", 30), ("Teléfono", 16), ("Web", 30)]


def build():
    camps = {n: json.loads(p.read_text()) for n, p in CAMPAIGNS.items() if p.exists()}
    wb = openpyxl.Workbook()
    today = date.today().isoformat()

    # Resumen: hoteles vs clínicas
    ws = wb.active; ws.title = "Resumen"
    ws.append(["Hosperai · Seguimiento de emails"]); ws["A1"].font = Font(bold=True, size=16)
    ws.append([f"Actualizado: {today}"]); ws.append([])
    ws.append(["Estado"] + list(camps)); [setattr(c, "font", Font(bold=True)) for c in ws[4]]
    cnts = {n: collections.Counter(r["status"] for r in rows) for n, rows in camps.items()}
    for st in COLORS:
        ws.append([st] + [cnts[n].get(st, 0) for n in camps])
        c = ws.cell(ws.max_row, 1); fill, fg = COLORS[st]
        c.fill = PatternFill("solid", fgColor=fill); c.font = Font(color=fg, bold=True)
    ws.append([]); ws.append(["Total"] + [len(r) for r in camps.values()])
    ws.append(["Enviados hoy"] + [sum(1 for r in rows for k in ("sent_1", "sent_2", "sent_3") if r[k] == today) for rows in camps.values()])
    contacted = {n: sum(1 for r in rows if r["sent_1"]) for n, rows in camps.items()}
    replied = {n: cnts[n].get("Respondió", 0) + cnts[n].get("No interesado", 0) for n in camps}
    ws.append(["% que responde"] + [f"{replied[n] / contacted[n] * 100:.1f}%" if contacted[n] else "—" for n in camps])
    ws.column_dimensions["A"].width = 22
    for col in "BC": ws.column_dimensions[col].width = 12

    for name, rows in camps.items():
        ws = wb.create_sheet(name)
        ws.append([c for c, _ in COLS])
        for i, (_, w) in enumerate(COLS, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
            h = ws.cell(1, i); h.font = Font(bold=True, color="FFFFFF"); h.fill = PatternFill("solid", fgColor="2563EB")
        for r in rows:
            nota = r["rating"] or r.get("segment", "")
            ws.append([r["n"], r["status"], r["name"], r["city"], r["email"], nota, int(r["reviews"] or 0) if str(r["reviews"]).isdigit() else "",
                       r["sent_1"], r["sent_2"], r["sent_3"], r["next_due"], r["replied"], r["notes"], r["phone"], r["website"]])
            fill, fg = COLORS.get(r["status"], COLORS["Pendiente"])
            for c in ws[ws.max_row][:3]:
                c.fill = PatternFill("solid", fgColor=fill)
            ws.cell(ws.max_row, 2).font = Font(color=fg, bold=True)
        ws.freeze_panes = "C2"; ws.auto_filter.ref = ws.dimensions

    # Próximos envíos: el orden real (seguimientos que tocan + nuevos alternando hoteles/clínicas)
    ws = wb.create_sheet("Próximos envíos", 1)
    ws.append(["Orden", "Campaña", "Qué se envía", "Negocio", "Ciudad", "Email", "Cuándo"])
    for c in ws[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="2563EB")
    queue = []
    for name, rows in camps.items():
        for r in rows:
            if r["status"] in ("Email 1 enviado", "Email 2 enviado") and r["next_due"]:
                queue.append((r["next_due"], 0, name, "Email 2 (vídeo)" if r["status"] == "Email 1 enviado" else "Email 3 (cierre)", r))
    pend = {n: [r for r in rows if r["status"] == "Pendiente"] for n, rows in camps.items()}
    i = 0
    while any(pend.values()) and i < 200:
        for n in camps:
            if pend[n]:
                queue.append(("9999", i, n, "Email 1", pend[n].pop(0))); i += 1
    queue.sort(key=lambda q: (q[0], q[1]))
    for k, (due, _, name, what, r) in enumerate(queue[:120], 1):
        ws.append([k, name, what, r["name"], r["city"], r["email"], due if due != "9999" else "siguiente día laborable libre"])
    for col, w in zip("ABCDEFG", (7, 10, 16, 34, 16, 32, 26)): ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"

    ws = wb.create_sheet("Textos")
    ws.append(["Campaña", "#", "Negocio", "Asunto", "Email 1", "Email 2", "Email 3"])
    for c in ws[1]: c.font = Font(bold=True)
    for name, rows in camps.items():
        for r in rows:
            ws.append([name, r["n"], r["name"], r["subject"], r["email_1"], r["email_2"], r["email_3"]])
    for col, w in zip("ABCDEFG", (10, 5, 30, 30, 60, 50, 50)): ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row: c.alignment = Alignment(wrap_text=True, vertical="top")

    try:
        wb.save(OUT)
    except PermissionError:  # el Excel está abierto → se guarda al lado
        wb.save(OUT.with_name("Hosperai_Envios (actualizado).xlsx"))


if __name__ == "__main__":
    build(); print("Excel actualizado:", OUT)
