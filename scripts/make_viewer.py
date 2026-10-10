"""Génère les données du lecteur.

- site/src/data/chapters.json et site/public/thumbs/N.webp pour le site Astro (dossier site/) ;
- viewer.html (ancien lecteur, gardé tant que le site n'est pas validé).

Usage : python scripts/make_viewer.py
À relancer après chaque rendu pour mettre à jour la liste des chapitres.
"""

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / "viewer_template.html"
THUMB_SIZE = (400, 560)


def chapter_data(root=ROOT):
    chapters = []
    for fr_dir in sorted((root / "chapters_fr").glob("chapter-*"), key=lambda p: int(p.name.split("-")[1])):
        en_dir = root / "chapters_en" / fr_dir.name
        pages = []
        for fr in sorted(fr_dir.iterdir()):
            en = next(en_dir.glob(fr.stem + ".*"), None)
            if not en:
                continue
            width, height = Image.open(fr).size
            pages.append({
                "name": fr.stem,
                "en": en.relative_to(root).as_posix(),
                "fr": fr.relative_to(root).as_posix(),
                "w": width,
                "h": height,
            })
        chapters.append({"name": fr_dir.name.split("-")[1], "pages": pages})
    return chapters


def site_data(chapters):
    # Format de la collection Astro : un id texte par entrée (file() loader).
    return [{"id": c["name"], "n": int(c["name"]), "pages": c["pages"]} for c in chapters if c["pages"]]


def make_thumb(src, dest):
    # Haut de la première page, au ratio de la vignette ; refait seulement si la page a changé.
    if dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime:
        return
    with Image.open(src) as im:
        width = im.width
        crop = im.convert("RGB").crop((0, 0, width, min(im.height, round(width * THUMB_SIZE[1] / THUMB_SIZE[0]))))
        crop.resize(THUMB_SIZE, Image.LANCZOS).save(dest, "WEBP", quality=80)


def write_site(root, chapters):
    data = site_data(chapters)
    out = root / "site" / "src" / "data" / "chapters.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    thumbs = root / "site" / "public" / "thumbs"
    thumbs.mkdir(parents=True, exist_ok=True)
    for c in data:
        make_thumb(root / c["pages"][0]["fr"], thumbs / f"{c['n']}.webp")


def main():
    chapters = chapter_data()
    write_site(ROOT, chapters)
    template = TEMPLATE.read_text(encoding="utf-8")
    data = json.dumps(chapters, ensure_ascii=False)
    (ROOT / "viewer.html").write_text(template.replace("/*DATA*/[]", data), encoding="utf-8")
    print("site/src/data/chapters.json, vignettes et viewer.html générés")


if __name__ == "__main__":
    main()
