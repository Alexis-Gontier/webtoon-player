"""Traduction d'un chapitre en deux commandes, sans passer par la lecture des images.

  python scripts/auto_translate.py inv N    OCR du chapitre -> translations/chN_fr.txt (texte anglais à traduire)
  python scripts/auto_translate.py build N  configs JSON + rendu + contrôle automatique du résultat

Format de translations/chN_fr.txt (une ligne par bloc, l'anglais lu par l'OCR en commentaire) :
  # EN: HOW DARE YOU...
  001.3 | dialogue | COMMENT OSES-TU...
Colonne du milieu : style, suivi en option d'un objet JSON de réglages (max_size, cut, close, open, box...).
Texte "-" : bloc ignoré (bruit OCR, ou deuxième morceau d'une bulle déjà traduite).

Le contrôle relit chaque page française par OCR : il signale les bulles en ÉCHEC, les bulles dont le
texte français n'est pas retrouvé (effacée par une voisine, illisible) et l'anglais resté visible.
Seuls les blocs signalés sont recadrés dans inventaire/chN/controle_PPP.png, à regarder à la main.
"""

import json
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from difflib import SequenceMatcher
from multiprocessing import Pool
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import inventory as inv
import translate_bubbles as tb

ROOT = Path(__file__).resolve().parent.parent
LINE = re.compile(r"^(\d{3})\.(\d+)\s*\|\s*([^|]*?)\s*\|\s*(.*)$")


def letters(text):
    return re.sub(r"[^A-ZÀ-Ÿ]", "", text.upper())


