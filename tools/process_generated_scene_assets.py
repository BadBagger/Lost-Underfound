from __future__ import annotations

from pathlib import Path
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "art" / "act01-production" / "scene" / "layered-v2"

SOURCES = {
    "bg_room": Path(r"C:\Users\KyleB\.codex\generated_images\019fc7c5-b162-7760-b53c-8c20e100dab9\call_b35cGGiSBIeck0521DTjZinH.png"),
    "occluder_set": Path(r"C:\Users\KyleB\.codex\generated_images\019fc7c5-b162-7760-b53c-8c20e100dab9\call_12UIha2rh4DJQkVSt1S95qBy.png"),
    "dust_reveal": Path(r"C:\Users\KyleB\.codex\generated_images\019fc7c5-b162-7760-b53c-8c20e100dab9\call_OQBv6d1nXbAq5fTxGiWhE1cZ.png"),
    "grate_open": Path(r"C:\Users\KyleB\.codex\generated_images\019fc7c5-b162-7760-b53c-8c20e100dab9\call_uVeedkDmkKMHGxbq0XcdYlFB.png"),
    "button": Path(r"C:\Users\KyleB\.codex\generated_images\019fc7c5-b162-7760-b53c-8c20e100dab9\call_tN2ngkrAsoTg2EQ7rM8qI4kS.png"),
}


def ensure_dirs() -> None:
    for child in ["source", "occluders", "dust", "grate", "button", "fx"]:
        (OUT / child).mkdir(parents=True, exist_ok=True)


