# Vendored guidelines

`academic/` is vendored from [Gabberflast/academic-pptx-skill](https://github.com/Gabberflast/academic-pptx-skill)
(MIT License, © 2026 Gabberflast — see `academic/LICENSE`). deckgen feeds `content_guidelines.md` and
`slide_patterns.md` to Claude when generating decks in `academic` style, and `deckgen lint` enforces
its QA checklist (action titles, ≤40 words per slide, references slide, end on conclusions).

The general design principles (content-informed palettes, web-safe fonts, visual QA loop via rendered
thumbnails) are adapted from Anthropic's
[pptx skill](https://github.com/ComposioHQ/awesome-claude-skills/blob/master/document-skills/pptx/SKILL.md).
That skill is proprietary, so none of its files are copied here; deckgen implements the ideas independently.
