"""Native-resolution Mooney generator. CLI supports one image or any batch size.

Examples:
  python mooney_tool.py Original/ Mooney/ --white 28 --sigma 8 --log params.csv
  python mooney_tool.py Original/ Mooney/ --params settings.csv --log actual.csv

settings.csv columns: file, white_pct, sigma. Kernel spans +/-3 sigma.
Images are never resized. White percentage is controlled independently of blur.
"""
import argparse
import csv
import math
from pathlib import Path
import cv2
import numpy as np

EXTENSIONS = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.webp'}


def make_mooney(image, white_pct=28., sigma=8.):
    """Gaussian blur, global brightness threshold, deterministic boundary ties.

    A fractional percentage implies floor(N*p/100) white pixels. If identical
    intensities straddle the threshold, ties are ordered by a broader blur and
    then image coordinates. The log reports how many tied pixels were filled.
    """
    if not np.isfinite(white_pct) or not 0 < white_pct < 100:
        raise ValueError('white percentage must be finite and between 0 and 100')
    if not np.isfinite(sigma) or not 0 <= sigma <= 200:
        raise ValueError('sigma must be finite and between 0 and 200 pixels')
    if image is None or image.size == 0:
        raise ValueError('image is empty or unreadable')
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = gray.astype(np.float32)
    k = 2 * math.ceil(3 * sigma) + 1
    blurred = cv2.GaussianBlur(gray, (k, k), sigma) if sigma else gray
    target = int(np.floor(gray.size * white_pct / 100 + 1e-6))
    if not 0 < target < gray.size:
        raise ValueError('image is too small for the requested percentage')
    threshold = float(np.partition(blurred.ravel(), -target)[-target])
    mask = blurred > threshold
    deficit = target - int(mask.sum())
    ties = np.flatnonzero(blurred.ravel() == threshold)
    if deficit:
        broad = cv2.GaussianBlur(gray, (2 * k + 1, 2 * k + 1), max(1., 2 * sigma))
        order = np.argsort(-broad.ravel()[ties], kind='stable')
        mask.ravel()[ties[order[:deficit]]] = True
    result = mask.astype(np.uint8) * 255
    return result, {'width': gray.shape[1], 'height': gray.shape[0],
        'sigma': float(sigma), 'ksize': k, 'white_pct_target': float(white_pct),
        'white_pct_actual': float(mask.mean() * 100), 'threshold': threshold,
        'boundary_tied_pixels': len(ties), 'boundary_filled_pixels': deficit}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('input', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--white', type=float, default=28., help='white pixels in percent')
    ap.add_argument('--sigma', type=float, default=8., help='Gaussian blur sigma in native pixels; 0 disables blur')
    ap.add_argument('--params', type=Path, help='per-image CSV overrides: file,white_pct,sigma')
    ap.add_argument('--log', type=Path, help='CSV containing actual parameters')
    args = ap.parse_args(argv)
    if not args.input.exists(): ap.error('input does not exist')
    files = [args.input] if args.input.is_file() else sorted(p for p in args.input.iterdir() if p.suffix.lower() in EXTENSIONS)
    if not files: ap.error('no supported images')
    if len({p.stem for p in files}) != len(files): ap.error('input stems must be unique')
    if args.input.resolve() == args.output.resolve(): ap.error('input and output must be different')
    settings = {}
    if args.params:
        with args.params.open(newline='') as fh:
            for row in csv.DictReader(fh):
                if row['file'] in settings: ap.error('duplicate file in parameters CSV')
                settings[row['file']] = row
        if set(settings) != {p.name for p in files}: ap.error('parameters CSV must cover exactly the input files')
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, path in enumerate(files, 1):
        row = settings.get(path.name, {})
        try:
            result, info = make_mooney(cv2.imread(str(path), cv2.IMREAD_COLOR),
                float(row.get('white_pct', args.white)), float(row.get('sigma', args.sigma)))
        except ValueError as error: ap.error(f'{path.name}: {error}')
        target = args.output / (path.stem + '.png')
        if not cv2.imwrite(str(target), result): raise OSError(f'could not write {target}')
        rows.append({'file': path.name, **info})
        print(f'[{i:03d}/{len(files)}] {path.name}: {info["width"]}x{info["height"]} sigma={info["sigma"]:g} k={info["ksize"]} white={info["white_pct_actual"]:.3f}%', flush=True)
    if args.log:
        args.log.parent.mkdir(parents=True, exist_ok=True)
        with args.log.open('w', newline='') as fh:
            writer = csv.DictWriter(fh, fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
    print(f'Done: {len(rows)} images; native dimensions preserved.')


if __name__ == '__main__':
    main()
