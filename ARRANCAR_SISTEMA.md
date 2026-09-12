# Hospera Review Monitor — Guía

Sistema actual: **un único script, una única terminal, sin servidor ni túnel.**
Lee reseñas de Google vía SerpAPI (no depende de la API oficial de Google) y manda la reseña + respuesta generada por IA al WhatsApp del manager. La publicación en Google se hace a mano (el manager pega la respuesta desde el link que le llega).

---

## Comprobar reseñas nuevas (lo que ejecutas día a día)

```
python3 ~/hospera/review_monitor.py --once
```

Revisa todos los clientes de la lista `CLIENTS` (dentro de `review_monitor.py`) y manda un WhatsApp por cada reseña nueva que encuentre. Si no hay reseñas nuevas, no manda nada.

Con hacerlo una vez al día es más que suficiente y no gasta el plan gratuito de SerpAPI (100 búsquedas/mes).

Otros modos:
```
python3 review_monitor.py --test    # busca reseñas pero NO manda WhatsApp (para probar sin gastar mensajes)
python3 review_monitor.py           # bucle infinito, revisa cada hora — solo cuando haya clientes de pago
```

---

## Añadir un cliente nuevo

Abre `review_monitor.py` y añade un bloque a la lista `CLIENTS` (arriba del archivo):

```python
{
    "name":      "Nombre del negocio",
    "data_id":   "0x...",              # sacado de su URL de Google Maps
    "type":      "restaurante",        # o "hotel", "chiringuito", etc.
    "signature": "El equipo de X",
    "phone":     "whatsapp:+34XXXXXXXXX",
    "state":     Path.home() / 'hospera/seen_XXXXX.json',
},
```

**Cómo sacar el `data_id`**: busca el negocio en Google Maps, copia la URL completa y pásamela — lo saco de ahí en un momento.

---

## Cómo lo recibe el manager

```
🔔 Nueva reseña — [Negocio]

👤 María García ⭐⭐⭐⭐
_Muy buena ubicación, personal amable..._

💬 Respuesta sugerida:
_Gracias María por tu visita..._

👉 Publicar en Google:
https://business.google.com/reviews
```

El manager entra al link, busca la reseña y pega la respuesta. No hace falta que responda nada por WhatsApp, es solo notificación + respuesta lista para copiar.

---

## Cuando haya clientes de pago (escalar)

- SerpAPI de pago: $50/mes → 5.000 búsquedas (~10 clientes revisando cada hora)
- Pasar de `--once` manual a bucle automático (`python3 review_monitor.py` sin flags, corriendo de fondo)
- Cambiar el número de WhatsApp del sandbox de Twilio por uno de empresa propio (ver conversación aparte sobre esto)

---

## Archivo `_archive/`

Ahí quedó guardado (no borrado) el sistema antiguo basado en la API oficial de Google Business Profile — nunca llegó a aprobarse y se abandonó a favor de SerpAPI. Incluye `auth_setup.py`, `credentials.json`, `token.json` y el `review_manager.py` original con el flujo SI/NO/EDITAR por WhatsApp. Si algún día se aprueba la API de Google y quieres retomar el auto-publish real, está todo ahí — si no, se puede ignorar por completo.
