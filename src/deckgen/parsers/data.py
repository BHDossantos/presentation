"""CSV / JSON data file -> Deck with KPI, chart and table slides (no API key needed)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from deckgen.models import ChartSpec, Deck, Layout, Metric, Series, Slide, TableSpec


def _number(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "").replace("$", "").replace("%", "")
    try:
        return float(text)
    except ValueError:
        return None


def _fmt(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    if abs(v) >= 10_000:
        return f"{v / 1_000:.1f}K"
    return f"{v:,.0f}" if float(v).is_integer() else f"{v:,.1f}"


def load_rows(path: str | Path) -> list[dict]:
    path = Path(path)
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("rows") or data.get("data") or next(iter(data.values()))
        return list(data)
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def deck_from_rows(rows: list[dict], title: str, subtitle: str | None = None, style: str = "business",
                   max_categories: int = 12) -> Deck:
    if not rows:
        raise ValueError("Data file has no rows")
    columns = list(rows[0].keys())
    label_col = columns[0]
    numeric = [c for c in columns[1:] if all(_number(r.get(c)) is not None for r in rows)]
    if not numeric:
        raise ValueError("Data file needs at least one numeric column after the label column")
    shown = rows[:max_categories]
    categories = [str(r[label_col]) for r in shown]
    slides = [Slide(layout=Layout.TITLE, title=title, subtitle=subtitle or f"Automated report · {len(rows)} rows")]

    primary = numeric[0]
    totals = {c: sum(_number(r[c]) for r in rows) for c in numeric}
    metrics = [Metric(value=_fmt(totals[c]), label=f"Total {c}") for c in numeric[:3]]
    top_row = max(rows, key=lambda r: _number(r[primary]))
    metrics.append(Metric(value=str(top_row[label_col]), label=f"Top {label_col.lower()} by {primary}"))
    slides.append(Slide(layout=Layout.METRICS, title=f"{top_row[label_col]} leads on {primary}",
                        metrics=metrics[:4]))

    for col in numeric:
        values = [_number(r[col]) for r in shown]
        hi = max(range(len(values)), key=values.__getitem__)
        lo = min(range(len(values)), key=values.__getitem__)
        avg = sum(values) / len(values)
        first, last = values[0], values[-1]
        change = f"{(last - first) / first:+.0%} from {categories[0]} to {categories[-1]}" if first else ""
        slides.append(Slide(
            layout=Layout.CHART,
            title=f"{categories[hi]} has the highest {col}",
            chart=ChartSpec(type="line" if len(values) > 8 else "column", categories=categories,
                            series=[Series(name=col, values=values)], highlight=hi,
                            annotation=f"Peak: {categories[hi]} at {_fmt(values[hi])} "
                                       f"({values[hi] / avg - 1:+.0%} vs average)"),
            bullets=[b for b in (f"Average {col}: {_fmt(avg)}",
                                 f"Lowest: {categories[lo]} ({_fmt(values[lo])})",
                                 f"Total: {_fmt(sum(values))}", change) if b],
        ))

    peaks = [max(abs(_number(r[c])) for r in rows) or 1 for c in numeric[:3]]
    if len(numeric) > 1 and max(peaks) / min(peaks) <= 5:  # only compare series on a similar scale
        slides.append(Slide(
            layout=Layout.CHART, title=f"{' vs '.join(numeric[:3])} side by side",
            chart=ChartSpec(type="column", categories=categories,
                            series=[Series(name=c, values=[_number(r[c]) for r in shown]) for c in numeric[:3]]),
        ))

    table_cols = [label_col] + numeric[:5]
    slides.append(Slide(
        layout=Layout.TABLE, title="Underlying data",
        table=TableSpec(headers=table_cols,
                        rows=[[str(r[label_col])] + [_fmt(_number(r[c])) for c in numeric[:5]] for r in rows[:12]]),
        citation=f"{len(rows)} rows" + (" (first 12 shown)" if len(rows) > 12 else ""),
    ))
    slides.append(Slide(layout=Layout.CONCLUSION, title="Key takeaways", bullets=[
        f"{top_row[label_col]} is the top performer on {primary}",
        *[f"Total {c}: {_fmt(totals[c])}" for c in numeric[:3]],
    ]))
    return Deck(title=title, subtitle=subtitle, style=style, slides=slides)


def load_data(path: str | Path, title: str | None = None, subtitle: str | None = None,
              style: str = "business") -> Deck:
    path = Path(path)
    return deck_from_rows(load_rows(path), title or path.stem.replace("_", " ").replace("-", " ").title(),
                          subtitle, style)
