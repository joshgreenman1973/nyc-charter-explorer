#!/usr/bin/env node
// Parse ./raw/charter.zip into ./out/charter.json + ./out/charter-version.json.
// Verbatim parser logic from BetaNYC's scripts/build-index.js (charter-only),
// so output matches the original data byte-for-byte. Do not "improve" the text
// extraction here — fidelity to the source-of-record is the whole point.
import { XMLParser } from "fast-xml-parser";
import AdmZip from "adm-zip";
import { writeFileSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const RAW = join(__dirname, "raw");
const OUT = join(__dirname, "out");
mkdirSync(OUT, { recursive: true });

const parser = new XMLParser({
  ignoreAttributes: false,
  attributeNamePrefix: "@_",
  textNodeName: "#text",
  isArray: (name) => ["LEVEL", "RECORD", "PARA", "CHARFORMAT"].includes(name),
});

function extractText(node) {
  if (!node) return "";
  if (typeof node === "string") return node;
  if (typeof node === "number") return String(node);
  let text = "";
  if (node["#text"]) text += node["#text"];
  for (const [key, val] of Object.entries(node)) {
    if (key.startsWith("@_") || key === "#text") continue;
    if (Array.isArray(val)) text += val.map(extractText).join(" ");
    else if (typeof val === "object") text += extractText(val);
  }
  return text.replace(/\s+/g, " ").trim();
}

function extractVersion(parsed) {
  try {
    const m = JSON.stringify(parsed).match(/Current through[^"\\]*/);
    if (m) return m[0].replace(/\\n/g, " ").replace(/\[ALP.*?\]/g, "").replace(/\s+/g, " ").trim();
  } catch {}
  return "Unknown";
}

function extractCitation(heading) {
  const s = heading.match(/[Ss]ection\s+([\d\-\.a-zA-Z]+)/);
  if (s) return `§ ${s[1].replace(/\.$/, "")}`;
  const c = heading.match(/[Cc]hapter\s+([\d\-]+)/);
  if (c) return `Chapter ${c[1]}`;
  const t = heading.match(/[Tt]itle\s+([\d\-]+)/);
  if (t) return `Title ${t[1]}`;
  return heading.split(":")[0].split(".")[0].trim();
}

function collectSections(node, corpus, sections) {
  if (!node) return;
  const levels = [node.LEVEL].flat().filter(Boolean);
  for (const level of levels) {
    const styleName = level["@_style-name"] || "";
    const records = [level.RECORD].flat().filter(Boolean);
    for (const record of records) {
      const heading = extractText(record.HEADING || "");
      if (!heading) continue;
      if ((styleName === "Section" || styleName === "Chapter") && heading.length > 3) {
        const bodyParts = [];
        const childLevels = [level.LEVEL].flat().filter(Boolean);
        for (const child of childLevels) {
          if ((child["@_style-name"] || "") === "Normal Level") {
            const childRecords = [child.RECORD].flat().filter(Boolean);
            for (const cr of childRecords) {
              const paras = [cr.PARA].flat().filter(Boolean);
              bodyParts.push(...paras.map(extractText));
            }
          }
        }
        sections.push({
          corpus,
          id: record["@_id"] || "",
          citation: extractCitation(heading),
          heading,
          text: bodyParts.join(" ").replace(/\s+/g, " ").trim(),
        });
      }
    }
    collectSections(level, corpus, sections);
  }
}

const zip = new AdmZip(join(RAW, "charter.zip"));
const entries = zip
  .getEntries()
  .filter((e) => e.entryName.startsWith("XML/") && e.entryName.endsWith(".xml"));
console.log(`Found ${entries.length} XML files`);

let version = "Unknown";
const sections = [];
for (const entry of entries) {
  const xml = entry.getData().toString("utf8").replace(/^﻿/, "");
  let parsed;
  try {
    parsed = parser.parse(xml);
  } catch (e) {
    console.warn(`  skip ${entry.entryName}: ${e.message}`);
    continue;
  }
  if (entry.entryName.endsWith("0-0-0-1.xml")) version = extractVersion(parsed);
  collectSections(parsed.DOCUMENT, "charter", sections);
}
console.log(`Indexed ${sections.length} sections. Version: ${version}`);

writeFileSync(join(OUT, "charter.json"), JSON.stringify(sections, null, 2));
writeFileSync(
  join(OUT, "charter-version.json"),
  JSON.stringify({ currentThrough: version, sectionCount: sections.length }, null, 2)
);
console.log(`Wrote out/charter.json + out/charter-version.json`);
