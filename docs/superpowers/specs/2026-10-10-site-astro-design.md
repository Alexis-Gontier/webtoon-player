# Site de lecture « Player » en Astro + Svelte : conception

Date : 2026-10-10. Statut : validé en discussion, à relire.

## But

Remplacer `viewer.html` (fichier unique généré par `scripts/make_viewer.py`) par un site construit avec
un framework, au niveau d'un site publiable avec SEO. Il reste en local (pas de déploiement), mais tout
est prêt pour une mise en ligne : URL par chapitre, métadonnées, sitemap.

Hors périmètre : déploiement, mode page par page, réglage de largeur, zoom (le lecteur est conçu pour
les accueillir plus tard).

## Choix techniques

- **Astro 7** (sortie statique) pour les pages, **Svelte 5** (runes) pour l'unique îlot interactif,
  `@astrojs/sitemap`. Versions relevées sur npm le 2026-10-10 : astro 7.3.8, svelte 5.57.2,
  @astrojs/svelte 9.0.1, @astrojs/sitemap 3.7.4.
- Astro plutôt que SvelteKit : site de contenu, pas de JS hors lecteur, SEO le plus simple.
  Svelte pour le lecteur : état réactif (mode, page, progression) plus simple à faire évoluer.
- Syntaxe vérifiée dans la doc officielle à jour (Context7, `@sveltejs/mcp`), pas dans des tutoriels.

## Organisation

```
site/
  astro.config.mjs          site, trailingSlash: 'always', intégrations svelte + sitemap
  package.json              scripts dev / build / preview / check
  src/
    config.ts               nom du site, URL de prod (fictive : https://player-fr.example),
                            langue, infos série (titre, auteurs, synopsis : vides = non affichées)
    content.config.ts       collection « chapters » chargée depuis data/chapters.json, schéma zod
    data/chapters.json      écrit par scripts/make_viewer.py
    layouts/Base.astro      <html lang="fr">, <Seo>, polices, ClientRouter, en-tête, pied
    components/
      Seo.astro             title, description, canonique absolue, OG, Twitter, JSON-LD
      Header.astro, Footer.astro, ChapterCard.astro
      Reader.svelte         îlot du lecteur
    pages/
      index.astro           accueil
      chapitre/[n].astro    getStaticPaths sur la collection
      404.astro
      robots.txt.ts         pointe vers le sitemap
    styles/global.css       thème actuel (HUD sombre cyan/rouge, grain, quadrillage) en variables
  public/
    favicon.svg, manifest.webmanifest, fonts/ (Bebas Neue, Chakra Petch auto-hébergées)
```

### Données

