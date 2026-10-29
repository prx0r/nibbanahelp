import PAGE from "./page.js";
import FILES from "./files.js";
import { GAP } from "./theme.js";
import CONTEXT from "./context.js";
import CHAT_PAGE from "./chat_html.js";
import VIS_PAGE from "./vis_html.js";
import TENSION_ROOTS from "./tension_roots.js";

const ALLOWED = /^(entries|essays|tensions)\/[^/]+\.md$|^motto\.txt$/;

const SYSTEM =
  "You are a dharma friend inside nibbanahelp, a shared diary of people " +
  "attaining nibbana. STRICT RULES: never give advice, recommendations, " +
  "or instructions. Only two moves: (1) ask questions — especially " +
  "questions that help the diarist notice and name tensions (cravings, " +
  "irritations, fog) in ordinary daily situations; (2) relay relevant " +
  "passages from the provided context, always with their source. When " +
  "you see a tension forming, name it plainly and map it to its root: " +
  "lobha (greed, pulling), dosa (hate, pushing), moha (delusion, fog). " +
  "If they ask what to do, reflect the question back with a sharper " +
  "question plus the most relevant relayed passage. Short replies. " +
  "One question at a time. Advanced mode: probe for specific mental " +
  "factors, not just roots — restlessness? doubt? view? conceit? worry? " +
  "aversion? Name the citta-class (e.g. doubt-rooted, worry-laden) rather " +
  "than labelling whole life situations; a debt is not greed, a doubting " +
  "mind-moment is delusion. Always separate the circumstance (real — e.g. " +
  "debt owed, to be handled practically by sustaining oneself) from the " +
  "affliction it incurs (mental states to discern, never to obey). " +
  "Lead with what you relayed — quoted passages with sources first, " +
  "your own words minimal and interrogative. You are " +
  "a finder, not a teacher.";

function page(title, inner) {
  return new Response(
    `<!doctype html><html><head><meta charset=utf-8>` +
      `<meta name=viewport content='width=device-width,initial-scale=1'>` +
      `<title>${title}</title><style>` +
      `body{background:#fff;color:#000;font-family:monospace;` +
      `margin:0;padding:0 ${GAP}}` +
      `a{color:#000}` +
      `pre{white-space:pre-wrap;font-family:monospace}` +
      `pre.blk{width:fit-content;max-width:100%;cursor:text}` +
      `.motto-blk{text-align:center;cursor:default}` +
      `.motto-line{text-align:center}` +
      `.motto{display:inline-block;font-style:italic;text-align:center;cursor:text}` +
      `#wrap{display:flex}` +
      `#nav{flex-shrink:0;padding-top:1rem;padding-right:${GAP};` +
      `font-size:.8rem}` +
      `#nav .daybox{display:flex;align-items:center;justify-content:center;width:2.2rem;height:2.2rem;` +
      `background:#fff;color:#000;border:1px solid #000;` +
      `font-family:monospace;font-size:1rem;` +
      `margin-bottom:.3rem}` +
      `#nav div{margin-bottom:.6rem}` +
      `#nav div a{display:block;padding:.15rem 0}` +
      `body{touch-action:manipulation}` +
      `#main{flex:1;min-width:0}` +
      `textarea{width:100%;box-sizing:border-box;font-family:monospace;` +
      `font-size:1rem;border:1px solid #000;padding:.5rem}` +
      `button{background:#000;color:#fff;border:0;padding:.6rem 1.2rem;` +
      `font-size:1rem;cursor:pointer}form{margin:2rem 0}` +
      `input[type=password]{font-family:monospace;font-size:1rem;` +
      `border:1px solid #000;padding:.5rem;width:100%;box-sizing:border-box}` +
      `</style></head><body>${inner}<script>` +
      `function t(id){var e=document.getElementById(id);` +
      `e.style.display=e.style.display==='none'?'block':'none';}` +
      `</script></body></html>`,
    { headers: { "content-type": "text/html; charset=utf-8" } }
  );
}

