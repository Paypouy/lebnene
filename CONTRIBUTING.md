# Contributing

## The one rule that matters: orthography

Lebanese has no standard spelling. This course picks ONE convention and never
deviates. PRs that break it will be asked to fix it.

### Arabic script (primary)
- Write as pronounced in Beirut Lebanese, not MSA: شو، هيك، هلّق، بدّي، منيح
- ق is written ق even when pronounced as hamze (قلب, pronounced *2alb*)
- Feminine ending: ة (دكّانة). Final imala is NOT marked in script.
- No case endings, ever. No شدّة except where it changes meaning (بدّي).

### Transliteration (always given on first occurrence, and in vocab tables)
Lebanese chat alphabet ("arabizi"), because it's what his Lebanese friends
will actually text him:

| Sound | Symbol | Example |
|---|---|---|
| ء / ق (urban) | 2 | 2alb (heart), 2ahwé (coffee) |
| ع | 3 | 3arabé (Arabic) |
| ح | 7 | 7elo (nice) |
| خ | kh | khalas |
| غ | gh | ghali (expensive) |
| ش | sh | shu |
| ج | j (French j) | jdid |
| imala (é like German "ee" in "See", short) | é | bét (house), lebnéné |
| long a | a / é per pronunciation | ktab vs. kén |

- Stress is not marked. Audio is the reference, not the spelling.
- German umlaut comparisons are welcome in notes (é ≈ "ee" in *Beet*).

## Lesson format

Copy `templates/lesson-template.md`. Every lesson MUST have: frontmatter,
dialogue (script + translit + DE + EN), vocab table (same 5 columns, the
extraction script parses it), one grammar point max, 3+ drills, role-play
variations, an assignment.

## Vocab table contract (parsed by scripts/extract_vocab.py)

```
| Arabic | Translit | Deutsch | English | Audio |
```
Audio column = filename in `audio/` or `TODO`.

## Links
Standard Markdown links with relative paths only — no `[[wikilinks]]`,
no `![[embeds]]` — so files render on GitHub and build in any generator.
(Obsidian: Settings → Files & Links → turn OFF "Use [[Wikilinks]]".)

## What we need most
1. Native-speaker review (open an issue per phrase, cite the lesson)
2. Audio recordings (48kHz mono, one file per vocab row: `l03-v07.mp3`)
3. New B1 scenarios using the template
