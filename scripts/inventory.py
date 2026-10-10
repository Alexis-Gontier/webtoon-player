"""Repérage des textes anglais par OCR (moteur intégré à Windows), utilisé par auto_translate.py.

Lignes OCR d'une page, regroupement en blocs, bulles sans texte lu, type de bloc ("bulle" ou "dessin").
L'OCR sert à localiser : le texte lu peut contenir des fautes, toujours relire la planche.
"""

import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np
import winocr
from PIL import Image, ImageDraw, ImageFont

import translate_bubbles as tb

ROOT = Path(__file__).parent
STRIP = 2000
OVERLAP = 300
SKIP = re.compile(r"VORTEX|SCANS|READ THIS SERIES", re.I)


def ocr_lines(page):
    """Lignes OCR de la page entière (lue par bandes qui se chevauchent), en coordonnées de page."""
    lines = []
    for top in range(0, page.height, STRIP - OVERLAP):
        strip = page.crop((0, top, page.width, min(page.height, top + STRIP)))
        for line in winocr.recognize_pil_sync(strip, "fr-FR")["lines"]:
            rects = [w["bounding_rect"] for w in line["words"]]
            x0 = min(r["x"] for r in rects)
            y0 = min(r["y"] for r in rects) + top
            x1 = max(r["x"] + r["width"] for r in rects)
            y1 = max(r["y"] + r["height"] for r in rects) + top
            text = line["text"].strip()
            # Doublons dus au chevauchement des bandes.
            if any(abs(l["box"][1] - y0) < 15 and abs(l["box"][0] - x0) < 25 for l in lines):
                continue
            lines.append({"text": text, "box": [int(x0), int(y0), int(x1), int(y1)]})
        if top + STRIP >= page.height:
            break
    return sorted(lines, key=lambda l: l["box"][1])


def group_blocks(lines):
    """Regroupe les lignes proches (même bulle) en blocs."""
    blocks = []
    for line in lines:
        x0, y0, x1, y1 = line["box"]
        h = y1 - y0
        for block in blocks:
            bx0, by0, bx1, by1 = block["box"]
            if y0 - by1 < 1.3 * h + 8 and x0 < bx1 + 20 and x1 > bx0 - 20:
                block["box"] = [min(bx0, x0), by0, max(bx1, x1), max(by1, y1)]
                block["text"] += " " + line["text"]
                break
        else:
            blocks.append({"text": line["text"], "box": list(line["box"])})
    # Bruit : onomatopées coréennes mal lues, filigrane du site.
    return [b for b in blocks if len(re.findall(r"[A-Za-z]", b["text"])) >= 2 and not SKIP.search(b["text"])]


def missing_bubbles(page, blocks):
    """Bulles que l'OCR a ratées : zones blanches fermées (ni bord gauche ni bord droit) assez grandes,
    contenant de l'encre sombre, sans aucun bloc détecté à l'intérieur."""
    gray = np.array(page.convert("L"))
    white = (gray > tb.WHITE_THRESHOLD).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(white, connectivity=4)
    found = []
    for i in range(1, count):
        x, y, w, h, area = stats[i]
        if area < 6000 or x == 0 or x + w >= page.width or w > 0.95 * page.width or h > 1200:
            continue
        if any(x <= b["point"][0] <= x + w and y <= b["point"][1] <= y + h for b in blocks):
            continue
        # Encre à l'intérieur de la silhouette (trous de la zone blanche = lettres).
        sub = labels[y:y + h, x:x + w] == i
        holes = (~sub) & (gray[y:y + h, x:x + w] < 100)
        rows = np.nonzero(sub.any(axis=1))[0]
        inside = np.zeros_like(sub)
        for r in rows:
            cols = np.nonzero(sub[r])[0]
            inside[r, cols.min():cols.max() + 1] = True
        ink = holes & inside
        if ink.sum() < 150 or w < 80 or h < 60:
            continue
        # Une bulle est presque convexe ; le blanc d'un dessin est déchiqueté.
        contours, _ = cv2.findContours(inside.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        hull = cv2.contourArea(cv2.convexHull(max(contours, key=cv2.contourArea)))
        if inside.sum() / max(hull, 1) < 0.9:
            continue
        # Bord : l'anneau juste autour de la silhouette doit être sombre (le contour de la bulle).
        ring = cv2.dilate(inside.astype(np.uint8), np.ones((9, 9), np.uint8)) - inside.astype(np.uint8)
        border = gray[y:y + h, x:x + w][ring[:h, :w] > 0] if ring.shape == sub.shape else None
        if border is None or (border < 110).mean() < 0.6:
            continue
        # Texte : plusieurs petits traits (des lettres), pas une seule grande tache.
        n, _, letter_stats, _ = cv2.connectedComponentsWithStats(ink.astype(np.uint8))
        letters = [s for s in letter_stats[1:] if 30 <= s[4] and s[3] < 90]
        if len(letters) < 3:
            continue
        ys, xs = np.nonzero(ink)
        found.append({"text": "(non lu par l'OCR)", "box": [int(x + xs.min()), int(y + ys.min()),
                                                             int(x + xs.max()), int(y + ys.max())]})
    return found


def kind(page, block):
    """'bulle' si le centre du bloc est dans une zone blanche fermée, sinon 'dessin' (mode box)."""
    x0, y0, x1, y1 = block["box"]
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    box = (0, max(0, cy - tb.CROP_RADIUS), page.width, min(page.height, cy + tb.CROP_RADIUS))
    try:
        tb.bubble_mask(page.crop(box), (cx, cy - box[1]), close=1)
        return "bulle"
    except ValueError:
        try:
            tb.bubble_mask(page.crop(box), (cx, cy - box[1]), close=1, page_edge=True)
            return "bulle"
        except ValueError:
            return "dessin"
