"""Render a Deck to an editable 16:9 .pptx using python-pptx (native text, charts and tables)."""

from __future__ import annotations

import math
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from deckgen.models import Deck, Layout, Slide
from deckgen.themes import Theme

SLIDE_W, SLIDE_H = 13.333, 7.5
MARGIN = 0.6
CONTENT_TOP = 1.55
CONTENT_BOTTOM = 6.75

CHART_TYPES = {
    "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "bar": XL_CHART_TYPE.BAR_CLUSTERED,
    "line": XL_CHART_TYPE.LINE_MARKERS,
    "pie": XL_CHART_TYPE.PIE,
}


def rgb(hex_color: str) -> RGBColor:
    return RGBColor.from_string(hex_color.lstrip("#").upper())


def blend(a: str, b: str, t: float) -> str:
    """Mix hex color ``a`` toward ``b`` by fraction ``t``."""
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb, strict=True))


def text_height(lines: list[str], width_in: float, size: int, char_w: float = 0.52) -> float:
    """Estimated height in inches of ``lines`` wrapped into ``width_in`` at ``size`` pt."""
    chars_per_line = max(1, int(width_in * 72 / (size * char_w)))
    rendered = sum(max(1, math.ceil(len(line) / chars_per_line)) for line in lines)
    return rendered * size * 1.2 / 72 + len(lines) * size * 0.45 / 72


def fit_font_size(lines: list[str], width_in: float, height_in: float, base: int, minimum: int,
                  char_w: float = 0.52) -> int:
    """Largest size <= base (and >= minimum) at which ``lines`` are estimated to fit the box."""
    size = base
    while size > minimum and text_height(lines, width_in, size, char_w) > height_in:
        size -= 1
    return size


