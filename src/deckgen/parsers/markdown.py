"""Markdown outline -> Deck.

Format (see ``examples/outline.md``)::

    ---
    title: Deck title            # YAML front matter -> Deck fields
    author: Jane Doe
    style: business | academic
    theme: corporate
    ---
    # Section divider
    ## Slide title  {conclusion}   # optional {layout} override
    Subtitle: small line under the title
    - bullet
    ### Left column heading        # two ### headings -> two_column
    > A quote
    -- Attribution
    Image: path/to/picture.png
    Source: (Author, 2024)         # citation footer
    Notes: speaker notes ... (until next heading)
    ```chart   (YAML ChartSpec)   ```table (YAML or pipe table)   ```metrics (YAML list)
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from deckgen.models import ChartSpec, Column, Deck, Layout, Metric, Slide, TableSpec

HEADING_LAYOUT = re.compile(r"^(?P<title>.*?)\s*\{\.?(?P<layout>[a-z_]+)\}\s*$")
BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?P<text>.+)$")
KEYED = re.compile(r"^(?P<key>subtitle|source|notes|image|citation)\s*:\s*(?P<value>.*)$", re.I)


def _split_front_matter(text: str) -> tuple[dict, str]:
    if text.startswith("---"):
        parts = text.split("\n---", 1)
        if len(parts) == 2:
            meta = yaml.safe_load(parts[0][3:]) or {}
            return meta, parts[1].split("\n", 1)[1] if "\n" in parts[1] else ""
    return {}, text


def _parse_pipe_table(lines: list[str]) -> TableSpec:
    rows = [[c.strip() for c in line.strip().strip("|").split("|")] for line in lines if line.strip()]
    rows = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
    return TableSpec(headers=rows[0], rows=rows[1:])


class _SlideBuilder:
    def __init__(self, title: str, layout: str | None):
        self.slide = Slide(title=title, layout=Layout(layout) if layout else Layout.BULLETS)
        self.explicit = layout is not None
        self.columns: list[Column] = []
        self.notes: list[str] = []
        self.in_notes = False

    def finish(self) -> Slide:
        s = self.slide
        if self.columns:
            if len(self.columns) >= 2:
                s.left, s.right = self.columns[0], self.columns[1]
            elif not s.bullets:
                s.bullets = self.columns[0].bullets
        if self.notes:
            s.notes = "\n".join(self.notes).strip() or None
        if not self.explicit:
            if s.chart:
                s.layout = Layout.CHART
            elif s.table:
                s.layout = Layout.TABLE
            elif s.metrics:
                s.layout = Layout.METRICS
            elif s.quote:
                s.layout = Layout.QUOTE
            elif s.image:
                s.layout = Layout.IMAGE
            elif s.left and s.right:
                s.layout = Layout.TWO_COLUMN
            elif re.search(r"\b(references|bibliography|sources)\b", s.title, re.I):
                s.layout = Layout.REFERENCES
        return s


def parse_markdown(text: str) -> Deck:
    meta, body = _split_front_matter(text)
    slides: list[Slide] = []
    current: _SlideBuilder | None = None
    lines = body.splitlines()
    i = 0

    def flush():
        nonlocal current
        if current is not None:
            slides.append(current.finish())
            current = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        i += 1
        if stripped.startswith("```"):
            kind = stripped[3:].strip().lower()
            block: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            if current is None:
                continue
            raw = "\n".join(block)
            if kind == "chart":
                current.slide.chart = ChartSpec.model_validate(yaml.safe_load(raw))
            elif kind == "table":
                if raw.lstrip().startswith("|"):
                    current.slide.table = _parse_pipe_table(block)
                else:
                    current.slide.table = TableSpec.model_validate(yaml.safe_load(raw))
            elif kind == "metrics":
                current.slide.metrics = [Metric.model_validate(m) for m in yaml.safe_load(raw)]
            continue
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            heading = stripped[level:].strip()
            if level <= 2:
                flush()
                m = HEADING_LAYOUT.match(heading)
                title, layout = (m["title"], m["layout"]) if m else (heading, None)
                if level == 1 and not layout:
                    if not meta.get("title") and not slides:
                        meta["title"] = title
                        continue
                    layout = "section"
                current = _SlideBuilder(title, layout)
            elif current is not None:
                current.in_notes = False
                current.columns.append(Column(heading=heading))
            continue
        if current is None:
            continue
        if current.in_notes:
            current.notes.append(line)
            continue
        if not stripped:
            continue
        keyed = KEYED.match(stripped)
        if keyed:
            key, value = keyed["key"].lower(), keyed["value"].strip()
            if key == "subtitle":
                current.slide.subtitle = value
            elif key in ("source", "citation"):
                current.slide.citation = value
            elif key == "image":
                current.slide.image = value
            elif key == "notes":
                current.in_notes = True
                if value:
                    current.notes.append(value)
            continue
        if stripped.startswith("|") and current.slide.table is None:
            block = [stripped]
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i].strip())
                i += 1
            current.slide.table = _parse_pipe_table(block)
            continue
        if stripped.startswith(">"):
            q = stripped.lstrip("> ").strip()
            current.slide.quote = f"{current.slide.quote} {q}".strip() if current.slide.quote else q
            continue
        if stripped.startswith(("--", "—")) and current.slide.quote:
            current.slide.attribution = stripped.lstrip("-— ").strip()
            continue
        bullet = BULLET.match(line)
        text_value = bullet["text"].strip() if bullet else stripped
        if current.columns:
            current.columns[-1].bullets.append(text_value)
        else:
            current.slide.bullets.append(text_value)
    flush()

    title = meta.pop("title", None) or (slides[0].title if slides else "Untitled deck")
    deck_fields = {k: meta[k] for k in ("subtitle", "author", "date", "style", "theme") if meta.get(k)}
    if "date" in deck_fields:
        deck_fields["date"] = str(deck_fields["date"])
    deck = Deck(title=title, slides=slides, **deck_fields)
    if not slides or slides[0].layout != Layout.TITLE:
        deck.slides.insert(0, Slide(layout=Layout.TITLE, title=deck.title, subtitle=deck.subtitle))
    return deck


def load_markdown(path: str | Path) -> Deck:
    return parse_markdown(Path(path).read_text(encoding="utf-8"))
