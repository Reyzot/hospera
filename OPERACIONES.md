# Hosperai — Manual de operaciones

Todo lo que hace falta para operar clientes, en orden. Andreu no usa la terminal:
él dice "activa X" / "revisa Y" y Claude ejecuta lo de aquí.

## 1. Piezas del sistema

| Pieza | Dónde | Qué hace |
|---|---|---|
| Web pública + vídeo demo | hosperai.es (GitHub Pages, repo Reyzot/hospera) | Marketing. `hosperai.es/demo` = vídeo para emails |
| Formulario de alta | https://app.hosperai.es | El hotel da sus datos + cuestionario de estilo + mensaje VIP |
| Check-in de recepción | https://app.hosperai.es/checkin/?h=SLUG&t=TOKEN | Recepción añade huéspedes; pestaña Guests = programados (editables) y enviados |
| Backend web | Cloudflare Pages `hosperai-app` + KV `hosperai-data` (carpeta `app_site/`) | Guarda altas (`o:<id>`) y huéspedes (`c:<slug>`) |
| Clientes | `clients.json` (pending / active / paused) + 2 clientes antiguos fijos en `review_monitor.py` (Arreu, Racó'ns) | Ficha de cada hotel: WhatsApp, idioma, estilo, servicios |
| WhatsApp | Twilio, número +1 339-218-1281 "Hosperai" (Meta WABA "Hosperai Reviews") | Solo envía con plantillas aprobadas (`whatsapp_templates.json`) |
| Email | hosperai.app@gmail.com (Gmail SMTP, `.env`) | Avisos a Andreu, respaldo a huéspedes sin WhatsApp, informes |

## 2. Tareas automáticas (launchd en el Mac — el Mac tiene que estar encendido)

| Cuándo | Script | Qué hace | Gasta |
|---|---|---|---|
| Cada 30 min | `onboard_clients.py` (desde `run_daily_reviewmonitor.sh`) | Baja altas nuevas → `clients.json` (pending) + email a Andreu | 1 búsqueda SerpAPI por alta nueva |
| 1 vez/día desde 9:00 | `review_monitor.py --once` | Reseñas nuevas → respuesta IA → WhatsApp al dueño | 1 búsqueda SerpAPI por cliente/día + Claude Haiku |
| Cada 30 min, 9:00–21:00 | `guest_followup.py` | WhatsApp a huéspedes (salida desde 11:00, mitad de estancia) | Twilio/Meta por mensaje |
| Lunes 9:30 | `reports.py --weekly` | PDF semanal (solo clientes con "Progress reports", solo español) | 0 búsquedas |
| Día 28, 20:00 | `reports.py --monthly` | PDF mensual + ranking Maps | ~9 búsquedas por cliente |
| Cada día 8:30 | `health_check.py` | Email a Andreu SOLO si algo falla (SerpAPI, saldo Twilio, WhatsApp no entregados, web caída, altas sin activar, errores) | 0 |

Logs: `launchd_out.log`, `launchd_err.log`, `guestfollowup_out.log`, `guestfollowup_err.log`.

## 3. Alta de un cliente nuevo — paso a paso

1. **Llamada de venta** (15 min) → si dice sí: Andreu le manda el **Email 1** (abajo) con `https://app.hosperai.es` y el enlace de pago (Stripe, pendiente de montar).
2. El hotel rellena el formulario. En ≤30 min llega a hosperai.app@gmail.com "🆕 Nuevo cliente Hosperai: X" con todo y el comando.
3. Andreu revisa la info y que ha pagado → le dice a Claude **"activa X"**.
4. Claude: `cd ~/hospera && python3 onboard_clients.py --approve SLUG`
   - si dice "no tiene data_id": buscar la ficha de Maps y ponerla a mano en `clients.json`.
   - crea `hosperai.es/r/SLUG.html` (página de reseña, se publica con git push)
   - imprime el **enlace de check-in** y el **Email 2 de bienvenida ya redactado** → pasárselo a Andreu.
5. Esa misma tarde/día: le llega al dueño el WhatsApp "Hosperai activado" con su histórico (en la primera pasada del monitor).
6. Comprobar al día siguiente en la pestaña Guests del hotel que recepción está metiendo huéspedes.

Pausar un cliente (impago/baja): `python3 onboard_clients.py --pause SLUG`.

**Email 1 (tras la llamada):**
> Subject: Welcome to Hosperai — 5 minutes to get started
> Hi {Name}, great talking to you! To set up Hosperai for {Hotel}, please fill in this short form (about 5 minutes) — it tells us how you want your review replies to sound: https://app.hosperai.es
> Once it's done you'll be live within 48 hours and I'll send you your reception link. — Andreu · Hosperai

## 4. Servicios que se activan según lo que marcó el hotel

| Casilla del formulario | Efecto |
|---|---|
| Answer reviews | `review_monitor` vigila sus reseñas y manda la respuesta al WhatsApp del dueño |
| Get more reviews | `guest_followup` escribe a sus huéspedes (check-in) |
| Progress reports | Informes semanal/mensual por email (solo si idioma = español, de momento) |
| Resto (web, Google Profile, etc.) | Trabajo manual, no automatizado |

## 5. Cambiar la web de alta / check-in

```
cd ~/hospera/app_site
export CLOUDFLARE_API_TOKEN=$(grep ^CLOUDFLARE_API_TOKEN ../.env | cut -d= -f2) CLOUDFLARE_ACCOUNT_ID=$(grep ^CLOUDFLARE_ACCOUNT_ID ../.env | cut -d= -f2)
npx wrangler pages deploy --project-name hosperai-app --branch main --commit-dirty=true
```
Páginas en `app_site/public/`, lógica en `app_site/functions/api/` (checkin.js, onboarding.js).
Admin del check-in (desde scripts): `GET /api/checkin?h=SLUG&key=CHECKIN_SECRET`; acciones POST `list/add/update/delete` (token del hotel) y `mark/reset` (key).

## 6. WhatsApp: reglas que NO se pueden saltar

- El primer mensaje a alguien SIEMPRE tiene que ser una plantilla aprobada por Meta. Texto libre solo llega si esa persona nos escribió en las últimas 24 h.
- Los scripts no envían con plantillas sin aprobar y solo marcan "enviado" si WhatsApp confirma la entrega.
- Errores típicos: 63016 = plantilla sin aprobar / fuera de ventana 24 h · 63024 / 63003 = el número no tiene WhatsApp (→ se usa el email del huésped).
- Plantillas: `hosperai_thanks_{es,en}`, `hosperai_thanks_vip_{es,en}`, `hosperai_midstay_{es,en}`, `hosperai_review_alert_{es,en}` (v2), `hosperai_activated_{es,en}`. Idiomas distintos de es → inglés.
- Límite sin verificar empresa en Meta: 250 personas/día. Verificar cuando haya volumen (necesita documento de empresa + email @hosperai.es).
- SMS de respaldo desactivado (`SMS_ENABLED` en `.env`) hasta que Twilio apruebe A2P (rechazado: se registró con datos de España).

## 7. Costes y límites

| Servicio | Plan | Límite que importa |
|---|---|---|
| SerpAPI | Gratis, 250 búsquedas/mes | ~39/mes por cliente → caben ~5-6 clientes. Después: plan de pago |
| Twilio + Meta | Pago por uso (saldo) | ~0,01–0,03 $ por WhatsApp. Aviso si saldo < 5 $ |
| Cloudflare Pages + KV | Gratis | 100k peticiones/día, deploys prácticamente ilimitados |
| Claude API (Haiku) | Pago por uso | Céntimos al mes |
| Gmail SMTP | Gratis | ~500 emails/día |

## 8. Pendiente / mejoras conocidas

- Pasar las tareas del Mac a un servidor (~5 $/mes) con el primer cliente de pago.
- Informes PDF en inglés (ahora los clientes en inglés no reciben informe).
- Cobro mensual con Stripe (Payment Link con suscripción).
- Correo andreu@hosperai.es (Zoho, esperando soporte) → luego calentamiento y envío a los 509 hoteles de `leads/`.
- Hora de envío a huéspedes = hora del Mac (Miami). Si hay un hotel en otra zona horaria, añadir zona por cliente.

## 9. Pruebas rápidas (sin enviar nada)

```
python3 review_monitor.py --test
python3 guest_followup.py --test
python3 health_check.py --test
python3 onboard_clients.py            # lista clientes y enlaces de check-in
```
Hotel demo de Andreu: slug `hosperai-demo-hotel` (flujo real: mensaje el día de salida), WhatsApp +34 675 680 256.

## 10. Demo en reuniones (WhatsApp al instante)

Enlace: https://app.hosperai.es/checkin/?h=hosperai-live-demo&t=9c9ae088e96cdebf&n=Hosperai%20Live%20Demo
- Se escribe el nombre del hotel del cliente + su nombre y móvil → el WhatsApp "Gracias por elegir {su hotel}" le llega en segundos.
- Lo envía directamente la función de Cloudflare (secrets TWILIO_SID, TWILIO_TOKEN, WA_FROM, TPL_ES, TPL_EN en Pages). No está en clients.json, guest_followup no lo toca.
- Si responde 63016: la plantilla aún no está aprobada por Meta.
