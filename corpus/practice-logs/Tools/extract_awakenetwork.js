/* CAPTURE (awakenetwork.org magazine articles) — run in Claude in Chrome
   (javascript_tool) on an awakenetwork journal page. These pages render a whole
   threaded journal as flat <p> text inside [itemprop=articleBody]; posts are
   delimited by <p><strong>USERNAME</strong></p> then a <p>date</p>.

   This parses the article IN-BROWSER into the standard log format and stashes the
   FINISHED .txt in localStorage (key: cap_txt_<slug>). Returns only a tiny status.
   Walk each part, then run combine_download.js once in a fresh tab; the sandbox
   feeds the single JSON to process_payload.py, which writes finished-text values
   straight to .txt.

   Same reasoning as the DhO snippet: never return content through the tool result
   (size cap + query-string filter), and never download per-page (multi-download gate).
*/
(() => {
  const body = document.querySelector('[itemprop=articleBody]') || document.querySelector('.item-page');
  if (!body) return JSON.stringify({ ready: false, note: 'article body not rendered yet — wait and re-run' });
  const title = document.title.replace(/\s*-\s*AwakeNetwork.*$/i, '').trim();
  const url = location.href;

  // byline author (used only for a signed intro block, e.g. Part 1)
  let byline = 'Chris Marti';
  const info = document.querySelector('.article-info');
  if (info) {
    const m = info.textContent.replace(/\s+/g, ' ').match(/Written by\s+(.+?)\s+Category/i);
    if (m) byline = m[1].trim().replace(/^(.+?)\s+\1$/, '$1'); // collapse "X X" -> "X"
  }

  let paras = Array.from(body.querySelectorAll(':scope > p'));
  if (paras.length < 3) paras = Array.from(body.querySelectorAll('p'));
  const norm = s => s.replace(/ /g, ' ');
  const txt = p => norm(p.textContent).trim();
  const isAuthor = p => p.children.length === 1 && p.children[0].tagName === 'STRONG'
      && txt(p) === norm(p.children[0].textContent).trim()
      && txt(p).length > 0 && txt(p).length <= 40;
  const isDate = t => /^[A-Z][a-z]{2,}\s+\d{1,2}\s+\d{4},\s+\d/.test(t) || /^\|\s*Post edited/i.test(t);
  const isSep  = t => /^\*{3,}$/.test(t.replace(/\s/g, ''));

  const firstAuthor = paras.findIndex(isAuthor);
  const preAuthor = paras.slice(0, firstAuthor === -1 ? paras.length : firstAuthor);
  const hasStars = preAuthor.some(p => isSep(txt(p)));
  const blocks = [];
  if (hasStars) { // signed intro (byline author) up to the **** separator
    const intro = [];
    for (const p of preAuthor) { if (isSep(txt(p))) break; const t = txt(p); if (t) intro.push(t); }
    if (intro.length) blocks.push({ user: byline, body: intro.join('\n\n') });
  }
  let i = firstAuthor;
  while (i !== -1 && i < paras.length) {
    if (!isAuthor(paras[i])) { i++; continue; }
    const user = txt(paras[i]);
    let j = i + 1; const bp = []; let first = true;
    while (j < paras.length && !isAuthor(paras[j])) {
      const t = txt(paras[j]);
      // drop any standalone timestamp paragraph (post header), wherever it sits
      if (isDate(t)) { first = false; j++; continue; }
      first = false;
      if (t) bp.push(t);
      j++;
    }
    blocks.push({ user, body: bp.join('\n\n') });
    i = j;
  }
  let s = `Title: ${title}\nURL: ${url}\n\n`;
  for (const b of blocks) s += `User: ${b.user}\n\n${b.body}\n---\n\n`;

  const slug = (url.split('/').pop() || 'article').replace(/[^a-z0-9-]/gi, '');
  const key = 'cap_txt_' + slug;
  localStorage.setItem(key, s);
  return JSON.stringify({
    ready: true, key, title, byline, hasStars,
    blocks: blocks.length, chars: s.length,
    firstUsers: blocks.slice(0, 3).map(b => b.user),
    lastUser: blocks.length ? blocks[blocks.length - 1].user : null
  });
})()
