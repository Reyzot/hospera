// Twilio llama aquí cuando alguien escribe al WhatsApp de Hosperai (+1 339 218 1281).
// Respondemos que este número solo envía mensajes y le damos el contacto de SU hotel (KV p:<teléfono>).
async function validSignature(request, form, token) {
  const sig = request.headers.get("X-Twilio-Signature") || "";
  const url = new URL(request.url); url.protocol = "https:";
  const data = url.toString() + [...form.keys()].sort().map(k => k + form.get(k)).join("");
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(token), { name: "HMAC", hash: "SHA-1" }, false, ["sign"]);
  const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(data));
  return btoa(String.fromCharCode(...new Uint8Array(mac))) === sig;
}
const xml = s => s.replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

export async function onRequestPost({ request, env }) {
  const form = await request.formData();
  if (!(await validSignature(request, form, env.TWILIO_TOKEN))) return new Response("forbidden", { status: 403 });
  const phone = String(form.get("From") || "").replace(/[^0-9]/g, "");
  const rec = (await env.DB.get(`p:${phone}`, "json")) || null;
  const es = rec ? rec.lang === "es" : /^34|^52|^54|^57|^56|^51|^58/.test(phone);
  let msg;
  if (rec && rec.contact) {
    msg = es
      ? `Hola 👋 Este número solo envía mensajes automáticos de ${rec.hotel} y no puede leer respuestas.\n\nPara contactar con ${rec.hotel}, escribe a: ${rec.contact}\n\n¡Gracias!`
      : `Hi 👋 This number only sends automated messages from ${rec.hotel} and can't read replies.\n\nTo contact ${rec.hotel}, please reach them at: ${rec.contact}\n\nThank you!`;
  } else if (rec) {
    msg = es
      ? `Hola 👋 Este número solo envía mensajes automáticos de ${rec.hotel} y no puede leer respuestas. Para contactar con ${rec.hotel}, usa su WhatsApp, teléfono o email habituales. ¡Gracias!`
      : `Hi 👋 This number only sends automated messages from ${rec.hotel} and can't read replies. To contact ${rec.hotel}, please use their usual WhatsApp, phone or email. Thank you!`;
  } else {
    msg = es
      ? "Hola 👋 Este número de Hosperai solo envía mensajes automáticos y no puede leer respuestas. Para hablar con nosotros: hosperai.app@gmail.com · hosperai.es"
      : "Hi 👋 This Hosperai number only sends automated messages and can't read replies. To reach us: hosperai.app@gmail.com · hosperai.es";
  }
  return new Response(`<?xml version="1.0" encoding="UTF-8"?><Response><Message>${xml(msg)}</Message></Response>`,
                      { headers: { "Content-Type": "text/xml; charset=utf-8" } });
}
