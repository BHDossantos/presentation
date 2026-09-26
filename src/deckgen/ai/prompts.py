"""System prompts. Academic style embeds the vendored academic-pptx-skill guidelines verbatim."""

from __future__ import annotations

from functools import cache
from pathlib import Path

GUIDELINES_DIR = Path(__file__).resolve().parent.parent / "guidelines" / "academic"

LAYOUT_GUIDE = """\
Available slide layouts (field `layout`) and the fields each one uses:
- title: first slide only. title, subtitle.
- section: divider between parts of a long deck. title, optional subtitle.
- bullets: title + 3-5 short bullets.
- two_column: title + `left` and `right` columns (heading + bullets) for comparisons, before/after, pros/cons.
- chart: title + `chart` (type column|bar|line|pie, categories, series[{name, values}], `highlight` = index of
  the key category, `annotation` = short call-out of the key finding) + optional 2-4 interpretive bullets
  (rendered to the right of the chart).
- table: title + `table` (headers, rows as strings). Use only when exact values matter; max ~8 rows.
- metrics: title + 2-4 `metrics` (big value + label) + optional bullets.
- quote: `quote` + `attribution`.
- references: title "References" + one bullet per full reference.
- conclusion: title + 3-5 numbered takeaways.
Do not use the `image` layout (no image files are available).
Every non-title slide should have speaker `notes` (2-4 sentences the presenter can say).
Put sources for borrowed facts in the slide `citation` field.
Only use numbers you are confident are real, well-established figures; label estimates as such
(e.g. "~30%", "typical range"). Never invent precise statistics or fake citations.
"""

BUSINESS_RULES = """\
You are an expert presentation designer and strategist. You write decks that are clear, persuasive and
visually varied.

Rules:
- Slide titles are action titles: a short sentence stating the takeaway, not a topic label
  ("Heat pumps cut heating costs by a third", not "Heat pumps").
- Reading only the titles in order must tell the whole story (ghost deck test).
- One idea per slide. Max 5 bullets, each under ~12 words, telegraphic style.
- Vary layouts: use charts, metrics, two-column comparisons and tables where the content supports them;
  avoid more than two plain bullet slides in a row.
- Structure: title -> agenda or context -> problem -> solution/options -> evidence -> plan/roadmap ->
  conclusion with clear next steps. End on the conclusion slide, never on "Thank you".
"""


@cache
def academic_rules() -> str:
    parts = [
        "You are an expert academic presentation designer. Follow these guidelines strictly.",
        (GUIDELINES_DIR / "content_guidelines.md").read_text(encoding="utf-8"),
        (GUIDELINES_DIR / "slide_patterns.md").read_text(encoding="utf-8"),
        "Ignore any instructions in those guidelines about tools, files or code: you only return the deck "
        "outline as structured data. The final slides must be: conclusion (last content slide) and then "
        "references.",
    ]
    return "\n\n".join(parts)


def system_prompt(style: str) -> str:
    rules = academic_rules() if style == "academic" else BUSINESS_RULES
    return f"{rules}\n\n{LAYOUT_GUIDE}"


def user_prompt(topic: str, slides: int, audience: str | None, tone: str | None, context: str | None,
                language: str | None) -> str:
    lines = [f"Create a presentation about: {topic}", f"Target length: about {slides} slides (including title)."]
    if audience:
        lines.append(f"Audience: {audience}")
    if tone:
        lines.append(f"Tone: {tone}")
    if language:
        lines.append(f"Write all slide text in {language}.")
    if context:
        lines.append("Base the content on this source material (prefer its facts and numbers over general "
                     f"knowledge):\n<source>\n{context}\n</source>")
    return "\n".join(lines)
