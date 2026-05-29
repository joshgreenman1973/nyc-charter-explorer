#!/usr/bin/env python3
"""Refresh the Charter data from American Legal Publishing, then rebuild the site.

THE BATCH PROCESS (what the user asked for):
  1. refresh/fetch-charter.js  downloads the authoritative Charter bulk XML zip from
     American Legal Publishing (files.amlegal.com/.../NewYorkCity/Charter/XML.zip) —
     the same source that powers codelibrary.amlegal.com.
  2. refresh/build-charter.js  parses it with fast-xml-parser into refresh/out/charter.json,
     using BetaNYC's exact parser logic (github.com/BetaNYC/nyc-charter-laws-rules). This
     reproduces the original data byte-for-byte, so citations like "§ 197-c" stay identical
     and the Charter Revision Commission map (data/crc-map.json) keeps matching.
  3. This script copies that into data/charter.json, refreshes data/versions.json, and runs
     build.py to regenerate charter-data.json / charter-data.js / the NotebookLM files.

It prints CHANGED or UNCHANGED so a scheduler can decide whether to commit + redeploy.

  python3 refresh.py            # full refresh + rebuild
  python3 refresh.py --check    # fetch + report whether the source moved; no writes

Source of truth: American Legal Publishing. Research/informational use only — not legal advice.
"""
import os, sys, json, shutil, datetime, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RDIR = os.path.join(HERE, "refresh")
OUT = os.path.join(RDIR, "out")


def run(cmd, cwd):
    print("  $", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def ensure_node_modules():
    if not os.path.isdir(os.path.join(RDIR, "node_modules")):
        print("Installing refresh/ node dependencies (one time) ...")
        run(["npm", "install", "--silent"], RDIR)


def current_through(path):
    try:
        return json.load(open(path))["charter"]["currentThrough"]
    except Exception:
        return None


def main():
    check_only = "--check" in sys.argv
    vpath = os.path.join(DATA, "versions.json")
    old_through = current_through(vpath)

    ensure_node_modules()
    print("Fetching Charter XML from American Legal Publishing ...")
    run(["node", "fetch-charter.js"], RDIR)
    print("Parsing XML (BetaNYC fast-xml-parser logic) ...")
    run(["node", "build-charter.js"], RDIR)

    ver = json.load(open(os.path.join(OUT, "charter-version.json")))
    new_through = ver["currentThrough"]
    count = ver["sectionCount"]
    changed = new_through != old_through

    if check_only:
        print(f"\n[--check] live source: {new_through}")
        print(f"[--check] local data:  {old_through}")
        print("CHANGED" if changed else "UNCHANGED")
        return 0

    # Sanity guard: never let a broken fetch wipe the dataset.
    if count < 800:
        print(f"ABORT: only {count} sections parsed (expected ~854). "
              "Source fetch looks broken; leaving existing data untouched.",
              file=sys.stderr)
        return 2

    shutil.copyfile(os.path.join(OUT, "charter.json"), os.path.join(DATA, "charter.json"))
    versions = json.load(open(vpath)) if os.path.exists(vpath) else {}
    versions["charter"] = {
        "currentThrough": new_through,
        "indexedAt": datetime.datetime.now(datetime.timezone.utc)
            .isoformat().replace("+00:00", "Z"),
        "sectionCount": count,
    }
    json.dump(versions, open(vpath, "w"), ensure_ascii=False, indent=2)
    print("Updated data/charter.json + data/versions.json")

    print("Rebuilding site (build.py) ...")
    run([sys.executable, "build.py"], HERE)

    print(f"\nDONE. {'CHANGED' if changed else 'UNCHANGED'}")
    print(f"  was: {old_through!r}")
    print(f"  now: {new_through!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