function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function cosine(a, b) {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length && i < b.length; i++) {
    dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i];
  }
  return dot / (Math.sqrt(na) * Math.sqrt(nb) + 1e-9);
}

let RELAY = null;
async function loadRelay(env) {
  if (RELAY) return RELAY;
  const [v, i] = await Promise.all([
    env.BRAIN.get("relay/vectors.json").then((r) => (r ? r.json() : {})),
    env.BRAIN.get("relay/index.json").then((r) => (r ? r.json() : [])),
  ]);
  let dharma = [], dharmaByConcept = {};
  try {
    const [dp, de] = await Promise.all([
      env.BRAIN.get("relay/dharma/passages.jsonl").then((r) => (r ? r.text() : "")),
      env.BRAIN.get("relay/dharma/passage_edges.jsonl").then((r) => (r ? r.text() : "")),
    ]);
    const byId = {};
    for (const line of dp.split("\n")) {
      if (!line.trim()) continue;
      try { const p = JSON.parse(line); byId[p.id] = p; dharma.push(p); } catch (e) { /* skip */ }
    }
    for (const line of de.split("\n")) {
      if (!line.trim()) continue;
      try {
        const e = JSON.parse(line);
        (dharmaByConcept[e.target] ||= []).push(e.source);
      } catch (err) { /* skip */ }
    }
    RELAY = { vecs: v, items: i, dharma, dharmaById: byId, dharmaByConcept };
  } catch (e) {
    RELAY = { vecs: v, items: i, dharma, dharmaByConcept };
  }
  return RELAY;
}

function stemKey(id) {
  return String(id).split(":").pop().replace(/^tension-/, "");
}

async function matchPassages(env, query, k = 5) {
  const { vecs, items, dharma, dharmaById, dharmaByConcept } = await loadRelay(env);
  if (!items.length) return [];
  const emb = await env.AI.run("@cf/baai/bge-m3", { text: [query] });
  const q = emb.data ? emb.data[0] : emb.result.data[0];
  const BOOST = { "own-tension": 1.35, "own-chat": 1.25, "canon": 1.1 };
  const scored = [];
  for (const item of items) {
    const v = vecs[item.id];
    if (!v) continue;
    scored.push([cosine(q, v) * (BOOST[item.kind] || 1), item]);
  }
  scored.sort((a, b) => b[0] - a[0]);
  let cands = scored.slice(0, 20).map(([, item]) => item);
  // graph stage: roots of matched tensions -> concept-constrained passages
  try {
    const roots = new Set();
    for (const c of cands) {
      let tid = null;
      if (typeof c.id === "string" && c.id.startsWith("tension:")) tid = "tensions/" + c.id.slice(8) + ".md";
      else if (typeof c.url === "string" && c.url.startsWith("tensions/")) tid = c.url;
      const rs = tid && TENSION_ROOTS[tid];
      if (rs) rs.forEach((r) => roots.add(r));
    }
    const seen = new Set(cands.map((c) => stemKey(c.id)));
    for (const r of roots) {
      for (const pid of (dharmaByConcept[r] || []).slice(0, 3)) {
        if (seen.has(stemKey(pid))) continue;
        seen.add(stemKey(pid));
        const p = dharmaById[pid];
        if (!p) continue;
        cands.push({ id: pid, kind: "graph", label: p.summary || p.text_id || pid,
                     url: p.text_id || "", text: p.text || "" });
      }
    }
  } catch (e) { /* graph stage optional */ }
  cands = cands.slice(0, 26);
  let ranked = cands;
  try {
    const rr = await env.AI.run("@cf/baai/bge-reranker-base", {
      query,
      contexts: ranked.map((item) => ({ text: (item.text || "").slice(0, 1000) })),
    });
    const order = (rr.response || rr.result?.response || [])
      .slice()
      .sort((a, b) => b.score - a.score)
      .map((r) => r.id)
      .filter((i) => Number.isInteger(i) && i >= 0 && i < ranked.length);
    if (order.length) ranked = order.map((i) => ranked[i]);
  } catch (e) { /* fall back to cosine order */ }
  return ranked.slice(0, k);
}

