from typer.testing import CliRunner

from deckgen.cli import app

runner = CliRunner()


def test_outline_command(examples, tmp_path):
    r = runner.invoke(app, ["outline", str(examples / "academic-talk.md"), "-o", str(tmp_path), "-f", "pptx,html"])
    assert r.exit_code == 0, r.output
    assert (tmp_path / "academic-talk.pptx").exists() and (tmp_path / "academic-talk.html").exists()


def test_generate_offline(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    r = runner.invoke(app, ["generate", "Net zero homes", "-o", str(tmp_path), "--name", "nz"])
    assert r.exit_code == 0, r.output
    assert "offline skeleton" in r.output and (tmp_path / "nz.deck.json").exists()
    r = runner.invoke(app, ["render", str(tmp_path / "nz.deck.json"), "-o", str(tmp_path), "-t", "midnight"])
    assert r.exit_code == 0, r.output


def test_data_lint_and_themes(examples, tmp_path):
    assert runner.invoke(app, ["data", str(examples / "sales.csv"), "-o", str(tmp_path)]).exit_code == 0
    assert runner.invoke(app, ["lint", str(examples / "energy-efficient-buildings.md")]).exit_code == 0
    assert "evergreen" in runner.invoke(app, ["themes"]).output
