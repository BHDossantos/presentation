"""PDF export and slide thumbnails via LibreOffice (``soffice``) and, optionally, pypdfium2."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


class ToolMissingError(RuntimeError):
    pass


def find_soffice() -> str | None:
    return shutil.which("soffice") or shutil.which("libreoffice")


def pptx_to_pdf(pptx_path: str | Path, out_dir: str | Path | None = None, timeout: int = 180) -> Path:
    soffice = find_soffice()
    if not soffice:
        raise ToolMissingError("PDF export needs LibreOffice: install it so `soffice` is on PATH.")
    pptx_path = Path(pptx_path).resolve()
    out_dir = Path(out_dir or pptx_path.parent).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run(
            [soffice, f"-env:UserInstallation=file://{profile}", "--headless", "--convert-to", "pdf",
             "--outdir", str(out_dir), str(pptx_path)],
            check=True, capture_output=True, timeout=timeout,
        )
    pdf = out_dir / f"{pptx_path.stem}.pdf"
    if not pdf.exists():
        raise RuntimeError(f"LibreOffice did not produce {pdf}")
    return pdf


def pdf_to_images(pdf_path: str | Path, out_dir: str | Path, scale: float = 1.0) -> list[Path]:
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:  # pragma: no cover - optional extra
        raise ToolMissingError("Thumbnails need the QA extra: pip install 'deckgen[qa]'") from exc
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("slide-*.png"):
        stale.unlink()
    pdf = pdfium.PdfDocument(str(pdf_path))
    paths = []
    for i in range(len(pdf)):
        image = pdf[i].render(scale=scale).to_pil()
        path = out_dir / f"slide-{i + 1:02d}.png"
        image.save(path)
        paths.append(path)
    pdf.close()
    return paths


def contact_sheet(images: list[Path], out_path: str | Path, cols: int = 3, thumb_w: int = 640) -> Path:
    """Tile slide images into one grid image for fast visual QA."""
    from PIL import Image, ImageDraw

    thumbs = []
    for p in images:
        im = Image.open(p).convert("RGB")
        im.thumbnail((thumb_w, thumb_w))
        thumbs.append(im)
    th = max(t.height for t in thumbs)
    rows = -(-len(thumbs) // cols)
    gap = 16
    sheet = Image.new("RGB", (cols * (thumb_w + gap) + gap, rows * (th + gap + 22) + gap), "#DDDDDD")
    draw = ImageDraw.Draw(sheet)
    for i, im in enumerate(thumbs):
        x = gap + (i % cols) * (thumb_w + gap)
        y = gap + (i // cols) * (th + gap + 22)
        draw.text((x, y), f"{i + 1}", fill="#333333")
        sheet.paste(im, (x, y + 18))
    out_path = Path(out_path)
    sheet.save(out_path)
    return out_path
