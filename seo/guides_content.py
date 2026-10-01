"""Contenido de las guías SEO. Cada guía: lang, slug, title (<60 car.), desc (<160), h1, lead, body (HTML), faqs, related."""

EN_REL = [("How to get more Google reviews", "/guides/get-more-google-reviews/"),
          ("How to respond to Google reviews (with templates)", "/guides/respond-to-google-reviews/"),
          ("Google reviews for hotels", "/guides/google-reviews-for-hotels/"),
          ("Google reviews for dental and medical clinics", "/guides/google-reviews-for-clinics/")]
ES_REL = [("Cómo conseguir más reseñas en Google", "/es/conseguir-mas-resenas-google/"),
          ("Cómo responder a reseñas de Google (con plantillas)", "/es/responder-resenas-google/"),
          ("Reseñas de Google para hoteles", "/es/resenas-google-hoteles/"),
          ("Reseñas de Google para clínicas", "/es/resenas-google-clinicas/")]


def rel(lst, slug):
    return [x for x in lst if slug not in x[1]][:3]


GUIDES = [
# ─────────────────────────────── EN 1 ───────────────────────────────
dict(lang="en", slug="get-more-google-reviews",
 title="How to Get More Google Reviews: 9 Methods That Work (2026)",
 desc="Practical, Google-compliant ways for hotels, clinics and local businesses to get more Google reviews, with message templates you can copy today.",
 h1="How to get more Google reviews: 9 methods that actually work",
 lead="Most happy customers never leave a review. Not because they don't want to, but because nobody asks them at the right moment, in the right way. Here's how to fix that, without breaking Google's rules.",
 body="""
<h2>Why Google reviews matter so much</h2>
<p>Google reviews are one of the main factors in how local businesses rank on Google Maps. More recent reviews also mean more trust: most people read reviews before booking a room, a dentist or a table, and they pay attention to how recent they are and whether the business replies.</p>
<p>The good news: if your customers are happy, getting more reviews is mostly a process problem, not a quality problem.</p>

<h2>1. Ask every customer, not just the happy ones</h2>
<p>Google's policies forbid "review gating", which means only asking customers you think are happy. Ask everyone, the same way. It's also better for you: a steady flow of honest reviews looks more trustworthy than a perfect 5.0 with 20 reviews.</p>

<h2>2. Ask at the right moment</h2>
<p>The best moment is just after the experience: on checkout day for a hotel, the same afternoon for a clinic or a spa. Wait a week and most people have moved on.</p>

<h2>3. Use a direct review link</h2>
<p>Every extra tap loses people. Send a link that opens the "write a review" box directly, instead of your Google Maps page. You can get it from your Google Business Profile ("Ask for reviews") or build it with your Place ID.</p>

<h2>4. Send it where people actually read: WhatsApp or SMS</h2>
<p>Emails often go unread. A short, personal WhatsApp or text message gets opened within minutes. Keep it human:</p>
<div class="tpl"><b>Template · thank-you message</b>Hi Maria! Thank you so much for choosing The Harbor Hotel. If you have a minute, sharing how it went would mean a lot to our team: [review link]. Thank you, and we hope to see you again soon!</div>

<h2>5. Send one reminder (only one)</h2>
<p>Many people mean to leave a review and forget. One friendly reminder two days later, only to those who didn't open the link, recovers a good share of them. More than one starts to feel like spam.</p>
<div class="tpl"><b>Template · reminder email</b>Hi Maria, thanks again for choosing us. If you haven't had a moment yet, your review really helps us and only takes a minute: [review link]. Thank you!</div>

<h2>6. Catch problems before they become bad reviews</h2>
<p>For longer stays, a short "is everything OK?" message halfway through gives unhappy customers a direct line to you. You fix the problem on the spot, instead of reading about it on Google.</p>

<h2>7. Make it easy at the front desk</h2>
<p>An NFC card or QR code at reception lets customers leave a review with a single tap while they're still with you. Train the team to mention it naturally: "If you enjoyed it, it helps us a lot."</p>

<h2>8. Reply to every review</h2>
<p>Customers are more likely to leave a review when they see the business answers. Replying also shows future customers that you care, and gives you a chance to calmly handle negative feedback.</p>

<h2>9. Never buy or incentivise reviews</h2>
<p>Paying for reviews, offering discounts in exchange for 5 stars, or writing them yourself breaks Google's rules and can get reviews removed or your profile penalised. It's simply not worth it.</p>

<h2>How much can this change?</h2>
<p>Results vary, but businesses that start asking every customer consistently usually go from a handful of reviews a month to several times more within the first weeks. The key is consistency: a process that runs every single day, not a campaign once a year.</p>
""",
 faqs=[("Is it allowed to ask customers for Google reviews?", "Yes. Google allows and encourages businesses to ask customers for reviews, as long as you ask everyone equally, don't offer incentives and don't filter out unhappy customers."),
       ("What's the best time to ask for a review?", "Right after the experience: on checkout day for hotels and on the day of the appointment for clinics and spas."),
       ("Can I send review requests by WhatsApp?", "Yes, as long as the customer gave you their number and knows they'll receive a message after their visit. WhatsApp messages are usually read much faster than emails."),
       ("How do I get a direct link to my Google review form?", "From your Google Business Profile, use \"Ask for reviews\" to copy your link. Tools like Hosperai create and track these links for you.")],
 related=rel(EN_REL, "get-more-google-reviews")),

# ─────────────────────────────── EN 2 ───────────────────────────────
dict(lang="en", slug="respond-to-google-reviews",
 title="How to Respond to Google Reviews (Templates for Good & Bad)",
 desc="How to reply to positive and negative Google reviews, with ready-to-use templates for hotels, clinics and local businesses, plus mistakes to avoid.",
 h1="How to respond to Google reviews: templates for good and bad reviews",
 lead="Replying to reviews builds trust with future customers and helps your Google profile. But writing a thoughtful reply to every single review takes time most teams don't have. Here's a simple framework, with templates.",
 body="""
<h2>Should you reply to every review?</h2>
<p>Yes. Replying to both positive and negative reviews shows people that there's a real team behind the business. Many customers read the replies as carefully as the reviews themselves.</p>

<h2>How to reply to a positive review</h2>
<ol><li>Thank them by name.</li><li>Mention something specific they said (the breakfast, the staff member, the treatment).</li><li>Invite them back.</li></ol>
<div class="tpl"><b>Template · positive review</b>Thank you so much, Sophie! We're thrilled you loved the location and the breakfast. We'll pass your kind words on to the team. Hope to welcome you back soon!</div>
<p>Avoid copy-pasting the same "Thanks for your review!" everywhere. It looks automated and wastes the chance to show personality.</p>

<h2>How to reply to a negative review</h2>
<ol><li>Stay calm and don't argue in public.</li><li>Apologise for their experience (even if you disagree with details).</li><li>Show what you're doing about it.</li><li>Offer a private channel to continue the conversation.</li></ol>
<div class="tpl"><b>Template · negative review</b>Hi James, we're really sorry about the air conditioning and the room size. That's not the stay we want for our guests. We've already flagged it with maintenance. If you'd like, write to us at frontdesk@yourhotel.com and we'll make it right.</div>

<h2>How to reply to a review in another language</h2>
<p>Reply in the reviewer's language. It's a small detail that guests notice, especially international travellers. If you don't speak the language, write your reply and translate it carefully, or use a tool that drafts it for you in their language with a translation for you to check.</p>

<h2>Mistakes to avoid</h2>
<ul><li>Arguing or blaming the customer in public.</li><li>Sharing private details (room number, treatment, booking info).</li><li>Replying weeks later. Aim for 24–48 hours.</li><li>Identical replies to every review.</li></ul>

<h2>How to save hours every month</h2>
<p>The hardest part isn't knowing what to write, it's finding the time to do it every day. That's why many businesses use a tool that drafts the reply for them in their own tone, so the owner only reviews and posts it. That turns 10 minutes per review into 10 seconds.</p>
""",
 faqs=[("How fast should I reply to a Google review?", "Ideally within 24 to 48 hours. Quick replies show customers that you're attentive, especially for negative reviews."),
       ("Should I reply to reviews without text?", "A short thank-you is enough. It still shows that you read and value every review."),
       ("Can AI write my review replies?", "Yes. AI can draft replies in your tone and in the reviewer's language. Always read and approve them before posting, so every reply sounds like you."),
       ("Can I delete a negative Google review?", "Only Google can remove reviews, and only if they break its policies (spam, offensive content, conflicts of interest). The best answer to a fair negative review is a calm, helpful reply.")],
 related=rel(EN_REL, "respond-to-google-reviews")),

# ─────────────────────────────── EN 3 ───────────────────────────────
dict(lang="en", slug="google-reviews-for-hotels",
 title="Google Reviews for Hotels: How Small Hotels Get More",
 desc="How independent hotels, B&Bs and inns can get more Google and Tripadvisor reviews and answer every one, without extra work for the front desk.",
 h1="Google reviews for hotels: how small hotels get more (and answer them all)",
 lead="For an independent hotel, Google is the new front door. Guests compare your rating, the number of reviews and how you reply before they even visit your website. Here's how small hotels compete with the big chains.",
 body="""
<h2>Why independent hotels fall behind</h2>
<p>Big chains have marketing teams that ask every guest for a review. Small hotels and B&Bs usually have great guests and great ratings, but far fewer reviews, simply because nobody has time to ask. On Google Maps, that can push a 5-star inn below a 4.3-star hotel with ten times more reviews.</p>

<h2>The checkout moment</h2>
<p>The best time to ask is checkout day, when the stay is still fresh. A personal message that day, with one-tap links to Google and Tripadvisor, gets far more reviews than a generic email a week later.</p>
<div class="tpl"><b>Template · checkout day</b>Hi Maria! Thank you so much for staying with us at The Harbor Hotel. We hope you had a wonderful time. If you have a minute, sharing how it went would mean a lot to our team: Google [link] · Tripadvisor [link]. Safe travels!</div>

<h2>Catch problems before checkout</h2>
<p>For stays of three nights or more, a short message halfway through ("Is everything going well?") gives guests a direct line to reception. A noisy AC fixed on day two is a happy guest on day four, instead of a 2-star review.</p>

<h2>Reply to every review, in the guest's language</h2>
<p>Hotels receive reviews in many languages. Replying in the guest's own language is a detail future guests notice. It also keeps your profile active, which Google values.</p>

<h2>Keep it simple for reception</h2>
<p>Whatever system you use, it has to take seconds at the front desk. The best setup is a private link where reception enters the guest's name, mobile and checkout date, and everything else runs automatically. Larger hotels can connect it to their PMS so guests are added without typing.</p>

<h2>What results to expect</h2>
<p>Hotels that ask every guest consistently usually multiply the number of reviews they get each month within the first few weeks, and they climb on Google Maps as a result. More visibility means more direct bookings, without commissions.</p>
""",
 faqs=[("Should hotels focus on Google or Tripadvisor reviews?", "Both. Google drives visibility on Maps and Search; Tripadvisor still matters for many travellers. Send guests a direct link to each and let them choose."),
       ("Is it allowed to ask hotel guests for reviews?", "Yes, as long as you ask every guest equally and don't offer rewards for positive reviews."),
       ("How do we get guest phone numbers?", "Most hotels already collect them at booking or check-in. Reception adds them in seconds, or the PMS sends them automatically."),
       ("How much does a review tool cost for a small hotel?", "Enterprise tools often cost $300+ per month. Hosperai starts at $99/month with no setup fee and no lock-in.")],
 related=rel(EN_REL, "google-reviews-for-hotels")),

# ─────────────────────────────── EN 4 ───────────────────────────────
dict(lang="en", slug="google-reviews-for-clinics",
 title="Google Reviews for Dental & Medical Clinics: A Simple Guide",
 desc="How dental practices, med spas and clinics can get more Google reviews from happy patients, reply to every one, and stay privacy-safe.",
 h1="Google reviews for dental and medical clinics: a simple, privacy-safe guide",
 lead="Patients choose dentists, med spas and physios on Google. A practice with 40 reviews loses to one with 400, even with better care. Here's how clinics can get more reviews without making patients or staff uncomfortable.",
 body="""
<h2>Why clinics get fewer reviews than they deserve</h2>
<p>Most patients leave happy, but healthcare feels private, so they rarely think of writing a review. Front desks are busy, and asking in person can feel awkward. The result: excellent practices with very few reviews.</p>

<h2>Ask after every appointment</h2>
<p>The best moment is the same day, a couple of hours after the visit. A short, warm message with a direct link to your Google review form works best.</p>
<div class="tpl"><b>Template · after the appointment</b>Hi Emily! Thank you for visiting Bright Smile Dental today. If you have a minute, a quick Google review would mean a lot to our team: [review link]. See you at your next check-up!</div>

<h2>Keep it privacy-safe</h2>
<ul><li>Never mention the treatment, diagnosis or procedure in the message or in your replies.</li>
<li>Only message patients who gave you their number and know they'll get a thank-you after their visit.</li>
<li>In replies, don't confirm that the reviewer is a patient or share any detail about their care.</li></ul>
<div class="tpl"><b>Template · reply to a patient review</b>Thank you so much for your kind words! Our whole team works hard to make every visit as comfortable as possible. We look forward to seeing you again.</div>

<h2>Reply to negative reviews carefully</h2>
<p>Acknowledge the experience, avoid any detail about the patient, and invite them to contact the practice directly. Calm, professional replies reassure future patients more than a perfect score.</p>

<h2>Make it effortless for the front desk</h2>
<p>A good system takes seconds per patient: name, mobile and visit date, and the thank-you message goes out automatically. Clinics with practice-management software can connect it so patients are added automatically.</p>
""",
 faqs=[("Is it legal for clinics to ask patients for reviews?", "Yes, as long as you don't offer incentives, you ask patients equally, and you don't disclose any health information in messages or replies."),
       ("What should a dentist reply to a negative review?", "Thank them, apologise for their experience without discussing any treatment details, and invite them to contact the practice privately."),
       ("When should a clinic ask for a review?", "The same day as the appointment, a few hours later, while the experience is fresh."),
       ("Does Hosperai work for med spas and physiotherapy clinics?", "Yes. It works for any business with appointments: dental practices, med spas, physiotherapy, chiropractic and aesthetic clinics.")],
 related=rel(EN_REL, "google-reviews-for-clinics")),

# ─────────────────────────────── ES 1 ───────────────────────────────
dict(lang="es", slug="conseguir-mas-resenas-google",
 title="Cómo conseguir más reseñas en Google: 9 métodos (2026)",
 desc="Formas prácticas y permitidas por Google para que hoteles, clínicas y negocios locales consigan más reseñas, con plantillas de mensajes para copiar.",
 h1="Cómo conseguir más reseñas en Google: 9 métodos que funcionan",
 lead="La mayoría de clientes contentos nunca deja una reseña. No porque no quieran, sino porque nadie se lo pide en el momento adecuado y de la forma adecuada. Así se soluciona, sin saltarse las normas de Google.",
 body="""
<h2>Por qué importan tanto las reseñas de Google</h2>
<p>Las reseñas son uno de los factores principales para salir arriba en Google Maps. Además, la gente lee las reseñas antes de reservar un hotel, un dentista o una mesa, y se fija en si son recientes y si el negocio responde.</p>
<p>La buena noticia: si tus clientes están contentos, conseguir más reseñas es un problema de proceso, no de calidad.</p>

<h2>1. Pídelo a todos los clientes, no solo a los contentos</h2>
<p>Google prohíbe pedir reseñas solo a quien crees que está satisfecho. Pídelo a todos por igual. Además, un flujo constante de reseñas reales da más confianza que un 5,0 con 20 reseñas.</p>

<h2>2. Pídelo en el momento justo</h2>
<p>Justo después de la experiencia: el día de salida en un hotel, la misma tarde en una clínica o un centro de estética. Una semana después, la mayoría ya se ha olvidado.</p>

<h2>3. Usa un enlace directo al formulario de reseña</h2>
<p>Cada toque de más hace que la gente abandone. Envía un enlace que abra directamente la ventana de "escribir reseña", no tu ficha de Google Maps.</p>

<h2>4. Envíalo donde la gente lo lee: WhatsApp</h2>
<p>Los emails a menudo no se abren. Un mensaje corto y personal por WhatsApp se lee en minutos:</p>
<div class="tpl"><b>Plantilla · agradecimiento</b>¡Hola María! Muchas gracias por elegir Hotel Aurora. Si tienes un minuto, contarnos qué tal fue nos ayudaría muchísimo: [enlace de reseña]. ¡Gracias y esperamos verte pronto!</div>

<h2>5. Un solo recordatorio</h2>
<p>Mucha gente quiere dejar la reseña y se le olvida. Un recordatorio amable dos días después, solo a quien no abrió el enlace, recupera una buena parte. Más de uno ya molesta.</p>
<div class="tpl"><b>Plantilla · recordatorio</b>Hola María, gracias otra vez por elegirnos. Si aún no has tenido un momento, tu opinión nos ayuda muchísimo y solo lleva un minuto: [enlace]. ¡Gracias!</div>

<h2>6. Detecta problemas antes de que sean malas reseñas</h2>
<p>En estancias largas, un mensaje a mitad ("¿va todo bien?") da al cliente una vía directa para avisarte. Arreglas el problema al momento en vez de leerlo en Google.</p>

<h2>7. Facilítalo en recepción</h2>
<p>Una tarjeta NFC o un código QR en el mostrador permite dejar la reseña con un toque mientras el cliente aún está contigo.</p>

<h2>8. Responde a todas las reseñas</h2>
<p>Los clientes se animan más a escribir cuando ven que el negocio contesta. Y responder demuestra a los futuros clientes que te importa.</p>

<h2>9. Nunca compres ni premies reseñas</h2>
<p>Pagar por reseñas, dar descuentos a cambio de 5 estrellas o escribirlas tú va contra las normas de Google y puede acabar con reseñas eliminadas o tu ficha penalizada.</p>
""",
 faqs=[("¿Está permitido pedir reseñas a los clientes?", "Sí. Google permite y recomienda pedir reseñas, siempre que se pida a todos por igual, sin incentivos y sin filtrar a los clientes descontentos."),
       ("¿Cuál es el mejor momento para pedir una reseña?", "Justo después de la experiencia: el día de salida en hoteles y el mismo día de la cita en clínicas y centros de estética."),
       ("¿Puedo pedir reseñas por WhatsApp?", "Sí, siempre que el cliente te haya dado su número y sepa que recibirá un mensaje después de su visita."),
       ("¿Cómo consigo el enlace directo para que me dejen reseña?", "Desde tu Perfil de Empresa de Google, en \"Pedir reseñas\". Herramientas como Hosperai crean y controlan estos enlaces por ti.")],
 related=rel(ES_REL, "conseguir-mas-resenas-google")),

# ─────────────────────────────── ES 2 ───────────────────────────────
dict(lang="es", slug="responder-resenas-google",
 title="Cómo responder a reseñas de Google (plantillas buenas y malas)",
 desc="Cómo responder a reseñas positivas y negativas en Google, con plantillas listas para usar en hoteles, clínicas y negocios locales, y errores a evitar.",
 h1="Cómo responder a reseñas de Google: plantillas para buenas y malas",
 lead="Responder a las reseñas genera confianza y ayuda a tu ficha de Google. Pero escribir una respuesta cuidada a cada reseña lleva un tiempo que la mayoría de equipos no tiene. Aquí tienes un método sencillo con plantillas.",
 body="""
<h2>¿Hay que responder a todas las reseñas?</h2>
<p>Sí. Responder a las positivas y a las negativas demuestra que detrás hay un equipo real. Muchos clientes leen las respuestas tanto como las reseñas.</p>

<h2>Cómo responder a una reseña positiva</h2>
<ol><li>Da las gracias por su nombre.</li><li>Menciona algo concreto que haya dicho.</li><li>Invítale a volver.</li></ol>
<div class="tpl"><b>Plantilla · reseña positiva</b>¡Muchísimas gracias, Sofía! Nos alegra un montón que te encantaran la ubicación y el desayuno. Se lo diremos al equipo. ¡Esperamos verte pronto de nuevo!</div>

<h2>Cómo responder a una reseña negativa</h2>
<ol><li>Mantén la calma y no discutas en público.</li><li>Pide disculpas por su experiencia.</li><li>Explica qué estás haciendo para solucionarlo.</li><li>Ofrece un canal privado para seguir hablando.</li></ol>
<div class="tpl"><b>Plantilla · reseña negativa</b>Hola Jaime, sentimos mucho lo del aire acondicionado y el tamaño de la habitación. No es la estancia que queremos para nuestros huéspedes y ya lo hemos pasado a mantenimiento. Si quieres, escríbenos a recepcion@tuhotel.com y lo solucionamos.</div>

<h2>Reseñas en otros idiomas</h2>
<p>Responde en el idioma de quien escribe. Es un detalle que los clientes extranjeros notan. Si no dominas el idioma, usa una herramienta que te prepare la respuesta en su idioma con la traducción para que la revises.</p>

<h2>Errores que debes evitar</h2>
<ul><li>Discutir o culpar al cliente en público.</li><li>Dar datos privados (habitación, tratamiento, reserva).</li><li>Responder semanas después. Lo ideal es en 24-48 horas.</li><li>La misma respuesta para todas las reseñas.</li></ul>

<h2>Cómo ahorrar horas cada mes</h2>
<p>Lo difícil no es saber qué escribir, sino encontrar tiempo para hacerlo cada día. Por eso muchos negocios usan una herramienta que les prepara la respuesta en su tono, y el dueño solo la revisa y la publica: de 10 minutos por reseña a 10 segundos.</p>
""",
 faqs=[("¿En cuánto tiempo hay que responder una reseña?", "Lo ideal es en 24-48 horas, sobre todo si es negativa."),
       ("¿Hay que responder a las reseñas sin texto?", "Un agradecimiento breve es suficiente. Demuestra que lees y valoras todas las reseñas."),
       ("¿Puede la IA escribir mis respuestas?", "Sí. La IA puede preparar respuestas en tu tono y en el idioma de quien escribe. Revísalas siempre antes de publicarlas."),
       ("¿Puedo borrar una reseña negativa?", "Solo Google puede eliminar reseñas, y solo si incumplen sus normas. Ante una reseña negativa justa, lo mejor es una respuesta tranquila y útil.")],
 related=rel(ES_REL, "responder-resenas-google")),

# ─────────────────────────────── ES 3 ───────────────────────────────
dict(lang="es", slug="resenas-google-hoteles",
 title="Reseñas de Google para hoteles: cómo conseguir más",
 desc="Cómo los hoteles independientes, B&B y hostales pueden conseguir más reseñas en Google y Tripadvisor y responderlas todas sin trabajo extra para recepción.",
 h1="Reseñas de Google para hoteles: cómo conseguir más y responderlas todas",
 lead="Para un hotel independiente, Google es la nueva puerta de entrada. Los huéspedes comparan tu nota, el número de reseñas y cómo respondes antes incluso de entrar en tu web.",
 body="""
<h2>Por qué los hoteles independientes se quedan atrás</h2>
<p>Las cadenas tienen equipos que piden la reseña a cada huésped. Los hoteles pequeños suelen tener muy buena nota pero muchas menos reseñas, simplemente porque nadie tiene tiempo de pedirlas. En Google Maps, eso puede dejar un hotel de 5 estrellas por debajo de uno de 4,3 con diez veces más reseñas.</p>

<h2>El momento del check-out</h2>
<p>El mejor momento es el día de salida. Un mensaje personal ese día, con enlaces directos a Google y Tripadvisor, consigue muchas más reseñas que un email genérico una semana después.</p>
<div class="tpl"><b>Plantilla · día de salida</b>¡Hola María! Muchas gracias por alojarte en Hotel Aurora. Esperamos que lo hayas disfrutado. Si tienes un minuto, contarnos qué tal fue nos ayudaría muchísimo: Google [enlace] · Tripadvisor [enlace]. ¡Buen viaje!</div>

<h2>Detecta problemas antes de la salida</h2>
<p>En estancias de tres noches o más, un mensaje a mitad ("¿va todo bien?") da al huésped una línea directa con recepción. Un aire acondicionado arreglado el segundo día es un huésped contento el cuarto, en vez de una reseña de 2 estrellas.</p>

<h2>Responde a todas, en el idioma del huésped</h2>
<p>Los hoteles reciben reseñas en muchos idiomas. Responder en el idioma de cada huésped es un detalle que los futuros clientes valoran, y mantiene tu ficha activa.</p>

<h2>Que sea sencillo para recepción</h2>
<p>Recepción solo debería tardar unos segundos por huésped: nombre, móvil y fecha de salida, y el resto funciona solo. Los hoteles más grandes pueden conectarlo a su PMS para que los huéspedes se añadan automáticamente.</p>
""",
 faqs=[("¿Los hoteles deben centrarse en Google o en Tripadvisor?", "En los dos. Google da visibilidad en Maps y en el buscador; Tripadvisor sigue siendo importante para muchos viajeros."),
       ("¿Se puede pedir reseñas a los huéspedes?", "Sí, siempre que se pida a todos por igual y sin ofrecer premios por reseñas positivas."),
       ("¿Cómo conseguimos el móvil de los huéspedes?", "La mayoría de hoteles ya lo piden en la reserva o el check-in. Recepción lo añade en segundos, o el PMS lo envía solo."),
       ("¿Cuánto cuesta una herramienta de reseñas para un hotel pequeño?", "Las herramientas grandes suelen costar más de 300 $ al mes. Hosperai empieza en 99 $/mes, sin coste de alta ni permanencia.")],
 related=rel(ES_REL, "resenas-google-hoteles")),

# ─────────────────────────────── ES 4 ───────────────────────────────
dict(lang="es", slug="resenas-google-clinicas",
 title="Reseñas de Google para clínicas dentales y de estética",
 desc="Cómo las clínicas dentales, de estética y de fisioterapia pueden conseguir más reseñas en Google de pacientes contentos y responderlas respetando la privacidad.",
 h1="Reseñas de Google para clínicas: guía sencilla y respetuosa con la privacidad",
 lead="Los pacientes eligen dentista, clínica de estética o fisio en Google. Una clínica con 40 reseñas pierde frente a una con 400, aunque atienda mejor. Así se consiguen más reseñas sin incomodar a pacientes ni al equipo.",
 body="""
<h2>Por qué las clínicas tienen menos reseñas de las que merecen</h2>
<p>La mayoría de pacientes sale contento, pero la salud es algo privado y pocos piensan en escribir una reseña. La recepción va saturada y pedirlo en persona puede resultar incómodo.</p>

<h2>Pídelo después de cada cita</h2>
<p>El mejor momento es el mismo día, un par de horas después de la visita, con un mensaje breve y cercano y un enlace directo.</p>
<div class="tpl"><b>Plantilla · después de la cita</b>¡Hola Laura! Gracias por visitarnos hoy en Clínica Sonrisa. Si tienes un minuto, una reseña en Google nos ayudaría muchísimo: [enlace]. ¡Nos vemos en la próxima revisión!</div>

<h2>Respeta la privacidad</h2>
<ul><li>Nunca menciones el tratamiento ni el diagnóstico en los mensajes ni en las respuestas.</li>
<li>Escribe solo a pacientes que te dieron su móvil y saben que recibirán un agradecimiento.</li>
<li>En las respuestas no confirmes que la persona es paciente ni des detalles de su atención.</li></ul>
<div class="tpl"><b>Plantilla · respuesta a un paciente</b>¡Muchas gracias por tus palabras! Todo el equipo trabaja para que cada visita sea lo más cómoda posible. ¡Te esperamos pronto!</div>

<h2>Responde con cuidado a las negativas</h2>
<p>Reconoce la experiencia, evita cualquier detalle del paciente e invítale a contactar directamente con la clínica. Una respuesta tranquila y profesional tranquiliza más a los futuros pacientes que una nota perfecta.</p>
""",
 faqs=[("¿Es legal que una clínica pida reseñas a sus pacientes?", "Sí, siempre que no ofrezcas incentivos, lo pidas a todos por igual y no reveles información de salud en mensajes ni respuestas."),
       ("¿Qué debe responder un dentista a una reseña negativa?", "Agradecer, disculparse por la experiencia sin entrar en detalles del tratamiento e invitar a hablar en privado."),
       ("¿Cuándo debe una clínica pedir la reseña?", "El mismo día de la cita, unas horas después, mientras la experiencia está reciente."),
       ("¿Hosperai sirve para clínicas de estética y fisioterapia?", "Sí. Funciona para cualquier negocio con citas: dentistas, estética, fisioterapia, quiroprácticos y clínicas.")],
 related=rel(ES_REL, "resenas-google-clinicas")),
]
