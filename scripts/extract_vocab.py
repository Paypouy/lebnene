#!/usr/bin/env python3
"""Extract vocabulary tables from lesson Markdown files into per-module CSVs.

Parses every table whose header matches the vocab contract:
    | Arabic | Translit | Deutsch | English | Audio |
and writes decks/module-N.csv plus decks/all.csv.

Usage: python scripts/extract_vocab.py
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSONS = ROOT / "lessons"
DECKS = ROOT / "decks"

HEADER_RE = re.compile(
    r"^\|\s*Arabic\s*\|\s*Translit\s*\|\s*Deutsch\s*\|\s*English\s*\|\s*Audio\s*\|\s*$",
    re.IGNORECASE,
)
ROW_RE = re.compile(r"^\|(.+)\|\s*$")
SEPARATOR_RE = re.compile(r"^\|[\s\-:|]+\|\s*$")


def parse_lesson(path: Path):
    """Yield (arabic, translit, deutsch, english, audio) rows from one file."""
    lesson_id = path.stem.split("-")[0]  # "01" from "01-marhaba.md"
    in_table = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if HEADER_RE.match(line):
            in_table = True
            continue
        if in_table:
            if SEPARATOR_RE.match(line):
                continue
            m = ROW_RE.match(line)
            if not m:
                in_table = False
                continue
            cells = [c.strip() for c in m.group(1).split("|")]
            if len(cells) != 5 or not cells[0]:
                continue
            yield lesson_id, *cells


def main() -> int:
    DECKS.mkdir(exist_ok=True)
    all_rows = []
    for module_dir in sorted(LESSONS.glob("module-*")):
        rows = []
        for lesson in sorted(module_dir.glob("*.md")):
            rows.extend(parse_lesson(lesson))
        out = DECKS / f"{module_dir.name}.csv"
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["lesson", "arabic", "translit", "deutsch", "english", "audio"])
            w.writerows(rows)
        print(f"{out.relative_to(ROOT)}: {len(rows)} cards")
        all_rows.extend(rows)
    with (DECKS / "all.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["lesson", "arabic", "translit", "deutsch", "english", "audio"])
        w.writerows(all_rows)
    print(f"decks/all.csv: {len(all_rows)} cards total")
    if not all_rows:
        print("ERROR: no vocab rows found — header contract broken?", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
