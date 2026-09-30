import { clean, json, text, rid } from "./_shared.js";

const FIELDS = ["contact_name", "contact_email", "business_name", "business_type", "address", "google_url", "tripadvisor_url",
  "whatsapp", "notify_lang", "signature", "formality", "length", "use_name", "emojis", "apologise", "take_offline",
  "complaint_contact", "compensation", "scenario_1", "scenario_2", "scenario_3", "highlights", "recurring_complaints",
  "not_offered", "always_mention", "never_say", "notes", "reply_preferences", "vip_message", "guest_contact", "plan"];

export async function onRequest({ request, env }) {
  if (request.method === "POST") {
    const form = await request.formData();
    if (form.get("bot-field")) return json({ ok: true });
    const data = {};
    for (const f of FIELDS) data[f] = clean(form.get(f), 1000);
    data.services = form.getAll("services").map(String);
    if (!data.business_name || !data.whatsapp) return text("missing fields", 400);
    const id = rid();
    await env.DB.put(`o:${id}`, JSON.stringify({ id, created_at: new Date().toISOString(), data }));
    return json({ ok: true });
  }
  if (request.method === "GET") {
    if (!env.CHECKIN_SECRET || new URL(request.url).searchParams.get("key") !== env.CHECKIN_SECRET) return text("forbidden", 403);
    const out = [];
    let cursor;
    do {
      const page = await env.DB.list({ prefix: "o:", cursor });
      for (const k of page.keys) { const v = await env.DB.get(k.name, "json"); if (v) out.push(v); }
      cursor = page.list_complete ? null : page.cursor;
    } while (cursor);
    return json(out);
  }
  return text("method not allowed", 405);
}
