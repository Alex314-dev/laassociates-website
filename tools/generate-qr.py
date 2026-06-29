#!/usr/bin/env python3
"""Generate the branded business-card QR code for LA Associates.

Encodes the live site URL and overlays the logo mark in the centre. Produces a
vector SVG (best for print) and a high-resolution PNG.

Re-run after changing the URL or brand colour:

    python3 tools/generate-qr.py

Requires: segno, Pillow  (pip install segno Pillow)
"""
from __future__ import annotations

import base64
import io
import re
from pathlib import Path

import segno
from PIL import Image

# --- configuration -----------------------------------------------------------
URL = "https://laassociatesbg.com/"
BRAND = "#8C181B"          # logo maroon — matches --brand in assets/css/styles.css
WHITE = "#ffffff"
ROOT = Path(__file__).resolve().parent.parent
LOGO_SRC = ROOT / "assets" / "img" / "logo-mark.png"
OUT_SVG = ROOT / "assets" / "img" / "qr-laassociatesbg.svg"
OUT_PNG = ROOT / "assets" / "img" / "qr-laassociatesbg.png"

# High error correction (~30%) so the centred logo overlay stays scannable.
LOGO_RATIO = 0.20          # logo width as a fraction of the QR width
PNG_SCALE = 28             # px per module for the raster output (-> ~1000px)
QUIET_ZONE = 4             # modules of white border (QR spec minimum)


def trimmed_logo() -> Image.Image:
    """Load the logo mark, trimmed to its non-transparent bounding box."""
    logo = Image.open(LOGO_SRC).convert("RGBA")
    bbox = logo.getbbox()
    return logo.crop(bbox) if bbox else logo


def make_png(qr: segno.QRCode) -> None:
    """Render the QR as a high-res PNG with a centred logo on a white chip."""
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=PNG_SCALE, border=QUIET_ZONE,
            dark=BRAND, light=WHITE)
    buf.seek(0)
    base = Image.open(buf).convert("RGBA")
    w, h = base.size

    logo = trimmed_logo()
    target = int(w * LOGO_RATIO)
    ratio = target / max(logo.size)
    logo = logo.resize((round(logo.width * ratio), round(logo.height * ratio)),
                       Image.LANCZOS)

    # White rounded chip behind the logo so it reads cleanly over the modules.
    pad = round(target * 0.16)
    chip_w, chip_h = logo.width + 2 * pad, logo.height + 2 * pad
    chip = Image.new("RGBA", (chip_w, chip_h), (0, 0, 0, 0))
    from PIL import ImageDraw
    radius = round(min(chip_w, chip_h) * 0.18)
    ImageDraw.Draw(chip).rounded_rectangle(
        [0, 0, chip_w - 1, chip_h - 1], radius=radius, fill=WHITE)
    chip.alpha_composite(logo, (pad, pad))

    base.alpha_composite(chip, ((w - chip_w) // 2, (h - chip_h) // 2))
    base.save(OUT_PNG)


def make_svg(qr: segno.QRCode) -> None:
    """Render the QR as SVG, injecting a centred white chip + embedded logo."""
    buf = io.BytesIO()
    qr.save(buf, kind="svg", scale=10, border=QUIET_ZONE,
            dark=BRAND, light=WHITE)
    svg = buf.getvalue().decode("utf-8")

    # Pull the canvas size so we can centre overlay elements in user units.
    m = re.search(r'<svg[^>]*\bwidth="([\d.]+)"[^>]*\bheight="([\d.]+)"', svg)
    vb_w, vb_h = float(m.group(1)), float(m.group(2))

    logo = trimmed_logo()
    logo_w = vb_w * LOGO_RATIO
    logo_h = logo_w * logo.height / logo.width
    pad = logo_w * 0.16
    chip_w, chip_h = logo_w + 2 * pad, logo_h + 2 * pad
    chip_x, chip_y = (vb_w - chip_w) / 2, (vb_h - chip_h) / 2
    logo_x, logo_y = (vb_w - logo_w) / 2, (vb_h - logo_h) / 2
    radius = min(chip_w, chip_h) * 0.18

    out = io.BytesIO()
    logo.save(out, format="PNG")
    b64 = base64.b64encode(out.getvalue()).decode("ascii")

    overlay = (
        f'<rect x="{chip_x:.3f}" y="{chip_y:.3f}" width="{chip_w:.3f}" '
        f'height="{chip_h:.3f}" rx="{radius:.3f}" ry="{radius:.3f}" fill="{WHITE}"/>'
        f'<image x="{logo_x:.3f}" y="{logo_y:.3f}" width="{logo_w:.3f}" '
        f'height="{logo_h:.3f}" href="data:image/png;base64,{b64}"/>'
    )
    svg = svg.replace("</svg>", overlay + "</svg>")
    OUT_SVG.write_text(svg, encoding="utf-8")


def main() -> None:
    qr = segno.make(URL, error="h")
    make_png(qr)
    make_svg(qr)
    print(f"Encoded: {URL}")
    print(f"  version={qr.version}  error={qr.error}")
    print(f"  wrote {OUT_SVG.relative_to(ROOT)}")
    print(f"  wrote {OUT_PNG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
