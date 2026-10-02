#!/usr/bin/env python3
"""ON AIR favicon set: a red tally badge with "ON / AIR" set in Pretendard Black (glyphs converted to paths).

usage: python make_favicon.py <Pretendard-Black.ttf>
writes onair/assets/favicon/{favicon.svg, favicon.ico, favicon-16.png, favicon-32.png, apple-touch-icon.png, icon-512.png}
"""
import io, pathlib, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from PIL import Image, ImageDraw, ImageFont

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "favicon"
TALLY, WHITE = "#FF2D4B", "#FFFFFF"

def word_path(font, text, height, tracking=-0.02):
    """SVG path data for `text`, scaled so cap height == `height` units; returns (d, width)."""
    gs, cmap, upm = font.getGlyphSet(), font.getBestCmap(), font["head"].unitsPerEm
    cap = getattr(font["OS/2"], "sCapHeight", 0) or int(upm * 0.7)
    k = height / cap
    x, parts = 0.0, []
    for ch in text:
        g = gs[cmap[ord(ch)]]
        pen = SVGPathPen(gs)
        g.draw(TransformPen(pen, (k, 0, 0, -k, x, height)))
        parts.append(pen.getCommands())
        x += g.width * k + tracking * height * 10
    return " ".join(parts), x - tracking * height * 10

def svg(font):
    on_d, on_w = word_path(font, "ON", 19)
    air_d, air_w = word_path(font, "AIR", 15)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="15" fill="{TALLY}"/>
  <circle cx="54.6" cy="9.4" r="3.5" fill="{WHITE}"/>
  <g fill="{WHITE}">
    <path transform="translate({(64 - on_w) / 2:.2f} 14.5)" d="{on_d}"/>
    <path transform="translate({(64 - air_w) / 2:.2f} 39)" d="{air_d}"/>
  </g>
</svg>
'''

def raster(ttf, size, simple=False):
    s = 1024
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 15 / 64), fill=TALLY)
    if simple:  # 16px: a single bold "ON" reads; two lines do not
        f = ImageFont.truetype(ttf, int(s * 0.56))
        d.text((s / 2, s / 2 + s * 0.02), "ON", font=f, fill=WHITE, anchor="mm")
    else:
        d.ellipse([s * 0.80, s * 0.09, s * 0.91, s * 0.20], fill=WHITE)
        d.text((s / 2, s * 0.385), "ON", font=ImageFont.truetype(ttf, int(s * 0.41)), fill=WHITE, anchor="mm")
        d.text((s / 2, s * 0.73), "AIR", font=ImageFont.truetype(ttf, int(s * 0.33)), fill=WHITE, anchor="mm")
    return im.resize((size, size), Image.LANCZOS)

def main():
    ttf = sys.argv[1]
    OUT.mkdir(parents=True, exist_ok=True)
    font = TTFont(ttf)
    (OUT / "favicon.svg").write_text(svg(font))
    raster(ttf, 16, simple=True).save(OUT / "favicon-16.png")
    raster(ttf, 32).save(OUT / "favicon-32.png")
    raster(ttf, 512).save(OUT / "icon-512.png")
    # apple touch icons are shown on a square tile: fill the corners instead of leaving them transparent
    tile = Image.new("RGBA", (180, 180), TALLY); tile.alpha_composite(raster(ttf, 180)); tile.convert("RGB").save(OUT / "apple-touch-icon.png")
    ico = [raster(ttf, 16, simple=True), raster(ttf, 32), raster(ttf, 48)]
    ico[2].save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=ico[:2])
    print("favicon set →", OUT)

if __name__ == "__main__":
    main()
