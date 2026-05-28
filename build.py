#!/usr/bin/env python3
"""Build enriched charter data + a NotebookLM-ready document from charter.json."""
import json, re, datetime

SRC = "data/charter.json"
VERS = "data/versions.json"

records = json.load(open(SRC))
versions = json.load(open(VERS))

def chapter_sort_key(citation):
    # "Chapter 18-A" -> (18, 'A'); "Chapter 2-A" -> (2,'A'); "Chapter 11" -> (11,'')
    m = re.match(r"Chapter\s+(\d+)(?:-([A-Z]+))?", citation)
    if not m:
        return (9999, "")
    return (int(m.group(1)), m.group(2) or "")

THIS_YEAR = datetime.date.today().year

def amendment_meta(text):
    """Extract Local Law citations + amendment recency from the editor's note.
    Dating is by Local Law number / explicit dates as recorded by the source
    compiler (American Legal). This is NOT Charter Revision Commission attribution."""
    laws = re.findall(r"L\.L\.\s*((?:19|20)\d{2})/(\d{2,3})", text)
    seen = set(); law_cites = []
    for y, n in laws:
        c = f"L.L. {y}/{n}"
        if c not in seen:
            seen.add(c); law_cites.append(c)
    ll_years = [int(c.split()[1].split('/')[0]) for c in law_cites]
    # The amendment year is the Local Law ENACTMENT year — unambiguous.
    latest = max(ll_years) if ll_years else None
    # Calendar dates in the note may include future EFFECTIVE dates; surface the
    # latest future-effective year separately so we don't mislabel it as "amended".
    cal_years = [int(m) for m in re.findall(r"\b\d{1,2}/\d{1,2}/((?:19|20)\d{2})", text)]
    future_years = [y for y in cal_years if y > THIS_YEAR]
    return {
        "laws": law_cites,
        "amend_count": len(law_cites),
        "latest_amend": latest,
        "eff_future": max(future_years) if future_years else None,
        "has_note": "Editor's note" in text,
    }

def section_sort_key(citation):
    # "§ 259" -> (259, ''); "§ 265-a" -> (265, 'a'); "§ 1-101" -> handle multi-part
    m = re.match(r"§\s*([\d]+)(?:-([\dA-Za-z]+))?", citation)
    if not m:
        return (999999, "")
    return (int(m.group(1)), m.group(2) or "")

# Walk in document order, attach each section to the current chapter.
items = []
current_chapter = {"citation": "Front matter", "heading": "Front matter", "num": 0, "suffix": ""}
chapters = []  # ordered list of chapter dicts

for idx, r in enumerate(records):
    cit = r["citation"]
    is_chapter = cit.startswith("Chapter")
    if is_chapter:
        # The source `citation` is truncated at the hyphen ("Chapter 18-" for
        # 18-A/B/C/D), which collides across distinct sub-chapters. The full
        # heading ("Chapter 18-A: ...") carries the canonical citation.
        hm = re.match(r"(Chapter\s+\d+(?:-[A-Z]+)?)", r["heading"])
        canon = hm.group(1) if hm else cit
        num, suffix = chapter_sort_key(canon)
        title = r["heading"]
        if ":" in title:
            title = title.split(":", 1)[1].strip()
        repealed = "[Repealed]" in r["heading"]
        current_chapter = {
            "citation": canon,
            "heading": r["heading"],
            "title": title,
            "num": num,
            "suffix": suffix,
            "repealed": repealed,
        }
        chapters.append(current_chapter)
        continue

    snum, ssuffix = section_sort_key(cit)
    # Section heading like "Section 259. Independent budget office." -> short title
    heading = r["heading"]
    sec_title = heading
    m = re.match(r"Section\s+[^.]+\.\s*(.*)", heading)
    if m:
        sec_title = m.group(1).strip()
    am = amendment_meta(r["text"])
    items.append({
        "id": r["id"],
        "doc_order": idx,
        "citation": cit,
        "heading": heading,
        "sec_title": sec_title,
        "text": r["text"].strip(),
        "chapter_citation": current_chapter["citation"],
        "chapter_title": current_chapter["title"],
        "chapter_num": current_chapter["num"],
        "chapter_suffix": current_chapter["suffix"],
        "sec_num": snum,
        "sec_suffix": ssuffix,
        "words": len(r["text"].split()),
        "laws": am["laws"],
        "amend_count": am["amend_count"],
        "latest_amend": am["latest_amend"],
        "eff_future": am["eff_future"],
    })

# Build chapter summary (count sections, sort)
chap_index = {}
for it in items:
    c = it["chapter_citation"]
    chap_index.setdefault(c, {
        "citation": c,
        "title": it["chapter_title"],
        "num": it["chapter_num"],
        "suffix": it["chapter_suffix"],
        "count": 0,
    })
    chap_index[c]["count"] += 1

chapter_list = sorted(chap_index.values(), key=lambda c: (c["num"], c["suffix"]))

out = {
    "version": versions,
    "generated": datetime.datetime.now().isoformat(),
    "chapters": chapter_list,
    "sections": items,
    "total_sections": len(items),
}
json.dump(out, open("charter-data.json", "w"), ensure_ascii=False)
print(f"Wrote charter-data.json: {len(items)} sections, {len(chapter_list)} chapters")

# ---- NotebookLM document ----
header = versions.get("charter") if isinstance(versions, dict) else None
# versions.json structure unknown; read raw
raw_v = open(VERS).read()
total_words = sum(it["words"] for it in items)

md = []
md.append("# Charter of the City of New York")
md.append("")
md.append("*The full text of the New York City Charter, organized by chapter and section, "
          "prepared as a single reference document for question-and-answer use.*")
md.append("")
md.append("**Currency:** Current through Local Law 2026/094, enacted May 16, 2026; includes "
          "amendments effective through May 17, 2026.")
md.append(f"**Scope:** {len(items)} sections across {len(chapter_list)} chapters (~{total_words:,} words).")
md.append("**Source:** American Legal Publishing code library (codelibrary.amlegal.com), "
          "compiled via the BetaNYC nyc-charter-laws-rules dataset.")
md.append("")
md.append("> This document is for research and informational purposes only and does not "
          "constitute legal advice. Always verify against the official code at "
          "codelibrary.amlegal.com before relying on any provision.")
md.append("")
md.append("---")
md.append("")
md.append("## Table of contents")
md.append("")
for c in chapter_list:
    rep = " *(repealed)*" if "[Repealed]" in c.get("title", "") else ""
    md.append(f"- **{c['citation']}** — {c['title']} ({c['count']} sections){rep}")
md.append("")
md.append("---")
md.append("")

# Body: group sections by chapter in sorted chapter order, sections in doc order within chapter
by_chapter = {}
for it in items:
    by_chapter.setdefault(it["chapter_citation"], []).append(it)

for c in chapter_list:
    md.append(f"## {c['citation']}: {c['title']}")
    md.append("")
    secs = by_chapter.get(c["citation"], [])
    for it in secs:
        md.append(f"### {it['citation']} — {it['sec_title']}".rstrip(" —"))
        md.append(f"*(in {c['citation']}: {c['title']})*")
        md.append("")
        md.append(it["text"] if it["text"] else "*[No text in source.]*")
        md.append("")
    md.append("")

doc = "\n".join(md)
open("NYC-Charter-for-NotebookLM.md", "w").write(doc)
# plain text version
open("NYC-Charter-for-NotebookLM.txt", "w").write(doc)
print(f"Wrote NotebookLM doc: ~{total_words:,} words, {len(doc):,} chars")
