"""Themes: colors, font and type scale. Built-ins live in ``builtin/*.yaml``; any YAML path works too."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path

import yaml

BUILTIN_DIR = Path(__file__).parent / "builtin"
DEFAULT_THEME = {"business": "corporate", "academic": "academic"}


def _hex(value) -> str:
    # Unquoted YAML like 000000 loads as an int; zfill restores the dropped leading zeros.
    return str(value).lstrip("#").upper().zfill(6)


@dataclass(frozen=True)
class Theme:
    name: str
    font: str = "Arial"
    background: str = "FFFFFF"
    title_background: str = "1F4E79"
    title_text: str = "FFFFFF"
    primary: str = "1F4E79"
    accent: str = "2E75B6"
    text: str = "222222"
    muted: str = "6B7280"
    highlight: str = "C2410C"
    chart_colors: list[str] = field(default_factory=lambda: ["2E75B6", "9CA3AF", "1F4E79", "BFDBFE"])
    title_size: int = 28
    body_size: int = 20
    min_body_size: int = 14
    title_rule: bool = True
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> Theme:
        known = {f.name for f in fields(cls)}
        clean = {k: v for k, v in data.items() if k in known}
        for key in ("background", "title_background", "title_text", "primary", "accent", "text", "muted",
                    "highlight"):
            if key in clean:
                clean[key] = _hex(clean[key])
        if "chart_colors" in clean:
            clean["chart_colors"] = [_hex(c) for c in clean["chart_colors"]]
        return cls(**clean)


def list_themes() -> list[Theme]:
    return [load_theme(p.stem) for p in sorted(BUILTIN_DIR.glob("*.yaml"))]


def load_theme(name_or_path: str | None, style: str = "business") -> Theme:
    """Load a built-in theme by name, or a custom theme from a YAML file path."""
    name_or_path = name_or_path or DEFAULT_THEME.get(style, "corporate")
    path = Path(name_or_path)
    if not path.suffix:
        path = BUILTIN_DIR / f"{name_or_path}.yaml"
    if not path.exists():
        available = ", ".join(p.stem for p in sorted(BUILTIN_DIR.glob("*.yaml")))
        raise ValueError(f"Unknown theme '{name_or_path}'. Built-in themes: {available}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    data.setdefault("name", path.stem)
    return Theme.from_dict(data)
