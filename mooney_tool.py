"""Mooney image generator (CLI, batch capable).

Gaussian blur followed by a global threshold that is found by binary search so that a
fixed percentage of pixels ends up white (Egger et al., "Inverse Rendering Best Explains
Face Perception Under Extreme Illuminations").

Examples:
    python mooney_tool.py photo.jpg out/ --white 16
    python mooney_tool.py Original/ Mooney/ --white 35 --blur-rel 0.04 --log params.csv
"""
import argparse
import csv
from pathlib import Path

import cv2
import numpy as np

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def kernel_size(h: int, w: int, blur_rel: float) -> int:
    k = int(round(blur_rel * min(h, w)))
    return max(1, k + (1 if k % 2 == 0 else 0))


def white_threshold(img: np.ndarray, white_frac: float, iters: int = 50) -> float:
    lo, hi = float(img.min()) - 1e-3, float(img.max())
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if (img > mid).mean() > white_frac:
            lo = mid
        else:
            hi = mid
    return hi


def fill_ties(mask: np.ndarray, blurred: np.ndarray, gray: np.ndarray, target: int, k: int) -> int:
    """Pixels with identical blurred values can make the exact white count unreachable by any threshold.
    Fill the shortfall from the tied pixels at the boundary, ranked by brightness in a wider blur."""
    deficit = target - int(mask.sum())
    if deficit <= 0:
        return 0
    tied = np.flatnonzero((blurred == blurred[~mask].max()) & ~mask)
    wide = cv2.blur(gray, (3 * k, 3 * k)).ravel()[tied]
    mask.flat[tied[np.argsort(-wide, kind="stable")[:deficit]]] = True
    return deficit


def make_mooney(image: np.ndarray, white_pct: float = 16.0, blur_rel: float = 0.028,
                sigma: float = 35.0, ksize: int = 0, invert: bool = False):
    """Return (mooney uint8 image, parameter dict). `image` is BGR or grayscale."""
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = gray.astype(np.float32)
    k = ksize if ksize > 0 else kernel_size(gray.shape[0], gray.shape[1], blur_rel)
    if k % 2 == 0:
        k += 1
    # With sigma >> ksize (paper: 7x7, sigma=35) this is close to a box blur of size k.
    blurred = cv2.GaussianBlur(gray, (k, k), sigma) if k > 1 else gray
    t = white_threshold(blurred, white_pct / 100.0)
    white = blurred > t
    tie_filled = fill_ties(white, blurred, gray, int(np.floor(white.size * white_pct / 100.0 + 1e-6)), k)
    mooney = np.where(white, 255, 0).astype(np.uint8)
    if invert:
        mooney = 255 - mooney
    info = {
        "ksize": k,
        "sigma": sigma,
        "threshold": round(t, 3),
        "white_pct_target": white_pct,
        "white_pct_actual": round(100.0 * float((mooney > 0).mean()), 2),
        "tie_filled_px": tie_filled,
        "inverted": invert,
    }
    return mooney, info


def iter_images(path: Path):
    if path.is_file():
        return [path]
    return sorted(p for p in path.iterdir() if p.suffix.lower() in IMAGE_EXTS)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate Mooney images (blur + white-pixel-percentage threshold).")
    ap.add_argument("input", type=Path, help="image file or folder of images")
    ap.add_argument("output", type=Path, help="output folder (PNG files, same stem as input)")
    ap.add_argument("--white", type=float, default=16.0,
                    help="percentage of white pixels, 0-100 (default 16, as in Egger et al.)")
    ap.add_argument("--blur-rel", type=float, default=0.028,
                    help="blur strength: kernel size as fraction of the shorter image side (7px @ 250px = 0.028)")
    ap.add_argument("--ksize", type=int, default=0, help="absolute kernel size in px (overrides --blur-rel)")
    ap.add_argument("--sigma", type=float, default=35.0, help="Gaussian sigma (default 35, as in the paper)")
    ap.add_argument("--invert", action="store_true", help="flip contrast polarity")
    ap.add_argument("--log", type=Path, help="optional CSV file recording the parameters per image")
    a = ap.parse_args(argv)

    if not 0 < a.white < 100:
        ap.error("--white must be between 0 and 100")
    if not a.input.exists():
        ap.error(f"input not found: {a.input}")
    files = iter_images(a.input)
    if not files:
        ap.error(f"no images found in {a.input}")
    a.output.mkdir(parents=True, exist_ok=True)

    rows = []
    for i, f in enumerate(files, 1):
        img = cv2.imread(str(f), cv2.IMREAD_COLOR)
        if img is None:
            print(f"[{i}/{len(files)}] skipped unreadable file {f.name}")
            continue
        mooney, info = make_mooney(img, a.white, a.blur_rel, a.sigma, a.ksize, a.invert)
        cv2.imwrite(str(a.output / f"{f.stem}.png"), mooney)
        rows.append({"file": f.name, **info})
        print(f"[{i}/{len(files)}] {f.name}: k={info['ksize']} white={info['white_pct_actual']:.1f}%")

    if a.log and rows:
        a.log.parent.mkdir(parents=True, exist_ok=True)
        with open(a.log, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    print(f"Done: {len(rows)} Mooney images written to {a.output}")


if __name__ == "__main__":
    main()
