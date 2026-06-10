# Lebnéné — Lebanese Arabic for Work & Friends

An open-source, scenario-based Lebanese Arabic course taking a learner from
zero (knowing the alphabet) to **CEFR A2** in **16 weeks / 32 lessons**,
followed by an open-ended B1 extension track.

Designed for learners who already read the Arabic script and want **spoken
Lebanese** — not MSA — for daily life, work, and friendships in Lebanon.

## Course shape

| Module | Weeks | Lessons | Theme | Outcome |
|---|---|---|---|---|
| 1 | 1–4 | 01–08 | Foundations | Introduce yourself, order, count, survive politely |
| 2 | 5–8 | 09–16 | Daily life | Get through a normal day in Beirut without English |
| 3 | 9–12 | 17–24 | Past & future | Tell what happened, make plans, solve problems |
| 4 | 13–16 | 25–32 | Work & social | Office talk, opinions, stories, humor → **A2 exit** |

- **2 lessons/week**, 60–90 min each, ~70% speaking / 30% new material
- **Daily Anki** (decks auto-built from lesson vocab — see `scripts/`)
- **Progress tracking**: can-do checklists per module + monthly recorded
  monologues (`assessments/`)

## Repository layout

```
lessons/module-N/NN-slug.md   one lesson per file (Obsidian-friendly Markdown)
assessments/                  checklists, monologue prompts, module tests
templates/lesson-template.md  for contributors
scripts/extract_vocab.py      lesson vocab tables → CSV
scripts/build_decks.py        CSV → Anki .apkg (genanki)
audio/                        native-speaker recordings (one file per vocab row / dialogue line)
.github/workflows/deploy.yml  Quartz → GitHub Pages
```

## Using with Obsidian

Open the repo folder as a vault. Frontmatter renders as Properties.
Standard Markdown links only (no wikilinks) — see `CONTRIBUTING.md`.

## Building the Anki decks

```bash
pip install genanki
python scripts/extract_vocab.py     # writes decks/*.csv
python scripts/build_decks.py       # writes decks/*.apkg
```

## Status / wanted

- [ ] Native-speaker audio for Modules 1–4
- [ ] Native review of all dialogues (issues welcome: "this sounds Syrian!")
- [ ] B1 extension lessons (33+)

License: **CC BY-SA 4.0**
