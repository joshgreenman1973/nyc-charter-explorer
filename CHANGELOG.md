# Changelog

Record of when the Charter data in this explorer changed, kept by `refresh.py`. A refresh is logged here only when American Legal Publishing's `currentThrough` version string advances. Section-level notes compare the new data against the prior copy by record id.

## 2026-06-02

- **Text-extraction fix (not Charter amendments).** Switched to a parser that preserves document order. The previous parser (fast-xml-parser) appended inline `<LINK>` cross-reference elements after the surrounding text, reordering spelled-out section numbers to the end of a sentence — e.g. "the provisions of sections 277 and 278 of the charter" had been mangled to "the provisions of sections and of the charter … two hundred seventy-seven two hundred seventy-eight." This affected 151 sections (now 0) and corrected text in ~565 sections. Also added a missing space after subdivision markers ("a.any" -> "a. any"). No section was added, removed or re-cited; the Charter Revision Commission tags are unaffected.
- Currency: `Current through Local Law 2026/094, enacted May 16, 2026,and includes amendments effective through May 27, 2026.` -> `Current through Local Law 2026/094, enacted May 16, 2026,and includes amendments effective through May 28, 2026.`

## 2026-05-29

- Currency: `Current through Local Law 2026/094, enacted May 16, 2026,and includes amendments effective through May 17, 2026.` -> `Current through Local Law 2026/094, enacted May 16, 2026,and includes amendments effective through May 27, 2026.`
- No section text changed (currency/effective-date update only). The effective-through date advanced from May 17 to May 27, 2026; Local Law 2026/094 remained the current version. Independently corroborated by the BetaNYC nyc-charter-laws-rules changelog for the same date.

## 2026-05-28

- Initial build. Current through Local Law 2026/094, enacted May 16, 2026, including amendments effective through May 17, 2026. 854 source records (770 text-bearing sections across 77 chapters). Source: American Legal Publishing bulk XML via the BetaNYC parser.
