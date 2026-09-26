"""Render a Deck to a single self-contained HTML slideshow (arrow keys / click to navigate)."""

from __future__ import annotations

import math
from html import escape
from pathlib import Path

from jinja2 import Environment, select_autoescape
from markupsafe import Markup

from deckgen.models import ChartSpec, Deck
from deckgen.renderers.pptx_renderer import blend
from deckgen.themes import Theme


def chart_svg(chart: ChartSpec, theme: Theme, width: int = 760, height: int = 420) -> Markup:
    """Small dependency-free SVG chart mirroring the PPTX chart (highlight + labels, no gridlines)."""
    colors = theme.chart_colors
    if chart.highlight is not None:
        colors = [c for c in colors if c != theme.highlight] or colors
    text = theme.text
    parts: list[str] = [f'<svg viewBox="0 0 {width} {height}" class="chart" role="img">']
    if chart.type == "pie":
        values = chart.series[0].values
        total = sum(values) or 1
        cx, cy, r = width * 0.26, height / 2, min(width, height) * 0.42
        angle = -math.pi / 2
        for i, v in enumerate(values):
            sweep = 2 * math.pi * v / total
            x1, y1 = cx + r * math.cos(angle), cy + r * math.sin(angle)
            x2, y2 = cx + r * math.cos(angle + sweep), cy + r * math.sin(angle + sweep)
            color = theme.highlight if chart.highlight == i else colors[i % len(colors)]
            large = 1 if sweep > math.pi else 0
            parts.append(f'<path d="M{cx},{cy} L{x1:.1f},{y1:.1f} A{r},{r} 0 {large} 1 {x2:.1f},{y2:.1f} Z" '
                         f'fill="#{color}" stroke="#{theme.background}" stroke-width="2"/>')
            ly = 40 + i * 34
            parts.append(f'<rect x="{width * 0.55}" y="{ly - 14}" width="16" height="16" fill="#{color}"/>')
            parts.append(f'<text x="{width * 0.55 + 24}" y="{ly}" fill="#{text}" font-size="15">'
                         f'{escape(chart.categories[i])} ({v / total:.0%})</text>')
            angle += sweep
        parts.append("</svg>")
        return Markup("".join(parts))

    all_values = [v for s in chart.series for v in s.values] or [1]
    vmax = max(max(all_values), 0) or 1
    pad_l, pad_b, pad_t = 20, 44, 30 if len(chart.series) == 1 else 50
    plot_w, plot_h = width - pad_l * 2, height - pad_b - pad_t
    n_cat, n_ser = len(chart.categories), len(chart.series)
    single = n_ser == 1
    horizontal = chart.type == "bar"

    def fmt(v: float) -> str:
        return f"{v:,.0f}" if abs(v) >= 100 or float(v).is_integer() else f"{v:,.1f}"

    if chart.type == "line":
        step = plot_w / max(n_cat - 1, 1)
        for s_idx, s in enumerate(chart.series):
            color = colors[s_idx % len(colors)]
            pts = [(pad_l + i * step, pad_t + plot_h - plot_h * v / vmax) for i, v in enumerate(s.values)]
            parts.append('<polyline fill="none" stroke="#{}" stroke-width="3" points="{}"/>'.format(
                color, " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)))
            for i, (x, y) in enumerate(pts):
                hl = single and chart.highlight == i
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{7 if hl else 4}" '
                             f'fill="#{theme.highlight if hl else color}"/>')
                parts.append(f'<text x="{x:.1f}" y="{y - 12:.1f}" text-anchor="middle" font-size="13" '
                             f'fill="#{text}">{fmt(s.values[i])}</text>')
        for i, cat in enumerate(chart.categories):
            parts.append(f'<text x="{pad_l + i * step:.1f}" y="{height - 14}" text-anchor="middle" '
                         f'font-size="14" fill="#{text}">{escape(cat)}</text>')
    else:
        group = (plot_h if horizontal else plot_w) / n_cat
        bar = group * 0.7 / n_ser
        label_w = 150 if horizontal else 0
        for c_idx, cat in enumerate(chart.categories):
            for s_idx, s in enumerate(chart.series):
                v = s.values[c_idx] if c_idx < len(s.values) else 0
                color = colors[s_idx % len(colors)]
                if single and chart.highlight is not None:
                    color = theme.highlight if chart.highlight == c_idx else blend(colors[0], theme.background, 0.45)
                offset = c_idx * group + group * 0.15 + s_idx * bar
                if horizontal:
                    length = (plot_w - label_w - 60) * v / vmax
                    y = pad_t + offset
                    parts.append(f'<rect x="{pad_l + label_w}" y="{y:.1f}" width="{length:.1f}" '
                                 f'height="{bar:.1f}" fill="#{color}" rx="2"/>')
                    parts.append(f'<text x="{pad_l + label_w + length + 6:.1f}" y="{y + bar / 2 + 5:.1f}" '
                                 f'font-size="13" fill="#{text}">{fmt(v)}</text>')
                else:
                    length = plot_h * v / vmax
                    x = pad_l + offset
                    parts.append(f'<rect x="{x:.1f}" y="{pad_t + plot_h - length:.1f}" width="{bar:.1f}" '
                                 f'height="{length:.1f}" fill="#{color}" rx="2"/>')
                    parts.append(f'<text x="{x + bar / 2:.1f}" y="{pad_t + plot_h - length - 6:.1f}" '
                                 f'text-anchor="middle" font-size="13" fill="#{text}">{fmt(v)}</text>')
            if horizontal:
                parts.append(f'<text x="{pad_l + label_w - 8}" y="{pad_t + c_idx * group + group / 2 + 5:.1f}" '
                             f'text-anchor="end" font-size="14" fill="#{text}">{escape(cat)}</text>')
            else:
                parts.append(f'<text x="{pad_l + c_idx * group + group / 2:.1f}" y="{height - 14}" '
                             f'text-anchor="middle" font-size="14" fill="#{text}">{escape(cat)}</text>')
    if n_ser > 1:
        for s_idx, s in enumerate(chart.series):
            x = pad_l + s_idx * 170
            parts.append(f'<rect x="{x}" y="4" width="14" height="14" fill="#{colors[s_idx % len(colors)]}"/>')
            parts.append(f'<text x="{x + 20}" y="16" font-size="14" fill="#{text}">{escape(s.name)}</text>')
    parts.append("</svg>")
    return Markup("".join(parts))


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ deck.title }}</title>
<style>
:root{--bg:#{{t.background}};--tbg:#{{t.title_background}};--tt:#{{t.title_text}};--pri:#{{t.primary}};
--acc:#{{t.accent}};--txt:#{{t.text}};--mut:#{{t.muted}};--hl:#{{t.highlight}};--card:#{{card}};}
*{box-sizing:border-box}html,body{margin:0;height:100%;background:#111;font-family:{{t.font}},Arial,sans-serif}
.deck{height:100%;display:flex;align-items:center;justify-content:center}
.slide{display:none;position:relative;width:min(100vw,177.78vh);aspect-ratio:16/9;background:var(--bg);
color:var(--txt);overflow:hidden;font-size:min(1.5vw,2.67vh);padding:4% 4.5% 5%}
.slide.active{display:flex;flex-direction:column}
.slide.dark{background:var(--tbg);color:var(--tt);justify-content:center}
h1{font-size:{{t.title_size/13.5}}em;color:var(--pri);margin:0 0 .2em;line-height:1.15}
.dark h1{color:var(--tt);font-size:3.2em}.dark .sub{color:var(--tt);opacity:.8;font-size:1.5em}
.rule{width:4em;height:.3em;background:var(--acc);margin:.2em 0 .8em}
.sub{color:var(--mut);font-size:1.1em;margin-bottom:.6em}.by{opacity:.65;margin-top:2em;font-size:1.1em}
.body{flex:1;display:flex;gap:3%;min-height:0}.body>div{flex:1;min-width:0}
ul,ol{margin:.2em 0;padding-left:1.3em;font-size:{{t.body_size/13.5}}em;line-height:1.35}li{margin-bottom:.5em}
li::marker{color:var(--acc)}.col h3{color:var(--acc);margin:.1em 0 .4em;font-size:1.5em}
.chartwrap{flex:1.6!important}.chart{width:100%;height:auto;max-height:100%}
.note{color:var(--hl);font-weight:700;font-size:1.15em;margin-bottom:.3em}
table{border-collapse:collapse;width:100%;font-size:1.05em}th{background:var(--pri);color:var(--bg);text-align:left}
th,td{padding:.45em .7em}tr:nth-child(even) td{background:var(--card)}td:not(:first-child),th:not(:first-child){text-align:right}
.metrics{display:flex;gap:2.5%;margin-top:1em}.metric{flex:1;background:var(--card);border-top:.35em solid var(--acc);
padding:1.2em .8em;text-align:center}.metric b{display:block;font-size:2.6em;white-space:nowrap;color:var(--pri)}.metric span{font-size:1.2em}
blockquote{font-size:2.3em;font-style:italic;color:var(--pri);margin:auto 6%;border-left:.15em solid var(--acc);padding-left:.8em}
.attr{color:var(--mut);margin:0 6% auto;font-size:1.3em;padding-left:1.2em}
.cite{position:absolute;left:4.5%;bottom:3%;font-size:.85em;color:var(--mut)}
.num{position:absolute;right:4.5%;bottom:3%;font-size:.85em;color:var(--mut)}
.concl{border-left:.3em solid var(--acc);padding-left:1em}
img{max-width:100%;max-height:100%;object-fit:contain}
.help{position:fixed;bottom:8px;left:50%;transform:translateX(-50%);color:#888;font:12px sans-serif}
@media print{body{background:none}.slide{display:flex!important;page-break-after:always;width:100vw}.help{display:none}}
</style></head><body><div class="deck">
{% for s in deck.slides %}{% set L = s.layout.value %}
<section class="slide{% if L in ('title','section') %} dark{% endif %}" data-i="{{ loop.index0 }}">
{% if L == 'title' %}
  <h1>{{ s.title }}</h1>{% if s.subtitle or deck.subtitle %}<div class="sub">{{ s.subtitle or deck.subtitle }}</div>{% endif %}
  {% if deck.author or deck.date %}<div class="by">{{ [deck.author, deck.date]|select|join(' · ') }}</div>{% endif %}
{% elif L == 'section' %}
  <h1>{{ s.title }}</h1><div class="rule"></div>{% if s.subtitle %}<div class="sub">{{ s.subtitle }}</div>{% endif %}
{% elif L == 'quote' %}
  <blockquote>{{ s.quote or s.title }}</blockquote>{% if s.attribution %}<div class="attr">— {{ s.attribution }}</div>{% endif %}
{% else %}
  <h1>{{ s.title }}</h1>{% if t.title_rule %}<div class="rule"></div>{% endif %}
  {% if s.subtitle %}<div class="sub">{{ s.subtitle }}</div>{% endif %}
  <div class="body">
  {% if L == 'two_column' %}
    {% for c in [s.left, s.right] if c %}<div class="col">{% if c.heading %}<h3>{{ c.heading }}</h3>{% endif %}
    <ul>{% for b in c.bullets %}<li>{{ b }}</li>{% endfor %}</ul></div>{% endfor %}
  {% elif L == 'chart' and s.chart %}
    <div class="chartwrap">{% if s.chart.annotation %}<div class="note">{{ s.chart.annotation }}</div>{% endif %}
    {{ svg(s.chart) }}</div>{% if s.bullets %}<div><ul>{% for b in s.bullets %}<li>{{ b }}</li>{% endfor %}</ul></div>{% endif %}
  {% elif L == 'table' and s.table %}
    <div><table><tr>{% for h in s.table.headers %}<th>{{ h }}</th>{% endfor %}</tr>
    {% for r in s.table.rows %}<tr>{% for c in r %}<td>{{ c }}</td>{% endfor %}</tr>{% endfor %}</table></div>
  {% elif L == 'metrics' %}
    <div><div class="metrics">{% for m in s.metrics[:4] %}<div class="metric"><b>{{ m.value }}</b><span>{{ m.label }}</span></div>{% endfor %}</div>
    {% if s.bullets %}<ul style="margin-top:1em">{% for b in s.bullets %}<li>{{ b }}</li>{% endfor %}</ul>{% endif %}</div>
  {% elif L == 'image' %}
    <div class="chartwrap">{% if s.image %}<img src="{{ s.image }}" alt="">{% endif %}</div>
    {% if s.bullets %}<div><ul>{% for b in s.bullets %}<li>{{ b }}</li>{% endfor %}</ul></div>{% endif %}
  {% elif L in ('references', 'conclusion') %}
    <div class="{{ 'concl' if L == 'conclusion' else '' }}"><ol {% if L == 'references' %}style="font-size:1.05em"{% endif %}>
    {% for b in s.bullets %}<li>{{ b }}</li>{% endfor %}</ol></div>
  {% else %}
    <div><ul>{% for b in s.bullets %}<li>{{ b }}</li>{% endfor %}</ul></div>
  {% endif %}
  </div>
  {% if s.citation %}<div class="cite">{{ s.citation }}</div>{% endif %}
  <div class="num">{{ loop.index }} / {{ deck.slides|length }}</div>
{% endif %}
</section>{% endfor %}
</div><div class="help">← → / click to navigate · F fullscreen</div>
<script>
const S=[...document.querySelectorAll('.slide')];let i=Math.max(0,Math.min(S.length-1,parseInt(location.hash.slice(1)||'1')-1));
function go(n){S[i].classList.remove('active');i=Math.max(0,Math.min(S.length-1,n));S[i].classList.add('active');history.replaceState(null,'','#'+(i+1));}
go(i);addEventListener('hashchange',()=>{const n=parseInt(location.hash.slice(1))-1;if(n!==i&&n>=0)go(n);});
document.addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' '].includes(e.key))go(i+1);
if(['ArrowLeft','PageUp'].includes(e.key))go(i-1);if(e.key==='Home')go(0);if(e.key==='End')go(S.length-1);
if(e.key==='f')document.documentElement.requestFullscreen?.();});
document.addEventListener('click',e=>go(e.clientX>innerWidth/3?i+1:i-1));
</script></body></html>
"""


def render_html(deck: Deck, theme: Theme, out_path: str | Path) -> Path:
    env = Environment(autoescape=select_autoescape(default=True))
    template = env.from_string(TEMPLATE)
    html = template.render(deck=deck, t=theme, card=blend(theme.accent, theme.background, 0.88),
                           svg=lambda c: chart_svg(c, theme))
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path
