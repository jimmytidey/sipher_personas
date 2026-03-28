#!/usr/bin/env python3
"""One-off: enrich n_indresp_ukda_data_dictionary.txt with question text from W18 PDF."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from pypdf import PdfReader

PDF_PATH = Path(__file__).resolve().parent / "6614-main-survey-questionnaire-w18.pdf"
DICT_PATH = Path(__file__).resolve().parent / "n_indresp_ukda_data_dictionary.txt"
REPORT_PATH = Path(__file__).resolve().parent / "n_indresp_question_text_report.txt"

QUESTION_START = re.compile(
    r"Question:\s*([\w_]+)\.\s*\n\s*([A-Z0-9_]+)",
    re.MULTILINE,
)


def extract_pdf_text() -> str:
    r = PdfReader(str(PDF_PATH))
    return "\n".join((p.extract_text() or "") for p in r.pages)


def clean_template(s: str) -> str:
    s = re.sub(r"\{[^}]*\}", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def segment_question_blocks(full: str) -> list[tuple[str, str, str]]:
    """Return list of (module, var_upper, segment_text)."""
    matches = list(QUESTION_START.finditer(full))
    out: list[tuple[str, str, str]] = []
    for i, m in enumerate(matches):
        mod, var = m.group(1), m.group(2)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full)
        seg = full[start:end]
        out.append((mod, var, seg))
    return out


def wording_from_segment(seg: str) -> tuple[str | None, str]:
    """
    Return (primary wording, source) where source is 'text', 'bracket', or 'box_label'.
    """
    # Bracket description right after var name line
    m_br = re.search(r"^\s*\[\s*([^\]]+?)\s*\]", seg, re.MULTILINE)
    bracket = m_br.group(1).strip() if m_br else None

    # First main Text: (not "Text" alone on a line for validation)
    m_txt = re.search(
        r"(?<!\w)Text:\s*\n(.+?)(?=\n\s*\nQuestion\nBox|\n\n(?:Question:|Options:|Use:\s|Hard Check:|Soft Check:|Scripting\s*Notes:|Module:|Source:|\Z))",
        seg,
        re.DOTALL | re.IGNORECASE,
    )
    if m_txt:
        t = clean_template(m_txt.group(1))
        if t:
            return t, "text"

    # Question Box Label (e.g. Month / Year when shared Text is on another part)
    m_box = re.search(
        r"Question\s*\n\s*Box\s*\n\s*Label:\s*\n\s*([^\n]+)",
        seg,
        re.IGNORECASE,
    )
    if m_box:
        lab = clean_template(m_box.group(1))
        if lab and bracket:
            return f"{bracket} ({lab})", "box_label"
        if lab:
            return lab, "box_label"

    if bracket:
        return bracket, "bracket"

    return None, "none"


def build_var_map(full: str) -> dict[str, tuple[str, str, str]]:
    """
    Map lowercase var name (without n_) -> (wording, source, module).
    Last occurrence wins (log duplicates).
    """
    mp: dict[str, tuple[str, str, str]] = {}
    dups: list[tuple[str, str]] = []
    for mod, var, seg in segment_question_blocks(full):
        w, src = wording_from_segment(seg)
        if not w:
            continue
        key = var.lower()
        if key in mp:
            dups.append((key, mod))
        mp[key] = (w, src, mod)

    # Multi-part questions: only the first field has Text:; later parts use Question Box only.
    dob_intro = mp.get("chkwebdobd")
    if dob_intro and dob_intro[1] == "text":
        base = dob_intro[0]
        mod0 = dob_intro[2]
        for part_key, part_label in (
            ("chkwebdobm", "Month"),
            ("chkwebdoby", "Year"),
        ):
            if part_key in mp:
                w, src, m = mp[part_key]
                if src in ("box_label", "bracket") and m == mod0:
                    mp[part_key] = (f"{base} ({part_label})", "shared_multipart", mod0)

    return mp, dups


POS_LINE = re.compile(
    r"^Pos\.\s*=\s*[\d,]+\s+Variable\s*=\s*([A-Za-z0-9_]+)\s+Variable label\s*=\s*(.*)$"
)

# Data file sometimes uses suffixed names for a second pass of the same question.
STEM_ALIASES: dict[str, str] = {
    "chkwebdobm2": "chkwebdobm",
    "chkwebdoby2": "chkwebdoby",
}


def main() -> int:
    print("Extracting PDF (may take ~1 min)...", flush=True)
    full = extract_pdf_text()
    mp, dups = build_var_map(full)
    print(f"PDF chars: {len(full)}, question blocks: {len(list(QUESTION_START.finditer(full)))}")
    print(f"Mapped questionnaire vars with wording: {len(mp)}, duplicate keys: {len(dups)}")

    lines = DICT_PATH.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    out: list[str] = []
    missing: list[str] = []
    matched = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        m = POS_LINE.match(line.rstrip("\n"))
        out.append(line)
        if m:
            varname = m.group(1)
            stem = (varname[2:] if varname.startswith("n_") else varname).lower()
            lookup = STEM_ALIASES.get(stem, stem)
            if i + 1 < len(lines) and lines[i + 1].startswith("Question text ="):
                pass  # already enriched
            elif lookup in mp:
                w, src, mod = mp[lookup]
                out.append(f"Question text = {w}\n")
                matched += 1
            else:
                missing.append(
                    f"{varname}\t{m.group(2).strip()}"
                )
        i += 1

    backup = DICT_PATH.with_suffix(".txt.bak_before_question_text")
    if not backup.exists():
        backup.write_text("".join(lines), encoding="utf-8")

    DICT_PATH.write_text("".join(out), encoding="utf-8")

    report_lines = [
        "Variables with no matching questionnaire question text in the Wave 18 PDF.\n",
        "(Derived, admin, grid aggregates, and renamed fields often have no verbatim question.)\n",
        f"Total dictionary variables (Pos. lines): {sum(1 for ln in lines if POS_LINE.match(ln.rstrip(chr(10)+chr(13))))}\n",
        f"Matched from PDF: {matched}\n",
        f"Not found in PDF: {len(missing)}\n",
        "\n",
    ]
    if dups:
        report_lines.append("Duplicate questionnaire variable keys (last module kept):\n")
        for k, mod in dups[:50]:
            report_lines.append(f"  {k} ({mod})\n")
        if len(dups) > 50:
            report_lines.append(f"  ... and {len(dups) - 50} more\n")
        report_lines.append("\n")

    report_lines.append("variable\tvariable_label\n")
    report_lines.extend(m + "\n" for m in missing)

    REPORT_PATH.write_text("".join(report_lines), encoding="utf-8")

    print(f"Wrote {DICT_PATH}")
    print(f"Backup (first run only): {backup}")
    print(f"Report: {REPORT_PATH}")
    print(f"Matched: {matched}, missing: {len(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
