"""
Posición de un negocio en Google Maps para una búsqueda (ej. "brunch miami beach"),
vía SerpAPI (engine=google_maps). Se usa en la auditoría gratuita.

Uso suelto:
  python3 maps_rank.py "<data_id>" "brunch miami beach" [--ll "@25.79,-80.13,14z"]

Coste: 1 búsqueda de SerpAPI por cada 20 resultados revisados (máx. 3 = top 60).
"""
import argparse
import requests
from review_monitor import SERPAPI_KEY


def maps_rank(data_id, keyword, ll=None, max_pages=3, hl="en"):
    """Devuelve dict con la posición (1-based) o None si no sale en el top revisado,
    los 3 primeros resultados y los datos del propio negocio si aparece."""
    checked, top, you, position = 0, [], None, None
    for page in range(max_pages):
        params = {"engine": "google_maps", "type": "search", "q": keyword,
                  "api_key": SERPAPI_KEY, "hl": hl, "start": page * 20}
        if ll:
            params["ll"] = ll
        data = requests.get("https://serpapi.com/search", params=params, timeout=20).json()
        results = data.get("local_results") or []
        for r in results:
            checked += 1
            item = {"title": r.get("title"), "rating": r.get("rating"), "reviews": r.get("reviews")}
            if len(top) < 3:
                top.append(item)
            if r.get("data_id") == data_id and position is None:
                position, you = checked, item
        if position is not None or len(results) < 20:
            break
    return {"keyword": keyword, "position": position, "checked": checked, "top": top, "you": you}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("data_id"); ap.add_argument("keyword")
    ap.add_argument("--ll", default=None)
    ap.add_argument("--pages", type=int, default=3)
    a = ap.parse_args()
    r = maps_rank(a.data_id, a.keyword, a.ll, a.pages)
    pos = f"#{r['position']}" if r["position"] else f"fuera del top {r['checked']}"
    print(f"'{r['keyword']}': {pos}")
    for i, t in enumerate(r["top"], 1):
        print(f"  {i}. {t['title']} · {t['rating']}★ ({t['reviews']})")