`make_viewer.py` écrit `site/src/data/chapters.json` :
`[{ "n": 245, "pages": [{ "name": "001", "en": "...", "fr": "...", "w": 690, "h": 2000 }] }]`.
Les chemins sont relatifs à la racine du dépôt. Le schéma de la collection refuse une donnée invalide
(le build échoue au lieu d'une page cassée).

### Images

Les ~1,4 Go restent dans `chapters_en/` et `chapters_fr/` : ni copie, ni recompression.
Le site construit leurs URL avec une base réglable (`PUBLIC_IMAGE_BASE`, défaut `/`).
En local, des jonctions de dossier (Windows, sans droits admin) rendent `chapters_en/` et `chapters_fr/`
visibles par le serveur de dev et de preview sans les copier dans `dist/`. Le mécanisme exact
(middleware Vite ou jonction créée après le build) est tranché dans le plan, avec vérification que
`dist/` ne contient pas les images.

Vignettes : première page FR recadrée en haut, réduite en WebP (~400 px de large), générée par
`make_viewer.py` (Pillow) dans `site/public/thumbs/N.webp`. Servent aussi d'image Open Graph.

## Pages

### Accueil `/`

- `<h1>` Player, synopsis s'il est renseigné.
- Bouton « Reprendre au chapitre X » (petit script inline, lit `chapter` et `progress:N` ; caché sans
  progression).
- Grille des chapitres : vignette, numéro, nombre de pages, badge « lu » (`read:N`) ou « en cours »
  (`progress:N` non vide), posés par le même script.
- JSON-LD `ComicSeries` avec la liste des chapitres.

### Chapitre `/chapitre/N/`

- Titre « Player — Chapitre N », fil d'Ariane (Accueil › Chapitre N), `<h1>`.
- Lecteur (voir plus bas).
- Fin de chapitre : liens `<a>` précédent / suivant (absents au premier et au dernier chapitre).
- `<link rel="prev">` / `<link rel="next">`, JSON-LD `ComicIssue` (issueNumber, isPartOf) et
  `BreadcrumbList`, image OG = vignette.
- `alt` des planches : « Chapitre N, page P (anglais|français) ».

### 404

Message et lien vers l'accueil.

## SEO commun

- `<Seo>` unique : title, meta description, canonique absolue (depuis `site`), `og:title`,
  `og:description`, `og:url`, `og:image`, `og:type`, `og:locale` fr_FR, Twitter `summary_large_image`.
- Barre oblique finale partout ; sitemap, canoniques et liens internes identiques.
- `sitemap-index.xml`, `robots.txt`, favicon SVG, `manifest.webmanifest`.

## Lecteur

### Rendu statique (Astro)

Pour chaque page : `<img class="en">` et `<img class="fr">` avec `width`/`height`, `alt`,
`decoding="async"`, `loading="lazy"` sauf les 2 premières (`fetchpriority="high"`).
En-têtes de colonnes EN / FR. Sans JS : lecture EN|FR côte à côte.

### Îlot `Reader.svelte` (`client:load`)

Monté autour de la bande sans la re-rendre (ne pas hydrater la liste d'images).

| État | Rôle |
|---|---|
| `view` (`en` / `both` / `fr`) | classe de la bande, boutons segmentés `aria-pressed`, libellé ; changement en gardant la position (page + fraction, logique `anchor()`/`goTo()` actuelle) |
| `page` | compteur « PAGE 07 / 42 », IntersectionObserver sur la colonne visible |
| `progress` | barre de progression |
| `chromeHidden` | barre masquée en descendant, visible en remontant |

- `$state` pour ces valeurs, `$derived` pour le reste, `$effect` seulement pour les effets de bord
  (observateur, écouteurs, sauvegarde) avec nettoyage.
- `localStorage` : mêmes clés qu'aujourd'hui (`view`, `chapter`, `progress:N`) + `read:N` à la fin
  du chapitre. Lectures et écritures dans try/catch. La progression de l'ancien viewer (origine
  `file://`) n'est pas reprise automatiquement.
- Raccourcis : `←`/`→` navigation vers chapitre N±1, `1`/`2`/`3` modes, `?` aide. Ignorés avec
  Ctrl/Meta/Alt ou dans un champ.
- Préchargement : 3 premières pages du chapitre suivant après 2 s, `<link rel="prefetch">`.
- View Transitions (`<ClientRouter />`) : le lecteur se réinitialise à chaque navigation
  (écouteurs retirés, position restaurée).
- `history.scrollRestoration = 'manual'` : la position vient de la progression enregistrée.

### Barre

Logo/titre, bouton « Chapitres » (vers l'accueil ; menu sur mobile), précédent/suivant, modes.
Le `<select>` actuel disparaît.

## Accessibilité

Lien d'évitement « Aller au lecteur », focus visible, `prefers-reduced-motion`, contraste AA,
annonce du compteur de page en `aria-live="polite"`.

## Flux de travail

```
python scripts/make_viewer.py       # données + vignettes
cd site && pnpm run build && pnpm run preview
```

`CLAUDE.md` et `README.md` mis à jour. `viewer.html` et `scripts/viewer_template.html` sont gardés
jusqu'à validation du nouveau site, puis supprimés.

## Vérification

- `svelte-autofixer` sur `Reader.svelte`, `astro check`, `astro build` sans erreur.
- `dist/` sans images de chapitres.
- Navigateur (Playwright) : chapitre 225 et 264 (sans suivant), changement de mode avec position
  gardée, reprise après rechargement, raccourcis, badge « lu », largeur mobile 390 px, rendu sans JS.
- Lighthouse SEO et accessibilité ; skills `marketing:seo-audit` et `web-design-guidelines`.
