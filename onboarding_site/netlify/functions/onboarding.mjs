import { getStore } from "@netlify/blobs";
import crypto from "node:crypto";

const SECRET = process.env.CHECKIN_SECRET || "";
const FIELDS = ["contact_name", "contact_email", "business_name", "business_type", "address", "google_url", "tripadvisor_url",
  "whatsapp", "notify_lang", "signature", "formality", "length", "use_name", "emojis", "apologise", "take_offline",
  "complaint_contact", "compensation", "scenario_1", "scenario_2", "scenario_3", "highlights", "recurring_complaints",
  "not_offered", "always_mention", "never_say", "notes"];

export default async (req) => {
  const store = getStore({ name: "onboarding", consistency: "strong" });
  if (req.method === "POST") {
    const form = await req.formData();
    if (form.get("bot-field")) return Response.json({ ok: true });
    const data = {};
    for (const f of FIELDS) data[f] = String(form.get(f) || "").trim().slice(0, 1000);
    data.services = form.getAll("services").map(String);
    if (!data.business_name || !data.whatsapp) return new Response("missing fields", { status: 400 });
    const id = `${Date.now()}-${crypto.randomBytes(4).toString("hex")}`;
    await store.setJSON(id, { id, created_at: new Date().toISOString(), data });
    return Response.json({ ok: true });
  }
  if (req.method === "GET") {
    if (!SECRET || new URL(req.url).searchParams.get("key") !== SECRET) return new Response("forbidden", { status: 403 });
    const { blobs } = await store.list();
    const out = [];
    for (const b of blobs) out.push(await store.get(b.key, { type: "json" }));
    return Response.json(out);
  }
  return new Response("method not allowed", { status: 405 });
};

export const config = { path: "/api/onboarding" };
