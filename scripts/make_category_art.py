"""Generate the per-category tiles used as fallback artwork for events.

Run from the project root with the project virtualenv:

    python scripts/make_category_art.py

Writes static/img/cat/<category>.png. Rendered rather than downloaded so the
images are ours, need no attribution, and cannot 404. Uses the Windows colour
emoji font; the committed PNGs mean nobody else needs it to run the app.
"""

import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

OUT = pathlib.Path(__file__).resolve().parent.parent / "static" / "img" / "cat"
SIZE = 600
EMOJI_FONT = "C:/Windows/Fonts/seguiemj.ttf"

# category: (glyph, gradient start, gradient end) - palette matches the app theme
TILES = {
    "dance": ("\U0001F483", (255, 42, 122), (138, 43, 226)),
    "singing": ("\U0001F3A4", (0, 160, 255), (0, 240, 255)),
    "sloka": ("\U0001F549", (255, 170, 0), (255, 215, 0)),
    "music": ("\U0001F3BB", (16, 185, 129), (0, 200, 170)),
    "art": ("\U0001F3A8", (255, 110, 40), (255, 42, 122)),
    "ritual": ("\U0001FA94", (255, 140, 0), (255, 60, 90)),
    "show": ("\u2728", (138, 43, 226), (0, 240, 255)),
    "workshop": ("\U0001F9F5", (90, 120, 255), (138, 43, 226)),
    "food": ("\U0001F35B", (255, 190, 60), (255, 110, 40)),
    "sports": ("\U0001F3C6", (0, 200, 120), (0, 160, 255)),
    "other": ("\U0001F3AA", (110, 120, 200), (60, 70, 140)),
}


def gradient(start, end):
    """A diagonal two-colour wash."""
    base = Image.new("RGB", (SIZE, SIZE))
    pixels = base.load()
    for y in range(SIZE):
        for x in range(SIZE):
            t = (x + y) / (2 * SIZE - 2)
            pixels[x, y] = tuple(round(start[i] + (end[i] - start[i]) * t) for i in range(3))
    return base


def build(name, glyph, start, end):
    image = gradient(start, end)
    draw = ImageDraw.Draw(image, "RGBA")

    # A soft dark vignette keeps the glyph readable at thumbnail size.
    draw.ellipse(
        [SIZE * 0.12, SIZE * 0.12, SIZE * 0.88, SIZE * 0.88], fill=(10, 12, 20, 90)
    )

    font = ImageFont.truetype(EMOJI_FONT, 109)
    glyph_layer = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(glyph_layer).text(
        (80, 80), glyph, font=font, anchor="mm", embedded_color=True
    )
    glyph_layer = glyph_layer.resize((int(SIZE * 0.52),) * 2, Image.LANCZOS)
    image.paste(
        glyph_layer,
        ((SIZE - glyph_layer.width) // 2, (SIZE - glyph_layer.height) // 2),
        glyph_layer,
    )

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.png"
    image.save(path, optimize=True)
    return path


def main():
    if not pathlib.Path(EMOJI_FONT).exists():
        sys.exit(f"Colour emoji font not found at {EMOJI_FONT}")

    for name, (glyph, start, end) in TILES.items():
        path = build(name, glyph, start, end)
        print(f"  {path.name:14} {path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