def similar(a, b):
    a, b = letters(a), letters(b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def pages(chapter):
    return sorted((ROOT / "chapters_en" / f"chapter-{chapter}").iterdir())


def inventory_page(src):
    page = Image.open(src).convert("RGB")
    lines = inv.ocr_lines(page)
    blocks = inv.group_blocks(lines)
    for b in blocks:
        x0, y0, x1, y1 = b["box"]
        b["point"] = [(x0 + x1) // 2, (y0 + y1) // 2]
    blocks = sorted(blocks + inv.missing_bubbles(page, blocks), key=lambda b: b["box"][1])
    for i, b in enumerate(blocks, 1):
        x0, y0, x1, y1 = b["box"]
        b["id"] = i
        b["point"] = [(x0 + x1) // 2, (y0 + y1) // 2]
        b["kind"] = inv.kind(page, b)
        inside = [l for l in lines if x0 <= (l["box"][0] + l["box"][2]) / 2 <= x1 and y0 <= (l["box"][1] + l["box"][3]) / 2 <= y1]
        b["line_h"] = int(sum(l["box"][3] - l["box"][1] for l in inside) / len(inside)) if inside else 0
    return src.name, blocks


def cmd_inv(chapter):
    out_dir = ROOT / "inventaire" / f"ch{chapter}"
    out_dir.mkdir(parents=True, exist_ok=True)
    with Pool() as pool:
        result = dict(pool.map(inventory_page, pages(chapter)))
    (out_dir / "inventaire.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    txt = ROOT / "translations" / f"ch{chapter}_fr.txt"
    rows = [f"# Chapitre {chapter} : remplir la 3e colonne (texte français), '-' pour ignorer un bloc."]
    for name, blocks in result.items():
        rows.append(f"\n## {name}")
        for b in blocks:
            style = "systeme" if b["kind"] == "dessin" else "dialogue"
            rows.append(f"# EN: {b['text']}   [{b['kind']} {b['point']} h={b['line_h']}]")
            rows.append(f"{Path(name).stem}.{b['id']} | {style} | ")
    if txt.exists():
        txt = txt.with_suffix(".new.txt")
    txt.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"{sum(len(b) for b in result.values())} blocs -> {txt}")


def parse(chapter):
    entries = {}
    for row in (ROOT / "translations" / f"ch{chapter}_fr.txt").read_text(encoding="utf-8").splitlines():
        m = LINE.match(row)
        if not m:
            continue
        page, bid, opts, text = m.groups()
        style, _, extra = opts.partition(" ")
        entries.setdefault(page, {})[int(bid)] = {"style": style or "dialogue", "text": text.strip(),
                                                   "extra": json.loads(extra) if extra.strip() else {}}
    return entries


def build_configs(chapter):
    inventory = json.loads((ROOT / "inventaire" / f"ch{chapter}" / "inventaire.json").read_text(encoding="utf-8"))
    entries = parse(chapter)
    paths, configs = [], []
    for name, blocks in inventory.items():
        stem = Path(name).stem
        bubbles = []
        for b in blocks:
            e = entries.get(stem, {}).get(b["id"])
            if not e or not e["text"] or e["text"] == "-":
                continue
            # Texte identique dans les deux langues (nom crié, « LAY! ») : l'original est gardé tel quel,
            # le refaire ne changeait que l'espace avant « ! » et abîmait le dessin qui chevauche la bulle
            # (ch. 237 p. 2).
            if not e["extra"] and len(letters(e["text"])) >= 2 and letters(e["text"]) == letters(b["text"]):
                continue
            item = {"id": b["id"], "text": e["text"].replace("\\n", "\n"), "style": e["style"]}
            # Même bulle lue deux fois par l'OCR (même texte, points proches) : les deux points se
            # partageraient la bulle et la videraient. On ne garde que le premier.
            if any(o["text"] == item["text"] and abs(o.get("point", o.get("box", [0, 0]))[1] - b["point"][1]) < 400
                   for o in bubbles):
                continue
            if b["kind"] == "dessin" and "point" not in e["extra"]:
                x0, y0, x1, y1 = b["box"]
                item["box"] = [max(0, x0 - 25), max(0, y0 - 15), x1 + 25, y1 + 15]
            else:
                item["point"] = b["point"]
            # La taille d'origine est mesurée dans la bulle par translate_bubbles.lettering_size.
            item.update(e["extra"])
            bubbles.append(item)
        # Entrées ajoutées à la main (texte que l'OCR n'a pas repéré) : id absent de l'inventaire,
        # avec "point" ou "box" dans les réglages JSON.
        known = {b["id"] for b in blocks}
        for bid, e in entries.get(stem, {}).items():
            if bid not in known and e["text"] not in ("", "-") and ("point" in e["extra"] or "box" in e["extra"]):
                # "(effacer)" : efface seulement (reste de lettres d'une bulle coupée par la page).
                text = "" if e["text"] == "(effacer)" else e["text"].replace("\\n", "\n")
                bubbles.append({"id": bid, "text": text, "style": e["style"], **e["extra"]})
        config = {"source": f"chapters_en/chapter-{chapter}/{name}", "output": f"chapters_fr/chapter-{chapter}/{name}",
                  "bubbles": bubbles}
        # Fichiers générés : rangés avec l'inventaire, translations/ ne garde que les txt.
        path = ROOT / "inventaire" / f"ch{chapter}" / f"config_{stem}.json"
        configs.append((path, config))
    link_split_bubbles(configs)
    for path, config in configs:
        path.write_text(json.dumps(config, ensure_ascii=False, indent=1), encoding="utf-8")
        paths.append(path)
    return paths, inventory


SPLIT_MAX_SIZE = 32


def fit_size(item):
    """Plus grande taille de police (base 200 px) à laquelle le texte remplit sa zone en mode "box" :
    meilleur découpage en lignes (coupures imposées comprises), écrit dans item["text"]. La moitié la
    plus serrée fixe ensuite la taille des deux moitiés."""
    font = tb.load_font(tb.STYLES[item.get("style", "systeme")], 200)
    x0, y0, x1, y1 = item.get("target") or item["box"]
    text = tb.prepare_text(item["text"])
    options = [[line.strip() for line in text.split("\n")]]
    words = tb.split_words(text.replace("\n", " "))
    if len(words) <= 14:
        options += list(tb.wrap_options(words, 4))

    def size(lines):
        width = max(font.getlength(line) for line in lines)
        line_h = 200 * item.get("line_spacing", 0.95)
        # Même interligne que le rendu (translate_bubbles.render_box) : capitale accentuée après la
        # première ligne → interligne agrandi. Sans ça, la moitié accentuée sortait plus petite (264 p. 30).
        if len(lines) > 1 and any(re.search(r"[ÀÂÄÇÉÈÊËÎÏÔÖÙÛÜ]", line) for line in lines[1:]):
            line_h += max(0, font.getbbox("E")[1] - font.getbbox("É")[1]) + (25 if item.get("outline") else 10)
        if any("Ç" in line for line in lines[:-1]):
            line_h += max(0, font.getbbox("Ç")[3] - font.getbbox("C")[3])
        return int(200 * min((x1 - x0) / width, (y1 - y0) / (line_h * len(lines))))
    def score(lines):
        # Mot court seul sur sa ligne (« LA », « CE », « TOUT ») : se lit mal. Coupures du txt préférées à égalité.
        orphan = len(lines) > 1 and any(len(line.replace(tb.NBSP, "")) <= 4 for line in lines)
        return size(lines) * (0.8 if orphan else 1) * (1.05 if lines == options[0] else 1)
    best = max(options, key=score)
    item["text"] = "\n".join(best)
    return size(best)


def link_split_bubbles(configs):
    """Bulle coupée entre deux pages : une moitié en bas d'une page, l'autre en haut de la suivante,
    toutes deux en mode "box" avec "fill". Chaque moitié remplissait sa zone : une moitié deux fois plus
    grosse que l'autre, et un trou au milieu (signalé une dizaine de fois, ch. 249-261, 10 octobre).
    Même taille maximale des deux côtés, et texte collé à la coupure ("seam")."""
    def text_boxes(config, edge):
        height = Image.open(ROOT / config["source"]).height
        for b in config["bubbles"]:
            if not b.get("text") or "box" not in b or "fill" not in b or b.get("ink_max") == 0:
                continue
            if (edge == "bottom" and b["box"][3] >= height - 10) or (edge == "top" and b["box"][1] <= 5):
                yield b
    for (_, upper), (_, lower) in zip(configs, configs[1:]):
        bottoms, tops = list(text_boxes(upper, "bottom")), list(text_boxes(lower, "top"))
        for a in bottoms:
            for b in tops:
                if min(a["box"][2], b["box"][2]) - max(a["box"][0], b["box"][0]) < 50:
                    continue
                # Même colonne des deux côtés : deux boîtes de largeurs différentes décalaient les lignes.
                x0, x1 = max(a["box"][0], b["box"][0]), min(a["box"][2], b["box"][2])
                for half in (a, b):
                    if "target" not in half:
                        half["target"] = [x0, half["box"][1], x1, half["box"][3]]
                size = min(a.get("max_size") or b.get("max_size") or SPLIT_MAX_SIZE, fit_size(a), fit_size(b))
                a["max_size"] = b["max_size"] = size
                a.setdefault("seam", "bottom")
                b.setdefault("seam", "top")


def check_page(args):
    """Relit la page française : bulles non retrouvées et anglais resté visible."""
    config_path, blocks = args
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    fr = Image.open(ROOT / config["output"]).convert("RGB")
    ocr = inv.group_blocks(inv.ocr_lines(fr))
    issues = []
    for b in config["bubbles"]:
        x, y = b["point"] if "point" in b else ((b["box"][0] + b["box"][2]) // 2, (b["box"][1] + b["box"][3]) // 2)
        near = " ".join(o["text"] for o in ocr if abs((o["box"][1] + o["box"][3]) / 2 - y) < 260
                        and abs((o["box"][0] + o["box"][2]) / 2 - x) < 400)
        expected = b["text"].replace("\n", " ")
        exp, got = letters(expected), letters(near)
        # L'OCR lit mal Anime Ace (R -> P, D -> O...) : on compte toutes les lettres retrouvées, pas un seul bloc.
        found = sum(m.size for m in SequenceMatcher(None, exp, got, autojunk=False).get_matching_blocks()) if got else 0
        if len(exp) >= 4 and found < 0.4 * len(exp):
            issues.append((b["id"], [x, y], f"texte FR non retrouvé : {expected!r} / lu : {near!r}"))
    # Texte lu loin de toute entrée : bulle que l'OCR de l'inventaire n'avait pas repérée, restée
    # en anglais (ch. 233 p. 7, "LET'S DO EVERYTHING..." sous une bulle collée).
    centres = [b["point"] if "point" in b else ((b["box"][0] + b["box"][2]) // 2, (b["box"][1] + b["box"][3]) // 2)
               for b in config["bubbles"]]
    ignored = [blk["point"] for blk in blocks]
    for o in ocr:
        ox, oy = (o["box"][0] + o["box"][2]) // 2, (o["box"][1] + o["box"][3]) // 2
        if len(letters(o["text"])) >= 8 and not any(abs(ox - x) < 300 and abs(oy - y) < 250 for x, y in centres + ignored):
            issues.append(("?", [ox, oy], f"texte non traité : {o['text']!r}"))
    french = [b["text"].replace("\n", " ") for b in config["bubbles"]]
    for blk in blocks:
        for o in ocr:
            # Texte identique dans les deux langues (noms propres, "TAE-WON,") : pas un reste d'anglais.
            if any(similar(o["text"], f) > 0.7 for f in french):
                continue
            if abs(o["box"][1] - blk["box"][1]) < 60 and abs(o["box"][0] - blk["box"][0]) < 80 \
                    and len(letters(blk["text"])) >= 5 and similar(o["text"], blk["text"]) > 0.7:
                issues.append((blk["id"], blk["point"], f"anglais resté : {o['text']!r}"))
    return Path(config["output"]).name, issues


def review_sheet(chapter, name, issues):
    en = Image.open(ROOT / "chapters_en" / f"chapter-{chapter}" / name).convert("RGB")
    fr = Image.open(ROOT / "chapters_fr" / f"chapter-{chapter}" / name).convert("RGB")
    font = ImageFont.truetype("arial.ttf", 20)
    tiles = []
    for bid, (x, y), _ in issues:
        box = (max(0, x - 260), max(0, y - 200), min(en.width, x + 260), min(en.height, y + 200))
        tile = Image.new("RGB", ((box[2] - box[0]) * 2 + 10, box[3] - box[1] + 26), (40, 40, 40))
        tile.paste(en.crop(box), (0, 26))
        tile.paste(fr.crop(box), (box[2] - box[0] + 10, 26))
        ImageDraw.Draw(tile).text((4, 2), f"{Path(name).stem}.{bid}", fill=(255, 255, 0), font=font)
        tiles.append(tile)
    out = Image.new("RGB", (max(t.width for t in tiles), sum(t.height + 6 for t in tiles)), (255, 255, 255))
    y = 0
    for t in tiles:
        out.paste(t, (0, y))
        y += t.height + 6
    path = ROOT / "inventaire" / f"ch{chapter}" / f"controle_{Path(name).stem}.png"
    out.save(path)
    return path


def cmd_build(chapter, only=None, render=True):
    tb.check_fonts()
    paths, inventory = build_configs(chapter)
    if only:
        paths = [p for p in paths if p.stem.split("_")[1] in only]
    # Rendu sur 4 processus (chacun peut charger LaMa). ProcessPoolExecutor plutôt que
    # multiprocessing.Pool : le Pool restait bloqué sans fin sous Windows (ch. 230 et 240, 9-10 octobre),
    # l'exécuteur lève BrokenProcessPool si un processus meurt.
    # Un processus tué (mémoire, plusieurs rendus en parallèle) cassait tout le chapitre et laissait des
    # pages de 0 octet (ch. 227-236, 247 le 10 octobre) : les pages perdues sont refaites une à une.
    logs = [None] * len(paths) if render else []
    if render:
        try:
            with ProcessPoolExecutor(min(4, os.cpu_count() or 1)) as pool:
                futures = [pool.submit(tb.process, path) for path in paths]
                for i, future in enumerate(futures):
                    try:
                        logs[i] = future.result()
                    except BrokenProcessPool:
                        pass
        except BrokenProcessPool:
            pass
    # Page perdue ou illisible (écriture interrompue, ch. 230 et 238 p. 14 le 10 octobre) : refaite seule.
    for i, path in enumerate(paths if render else []):
        output = ROOT / json.loads(path.read_text(encoding="utf-8"))["output"]
        try:
            if logs[i] is None:
                raise ValueError("processus tué")
            Image.open(output).verify()
        except Exception:
            logs[i] = tb.process(path)
    for log in logs:
        for row in log.splitlines():
            if "ÉCHEC," in row or "ÉCHEC :" in row:
                print(f"{log.splitlines()[0]} {row.strip()}")
    with ProcessPoolExecutor(min(12, os.cpu_count() or 1)) as pool:
        results = list(pool.map(check_page, [(p, inventory[Path(json.loads(p.read_text(encoding='utf-8'))['source']).name])
                                             for p in paths]))
    (ROOT / "inventaire" / f"ch{chapter}" / "rendu.log").write_text("\n".join(logs), encoding="utf-8")
    total = 0
    for name, issues in results:
        if issues:
            total += len(issues)
            for bid, point, msg in issues:
                print(f"{Path(name).stem}.{bid} {point} {msg}")
            print(f"  -> {review_sheet(chapter, name, issues)}")
    print(f"Contrôle : {total} point(s) à vérifier.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    command, chapter = sys.argv[1], int(sys.argv[2])
    if command == "inv":
        cmd_inv(chapter)
    else:
        # "check" relance seulement le contrôle, sans refaire le rendu.
        cmd_build(chapter, sys.argv[3:], render=command != "check")
