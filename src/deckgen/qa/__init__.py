"""Content QA: automated checks for the academic-pptx-skill checklist and general slide hygiene."""

from __future__ import annotations

import re
from dataclasses import dataclass

from deckgen.models import Deck, Layout, Slide

TOPIC_LABELS = {
    "introduction", "background", "results", "methods", "methodology", "data", "discussion", "overview",
    "agenda", "summary", "literature review", "conclusion", "conclusions", "thank you", "questions",
    "q&a", "outline", "motivation",
}


@dataclass
class Issue:
    slide: int
    level: str  # "error" | "warning"
    message: str

    def __str__(self) -> str:
        where = f"slide {self.slide}" if self.slide else "deck"
        return f"[{self.level}] {where}: {self.message}"


def body_words(slide: Slide) -> int:
    texts = list(slide.bullets)
    for col in (slide.left, slide.right):
        if col:
            texts += col.bullets + ([col.heading] if col.heading else [])
    if slide.quote:
        texts.append(slide.quote)
    return sum(len(t.split()) for t in texts)


def lint_deck(deck: Deck) -> list[Issue]:
    academic = deck.style == "academic"
    max_bullets = 5 if academic else 6
    max_words = 40 if academic else 60
    issues: list[Issue] = []
    content = [(i, s) for i, s in enumerate(deck.slides, start=1)
               if s.layout not in (Layout.TITLE, Layout.SECTION, Layout.REFERENCES, Layout.QUOTE)]

    for n, s in content:
        if len(s.bullets) > max_bullets:
            issues.append(Issue(n, "warning", f"{len(s.bullets)} bullets (max {max_bullets}); split the slide"))
        words = body_words(s)
        if words > max_words:
            issues.append(Issue(n, "warning", f"{words} words of body text (max ~{max_words})"))
        title = s.title.strip().lower().rstrip(".")
        if title in TOPIC_LABELS or len(s.title.split()) < 3:
            issues.append(Issue(n, "error" if academic else "warning",
                                f"'{s.title}' is a topic label; use an action title stating the takeaway"))
        if s.layout == Layout.CHART and s.chart is None:
            issues.append(Issue(n, "error", "chart layout without chart data"))
        if s.layout == Layout.TABLE and s.table is None:
            issues.append(Issue(n, "error", "table layout without table data"))
        if s.chart is not None:
            lengths = {len(x.values) for x in s.chart.series}
            if lengths != {len(s.chart.categories)}:
                issues.append(Issue(n, "error", "chart series length does not match categories"))
            if academic and s.chart.annotation is None and s.chart.highlight is None:
                issues.append(Issue(n, "warning", "exhibit has no highlighted key finding / annotation"))
        if s.table is not None and len(s.table.rows) > 12:
            issues.append(Issue(n, "warning", f"table has {len(s.table.rows)} rows; keep to ~12 or less"))
        if re.search(r"\[[^\]]+\]", s.title + " ".join(s.bullets)):
            issues.append(Issue(n, "warning", "contains [placeholder] text"))

    last = deck.slides[-1] if deck.slides else None
    if last and re.search(r"thank|questions\??$", last.title, re.I):
        issues.append(Issue(len(deck.slides), "error" if academic else "warning",
                            "deck ends on 'Thank you'/'Questions'; end on the conclusions slide"))
    if academic:
        if not any(s.layout == Layout.REFERENCES for s in deck.slides):
            issues.append(Issue(0, "error", "no References slide"))
        non_ref = [s for s in deck.slides if s.layout != Layout.REFERENCES]
        if non_ref and non_ref[-1].layout != Layout.CONCLUSION:
            issues.append(Issue(0, "warning", "last non-reference slide is not a conclusion slide"))
        if len(deck.slides) > 15 and not any(s.layout == Layout.SECTION for s in deck.slides):
            issues.append(Issue(0, "warning", "deck > 15 slides without section dividers"))
    return issues
