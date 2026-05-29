#!/usr/bin/env node
// Download the Charter bulk XML zip from American Legal Publishing into ./raw/.
// Charter-only trim of BetaNYC's scripts/fetch-data.js (same source URL).
import { createWriteStream, mkdirSync } from "fs";
import { pipeline } from "stream/promises";
import { Readable } from "stream";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const RAW = join(__dirname, "raw");
mkdirSync(RAW, { recursive: true });

// https (their script used http and relied on a 301 -> https redirect).
const URL = "https://files.amlegal.com/pdffiles/NewYorkCity/Charter/XML.zip";
const dest = join(RAW, "charter.zip");

console.log(`Downloading charter from ${URL} ...`);
const res = await fetch(URL, {
  headers: {
    "User-Agent":
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " +
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
  },
});
if (!res.ok) {
  console.error(`Failed: HTTP ${res.status}`);
  process.exit(1);
}
await pipeline(Readable.fromWeb(res.body), createWriteStream(dest));
console.log(`Saved ${dest}`);
