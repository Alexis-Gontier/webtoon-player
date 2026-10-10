"""Repère le texte français nettement plus petit que le lettrage anglais de la même bulle.

  python scripts/audit_render.py N [N ...]

Compare, pour chaque entrée rendue, la hauteur d'une capitale française (taille du journal
inventaire/chN/rendu.log × proportion de la police) à la hauteur de ligne anglaise lue par l'OCR
(inventaire.json, "line_h"). Sous SEUIL, l'entrée est listée et recadrée dans
inventaire/chN/tailles.png (anglais | français), à regarder avant de corriger.
Correction habituelle : voir « Méthode de correction » dans docs/translation-reference.md.
"""

import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import translate_bubbles as tb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SEUIL = 0.6
LOG_LINE = re.compile(r"\s+(?:box \[\d+, \d+\]|\(\d+, \d+\)) (\S+) (\d+)px #(\d+) : (.*)")


def cap_ratio(style_name):
    fonts = tb.get_fonts(tb.STYLES[style_name], 100)
    top, bottom = fonts.main.getbbox("H", anchor="ls")[1::2]
    return (bottom - top) / 100


def scan(chapter):
    folder = ROOT / "inventaire" / f"ch{chapter}"
    inventory = json.loads((folder / "inventaire.json").read_text(encoding="utf-8"))
    found, page = [], None
    for line in (folder / "rendu.log").read_text(encoding="utf-8").splitlines():
        if line.startswith("== config_"):
            page = line.split("config_")[1].split(".")[0]
            continue
        m = LOG_LINE.match(line)
        if not m or not page:
            continue
        style, size, bid, text = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
        block = next((b for b in inventory.get(f"{page}.webp", []) if b["id"] == bid), None)
        if not block or block.get("line_h", 0) < 20 or style not in tb.STYLES:
            continue
        ratio = size * cap_ratio(style) / block["line_h"]
        if ratio < SEUIL:
            found.append((page, bid, block["box"], ratio, text))
    return found


def sheet(chapter, found):
    font = ImageFont.truetype("arial.ttf", 16)
    tiles = []
    for page, bid, (x0, y0, x1, y1), ratio, _ in found:
        en = Image.open(ROOT / "chapters_en" / f"chapter-{chapter}" / f"{page}.webp").convert("RGB")
        fr = Image.open(ROOT / "chapters_fr" / f"chapter-{chapter}" / f"{page}.webp").convert("RGB")
        box = (max(0, x0 - 120), max(0, y0 - 120), min(en.width, x1 + 120), min(en.height, y1 + 120))
        tile = Image.new("RGB", ((box[2] - box[0]) * 2 + 6, box[3] - box[1] + 20), (60, 60, 60))
        tile.paste(en.crop(box), (0, 20))
        tile.paste(fr.crop(box), (box[2] - box[0] + 6, 20))
        ImageDraw.Draw(tile).text((2, 1), f"{page}.{bid} {ratio:.0%}", fill="yellow", font=font)
        tile.thumbnail((640, 260))
        tiles.append(tile)
    out = Image.new("RGB", (max(t.width for t in tiles), sum(t.height + 4 for t in tiles)), "white")
    y = 0
    for tile in tiles:
        out.paste(tile, (0, y))
        y += tile.height + 4
    path = ROOT / "inventaire" / f"ch{chapter}" / "tailles.png"
    out.save(path)
    return path


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for chapter in sys.argv[1:]:
        found = scan(chapter)
        for page, bid, _, ratio, text in found:
            print(f"ch{chapter} {page}.{bid} {ratio:.0%} : {text}")
        print(f"ch{chapter} : {len(found)} texte(s) trop petit(s)" + (f" -> {sheet(chapter, found)}" if found else ""))
