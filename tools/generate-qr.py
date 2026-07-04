#!/usr/bin/env python3
"""Generate a branded business-card QR code for any website + logo.

Encodes a site URL and overlays a logo mark in the centre. Produces a vector
SVG (best for print) and a high-resolution PNG. The QR module colour is inferred
from the logo's dominant vibrant colour (override with --color).

Examples:

    # Default LA Associates QR (no args reproduces the original)
    python3 tools/generate-qr.py

    # Any brand: pass a URL and a logo image
    python3 tools/generate-qr.py https://example.com path/to/logo.png

    # Force a specific brand colour
    python3 tools/generate-qr.py https://example.com logo.png --color "#123456"

Outputs are auto-named in assets/img/ as qr-<domain-slug>.svg / .png.

Requires: segno, Pillow  (pip install segno Pillow)
"""
from __future__ import annotations

import argparse
import base64
import colorsys
import io
import re
from collections import defaultdict
from pathlib import Path

import segno
from PIL import Image, ImageDraw

# --- configuration -----------------------------------------------------------
DEFAULT_URL = "https://laassociatesbg.com/"
WHITE = "#ffffff"
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOGO = ROOT / "assets" / "img" / "logo-mark.png"
DEFAULT_OUT_DIR = ROOT / "assets" / "img"

# High error correction (~30%) so the centred logo overlay stays scannable.
LOGO_RATIO = 0.20          # logo width as a fraction of the QR width
PNG_SCALE = 28             # px per module for the raster output (-> ~1000px)
QUIET_ZONE = 4             # modules of white border (QR spec minimum)

HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def trimmed_logo(logo_src: Path) -> Image.Image:
    """Load a logo mark, trimmed to its non-transparent bounding box."""
    logo = Image.open(logo_src).convert("RGBA")
    bbox = logo.getbbox()
    return logo.crop(bbox) if bbox else logo


def domain_slug(url: str) -> str:
    """Derive a filename slug from a URL's second-level domain label.

    ``https://laassociatesbg.com/`` -> ``laassociatesbg`` so the default run
    keeps writing the existing qr-laassociatesbg.svg / .png files.
    """
    from urllib.parse import urlparse

    host = urlparse(url).netloc or urlparse(url).path
    host = host.split(":")[0]                      # drop any :port
    if host.startswith("www."):
        host = host[4:]
    labels = [p for p in host.split(".") if p]
    label = labels[-2] if len(labels) >= 2 else (labels[0] if labels else "qr")
    slug = re.sub(r"[^a-z0-9]", "", label.lower())
    return slug or "qr"


