// app.hosperai.es/g/<hotel> y /t/<hotel> → formulario de reseña directo de Google / Tripadvisor (y cuenta clics por mes).
export async function reviewRedirect({ params, env }, which) {
  const slug = String(params.slug || "").slice(0, 60);
  const links = (await env.DB.get(`r:${slug}`, "json")) || {};
  const target = links[which];
  if (!target) return Response.redirect("https://hosperai.es", 302);
  const k = `n:${slug}:${which}:${new Date().toISOString().slice(0, 7)}`;
  try { await env.DB.put(k, String((parseInt(await env.DB.get(k)) || 0) + 1)); } catch {}
  return Response.redirect(target, 302);
}
