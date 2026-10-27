# Player : traduction française

Traduction du webtoon « Player » (chapitres 225 à 264) pour lecture personnelle. Le texte anglais
est repéré par OCR, effacé bulle par bulle, puis remplacé par le texte français avec des polices
proches du lettrage d'origine.

## Lire

Site (Astro + Svelte, une page par chapitre) : `python scripts/make_viewer.py`, puis dans `site/` :
`pnpm install` (une fois), `pnpm run build`, `pnpm run preview` et ouvrir http://localhost:4321/.
Développement : `pnpm run dev`. Tests : `pnpm test`, `pnpm run test:dist` (après un build), `pnpm run e2e`.
## Structure

```
chapters_en/        originaux anglais (jamais modifiés)
chapters_fr/        pages traduites, même nom de fichier que l'original
chapters_web/       copies WebP q80 des deux dossiers ci-dessus (seules planches versionnées, publiées avec le site)
translations/       traductions : chN_fr.txt (+ configs JSON écrites à la main pour les ch. 225 et 259)
inventaire/         dossier de travail régénérable : OCR, configs générées, images de contrôle, journaux
scripts/            outils (voir ci-dessous)
models/             lama_fp32.onnx : inpainting LaMa (effacement par défaut), huggingface.co/Carve/LaMa-ONNX
                    text_detection_en_ppocrv3.onnx : détecteur de texte de find_missed.py (opencv/text_detection_ppocr)
fonts/              polices de lettrage (Anton, Mouse Memoirs... ; Anime Ace 2 complétée de Ç et Œ, à installer soi-même)
docs/               translation-reference.md : règles, glossaire, options du moteur, erreurs résolues
                    audit-2026-10-09.md : audit des règles, points restant à corriger
site/               site Astro + Svelte (pages, lecteur, SEO) ; données écrites par scripts/make_viewer.py
tests/              tests Python (pytest)```

## Outils

Installation : `pip install -r requirements.txt` (Windows, pour l'OCR intégré).

```
python scripts/auto_translate.py inv N             # OCR -> translations/chN_fr.txt à remplir
python scripts/auto_translate.py build N [PPP ...] # rendu + contrôle OCR
python scripts/auto_translate.py check N [PPP ...] # contrôle seul
python scripts/find_missed.py N [N ...]            # texte anglais oublié (détecteur de texte)
python scripts/audit_render.py N [N ...]           # texte français nettement plus petit que l'anglais
python scripts/translate_bubbles.py translations/ch225_*.json   # rendu depuis des configs JSON
python scripts/make_viewer.py                      # données et vignettes du site
python scripts/compress_pages.py                   # copies WebP q80 des planches dans chapters_web/ (git)
.\scripts\download-chapter.ps1 -ChapterUrl <url du chapitre>    # télécharge les chapitres suivants
python scripts/add_french_glyphs.py <src.ttf> <sortie.ttf>      # ajoute Ç/Œ à une police
```

Format d'une ligne de `translations/chN_fr.txt` : `PAGE.ID | style [réglages JSON] | TEXTE`
(`-` = bloc ignoré, `\n` = retour à la ligne). Le détail est dans `docs/translation-reference.md`.

## En ligne

Le site est publié sur Vercel : https://player-fr.vercel.app/ (`site/vercel.json`), reconstruit à chaque push
sur `main`. GitHub Actions (`.github/workflows/ci.yml`) vérifie types, tests, lint et build sur chaque push et
pull request. Le build en ligne lit les planches dans `chapters_web/` : après un nouveau chapitre, lancer
`make_viewer.py` puis `compress_pages.py` et committer `chapters_web/` et `site/public/thumbs/`.

## Contribuer

Corrections de traduction, bugs du site ou du moteur : voir [CONTRIBUTING.md](CONTRIBUTING.md). Les questions
et idées vont dans les Discussions du dépôt.

Les planches originales et la police Anime Ace 2 ne sont pas dans le dépôt : sans elles, tu peux corriger
les textes et le code, mais pas refaire le rendu des pages.

## Licence

Le code (`scripts/`, `site/`, `tests/`) est sous licence [MIT](LICENSE). Le webtoon « Player » (플레이어),
de Park Jong-seok et Oh Hyeon-jun (Naver Webtoon), appartient à ses auteurs : ses pages, sa cover et ses
dialogues ne sont pas couverts. Les textes de `translations/` sont une traduction non officielle, faite pour
une lecture personnelle.

