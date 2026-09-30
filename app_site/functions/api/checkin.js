import { clean, json, text, rid, hotelToken } from "./_shared.js";

const DAY = 86400000;
const EDITABLE = { name: 80, phone: 30, email: 120, lang: 20, checkin: 10, checkout: 10 };
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
    list.push(rec);
    await save(env, slug, list);
    return json({ ok: true, id: rec.id });
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
    if (!["departure_sent", "midstay_sent"].includes(b.field)) return text("bad field", 400);
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
