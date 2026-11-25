"""Input parsers: Markdown / YAML / JSON outlines and CSV / JSON data files."""

from __future__ import annotations

from pathlib import Path

import yaml

from deckgen.models import Deck, Layout, Slide
from deckgen.parsers.data import load_data
from deckgen.parsers.markdown import load_markdown, parse_markdown

__all__ = ["load_outline", "load_data", "load_markdown", "parse_markdown"]


def load_outline(path: str | Path) -> Deck:
    """Load a deck outline from .md, .yaml/.yml or .json (a saved deck.json)."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".md", ".markdown", ".txt"):
        return load_markdown(path)
    if suffix in (".yaml", ".yml"):
        deck = Deck.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    elif suffix == ".json":
        deck = Deck.from_json(path)
    else:
        raise ValueError(f"Unsupported outline format: {path.suffix}")
    if not deck.slides or deck.slides[0].layout != Layout.TITLE:
        deck.slides.insert(0, Slide(layout=Layout.TITLE, title=deck.title, subtitle=deck.subtitle))
    return deck
