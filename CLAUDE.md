# Player : traduction EN → FR

Webtoon « Player » traduit pour lecture personnelle : `chapters_en/chapter-N/` → `chapters_fr/chapter-N/`
(même nom de fichier). Lire `docs/translation-reference.md` (glossaire, options du moteur, erreurs déjà
résolues) avant un nouveau chapitre ou un réglage inhabituel. Structure du dossier : `README.md`.

## Commandes (depuis la racine)

```
python scripts/auto_translate.py inv N             # OCR -> translations/chN_fr.txt à remplir
python scripts/auto_translate.py build N [PPP ...] # rendu + contrôle OCR (toutes les pages ou certaines)
python scripts/auto_translate.py check N [PPP ...] # contrôle seul
python scripts/find_missed.py N [N ...]            # texte anglais oublié -> inventaire/chN/oublis.png
python scripts/audit_render.py N [N ...]           # texte FR trop petit vs anglais -> inventaire/chN/tailles.png
python scripts/translate_bubbles.py translations/ch225_*.json   # ch. 225 et 259 : JSON manuels, sans txt
python scripts/make_viewer.py                      # données du site + vignettes après chaque rendu
cd site && pnpm run build && pnpm run preview      # site Astro sur http://localhost:4321/ (pnpm uniquement)
```

Sources : `translations/` (txt + JSON manuels 225/259). Tout le généré va dans `inventaire/chN/`
(garder les `inventaire.json` : ils évitent de refaire l'OCR).

## Déroulé d'un chapitre

1. `inv N`, puis une planche contact des blocs pour corriger ce que l'OCR a mal lu.
2. Regarder les pages sans aucune entrée traduite : l'OCR peut rater une page entière.
3. Remplir `translations/chN_fr.txt` (`PAGE.ID | style [json] | TEXTE`, `-` = ignorer).
   Bulles ratées : id 100+ avec `{"point": [x, y]}` ou `{"box": [...]}`.
4. `build N` : c'est la vérification. Chercher `ÉCHEC,` / `ÉCHEC :` (« ÉCHEC ET MAT » est une
   réplique), puis regarder en petites planches seulement les points signalés, les `box` et les
   bulles ajoutées à la main.
5. `find_missed.py N` : l'OCR rate les lettrages stylisés et les textes courts (« YEAH! », légendes
   blanches cernées). Regarder `oublis.png` et ajouter les vrais oublis (id 100+).
6. `audit_render.py N` : texte nettement plus petit que l'anglais, à regarder dans `tailles.png`.
7. `make_viewer.py`, puis `pnpm run build` dans `site/`, puis chapitre suivant sans demander.

Retours de l'utilisateur : appliquer la « Méthode de correction » de `docs/translation-reference.md`.
Un défaut qui revient se corrige dans le moteur, puis rendu de tous les chapitres et repérage
(`find_missed`, `audit_render`) partout. Jamais bulle par bulle seulement à l'endroit signalé.

## Règles

- IMPORTANT : **UNNAME**, **PLAYER(S)**, **RANKER** et **UNRANKER** ne se traduisent jamais ; tout le
  reste se traduit. Nouveau terme de jeu douteux → demander à l'utilisateur.
- Typographie : majuscules accentuées, apostrophe `’`, guillemets droits `"` (l'espace insécable
  avant `? ! : ;` est ajoutée par le moteur).
- Traduire un fragment (« I... ») en connaissant la bulle suivante.
- Style selon le lettrage anglais : capitales droites → `dialogue`, penchées fines → `italique`,
  pinceau → `cri`, légendes sans bulle → `systeme` en mode `box`.
- Ne fixer `max_size` que si le texte touche un décor (la taille suit les lettres anglaises).

## Pièges

- `\n` dans les txt et modifications de `scripts/translate_bubbles.py` : outil Edit uniquement
  (printf, sed ou un script Python transforment `\n` en vrai retour à la ligne).
- Bonshommes de neige (bulles collées) : une bulle oubliée vide sa voisine sans ÉCHEC.
- Coûts : ne jamais inspecter chaque bulle en image.

## Compaction

Conserver : le chapitre en cours, les pages encore à corriger, les fichiers modifiés et toute
décision de traduction prise avec l'utilisateur.
