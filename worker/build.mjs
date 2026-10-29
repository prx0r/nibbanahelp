#!/usr/bin/env node
// build.mjs — inline site/index.html + raw file bodies into the bundle.
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from "fs";
import { dirname, join, relative } from "path";
import { fileURLToPath } from "url";

const dir = dirname(fileURLToPath(import.meta.url));
const root = join(dir, "..");
const gapMatch = readFileSync(join(root, "tools", "site.py"), "utf8").match(/^GAP = "([^"]+)"/m);
const gap = gapMatch ? gapMatch[1] : "1rem";
mkdirSync(join(dir, "src"), { recursive: true });
writeFileSync(join(dir, "src", "theme.js"), `export const GAP = ${JSON.stringify(gap)};\n`);
const html = readFileSync(join(root, "site", "index.html"), "utf8");
writeFileSync(
  join(dir, "src", "page.js"),
  "export default " + JSON.stringify(html) + ";\n"
);

const files = {};
const anchors = {};
const dayGroups = {};
const tensionRoots = {};
for (const sub of ["entries", "essays"]) {
  for (const f of readdirSync(join(root, sub))) {
    if (!f.endsWith(".md") || f.startsWith("_")) continue;
    const text = readFileSync(join(root, sub, f), "utf8");
    const i = text.indexOf("---");
    const m = text.match(/^day:\s*(\S+)/m);
    const day = m ? m[1] : "?";
    const body = i >= 0 ? text.slice(i + 3).replace(/^\n+/, "") : text;
    files[`${sub}/${f}`] = body;
    const g = (dayGroups[day] ||= { entries: [], essays: [] });
    g[sub].push(`${sub}/${f}`);
  }
}
for (const f of readdirSync(join(root, "tensions"))) {
  if (!f.endsWith(".md") || f.startsWith("_")) continue;
  const text = readFileSync(join(root, "tensions", f), "utf8");
  const i = text.indexOf("---");
  files[`tensions/${f}`] =
    i >= 0 ? text.slice(i + 3).replace(/^\n+/, "") : text;
  const m = text.match(/^roots:\s*\[(.+?)\]\s*$/m);
  if (m) tensionRoots[`tensions/${f}`] = m[1].split(",").map((s) => s.trim());
}
files["motto.txt"] = readFileSync(join(root, "motto.txt"), "utf8").trim();
writeFileSync(
  join(dir, "src", "tension_roots.js"),
  "export default " + JSON.stringify(tensionRoots) + ";\n"
);

// grounding context for chat: live tensions + root profiles, truncated
let context = "LIVE TENSIONS:\n";
for (const f of readdirSync(join(root, "tensions"))) {
  if (!f.endsWith(".md")) continue;
  const text = readFileSync(join(root, "tensions", f), "utf8");
  const head = text.split("---")[0];
  const get = (k) => (head.match(new RegExp(`^${k}:\\s*(.+)$`, "m")) || [])[1] || "";
  const body = text.split("---")[1].trim();
  const clipped = body.length > 900 ? body.slice(0, 300) + "\n[...]\n" + body.slice(-500) : body.slice(0, 900);
  context += `- ${get("id")} [${get("status")}] roots=${get("roots")} :: ${get("summary")}\n  ${clipped}\n`;
}
context += "\nDIARY (verbatim, newest last):\n";
for (const sub of ["entries", "essays"]) {
  for (const f of readdirSync(join(root, sub))) {
    if (!f.endsWith(".md") || f.startsWith("_")) continue;
    const text = readFileSync(join(root, sub, f), "utf8");
    const body = (text.split("---")[1] || text).trim().slice(0, 600);
    context += `--- ${sub}/${f} ---\n${body}\n`;
  }
}
context += "\nROOTS:\n";
for (const f of ["greed-lobha.md", "hatred-dosa.md", "delusion-moha.md", "abhidhamma.md"]) {
  try {
    context += `--- ${f} ---\n` + readFileSync(join(root, "roots", f), "utf8").slice(0, 900) + "\n";
  } catch (e) { /* skip */ }
}
writeFileSync(
  join(dir, "src", "context.js"),
  "export default " + JSON.stringify(context.slice(0, 8000)) + ";\n"
);

// static pages (built by tools/site.py)
for (const p of ["chat.html", "vis.html"]) {
  writeFileSync(
    join(dir, "src", p.replace(".", "_") + ".js"),
    "export default " + JSON.stringify(readFileSync(join(root, "site", p), "utf8")) + ";\n"
  );
}
for (const day of Object.keys(dayGroups)) {
  dayGroups[day].entries.forEach((f, n) => (anchors[`d${day}-e${n}`] = f));
  dayGroups[day].essays.forEach((f, n) => (anchors[`d${day}-s${n}`] = f));
}
writeFileSync(
  join(dir, "src", "files.js"),
  "export default " + JSON.stringify(files) + ";\n"
);
writeFileSync(
  join(dir, "src", "anchors.js"),
  "export default " + JSON.stringify(anchors) + ";\n"
);
console.log("inlined", html.length, "bytes html +",
  Object.keys(files).length, "files +",
  Object.keys(anchors).length, "anchors");
