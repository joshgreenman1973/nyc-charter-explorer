# NYC Charter Explorer

A searchable, sortable web version of the **Charter of the City of New York**, plus a clean single-file export for use with Google NotebookLM.

**Live site:** https://joshgreenman1973.github.io/nyc-charter-explorer/

## What's here

- **`index.html`** — the explorer. Full text of the Charter (770 sections, 77 chapters), full-text + title search with relevance ranking, sort by chapter / section number / length / relevance, per-chapter filtering, sticky chapter table of contents. Data is bundled in `charter-data.js`, so the page also works by double-clicking the file locally — no server required.
- **`NYC-Charter-for-NotebookLM.md`** / **`.txt`** — the entire Charter as one structured document (table of contents + every section under its chapter). ~318,000 words, under NotebookLM's 500k-word-per-source limit. Drop either file into a NotebookLM notebook as a source.
- **`build.py`** — regenerates `charter-data.json`, `charter-data.js`, and the NotebookLM files from the raw source in `data/`.

## Methodology

- **Source.** Text comes from the American Legal Publishing code library (https://codelibrary.amlegal.com/codes/newyorkcity/latest/overview), compiled via the open [BetaNYC nyc-charter-laws-rules](https://github.com/BetaNYC/nyc-charter-laws-rules) dataset (`data/index/json/charter.json`).
- **Currency.** Current through Local Law 2026/094, enacted May 16, 2026; includes amendments effective through May 17, 2026. (Source indexed 2026-05-26.)
- **Counts.** The source has 854 charter records: 84 chapter headers, 768 numbered sections, and 2 front-matter items (Preamble, Introductory). The explorer indexes the 770 text-bearing items (768 sections + 2 front-matter) grouped into the 77 chapters that contain at least one section. Eleven fully-repealed, empty chapters carry no section text and are omitted.
- **Citation fix.** The raw source truncates sub-chapter citations at the hyphen — e.g. "Chapter 18-" is shared by Chapters 18-A, 18-B, 18-C and 18-D. The canonical citation is recovered from each chapter's full heading ("Chapter 18-A: Civilian Complaint Review Board"), so sub-chapters stay distinct and sort correctly (Chapter 2 before 2-A, etc.).
- **Ordering.** Chapters and sections are ordered by their charter number, not the arbitrary order of the source index.
- **Amendment dating & spotlight.** Each section's editor's note is parsed for Local Law citations (`L.L. YYYY/NNN`). From these the explorer derives a most-recent **amendment year** (the Local Law *enactment* year), a distinct **amendment count**, and the full list of Local Laws on record. This powers the "Most recently amended" and "Most amended" sorts, the "amended since" filter, and the per-section badge. A separate "eff. YYYY" tag marks a change with a *future* effective date (parsed from calendar dates in the note) that is on record but not yet in force. 388 of 770 sections carry a Local Law note.
  - **Note — the Local Law dates above are not Charter Revision Commission attribution.** The source compiler records changes by Local Law number, not by which body originated them. The separate CRC tagging below fills that gap from official commission documents.
- **Charter Revision Commission tagging.** A separate layer (`data/crc-map.json`) tags sections changed by a *passed* ballot proposal from the 2018, 2019, 2024 and 2025 Charter Revision Commissions. This powers the "CRC" badge, the per-section proposal list, and the "revision commission" filter.
  - **How it was built.** Section lists come from each commission's official **"Proposed Charter Amendment Text"** appendix (the legal text that states "Section X … is amended/added/repealed"). Those enacting clauses were extracted programmatically and spot-verified against the source PDFs; the abstracts and ballot pamphlets contain no section numbers and were not used for the lists. Source URLs are in `data/crc-map.json`.
  - **Only passed proposals are tagged.** Proposals that failed at the ballot (2024 Q6 MWBE/modernization; 2025 Q6 even-year elections) did not change the Charter and are recorded with `passed: false` but not applied as tags. § 1152 (the Charter's effective-date/transition section) is amended by nearly every proposal.
  - **Confidence.** Section lists: high (explicit in official CRC amendment text). Pass/fail outcomes: from election results. This covers the four most recent commissions only — earlier amendments are reflected in the Local Law dating but not CRC-tagged.
- **Limitations.** This is a reformatting of a third-party compilation, not the official code. Textual errors or omissions in the source carry through. For research and informational purposes only — not legal advice. Verify against the official code before relying on any provision.