def infer_brand_color(logo: Image.Image) -> str:
    """Infer the dominant vibrant colour of a trimmed RGBA logo as ``#rrggbb``.

    Keeps opaque, saturated, mid-brightness pixels, buckets them coarsely and
    picks the saturation-weighted heaviest bucket. Falls back to the darkest
    opaque pixel (then black) for monochrome / greyscale logos.
    """
    small = logo.copy()
    small.thumbnail((128, 128), Image.LANCZOS)
    pixels = list(small.getdata())

    buckets: dict[tuple[int, int, int], list[float]] = defaultdict(
        lambda: [0.0, 0.0, 0.0, 0.0])  # weight, r*w, g*w, b*w
    darkest = None  # (value, (r, g, b)) among opaque pixels, for the fallback

    for r, g, b, a in pixels:
        if a <= 128:
            continue
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if darkest is None or v < darkest[0]:
            darkest = (v, (r, g, b))
        if s < 0.25 or v < 0.15 or v > 0.95:
            continue
        key = (r // 32, g // 32, b // 32)
        acc = buckets[key]
        acc[0] += s
        acc[1] += r * s
        acc[2] += g * s
        acc[3] += b * s

    if buckets:
        weight, rw, gw, bw = max(buckets.values(), key=lambda acc: acc[0])
        rgb = (round(rw / weight), round(gw / weight), round(bw / weight))
        print("  brand colour: inferred from logo (vibrant)")
    elif darkest is not None:
        rgb = darkest[1]
        print("  brand colour: inferred from logo (darkest — no vibrant tone)")
    else:
        rgb = (0, 0, 0)
        print("  brand colour: fallback black (empty logo)")

    return "#{:02x}{:02x}{:02x}".format(*rgb)


def make_png(qr: segno.QRCode, logo: Image.Image, brand: str,
             out_png: Path) -> None:
    """Render the QR as a high-res PNG with a centred logo on a white chip."""
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=PNG_SCALE, border=QUIET_ZONE,
            dark=brand, light=WHITE)
    buf.seek(0)
    base = Image.open(buf).convert("RGBA")
    w, h = base.size

    target = int(w * LOGO_RATIO)
    ratio = target / max(logo.size)
    logo = logo.resize((round(logo.width * ratio), round(logo.height * ratio)),
                       Image.LANCZOS)

    # White rounded chip behind the logo so it reads cleanly over the modules.
    pad = round(target * 0.16)
    chip_w, chip_h = logo.width + 2 * pad, logo.height + 2 * pad
    chip = Image.new("RGBA", (chip_w, chip_h), (0, 0, 0, 0))
    radius = round(min(chip_w, chip_h) * 0.18)
    ImageDraw.Draw(chip).rounded_rectangle(
        [0, 0, chip_w - 1, chip_h - 1], radius=radius, fill=WHITE)
    chip.alpha_composite(logo, (pad, pad))

    base.alpha_composite(chip, ((w - chip_w) // 2, (h - chip_h) // 2))
    base.save(out_png)


def make_svg(qr: segno.QRCode, logo: Image.Image, brand: str,
             out_svg: Path) -> None:
    """Render the QR as SVG, injecting a centred white chip + embedded logo."""
    buf = io.BytesIO()
    qr.save(buf, kind="svg", scale=10, border=QUIET_ZONE,
            dark=brand, light=WHITE)
    svg = buf.getvalue().decode("utf-8")

    # Pull the canvas size so we can centre overlay elements in user units.
    m = re.search(r'<svg[^>]*\bwidth="([\d.]+)"[^>]*\bheight="([\d.]+)"', svg)
    vb_w, vb_h = float(m.group(1)), float(m.group(2))

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
    out_svg.write_text(svg, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("url", nargs="?", default=DEFAULT_URL,
                   help=f"site URL to encode (default: {DEFAULT_URL})")
    p.add_argument("logo", nargs="?", default=str(DEFAULT_LOGO),
                   help="path to the logo image (default: assets/img/logo-mark.png)")
    p.add_argument("--color", default=None,
                   help="brand colour hex (e.g. '#8C181B'); inferred from the "
                        "logo when omitted")
    p.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR),
                   help="output directory (default: assets/img)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if args.color is not None and not HEX_RE.match(args.color):
        raise SystemExit(f"error: --color must be a hex like '#8C181B', got "
                         f"{args.color!r}")

    logo_src = Path(args.logo)
    if not logo_src.is_absolute() and not logo_src.exists():
        # Fall back to a path relative to the repo root (handy for defaults).
        alt = ROOT / args.logo
        if alt.exists():
            logo_src = alt
    if not logo_src.exists():
        raise SystemExit(f"error: logo not found: {args.logo}")

    logo = trimmed_logo(logo_src)
    brand = args.color if args.color else infer_brand_color(logo)

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = domain_slug(args.url)
    out_svg = out_dir / f"qr-{slug}.svg"
    out_png = out_dir / f"qr-{slug}.png"

    qr = segno.make(args.url, error="h")
    make_png(qr, logo, brand, out_png)
    make_svg(qr, logo, brand, out_svg)

    print(f"Encoded: {args.url}")
    print(f"  version={qr.version}  error={qr.error}  colour={brand}")
    print(f"  logo={logo_src}")
    try:
        print(f"  wrote {out_svg.relative_to(ROOT)}")
        print(f"  wrote {out_png.relative_to(ROOT)}")
    except ValueError:
        print(f"  wrote {out_svg}")
        print(f"  wrote {out_png}")


if __name__ == "__main__":
    main()
