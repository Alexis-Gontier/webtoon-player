"""Ajoute Ç, ç, Œ, œ à une police TrueType qui ne les a pas (ex. Anime Ace 2.0 BB).

Usage : python scripts/add_french_glyphs.py <source.ttf> <sortie.ttf>
Ç = C + virgule sous la lettre, Œ = O et E accolés. Glyphes composites :
ils suivent exactement le dessin des lettres d'origine.
"""

import sys

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent

# Lettrage tout en capitales : les minuscules reprennent les capitales.
COMPOSITES = {0xC7: "cedilla", 0xE7: "cedilla", 0x152: "oe", 0x153: "oe"}


def component(name, x, y):
    c = GlyphComponent()
    c.glyphName, c.x, c.y, c.flags = name, x, y, 0x4  # ROUND_XY_TO_GRID
    return c


def main(src, dst):
    font = TTFont(src)
    cmap = font.getBestCmap()
    glyf, hmtx = font["glyf"], font["hmtx"]
    letter = {ch: cmap[ord(ch)] for ch in "COE,"}
    comma = glyf[letter[","]]
    comma.recalcBounds(glyf)
    c_glyph = glyf[letter["C"]]
    c_glyph.recalcBounds(glyf)

    for code, kind in COMPOSITES.items():
        if code in cmap:
            continue
        name = f"uni{code:04X}"
        glyph = Glyph()
        glyph.numberOfContours = -1
        if kind == "cedilla":
            # Virgule centrée sous le C, son haut juste sous la ligne de base.
            dx = (c_glyph.xMin + c_glyph.xMax) // 2 - (comma.xMin + comma.xMax) // 2
            dy = -comma.yMax - 10
            glyph.components = [component(letter["C"], 0, 0), component(letter[","], dx, dy)]
            width = hmtx[letter["C"]][0]
        else:
            # O puis E, légèrement chevauchés comme dans une ligature.
            o_width = hmtx[letter["O"]][0]
            overlap = o_width // 5
            glyph.components = [component(letter["O"], 0, 0), component(letter["E"], o_width - overlap, 0)]
            width = o_width - overlap + hmtx[letter["E"]][0]
        glyf[name] = glyph  # ajoute aussi le nom à l'ordre des glyphes de la police
        hmtx[name] = (width, 0)
        for table in font["cmap"].tables:
            if table.isUnicode():
                table.cmap[code] = name
        print(f"ajouté {chr(code)} ({name})")
    if 0xA0 not in cmap:
        # Espace insécable (avant ? ! : ;) : même dessin que l'espace normale.
        for table in font["cmap"].tables:
            if table.isUnicode():
                table.cmap[0xA0] = cmap[0x20]
        print("ajouté espace insécable")
    font.save(dst)


if __name__ == "__main__":
    main(*sys.argv[1:3])
