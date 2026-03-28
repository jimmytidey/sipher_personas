#!/usr/bin/env python3
"""Build variable description CSVs from UKDA-style data dictionaries."""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# (dictionary path, output csv path(s))
DESCRIPTION_JOBS: list[tuple[Path, list[Path]]] = [
    (
        ROOT / "n_indresp_ukda_data_dictionary.txt",
        [
            ROOT / "n_indresp_description.csv",
            ROOT / "n_indesrep_description.csv",
        ],
    ),
    (
        ROOT / "xwaveid_ukda_data_dictionary.txt",
        [ROOT / "xwave_description.csv"],
    ),
]

POS_RE = re.compile(
    r"^Pos\.\s*=\s*([\d,]+)\s+Variable\s*=\s*([A-Za-z0-9_]+)\s+Variable label\s*=\s*(.*)$"
)
Q_RE = re.compile(r"^Question text = (.*)$")
VAL_RE = re.compile(r"^\s*Value\s*=\s*([^\t]+?)\s+Label\s*=\s*(.*)$")


def parse_dictionary(path: Path) -> list[dict]:
    rows: list[dict] = []
    pos = var = label = ""
    question: str | None = None
    values: list[tuple[str, str]] = []

    def flush() -> None:
        nonlocal pos, var, label, question, values
        if not var:
            return
        desc = _combine(label, question, values)
        rows.append(
            {
                "pos": pos,
                "variable": var,
                "variable_label": label,
                "question_text": question or "",
                "combined_description": desc,
            }
        )

    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            m = POS_RE.match(line)
            if m:
                flush()
                pos, var, label = m.group(1).replace(",", ""), m.group(2), m.group(3).strip()
                question = None
                values = []
                continue
            mq = Q_RE.match(line)
            if mq:
                question = mq.group(1).strip()
                continue
            mv = VAL_RE.match(line)
            if mv and var:
                values.append((mv.group(1).strip(), mv.group(2).strip()))
    flush()
    return rows


def _head(variable_label: str, question: str | None) -> str:
    if not question or not question.strip():
        return variable_label
    q = question.strip()
    v = variable_label.strip()
    if q == v or q.lower() == v.lower():
        return v
    if q.lower() in v.lower():
        return v
    return f"{v} — {q}"


def _combine(
    variable_label: str,
    question: str | None,
    value_pairs: list[tuple[str, str]],
) -> str:
    head = _head(variable_label, question)
    if value_pairs:
        codes = "; ".join(f"{code}: {lab}" for code, lab in value_pairs)
        return f"{head} — Response codes: {codes}"
    return head


def main() -> int:
    fieldnames = [
        "pos",
        "variable",
        "variable_label",
        "question_text",
        "combined_description",
    ]
    for dict_path, outs in DESCRIPTION_JOBS:
        if not dict_path.is_file():
            print(f"Skip (missing): {dict_path}", file=sys.stderr)
            continue
        rows = parse_dictionary(dict_path)
        for out in outs:
            with out.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                w.writeheader()
                w.writerows(rows)
            print(f"Wrote {len(rows)} rows to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
