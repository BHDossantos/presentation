"""Deck -> normalized Deck -> files. Shared by the CLI, batch runs and the Python API."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from deckgen.models import Deck, Layout, Slide
from deckgen.renderers.html_renderer import render_html
from deckgen.renderers.pdf import pptx_to_pdf
from deckgen.renderers.pptx_renderer import render_pptx
from deckgen.themes import load_theme

FORMATS = ("pptx", "html", "pdf", "json")


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "deck"


def normalize(deck: Deck) -> Deck:
    """Split overlong bullet slides into continuation slides so nothing overflows."""
    limit = 5 if deck.style == "academic" else 6
    out: list[Slide] = []
    for s in deck.slides:
        splittable = s.layout in (Layout.BULLETS, Layout.CONCLUSION) and len(s.bullets) > limit
        if not splittable:
            out.append(s)
            continue
        chunks = [s.bullets[i:i + limit] for i in range(0, len(s.bullets), limit)]
        for n, chunk in enumerate(chunks):
            title = s.title if n == 0 else f"{s.title} (cont.)"
            out.append(s.model_copy(update={"title": title, "bullets": chunk,
                                            "notes": s.notes if n == 0 else None}))
    return deck.model_copy(update={"slides": out})


@dataclass
class BuildResult:
    deck: Deck
    outputs: dict[str, Path] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def build(deck: Deck, out_dir: str | Path = "out", formats: tuple[str, ...] | list[str] = ("pptx", "html"),
          theme: str | None = None, name: str | None = None) -> BuildResult:
    unknown = set(formats) - set(FORMATS)
    if unknown:
        raise ValueError(f"Unknown format(s): {', '.join(sorted(unknown))}. Choose from {', '.join(FORMATS)}")
    deck = normalize(deck)
    theme_obj = load_theme(theme or deck.theme, deck.style)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = name or slugify(deck.title)
    result = BuildResult(deck=deck)
    if "json" in formats:
        result.outputs["json"] = deck.to_json(out_dir / f"{stem}.deck.json")
    if "pptx" in formats or "pdf" in formats:
        result.outputs["pptx"] = render_pptx(deck, theme_obj, out_dir / f"{stem}.pptx")
    if "html" in formats:
        result.outputs["html"] = render_html(deck, theme_obj, out_dir / f"{stem}.html")
    if "pdf" in formats:
        try:
            result.outputs["pdf"] = pptx_to_pdf(result.outputs["pptx"], out_dir)
        except Exception as exc:  # noqa: BLE001 - PDF is best-effort; report and keep other outputs
            result.warnings.append(f"PDF export skipped: {exc}")
    return result