class PptxRenderer:
    def __init__(self, theme: Theme):
        self.theme = theme

    # ---------------------------------------------------------------- public
    def render(self, deck: Deck, out_path: str | Path) -> Path:
        prs = Presentation()
        prs.slide_width, prs.slide_height = Inches(SLIDE_W), Inches(SLIDE_H)
        prs.core_properties.title = deck.title
        if deck.author:
            prs.core_properties.author = deck.author
        blank = prs.slide_layouts[6]
        total = len(deck.slides)
        for number, spec in enumerate(deck.slides, start=1):
            slide = prs.slides.add_slide(blank)
            draw = getattr(self, f"_draw_{spec.layout.value}")
            draw(slide, spec, deck)
            if spec.layout not in (Layout.TITLE, Layout.SECTION):
                self._footer(slide, spec, number, total)
            if spec.notes:
                slide.notes_slide.notes_text_frame.text = spec.notes
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        prs.save(out_path)
        return out_path

    # ---------------------------------------------------------------- primitives
    def _background(self, slide, color: str) -> None:
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = rgb(color)

    def _rect(self, slide, x, y, w, h, color: str, shape=MSO_SHAPE.RECTANGLE):
        shp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        shp.fill.solid()
        shp.fill.fore_color.rgb = rgb(color)
        shp.line.fill.background()
        shp.shadow.inherit = False
        return shp

    def _text(self, slide, x, y, w, h, text: str, size: int, color: str, bold=False, italic=False,
              align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = box.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = Inches(0.05)
        for i, line in enumerate(text.split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            run = p.add_run()
            run.text = line
            self._style_run(run, size, color, bold, italic)
        return box

    def _style_run(self, run, size, color, bold=False, italic=False):
        run.font.name = self.theme.font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = rgb(color)

    def _bullets(self, slide, x, y, w, h, items: list[str], size: int | None = None, color=None,
                 numbered=False, marker_color=None):
        t = self.theme
        base = t.body_size + (4 if len(items) <= 4 else 2 if len(items) <= 5 else 0)
        size = size or fit_font_size(items, w - 0.4, h, base, t.min_body_size)
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = box.text_frame
        tf.word_wrap = True
        for i, item in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_after = Pt(size * 0.55)
            p.line_spacing = 1.1
            self._set_bullet(p, size, numbered, marker_color or t.accent)
            run = p.add_run()
            run.text = item
            self._style_run(run, size, color or t.text)
        return box

    def _set_bullet(self, paragraph, size: int, numbered: bool, color: str) -> None:
        pPr = paragraph._p.get_or_add_pPr()
        indent = int(Pt(size * 1.3))
        pPr.set("marL", str(indent))
        pPr.set("indent", str(-indent))
        for tag in ("a:buClr", "a:buFont", "a:buChar", "a:buAutoNum", "a:buNone"):
            for el in pPr.findall(qn(tag)):
                pPr.remove(el)
        clr = pPr.makeelement(qn("a:buClr"), {})
        srgb = clr.makeelement(qn("a:srgbClr"), {"val": color})
        clr.append(srgb)
        pPr.append(clr)
        if numbered:
            pPr.append(pPr.makeelement(qn("a:buAutoNum"), {"type": "arabicPeriod"}))
        else:
            pPr.append(pPr.makeelement(qn("a:buFont"), {"typeface": "Arial"}))
            pPr.append(pPr.makeelement(qn("a:buChar"), {"char": "•"}))

    def _title(self, slide, spec: Slide) -> None:
        t = self.theme
        size = fit_font_size([spec.title], SLIDE_W - 2 * MARGIN, 1.0, t.title_size, 20)
        self._text(slide, MARGIN, 0.35, SLIDE_W - 2 * MARGIN, 1.05, spec.title, size, t.primary, bold=True,
                   anchor=MSO_ANCHOR.BOTTOM)
        if t.title_rule:
            self._rect(slide, MARGIN + 0.05, 1.42, 0.9, 0.06, t.accent)
        if spec.subtitle:
            self._text(slide, MARGIN, 1.5, SLIDE_W - 2 * MARGIN, 0.45, spec.subtitle, 16, t.muted)

    def _content_top(self, spec: Slide) -> float:
        return CONTENT_TOP + (0.45 if spec.subtitle else 0.0)

    def _footer(self, slide, spec: Slide, number: int, total: int) -> None:
        t = self.theme
        self._text(slide, SLIDE_W - MARGIN - 1.2, SLIDE_H - 0.5, 1.2, 0.3, f"{number} / {total}", 11, t.muted,
                   align=PP_ALIGN.RIGHT)
        if spec.citation:
            self._text(slide, MARGIN, SLIDE_H - 0.55, SLIDE_W - 2 * MARGIN - 1.4, 0.4, spec.citation, 12,
                       t.muted)

    # ---------------------------------------------------------------- layouts
    def _draw_title(self, slide, spec: Slide, deck: Deck) -> None:
        t = self.theme
        self._background(slide, t.title_background)
        self._rect(slide, MARGIN, 2.2, 0.12, 2.6, t.accent)
        size = fit_font_size([spec.title], 11.0, 1.9, 44, 28)
        self._text(slide, MARGIN + 0.4, 2.0, 11.5, 1.9, spec.title, size, t.title_text, bold=True,
                   anchor=MSO_ANCHOR.BOTTOM)
        subtitle = spec.subtitle or deck.subtitle
        if subtitle:
            self._text(slide, MARGIN + 0.4, 4.0, 11.5, 0.9, subtitle, 22, blend(t.title_text, t.title_background, 0.2))
        byline = " · ".join(x for x in (deck.author, deck.date) if x)
        if byline:
            self._text(slide, MARGIN + 0.4, 5.6, 11.5, 0.5, byline, 16, blend(t.title_text, t.title_background, 0.35))

    def _draw_section(self, slide, spec: Slide, deck: Deck) -> None:
        t = self.theme
        self._background(slide, t.title_background)
        self._rect(slide, MARGIN + 0.05, 4.25, 1.2, 0.08, t.accent)
        self._text(slide, MARGIN, 2.3, SLIDE_W - 2 * MARGIN, 1.8, spec.title, 40, t.title_text, bold=True,
                   anchor=MSO_ANCHOR.BOTTOM)
        if spec.subtitle:
            self._text(slide, MARGIN, 4.5, SLIDE_W - 2 * MARGIN, 0.8, spec.subtitle, 20,
                       blend(t.title_text, t.title_background, 0.25))

    def _draw_bullets(self, slide, spec: Slide, deck: Deck) -> None:
        self._background(slide, self.theme.background)
        self._title(slide, spec)
        top = self._content_top(spec)
        self._bullets(slide, MARGIN, top + 0.15, SLIDE_W - 2 * MARGIN, CONTENT_BOTTOM - top - 0.15, spec.bullets)

    def _draw_conclusion(self, slide, spec: Slide, deck: Deck) -> None:
        t = self.theme
        self._background(slide, t.background)
        self._title(slide, spec)
        top = self._content_top(spec) + 0.15
        box = self._bullets(slide, MARGIN + 0.35, top, SLIDE_W - 2 * MARGIN - 0.35, CONTENT_BOTTOM - top - 0.2,
                            spec.bullets, numbered=True)
        size = box.text_frame.paragraphs[0].runs[0].font.size.pt if spec.bullets else t.body_size
        bar_h = min(CONTENT_BOTTOM - top - 0.2, text_height(spec.bullets, SLIDE_W - 2 * MARGIN - 0.75, int(size)))
        self._rect(slide, MARGIN, top + 0.05, 0.08, max(bar_h, 0.8), t.accent)

    def _draw_two_column(self, slide, spec: Slide, deck: Deck) -> None:
        t = self.theme
        self._background(slide, t.background)
        self._title(slide, spec)
        top = self._content_top(spec) + 0.15
        col_w = (SLIDE_W - 2 * MARGIN - 0.5) / 2
        for i, col in enumerate((spec.left, spec.right)):
            if col is None:
                continue
            x = MARGIN + i * (col_w + 0.5)
            y = top
            if col.heading:
                self._text(slide, x, y, col_w, 0.5, col.heading, t.body_size + 2, t.accent, bold=True)
                self._rect(slide, x + 0.05, y + 0.55, col_w - 0.1, 0.03, blend(t.accent, t.background, 0.6))
                y += 0.7
            self._bullets(slide, x, y, col_w, CONTENT_BOTTOM - y, col.bullets)

    def _draw_chart(self, slide, spec: Slide, deck: Deck) -> None:
        t = self.theme
        self._background(slide, t.background)
        self._title(slide, spec)
        top = self._content_top(spec) + 0.1
        has_text = bool(spec.bullets)
        chart_w = 7.6 if has_text else SLIDE_W - 2 * MARGIN
        if spec.chart is not None:
            self._chart(slide, spec, MARGIN, top, chart_w, CONTENT_BOTTOM - top)
        if has_text:
            x = MARGIN + chart_w + 0.35
            self._bullets(slide, x, top + 0.3, SLIDE_W - MARGIN - x, CONTENT_BOTTOM - top - 0.3, spec.bullets)

    def _chart(self, slide, spec: Slide, x, y, w, h) -> None:
        t = self.theme
        c = spec.chart
        assert c is not None
        if c.annotation:
            color = t.highlight if c.highlight is not None else t.accent
            self._text(slide, x, y, w, 0.45, c.annotation, 16, color, bold=True)
            y, h = y + 0.5, h - 0.5
        data = CategoryChartData()
        data.categories = c.categories
        for s in c.series:
            data.add_series(s.name, [float(v) for v in s.values])
        frame = slide.shapes.add_chart(CHART_TYPES[c.type], Inches(x), Inches(y), Inches(w), Inches(h), data)
        chart = frame.chart
        chart.font.name = t.font
        chart.font.size = Pt(14)
        chart.font.color.rgb = rgb(t.text)
        is_pie = c.type == "pie"
        chart.has_legend = is_pie or len(c.series) > 1
        if chart.has_legend:
            chart.legend.position = XL_LEGEND_POSITION.BOTTOM
            chart.legend.include_in_layout = False
        if not is_pie:
            va = chart.value_axis
            va.has_major_gridlines = False
            va.visible = False
            ca = chart.category_axis
            ca.format.line.color.rgb = rgb(blend(t.text, t.background, 0.7))
            ca.tick_labels.font.size = Pt(14)
            ca.tick_labels.font.color.rgb = rgb(t.text)
        plot = chart.plots[0]
        plot.has_data_labels = True
        labels = plot.data_labels
        labels.font.size = Pt(12)
        labels.font.color.rgb = rgb(t.text)
        labels.number_format = "#,##0.##"
        labels.number_format_is_linked = False
        if is_pie:
            labels.position = XL_LABEL_POSITION.OUTSIDE_END
            labels.font.size = Pt(14)
        if c.type in ("column", "bar"):
            plot.gap_width = 60
        colors = t.chart_colors
        if c.highlight is not None:
            colors = [x for x in colors if x != t.highlight] or colors
        if is_pie:
            for i, point in enumerate(plot.series[0].points):
                point.format.fill.solid()
                color = t.highlight if c.highlight == i else colors[i % len(colors)]
                point.format.fill.fore_color.rgb = rgb(color)
            return
        single = len(c.series) == 1
        for i, series in enumerate(plot.series):
            color = colors[i % len(colors)]
            if single and c.highlight is not None:
                color = blend(colors[0], t.background, 0.45) if c.type != "line" else colors[0]
            if c.type == "line":
                series.format.line.color.rgb = rgb(color)
                series.format.line.width = Pt(3)
                series.smooth = False
            else:
                series.format.fill.solid()
                series.format.fill.fore_color.rgb = rgb(color)
            if single and c.highlight is not None and 0 <= c.highlight < len(c.categories):
                point = series.points[c.highlight]
                if c.type == "line":
                    point.marker.format.fill.solid()
                    point.marker.format.fill.fore_color.rgb = rgb(t.highlight)
                    point.marker.size = 12
                else:
                    point.format.fill.solid()
                    point.format.fill.fore_color.rgb = rgb(t.highlight)

    def _draw_table(self, slide, spec: Slide, deck: Deck) -> None:
        t = self.theme
        self._background(slide, t.background)
        self._title(slide, spec)
        if spec.table is None:
            return
        top = self._content_top(spec) + 0.15
        headers, rows = spec.table.headers, spec.table.rows
        n_rows, n_cols = len(rows) + 1, max(len(headers), 1)
        avail_h = CONTENT_BOTTOM - top
        size = max(11, min(18, int(avail_h * 72 / (n_rows * 1.9))))
        row_h = min(0.6, avail_h / n_rows)
        width = SLIDE_W - 2 * MARGIN
        shape = slide.shapes.add_table(n_rows, n_cols, Inches(MARGIN), Inches(top), Inches(width),
                                       Inches(row_h * n_rows))
        table = shape.table
        stripe = blend(t.accent, t.background, 0.9)
        for c_idx in range(n_cols):
            table.columns[c_idx].width = Emu(int(Inches(width) / n_cols))
        for r_idx in range(n_rows):
            values = headers if r_idx == 0 else rows[r_idx - 1]
            for c_idx in range(n_cols):
                cell = table.cell(r_idx, c_idx)
                cell.text = str(values[c_idx]) if c_idx < len(values) else ""
                cell.fill.solid()
                cell.fill.fore_color.rgb = rgb(t.primary if r_idx == 0 else (stripe if r_idx % 2 == 0
                                                                            else t.background))
                cell.margin_left = cell.margin_right = Inches(0.1)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                for p in cell.text_frame.paragraphs:
                    p.alignment = PP_ALIGN.LEFT if c_idx == 0 else PP_ALIGN.RIGHT
                    for run in p.runs:
                        header_color = t.background if t.primary != t.background else t.title_text
                        self._style_run(run, size, header_color if r_idx == 0 else t.text, bold=r_idx == 0)

    def _draw_metrics(self, slide, spec: Slide, deck: Deck) -> None:
        t = self.theme
        self._background(slide, t.background)
        self._title(slide, spec)
        metrics = spec.metrics[:4]
        if not metrics:
            return
        top = self._content_top(spec) + 0.4
        gap = 0.35
        card_w = (SLIDE_W - 2 * MARGIN - gap * (len(metrics) - 1)) / len(metrics)
        card_h = 2.6 if spec.bullets else 3.6
        card_fill = blend(t.accent, t.background, 0.88)
        for i, m in enumerate(metrics):
            x = MARGIN + i * (card_w + gap)
            self._rect(slide, x, top, card_w, card_h, card_fill)
            self._rect(slide, x, top, card_w, 0.08, t.accent)
            size = fit_font_size([m.value], card_w - 0.3, 1.0, 54, 24, char_w=0.62)
            self._text(slide, x + 0.15, top + 0.35, card_w - 0.3, 1.4, m.value, size, t.primary, bold=True,
                       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            self._text(slide, x + 0.15, top + 1.8, card_w - 0.3, card_h - 1.9, m.label, 16, t.text,
                       align=PP_ALIGN.CENTER)
        if spec.bullets:
            y = top + card_h + 0.35
            self._bullets(slide, MARGIN, y, SLIDE_W - 2 * MARGIN, CONTENT_BOTTOM - y, spec.bullets)

    def _draw_quote(self, slide, spec: Slide, deck: Deck) -> None:
        t = self.theme
        self._background(slide, t.background)
        self._text(slide, MARGIN + 0.4, 0.8, 1.5, 1.5, "“", 120, t.accent, bold=True)
        quote = spec.quote or spec.title
        size = fit_font_size([quote], 10.5, 3.2, 34, 20)
        self._text(slide, MARGIN + 1.2, 2.0, 10.5, 3.2, quote, size, t.primary, italic=True,
                   anchor=MSO_ANCHOR.MIDDLE)
        if spec.attribution:
            self._text(slide, MARGIN + 1.2, 5.35, 10.5, 0.5, f"— {spec.attribution}", 18, t.muted)

    def _draw_image(self, slide, spec: Slide, deck: Deck) -> None:
        t = self.theme
        self._background(slide, t.background)
        self._title(slide, spec)
        top = self._content_top(spec) + 0.15
        has_text = bool(spec.bullets)
        box_w = 7.4 if has_text else SLIDE_W - 2 * MARGIN
        box_h = CONTENT_BOTTOM - top
        path = Path(spec.image) if spec.image else None
        if path and path.exists():
            self._picture(slide, path, MARGIN, top, box_w, box_h)
        else:
            ph = self._rect(slide, MARGIN, top, box_w, box_h, blend(t.muted, t.background, 0.85))
            ph.text_frame.text = f"Image: {spec.image or 'placeholder'}"
            for run in ph.text_frame.paragraphs[0].runs:
                self._style_run(run, 14, t.muted)
        if has_text:
            x = MARGIN + box_w + 0.35
            self._bullets(slide, x, top + 0.2, SLIDE_W - MARGIN - x, box_h - 0.2, spec.bullets)

    def _picture(self, slide, path: Path, x, y, w, h) -> None:
        pic = slide.shapes.add_picture(str(path), Inches(x), Inches(y))
        ratio = min(Inches(w) / pic.width, Inches(h) / pic.height)
        pic.width, pic.height = int(pic.width * ratio), int(pic.height * ratio)
        pic.left = int(Inches(x) + (Inches(w) - pic.width) / 2)
        pic.top = int(Inches(y) + (Inches(h) - pic.height) / 2)

    def _draw_references(self, slide, spec: Slide, deck: Deck) -> None:
        t = self.theme
        self._background(slide, t.background)
        self._title(slide, spec)
        top = self._content_top(spec) + 0.15
        size = fit_font_size(spec.bullets, SLIDE_W - 2 * MARGIN - 0.4, CONTENT_BOTTOM - top, 16, 11)
        self._bullets(slide, MARGIN, top, SLIDE_W - 2 * MARGIN, CONTENT_BOTTOM - top, spec.bullets, size=size,
                      numbered=True, marker_color=t.muted)


def render_pptx(deck: Deck, theme: Theme, out_path: str | Path) -> Path:
    return PptxRenderer(theme).render(deck, out_path)
