"""Genera ~/Desktop/Hosperai_Envios.xlsx desde outreach_state.json (la fuente de verdad).
Se regenera después de cada envío / respuesta. Ábrelo para mirar; no hace falta editarlo."""
import json, collections
from pathlib import Path
from datetime import date
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter

D = Path(__file__).parent
STATE = D / "outreach_state.json"
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
COLS = [("#", 5), ("Estado", 16), ("Hotel", 34), ("Ciudad", 16), ("Email", 32), ("Nota", 6), ("Reseñas", 8),
        ("Email 1", 11), ("Email 2", 11), ("Email 3", 11), ("Próximo envío", 13), ("Respondió", 11),
        ("Notas", 30), ("Teléfono", 16), ("Web", 30)]


def build():
    rows = json.loads(STATE.read_text())
    wb = openpyxl.Workbook()

    # Resumen
    ws = wb.active; ws.title = "Resumen"
    cnt = collections.Counter(r["status"] for r in rows)
    today = date.today().isoformat()
    sent_today = sum(1 for r in rows for k in ("sent_1", "sent_2", "sent_3") if r[k] == today)
    ws.append(["Hosperai · Seguimiento de emails"]); ws["A1"].font = Font(bold=True, size=16)
    ws.append([f"Actualizado: {today}"]); ws.append([])
    ws.append(["Estado", "Hoteles"])
    for st in COLORS:
        ws.append([st, cnt.get(st, 0)])
        c = ws.cell(ws.max_row, 1); fill, fg = COLORS[st]
        c.fill = PatternFill("solid", fgColor=fill); c.font = Font(color=fg, bold=True)
    ws.append([]); ws.append(["Total", len(rows)]); ws.append(["Enviados hoy", sent_today])
    for c in ws[4]: c.font = Font(bold=True)
    ws.column_dimensions["A"].width = 22; ws.column_dimensions["B"].width = 10

    # Lista en orden de envío
    ws = wb.create_sheet("Envíos", 0)
    ws.append([c for c, _ in COLS])
    for i, (_, w) in enumerate(COLS, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
        h = ws.cell(1, i); h.font = Font(bold=True, color="FFFFFF"); h.fill = PatternFill("solid", fgColor="2563EB")
    for r in rows:
        ws.append([r["n"], r["status"], r["name"], r["city"], r["email"], r["rating"], int(r["reviews"] or 0),
                   r["sent_1"], r["sent_2"], r["sent_3"], r["next_due"], r["replied"], r["notes"], r["phone"], r["website"]])
        fill, fg = COLORS.get(r["status"], COLORS["Pendiente"])
        for c in ws[ws.max_row][:3]:
            c.fill = PatternFill("solid", fgColor=fill)
        ws.cell(ws.max_row, 2).font = Font(color=fg, bold=True)
    ws.freeze_panes = "C2"; ws.auto_filter.ref = ws.dimensions
    for row in ws.iter_rows(min_row=2):
        for c in row: c.alignment = Alignment(vertical="center")

    # Textos de cada email (por si quieres ver qué se le mandó a cada uno)
    ws = wb.create_sheet("Textos")
    ws.append(["#", "Hotel", "Asunto", "Email 1", "Email 2", "Email 3"])
    for c in ws[1]: c.font = Font(bold=True)
    for r in rows:
        ws.append([r["n"], r["name"], r["subject"], r["email_1"], r["email_2"], r["email_3"]])
    for col, w in zip("ABCDEF", (5, 30, 30, 60, 50, 50)): ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row: c.alignment = Alignment(wrap_text=True, vertical="top")

    try:
        wb.save(OUT)
    except PermissionError:  # el Excel está abierto → se guarda al lado
        wb.save(OUT.with_name("Hosperai_Envios (actualizado).xlsx"))


if __name__ == "__main__":
    build(); print("Excel actualizado:", OUT)
