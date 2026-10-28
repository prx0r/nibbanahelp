#!/usr/bin/env node
// build.mjs — inline site/index.html into the worker bundle. No deps.
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const dir = join(dirname(fileURLToPath(import.meta.url)));
const html = readFileSync(join(dir, "..", "site", "index.html"), "utf8");
mkdirSync(join(dir, "src"), { recursive: true });
writeFileSync(
  join(dir, "src", "page.js"),
  "export default " + JSON.stringify(html) + ";\n"
);
console.log("inlined", html.length, "bytes -> worker/src/page.js");
