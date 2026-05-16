# Owner: HAWRAA
from pathlib import Path

from PIL import Image, ImageDraw


def generate_overlay(
    image_path: str,
    label: str,
    confidence: float,
    out_path: str,
) -> None:
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    text = f"{label} ({confidence:.1%})"

    # black banner at the top, white text over it
    draw.rectangle([0, 0, img.width, 40], fill=(0, 0, 0))
    draw.text((10, 10), text, fill=(255, 255, 255))

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")
