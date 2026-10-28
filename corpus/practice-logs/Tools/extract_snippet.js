/* CAPTURE — run in Claude in Chrome (javascript_tool) on an open DhO thread page.
   Extracts title + every message's {usernameRaw, contentHTML} and stashes the
   payload in localStorage (key: cap_dho_<threadId>). Returns only a tiny status.

   WHY THIS SHAPE (learned the hard way — see RUNBOOK §3):
   - Do NOT return page content through the tool result: the javascript_tool channel
     is size-capped (~30k) AND runs a safety filter that BLOCKS forum text (it's full
     of query-string URLs -> "[BLOCKED: Cookie/query string data]"). So we return
     only {status}, never the payload.
   - Do NOT download here. Chrome silently blocks the 2nd+ automatic download in a
     tab. Instead we ACCUMULATE every thread into localStorage (persists across
     same-origin navigations) and do ONE download at the end — see combine_download.js.
*/
(() => {
  const cards = Array.from(document.querySelectorAll('div.card.panel'))
    .filter(c => c.querySelector('div.message-content'));
  if (!cards.length) {
    // client-render may not be ready; re-run after a moment
    return JSON.stringify({ ready: false, note: 'no message cards yet — wait and re-run', title: document.title });
  }
  const messages = cards.map(c => {
    const u = c.querySelector('h5.message-user-display');
    const mc = c.querySelector('div.message-content');
    return { usernameRaw: u ? u.textContent : '', contentHTML: mc.innerHTML };
  });
  const payload = {
    title: document.title.replace(/ - Discussion - www\.dharmaoverground\.org$/, ''),
    url: location.href,
    messages
  };
  const id = (location.href.match(/message\/(\d+)/) || [])[1] || String(Date.now());
  const key = 'cap_dho_' + id;
  localStorage.setItem(key, JSON.stringify(payload));
  return JSON.stringify({
    ready: true, key, title: payload.title,
    messageCount: messages.length,
    firstUser: (messages[0].usernameRaw || '').split(',')[0].trim(),
    payloadChars: localStorage.getItem(key).length
  });
})()