function livePage() {
  const m = PAGE.match(/<body>([\s\S]*)<\/body>/);
  return m ? m[1] : PAGE;
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);

    if (url.pathname === "/") {
      return page("nibbanahelp", livePage());
    }

    if (url.pathname === "/vis") {
      return new Response(VIS_PAGE, {
        headers: { "content-type": "text/html; charset=utf-8" },
      });
    }

    if (url.pathname === "/chat" && req.method === "GET") {
      return new Response(CHAT_PAGE, {
        headers: { "content-type": "text/html; charset=utf-8" },
      });
    }

    if (url.pathname === "/chat" && req.method === "POST") {
      let data;
      try {
        data = await req.json();
      } catch (e) {
        return new Response("bad json", { status: 400 });
      }
      const sid = typeof data.sid === "string" && /^[A-Za-z0-9_-]{1,32}$/.test(data.sid) ? data.sid : "x";
      const hist = Array.isArray(data.messages) ? data.messages.slice(-12) : [];
      const clean = hist.filter((m) => m && (m.role === "user" || m.role === "assistant") && typeof m.content === "string").slice(-12);
      if (!clean.length || clean[clean.length - 1].role !== "user") {
        return new Response("no question", { status: 400 });
      }
      const query = clean[clean.length - 1].content;
      let relay = [];
      try {
        relay = await matchPassages(env, query, 5);
      } catch (e) { /* chat still works without relay */ }
      const relayBlock = relay.length
        ? "\n\nSIMILAR LIVED PASSAGES (relay these with their sources, never invent advice):\n" +
          relay.map((m) => `- [${m.kind}] ${m.label} :: ${m.url}\n  ${m.text.slice(0, 600)}`).join("\n")
        : "";
      const messages = [{ role: "system", content: SYSTEM + "\n\nContext (live tensions + roots):\n" + CONTEXT + relayBlock }, ...clean.map((m) => ({ role: m.role, content: m.content.slice(0, 2000) }))];
      let reply;
      try {
        const out = await env.AI.run("@cf/deepseek-ai/deepseek-v4-flash", { messages, max_tokens: 800 });
        reply = out.response || out.result?.response || (out.choices && out.choices[0] && out.choices[0].message && out.choices[0].message.content) || "";
        if (typeof reply !== "string" || !reply.trim()) throw new Error("empty");
      } catch (e) {
        return new Response(JSON.stringify({ error: "ai unavailable" }), { status: 502, headers: { "content-type": "application/json" } });
      }
      await env.BRAIN.put(`pending/chat/${sid}/${Date.now()}.json`, JSON.stringify({ sid, at: new Date().toISOString(), user: query, assistant: reply, relayed: relay.map((m) => m.id) }));
      return new Response(JSON.stringify({ reply, sources: relay.map((m) => ({ label: m.label, url: m.url, excerpt: (m.text || "").slice(0, 280) })) }), { headers: { "content-type": "application/json" } });
    }

    if (url.pathname === "/save" && req.method === "POST") {
      const form = await req.formData();
      const f = form.get("f");
      const body = form.get("body");
      if (typeof f !== "string" || !ALLOWED.test(f) || !(f in FILES)) {
        return new Response("bad file", { status: 400 });
      }
      if (typeof body !== "string" || body.length > 200000) {
        return new Response("bad body", { status: 400 });
      }
      if (f === "motto.txt" && body.split("\n").filter((l) => l.trim()).length > 5) {
        return new Response("max 5 lines", { status: 400 });
      }
      await env.BRAIN.put("pending/" + f, body);
      return page(
        "saved",
        `<p>saved — syncs into the diary on the next sync run.</p>` +
          `<p><a href='/'>back</a></p>`
      );
    }

    if (url.pathname === "/health") {
      return new Response("ok", { headers: { "content-type": "text/plain" } });
    }

    return new Response("nothing here", { status: 404 });
  },
};
