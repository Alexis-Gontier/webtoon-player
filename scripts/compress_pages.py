"""Copies allégées des planches pour git : chapters_en/ et chapters_fr/ -> chapters_web/en|fr/.

WebP qualité 80 : environ 2,3 fois plus léger, sans différence visible. Les originaux ne sont
jamais modifiés (le moteur a besoin des anglais en pleine qualité pour l'OCR et l'effacement).
Incrémental : seules les pages nouvelles ou modifiées sont recompressées, les copies de pages
supprimées sont retirées.

Usage : python scripts/compress_pages.py   (après make_viewer.py, avant de committer)
"""

import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
QUALITY = 80
JPEG_QUALITY = 85  # pages trop hautes pour WebP (ch. 244 p5 et p9)
WEBP_MAX = 16383   # côté maximal d'une image WebP
LANGS = ("en", "fr")


def compress(job):
    src, dest = job
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    with Image.open(src) as im:
        if dest.suffix == ".jpg":
            im.convert("RGB").save(tmp, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        else:
            im.convert("RGB").save(tmp, "WEBP", quality=QUALITY, method=6)
    os.replace(tmp, dest)  # jamais de copie à moitié écrite
    # Même date que l'original : la copie est à jour tant que l'original ne change pas.
    stat = src.stat()
    os.utime(dest, ns=(stat.st_atime_ns, stat.st_mtime_ns))


def jobs(root):
    todo, keep = [], set()
    for lang in LANGS:
        src_dir, out_dir = root / f"chapters_{lang}", root / "chapters_web" / lang
        for src in sorted(src_dir.glob("chapter-*/*")):
            if src.suffix.lower() not in (".webp", ".png", ".jpg", ".jpeg"):
                continue
            with Image.open(src) as im:  # lit seulement l'en-tête
                ext = ".jpg" if max(im.size) > WEBP_MAX else ".webp"
            dest = out_dir / src.parent.name / (src.stem + ext)
            keep.add(dest)
            if not dest.exists() or dest.stat().st_mtime_ns != src.stat().st_mtime_ns:
                todo.append((src, dest))
    return todo, keep


def compress_all(root=ROOT):
    todo, keep = jobs(root)
    if len(todo) > 8:
        with ProcessPoolExecutor() as pool:
            list(pool.map(compress, todo, chunksize=4))
    else:
        for job in todo:
            compress(job)
    for old in (root / "chapters_web").glob("*/chapter-*/*"):
        if old not in keep:
            old.unlink()
    return len(todo)


def main():
    n = compress_all()
    size = sum(f.stat().st_size for f in (ROOT / "chapters_web").rglob("*.*"))
    print(f"{n} page(s) compressée(s) ; chapters_web/ : {size / 1e6:.0f} Mo")


if __name__ == "__main__":
    main()
