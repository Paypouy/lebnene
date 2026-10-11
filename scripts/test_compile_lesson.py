"""Tests for compile_lesson.py. Run: pytest scripts/test_compile_lesson.py -q"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from compile_lesson import ar_tokens, is_known, lint, validate_script  # noqa: E402

REPO = Path(__file__).resolve().parent.parent

VOCAB_HEADER = "| Arabic | Translit | Deutsch | English | Audio |"


def _lesson(root: Path, n: int, *, vocab_count: int, vocab: list[str], dialogue: list[str], header: str = VOCAB_HEADER) -> Path:
    path = root / "lessons" / "module-1" / f"{n:02d}-test.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows_d = "\n".join(dialogue)
    rows_v = "\n".join(vocab)
    sep = "|" + "---|" * (header.count("|") - 1)
    path.write_text(
        f"---\nlesson: {n}\nmodule: 1\nvocab_count: {vocab_count}\n---\n\n"
        f"## Dialogue\n\n| | Arabic | Translit | Deutsch | English |\n|---|---|---|---|---|\n{rows_d}\n\n"
        f"## Vocabulary\n\n{header}\n{sep}\n{rows_v}\n",
        encoding="utf-8",
    )
    return path


def test_ar_tokens_normalises():
    assert ar_tokens("أهلا وسهلا! كيفك؟") == ["اهلا", "وسهلا", "كيفك"]


def test_ar_tokens_strips_harakat_and_splits_slash():
    assert ar_tokens("تشرّفنا / منيحة") == ["تشرفنا", "منيحة"]


def test_is_known_strips_one_prefix():
    assert is_known("وانت", {"انت"}) and not is_known("كتاب", {"انت"})


def test_lint_flags_vocab_count(tmp_path):
    _lesson(tmp_path, 1, vocab_count=3, vocab=["| مرحبا | mar7aba | hallo | hello | TODO |", "| كيفك | kifak | wie | how | TODO |"],
            dialogue=["| A | مرحبا | mar7aba | Hallo | Hello |"])
    errors, _ = lint(tmp_path, None, False)
    assert any("vocab_count 3 vs 2" in e for e in errors)


def test_lint_flags_bad_header(tmp_path):
    _lesson(tmp_path, 1, vocab_count=1, vocab=["| مرحبا | mar7aba | hallo | hello |"],
            dialogue=["| A | مرحبا | mar7aba | Hallo | Hello |"], header="| Arabic | Translit | Deutsch | English |")
    errors, _ = lint(tmp_path, None, False)
    assert any("vocab header" in e for e in errors)


def test_lint_flags_stray_translit_space(tmp_path):
    _lesson(tmp_path, 1, vocab_count=1, vocab=["| مرحبا | mar7aba | hallo | hello | TODO |"],
            dialogue=["| A | مرحبا | sheft o | Hallo | Hello |"])
    _, warnings = lint(tmp_path, None, False)
    assert any("stray" in w for w in warnings)


def test_lint_unknown_token_is_warning_without_script(tmp_path):
    _lesson(tmp_path, 1, vocab_count=1, vocab=["| مرحبا | mar7aba | hallo | hello | TODO |"],
            dialogue=["| A | مرحبا كتاب | mar7aba ktéb | Hallo | Hello |"])
    errors, warnings = lint(tmp_path, None, False)
    assert any("كتاب" in w for w in warnings)
    assert not any("كتاب" in e for e in errors)


def test_lint_unknown_token_is_error_with_script(tmp_path):
    md = _lesson(tmp_path, 1, vocab_count=1, vocab=["| مرحبا | mar7aba | hallo | hello | TODO |"],
                 dialogue=["| A | مرحبا كتاب | mar7aba ktéb | Hallo | Hello |"])
    md.with_name("01-test.tutor.yaml").write_text(
        "lesson: 1\nlexicon:\n  - {ar: مرحبا, tr: mar7aba, en: hello}\n"
        "steps:\n  - {id: '1', type: present, say: {ar: مرحبا, tr: mar7aba, en: Hello}}\n",
        encoding="utf-8",
    )
    errors, _ = lint(tmp_path, None, False)
    assert any("كتاب" in e for e in errors)


def test_lint_checks_script_arabic_against_lexicon(tmp_path):
    md = _lesson(tmp_path, 1, vocab_count=1, vocab=["| مرحبا | mar7aba | hallo | hello | TODO |"],
                 dialogue=["| A | مرحبا | mar7aba | Hallo | Hello |"])
    md.with_name("01-test.tutor.yaml").write_text(
        "lesson: 1\nlexicon:\n  - {ar: مرحبا, tr: mar7aba, en: hello}\n"
        "steps:\n  - {id: '1', type: present, say: {ar: مرحبا قلم, tr: mar7aba 2alam, en: Hello pen}}\n",
        encoding="utf-8",
    )
    errors, _ = lint(tmp_path, None, False)
    assert any("قلم" in e for e in errors)


def _script(*steps):
    return {"lesson": 1, "lexicon": [{"ar": "مرحبا", "tr": "mar7aba", "en": "hello"}], "steps": list(steps)}


def test_validate_script_requires_fields():
    data = _script({"id": "1", "type": "present", "say": {"ar": "مرحبا", "tr": "mar7aba", "en": "Hello"}},
                   {"id": "2", "type": "respond", "prompt": "Say hi"})
    assert validate_script(data) == ["step 2: respond requires expect"]


def test_validate_script_substitute_needs_one_item_placeholder_and_three_items():
    bad = _script({"id": "1", "type": "substitute", "prompt": "p", "pattern": "ana esmé", "items": ["A", "B"]})
    errors = validate_script(bad)
    assert "step 1: pattern needs exactly one {item}" in errors
    assert "step 1: substitute needs at least 3 items" in errors


def test_validate_script_rejects_duplicate_ids():
    step = {"id": "1", "type": "present", "say": {"ar": "مرحبا", "tr": "mar7aba", "en": "Hello"}}
    assert "duplicate step id 1" in validate_script(_script(step, dict(step)))


def test_validate_script_translate_directions():
    ok = _script({"id": "1", "type": "translate", "prompt": "Hello", "expect": {"ar": "مرحبا", "tr": "mar7aba"}},
                 {"id": "2", "type": "translate", "direction": "ar-en", "say": {"ar": "مرحبا", "tr": "mar7aba", "en": "Hello"}, "expect": {"en": "hello"}})
    assert validate_script(ok) == []
    bad = _script({"id": "1", "type": "translate", "direction": "ar-en", "expect": {"en": "hello"}})
    assert validate_script(bad) == ["step 1: translate ar-en requires say"]


def test_ar_tokens_strips_ellipsis():
    assert ar_tokens("عم بكتب…") == ["عم", "بكتب"]


def test_draft_l01_shape():
    from compile_lesson import draft, parse_lesson

    doc = parse_lesson(REPO / "lessons" / "module-1" / "01-marhaba.md")
    data = draft(doc)

    assert len(data["lexicon"]) == len(doc.vocab_rows) >= 16
    assert [s["type"] for s in data["steps"]] == ["present", "respond"] * 5
    first_respond = data["steps"][1]
    assert first_respond["expect"]["tr"] == "mar7abtén!"
    assert first_respond["prompt"] == 'Reply as Daniel: Hello back! (lit. "two hellos")'
    assert [s["id"] for s in data["steps"]] == [str(i) for i in range(1, 11)]
    assert validate_script(data) == []


def test_lint_checks_gender_variant_arabic(tmp_path):
    md = _lesson(tmp_path, 1, vocab_count=1, vocab=["| مرحبا | mar7aba | hallo | hello | TODO |"],
                 dialogue=["| A | مرحبا | mar7aba | Hallo | Hello |"])
    md.with_name("01-test.tutor.yaml").write_text(
        "lesson: 1\nlexicon:\n  - {ar: مرحبا, tr: mar7aba, en: hello}\n"
        "steps:\n  - {id: '1', type: present, say: {ar: مرحبا, tr: mar7aba, en: Hello},"
        " gender_variants: {f: {say: {ar: مرحبا قلم, tr: x, en: y}}}}\n",
        encoding="utf-8",
    )
    errors, _ = lint(tmp_path, None, False)
    assert any("قلم" in e for e in errors)
