from pptx import Presentation

from deckgen import build
from deckgen.models import Deck, Layout, Slide
from deckgen.parsers import load_outline
from deckgen.pipeline import normalize
from deckgen.themes import list_themes, load_theme


def test_pptx_and_html_render_all_layouts(examples, tmp_path):
    deck = load_outline(examples / "energy-efficient-buildings.md")
    result = build(deck, tmp_path, ["pptx", "html", "json"])
    prs = Presentation(result.outputs["pptx"])
    assert len(prs.slides) == len(deck.slides)
    assert sum(1 for s in prs.slides for sh in s.shapes if sh.has_chart) == 4
    assert sum(1 for s in prs.slides for sh in s.shapes if sh.has_table) == 1
    assert "design order" in prs.slides[2].notes_slide.notes_text_frame.text
    html = result.outputs["html"].read_text()
    assert html.count('<section class="slide') == len(deck.slides) and "<svg" in html
    assert Deck.from_json(result.outputs["json"]).title == deck.title


def test_every_theme_renders(tmp_path):
    deck = Deck(title="T", slides=[Slide(layout=Layout.TITLE, title="T"),
                                   Slide(title="A useful title", bullets=["x"])])
    for theme in list_themes():
        assert build(deck, tmp_path, ["pptx"], theme=theme.name, name=theme.name).outputs["pptx"].exists()


def test_normalize_splits_long_slides():
    deck = Deck(title="T", slides=[Slide(title="Many points here", bullets=[str(i) for i in range(13)])])
    out = normalize(deck)
    assert [len(s.bullets) for s in out.slides] == [6, 6, 1]
    assert out.slides[1].title.endswith("(cont.)")


def test_custom_theme_file(tmp_path):
    path = tmp_path / "brand.yaml"
    path.write_text("name: brand\naccent: '#FF0000'\n")
    assert load_theme(str(path)).accent == "FF0000"
