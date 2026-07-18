#!/usr/bin/env python3
"""
prep_photo.py — turn a normal photo into a high-contrast, background-free
grayscale source image that's ready for ASCII conversion.

Usage:
    python scripts/prep_photo.py source-photo.jpg [output.png]

Pipeline:
    1. Remove the background with rembg (subject isolation).
    2. Boost local contrast with OpenCV CLAHE (contrast-limited adaptive
       histogram equalization) — this is what turns a flatly-lit face into
       one with real highlights and shadows.
    3. Composite onto pure white so the background maps to the blank end
       of the ASCII ramp (white -> space character).

Output: a grayscale PNG, source-prepped.png by default.
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image
import cv2
from rembg import remove


def remove_background(input_path: Path) -> Image.Image:
    """Return an RGBA image with the background stripped out."""
    with open(input_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    from io import BytesIO
    return Image.open(BytesIO(output_bytes)).convert("RGBA")


def apply_clahe(gray: np.ndarray) -> np.ndarray:
    """Contrast-limited adaptive histogram equalization on a grayscale array."""
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def composite_on_white(rgba: Image.Image) -> Image.Image:
    """Flatten an RGBA image onto a pure white background."""
    white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    return Image.alpha_composite(white_bg, rgba).convert("RGB")


def prep(input_path: Path, output_path: Path) -> None:
    print(f"[1/3] Removing background from {input_path.name} ...")
    subject_rgba = remove_background(input_path)

    print("[2/3] Compositing onto white + boosting local contrast (CLAHE) ...")
    flattened = composite_on_white(subject_rgba)
    gray = cv2.cvtColor(np.array(flattened), cv2.COLOR_RGB2GRAY)
    contrasted = apply_clahe(gray)

    print(f"[3/3] Writing {output_path} ...")
    Image.fromarray(contrasted).save(output_path)
    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <source-photo> [output.png]")
        sys.exit(1)

    src = Path(sys.argv[1])
    if not src.exists():
        print(f"Error: {src} not found")
        sys.exit(1)

    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("source-prepped.png")
    prep(src, out)
