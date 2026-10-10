"""Génère viewer.html : chapitre anglais à gauche, français à droite, défilement synchronisé.

Usage : python scripts/make_viewer.py
Puis ouvrir viewer.html (à la racine) dans le navigateur (double-clic).
À relancer après chaque rendu pour mettre à jour la liste des chapitres.
"""

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / "viewer_template.html"


def chapter_data():
    chapters = []
    for fr_dir in sorted((ROOT / "chapters_fr").glob("chapter-*"), key=lambda p: int(p.name.split("-")[1])):
        en_dir = ROOT / "chapters_en" / fr_dir.name
        pages = []
        for fr in sorted(fr_dir.iterdir()):
            en = next(en_dir.glob(fr.stem + ".*"), None)
            if not en:
                continue
            width, height = Image.open(fr).size
            pages.append({
                "name": fr.stem,
                "en": en.relative_to(ROOT).as_posix(),
                "fr": fr.relative_to(ROOT).as_posix(),
                "w": width,
                "h": height,
            })
        chapters.append({"name": fr_dir.name.split("-")[1], "pages": pages})
    return chapters


def main():
    template = TEMPLATE.read_text(encoding="utf-8")
    data = json.dumps(chapter_data(), ensure_ascii=False)
    (ROOT / "viewer.html").write_text(template.replace("/*DATA*/[]", data), encoding="utf-8")
    print("viewer.html généré")


if __name__ == "__main__":
    main()
