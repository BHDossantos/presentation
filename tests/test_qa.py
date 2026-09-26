from deckgen.ai import skeleton_deck
from deckgen.models import Deck, Layout, Slide
from deckgen.parsers import load_outline
from deckgen.qa import lint_deck


def test_examples_are_clean(examples):
    for name in ("energy-efficient-buildings.md", "academic-talk.md"):
        assert lint_deck(load_outline(examples / name)) == []


def test_academic_rules():
    deck = Deck(title="T", style="academic", slides=[
        Slide(layout=Layout.TITLE, title="T"),
        Slide(title="Results", bullets=["a"] * 6),
        Slide(title="Thank you"),
    ])
    messages = " | ".join(str(i) for i in lint_deck(deck))
    assert "topic label" in messages and "6 bullets" in messages
    assert "References" in messages and "Thank you" in messages


def test_skeleton_flags_placeholders():
    issues = lint_deck(skeleton_deck("Heat pumps", "academic"))
    assert any("placeholder" in i.message for i in issues)
