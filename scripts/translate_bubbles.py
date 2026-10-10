"""Remplace le texte de bulles, bulle par bulle.

Usage : python scripts/translate_bubbles.py <config.json> [<config.json> ...]

Le fichier de configuration indique l'image source (toujours l'original
anglais), l'image de sortie et, pour chaque bulle :
  - "point" : un point à l'intérieur de la bulle, près du texte ;
  - "text"  : le texte français (\\n impose une coupure de ligne) ;
  - "style" : dialogue (défaut), italique, pensee, cri, chuchotement, systeme ou titre ;
  - "cut"   : optionnel, [[x1, y1], [x2, y2]] sépare deux bulles qui se touchent ;
  - "max_size" : optionnel, taille de police maximale.
Pour un texte posé sur le dessin, sans bulle : "box" [x0, y0, x1, y1] à la place de "point",
avec en option "outline" (couleur du liseré), "grow" (marge d'effacement) et "colors" (dégradé).
Seul l'intérieur de la bulle est nettoyé : le contour, la queue et le fond
de la page restent intacts.
Toutes les options (box, light, thick, outlined, target, stretch...) : docs/translation-reference.md.
"""

import heapq
import json
import os
import re
import sys
from itertools import combinations
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cv2
import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "fonts"
# Polices choisies pour ressembler au lettrage de la version anglaise (voir docs/translation-reference.md).
STYLES = {
    "dialogue": {"font": FONTS / "AnimeAce2-Regular-FR.ttf", "stroke": 1, "max_size": 48},
    "italique": {"font": FONTS / "AnimeAce2-Italic-FR.ttf", "stroke": 1, "max_size": 44},
    "pensee": {"font": FONTS / "AnimeAce2-Italic-FR.ttf", "stroke": 1, "max_size": 44},
    "cri": {"font": FONTS / "MouseMemoirs-Regular.ttf", "line_spacing": 1.0, "max_size": 130},
    "chuchotement": {"font": FONTS / "AnimeAce2-Regular-FR.ttf", "max_size": 28},
    "systeme": {"font": FONTS / "Anton-Regular.ttf", "max_size": 200},
    "titre": {"font": FONTS / "MetalMania-Regular.ttf", "max_size": 200},
    # Fiches d'information sans bulle en capitales fines et condensées (ex. « EGO WEAPON », ch. 225).
    "cartouche": {"font": FONTS / "Oswald[wght].ttf", "weight": 300, "max_size": 200},
}
REQUIRED_CHARS = "ÉÈÊËÀÂÇÙÛÎÏÔŒ’?!.,:;\u00a0-"
WHITE_THRESHOLD = 200
OUTLINE_MARGIN = 6
TEXT_MARGIN = 0.82
LINE_SPACING = 1.25
MIN_FONT_SIZE = 18
# Coupures imposées (\n) abandonnées si un découpage automatique donne un texte au moins 25 % plus grand.
REWRAP_GAIN = 1.25
# Centrage sur le texte anglais abandonné s'il rapetisse le texte sous cette part de la taille centrée.
# Bulle coupée par le haut ou le bas de la page : seuil plus bas, le centre de la moitié visible
# met le texte 40 px trop bas une fois les pages recollées (ch. 239 p. 19).
INK_CENTRE_KEEP = 0.9
INK_CENTRE_KEEP_EDGE = 0.75
CROP_RADIUS = 450
MIN_BUBBLE_SIZE = 90
COLOR_SATURATION = 50
NBSP = "\u00a0"
FALLBACK_FONT = r"C:\Windows\Fonts\seguisym.ttf"


def check_fonts():
    """Refuse toute police à laquelle il manque un caractère français."""
    for name, style in STYLES.items():
        if not Path(style["font"]).exists():
            raise SystemExit(f"Police du style {name!r} introuvable : {style['font']}")
        cmap = TTFont(style["font"]).getBestCmap()
        missing = [c for c in REQUIRED_CHARS if ord(c) not in cmap]
        if missing:
            raise SystemExit(f"Police du style {name!r} incomplète, manque : {''.join(missing)!r}")


def white_seeds(gray, x, y, radius=160):
    """Pixels blancs autour du point, du plus proche au plus lointain."""
    for r in range(0, radius, 3):
        for dx, dy in ((r, 0), (-r, 0), (0, r), (0, -r), (r, r), (-r, -r), (r, -r), (-r, r)):
            px, py = x + dx, y + dy
            if 0 <= px < gray.width and 0 <= py < gray.height and gray.getpixel((px, py)) > WHITE_THRESHOLD:
                yield px, py


def flood_bubble(binary, seed, page_edge=False):
    """Remplit depuis le premier pixel blanc qui donne une zone assez grande pour être une bulle
    (et pas l'intérieur d'une lettre comme le creux d'un O).
    page_edge : bulle coupée par le bord gauche ou droit de l'image ; le bord sert de contour,
    mais la zone ne doit alors pas toucher à la fois le haut et le bas du recadrage (ce serait le fond)."""
    if page_edge:
        binary = binary.copy()
        draw = ImageDraw.Draw(binary)
        draw.rectangle((0, 0, 2, binary.height), fill=0)
        draw.rectangle((binary.width - 3, 0, binary.width, binary.height), fill=0)
    for px, py in white_seeds(binary, *seed):
        if binary.getpixel((px, py)) != 255:
            continue
        region = binary.copy()
        ImageDraw.floodfill(region, (px, py), 128)
        region = region.point(lambda v: 255 if v == 128 else 0)
        box = region.getbbox()
        if box and box[2] - box[0] >= MIN_BUBBLE_SIZE and box[3] - box[1] >= MIN_BUBBLE_SIZE:
            # Une zone qui touche les côtés du recadrage a fui hors de la bulle
            # (contour ouvert, par exemple par une onomatopée cernée de blanc).
            if box[0] == 0 or box[2] == binary.width or (page_edge and box[1] == 0 and box[3] == binary.height):
                raise ValueError("la bulle fuit vers le fond (contour ouvert) ; ajouter un \"cut\"")
            return region
    raise ValueError(f"Aucune bulle trouvée près de {seed}")


