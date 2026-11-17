from typer.testing import CliRunner

from deckgen.cli import app
from deckgen.models import Deck, Slide
from deckgen.notes import speaker_notes


def sample():
    return Deck(title="Rehearsal", slides=[
        Slide(title="Opening"),
        Slide(title="Café", notes="Olá!\n\nKeep this paragraph."),
        Slide(title="Closing", notes="  "),
    ])


def test_notes_preserve_numbering_and_unicode():
    text = speaker_notes(sample())
    assert "Slide 2: Café" in text
    assert "Olá!\n\nKeep this paragraph." in text
    assert "Slide 1" not in text and "Slide 3" not in text
    assert text.endswith("\n")


def test_include_empty_and_empty_deck():
    text = speaker_notes(sample(), include_empty=True)
    assert text.count("[No speaker notes]") == 2
    assert "Slide 1: Opening" in text and "Slide 3: Closing" in text
    assert "No speaker notes found." in speaker_notes(Deck(title="Empty", slides=[]))


def test_export_notes_stdout_and_nested_file(tmp_path):
    source = tmp_path / "sample.deck.json"
    sample().to_json(source)
    runner = CliRunner()
    result = runner.invoke(app, ["export-notes", str(source)])
    assert result.exit_code == 0, result.output
    assert result.output == speaker_notes(sample())
    target = tmp_path / "scripts" / "rehearsal.txt"
    result = runner.invoke(app, ["export-notes", str(source), "-o", str(target), "--include-empty"])
    assert result.exit_code == 0, result.output
    assert target.read_text(encoding="utf-8") == speaker_notes(sample(), include_empty=True)


def test_reject_input_overwrite(tmp_path):
    source = tmp_path / "sample.deck.json"
    sample().to_json(source)
    before = source.read_bytes()
    result = CliRunner().invoke(app, ["export-notes", str(source), "-o", str(source)])
    assert result.exit_code == 2
    assert source.read_bytes() == before


def test_outline_input(tmp_path):
    source = tmp_path / "talk.md"
    source.write_text("---\ntitle: Talk\n---\n## Welcome\nNotes: Hello everyone\n", encoding="utf-8")
    result = CliRunner().invoke(app, ["export-notes", str(source)])
    assert result.exit_code == 0, result.output
    assert "Hello everyone" in result.output
