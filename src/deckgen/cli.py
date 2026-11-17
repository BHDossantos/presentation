"""Command line interface: ``deckgen --help``."""

from __future__ import annotations

from pathlib import Path

import typer
import yaml

from deckgen.ai import GenerationError, generate_deck, has_credentials, skeleton_deck
from deckgen.models import Deck
from deckgen.notes import speaker_notes
from deckgen.parsers import load_data, load_outline
from deckgen.pipeline import FORMATS, BuildResult, build
from deckgen.qa import lint_deck
from deckgen.themes import list_themes

app = typer.Typer(add_completion=False, no_args_is_help=True,
                  help="Generate presentations automatically: topic, outline or data in -> PPTX / HTML / PDF out.")

FormatOpt = typer.Option("pptx,html,json", "--format", "-f", help=f"Comma list of: {', '.join(FORMATS)}")
OutOpt = typer.Option(Path("out"), "--out", "-o", help="Output directory")
ThemeOpt = typer.Option(None, "--theme", "-t", help="Built-in theme name or path to a theme YAML")
NameOpt = typer.Option(None, "--name", help="Output file stem (default: slug of the title)")
StyleOpt = typer.Option("business", "--style", "-s", help="business | academic")


def _formats(value: str) -> list[str]:
    return [f.strip().lower() for f in value.split(",") if f.strip()]


def _report(result: BuildResult) -> None:
    for kind, path in result.outputs.items():
        typer.echo(f"  {kind:5} -> {path}")
    for w in result.warnings:
        typer.secho(f"  ! {w}", fg=typer.colors.YELLOW)
    issues = lint_deck(result.deck)
    if issues:
        typer.secho(f"  {len(issues)} QA note(s); run `deckgen lint` on the .deck.json for details",
                    fg=typer.colors.YELLOW)


def _build(deck: Deck, out: Path, fmt: str, theme: str | None, name: str | None) -> BuildResult:
    result = build(deck, out, _formats(fmt), theme, name)
    typer.secho(f"Built '{result.deck.title}' ({len(result.deck.slides)} slides)", fg=typer.colors.GREEN)
    _report(result)
    return result


