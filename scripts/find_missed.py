"""Cherche le texte anglais oublié : zones de texte de la page anglaise restées intactes en français.

  python scripts/find_missed.py N [N ...]

L'OCR de l'inventaire rate les lettrages stylisés (pinceau, lettres blanches cernées, texte pâle) et
le contrôle de `build` ignore les textes courts : « YEAH! », « NOW! », « SOUL SWORD... » (ch. 227-243)
n'avaient jamais été signalés. Ici un détecteur de texte (PP-OCRv3, models/text_detection_en_ppocrv3.onnx,
opencv/text_detection_ppocr sur Hugging Face) repère les zones de texte sans les lire ; on garde celles
que le rendu n'a pas touchées, puis on les relit par OCR pour écarter le dessin et le coréen.
Résultat : liste dans le terminal et planche inventaire/chN/oublis.png (anglais | français).
Bruit attendu : filigranes et crédits de scan, logo PLAYER, noms seuls, « PRAISE GOD » dessiné.
"""

import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np
import winocr
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
DETECTOR = ROOT / "models" / "text_detection_en_ppocrv3.onnx"
# Filigranes, crédits et annonces de la team de scan, logo de fin de chapitre.
NOISE = re.compile(r"SCAN|\.COM|DISCORD|HTTP|Ifi1|SSf11|Hyeon|Jong|READ|PLAYER|PUVER|RAYER|AHol|EFcl|HHO"
                   r"|CHAPTER|CHAPIER|SUPPORT|UNLOCK|DIVE DEEPER|STORM", re.I)


def detector():
    model = cv2.dnn_TextDetectionModel_DB(cv2.dnn.readNet(str(DETECTOR)))
    model.setBinaryThreshold(0.3)
    model.setPolygonThreshold(0.5)
    model.setUnclipRatio(2.0)
    model.setMaxCandidates(200)
    model.setInputSize((800, 800))
    model.setInputMean((123.675, 116.28, 103.53))
    model.setInputScale(1.0 / 255.0 / np.array([0.229, 0.224, 0.225]))
    return model


def detect(model, page):
    """Boîtes de texte [x0, y0, x1, y1] de la page, lue par tuiles de 800 px qui se chevauchent."""
    boxes = []
    for top in range(0, page.shape[0], 700):
        tile = np.zeros((800, 800, 3), np.uint8)
        part = page[top:top + 800, :800]
        tile[:part.shape[0], :part.shape[1]] = part
        polys, _ = model.detect(cv2.cvtColor(tile, cv2.COLOR_RGB2BGR))
        for poly in polys:
            poly = np.array(poly)
            (x0, y0), (x1, y1) = poly.min(0), poly.max(0)
            boxes.append([max(0, int(x0)), max(0, int(y0) + top), min(page.shape[1], int(x1)),
                          min(page.shape[0], int(y1) + top)])
    return boxes


def read(crop):
    """Meilleure lecture OCR entre l'image, son négatif et une version contrastée (lettres claires)."""
    best = ""
    for variant in (crop, ImageOps.invert(crop), ImageOps.autocontrast(ImageOps.grayscale(crop), cutoff=5).convert("RGB")):
        variant = variant.resize((variant.width * 2, variant.height * 2))
        text = " ".join(line["text"] for line in winocr.recognize_pil_sync(variant, "fr-FR")["lines"])
        if len(re.findall(r"[A-Za-z]", text)) > len(re.findall(r"[A-Za-z]", best)):
            best = text
    return best


def letters(text):
    """Comme auto_translate.letters : lettres seules, en capitales."""
    return re.sub(r"[^A-ZÀ-Ÿ]", "", text.upper())


def bubble_lettering(page, x0, y0, x1, y1):
    """Lettres sombres sur fond clair (bulle) : signalées même si l'OCR ne lit rien.

    Le lettrage au feutre condensé (« OY! TAKE IT! », « HOW DARE YOU INSULT ME?! », ch. 238) donne
    une lecture vide alors que le détecteur l'a bien trouvé.
    """
    m = 14
    h, w = page.shape[:2]
    # Une ligne de lettrage est large ; les petites zones carrées sont des onomatopées ou du dessin.
    if x1 - x0 < 100 or (x1 - x0) < 1.8 * (y1 - y0) or x0 < 15 or x1 > w - 15:
        return False
    a, b, c, d = max(0, x0 - m), max(0, y0 - m), min(w, x1 + m), min(h, y1 + m)
    gray = page[b:d, a:c].mean(axis=2)
    ring = np.concatenate([gray[:m].ravel(), gray[-m:].ravel(), gray[:, :m].ravel(), gray[:, -m:].ravel()])
    ink = (page[y0:y1, x0:x1].mean(axis=2) < 90).mean()
    return (ring > 215).mean() > 0.9 and 0.04 < ink < 0.45


