"""deckgen: generate presentations automatically from a topic, an outline or a data file."""

from deckgen.models import ChartSpec, Column, Deck, Layout, Metric, Series, Slide, TableSpec
from deckgen.pipeline import build, normalize

__version__ = "0.1.0"
__all__ = ["ChartSpec", "Column", "Deck", "Layout", "Metric", "Series", "Slide", "TableSpec", "build",
           "normalize"]