@app.command()
def generate(
    topic: str = typer.Argument(..., help="What the presentation is about"),
    slides: int = typer.Option(10, "--slides", "-n", min=3, max=40),
    style: str = StyleOpt,
    audience: str | None = typer.Option(None, "--audience", "-a"),
    tone: str | None = typer.Option(None, "--tone"),
    language: str | None = typer.Option(None, "--language", "-l"),
    context: Path | None = typer.Option(None, "--context", "-c", help="Text/Markdown file with source material"),
    model: str | None = typer.Option(None, "--model", help="Claude model (default: $DECKGEN_MODEL or claude-opus-5)"),
    effort: str = typer.Option("high", "--effort", help="low | medium | high | xhigh | max"),
    offline: bool = typer.Option(False, "--offline", help="Skip the API; emit an editable skeleton"),
    out: Path = OutOpt, fmt: str = FormatOpt, theme: str | None = ThemeOpt, name: str | None = NameOpt,
) -> None:
    """Write a full deck about TOPIC with Claude (falls back to a skeleton without an API key)."""
    if offline or not has_credentials():
        if not offline:
            typer.secho("No ANTHROPIC_API_KEY set: generating an offline skeleton deck instead.",
                        fg=typer.colors.YELLOW)
        deck = skeleton_deck(topic, style, audience)
    else:
        typer.echo(f"Asking Claude to write a {slides}-slide {style} deck...")
        try:
            deck = generate_deck(topic, slides=slides, style=style, audience=audience, tone=tone,
                                 context=context.read_text(encoding="utf-8") if context else None,
                                 language=language, model=model, effort=effort)
        except GenerationError as exc:
            typer.secho(f"Generation failed: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1) from exc
    _build(deck, out, fmt, theme, name)


@app.command()
def outline(path: Path = typer.Argument(..., exists=True, help=".md, .yaml or .deck.json outline"),
            out: Path = OutOpt, fmt: str = FormatOpt, theme: str | None = ThemeOpt,
            name: str | None = NameOpt, style: str | None = typer.Option(None, "--style", "-s")) -> None:
    """Build a deck from a Markdown / YAML / JSON outline (no API key needed)."""
    deck = load_outline(path)
    if style:
        deck.style = style  # type: ignore[assignment]
    _build(deck, out, fmt, theme, name or path.name.split(".")[0])


@app.command()
def render(path: Path = typer.Argument(..., exists=True, help="A .deck.json file (e.g. edited AI output)"),
           out: Path = OutOpt, fmt: str = typer.Option("pptx,html", "--format", "-f"),
           theme: str | None = ThemeOpt, name: str | None = NameOpt) -> None:
    """Re-render a saved deck.json, e.g. after editing it or to try another theme."""
    _build(Deck.from_json(path), out, fmt, theme, name or path.name.split(".")[0])


@app.command()
def data(path: Path = typer.Argument(..., exists=True, help="CSV or JSON rows; first column = labels"),
         title: str | None = typer.Option(None, "--title"), subtitle: str | None = typer.Option(None, "--subtitle"),
         style: str = StyleOpt, out: Path = OutOpt, fmt: str = FormatOpt, theme: str | None = ThemeOpt,
         name: str | None = NameOpt) -> None:
    """Turn a data file into a report deck: KPIs, highlighted charts, table and takeaways."""
    _build(load_data(path, title, subtitle, style), out, fmt, theme, name)


@app.command()
def batch(path: Path = typer.Argument(..., exists=True, help="YAML file with a `jobs:` list"),
          out: Path = OutOpt) -> None:
    """Build many decks from one YAML job file (good for cron / CI automation)."""
    spec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    base = path.parent
    failures = 0
    for job in spec.get("jobs", []):
        kind = job.get("type", "outline")
        opts = dict(out_dir=out / job.get("out", ""), formats=_formats(job.get("format", "pptx,html")),
                    theme=job.get("theme"), name=job.get("name"))
        try:
            if kind == "outline":
                deck = load_outline(base / job["input"])
            elif kind == "data":
                deck = load_data(base / job["input"], job.get("title"), job.get("subtitle"),
                                 job.get("style", "business"))
            elif kind == "generate":
                style = job.get("style", "business")
                deck = (generate_deck(job["topic"], slides=job.get("slides", 10), style=style,
                                      audience=job.get("audience"), tone=job.get("tone"))
                        if has_credentials() else skeleton_deck(job["topic"], style, job.get("audience")))
            else:
                raise ValueError(f"unknown job type '{kind}'")
            result = build(deck, **opts)
            typer.secho(f"[ok] {deck.title}", fg=typer.colors.GREEN)
            _report(result)
        except Exception as exc:  # noqa: BLE001 - keep going, report at the end
            failures += 1
            typer.secho(f"[failed] {job}: {exc}", fg=typer.colors.RED, err=True)
    if failures:
        raise typer.Exit(1)


@app.command()
def lint(path: Path = typer.Argument(..., exists=True, help="Outline or .deck.json"),
         strict: bool = typer.Option(False, "--strict", help="Exit non-zero on warnings too")) -> None:
    """Check a deck against presentation best practices (action titles, word limits, references...)."""
    deck = load_outline(path)
    typer.echo("Ghost deck (titles only; should tell the whole story):")
    for i, title in enumerate(deck.ghost_deck(), start=1):
        typer.echo(f"  {i:2}. {title}")
    issues = lint_deck(deck)
    for issue in issues:
        typer.secho(f"  {issue}", fg=typer.colors.RED if issue.level == "error" else typer.colors.YELLOW)
    if not issues:
        typer.secho("No issues found.", fg=typer.colors.GREEN)
    if any(i.level == "error" for i in issues) or (strict and issues):
        raise typer.Exit(1)


@app.command()
def thumbnails(pptx: Path = typer.Argument(..., exists=True), out: Path | None = typer.Option(None, "--out", "-o"),
               cols: int = typer.Option(3, "--cols")) -> None:
    """Render slide PNGs + a contact sheet for visual QA (needs LibreOffice and `deckgen[qa]`)."""
    from deckgen.renderers.pdf import contact_sheet, pdf_to_images, pptx_to_pdf

    out = out or pptx.with_suffix("")
    pdf = pptx_to_pdf(pptx, out)
    images = pdf_to_images(pdf, out)
    sheet = contact_sheet(images, out / "contact-sheet.png", cols=cols)
    typer.echo(f"{len(images)} slide images in {out}; contact sheet: {sheet}")


@app.command("export-notes")
def export_notes(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, help="Outline or .deck.json"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Text file; omit to print to stdout"),
    include_empty: bool = typer.Option(False, "--include-empty", help="Include slides without notes"),
) -> None:
    """Export a rehearsal script with slide numbers and titles, without an API or PDF tools."""
    if output and output.resolve() == path.resolve():
        raise typer.BadParameter("Output must differ from the input file.", param_hint="--output")
    deck = Deck.from_json(path) if path.suffix.lower() == ".json" else load_outline(path)
    text = speaker_notes(deck, include_empty=include_empty)
    if output is None:
        typer.echo(text, nl=False)
        return
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    except OSError as exc:
        typer.secho(f"Cannot write notes: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Speaker notes -> {output}")


@app.command()
def themes() -> None:
    """List built-in themes."""
    for t in list_themes():
        typer.echo(f"  {t.name:11} {t.description}")


if __name__ == "__main__":  # pragma: no cover
    app()