def span_fill(region):
    """Remplit chaque ligne et chaque colonne entre ses pixels extrêmes, puis garde l'intersection :
    donne la silhouette pleine de la bulle sans les recoins enfermés à l'extérieur."""
    width, height = region.size
    data = region.tobytes()
    rows = bytearray(width * height)
    cols = bytearray(width * height)
    for y in range(height):
        line = data[y * width:(y + 1) * width]
        left = line.find(b"\xff")
        if left >= 0:
            right = line.rfind(b"\xff")
            rows[y * width + left:y * width + right + 1] = b"\xff" * (right - left + 1)
    transposed = region.transpose(Image.Transpose.TRANSPOSE).tobytes()
    for x in range(width):
        line = transposed[x * height:(x + 1) * height]
        top = line.find(b"\xff")
        if top >= 0:
            bottom = line.rfind(b"\xff")
            for y in range(top, bottom + 1):
                cols[y * width + x] = 255
    rows_img = Image.frombytes("L", region.size, bytes(rows))
    cols_img = Image.frombytes("L", region.size, bytes(cols))
    return ImageChops.multiply(rows_img, cols_img)


def split_region(region, seed, others):
    """Bulles collées (en bonhomme de neige) : si d'autres bulles de la page tombent dans la même
    zone blanche, on la partage par ligne de partage des eaux sur la carte des distances.
    La frontière passe au col, l'endroit le plus étroit entre les bulles."""
    filled = np.array(span_fill(region)) > 0
    h, w = filled.shape
    inside = [(int(px), int(py)) for px, py in others if 0 <= px < w and 0 <= py < h and filled[int(py), int(px)]]
    if not inside:
        return region
    # Inondation depuis chaque point, du plus profond (loin du contour) au moins profond :
    # les fronts de deux bulles se rencontrent au col, là où la distance au contour est minimale.
    dist = cv2.distanceTransform(filled.astype(np.uint8), cv2.DIST_L2, 5)
    labels = np.zeros((h, w), np.int8)
    queue = []
    for i, (px, py) in enumerate([tuple(map(int, seed))] + inside, 1):
        # Le point remonte vers le centre de sa bulle (maximum local de distance) : un point
        # posé près du bord partirait trop tard et la bulle voisine déborderait par le col.
        while True:
            y0, x0 = max(py - 3, 0), max(px - 3, 0)
            window = dist[y0:py + 4, x0:px + 4]
            ny, nx = np.unravel_index(window.argmax(), window.shape)
            if window[ny, nx] <= dist[py, px]:
                break
            px, py = x0 + nx, y0 + ny
        labels[py, px] = i
        heapq.heappush(queue, (-dist[py, px], px, py))
    while queue:
        _, px, py = heapq.heappop(queue)
        label = labels[py, px]
        for nx, ny in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)):
            if 0 <= nx < w and 0 <= ny < h and filled[ny, nx] and not labels[ny, nx]:
                labels[ny, nx] = label
                heapq.heappush(queue, (-dist[ny, nx], nx, ny))
    own = (labels == 1).astype(np.uint8)
    # Retrait de quelques pixels le long de la frontière, comme un "cut".
    own = cv2.erode(own, np.ones((5, 5), np.uint8))
    return ImageChops.multiply(region, Image.fromarray(own * 255))


def bubble_mask(crop, seed, cut=None, opening=None, close=0, color_bg=False, others=(), page_edge=False):
    """Masque de l'intérieur de la bulle, lettres comprises, sans le contour."""
    gray = crop.convert("L")
    binary = gray.point(lambda v: 255 if v > WHITE_THRESHOLD else 0)
    if color_bg:
        # Les traits colorés comptent comme du fond : une lettre qui les touche reste du texte à effacer.
        # À réserver aux bulles dont le contour est refermé par un "cut", sinon la couleur ouvre une brèche.
        binary.paste(255, mask=colored_pixels(crop, grow=False))
    if close:
        # Referme les petites brèches du contour (traits clairs qui le traversent).
        binary = binary.filter(ImageFilter.MinFilter(close * 2 + 1))
    if opening:
        # Détache un trait noir qui entre dans la bulle : sa partie intérieure sera effacée.
        ImageDraw.Draw(binary).line([tuple(p) for p in opening], fill=255, width=7)
    if cut:
        # Sépare deux bulles qui se touchent, ou referme un contour ouvert.
        ImageDraw.Draw(binary).line([tuple(p) for p in cut], fill=0, width=5)

    # Zone blanche reliée au point de départ (l'intérieur moins les lettres).
    region = flood_bubble(binary, seed, page_edge)
    region = split_region(region, seed, others)

    # Extérieur = tout ce qui, hors de cette zone, touche un bord du recadrage.
    outside = ImageChops.invert(region)
    for corner in ((0, 0), (crop.width - 1, 0), (0, crop.height - 1), (crop.width - 1, crop.height - 1)):
        if outside.getpixel(corner) == 255:
            ImageDraw.floodfill(outside, corner, 128)
    interior = outside.point(lambda v: 0 if v == 128 else 255)
    interior = ImageChops.multiply(interior, span_fill(region))

    # Garder une marge pour ne jamais toucher le contour.
    interior = interior.filter(ImageFilter.MinFilter(OUTLINE_MARGIN * 2 + 1))
    return interior, region


def colored_pixels(crop, grow=True):
    """Pixels nettement colorés (traits d'onomatopée...), à ne jamais effacer : le texte est noir."""
    hsv = crop.convert("HSV")
    saturation = hsv.getchannel("S").point(lambda v: 255 if v > COLOR_SATURATION else 0)
    value = hsv.getchannel("V").point(lambda v: 255 if v > 60 else 0)
    colored = ImageChops.multiply(saturation, value)
    return colored.filter(ImageFilter.MaxFilter(5)) if grow else colored


