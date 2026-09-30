import { getStore } from "@netlify/blobs";
import crypto from "node:crypto";

const SECRET = process.env.CHECKIN_SECRET || "";
const token = (slug) => crypto.createHmac("sha256", SECRET).update(slug).digest("hex").slice(0, 16);
const clean = (v, n = 120) => String(v || "").trim().slice(0, n);
const DAY = 86400000;

export default async (req) => {
  if (!SECRET) return new Response("not configured", { status: 500 });
  const store = getStore("checkins");
  const url = new URL(req.url);

  if (req.method === "POST") {
    let b;
    try { b = await req.json(); } catch { return new Response("bad json", { status: 400 }); }
    const slug = clean(b.h, 60);
    if (!slug || b.t !== token(slug)) return new Response("forbidden", { status: 403 });
    const rec = {
      name: clean(b.name, 80), phone: clean(b.phone, 30), email: clean(b.email, 120),
      lang: clean(b.lang, 20), checkin: clean(b.checkin, 10), checkout: clean(b.checkout, 10),
      created: new Date().toISOString(),
    };
    if (!rec.name || !rec.checkout || !(rec.phone || rec.email)) return new Response("missing fields", { status: 400 });
    await store.setJSON(`${slug}/${Date.now()}-${crypto.randomBytes(4).toString("hex")}`, rec);
    return Response.json({ ok: true });
  }

  if (req.method === "GET") {
    if (url.searchParams.get("key") !== SECRET) return new Response("forbidden", { status: 403 });
    const slug = clean(url.searchParams.get("h"), 60);
    const { blobs } = await store.list({ prefix: `${slug}/` });
    const out = [];
    for (const b of blobs) {
      const rec = await store.get(b.key, { type: "json" });
      if (rec && rec.checkout && Date.parse(rec.checkout) < Date.now() - 30 * DAY) { await store.delete(b.key); continue; }
      if (rec) out.push(rec);
    }
    return Response.json(out);
  }
  return new Response("method not allowed", { status: 405 });
};

export const config = { path: "/api/checkin" };
