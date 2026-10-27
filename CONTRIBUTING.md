# Contribuer

Merci de vouloir aider ! Les contributions sont bienvenues sur trois fronts : la traduction, le moteur
de lettrage (`scripts/`) et le site de lecture (`site/`).

Avant de commencer, une limite importante : **les planches originales ne sont pas dans ce dépôt**
(`chapters_en/` et `chapters_fr/` sont ignorés par git ; seules leurs copies allégées de `chapters_web/`
le sont, pour le site). Le moteur a besoin des originaux : sans eux, tu peux corriger un texte ou le code,
mais pas refaire le rendu des pages.

## Signaler un problème

Ouvre une issue avec le modèle qui correspond :

- **Erreur de traduction** : chapitre, page, la phrase actuelle et ta proposition.
- **Bug du site** : ce que tu as fait, ce qui s’est passé, navigateur et taille d’écran.

Pour une question ou une idée qui n’est pas encore une tâche précise, passe par les **Discussions**.

## Proposer une correction de traduction

Les textes sont dans `translations/chN_fr.txt`, une ligne par bulle :

```
PAGE.ID | style [json] | TEXTE
001.8   | dialogue      | TU DÉTESTES VRAIMENT CES PETITS, HEIN ?
```

- Ne modifie que la partie `TEXTE`, sauf si tu sais ce que fait le reste (voir
  `docs/translation-reference.md`).
- **UNNAME, PLAYER(S), RANKER et UNRANKER ne se traduisent jamais.** Tout le reste se traduit.
- Typographie : majuscules accentuées (É, À, Ç), apostrophe `’`, guillemets droits `"`. Pas d’espace
  avant `? ! : ;` : le moteur ajoute l’espace insécable.
- Un fragment (« I... ») se traduit en tenant compte de la bulle suivante.
- Un retour à la ligne forcé s’écrit `\n` dans le texte.

Le glossaire et les choix déjà faits sont dans `docs/translation-reference.md`. Un terme de jeu nouveau ou
douteux : demande dans les Discussions avant de trancher.

## Travailler sur le code

### Moteur de lettrage (Python, Windows)

```
pip install -r requirements.txt
python -m pytest tests
```

L’OCR utilise celui de Windows (`winocr`) ; les modèles ONNX sont à télécharger (voir le README).

### Site (Astro + Svelte, pnpm uniquement)

```
cd site
pnpm install
pnpm dev                       # http://localhost:4321/
```

Avant d’ouvrir une pull request, tout doit passer :

```
pnpm typecheck && pnpm test && pnpm lint && pnpm knip
pnpm build && pnpm test:dist && pnpm e2e
```

Sans les originaux, les images des chapitres ne s’affichent pas en local. Pour voir le site comme en ligne,
avec les copies de `chapters_web/` : `PAGES_SOURCE=web pnpm build && pnpm preview`.

## Pull requests

- Une pull request = un sujet (un chapitre, un bug, une fonctionnalité).
- Branche nommée `fix/…`, `feat/…` ou `trad/chN-…`.
- Messages de commit courts, en français, au format `type(portée): résumé`
  (ex. `fix(ch231): accord de « mauvais petits »`).
- Décris ce qui change et pourquoi ; ajoute une capture pour tout changement visible.
- Pas de planche originale ni de police sous licence restrictive dans les commits ; les copies de
  `chapters_web/` ne changent qu’avec un nouveau rendu.

## Respect

Reste courtois et constructif dans les issues, les Discussions et les relectures. Les remarques portent sur
le travail, jamais sur la personne.