def ignored_boxes(chapter, page_name):
    """Blocs de l'inventaire laissés d'origine exprès : marqués '-' dans le txt (crédits, bruit), ou
    texte identique à l'anglais sans réglage JSON (« MIRAGE...! », gardé tel quel par le moteur)."""
    inventory = ROOT / "inventaire" / f"ch{chapter}" / "inventaire.json"
    txt = ROOT / "translations" / f"ch{chapter}_fr.txt"
    if not inventory.exists() or not txt.exists():
        return []
    rows = {}
    for line in txt.read_text(encoding="utf-8").splitlines():
        if line.count(" | ") >= 2 and not line.startswith("#"):
            key, opts, text = line.split(" | ", 2)
            rows[key.strip()] = (opts.strip(), text.strip())
    blocks = json.loads(inventory.read_text(encoding="utf-8")).get(page_name, [])
    kept = []
    for b in blocks:
        opts, text = rows.get(f"{page_name[:3]}.{b['id']}", ("", ""))
        same = " " not in opts and len(letters(text)) >= 2 and letters(text) == letters(b["text"])
        if text == "-" or same:
            kept.append(b["box"])
    return kept


def scan(chapter, model):
    found = []
    for en_path in sorted((ROOT / "chapters_en" / f"chapter-{chapter}").iterdir()):
        fr_path = ROOT / "chapters_fr" / f"chapter-{chapter}" / en_path.name
        en = np.array(Image.open(en_path).convert("RGB"))
        fr = np.array(Image.open(fr_path).convert("RGB")) if fr_path.exists() else en
        if fr.shape != en.shape:
            continue
        skip = ignored_boxes(chapter, en_path.name)
        seen = set()
        for x0, y0, x1, y1 in detect(model, en):
            if x1 - x0 < 20 or y1 - y0 < 10 or y0 // 60 in seen:
                continue
            # Zone retouchée par le rendu : déjà traduite.
            diff = np.abs(en[y0:y1, x0:x1].astype(int) - fr[y0:y1, x0:x1].astype(int)).max(axis=2)
            if (diff < 15).mean() < 0.9:
                continue
            if any(not (x1 < a - 20 or x0 > c + 20 or y1 < b - 20 or y0 > d + 20) for a, b, c, d in skip):
                continue
            text = read(Image.fromarray(en[y0:y1, x0:x1]))
            if not re.search(r"[A-Za-z]{3,}", text) and bubble_lettering(en, x0, y0, x1, y1):
                text = f"(illisible, bulle) {text}".strip()
            if re.search(r"[A-Za-z]{3,}", text) and not NOISE.search(text):
                seen.add(y0 // 60)
                found.append((en_path.name, [x0, y0, x1, y1], text))
    return found


def sheet(chapter, found):
    font = ImageFont.truetype("arial.ttf", 16)
    tiles = []
    for name, (x0, y0, x1, y1), _ in found:
        en = Image.open(ROOT / "chapters_en" / f"chapter-{chapter}" / name).convert("RGB")
        fr = Image.open(ROOT / "chapters_fr" / f"chapter-{chapter}" / name).convert("RGB")
        box = (max(0, x0 - 60), max(0, y0 - 60), min(en.width, x1 + 60), min(en.height, y1 + 60))
        tile = Image.new("RGB", ((box[2] - box[0]) * 2 + 6, box[3] - box[1] + 20), (60, 60, 60))
        tile.paste(en.crop(box), (0, 20))
        tile.paste(fr.crop(box), (box[2] - box[0] + 6, 20))
        ImageDraw.Draw(tile).text((2, 1), f"{name[:3]} {[x0, y0, x1, y1]}", fill="yellow", font=font)
        tile.thumbnail((700, 260))
        tiles.append(tile)
    out = Image.new("RGB", (max(t.width for t in tiles), sum(t.height + 4 for t in tiles)), "white")
    y = 0
    for tile in tiles:
        out.paste(tile, (0, y))
        y += tile.height + 4
    path = ROOT / "inventaire" / f"ch{chapter}" / "oublis.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path)
    return path


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    model = detector()
    for chapter in sys.argv[1:]:
        found = scan(chapter, model)
        for name, box, text in found:
            print(f"ch{chapter} {name[:3]} {box} {text}")
        print(f"ch{chapter} : {len(found)} zone(s) à regarder" + (f" -> {sheet(chapter, found)}" if found else ""))
