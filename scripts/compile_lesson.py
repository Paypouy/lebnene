#!/usr/bin/env python3
"""Lint lesson files and their tutor scripts (NN-slug.tutor.yaml).

Usage:
    python scripts/compile_lesson.py lint [--lesson N] [--strict]
    python scripts/compile_lesson.py draft <lesson.md>    # YAML draft to stdout

`lint` exits 1 on errors. Unknown Arabic words in a lesson without a tutor
script are warnings unless --strict.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

VOCAB_HEADER = ["Arabic", "Translit", "Deutsch", "English", "Audio"]
STEP_TYPES = {"present", "repeat", "respond", "substitute", "translate"}

_HARAKAT = re.compile(r"[ً-ْـ]")
_AR_PUNCT = re.compile(r"[؟،!.:«»\"()?,;…]")
_PREFIXES = ("وال", "بال", "لل", "ال", "و", "ب", "ل")
_STRAY = re.compile(r"(?<!\S)[aeioué](?!\S)")
_ARABIC = re.compile(r"[؀-ۿ]")


def ar_tokens(text: str) -> list[str]:
    text = _HARAKAT.sub("", text)
    text = text.translate(str.maketrans("أإآ", "ااا"))
    text = _AR_PUNCT.sub(" ", text)
    return [t for t in re.split(r"[\s/]+", text) if t and _ARABIC.search(t)]


def is_known(token: str, lexicon: set[str]) -> bool:
    if token in lexicon:
        return True
    for prefix in _PREFIXES:
        if token.startswith(prefix) and token[len(prefix):] in lexicon:
            return True
    return False


@dataclass
class LessonDoc:
    path: Path
    number: int
    vocab_count: int | None
    vocab_header: list[str] = field(default_factory=list)
    vocab_rows: list[list[str]] = field(default_factory=list)
    dialogue_rows: list[dict] = field(default_factory=list)


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _table(body: str, heading: str) -> tuple[list[str], list[list[str]]]:
    """First table under the first `## <heading>...` section: (header, rows)."""
    m = re.search(rf"^## {heading}[^\n]*\n(.*?)(?=^## |\Z)", body, re.M | re.S)
    if not m:
        return [], []
    lines = [l for l in m.group(1).splitlines() if l.startswith("|")]
    if not lines:
        return [], []
    rows = [_cells(l) for l in lines[1:] if not re.match(r"^\|[\s\-|:]+\|$", l)]
    return _cells(lines[0]), rows


def parse_lesson(path: Path) -> LessonDoc:
    text = path.read_text(encoding="utf-8")
    number = int(re.search(r"^lesson:\s*(\d+)", text, re.M).group(1))
    vc = re.search(r"^vocab_count:\s*(\d+)", text, re.M)
    vocab_header, vocab_rows = _table(text, "Vocab")
    d_header, d_rows = _table(text, "Dialogue")
    keys = {"": "speaker", "Arabic": "ar", "Translit": "tr", "Deutsch": "de", "English": "en"}
    dialogue = [{keys.get(h, h): (row[i] if i < len(row) else "") for i, h in enumerate(d_header)} for row in d_rows]
    return LessonDoc(path, number, int(vc.group(1)) if vc else None, vocab_header, vocab_rows, dialogue)


def validate_script(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data.get("lesson"), int):
        errors.append("lesson must be an int")
    lexicon = data.get("lexicon")
    if not isinstance(lexicon, list) or not lexicon:
        errors.append("lexicon must be a non-empty list")
    else:
        for i, entry in enumerate(lexicon):
            if not all(isinstance(entry, dict) and entry.get(k) for k in ("ar", "tr", "en")):
                errors.append(f"lexicon[{i}] needs ar, tr, en")
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        return errors + ["steps must be a non-empty list"]
    seen: set[str] = set()
    for step in steps:
        sid = str(step.get("id", "?"))
        if sid in seen:
            errors.append(f"duplicate step id {sid}")
        seen.add(sid)
        kind = step.get("type")
        if kind not in STEP_TYPES:
            errors.append(f"step {sid}: unknown type {kind!r}")
            continue
        need: list[str] = []
        if kind in ("present", "repeat"):
            need = ["say"]
        elif kind == "respond":
            need = ["prompt", "expect"]
        elif kind == "substitute":
            need = ["prompt", "pattern", "items"]
        elif kind == "translate":
            direction = step.get("direction", "en-ar")
            if direction not in ("en-ar", "ar-en"):
                errors.append(f"step {sid}: unknown direction {direction!r}")
            elif direction == "ar-en":
                need = ["say", "expect"]
                if "say" in step and not (step.get("expect") or {}).get("en"):
                    errors.append(f"step {sid}: translate ar-en requires expect.en")
            else:
                need = ["prompt", "expect"]
        for key in need:
            if not step.get(key):
                label = f"translate {step.get('direction', 'en-ar')}" if kind == "translate" else kind
                errors.append(f"step {sid}: {label} requires {key}")
        if kind == "substitute" and step.get("pattern") is not None:
            if step["pattern"].count("{item}") != 1:
                errors.append(f"step {sid}: pattern needs exactly one {{item}}")
            if len(step.get("items") or []) < 3:
                errors.append(f"step {sid}: substitute needs at least 3 items")
    return errors


def draft(doc: LessonDoc) -> dict:
    """Draft script: vocab rows -> lexicon; dialogue -> present (first speaker) / respond (others)."""
    lexicon = []
    for row in doc.vocab_rows:
        ar, tr, de, en = (row + ["", "", "", ""])[:4]
        entry = {"ar": ar, "tr": tr, "en": en}
        if de:
            entry["de"] = de
        lexicon.append(entry)
    steps = []
    first = doc.dialogue_rows[0]["speaker"] if doc.dialogue_rows else ""
    for i, row in enumerate(doc.dialogue_rows, start=1):
        line = {"ar": row["ar"], "tr": row["tr"]}
        if row["speaker"] == first:
            steps.append({"id": str(i), "type": "present", "say": {**line, "en": row["en"]}})
        else:
            steps.append({"id": str(i), "type": "respond", "prompt": f"Reply as {row['speaker']}: {row['en']}", "expect": line})
    return {"lesson": doc.number, "lexicon": lexicon, "steps": steps}


def _lesson_files(root: Path) -> list[Path]:
    return sorted(p for p in root.glob("lessons/*/*.md") if not p.name.endswith(".tutor.md"))


def _script_path(md: Path) -> Path:
    return md.with_name(md.stem + ".tutor.yaml")


def _script_arabic(data: dict) -> list[str]:
    out: list[str] = []
    for step in data.get("steps") or []:
        for source in [step, *(step.get("gender_variants") or {}).values()]:
            for key in ("say", "expect"):
                value = source.get(key) or {}
                if value.get("ar"):
                    out.append(value["ar"])
    return out


def lint(root: Path, lesson: int | None, strict: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    lexicon: set[str] = set()
    for md in _lesson_files(root):
        doc = parse_lesson(md)
        tag = f"L{doc.number:02d}"
        for row in doc.vocab_rows:
            if row:
                lexicon.update(ar_tokens(row[0]))
        script = None
        sp = _script_path(md)
        if sp.exists():
            script = yaml.safe_load(sp.read_text(encoding="utf-8")) or {}
            for entry in script.get("lexicon") or []:
                if isinstance(entry, dict):
                    lexicon.update(ar_tokens(str(entry.get("ar", ""))))
        if lesson is not None and doc.number != lesson:
            continue
        if doc.vocab_count is not None and doc.vocab_count != len(doc.vocab_rows):
            errors.append(f"{tag}: vocab_count {doc.vocab_count} vs {len(doc.vocab_rows)} rows")
        if doc.vocab_header and doc.vocab_header != VOCAB_HEADER:
            errors.append(f"{tag}: vocab header {doc.vocab_header}")
        for row in doc.dialogue_rows:
            tr = row.get("tr", "")
            if _STRAY.search(tr):
                warnings.append(f"{tag}: stray space in translit {tr!r}")
        unknown_sink = errors if (script is not None or strict) else warnings
        for row in doc.dialogue_rows:
            for tok in ar_tokens(row.get("ar", "")):
                if not is_known(tok, lexicon):
                    unknown_sink.append(f"{tag}: dialogue word {tok} not in cumulative lexicon")
        if script is not None:
            errors.extend(f"{tag} script: {e}" for e in validate_script(script))
            for text in _script_arabic(script):
                for tok in ar_tokens(text):
                    if not is_known(tok, lexicon):
                        errors.append(f"{tag} script: {tok} not in cumulative lexicon")
    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_lint = sub.add_parser("lint")
    p_lint.add_argument("--lesson", type=int)
    p_lint.add_argument("--strict", action="store_true")
    p_draft = sub.add_parser("draft")
    p_draft.add_argument("lesson_md", type=Path)
    args = parser.parse_args(argv)
    if args.cmd == "draft":
        data = draft(parse_lesson(args.lesson_md))
        sys.stdout.write(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000))
        return 0
    root = Path(__file__).resolve().parent.parent
    errors, warnings = lint(root, args.lesson, args.strict)
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    print(f"{len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
