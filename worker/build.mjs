#!/usr/bin/env node
// build.mjs — inline site/index.html + raw file bodies into the bundle.
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from "fs";
import { dirname, join, relative } from "path";
import { fileURLToPath } from "url";

const dir = dirname(fileURLToPath(import.meta.url));
const root = join(dir, "..");
const html = readFileSync(join(root, "site", "index.html"), "utf8");
mkdirSync(join(dir, "src"), { recursive: true });
writeFileSync(
  join(dir, "src", "page.js"),
  "export default " + JSON.stringify(html) + ";\n"
);

const files = {};
const anchors = {};
const dayGroups = {};
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
  if (!f.endsWith(".md")) continue;
  const text = readFileSync(join(root, "tensions", f), "utf8");
  const i = text.indexOf("---");
  files[`tensions/${f}`] =
    i >= 0 ? text.slice(i + 3).replace(/^\n+/, "") : text;
}
files["motto.txt"] = readFileSync(join(root, "motto.txt"), "utf8").trim();
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
