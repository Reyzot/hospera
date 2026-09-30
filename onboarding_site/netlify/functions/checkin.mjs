import { getStore } from "@netlify/blobs";
import crypto from "node:crypto";

const SECRET = process.env.CHECKIN_SECRET || "";
const token = (slug) => crypto.createHmac("sha256", SECRET).update(slug).digest("hex").slice(0, 16);
const clean = (v, n = 120) => String(v || "").trim().slice(0, n);
const DAY = 86400000;
const EDITABLE = { name: 80, phone: 30, email: 120, lang: 20, checkin: 10, checkout: 10 };

async function listHotel(store, slug) {
  const { blobs } = await store.list({ prefix: `${slug}/` });
  const out = [];
  for (const b of blobs) {
    const rec = await store.get(b.key, { type: "json" });
    if (!rec) continue;
    if (rec.checkout && Date.parse(rec.checkout) < Date.now() - 30 * DAY) { await store.delete(b.key); continue; }
    out.push({ ...rec, id: b.key.slice(slug.length + 1) });
  }
  return out.sort((a, b) => (a.checkout || "").localeCompare(b.checkout || ""));
}

export default async (req) => {
  if (!SECRET) return new Response("not configured", { status: 500 });
  const store = getStore({ name: "checkins", consistency: "strong" });
  const url = new URL(req.url);

  if (req.method === "GET") {
    if (url.searchParams.get("key") !== SECRET) return new Response("forbidden", { status: 403 });
    return Response.json(await listHotel(store, clean(url.searchParams.get("h"), 60)));
  }
  if (req.method !== "POST") return new Response("method not allowed", { status: 405 });

  let b;
  try { b = await req.json(); } catch { return new Response("bad json", { status: 400 }); }
  const slug = clean(b.h, 60);
  const action = b.action || "add";
  const admin = b.key && b.key === SECRET;
  if (!slug || (!admin && b.t !== token(slug))) return new Response("forbidden", { status: 403 });
  const id = clean(b.id, 60).replace(/[^a-z0-9-]/gi, "");
  const key = `${slug}/${id}`;

  if (action === "add") {
    const rec = { created: new Date().toISOString() };
    for (const [f, n] of Object.entries(EDITABLE)) rec[f] = clean(b[f], n);
    if (!rec.name || !rec.checkout || !(rec.phone || rec.email)) return new Response("missing fields", { status: 400 });
    await store.setJSON(`${slug}/${Date.now()}-${crypto.randomBytes(4).toString("hex")}`, rec);
    return Response.json({ ok: true });
  }
  if (action === "list") return Response.json(await listHotel(store, slug));

  const rec = id && await store.get(key, { type: "json" });
  if (!rec) return new Response("not found", { status: 404 });

  if (action === "update") {
    for (const [f, n] of Object.entries(EDITABLE)) if (f in (b.fields || {})) rec[f] = clean(b.fields[f], n);
    if (!rec.name || !rec.checkout || !(rec.phone || rec.email)) return new Response("missing fields", { status: 400 });
    rec.edited = new Date().toISOString();
    await store.setJSON(key, rec);
    return Response.json({ ok: true });
  }
  if (action === "delete") { await store.delete(key); return Response.json({ ok: true }); }
  if (action === "mark" && admin) {
    if (!["departure_sent", "midstay_sent"].includes(b.field)) return new Response("bad field", { status: 400 });
    rec[b.field] = new Date().toISOString();
    rec[`${b.field}_via`] = clean(b.via, 20);
    await store.setJSON(key, rec);
    return Response.json({ ok: true });
  }
  if (action === "reset" && admin) {
    for (const f of ["departure_sent", "departure_sent_via", "midstay_sent", "midstay_sent_via"]) delete rec[f];
    await store.setJSON(key, rec);
    return Response.json({ ok: true });
  }
  return new Response("bad action", { status: 400 });
};

export const config = { path: "/api/checkin" };
