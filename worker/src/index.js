import PAGE from "./page.js";
import FILES from "./files.js";
import ANCHORS from "./anchors.js";

const ALLOWED = /^(entries|essays|tensions)\/[^/]+\.md$|^motto\.txt$/;

function page(title, inner) {
  return new Response(
    `<!doctype html><html><head><meta charset=utf-8>` +
      `<meta name=viewport content='width=device-width,initial-scale=1'>` +
      `<title>${title}</title><style>` +
      `body{background:#fff;color:#000;font-family:monospace;` +
      `margin:0;padding:0 1rem}` +
      `a{color:#000}pre{white-space:pre-wrap;font-family:monospace}` +
      `#wrap{display:flex}` +
      `#nav{width:12rem;flex-shrink:0;padding-top:1rem}` +
      `#nav button{display:block;width:2.2rem;height:2.2rem;` +
      `background:#fff;color:#000;border:1px solid #000;` +
      `font-family:monospace;font-size:1rem;cursor:pointer;` +
      `margin-bottom:.3rem}` +
      `#nav div{font-size:.8rem;margin-bottom:.6rem}` +
      `#main{flex:1;min-width:0}` +
      `.motto{color:#888;font-style:italic}` +
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

function livePage() {
  const withEdits = PAGE.replace(
    /<span id="(d\d+-[es]\d+)"><\/span>/g,
    (m, id) =>
      ANCHORS[id]
        ? `${m}<p><a href="/edit?f=${ANCHORS[id]}">edit</a></p>`
        : m
  );
  const m = withEdits.match(/<body>([\s\S]*)<\/body>/);
  return m ? m[1] : withEdits;
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);

    if (url.pathname === "/") {
      return page("nibbanahelp", livePage());
    }

    if (url.pathname === "/edit") {
      const f = url.searchParams.get("f") || "";
      if (!ALLOWED.test(f) || !(f in FILES)) {
        return new Response("no such file", { status: 404 });
      }
      let body = FILES[f];
      const pend = await env.BRAIN.get("pending/" + f);
      if (pend) body = await pend.text();
      return page(
        "edit " + f,
        `<form method=post action=/save>` +
          `<input type=hidden name=f value="${f}">` +
          `<textarea name=body rows=30>${esc(body)}</textarea><br>` +
          `<label>password <input type=password name=pw></label><br><br>` +
          `<button>save</button></form>` +
          `<p><a href='/'>back (discard)</a></p>`
      );
    }

    if (url.pathname === "/save" && req.method === "POST") {
      const form = await req.formData();
      if (form.get("pw") !== env.EDIT_PASSWORD) {
        return new Response("wrong password", { status: 401 });
      }
      const f = form.get("f");
      const body = form.get("body");
      if (typeof f !== "string" || !ALLOWED.test(f) || !(f in FILES)) {
        return new Response("bad file", { status: 400 });
      }
      if (typeof body !== "string" || body.length > 200000) {
        return new Response("bad body", { status: 400 });
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
