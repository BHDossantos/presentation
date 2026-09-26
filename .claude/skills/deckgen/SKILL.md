---
name: deckgen
description: Build presentations (PowerPoint/HTML/PDF) with this repo's deckgen CLI. Use when the user asks to make, generate, update or preview slides, a deck or a presentation from a topic, notes, a paper or a data file.
---

# Making decks with deckgen

1. **Pick the input mode**
   - A topic only, with an API key available → `deckgen generate "<topic>" --slides N [--style academic] [--audience ...]`
   - Otherwise, or when you are writing the content yourself (usually best for quality and control), write a
     Markdown outline in `examples/` or `out/` following `examples/energy-efficient-buildings.md` (the format is in
     README.md), then run `deckgen outline <file> -f pptx,html,pdf,json`.
   - A spreadsheet → `deckgen data <file.csv> --title ...`
2. **Write good content**
   - Every content slide title is an action title: a sentence stating the takeaway.
   - Reading the titles alone must tell the story (ghost deck test).
   - 3–5 short bullets per slide, one exhibit per chart slide, with `highlight` + `annotation` on the key finding.
   - Put sources in `Source:` and speaker notes in `Notes:`.
   - End on a `{conclusion}` slide; for academic decks follow with References.
   - Only use real, well-established numbers; label illustrative values as such.
   - For academic talks, follow `src/deckgen/guidelines/academic/`.
3. **Pick a theme** that matches the subject (`deckgen themes`), or write a custom theme YAML.
4. **QA loop**
   - `deckgen lint <outline>` must report no errors.
   - Run `deckgen thumbnails out/<deck>.pptx` and look at `contact-sheet.png` for overflow, overlaps, clipped
     labels and wrong colors.
   - Fix and repeat until a full pass finds nothing new.
5. Share the `.pptx` (editable), `.pdf` and `.html` from `out/`.
