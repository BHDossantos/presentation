"""Portable rehearsal scripts, independent of PowerPoint and PDF tools."""

from deckgen.models import Deck


def speaker_notes(deck: Deck, include_empty: bool = False) -> str:
    """Return a UTF-8-friendly text script preserving original slide numbers."""
    parts = [deck.title, "=" * len(deck.title)]
    count = 0
    for number, slide in enumerate(deck.slides, 1):
        notes = (slide.notes or "").strip()
        if not notes and not include_empty:
            continue
        count += 1
        parts.extend(["", f"Slide {number}: {slide.title}", "", notes or "[No speaker notes]"])
    if not count:
        parts.extend(["", "No speaker notes found."])
    return "\n".join(parts) + "\n"
