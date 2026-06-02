#!/usr/bin/env python3
"""Fetch the Charter bulk XML from American Legal Publishing and extract it to
refresh/out/charter.json — using a DOCUMENT-ORDER parser.

Why this replaced the earlier fast-xml-parser (Node) step:
  The Charter XML interleaves inline <LINK> cross-reference elements (and
  <CHARFORMAT> spans) inside the running text, e.g.
      ...established pursuant to section <LINK>two hundred ninety-eight</LINK> of...
  fast-xml-parser groups child elements by tag and appends their text AFTER the
  surrounding text, which silently REORDERS the inline values to the end of the
  sentence (so "section 277 and 278 of the charter" came out as "sectionand of
  the charter ... two hundred seventy-seven two hundred seventy-eight"). Python's
  ElementTree reads text in document order (via itertext), which preserves it.

It also adds one cosmetic fix: the source has no space after a subdivision marker
("a.any goods" -> "a. any goods"). Only clause-leading single letters (and short
roman numerals) are touched; "e.g."/"i.e." do not appear in the Charter and URLs
like nyc.gov are excluded by the whitespace lookbehind.

Output schema matches what build.py consumes: a list of
{corpus, id, citation, heading, text}, plus out/charter-version.json.
"""
import io, os, re, sys, json, zipfile, urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
RAW = os.path.join(HERE, "raw")
XML_URL = "https://files.amlegal.com/pdffiles/NewYorkCity/Charter/XML.zip"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def fix_subdivisions(text):
    # add a space after a clause-leading subdivision marker that runs into the next word
    text = re.sub(r'(?<=\s)([a-z])\.(?=[a-z])', r'\1. ', text)
    text = re.sub(r'(?<=[\s;:])(i{2,3}|iv|vi{0,3})\.(?=[a-z])', r'\1. ', text)
    return text


def node_text(el):
    """All text under a node, in document order, whitespace-collapsed."""
    return re.sub(r'\s+', ' ', ''.join(el.itertext())).strip()


def heading_text(rec):
    h = rec.find('HEADING')
    return node_text(h) if h is not None else ''


def extract_citation(h):
    m = re.search(r'[Ss]ection\s+([\d\-\.a-zA-Z]+)', h)
    if m:
        return '§ ' + re.sub(r'\.$', '', m.group(1))
    m = re.search(r'[Cc]hapter\s+([\d\-]+)', h)
    if m:
        return 'Chapter ' + m.group(1)
    m = re.search(r'[Tt]itle\s+([\d\-]+)', h)
    if m:
        return 'Title ' + m.group(1)
    return h.split(':')[0].split('.')[0].strip()


def collect(parent, corpus, out):
    for level in parent.findall('LEVEL'):
        style = level.get('style-name', '')
        for rec in level.findall('RECORD'):
            heading = heading_text(rec)
            if not heading:
                continue
            if style in ('Section', 'Chapter') and len(heading) > 3:
                body = []
                for child in level.findall('LEVEL'):
                    if child.get('style-name', '') == 'Normal Level':
                        for cr in child.findall('RECORD'):
                            for para in cr.findall('PARA'):
                                body.append(node_text(para))
                text = re.sub(r'\s+', ' ', ' '.join(body)).strip()
                out.append({
                    'corpus': corpus, 'id': rec.get('id', ''),
                    'citation': extract_citation(heading), 'heading': heading,
                    'text': fix_subdivisions(text),
                })
        collect(level, corpus, out)


def extract_version(root):
    # the "Current through ..." line is split across a <LINEBRK/>; read in order
    full = re.sub(r'\[ALP.*?\]', '', re.sub(r'\s+', ' ', ''.join(root.itertext())))
    m = re.search(r'Current through .*?effective through \w+ \d+, \d{4}\.', full)
    if m:
        return m.group(0).strip()
    m = re.search(r'Current through[^.]*\.', full)
    return m.group(0).strip() if m else 'Unknown'


def fetch_zip():
    os.makedirs(RAW, exist_ok=True)
    dest = os.path.join(RAW, 'charter.zip')
    req = urllib.request.Request(XML_URL, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    open(dest, 'wb').write(data)
    return data


def main():
    print(f"Downloading Charter XML from {XML_URL} ...")
    data = fetch_zip()
    zf = zipfile.ZipFile(io.BytesIO(data))
    names = sorted(n for n in zf.namelist()
                   if n.startswith('XML/') and n.endswith('.xml'))
    print(f"  {len(names)} XML files")
    sections, version = [], 'Unknown'
    for name in names:
        raw = zf.read(name).decode('utf-8-sig', 'replace')
        try:
            root = ET.fromstring(raw)
        except ET.ParseError as e:
            print(f"  skip {name}: {e}", file=sys.stderr)
            continue
        if name.endswith('0-0-0-1.xml'):
            version = extract_version(root)
        collect(root, 'charter', sections)
    print(f"  Indexed {len(sections)} sections. Version: {version}")
    os.makedirs(OUT, exist_ok=True)
    json.dump(sections, open(os.path.join(OUT, 'charter.json'), 'w'),
              ensure_ascii=False, indent=2)
    json.dump({'currentThrough': version, 'sectionCount': len(sections)},
              open(os.path.join(OUT, 'charter-version.json'), 'w'),
              ensure_ascii=False, indent=2)
    print("  Wrote out/charter.json + out/charter-version.json")
    return 0


if __name__ == '__main__':
    sys.exit(main())
