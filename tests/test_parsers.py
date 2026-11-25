from deckgen.models import Layout
from deckgen.parsers import load_data, load_outline, parse_markdown


def test_markdown_front_matter_and_layout_inference(examples):
    deck = load_outline(examples / "energy-efficient-buildings.md")
    assert deck.title.startswith("Energy-Efficient")
    assert deck.theme == "evergreen"
    layouts = [s.layout for s in deck.slides]
    assert layouts[0] == Layout.TITLE
    assert layouts[-1] == Layout.CONCLUSION
    assert {Layout.CHART, Layout.TABLE, Layout.METRICS, Layout.TWO_COLUMN} <= set(layouts)
    pie = next(s for s in deck.slides if s.chart and s.chart.type == "pie")
    assert len(pie.chart.categories) == len(pie.chart.series[0].values) == 4
    assert pie.citation and pie.notes
    assert all(s.notes for s in deck.slides[1:])


def test_markdown_elements():
    deck = parse_markdown(
        "# My Talk\n\n## Big quote\n> Less is more\n-- Mies\n\n## Split view\n### A\n- one\n### B\n- two\n"
        "\n## Numbers\n| k | v |\n|---|---|\n| a | 1 |\n\n## Section {section}\n\n## References\n- Ref 1\n"
    )
    assert deck.title == "My Talk"
    by_title = {s.title: s for s in deck.slides}
    assert by_title["Big quote"].layout == Layout.QUOTE and by_title["Big quote"].attribution == "Mies"
    assert by_title["Split view"].layout == Layout.TWO_COLUMN and by_title["Split view"].right.bullets == ["two"]
    assert by_title["Numbers"].table.rows == [["a", "1"]]
    assert by_title["Section"].layout == Layout.SECTION
    assert by_title["References"].layout == Layout.REFERENCES


def test_yaml_outline_gets_title_slide(examples):
    deck = load_outline(examples / "outline.yaml")
    assert deck.slides[0].layout == Layout.TITLE and deck.theme == "noir"


def test_data_deck(examples):
    deck = load_data(examples / "sales.csv", title="Sales")
    charts = [s for s in deck.slides if s.layout == Layout.CHART]
    assert len(charts) == 3  # one per numeric column; mixed scales skip the comparison chart
    assert charts[0].chart.highlight == 5 and charts[0].title.startswith("Jun")
    assert deck.slides[-1].layout == Layout.CONCLUSION