def fill_color(crop, region):
    pixels = [p for p, m in zip(crop.get_flattened_data(), region.get_flattened_data()) if m]
    pixels.sort(key=sum)
    return pixels[len(pixels) // 2]


def lettering_size(crop, mask, color, style, text):
    """Taille de police qui reproduit la hauteur du lettrage anglais de la bulle (ch. 239 : texte
    français deux fois plus petit que l'original dans les grandes bulles), ou None si rien de mesurable."""
    gray = np.array(crop.convert("L"), dtype=np.int16)
    inside = np.array(mask) > 0
    ink = ((np.abs(gray - sum(color) / 3) > 110) & inside).astype(np.uint8)
    # Hauteur des lettres une à une (des lignes serrées se touchent : un profil par lignes les fusionnait).
    n, _, stats, _ = cv2.connectedComponentsWithStats(ink)
    heights = sorted(int(h) for w, h in stats[1:, [cv2.CC_STAT_WIDTH, cv2.CC_STAT_HEIGHT]] if h >= 6 and w < 3 * h)
    if not heights:
        return None
    fonts = get_fonts(style, 100)
    # Ponctuation seule ("...", "!") : hauteur de ces signes ; sinon hauteur d'une capitale.
    sample = text.strip() if not any(c.isalpha() for c in text) else "H"
    box = fonts.main.getbbox(sample, anchor="ls")
    ratio = (box[3] - box[1]) / 100
    # 3e quartile : les capitales pleine hauteur, pas les virgules ni les lettres collées entre elles.
    measured = max(heights) if sample != "H" else heights[len(heights) * 3 // 4]
    return max(MIN_FONT_SIZE, min(160, int(measured / ratio)))


def ink_height(crop, mask, color):
    """Hauteur du plus grand tracé du texte original dans la bulle (diamètre des points de "...")."""
    gray = np.array(crop.convert("L"), dtype=np.int16)
    ink = (np.abs(gray - sum(color) / 3) > 110) & (np.array(mask) > 0)
    rows = np.flatnonzero(ink.sum(axis=1) >= 3)
    if not len(rows):
        return 0, None
    cols = np.flatnonzero(ink.any(axis=0))
    return int(rows[-1] - rows[0] + 1), ((cols[0] + cols[-1]) / 2, (rows[0] + rows[-1]) / 2)


def draw_dots(crop, mask, measure, color):
    """Points de suspension seuls : Anime Ace n'a que de petits points carrés, l'original des disques."""
    bbox = mask.getbbox()
    extents = row_extents(mask)
    cy = (bbox[1] + bbox[3]) / 2
    ext = extents[int(cy)]
    cx = (ext[0] + ext[1]) / 2
    diameter, centre = measure
    # Même place que les points d'origine quand on a pu les mesurer.
    if centre:
        cx, cy = centre
    d = diameter or max(10, (bbox[2] - bbox[0]) // 14)
    step = d * 2.2
    draw = ImageDraw.Draw(crop)
    for i in (-1, 0, 1):
        x = cx + i * step
        draw.ellipse((x - d / 2, cy - d / 2, x + d / 2, cy + d / 2), fill=color)
    return d


def row_extents(mask):
    """Pour chaque ligne du masque : (x_min, x_max) ou None."""
    width, height = mask.size
    data = mask.tobytes()
    extents = []
    for y in range(height):
        row = data[y * width:(y + 1) * width]
        left = next((x for x in range(width) if row[x]), None)
        if left is None:
            extents.append(None)
            continue
        right = width - 1 - next(x for x in range(width) if row[width - 1 - x])
        extents.append((left, right))
    return extents


JOIN = "⁠"  # morceau de mot coupé au trait d'union : se recolle sans espace au précédent
NO_HYPHEN_BREAK = {"CE", "IL", "ILS", "ELLE", "ELLES", "ON", "TU", "JE", "NOUS", "VOUS", "LÀ", "CI"}
# Noms propres à trait d'union : jamais coupés (« SEOL- / JIN, », ch. 264 p. 18).
NAMES_NO_BREAK = {"SEOL-JIN", "TAE-WON", "MO-KI-KO", "SANS-NOM"}


def split_words(text):
    """Mots du texte, les mots composés découpés après leurs traits d'union (« PROUVE- », JOIN « LE- »,
    JOIN « MOI. ») : la police française est plus large que le lettrage anglais, et un mot comme
    « PROUVE-LE-MOI. » restait sur une ligne deux fois plus petite (ch. 230 p. 5). Pas de coupure
    autour d'un morceau d'une lettre (A-T-IL, CORPS-À-CORPS, C-C’ÉTAIT)."""
    tokens = []
    for word in text.split(" "):
        if not word:
            continue
        if any(name in word.upper() for name in NAMES_NO_BREAK):
            tokens.append(word)
            continue
        pieces = [word.split("-")[0]]
        for part in word.split("-")[1:]:
            # Ni autour d'une lettre seule, ni devant un pronom inversé (QU’EST-CE, VAS-TU, CELUI-LÀ).
            if (len(re.sub(r"\W", "", pieces[-1].split("-")[-1])) >= 2 and len(re.sub(r"\W", "", part)) >= 2
                    and re.sub(r"\W", "", part) not in NO_HYPHEN_BREAK):
                pieces.append(part)
            else:
                pieces[-1] += "-" + part
        for i, piece in enumerate(pieces):
            tokens.append((JOIN if i else "") + piece + ("-" if i < len(pieces) - 1 else ""))
    return tokens


def wrap_options(words, max_lines=6):
    for n in range(1, min(len(words), max_lines) + 1):
        for cuts in combinations(range(1, len(words)), n - 1):
            bounds = (0, *cuts, len(words))
            yield [" ".join(words[a:b]).replace(" " + JOIN, "").replace(JOIN, "")
                   for a, b in zip(bounds, bounds[1:])]


def prepare_text(text):
    # Espace insécable avant ? ! : ; pour ne jamais rejeter le signe seul en début de ligne.
    # Et avant % : « 100 % » restait coupé sur deux lignes (ch. 264 p. 21).
    for sign in "?!:;%":
        text = text.replace(" " + sign, NBSP + sign)
    return text


class Fonts:
    """Police d'un style à une taille donnée, avec repli pour les symboles absents (♥...)."""

    def __init__(self, style, size):
        path = style["font"]
        self.size = size
        self.main = load_font(style, size)
        self.spacing = style.get("line_spacing", LINE_SPACING)
        self.cmap = TTFont(path).getBestCmap() if str(path) not in CMAPS else CMAPS[str(path)]
        CMAPS[str(path)] = self.cmap
        self.fallback = ImageFont.truetype(FALLBACK_FONT, size)

    def runs(self, line):
        runs = []
        for char in line:
            font = self.main if ord(char) in self.cmap or char == NBSP else self.fallback
            if runs and runs[-1][1] is font:
                runs[-1][0] += char
            else:
                runs.append([char, font])
        return runs

    def length(self, line):
        return sum(font.getlength(text) for text, font in self.runs(line))


CMAPS = {}
FONT_CACHE = {}


def get_fonts(style, size):
    """Les polices chargées sont gardées : la mise en page en essaie des milliers de combinaisons."""
    key = (str(style["font"]), style.get("weight"), size)
    if key not in FONT_CACHE:
        FONT_CACHE[key] = Fonts(style, size)
    return FONT_CACHE[key]


def load_font(style, size):
    font = ImageFont.truetype(str(style["font"]), size)
    if "weight" in style:
        # Police variable : on règle l'axe de graisse, les autres axes gardent leur valeur par défaut.
        values = []
        for axis in font.get_variation_axes():
            name = axis["name"].decode() if isinstance(axis["name"], bytes) else axis["name"]
            values.append(style["weight"] if name.lower() == "weight" else axis["default"])
        font.set_variation_by_axes(values)
    return font


def fits(lines, fonts, extents, cy):
    line_h = fonts.size * fonts.spacing
    top = cy - line_h * len(lines) / 2
    for i, line in enumerate(lines):
        width = fonts.length(line)
        for y in (int(top + i * line_h), int(top + (i + 1) * line_h)):
            # Hors du recadrage : refusé (avant, la ligne était ramenée au bord et passait à tort).
            ext = extents[y] if 0 <= y < len(extents) else None
            if ext is None or width > (ext[1] - ext[0]) * TEXT_MARGIN:
                return False
    return True


def score(lines, fonts, target=0):
    """Plus c'est haut, mieux c'est : grande taille, peu de lignes, pas de mot isolé.
    Sous 80 % de la taille du lettrage anglais ("target"), chaque pixel perdu compte double :
    ch. 231 p. 12, "PAS POSSIBLE !!!" restait sur une ligne en 29 px pour un "NO WAY!!!" de 66 px, et
    ch. 234 p. 4 préférait 3 lignes en 25 px à 5 lignes en 32 px pour un anglais de 37 px (seuil à 65 %)."""
    widths = [fonts.length(l) for l in lines]
    orphans = sum(1 for l in lines if len(lines) > 1 and " " not in l.replace(NBSP, "") and len(l) <= 3)
    balance = (max(widths) - min(widths)) / max(widths)
    hyphens = sum(1 for l in lines[:-1] if l.endswith("-"))
    return (fonts.size - 3 * len(lines) - 10 * orphans - 6 * balance - 4 * hyphens
            - max(0, 0.8 * target - fonts.size))


def layout(text, mask, style, max_size, cy=None):
    bbox = mask.getbbox()
    if bbox is None:
        raise ValueError("masque de bulle vide")
    if cy is None:
        # Centre de masse et pas centre du cadre : la queue de la bulle, fine mais longue, remontait le
        # texte de 70 px (ch. 234 p. 3) ; elle ne pèse presque rien dans la masse.
        cy = float(np.nonzero(np.array(mask))[0].mean())
    extents = row_extents(mask)
    text = prepare_text(text)

    def best_of(options):
        best = None
        for lines in options:
            # Plus grande taille qui tient pour ce découpage.
            lo, hi, found = MIN_FONT_SIZE, max_size, None
            while lo <= hi:
                mid = (lo + hi) // 2
                fonts = get_fonts(style, mid)
                if fits(lines, fonts, extents, cy):
                    found, lo = fonts, mid + 1
                else:
                    hi = mid - 1
            if found:
                s = score(lines, found, max_size)
                if best is None or s > best[0]:
                    best = (s, found, lines)
        return best

    # split(" ") et pas split() : l'espace insécable avant ? ! : ; doit rester collé au signe.
    auto = best_of(wrap_options(split_words(text.replace("\n", " "))))
    best = auto
    if "\n" in text:
        # Les retours à la ligne explicites (\n) sont gardés, sauf s'ils rapetissent nettement le texte :
        # des coupures posées à la main rendaient des bulles minuscules (ch. 229-233, 9-10 octobre).
        manual = best_of([[line.strip(" ") for line in text.split("\n")]])
        if manual and not (auto and auto[1].size >= REWRAP_GAIN * manual[1].size):
            best = manual
    if not best:
        raise ValueError(f"Texte trop long pour la bulle : {text!r}")
    return best[1], best[2], cy, extents


def draw_text(crop, mask, text, style, max_size, color, cy=None):
    fonts, lines, cy, extents = layout(text, mask, style, max_size, cy)
    bbox = mask.getbbox()
    draw = ImageDraw.Draw(crop)
    line_h = fonts.size * fonts.spacing
    top = cy - line_h * len(lines) / 2
    # Centrage sur la hauteur réelle des majuscules : certaines polices ont des métriques très hautes.
    cap_top, cap_bottom = fonts.main.getbbox("H", anchor="ls")[1::2]
    stroke = style.get("stroke", 0)
    for i, line in enumerate(lines):
        y_mid = top + (i + 0.5) * line_h
        baseline = y_mid - (cap_top + cap_bottom) / 2
        ext = extents[int(y_mid)]
        cx = (ext[0] + ext[1]) / 2 if ext else (bbox[0] + bbox[2]) / 2
        x = cx - fonts.length(line) / 2
        for run, font in fonts.runs(line):
            draw.text((x, baseline), run, font=font, fill=color, anchor="ls", stroke_width=stroke, stroke_fill=color)
            x += font.getlength(run)
    return fonts.size, lines


LAMA_MODEL = ROOT / "models" / "lama_fp32.onnx"
_lama_net = None


def lama_fill(page, box, erase):
    """Inpainting LaMa (big-lama en ONNX, huggingface.co/Carve/LaMa-ONNX) : prolonge les hachures
    et les traits du dessin là où cv2.inpaint laissait une tache floue (ch. 227 p. 28).
    Le modèle travaille en 512 × 512 : on lui donne un carré de page centré sur la zone, assez
    grand pour le contexte, et seuls les pixels effacés sont remplacés."""
    global _lama_net
    if _lama_net is None:
        _lama_net = cv2.dnn.readNetFromONNX(str(LAMA_MODEL))
    x0, y0, x1, y1 = box
    # Zone à peu près carrée autour de la boîte, bornée par la page (la boîte peut dépasser le bas
    # de la page ou être plus haute que large : ch. 243 p. 10).
    side = max(x1 - x0, y1 - y0, 512) + 100
    rw, rh = min(side, page.width), min(side, page.height)
    rx = min(max(0, (x0 + x1) // 2 - rw // 2), page.width - rw)
    ry = min(max(0, (y0 + y1) // 2 - rh // 2), page.height - rh)
    region = np.array(page.crop((rx, ry, rx + rw, ry + rh)))
    # Partie commune de la boîte et de la zone, dans les deux repères.
    ox0, oy0, ox1, oy1 = max(x0, rx), max(y0, ry), min(x1, rx + rw), min(y1, ry + rh)
    clean = np.array(page.crop(box))
    if ox0 >= ox1 or oy0 >= oy1:
        return clean
    in_box = (slice(oy0 - y0, oy1 - y0), slice(ox0 - x0, ox1 - x0))
    in_region = (slice(oy0 - ry, oy1 - ry), slice(ox0 - rx, ox1 - rx))
    mask = np.zeros((rh, rw), np.uint8)
    mask[in_region] = erase[in_box]
    _lama_net.setInput(cv2.dnn.blobFromImage(region, 1 / 255, (512, 512)), "image")
    _lama_net.setInput((cv2.dnn.blobFromImage(mask, 1.0, (512, 512)) > 0).astype(np.float32), "mask")
    out = np.clip(_lama_net.forward()[0].transpose(1, 2, 0), 0, 255).astype(np.uint8)
    out = cv2.resize(out, (rw, rh), interpolation=cv2.INTER_CUBIC)
    part, filled, sel = clean[in_box], out[in_region], erase[in_box] > 0
    part[sel] = filled[sel]
    return clean


def free_text(page, item):
    """Texte posé sur le dessin, sans bulle (titres, noms de compétence) : efface les lettres
    par inpainting puis redessine le texte avec le dégradé de couleur de l'original."""
    x0, y0, x1, y1 = item["box"]
    crop = np.array(page.crop((x0, y0, x1, y1)))
    # Encre = pixels nettement plus sombres que le fond clair (les traits cyan très clairs sont exclus).
    ink = (crop.max(axis=2) < item.get("ink_max", 215)).astype(np.uint8) * 255
    if "ink_red_max" in item:
        # Lettres bleu soutenu sur fond bleu clair : seul le canal rouge les distingue.
        ink = ((crop[:, :, 0] < item["ink_red_max"]) & (crop[:, :, 2] > 120)).astype(np.uint8) * 255
    if item.get("light"):
        # Lettres claires sur fond sombre : l'encre est ce qui est plus clair que le seuil.
        ink = (crop.min(axis=2) > item.get("light_min", 190)).astype(np.uint8) * 255
    if item.get("light_any"):
        # Lettres claires mais colorées (dégradé orangé, ch. 252) : le canal le plus fort suffit.
        ink = (crop.max(axis=2) > item["light_any"]).astype(np.uint8) * 255
    if item.get("outlined"):
        # Lettres blanches cernées de sombre sur un ciel clair (ch. 257 p. 1) : le blanc des nuages
        # n'est pas collé à un trait sombre, celui des lettres l'est.
        dark = (crop.max(axis=2) < item.get("ink_max", 90)).astype(np.uint8)
        near = cv2.dilate(dark, np.ones((item["outlined"] * 2 + 1,) * 2, np.uint8))
        white = crop.min(axis=2) > item.get("light_min", 215)
        edge = (dark > 0) & (cv2.dilate(white.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)
        if item.get("outlined_fill"):
            # Lettres noires épaisses cernées de blanc (ch. 231 p. 2) : toute la tache noire bordée
            # de blanc, pas seulement son bord, sinon l'intérieur des lettres reste en fantôme.
            n, labels = cv2.connectedComponents(dark)
            touched = np.zeros(n, bool)
            touched[np.unique(labels[edge])] = True
            # Les traits du dessin collés au liseré traversent la zone, les lettres jamais.
            touched[np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))] = False
            touched[0] = False
            edge = touched[labels]
        ink = ((white & (near > 0)) | edge).astype(np.uint8) * 255
    if item.get("unsat"):
        # Titre blanc cerné de noir posé sur un dessin coloré (ch. 240) : les lettres sont les seuls
        # pixels sans couleur (blancs ou noirs), le décor est saturé.
        sat = crop.max(axis=2).astype(int) - crop.min(axis=2)
        ink = ((sat < item["unsat"]) & (crop.min(axis=2) > item.get("light_min", 170))).astype(np.uint8) * 255
    if item.get("solid"):
        # Lettres blanches cernées de noir sur fond clair : seul le cerne est de l'« encre ».
        # Une fermeture morphologique bouche l'intérieur des lettres, sinon il reste en fantôme.
        size = item["solid"] * 2 + 1
        ink = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, np.ones((size, size), np.uint8))
    if item.get("thick"):
        # Onomatopée géante au pinceau dans une bulle en dents de scie (ch. 245) : une ouverture
        # morphologique ne garde que les traits épais des lettres, le contour fin de la bulle reste.
        size = item["thick"] * 2 + 1
        ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((size, size), np.uint8))
    if item.get("max_letter"):
        # Ne garde que les taches de la taille d'une lettre : le blanc du dessin pris dans la zone
        # (ch. 226, fiches de contrat) ne doit être ni effacé ni compté dans l'emprise du texte.
        n, labels, stats, _ = cv2.connectedComponentsWithStats(ink)
        keep = np.zeros(n, bool)
        keep[1:] = stats[1:, cv2.CC_STAT_HEIGHT] <= item["max_letter"]
        ink = (keep[labels] * 255).astype(np.uint8)
    ys, _ = np.nonzero(ink)
    if not len(ys) and "target" in item and "colors" in item:
        # Zone déjà effacée par une entrée précédente (lignes qui se chevauchent, ch. 226 p. 10) :
        # on pose seulement le texte à l'emplacement "target".
        ys = np.array([0])
    elif not len(ys) and not item["text"].strip():
        # Effacement seul d'une zone déjà nettoyée par une entrée précédente (ch. 254 p. 24) : rien à faire.
        return 0, []
    elif not len(ys):
        raise ValueError("aucun texte trouvé dans la zone")
    top, bottom = ys.min(), ys.max()
    pixels = crop[ink > 0]
    span = max(1, bottom - top)
    colors = item.get("colors") or [
        tuple(int(v) for v in pixels[ys < top + span * 0.25].mean(axis=0)),
        tuple(int(v) for v in pixels[ys > bottom - span * 0.25].mean(axis=0)),
    ]
    grow = item.get("grow", 4)
    erase = cv2.dilate(ink, np.ones((grow * 2 + 1, grow * 2 + 1), np.uint8))
    if "fill" in item:
        # Halo ou liseré clair autour des lettres (beige, ch. 237 p. 10) : tout ce qui n'a pas la couleur
        # du fond, à moins de 20 px des lettres, part avec elles.
        off = np.abs(crop.astype(int) - np.array(item["fill"])).max(axis=2) > 6
        near = cv2.dilate(ink, np.ones((41, 41), np.uint8)) > 0
        erase = np.maximum(erase, cv2.dilate((off & near).astype(np.uint8) * 255, np.ones((3, 3), np.uint8)))
    if "fill" in item:
        # Fond uni (blanc d'une bulle) : simple remplissage, l'inpainting baverait depuis le contour voisin.
        # Couleur relevée juste autour des lettres : un blanc de 253 rempli en 255 laissait la
        # forme des lettres anglaises en fantôme (ch. 231 p. 13). "fill" sert de repère.
        ring = (cv2.dilate(erase, np.ones((9, 9), np.uint8)) > 0) & (erase == 0)
        fill = np.array(item["fill"])
        if ring.any():
            around = np.median(crop[ring], axis=0)
            if np.abs(around - fill).max() <= 15:
                fill = around.round().astype(np.uint8)
        clean = crop.copy()
        clean[erase > 0] = fill
        result = Image.fromarray(clean)
    elif item.get("vfill"):
        # Fond à rayures verticales : chaque colonne effacée est recomposée entre le pixel
        # juste au-dessus et celui juste au-dessous (l'inpainting y laissait un pavé sombre).
        clean = crop.astype(float)
        height = crop.shape[0]
        for x in np.nonzero(erase.any(axis=0))[0]:
            col = erase[:, x] > 0
            y = 0
            while y < height:
                if not col[y]:
                    y += 1
                    continue
                start = y
                while y < height and col[y]:
                    y += 1
                above = clean[start - 1, x] if start > 0 else clean[min(y, height - 1), x]
                below = clean[y, x] if y < height else above
                t = np.linspace(0, 1, y - start + 2)[1:-1, None]
                clean[start:y, x] = above * (1 - t) + below * t
        result = Image.fromarray(clean.astype(np.uint8))
    elif item.get("blur_fill"):
        # Très grosses lettres sur un fond lumineux flou (ch. 239 p. 38) : l'inpainting y faisait des
        # pavés. On remplit avec la moyenne floue du fond voisin, sans les lettres.
        keep = (erase == 0).astype(np.float32)
        sigma = item["blur_fill"]
        num = cv2.GaussianBlur(crop.astype(np.float32) * keep[..., None], (0, 0), sigma)
        den = cv2.GaussianBlur(keep, (0, 0), sigma)[..., None]
        soft = num / np.maximum(den, 1e-3)
        # Bord fondu : un remplissage net dessinait les pavés des lettres effacées.
        alpha = cv2.GaussianBlur(cv2.dilate(erase, np.ones((9, 9), np.uint8)).astype(np.float32) / 255, (0, 0), 4)
        clean = (soft * alpha[..., None] + crop * (1 - alpha[..., None])).astype(np.uint8)
        result = Image.fromarray(clean)
    elif item.get("cv_inpaint"):
        clean = cv2.inpaint(cv2.cvtColor(crop, cv2.COLOR_RGB2BGR), erase, 9, cv2.INPAINT_TELEA)
        result = Image.fromarray(cv2.cvtColor(clean, cv2.COLOR_BGR2RGB))
    else:
        # LaMa par défaut depuis le 9 octobre : cv2.inpaint laissait des pavés flous sur le dessin.
        result = Image.fromarray(lama_fill(page, (x0, y0, x1, y1), erase))
    if "line" in item:
        # Texte qui chevauche un contour de bulle : le contour, effacé avec les lettres, est retracé
        # le long des points relevés sur l'original ([x, y] de la page), avant de poser le texte.
        points = [(x - x0, y - y0) for x, y in item["line"]]
        ImageDraw.Draw(result).line(points, fill=(0, 0, 0), width=item.get("line_width", 7), joint="curve")

    if not item["text"].strip():
        # Effacement seul (reste de lettres d'une bulle coupée entre deux pages).
        page.paste(result, (x0, y0))
        return 0, []

    # Zone où poser le nouveau texte : l'emprise des lettres d'origine, ou "target" si fourni.
    _, xs = np.nonzero(ink)
    tx0, ty0, tx1, ty1 = item.get("target") or (xs.min() + x0, top + y0, xs.max() + x0, bottom + y0)
    tx0, ty0, tx1, ty1 = tx0 - x0, ty0 - y0, tx1 - x0, ty1 - y0

    # Rendu à grande taille, puis mise à l'échelle sur la zone. Les titres d'origine sont
    # hauts et étroits : on autorise un étirement vertical limité ("stretch").
    style = STYLES[item.get("style", "systeme")]
    lines = [line.strip() for line in prepare_text(item["text"]).split("\n")]
    font = load_font(style, 200)
    base_h = int(200 * item.get("line_spacing", 0.95))

    def spacing(candidate):
        # Capitale accentuée sous la première ligne : son accent touchait la ligne du dessus, et avec le
        # liseré les lettres se soudaient (« ÉTAIJ », « LE PLAN » rayé, ch. 240 p. 11). Interligne
        # agrandi de la hauteur de l'accent, plus la marge du liseré (texte tracé à 200 px puis réduit
        # ~5 fois : le liseré de 3-5 px vaut ~25 px ici). Calculé sur les lignes finales, après redécoupage.
        h = base_h
        if len(candidate) > 1 and any(re.search(r"[ÀÂÄÇÉÈÊËÎÏÔÖÙÛÜ]", line) for line in candidate[1:]):
            h += max(0, font.getbbox("E")[1] - font.getbbox("É")[1]) + (25 if item.get("outline") else 10)
        # Cédille d'un Ç avant la dernière ligne : elle tombait sur la ligne suivante (« DİNGUE », ch. 264 p. 20).
        if any("Ç" in line for line in candidate[:-1]):
            h += max(0, font.getbbox("Ç")[3] - font.getbbox("C")[3])
        return h
    box_w, box_h = tx1 - tx0, ty1 - ty0

    def letter_height(candidate):
        # Hauteur de lettre obtenue sur la zone (étirement compris, plafonné : un texte très étiré se lit mal).
        w = max(font.getlength(line) for line in candidate)
        h = spacing(candidate) * len(candidate)
        scale = min(box_w / w, box_h / h)
        orphan = any(len(candidate) > 1 and " " not in line and len(line) <= 3 for line in candidate)
        return scale * min(item.get("stretch", 1.0), box_h / (h * scale), 1.3) * (0.85 if orphan else 1)

    words = split_words(prepare_text(item["text"]).replace("\n", " "))
    # Moitié de bulle coupée par la page : coupures gardées, la taille est réglée sur les deux moitiés.
    if not item.get("angle") and not item.get("seam") and 1 < len(words) <= 14:
        # Coupures imposées gardées sauf si elles rapetissent nettement le texte (cadres jaunes du ch. 232,
        # légendes du ch. 233 : lignes trop longues pour la zone, texte deux fois plus petit que l'anglais).
        auto = max(wrap_options(words), key=letter_height)
        if letter_height(auto) >= REWRAP_GAIN * letter_height(lines):
            lines = auto
    line_h = spacing(lines)
    # Toile à la largeur du texte : une ligne longue (ch. 226 p. 10, 5000 px) était coupée aux deux bouts.
    width = max(4000, int(max(font.getlength(line) for line in lines)) + 400)
    big = Image.new("L", (width, line_h * len(lines) + 400), 0)
    draw = ImageDraw.Draw(big)
    for i, line in enumerate(lines):
        draw.text((width // 2, 200 + i * line_h + line_h // 2), line, font=font, fill=255, anchor="mm")
    big = big.crop(big.getbbox())
    if item.get("angle"):
        # Texte incliné comme l'original (degrés, sens antihoraire).
        big = big.rotate(item["angle"], resample=Image.BICUBIC, expand=True)
        big = big.crop(big.getbbox())
    scale = min(box_w / big.width, box_h / big.height)
    # Taille plafonnée : une moitié de bulle coupée par la page (« PARCE QUE » / « SEOL-JIN ME
    # PROTÉGERA. », ch. 249-250) remplissait sa zone et sortait deux fois plus grande que l'autre
    # moitié. "max_size" (même valeur sur les deux pages), sinon la taille maximale du style de bulle.
    cap = item.get("max_size") or (style["max_size"] if item.get("fill") and style["max_size"] < 100 else None)
    if cap:
        scale = min(scale, cap / 200)
    stretch = min(item.get("stretch", 1.0), box_h / (big.height * scale))
    new_w, new_h = max(1, round(big.width * scale)), max(1, round(big.height * scale * stretch))
    text_mask = Image.new("L", result.size, 0)
    top = ty0 + (box_h - new_h) / 2
    # Moitié de bulle coupée par la page ("seam", posé par auto_translate.link_split_bubbles) : texte
    # collé à la coupure, l'autre moitié continue juste de l'autre côté, sans trou au milieu.
    gap = 200 * scale * 0.2
    if item.get("seam") == "bottom":
        top = ty1 - new_h - gap
    elif item.get("seam") == "top":
        top = ty0 + gap
    text_mask.paste(big.resize((new_w, new_h), Image.LANCZOS), (round(tx0 + (box_w - new_w) / 2), round(top)))
    size = round(200 * scale)
    if item.get("outline"):
        stroke = text_mask.filter(ImageFilter.MaxFilter(item.get("outline_width", 5) * 2 + 1))
        result.paste(tuple(item["outline"]), mask=stroke.filter(ImageFilter.GaussianBlur(1)))
    # Dégradé vertical du haut vers le bas des lettres, comme l'original.
    box = text_mask.getbbox()
    gradient = Image.new("RGB", result.size)
    g = ImageDraw.Draw(gradient)
    for y in range(result.height):
        t = min(max((y - box[1]) / max(1, box[3] - box[1]), 0), 1)
        g.line((0, y, result.width, y), fill=tuple(int(a + (b - a) * t) for a, b in zip(*colors)))
    result.paste(gradient, mask=text_mask)
    page.paste(result, (x0, y0))
    return size, lines


def find_mask(crop, seed, cut, opening, close, color_bg, others):
    """Masque de la bulle ; en cas de fuite, réessaie en refermant les petites brèches du contour,
    puis en prenant le bord de l'image comme contour (bulle coupée par le bord de la page)."""
    attempts = [(close, False)] + [(c, False) for c in (1, 2) if c > close] + [(close, True)]
    for i, (attempt, edge) in enumerate(attempts):
        try:
            mask = bubble_mask(crop, seed, cut, opening, attempt, color_bg, others, edge)
            return mask, attempt if not edge else "bord"
        except ValueError as error:
            if "fuit" not in str(error) or i == len(attempts) - 1:
                raise


def process(config_path):
    config_path = Path(config_path)
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    page = Image.open(ROOT / config["source"]).convert("RGB")
    # Les masques se calculent toujours sur l'original : une bulle déjà traduite ne fausse pas sa voisine.
    source = page.copy()
    log = [f"== {config_path.name}"]
    points = [tuple(b["point"]) for b in config["bubbles"] if "point" in b]
    done = np.zeros((page.height, page.width), bool)  # intérieur des bulles déjà traitées
    for bubble in config["bubbles"]:
        if "box" in bubble:
            try:
                size, lines = free_text(page, bubble)
                log.append(f"  box {bubble['box'][:2]} {bubble.get('style', 'systeme')} {size}px #{bubble.get('id', '')} : {' / '.join(lines)}")
            except ValueError as error:
                log.append(f"  box {bubble['box'][:2]} ÉCHEC : {error}")
            continue
        style = STYLES[bubble.get("style", "dialogue")]
        x, y = bubble["point"]
        # Recadrage élargi aux bulles voisines : une voisine coupée par le bord du recadrage faussait
        # le partage du bonhomme de neige, la bulle du bas effaçait la 2e ligne du haut (ch. 236 p. 16).
        top, bottom = y - CROP_RADIUS, y + CROP_RADIUS
        for ox, oy in points:
            if (ox, oy) != (x, y) and abs(oy - y) < CROP_RADIUS:
                top, bottom = min(top, oy - CROP_RADIUS // 2), max(bottom, oy + CROP_RADIUS // 2)
        box = (0, max(0, top), page.width, min(page.height, bottom))
        crop = page.crop(box)
        cut = [(cx, cy - box[1]) for cx, cy in bubble["cut"]] if "cut" in bubble else None
        # Les autres bulles de la page servent à séparer automatiquement les bulles collées.
        others = [(ox, oy - box[1]) for ox, oy in points if (ox, oy) != (x, y)]
        try:
            opening = [(ox, oy - box[1]) for ox, oy in bubble["open"]] if "open" in bubble else None
            (mask, region), closed = find_mask(
                source.crop(box), (x, y - box[1]), cut, opening, bubble.get("close", 0), bubble.get("color_bg", False), others
            )
            color = fill_color(crop, region)
            # Sans "max_size" imposé, la taille suit le lettrage original mesuré dans la bulle.
            max_size = bubble.get("max_size") or lettering_size(source.crop(box), mask, color, style, bubble["text"]) \
                or style["max_size"]
            centred = layout(bubble["text"], mask, style, max_size)[0].size
            # Centre vertical du texte anglais : une bulle coupée par le bord de la page (ch. 239 p. 45)
            # n'a ici que sa moitié visible, son centre géométrique tombe trop bas. On garde le centre
            # de la bulle si le texte y rapetissait trop.
            cy = ink_height(source.crop(box), mask, color)[1]
            cy = cy[1] if cy else None
            rows = np.nonzero(np.array(mask).any(axis=1))[0]
            edge = (box[1] == 0 and rows[0] == 0) or (box[3] >= page.height and rows[-1] >= mask.height - 1)
            keep = INK_CENTRE_KEEP_EDGE if edge else INK_CENTRE_KEEP
            if cy is not None:
                try:
                    if layout(bubble["text"], mask, style, max_size, cy)[0].size < keep * centred:
                        cy = None
                except ValueError:
                    cy = None
        except ValueError as error:
            log.append(f"  ({x}, {y}) ÉCHEC, bulle laissée telle quelle : {error}")
            continue
        # Bulle qui recouvre une bulle déjà traitée : elle effacerait son texte (bonhomme de neige raté).
        here = np.zeros((page.height, page.width), bool)
        here[box[1]:box[3]] = np.array(mask) > 0
        if (here & done).sum() > 0.05 * here.sum():
            log.append(f"  ({x}, {y}) ÉCHEC : recouvre une bulle voisine déjà traduite ; ajouter un \"cut\" au col")
        done |= here
        original = crop.copy()
        colored = colored_pixels(crop)
        if bubble.get("erase_color"):
            # Texte lui-même en couleur (ch. 232, lettres brunes) : rien à préserver.
            colored = Image.new("L", crop.size, 0)
        # Dans la marge autour des traits colorés, les pixels noirs sont des restes de lettres : on les efface
        # aussi, seule la couleur (et son anticrénelage clair) est préservée.
        dark = original.convert("L").point(lambda v: 255 if v < 90 else 0)
        colored = ImageChops.subtract(colored, ImageChops.subtract(dark, colored_pixels(crop, grow=False)))
        # Couleur enfermée dans la bulle = texte (halo beige autour des lettres, ch. 237 p. 9 ; lettres
        # brunes, ch. 232) : effacée. Seule la couleur qui touche le contour (onomatopée qui traverse
        # la bulle) est préservée.
        inside = np.array(mask) > 0
        deep = cv2.erode(inside.astype(np.uint8), np.ones((25, 25), np.uint8)) > 0
        col = (np.array(colored) > 0).astype(np.uint8)
        n, labels = cv2.connectedComponents(col)
        if n > 1:
            touches = np.zeros(n, bool)
            touches[np.unique(labels[(col > 0) & ~deep])] = True
            touches[0] = False
            colored = Image.fromarray((touches[labels] * 255).astype(np.uint8))
        crop.paste(Image.new("RGB", crop.size, color), mask=ImageChops.subtract(mask, colored))
        # Texte noir sur bulle claire, blanc sur bulle sombre.
        text_color = (0, 0, 0) if sum(color) > 384 else (255, 255, 255)
        if bubble["text"].strip() in ("...", "…"):
            size, lines = draw_dots(crop, mask, ink_height(original, mask, color), text_color), ["(points)"]
        else:
            size, lines = draw_text(crop, mask, bubble["text"], style, max_size, text_color, cy)
        # Les onomatopées colorées repassent par-dessus le texte, comme dans l'original.
        crop.paste(original, mask=ImageChops.multiply(mask, colored))
        page.paste(crop, box[:2])
        note = "" if closed == bubble.get("close", 0) else (
            " (bord de page pris comme contour)" if closed == "bord" else f" (close {closed} automatique)")
        log.append(f"  ({x}, {y}) {bubble.get('style', 'dialogue')} {size}px #{bubble.get('id', '')} : {' / '.join(lines)}{note}")
    output = ROOT / config["output"]
    output.parent.mkdir(parents=True, exist_ok=True)
    page.save(output, quality=95)
    log.append(f"  -> {config['output']}")
    return "\n".join(log)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    check_fonts()
    # Une page par processus, 4 à la fois (LaMa) ; ProcessPoolExecutor : multiprocessing.Pool restait
    # bloqué sans fin sous Windows (ch. 259, 10 octobre).
    with ProcessPoolExecutor(min(len(sys.argv) - 1, os.cpu_count() or 1, 4) or 1) as pool:
        for text in pool.map(process, sys.argv[1:]):
            print(text, flush=True)
