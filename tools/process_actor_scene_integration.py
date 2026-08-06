from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "art" / "act01-production" / "characters"
OUT = ROOT / "art" / "act01-production" / "characters-integrated"

SHEETS = [
    ("pip", "idle"),
    ("pip", "walk"),
    ("pip", "dust-reach"),
    ("pip", "toll-paid"),
    ("bramble", "idle"),
    ("bramble", "talk"),
    ("old-bottlecap", "idle"),
    ("old-bottlecap", "toll-refused"),
    ("old-bottlecap", "toll-paid"),
    ("scuttle", "dash"),
]


def luminance_overlay(size: tuple[int, int], strength: float) -> Image.Image:
    width, height = size
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    pixels = overlay.load()
    for y in range(height):
        for x in range(width):
            upper_left = 1 - ((x / max(1, width)) * 0.52 + (y / max(1, height)) * 0.78)
            lower_right = ((x / max(1, width)) * 0.65 + (y / max(1, height)) * 0.85)
            if upper_left > 0.32:
                pixels[x, y] = (255, 209, 132, int(42 * strength * upper_left))
            elif lower_right > 0.58:
                pixels[x, y] = (68, 35, 18, int(62 * strength * (lower_right - 0.36)))
    return overlay.filter(ImageFilter.GaussianBlur(3))


def texture_overlay(size: tuple[int, int], alpha: int = 18) -> Image.Image:
    width, height = size
    texture = Image.new("RGBA", size, (0, 0, 0, 0))
    pixels = texture.load()
    seed = 915371
    for y in range(height):
        for x in range(width):
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            value = 120 + seed % 55
            pixels[x, y] = (value, value, value, alpha)
    return texture.filter(ImageFilter.GaussianBlur(0.35))


def alpha_mask(image: Image.Image) -> Image.Image:
    return image.getchannel("A").filter(ImageFilter.GaussianBlur(0.35))


def clipped(layer: Image.Image, mask: Image.Image) -> Image.Image:
    out = layer.copy()
    out.putalpha(ImageChops.multiply(out.getchannel("A"), mask))
    return out


def warm_recolor(image: Image.Image, actor: str) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            # Nudge clean vector colors toward the room's ochre/brown value range.
            rr = int(min(255, r * 0.96 + 12))
            gg = int(min(255, g * 0.91 + 8))
            bb = int(min(255, b * 0.82 + 4))
            if actor == "bramble" and r > 180 and g > 180 and b > 170:
                rr = int(min(255, rr * 0.9 + 34))
                gg = int(min(255, gg * 0.86 + 30))
                bb = int(min(255, bb * 0.78 + 22))
            pixels[x, y] = (rr, gg, bb, a)
    return rgba


def painterly_integrate(path: Path, actor: str) -> Image.Image:
    base = warm_recolor(Image.open(path), actor)
    mask = alpha_mask(base)

    lit = Image.alpha_composite(base, clipped(luminance_overlay(base.size, 1.0), mask))

    # Subtle whole-actor grain breaks the clean vector fill without changing alpha.
    tex = clipped(texture_overlay(base.size), mask)
    textured = Image.alpha_composite(lit, tex)

    # Paint-like edge softening and warm outline, still preserving the original matte.
    alpha = base.getchannel("A")
    edge = alpha.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(0.55))
    outline = Image.new("RGBA", base.size, (58, 35, 22, 0))
    outline.putalpha(edge.point(lambda value: min(95, int(value * 0.52))))
    result = Image.alpha_composite(outline, textured)
    result.putalpha(alpha)
    return result


def process_sheet(actor: str, action: str) -> None:
    source = SRC / actor / action
    dest = OUT / actor / action
    dest.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.name == "registration.json":
            shutil.copy2(item, dest / item.name)
        elif item.suffix.lower() == ".png" and "onion" not in item.name:
            painterly_integrate(item, actor).save(dest / item.name)


def main() -> None:
    for actor, action in SHEETS:
        process_sheet(actor, action)
    print(f"wrote integrated actor frames to {OUT}")


if __name__ == "__main__":
    main()
