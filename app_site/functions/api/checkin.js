import { clean, json, text, rid, hotelToken } from "./_shared.js";

const DAY = 86400000;
const EDITABLE = { name: 80, phone: 30, email: 120, lang: 20, checkin: 10, checkout: 10, vip: 3 };
const DEMO_SLUG = "hosperai-live-demo";
const DEMO_REVIEW_LINK = "https://hosperai.es/r/hosperai-demo-hotel.html";

// Demo en reuniones: el WhatsApp de agradecimiento sale al instante (los hoteles reales, el día de salida).
async function sendDemoWhatsApp(env, rec, hotelName) {
  const lang = rec.lang === "Español" || rec.lang === "Català" ? "es" : "en";
  const phone = "+" + rec.phone.replace(/[^0-9]/g, "");
  const first = rec.name.split(" ")[0];
  const q = encodeURIComponent(hotelName);
  const useNew = !!(lang === "es" ? env.TPL_GT_ES : env.TPL_GT_EN);  // plantilla nueva con Google + Tripadvisor (cuando Meta la apruebe)
  const vars = useNew
    ? { 1: first.charAt(0).toUpperCase() + first.slice(1), 2: hotelName,
        3: `https://www.google.com/maps/search/${q}`, 4: `https://www.tripadvisor.com/Search?q=${q}` }
    : { 1: first.charAt(0).toUpperCase() + first.slice(1), 2: hotelName, 3: DEMO_REVIEW_LINK };
  const auth = "Basic " + btoa(`${env.TWILIO_SID}:${env.TWILIO_TOKEN}`);
  const base = `https://api.twilio.com/2010-04-01/Accounts/${env.TWILIO_SID}/Messages`;
  const r = await fetch(`${base}.json`, {
    method: "POST", headers: { Authorization: auth, "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ From: env.WA_FROM, To: `whatsapp:${phone}`, ContentSid: useNew ? (lang === "es" ? env.TPL_GT_ES : env.TPL_GT_EN) : (lang === "es" ? env.TPL_ES : env.TPL_EN),
                                ContentVariables: JSON.stringify(vars) }),
  });
  let m = await r.json();
  if (!r.ok) return { status: "failed", error: m.message || r.status };
  for (let i = 0; i < 6; i++) {
    await new Promise(res => setTimeout(res, 1500));
    m = await (await fetch(`${base}/${m.sid}.json`, { headers: { Authorization: auth } })).json();
    if (["delivered", "read", "failed", "undelivered"].includes(m.status)) break;
  }
  return { status: m.status, error: m.error_code || null };
}
const FLAGS = ["departure_sent", "departure_sent_via", "midstay_sent", "midstay_sent_via"];

// Todos los huéspedes de un hotel en una sola clave (c:<slug>): lectura inmediata tras guardar.
async function load(env, slug) {
  const all = (await env.DB.get(`c:${slug}`, "json")) || [];
  const fresh = all.filter(r => !(r.checkout && Date.parse(r.checkout) < Date.now() - 30 * DAY));
  if (fresh.length !== all.length) await save(env, slug, fresh);
  return fresh;
}
const save = (env, slug, list) => env.DB.put(`c:${slug}`, JSON.stringify(list));
const sorted = list => [...list].sort((a, b) => (a.checkout || "").localeCompare(b.checkout || ""));

export async function onRequest({ request, env }) {
  const SECRET = env.CHECKIN_SECRET || "";
  if (!SECRET) return text("not configured", 500);
  const url = new URL(request.url);

  if (request.method === "GET") {
    if (url.searchParams.get("key") !== SECRET) return text("forbidden", 403);
    return json(sorted(await load(env, clean(url.searchParams.get("h"), 60))));
  }
  if (request.method !== "POST") return text("method not allowed", 405);

  let b;
  try { b = await request.json(); } catch { return text("bad json", 400); }
  const slug = clean(b.h, 60);
  const admin = b.key && b.key === SECRET;
  if (!slug || (!admin && b.t !== await hotelToken(SECRET, slug))) return text("forbidden", 403);
  const action = b.action || "add";
  const list = await load(env, slug);

  if (action === "list") return json(sorted(list));
  if (action === "add") {
    const rec = { id: rid(), created: new Date().toISOString() };
    for (const [f, n] of Object.entries(EDITABLE)) rec[f] = clean(b[f], n);
    if (!rec.name || !rec.checkout || !(rec.phone || rec.email)) return text("missing fields", 400);
    let demo = null;
    if (slug === DEMO_SLUG && rec.phone) {
      demo = await sendDemoWhatsApp(env, rec, clean(b.demo_hotel, 80) || "Hosperai Demo Hotel");
      if (["delivered", "read", "sent"].includes(demo.status)) {
        rec.departure_sent = new Date().toISOString(); rec.departure_sent_via = "WhatsApp";
        await env.DB.put(`p:${rec.phone.replace(/[^0-9]/g, "")}`, JSON.stringify({
          hotel: clean(b.demo_hotel, 80) || "Hosperai Demo Hotel", contact: "",
          lang: rec.lang === "Español" || rec.lang === "Català" ? "es" : "en" }), { expirationTtl: 60 * 86400 });
      }
    }
    list.push(rec);
    await save(env, slug, list);
    return json({ ok: true, id: rec.id, demo });
  }

  const rec = list.find(r => r.id === clean(b.id, 60));
  if (!rec) return text("not found", 404);

  if (action === "update") {
    for (const [f, n] of Object.entries(EDITABLE)) if (f in (b.fields || {})) rec[f] = clean(b.fields[f], n);
    if (!rec.name || !rec.checkout || !(rec.phone || rec.email)) return text("missing fields", 400);
    rec.edited = new Date().toISOString();
  } else if (action === "delete") {
    list.splice(list.indexOf(rec), 1);
  } else if (action === "mark" && admin) {
    if (!["departure_sent", "midstay_sent", "reminder_sent"].includes(b.field)) return text("bad field", 400);
    rec[b.field] = new Date().toISOString();
    rec[`${b.field}_via`] = clean(b.via, 20);
  } else if (action === "reset" && admin) {
    for (const f of FLAGS) delete rec[f];
  } else {
    return text("bad action", 400);
  }
  await save(env, slug, list);
  return json({ ok: true });
}
