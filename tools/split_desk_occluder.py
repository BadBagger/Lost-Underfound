"""Split the generated desk's chair from its counter-front occluder.

The source was generated as one transparent asset. The chair must sit behind
Bramble, while the counter stays in front, so one draw layer cannot express the
intended staging.
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "art" / "act01-production" / "scene" / "layered-v2" / "occluders" / "desk_front.png"
OUT = SOURCE.parent
CHAIR_BOX = (178, 0, 319, 104)


def main() -> None:
    source = Image.open(SOURCE).convert("RGBA")
    chair = Image.new("RGBA", source.size, (0, 0, 0, 0))
    chair.alpha_composite(source.crop(CHAIR_BOX), (CHAIR_BOX[0], CHAIR_BOX[1]))

    counter = source.copy()
    alpha = counter.getchannel("A")
    alpha.paste(0, CHAIR_BOX)
    counter.putalpha(alpha)

    chair.save(OUT / "desk_chair_back.png")
    counter.save(OUT / "desk_front_actor_gap.png")
    print("wrote desk_chair_back.png and desk_front_actor_gap.png")


if __name__ == "__main__":
    main()
