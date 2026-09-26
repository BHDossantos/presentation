"""Deterministic deck skeleton used when no API credentials are available.

It gives a correctly structured, editable starting point (``deck.json``) with bracketed placeholders.
"""

from __future__ import annotations

from deckgen.models import ChartSpec, Column, Deck, Layout, Metric, Series, Slide


def skeleton_deck(topic: str, style: str = "business", audience: str | None = None) -> Deck:
    t = topic.strip().rstrip(".")
    if style == "academic":
        slides = [
            Slide(layout=Layout.TITLE, title=t, subtitle="[Venue · Date]"),
            Slide(title=f"[Central question: what does this work show about {t}?]",
                  bullets=["[State the research question in one sentence]", "[Why it matters now]"]),
            Slide(title="[Prior work leaves a specific gap unexplained]",
                  bullets=["[Situation: what is established]", "[Complication: what is missing]"],
                  citation="[(Author, Year)]"),
            Slide(title="[Method exploits a specific design or dataset]",
                  bullets=["[Data source and sample]", "[Identification / approach]", "[Key assumption]"]),
            Slide(layout=Layout.CHART, title="[Main result stated as a complete sentence]",
                  chart=ChartSpec(type="column", categories=["[A]", "[B]", "[C]"],
                                  series=[Series(name="[Measure]", values=[1, 3, 2])], highlight=1,
                                  annotation="[Key finding call-out]"),
                  bullets=["[Interpretation]", "[Magnitude in context]"]),
            Slide(title="[Result holds under robustness checks]",
                  bullets=["[Check 1]", "[Check 2]", "[Limitation]"]),
            Slide(layout=Layout.CONCLUSION, title="[Conclusion: the one claim the audience should remember]",
                  bullets=["[Contribution]", "[Implication]", "[Next step] · [contact / link]"]),
            Slide(layout=Layout.REFERENCES, title="References", bullets=["[Author (Year). Title. Venue.]"]),
        ]
    else:
        slides = [
            Slide(layout=Layout.TITLE, title=t, subtitle=f"[Prepared for {audience or 'stakeholders'}]"),
            Slide(title=f"[Why {t} matters now]", bullets=["[Context]", "[Opportunity]", "[Risk of inaction]"]),
            Slide(layout=Layout.METRICS, title="[Three numbers frame the opportunity]",
                  metrics=[Metric(value="[X%]", label="[metric]"), Metric(value="[$Y]", label="[metric]"),
                           Metric(value="[Z]", label="[metric]")]),
            Slide(layout=Layout.TWO_COLUMN, title="[Today vs. proposed approach]",
                  left=Column(heading="Today", bullets=["[Pain point]", "[Pain point]"]),
                  right=Column(heading="Proposed", bullets=["[Improvement]", "[Improvement]"])),
            Slide(layout=Layout.CHART, title="[Evidence supports the proposal]",
                  chart=ChartSpec(type="column", categories=["Q1", "Q2", "Q3", "Q4"],
                                  series=[Series(name="[Metric]", values=[10, 14, 19, 26])], highlight=3,
                                  annotation="[Key trend call-out]"),
                  bullets=["[Interpretation]"]),
            Slide(title="[Roadmap delivers value in three phases]",
                  bullets=["[Phase 1 — timeframe]", "[Phase 2 — timeframe]", "[Phase 3 — timeframe]"]),
            Slide(layout=Layout.CONCLUSION, title="[Decision needed and next steps]",
                  bullets=["[Ask]", "[Owner and date]", "[Success metric]"]),
        ]
    for s in slides[1:]:
        s.notes = "[Speaker notes]"
    return Deck(title=t, style=style, slides=slides)  # type: ignore[arg-type]
