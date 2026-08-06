"""Remove a magenta chroma-key fringe while preserving partial alpha."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: despill_chroma.py <input.png> <output.png>")

    source, destination = map(Path, sys.argv[1:])
    image = Image.open(source).convert("RGBA")
    pixels = image.load()

    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue

            # A chroma-key edge blended against #ff00ff has both red and blue
            # above green. Remove only that shared excess; opaque browns, gold,
            # and grey fur do not satisfy this condition. Alpha is untouched.
            spill = max(0, min(red, blue) - green)
            if spill:
                # The supplied strip was RGB against a solid matte, so its
                # anti-aliased edge is still opaque. Turn the same measured
                # matte contribution into partial alpha before removing it.
                # This preserves a soft fur silhouette rather than a binary
                # hard key or a pink fringe.
                matte_alpha = max(0, round(255 - spill * 1.3))
                pixels[x, y] = (
                    max(0, red - spill),
                    green,
                    max(0, blue - spill),
                    min(alpha, matte_alpha),
                )

    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)


if __name__ == "__main__":
    main()
