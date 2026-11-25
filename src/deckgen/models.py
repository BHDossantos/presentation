"""Deck data model shared by every input parser, the AI generator and every renderer."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class Layout(str, Enum):
    TITLE = "title"
    SECTION = "section"
    BULLETS = "bullets"
    TWO_COLUMN = "two_column"
    CHART = "chart"
    TABLE = "table"
    METRICS = "metrics"
    QUOTE = "quote"
    IMAGE = "image"
    REFERENCES = "references"
    CONCLUSION = "conclusion"


class Series(BaseModel):
    name: str
    values: list[float]


class ChartSpec(BaseModel):
    type: Literal["column", "bar", "line", "pie"] = "column"
    categories: list[str]
    series: list[Series]
    highlight: int | None = Field(
        default=None, description="Index of the category to highlight as the key finding."
    )
    annotation: str | None = Field(default=None, description="Short call-out for the key finding.")
    y_label: str | None = None


class TableSpec(BaseModel):
    headers: list[str]
    rows: list[list[str]]


class Metric(BaseModel):
    value: str = Field(description="The big number, e.g. '42%' or '$1.2M'.")
    label: str


class Column(BaseModel):
    heading: str | None = None
    bullets: list[str] = Field(default_factory=list)


class Slide(BaseModel):
    layout: Layout = Layout.BULLETS
    title: str
    subtitle: str | None = None
    bullets: list[str] = Field(default_factory=list)
    left: Column | None = None
    right: Column | None = None
    chart: ChartSpec | None = None
    table: TableSpec | None = None
    metrics: list[Metric] = Field(default_factory=list)
    quote: str | None = None
    attribution: str | None = None
    image: str | None = Field(default=None, description="Local path to an image file.")
    citation: str | None = Field(default=None, description="Source shown at the bottom of the slide.")
    notes: str | None = Field(default=None, description="Speaker notes.")


class Deck(BaseModel):
    title: str
    subtitle: str | None = None
    author: str | None = None
    date: str | None = None
    style: Literal["business", "academic"] = "business"
    theme: str | None = None
    slides: list[Slide]

    def to_json(self, path: str | Path) -> Path:
        path = Path(path)
        path.write_text(self.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
        return path

    @classmethod
    def from_json(cls, path: str | Path) -> Deck:
        return cls.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))

    def ghost_deck(self) -> list[str]:
        """Titles in order: reading them alone should tell the whole story."""
        return [s.title for s in self.slides]
