import PAGE from "./page.js";

export default {
  async fetch(req) {
    const url = new URL(req.url);
    if (url.pathname === "/") {
      return new Response(PAGE, {
        headers: { "content-type": "text/html; charset=utf-8" },
      });
    }
    if (url.pathname === "/health") {
      return new Response("ok", { headers: { "content-type": "text/plain" } });
    }
    return new Response("nothing here", { status: 404 });
  },
};