def alpha_green_hard(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = pixels[x, y]
            if g > 135 and r < 95 and b < 95 and g > r * 1.45 and g > b * 1.45:
                pixels[x, y] = (r, g, b, 0)
    return rgba


def alpha_green_partial(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = pixels[x, y]
            green_dominance = g - max(r, b)
            if g > 150 and r < 42 and b < 42:
                pixels[x, y] = (r, g, b, 0)
                continue
            if g > 105 and green_dominance > 14:
                inferred_alpha = max(r, b) / 255.0
                new_alpha = int(max(0, min(255, inferred_alpha * 255)))
                if new_alpha <= 2:
                    pixels[x, y] = (r, g, b, 0)
                    continue
                scale = 255 / max(1, new_alpha)
                rr = int(max(0, min(255, r * scale)))
                bb = int(max(0, min(255, b * scale)))
                neutral_green = int((rr + bb) * 0.48)
                gg = int(max(min(rr, bb), min(neutral_green, g - green_dominance)))
                pixels[x, y] = (rr, gg, bb, new_alpha)
                continue
            if a > 0 and g > max(r, b) + 4:
                # Despill semi-transparent dust/web edges without flattening their alpha.
                pixels[x, y] = (r, int(min(g, (r + b) * 0.46)), b, a)
    return rgba


def alpha_gray(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = pixels[x, y]
            if abs(r - g) < 7 and abs(g - b) < 7 and 96 <= r <= 180:
                pixels[x, y] = (r, g, b, 0)
    return rgba


def warm_dust(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            rr = int(min(255, r * 1.06 + 8))
            gg = int(min(255, min(g, (r + b) * 0.52) * 0.94 + 5))
            bb = int(min(255, b * 0.9))
            pixels[x, y] = (rr, gg, bb, a)
    return rgba


def crop_alpha(image: Image.Image, padding: int = 8) -> Image.Image:
    bbox = image.getbbox()
    if not bbox:
        return image
    left = max(0, bbox[0] - padding)
    top = max(0, bbox[1] - padding)
    right = min(image.width, bbox[2] + padding)
    bottom = min(image.height, bbox[3] + padding)
    return image.crop((left, top, right, bottom))


def resize_fit(image: Image.Image, max_w: int, max_h: int) -> Image.Image:
    copy = image.copy()
    copy.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    return copy


def save_alpha_crop(source: Image.Image, box: tuple[int, int, int, int], dest: Path, max_size: tuple[int, int] | None = None) -> None:
    cut = alpha_green_hard(source.crop(box))
    cut = crop_alpha(cut)
    if max_size:
        cut = resize_fit(cut, *max_size)
    dest.parent.mkdir(parents=True, exist_ok=True)
    cut.save(dest)


def save_strip_frames(source: Image.Image, dest_dir: Path, prefix: str, count: int, key: str, max_size: tuple[int, int]) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        left = round(index * source.width / count)
        right = round((index + 1) * source.width / count)
        frame = source.crop((left, 0, right, source.height))
        if key == "gray":
            frame = alpha_gray(frame)
        elif key == "green-partial-dust":
            frame = warm_dust(alpha_green_partial(frame))
        elif key == "green-partial":
            frame = alpha_green_partial(frame)
        else:
            frame = alpha_green_hard(frame)
        frame = crop_alpha(frame, 10)
        frame = resize_fit(frame, *max_size)
        frame.save(dest_dir / f"{prefix}_{index + 1:02d}.png")


def write_dark_qa(entries: list[tuple[str, Path]], dest: Path) -> None:
    thumbs: list[tuple[str, Image.Image]] = []
    for label, file_path in entries:
        image = Image.open(file_path).convert("RGBA")
        image.thumbnail((210, 150), Image.Resampling.LANCZOS)
        thumbs.append((label, image.copy()))
    width = max(1, len(thumbs)) * 230
    height = 190
    sheet = Image.new("RGBA", (width, height), (18, 16, 20, 255))
    for index, (label, image) in enumerate(thumbs):
        x = index * 230 + 10
        y = 24
        checker = Image.new("RGBA", image.size, (18, 16, 20, 255))
        sheet.alpha_composite(checker, (x, y))
        sheet.alpha_composite(image, (x, y))
        # Small label strip is outside the transparent asset and only in QA.
        for xx in range(x, min(x + 210, sheet.width)):
            for yy in range(4, 18):
                sheet.putpixel((xx, yy), (34, 29, 24, 255))
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(dest)


def write_shadow_sprite(dest: Path) -> None:
    width, height = 256, 96
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pixels = image.load()
    center_x = (width - 1) / 2
    center_y = (height - 1) / 2
    radius_x = width * 0.44
    radius_y = height * 0.32
    for y in range(height):
        for x in range(width):
            dx = (x - center_x) / radius_x
            dy = (y - center_y) / radius_y
            distance = dx * dx + dy * dy
            if distance >= 1:
                continue
            alpha = int(92 * (1 - distance) ** 1.8)
            pixels[x, y] = (25, 14, 8, alpha)
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest)


def main() -> None:
    ensure_dirs()
    for name, source in SOURCES.items():
        if not source.exists():
            raise SystemExit(f"missing generated source: {source}")
        Image.open(source).save(OUT / "source" / f"{name}.png")

    bg = Image.open(SOURCES["bg_room"]).convert("RGB").resize((1280, 720), Image.Resampling.LANCZOS)
    bg.save(OUT / "bg_room.png")

    occluders = Image.open(SOURCES["occluder_set"])
    third = occluders.width // 3
    save_alpha_crop(occluders, (0, 0, third, occluders.height), OUT / "occluders" / "desk_front.png", (465, 255))
    save_alpha_crop(occluders, (third, 0, third * 2, occluders.height), OUT / "occluders" / "gate_front.png", (285, 350))
    cobweb = alpha_green_partial(occluders.crop((third * 2 + 110, 0, occluders.width, occluders.height)))
    cobweb = crop_alpha(cobweb)
    cobweb = resize_fit(cobweb, 340, 360)
    cobweb.save(OUT / "cobweb.png")
    write_shadow_sprite(OUT / "fx" / "soft_oval_shadow.png")

    button = Image.open(SOURCES["button"])
    for index, name in enumerate(["icon", "held", "tossed"]):
        save_alpha_crop(
            button,
            (round(index * button.width / 3), 0, round((index + 1) * button.width / 3), button.height),
            OUT / "button" / f"{name}.png",
            (96, 96),
        )

    dust = Image.open(SOURCES["dust_reveal"])
    save_strip_frames(dust, OUT / "dust", "reveal", 6, "green-partial-dust", (135, 100))
    (OUT / "dust" / "reveal_01.png").replace(OUT / "dust" / "idle.png")
    save_strip_frames(dust, OUT / "dust", "reveal", 6, "green-partial-dust", (135, 100))

    grate = Image.open(SOURCES["grate_open"])
    save_strip_frames(grate, OUT / "grate", "open", 6, "gray", (250, 210))
    Image.open(OUT / "grate" / "open_01.png").save(OUT / "grate" / "closed.png")

    write_dark_qa(
        [
            ("cobweb", OUT / "cobweb.png"),
            ("dust4", OUT / "dust" / "reveal_04.png"),
            ("dust5", OUT / "dust" / "reveal_05.png"),
            ("dust6", OUT / "dust" / "reveal_06.png"),
        ],
        OUT / "qa" / "partial-alpha-dark-check.png",
    )

    print(f"wrote layered scene assets to {OUT}")


if __name__ == "__main__":
    main()
