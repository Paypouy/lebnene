#!/usr/bin/env python3
"""Build Anki .apkg decks from decks/module-N.csv (run extract_vocab.py first).

Card 1: Arabic -> Translit + DE + EN (+ audio if present)
Card 2: DE -> Arabic + Translit  (production direction)

Usage: pip install genanki && python scripts/build_decks.py
"""
import csv
import hashlib
from pathlib import Path

import genanki

ROOT = Path(__file__).resolve().parent.parent
DECKS = ROOT / "decks"
AUDIO = ROOT / "audio"


def stable_id(name: str) -> int:
    return int(hashlib.sha1(name.encode()).hexdigest()[:10], 16)


MODEL = genanki.Model(
    stable_id("lebnene-vocab-model"),
    "Lebnene Vocab",
    fields=[
        {"name": "Arabic"},
        {"name": "Translit"},
        {"name": "Deutsch"},
        {"name": "English"},
        {"name": "Audio"},
        {"name": "Lesson"},
    ],
    templates=[
        {
            "name": "Recognition (AR -> DE)",
            "qfmt": '<div style="font-size:48px;direction:rtl">{{Arabic}}</div>{{Audio}}',
            "afmt": '{{FrontSide}}<hr id="answer">'
                    '<div style="font-size:24px">{{Translit}}</div>'
                    "<div>{{Deutsch}} · {{English}}</div>"
                    '<div style="color:#888">Lektion {{Lesson}}</div>',
        },
        {
            "name": "Production (DE -> AR)",
            "qfmt": '<div style="font-size:28px">{{Deutsch}}</div>',
            "afmt": '{{FrontSide}}<hr id="answer">'
                    '<div style="font-size:48px;direction:rtl">{{Arabic}}</div>'
                    '<div style="font-size:24px">{{Translit}}</div>{{Audio}}',
        },
    ],
    css=".card { font-family: system-ui; text-align: center; }",
)


def build(csv_path: Path) -> None:
    deck_name = f"Lebnéné::{csv_path.stem}"
    deck = genanki.Deck(stable_id(deck_name), deck_name)
    media = []
    with csv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            audio_field = ""
            audio_name = row["audio"].strip()
            if audio_name and audio_name.upper() != "TODO":
                audio_path = AUDIO / audio_name
                if audio_path.exists():
                    media.append(str(audio_path))
                    audio_field = f"[sound:{audio_name}]"
            deck.add_note(
                genanki.Note(
                    model=MODEL,
                    fields=[
                        row["arabic"], row["translit"], row["deutsch"],
                        row["english"], audio_field, row["lesson"],
                    ],
                    guid=genanki.guid_for(row["arabic"], row["deutsch"]),
                )
            )
    pkg = genanki.Package(deck)
    pkg.media_files = media
    out = DECKS / f"{csv_path.stem}.apkg"
    pkg.write_to_file(out)
    print(f"{out.relative_to(ROOT)} ({len(deck.notes)} notes, {len(media)} audio)")


def main() -> None:
    csvs = sorted(DECKS.glob("module-*.csv"))
    if not csvs:
        raise SystemExit("No CSVs found — run scripts/extract_vocab.py first.")
    for c in csvs:
        build(c)


if __name__ == "__main__":
    main()
