import sys
sys.path.insert(0, '/Users/andreurey/Library/Python/3.9/lib/python/site-packages')

from playwright.sync_api import sync_playwright
import time
import re
import os

HOTELS = [
    "pension-casa-blanca",
    "pension-45",
    "pension-portugal",
    "hostal-girona",
    "hostal-eden-barcelona",
    "hostal-drassanes",
    "pension-ciudadela",
    "pension-villanueva",
    "hostal-centric",
    "hostalaslyp114",
    "pension-san-ramon",
    "hotel-curious",
    "anba-boutique-b-b-barcelona",
    "hostal-goya",
    "denit",
    "pensio-2000",
    "hostal-lausanne",
    "hostal-bcn-ramblas",
    "pensio-mari-luz",
    "hostal-sea-point",
]

def get_calendar_prices(page, slug):
    # Estancia 30 noches — fuerza a Booking a mostrar el calendario sin disponibilidad
    url = f"https://www.booking.com/hotel/es/{slug}.es.html?checkin=2026-06-29&checkout=2026-07-29&group_adults=1&no_rooms=1"
    try:
        page.goto(url, timeout=20000, wait_until="domcontentloaded")
        time.sleep(3)

        # Cerrar popups
        for sel in ['#onetrust-accept-btn-handler', "[aria-label='Dismiss sign-in info.']", "[aria-label='Cerrar']"]:
            try:
                page.click(sel, timeout=1500)
                time.sleep(0.5)
            except:
                pass

        # Abrir el calendario clicando en el campo de fechas
        for sel in [
            '[data-testid="date-display-field-start"]',
            '[data-testid="searchbox-dates-container"]',
            'input[name="checkin"]',
        ]:
            try:
                page.locator(sel).first.click(timeout=3000)
                time.sleep(2)
                break
            except:
                pass

        # Navegar al mes de julio si estamos en junio
        for _ in range(3):
            try:
                month_text = page.locator('[data-testid="datepicker-month-name"]').first.inner_text(timeout=2000)
                if 'julio' in month_text.lower() or 'july' in month_text.lower():
                    break
                page.locator('[data-testid="datepicker-next-month-button"]').click(timeout=2000)
                time.sleep(1)
            except:
                break

        # Leer precios con el selector [data-date] confirmado por DevTools
        prices = {}
        cells = page.locator('[data-date]').all()
        for cell in cells:
            try:
                date = cell.get_attribute('data-date', timeout=500)
                text = cell.inner_text(timeout=500)
                # Buscar precio en formato "€ 168"
                match = re.search(r'€\s*(\d+)', text)
                if match and date:
                    prices[date] = int(match.group(1))
            except:
                pass

        return prices

    except Exception as e:
        return {}

def main():
    print("\n🔍 Leyendo precios del calendario de Booking — julio 2026\n")
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 900},
            locale='es-ES'
        )
        page = context.new_page()

        for i, slug in enumerate(HOTELS):
            name = slug.replace('-', ' ').title()
            print(f"\n[{i+1}/{len(HOTELS)}] {name}")

            prices = get_calendar_prices(page, slug)

            # Filtrar solo julio 2026
            july_prices = {k: v for k, v in prices.items() if k.startswith('2026-07')}

            if not july_prices:
                print(f"  ⚠️  Sin precios en el calendario")
                results.append({'name': name, 'slug': slug, 'error': True})
            else:
                vals = list(july_prices.values())
                mn, mx = min(vals), max(vals)
                variacion = round((mx - mn) / mn * 100)
                flat = variacion <= 20
                status = "🔴 PRECIO PLANO" if flat else "✅ Variable"
                print(f"  Precios julio: {sorted(set(vals))}")
                print(f"  → €{mn}-€{mx} | Variación: {variacion}% | {status}")
                results.append({'name': name, 'slug': slug, 'min': mn, 'max': mx, 'variacion': variacion, 'flat': flat})

            time.sleep(2)

        browser.close()

    # Resumen
    flat = [r for r in results if r.get('flat')]
    print(f"\n{'='*60}")
    print(f"TARGETS CON PRECIO PLANO: {len(flat)}")
    print(f"{'='*60}")
    for r in flat:
        print(f"  ⭐ {r['name']} | €{r['min']}/noche | Variación: {r['variacion']}%")

    out = os.path.expanduser('~/Desktop/booking_targets.txt')
    with open(out, 'w') as f:
        f.write("HOTELES BARCELONA — ANÁLISIS PRICING JULIO 2026\n")
        f.write("="*60 + "\n\n")
        f.write(f"TARGETS PRECIO PLANO ({len(flat)}):\n")
        for r in flat:
            f.write(f"  ⭐ {r['name']} | €{r['min']}/noche | Variación: {r['variacion']}%\n")
        f.write("\nTODOS LOS RESULTADOS:\n")
        for r in results:
            if not r.get('error'):
                s = "PLANO" if r['flat'] else "variable"
                f.write(f"  {r['name']} | €{r['min']}-€{r['max']} | {r['variacion']}% | {s}\n")
    print(f"\nGuardado en: ~/Desktop/booking_targets.txt")

if __name__ == '__main__':
    main()
