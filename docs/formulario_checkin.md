# Formulario de check-in — captura para el Review Booster

Crear en forms.google.com → "Formulario en blanco". Lo rellena recepción (o quien
tome la reserva) en 10 segundos por huésped. Las respuestas caen en una Sheet
vinculada (Respuestas → icono de Sheets).

1. **Nombre del huésped** (respuesta corta)
2. **Teléfono (con prefijo de país)** (respuesta corta, opcional) — ej. +13054578397
3. **Email del huésped** (respuesta corta, opcional) — de reserva. Solo hace falta uno de los dos (teléfono o email), pero cuantos más tengamos, mejor.
4. **Idioma del huésped** (opción múltiple: Español / English / Català / Français / Deutsch / Italiano / Otro)
5. **Fecha de entrada** (fecha)
6. **Fecha de salida** (fecha)

## Publicar la Sheet como CSV (una vez, no hace falta repetirlo)

1. Abre la Sheet de respuestas → **Archivo → Compartir → Publicar en la Web**
2. Elige la pestaña de respuestas, formato **"Valores separados por comas (.csv)"**
3. Copia esa URL — es la que va en `checkin_sheet_url` del cliente en `review_monitor.py`

## Qué hace el sistema con esto

- El día de salida: si no ha dejado reseña todavía, le llega un mensaje
  pidiéndosela, en su idioma, con un enlace donde elige Google o TripAdvisor.
- Si la estancia es de más de una noche: a mitad de estancia le llega un
  mensaje corto preguntando si todo va bien, con un enlace directo para avisar
  al negocio si algo falla — para arreglarlo antes de que se vaya.
- Canal: si tenemos su teléfono, se manda por SMS. Si no tenemos teléfono
  pero sí su email (de la reserva), se manda por email en su lugar — así
  el Boost Review funciona aunque el negocio solo capture el email.
