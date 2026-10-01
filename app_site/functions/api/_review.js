// app.hosperai.es/g/<hotel> y /t/<hotel> → formulario de reseña directo de Google / Tripadvisor.
// Cuenta clics por mes y, si lleva ?u=<id del huésped>, lo marca en su ficha (para no mandarle el recordatorio).
export async function reviewRedirect({ params, env, request }, which) {
  const slug = String(params.slug || "").slice(0, 60);
  const links = (await env.DB.get(`r:${slug}`, "json")) || {};
  const target = links[which];
  if (!target) return Response.redirect("https://hosperai.es", 302);
  const k = `n:${slug}:${which}:${new Date().toISOString().slice(0, 7)}`;
  try { await env.DB.put(k, String((parseInt(await env.DB.get(k)) || 0) + 1)); } catch {}
  const u = new URL(request.url).searchParams.get("u");
  if (u) {
    try {
      const list = (await env.DB.get(`c:${slug}`, "json")) || [];
      const g = list.find(x => x.id === u);
      if (g && !g[`clicked_${which}`]) { g[`clicked_${which}`] = new Date().toISOString(); await env.DB.put(`c:${slug}`, JSON.stringify(list)); }
    } catch {}
  }
  return Response.redirect(target, 302);
}
