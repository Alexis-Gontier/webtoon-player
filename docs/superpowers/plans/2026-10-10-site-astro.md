# Site Astro + Svelte : plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal :** remplacer `viewer.html` par un site Astro statique (une page par chapitre, SEO complet) dont
le lecteur interactif est un îlot Svelte 5.

**Architecture :** `scripts/make_viewer.py` écrit les données (`site/src/data/chapters.json`) et les
vignettes. Astro génère accueil, pages chapitres et 404 en HTML statique ; la bande d'images est du
HTML pur, `Reader.svelte` (`client:only="svelte"`) ne pilote que les modes, le compteur, la progression
et les raccourcis. Les images restent dans `chapters_en/` et `chapters_fr/` et sont servies par un
middleware (dev) et un petit serveur `sirv` (preview), jamais copiées dans `dist/`.

**Tech Stack :** Astro 7.3.8, Svelte 5.57.2, @astrojs/svelte 9.0.1, @astrojs/sitemap 3.7.4, sirv 3.0.2,
vitest 5.0.3, @playwright/test 1.64.0, Python 3 + Pillow (déjà installé), pytest 9.

**Spec :** `docs/superpowers/specs/2026-10-10-site-astro-design.md`

## Global Constraints

- Langue du site : `fr` ; textes de l'interface en français, typographie du projet (apostrophe `’`).
- URL de production fictive : `https://player-fr.example` ; `trailingSlash: 'always'`.
- Aucune image de chapitre dans `site/dist/` ni dans `site/public/` (seules les vignettes y vont).
- Clés `localStorage` compatibles avec l'ancien lecteur : `view`, `chapter`, `progress:N`
  (JSON `{"page":p,"frac":f}`, vide = début) ; nouvelle clé `read:N` = `"1"`.
- Modes : `en`, `both`, `fr` (défaut `both`) ; raccourcis `←` `→` `1` `2` `3` `?` `Échap`.
- Infos de série (auteurs, synopsis) non inventées : champs vides = non affichés.
- Toute syntaxe Astro/Svelte douteuse se vérifie dans la doc officielle (Context7 `/withastro/docs`,
  `pnpm dlx @sveltejs/mcp get-documentation`), et `pnpm dlx @sveltejs/mcp svelte-autofixer` passe sur chaque
  `.svelte` avant de finir une tâche (skill `svelte-code-writer`).
- `viewer.html` et `scripts/viewer_template.html` restent en place et fonctionnels.
- Gestionnaire de paquets : **pnpm** uniquement (`pnpm add`, `pnpm run`, `pnpm exec`, `pnpm dlx`),
  jamais npm/npx ; un seul lockfile, `site/pnpm-lock.yaml`.
- Toutes les commandes `pnpm` se lancent depuis `site/`, les commandes Python depuis la racine.

## Fichiers

```
.gitignore                              (Tâche 0)
scripts/make_viewer.py                  modifié : + chapters.json + vignettes (Tâche 1)
tests/test_make_viewer.py               (Tâche 1)
site/
  package.json, astro.config.mjs, tsconfig.json, svelte.config.js, vitest.config.ts,
  playwright.config.ts, .gitignore                                   (Tâche 2, 6)
  integrations/chapter-images.mjs       middleware dev des images     (Tâche 2)
  scripts/serve.mjs                     serveur de preview            (Tâche 2)
  src/config.ts                         réglages du site              (Tâche 2)
  src/content.config.ts                 collection « chapters »       (Tâche 2)
  src/lib/chapters.ts                   lecture de la collection      (Tâche 2)
  src/lib/urls.ts, storage.ts, position.ts   logique pure testée      (Tâche 3)
  src/styles/global.css                 thème                         (Tâche 4)
  src/layouts/Base.astro, src/components/Seo.astro, Header.astro, Footer.astro   (Tâche 4)
  public/favicon.svg, public/manifest.webmanifest                    (Tâche 4)
  src/pages/chapitre/[n].astro                                        (Tâche 5)
  src/components/Reader.svelte                                        (Tâche 6)
  src/pages/index.astro, src/components/ChapterCard.astro, src/pages/404.astro,
  src/pages/robots.txt.ts                                             (Tâche 7)
  tests/unit/*.test.ts, tests/dist/*.test.ts, tests/e2e/*.spec.ts
CLAUDE.md, README.md                    (Tâche 8)
```

---

### Tâche 0 : dépôt git (à confirmer avec l'utilisateur)

Le dossier n'est pas un dépôt git. Si l'utilisateur accepte, initialiser pour pouvoir committer chaque
tâche ; sinon sauter cette tâche et ignorer les étapes « Commit » suivantes.

**Files :** Create `.gitignore`

- [ ] **Étape 1 : écrire `.gitignore`**

```gitignore
chapters_en/
chapters_fr/
inventaire/
models/*.onnx
__pycache__/
site/node_modules/
site/dist/
site/.astro/
site/public/thumbs/
site/test-results/
site/playwright-report/
```

- [ ] **Étape 2 : initialiser et committer l'existant**

```bash
git init
git add -A
git commit -m "chore: état initial du projet"
```

---

### Tâche 1 : `make_viewer.py` écrit les données du site et les vignettes

**Files :**
- Modify : `scripts/make_viewer.py`
- Create : `tests/test_make_viewer.py`

**Interfaces :**
- Produces : `site/src/data/chapters.json` = liste triée de
  `{"id": "245", "n": 245, "pages": [{"name": "001", "en": "chapters_en/chapter-245/001.webp", "fr": "chapters_fr/chapter-245/001.webp", "w": 800, "h": 8337}]}` ;
  `site/public/thumbs/<n>.webp` (400×560, haut de la 1re page FR).
- Fonctions Python : `chapter_data(root: Path) -> list[dict]`, `site_data(chapters) -> list[dict]`,
  `make_thumb(src: Path, dest: Path) -> None`, `write_site(root: Path, chapters) -> None`.

- [ ] **Étape 1 : écrire le test qui échoue**

```python
# tests/test_make_viewer.py
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import make_viewer  # noqa: E402


def fake_repo(tmp_path: Path) -> Path:
    for lang in ("en", "fr"):
        for n in (226, 225):
            d = tmp_path / f"chapters_{lang}" / f"chapter-{n}"
            d.mkdir(parents=True)
            for page in ("001", "002"):
                Image.new("RGB", (800, 1600), "white").save(d / f"{page}.webp")
    return tmp_path


def test_site_data_is_sorted_with_ids(tmp_path):
    root = fake_repo(tmp_path)
    data = make_viewer.site_data(make_viewer.chapter_data(root))
    assert [c["id"] for c in data] == ["225", "226"]
    assert data[0]["n"] == 225
    assert data[0]["pages"][0] == {
        "name": "001",
        "en": "chapters_en/chapter-225/001.webp",
        "fr": "chapters_fr/chapter-225/001.webp",
        "w": 800,
        "h": 1600,
    }


def test_write_site_creates_json_and_thumbs(tmp_path):
    root = fake_repo(tmp_path)
    make_viewer.write_site(root, make_viewer.chapter_data(root))
    data = json.loads((root / "site/src/data/chapters.json").read_text(encoding="utf-8"))
    assert len(data) == 2
    thumb = Image.open(root / "site/public/thumbs/225.webp")
    assert thumb.size == (400, 560)
```

- [ ] **Étape 2 : vérifier l'échec**

Run : `python -m pytest tests/test_make_viewer.py -v`
Expected : FAIL, `chapter_data() takes 0 positional arguments` / `AttributeError: site_data`.

- [ ] **Étape 3 : implémenter**

Remplacer `scripts/make_viewer.py` par :

```python
"""Génère les données du lecteur.

- site/src/data/chapters.json et site/public/thumbs/N.webp pour le site Astro (dossier site/) ;
- viewer.html (ancien lecteur, gardé tant que le site n'est pas validé).

Usage : python scripts/make_viewer.py
À relancer après chaque rendu pour mettre à jour la liste des chapitres.
"""

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / "viewer_template.html"
THUMB_SIZE = (400, 560)


def chapter_data(root=ROOT):
    chapters = []
    for fr_dir in sorted((root / "chapters_fr").glob("chapter-*"), key=lambda p: int(p.name.split("-")[1])):
        en_dir = root / "chapters_en" / fr_dir.name
        pages = []
        for fr in sorted(fr_dir.iterdir()):
            en = next(en_dir.glob(fr.stem + ".*"), None)
            if not en:
                continue
            width, height = Image.open(fr).size
            pages.append({
                "name": fr.stem,
                "en": en.relative_to(root).as_posix(),
                "fr": fr.relative_to(root).as_posix(),
                "w": width,
                "h": height,
            })
        chapters.append({"name": fr_dir.name.split("-")[1], "pages": pages})
    return chapters


def site_data(chapters):
    # Format de la collection Astro : un id texte par entrée (file() loader).
    return [{"id": c["name"], "n": int(c["name"]), "pages": c["pages"]} for c in chapters if c["pages"]]


def make_thumb(src, dest):
    # Haut de la première page, au ratio de la vignette ; refait seulement si la page a changé.
    if dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime:
        return
    with Image.open(src) as im:
        width = im.width
        crop = im.convert("RGB").crop((0, 0, width, min(im.height, round(width * THUMB_SIZE[1] / THUMB_SIZE[0]))))
        crop.resize(THUMB_SIZE, Image.LANCZOS).save(dest, "WEBP", quality=80)


def write_site(root, chapters):
    data = site_data(chapters)
    out = root / "site" / "src" / "data" / "chapters.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    thumbs = root / "site" / "public" / "thumbs"
    thumbs.mkdir(parents=True, exist_ok=True)
    for c in data:
        make_thumb(root / c["pages"][0]["fr"], thumbs / f"{c['n']}.webp")


def main():
    chapters = chapter_data()
    write_site(ROOT, chapters)
    template = TEMPLATE.read_text(encoding="utf-8")
    (ROOT / "viewer.html").write_text(template.replace("/*DATA*/[]", json.dumps(chapters, ensure_ascii=False)), encoding="utf-8")
    print("site/src/data/chapters.json, vignettes et viewer.html générés")


if __name__ == "__main__":
    main()
```

- [ ] **Étape 4 : vérifier le succès, puis lancer pour de vrai**

Run : `python -m pytest tests/test_make_viewer.py -v` → 2 PASS.
Run : `python scripts/make_viewer.py` → `site/src/data/chapters.json` contient 40 entrées (225 à 264),
`site/public/thumbs/` 40 fichiers, `viewer.html` toujours fonctionnel.

- [ ] **Étape 5 : commit**

```bash
git add scripts/make_viewer.py tests/test_make_viewer.py
git commit -m "feat(viewer): données et vignettes pour le site Astro"
```

---

### Tâche 2 : squelette Astro, collection et service des images

**Files :** Create `site/package.json`, `site/pnpm-workspace.yaml`, `site/pnpm-lock.yaml` (pnpm), `site/astro.config.mjs`, `site/tsconfig.json`,
`site/svelte.config.js`, `site/.gitignore`, `site/integrations/chapter-images.mjs`,
`site/scripts/serve.mjs`, `site/src/config.ts`, `site/src/content.config.ts`,
`site/src/lib/chapters.ts`, `site/src/pages/index.astro` (provisoire), `site/src/pages/404.astro`
(provisoire), `site/tests/dist/build.test.ts`, `site/vitest.config.ts`.

**Interfaces :**
- Consumes : `site/src/data/chapters.json` (Tâche 1).
- Produces : `getChapters(): Promise<Chapter[]>` dans `src/lib/chapters.ts` avec
  `type Chapter = { n: number; pages: Page[] }`, `type Page = { name: string; en: string; fr: string; w: number; h: number }` ;
  `SITE` et `IMAGE_BASE` dans `src/config.ts` ; `imageHandlers()` dans `integrations/chapter-images.mjs` ;
  `pnpm run dev` / `pnpm run build` / `pnpm run preview` (port 4321).

- [ ] **Étape 1 : installer**

Gestionnaire de paquets : **pnpm** (11.27 installé sur la machine). Créer `site/package.json` :

```json
{
  "name": "player-fr",
  "private": true,
  "type": "module",
  "packageManager": "pnpm@11.27.1",
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "node scripts/serve.mjs",
    "check": "astro check",
    "test": "vitest run tests/unit",
    "test:dist": "vitest run tests/dist",
    "e2e": "playwright test"
  }
}
```

et `site/pnpm-workspace.yaml` : depuis pnpm 10, les scripts d'installation des dépendances sont
bloqués par défaut ; en pnpm 11 on les autorise un par un avec `allowBuilds` (les anciens
`onlyBuiltDependencies` sont ignorés).

```yaml
allowBuilds:
  esbuild: true
  sharp: false   # pas d'optimisation d'images Astro : les planches sont servies telles quelles
```

```bash
cd site
pnpm add astro@7.3.8 svelte@5.57.2 @astrojs/svelte@9.0.1 @astrojs/sitemap@3.7.4 sirv@3.0.2 @fontsource/bebas-neue @fontsource/chakra-petch
pnpm add -D @astrojs/check typescript vitest@5.0.3 @playwright/test@1.64.0
pnpm ignored-builds
```

`pnpm ignored-builds` doit ne rien lister d'indécis : si un paquet y apparaît, l'ajouter à
`allowBuilds` (`true` seulement s'il est nécessaire au build, sinon `false`) et relancer `pnpm install`.
Si une version exacte n'existe plus, prendre la dernière de la même majeure et le noter.

- [ ] **Étape 2 : écrire le test de build qui échoue**

```ts
// site/vitest.config.ts
import { defineConfig } from 'vitest/config';
export default defineConfig({ test: { include: ['tests/unit/**/*.test.ts', 'tests/dist/**/*.test.ts'] } });
```

```ts
// site/tests/dist/build.test.ts
import { existsSync, readdirSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const dist = new URL('../../dist/', import.meta.url);

describe('build', () => {
  it('produit l’accueil et la 404', () => {
    expect(existsSync(new URL('index.html', dist))).toBe(true);
    expect(existsSync(new URL('404.html', dist))).toBe(true);
  });
  it('ne copie aucune image de chapitre', () => {
    const top = readdirSync(dist);
    expect(top).not.toContain('chapters_en');
    expect(top).not.toContain('chapters_fr');
  });
});
```

Run : `pnpm run test:dist` → FAIL (pas de `dist/`).

- [ ] **Étape 3 : configuration**

```js
// site/astro.config.mjs
import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
import sitemap from '@astrojs/sitemap';
import { chapterImages } from './integrations/chapter-images.mjs';

export default defineConfig({
  site: 'https://player-fr.example',
  trailingSlash: 'always',
  prefetch: true,
  integrations: [svelte(), sitemap(), chapterImages()],
});
```

```js
// site/svelte.config.js
import { vitePreprocess } from '@astrojs/svelte';
export default { preprocess: vitePreprocess() };
```

```json
// site/tsconfig.json
{ "extends": "astro/tsconfigs/strict", "include": [".astro/types.d.ts", "**/*"], "exclude": ["dist"] }
```

```gitignore
# site/.gitignore
node_modules/
dist/
.astro/
public/thumbs/
test-results/
playwright-report/
```

- [ ] **Étape 4 : service des images (dev et preview)**

```js
// site/integrations/chapter-images.mjs
// Les planches restent dans chapters_en/ et chapters_fr/ à la racine du dépôt : servies telles quelles,
// jamais copiées dans dist/ (1,4 Go). En ligne, PUBLIC_IMAGE_BASE pointerait vers un CDN.
import sirv from 'sirv';
import { fileURLToPath } from 'node:url';

const REPO = fileURLToPath(new URL('../../', import.meta.url));
const DIRS = ['chapters_en', 'chapters_fr'];

export function imageHandlers() {
  return DIRS.map(dir => [`/${dir}`, sirv(REPO + dir, { dev: true })]);
}

export function chapterImages() {
  return {
    name: 'chapter-images',
    hooks: {
      'astro:server:setup': ({ server }) => {
        for (const [prefix, handler] of imageHandlers()) server.middlewares.use(prefix, handler);
      },
    },
  };
}
```

```js
// site/scripts/serve.mjs
// Preview du build : dist/ + planches du dépôt, 404.html pour le reste.
import http from 'node:http';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import sirv from 'sirv';
import { imageHandlers } from '../integrations/chapter-images.mjs';

const dist = new URL('../dist/', import.meta.url);
const notFound = readFileSync(new URL('404.html', dist));
const site = sirv(fileURLToPath(dist), { etag: true });
const images = imageHandlers();
const port = Number(process.env.PORT) || 4321;

http.createServer((req, res) => {
  const fallback = () => {
    res.writeHead(404, { 'content-type': 'text/html; charset=utf-8' });
    res.end(notFound);
  };
  const match = images.find(([prefix]) => req.url.startsWith(prefix + '/'));
  if (match) {
    req.url = req.url.slice(match[0].length);
    return match[1](req, res, fallback);
  }
  site(req, res, fallback);
}).listen(port, () => console.log(`http://localhost:${port}/`));
```

- [ ] **Étape 5 : réglages, collection, accès aux données**

```ts
// site/src/config.ts
export const SITE = {
  name: 'Player — Traduction française',
  shortName: 'Player FR',
  lang: 'fr',
  locale: 'fr_FR',
  description: 'Le webtoon Player en version originale et en traduction française, chapitre par chapitre, avec lecture côte à côte.',
  series: {
    title: 'Player',
    authors: [] as string[], // à remplir : ne s’affiche pas tant que c’est vide
    synopsis: '',
  },
};

// Racine des planches : '/' en local (servies depuis le dépôt), URL d’un CDN en ligne.
export const IMAGE_BASE: string = import.meta.env.PUBLIC_IMAGE_BASE ?? '/';
```

```ts
// site/src/content.config.ts
import { defineCollection } from 'astro:content';
import { file } from 'astro/loaders';
import { z } from 'astro/zod';

const page = z.object({
  name: z.string(),
  en: z.string(),
  fr: z.string(),
  w: z.number().int().positive(),
  h: z.number().int().positive(),
});

const chapters = defineCollection({
  loader: file('src/data/chapters.json'),
  schema: z.object({ n: z.number().int().positive(), pages: z.array(page).min(1) }),
});

export const collections = { chapters };
```

```ts
// site/src/lib/chapters.ts
import { getCollection } from 'astro:content';

export type Page = { name: string; en: string; fr: string; w: number; h: number };
export type Chapter = { n: number; pages: Page[] };

export async function getChapters(): Promise<Chapter[]> {
  return (await getCollection('chapters')).map(entry => entry.data).sort((a, b) => a.n - b.n);
}
```

- [ ] **Étape 6 : pages provisoires (remplacées en Tâche 7)**

```astro
---
// site/src/pages/index.astro (provisoire)
import { getChapters } from '../lib/chapters';
const chapters = await getChapters();
---
<html lang="fr"><head><meta charset="utf-8"><title>Player</title></head>
<body><ul>{chapters.map(c => <li>{c.n} ({c.pages.length} pages)</li>)}</ul></body></html>
```

```astro
---
// site/src/pages/404.astro (provisoire)
---
<html lang="fr"><head><meta charset="utf-8"><title>Page introuvable</title></head><body><a href="/">Accueil</a></body></html>
```

- [ ] **Étape 7 : vérifier**

Run : `pnpm exec astro sync && pnpm run build && pnpm run test:dist` → PASS.
Run : `pnpm run preview` (en arrière-plan), puis
`curl -s -o /dev/null -w "%{http_code}" http://localhost:4321/chapters_fr/chapter-245/001.webp` → `200`,
`curl -s -o /dev/null -w "%{http_code}" http://localhost:4321/nimporte/` → `404`. Arrêter le serveur.
Run : `pnpm run dev` puis le même `curl` sur le port de dev (4321) → `200`. Arrêter.

- [ ] **Étape 8 : commit**

```bash
git add site
git commit -m "feat(site): squelette Astro, collection des chapitres, service des planches"
```

---

### Tâche 3 : logique pure testée (URL, stockage, position)

**Files :** Create `site/src/lib/urls.ts`, `site/src/lib/storage.ts`, `site/src/lib/position.ts`,
`site/tests/unit/urls.test.ts`, `site/tests/unit/storage.test.ts`, `site/tests/unit/position.test.ts`.

**Interfaces (Produces) :**
- `urls.ts` : `chapterPath(n: number): string` → `/chapitre/245/` ; `imageUrl(base: string, path: string): string` ;
  `absolute(path: string, site: URL | string): string`.
- `storage.ts` : `type View = 'en' | 'both' | 'fr'` ; `VIEWS: readonly View[]` ; `parseView(raw: string | null): View` ;
  `progressKey(n: number): string` ; `readKey(n: number): string` ;
  `interface KV { getItem(k: string): string | null; setItem(k: string, v: string): void; removeItem(k: string): void }` ;
  `type Store = { get(k: string): string | null; set(k: string, v: string): void }` ;
  `createStore(kv?: KV | null): Store` (une valeur `''` supprime la clé) ;
  `chapterStatus(store: Store, n: number): 'read' | 'progress' | null`.
- `position.ts` : `type Anchor = { page: number; frac: number }` ; `type Box = { top: number; bottom: number; height: number }` ;
  `anchorFrom(boxes: Box[]): Anchor | null` ; `scrollTargetFor(a: Anchor | null, boxes: Box[], scrollY: number): number` ;
  `parseAnchor(raw: string | null): Anchor | null`.

- [ ] **Étape 1 : tests qui échouent**

```ts
// site/tests/unit/urls.test.ts
import { describe, expect, it } from 'vitest';
import { absolute, chapterPath, imageUrl } from '../../src/lib/urls';

describe('urls', () => {
  it('chapterPath finit par une barre oblique', () => expect(chapterPath(245)).toBe('/chapitre/245/'));
  it('imageUrl joint base et chemin sans double barre', () => {
    expect(imageUrl('/', 'chapters_fr/chapter-245/001.webp')).toBe('/chapters_fr/chapter-245/001.webp');
    expect(imageUrl('https://cdn.example/', 'chapters_fr/a.webp')).toBe('https://cdn.example/chapters_fr/a.webp');
    expect(imageUrl('https://cdn.example', 'chapters_fr/a.webp')).toBe('https://cdn.example/chapters_fr/a.webp');
  });
  it('absolute rend une URL complète', () =>
    expect(absolute('/thumbs/245.webp', 'https://player-fr.example')).toBe('https://player-fr.example/thumbs/245.webp'));
});
```

```ts
// site/tests/unit/storage.test.ts
import { describe, expect, it } from 'vitest';
import { chapterStatus, createStore, parseView, progressKey, readKey, type KV } from '../../src/lib/storage';

function memory(): KV & { data: Map<string, string> } {
  const data = new Map<string, string>();
  return { data, getItem: k => data.get(k) ?? null, setItem: (k, v) => void data.set(k, v), removeItem: k => void data.delete(k) };
}

describe('storage', () => {
  it('clés compatibles avec l’ancien lecteur', () => {
    expect(progressKey(245)).toBe('progress:245');
    expect(readKey(245)).toBe('read:245');
  });
  it('parseView refuse les valeurs inconnues', () => {
    expect(parseView('fr')).toBe('fr');
    expect(parseView('xx')).toBe('both');
    expect(parseView(null)).toBe('both');
  });
  it('set("") supprime la clé', () => {
    const kv = memory();
    const store = createStore(kv);
    store.set('a', '1');
    store.set('a', '');
    expect(kv.data.has('a')).toBe(false);
  });
  it('sans stockage disponible, ne lève pas', () => {
    const store = createStore(null);
    store.set('a', '1');
    expect(store.get('a')).toBeNull();
  });
  it('un stockage qui lève est ignoré', () => {
    const broken: KV = { getItem: () => { throw new Error(); }, setItem: () => { throw new Error(); }, removeItem: () => { throw new Error(); } };
    const store = createStore(broken);
    expect(() => store.set('a', '1')).not.toThrow();
    expect(store.get('a')).toBeNull();
  });
  it('chapterStatus', () => {
    const store = createStore(memory());
    expect(chapterStatus(store, 245)).toBeNull();
    store.set('progress:245', '{"page":3,"frac":0.5}');
    expect(chapterStatus(store, 245)).toBe('progress');
    store.set('read:245', '1');
    expect(chapterStatus(store, 245)).toBe('read');
  });
});
```

```ts
// site/tests/unit/position.test.ts
import { describe, expect, it } from 'vitest';
import { anchorFrom, parseAnchor, scrollTargetFor, type Box } from '../../src/lib/position';

const box = (top: number, height: number): Box => ({ top, bottom: top + height, height });

describe('position', () => {
  it('aucune image : pas d’ancre', () => expect(anchorFrom([])).toBeNull());
  it('page en haut de l’écran et fraction passée', () => {
    // page 1 déjà passée, page 2 commence 500 px au-dessus du haut de l’écran
    expect(anchorFrom([box(-2500, 2000), box(-500, 2000)])).toEqual({ page: 1, frac: 0.25 });
  });
  it('tout est passé : dernière page, fraction 1', () =>
    expect(anchorFrom([box(-4000, 2000), box(-2000, 1999)])).toEqual({ page: 1, frac: 1 }));
  it('début de chapitre : défilement 0', () =>
    expect(scrollTargetFor({ page: 0, frac: 0 }, [box(300, 2000)], 0)).toBe(0));
  it('cible = haut de la page + fraction de sa hauteur', () =>
    expect(scrollTargetFor({ page: 1, frac: 0.5 }, [box(100, 1000), box(1100, 2000)], 400)).toBe(1100 + 400 + 1000));
  it('ancre hors limites : début', () => expect(scrollTargetFor({ page: 9, frac: 0.5 }, [box(0, 10)], 0)).toBe(0));
  it('parseAnchor valide le JSON', () => {
    expect(parseAnchor('{"page":2,"frac":0.3}')).toEqual({ page: 2, frac: 0.3 });
    expect(parseAnchor('')).toBeNull();
    expect(parseAnchor('{oops')).toBeNull();
    expect(parseAnchor('{"page":-1,"frac":0.3}')).toBeNull();
    expect(parseAnchor('{"page":1,"frac":2}')).toBeNull();
  });
});
```

Run : `pnpm test` → FAIL (modules absents).

- [ ] **Étape 2 : implémenter**

```ts
// site/src/lib/urls.ts
export const chapterPath = (n: number) => `/chapitre/${n}/`;

export const imageUrl = (base: string, path: string) => `${base.replace(/\/+$/, '')}/${path.replace(/^\/+/, '')}`;

export const absolute = (path: string, site: URL | string) => new URL(path, site).href;
```

```ts
// site/src/lib/storage.ts
export type View = 'en' | 'both' | 'fr';
export const VIEWS: readonly View[] = ['en', 'both', 'fr'];

export const parseView = (raw: string | null): View => (VIEWS as readonly string[]).includes(raw ?? '') ? (raw as View) : 'both';
export const progressKey = (n: number) => `progress:${n}`;
export const readKey = (n: number) => `read:${n}`;

export interface KV {
  getItem(k: string): string | null;
  setItem(k: string, v: string): void;
  removeItem(k: string): void;
}
export type Store = { get(k: string): string | null; set(k: string, v: string): void };

function browserStorage(): KV | null {
  // Navigation privée, stockage bloqué ou rendu serveur : pas de stockage, sans erreur.
  try { return window.localStorage; } catch { return null; }
}

export function createStore(kv: KV | null = browserStorage()): Store {
  return {
    get(k) { try { return kv?.getItem(k) ?? null; } catch { return null; } },
    set(k, v) { try { if (v === '') kv?.removeItem(k); else kv?.setItem(k, v); } catch { /* stockage indisponible */ } },
  };
}

export function chapterStatus(store: Store, n: number): 'read' | 'progress' | null {
  if (store.get(readKey(n)) === '1') return 'read';
  return store.get(progressKey(n)) ? 'progress' : null;
}
```

```ts
// site/src/lib/position.ts
// Position de lecture : la page en haut de l'écran et la fraction déjà passée de cette page.
// Indépendant de la largeur, donc des modes EN / EN|FR / FR.
export type Anchor = { page: number; frac: number };
export type Box = { top: number; bottom: number; height: number };

export function anchorFrom(boxes: Box[]): Anchor | null {
  if (!boxes.length) return null;
  const page = boxes.findIndex(b => b.bottom > 0);
  if (page < 0) return { page: boxes.length - 1, frac: 1 };
  const b = boxes[page];
  return { page, frac: Math.max(0, -b.top) / b.height };
}

export function scrollTargetFor(a: Anchor | null, boxes: Box[], scrollY: number): number {
  const b = a ? boxes[a.page] : undefined;
  if (!a || !b || (a.page === 0 && a.frac === 0)) return 0;
  return b.top + scrollY + a.frac * b.height;
}

export function parseAnchor(raw: string | null): Anchor | null {
  if (!raw) return null;
  try {
    const { page, frac } = JSON.parse(raw);
    return Number.isInteger(page) && page >= 0 && typeof frac === 'number' && frac >= 0 && frac <= 1 ? { page, frac } : null;
  } catch {
    return null;
  }
}
```

- [ ] **Étape 3 : vérifier**

Run : `pnpm test` → tous PASS.

- [ ] **Étape 4 : commit**

```bash
git add site/src/lib site/tests/unit
git commit -m "feat(site): logique d’URL, de stockage et de position testée"
```

---

### Tâche 4 : layout, SEO, thème, polices, favicon, manifeste

**Files :** Create `site/src/styles/global.css`, `site/src/layouts/Base.astro`,
`site/src/components/Seo.astro`, `site/src/components/Header.astro`, `site/src/components/Footer.astro`,
`site/public/favicon.svg`, `site/public/manifest.webmanifest`, `site/tests/dist/seo.test.ts`.
Modify : `site/src/pages/index.astro` (utilise `Base`, contenu toujours provisoire).

**Interfaces :**
- Consumes : `SITE` (config), `absolute`, `chapterPath` (urls), `getChapters`.
- Produces : `Base.astro` props
  `{ title: string; description: string; image?: string; type?: 'website' | 'article'; noindex?: boolean; jsonLd?: object | object[]; prev?: number | null; next?: number | null }`
  (+ slot) ; `Header.astro` props `{ prev?: number | null; next?: number | null }` ; dans le header,
  l'élément `<div class="progress" id="progress">` que le lecteur remplit.
  Attributs sur `<html>` : `data-view` (posé avant l'affichage), `data-chrome` (`hidden` ou absent).

- [ ] **Étape 1 : test du `<head>` qui échoue**

```ts
// site/tests/dist/seo.test.ts
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const html = (path: string) => readFileSync(new URL(`../../dist/${path}`, import.meta.url), 'utf-8');

describe('head commun (accueil)', () => {
  const page = html('index.html');
  it('langue, titre, description', () => {
    expect(page).toMatch(/<html lang="fr"/);
    expect(page).toMatch(/<title>Player — Traduction française<\/title>/);
    expect(page).toMatch(/<meta name="description" content="[^"]+"/);
  });
  it('canonique absolue avec barre oblique finale', () =>
    expect(page).toContain('<link rel="canonical" href="https://player-fr.example/"'));
  it('Open Graph et Twitter', () => {
    for (const p of ['og:title', 'og:description', 'og:url', 'og:image', 'og:type', 'og:locale'])
      expect(page).toContain(`property="${p}"`);
    expect(page).toContain('name="twitter:card" content="summary_large_image"');
    expect(page).toMatch(/property="og:image" content="https:\/\/player-fr\.example\/thumbs\/\d+\.webp"/);
  });
  it('favicon, manifeste, sitemap', () => {
    expect(page).toContain('href="/favicon.svg"');
    expect(page).toContain('href="/manifest.webmanifest"');
    expect(page).toContain('href="/sitemap-index.xml"');
  });
  it('pas de Google Fonts', () => expect(page).not.toContain('fonts.googleapis.com'));
  it('lien d’évitement', () => expect(page).toContain('class="skip"'));
});
```

Run : `pnpm run build && pnpm run test:dist` → FAIL.

- [ ] **Étape 2 : thème `global.css`**

Créer `site/src/styles/global.css` en reprenant **les lignes 13 à 177 de `scripts/viewer_template.html`**
(variables `:root`, fond, grain, quadrillage, barre, boutons, carte de titre, bande, compteur, fin,
animations, mobile), avec ces remplacements de sélecteurs, partout :

| Ancien | Nouveau |
|---|---|
| `body.both` | `[data-view="both"]` |
| `body.fr .strip .en, body.en .strip .fr` | `[data-view="fr"] .strip .en, [data-view="en"] .strip .fr` |
| `body:not(.both) .col-head` | `:root:not([data-view="both"]) .col-head` |
| `body.chrome-hidden` | `[data-chrome="hidden"]` |
| `--hud: "Chakra Petch", …` / `--display: "Bebas Neue", …` | inchangés (polices auto-hébergées, étape 4) |

Supprimer les règles `.chapter-select` (lignes 81-86 et sa mention ligne 87) : le `<select>` disparaît.
Remplacer `.icon-btn:disabled, .end-btn:disabled` par `.icon-btn[aria-disabled="true"]` (les
boutons deviennent des liens). Ajouter `text-decoration: none;` à `.icon-btn, .end-btn` et
`display: inline-grid; place-items: center;` à `.end-btn`.

Puis ajouter à la fin :

```css
/* ---------- Ajouts du site ---------- */
a { color: inherit; }
.skip {
  position: absolute; left: 12px; top: -60px; z-index: 50; padding: 10px 14px;
  background: var(--cyan); color: var(--ink); font-weight: 700; text-decoration: none;
}
.skip:focus { top: 12px; }
:focus-visible { outline: 1px solid var(--cyan); outline-offset: 2px; }
.logo { text-decoration: none; }
.site-nav { display: flex; align-items: center; gap: 6px; justify-self: end; }
.nav-link {
  height: 36px; padding: 0 14px; display: inline-grid; place-items: center; text-decoration: none;
  font: 600 13px var(--hud); letter-spacing: .06em; text-transform: uppercase; color: var(--text);
  border: 1px solid var(--line-strong);
  clip-path: polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px);
}
.nav-link:hover { color: var(--cyan); border-color: var(--cyan); }
.crumbs { position: relative; z-index: 1; width: min(690px, 100% - 32px); margin: 24px auto 0; font-size: 12px; letter-spacing: .1em; color: var(--muted); text-transform: uppercase; }
[data-view="both"] .crumbs { width: min(1100px, 100% - 32px); }
.crumbs a { color: var(--cyan); text-decoration: none; }
.view-label { display: none; }
[data-view="en"] .view-label[data-for="en"], [data-view="both"] .view-label[data-for="both"], [data-view="fr"] .view-label[data-for="fr"] { display: inline; }
.site-footer { position: relative; z-index: 1; padding: 32px 16px 48px; text-align: center; color: var(--muted); font-size: 12px; letter-spacing: .1em; }
.strip:focus { outline: none; }
```

- [ ] **Étape 3 : composants**

```astro
---
// site/src/components/Seo.astro
import { SITE } from '../config';
import { absolute } from '../lib/urls';

interface Props {
  title: string;
  description: string;
  image: string;
  type: 'website' | 'article';
  noindex: boolean;
  jsonLd: object[];
  prev: number | null;
  next: number | null;
}
const { title, description, image, type, noindex, jsonLd, prev, next } = Astro.props;
const site = Astro.site!;
const canonical = absolute(Astro.url.pathname, site);
const imageUrl = absolute(image, site);
---
<title>{title}</title>
<meta name="description" content={description} />
{noindex ? <meta name="robots" content="noindex" /> : <link rel="canonical" href={canonical} />}
{prev !== null && <link rel="prev" href={absolute(`/chapitre/${prev}/`, site)} />}
{next !== null && <link rel="next" href={absolute(`/chapitre/${next}/`, site)} />}
<meta property="og:site_name" content={SITE.name} />
<meta property="og:title" content={title} />
<meta property="og:description" content={description} />
<meta property="og:url" content={canonical} />
<meta property="og:image" content={imageUrl} />
<meta property="og:type" content={type} />
<meta property="og:locale" content={SITE.locale} />
<meta name="twitter:card" content="summary_large_image" />
{jsonLd.map(data => <script type="application/ld+json" set:html={JSON.stringify(data)} />)}
```

```astro
---
// site/src/components/Header.astro
import { chapterPath } from '../lib/urls';
interface Props { prev?: number | null; next?: number | null }
const { prev = null, next = null } = Astro.props;
const onChapter = prev !== null || next !== null;
---
<header class:list={['bar', { 'has-seg': onChapter }]}>
  <a class="logo" href="/" aria-label="Player, accueil"><span class="mark"></span>PLAYER<small>EN / FR</small></a>
  <nav class="site-nav" aria-label="Navigation">
    {onChapter && (prev !== null
      ? <a class="icon-btn" href={chapterPath(prev)} title="Chapitre précédent (←)" aria-label="Chapitre précédent">‹</a>
      : <span class="icon-btn" aria-disabled="true">‹</span>)}
    <a class="nav-link" href="/#chapitres">Chapitres</a>
    {onChapter && (next !== null
      ? <a class="icon-btn" href={chapterPath(next)} title="Chapitre suivant (→)" aria-label="Chapitre suivant">›</a>
      : <span class="icon-btn" aria-disabled="true">›</span>)}
  </nav>
  <div class="progress" id="progress"></div>
</header>
```

Note CSS : la grille de `.bar` passe à 2 colonnes (`grid-template-columns: 1fr auto`) puisque la
navigation est à droite ; le `.seg` du lecteur reste en `position: fixed` à droite — sur les pages
chapitre, ajouter `.has-seg .site-nav { margin-right: 260px; }` en bureau seulement (dans un
`@media (min-width: 761px)`), pour ne pas passer sous les boutons de mode. (`data-view` est posé sur
toutes les pages, il ne peut pas servir à repérer les pages chapitre.)

```astro
---
// site/src/components/Footer.astro
---
<footer class="site-footer">
  <p>Traduction française faite pour une lecture personnelle. « Player » appartient à ses auteurs.</p>
</footer>
```

```astro
---
// site/src/layouts/Base.astro
import '@fontsource/bebas-neue';
import '@fontsource/chakra-petch/400.css';
import '@fontsource/chakra-petch/500.css';
import '@fontsource/chakra-petch/600.css';
import '@fontsource/chakra-petch/700.css';
import '../styles/global.css';
import { ClientRouter } from 'astro:transitions';
import Seo from '../components/Seo.astro';
import Header from '../components/Header.astro';
import Footer from '../components/Footer.astro';
import { SITE } from '../config';
import { getChapters } from '../lib/chapters';

interface Props {
  title: string;
  description: string;
  image?: string;
  type?: 'website' | 'article';
  noindex?: boolean;
  jsonLd?: object | object[];
  prev?: number | null;
  next?: number | null;
}
const latest = (await getChapters()).at(-1)!;
const {
  title, description, image = `/thumbs/${latest.n}.webp`, type = 'website', noindex = false,
  jsonLd = [], prev = null, next = null,
} = Astro.props;
---
<!doctype html>
<html lang={SITE.lang}>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="theme-color" content="#07090d" />
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
  <link rel="manifest" href="/manifest.webmanifest" />
  <link rel="sitemap" href="/sitemap-index.xml" />
  <Seo {title} {description} {image} {type} {noindex} jsonLd={[jsonLd].flat()} {prev} {next} />
  <script is:inline>
    // Mode d’affichage posé avant le premier rendu (pas de saut EN|FR -> FR), et après chaque navigation.
    (() => {
      const apply = () => {
        let v = null;
        try { v = localStorage.getItem('view'); } catch {}
        document.documentElement.dataset.view = ['en', 'both', 'fr'].includes(v) ? v : 'both';
      };
      apply();
      if (!window.__playerView) {
        window.__playerView = true;
        document.addEventListener('astro:after-swap', apply);
      }
    })();
  </script>
  <ClientRouter />
</head>
<body>
  <a class="skip" href="#contenu">Aller au contenu</a>
  <Header {prev} {next} />
  <main id="contenu" tabindex="-1">
    <slot />
  </main>
  <Footer />
</body>
</html>
```

(Sur les pages chapitre, la Tâche 5 fait pointer le lien d’évitement vers `#strip` en ajoutant
`id="strip"` et `tabindex="-1"` à la bande ; le lien générique `#contenu` reste valable partout.)

- [ ] **Étape 4 : fichiers publics**

```svg
<!-- site/public/favicon.svg -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" fill="#07090d"/><rect x="9" y="9" width="14" height="14" fill="none" stroke="#5ce1ff" stroke-width="3" transform="rotate(45 16 16)"/></svg>
```

```json
{
  "name": "Player — Traduction française",
  "short_name": "Player FR",
  "lang": "fr",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#07090d",
  "theme_color": "#07090d",
  "icons": [{ "src": "/favicon.svg", "sizes": "any", "type": "image/svg+xml" }]
}
```
(fichier `site/public/manifest.webmanifest`)

Modifier `site/src/pages/index.astro` provisoire pour envelopper la liste dans
`<Base title="Player — Traduction française" description={SITE.description}>…</Base>`.

- [ ] **Étape 5 : vérifier**

Run : `pnpm run check && pnpm run build && pnpm run test:dist` → PASS, 0 erreur `astro check`.

- [ ] **Étape 6 : commit**

```bash
git add site
git commit -m "feat(site): layout, SEO commun, thème et polices auto-hébergées"
```

---

### Tâche 5 : page chapitre statique

**Files :** Create `site/src/pages/chapitre/[n].astro`, `site/tests/dist/chapter.test.ts`.

**Interfaces :**
- Consumes : `getChapters`, `chapterPath`, `imageUrl`, `absolute`, `IMAGE_BASE`, `SITE`, `Base`.
- Produces : dans le HTML, `#strip[data-chapter][data-total]` contenant les `.col-head.en`,
  `.col-head.fr` puis, pour chaque page, `img.en` et `img.fr` avec `data-page="1…"` ;
  `section#end.end` ; un point de montage pour le lecteur (Tâche 6) juste après `#end`.

- [ ] **Étape 1 : test qui échoue**

```ts
// site/tests/dist/chapter.test.ts
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const chapters = JSON.parse(readFileSync(new URL('../../src/data/chapters.json', import.meta.url), 'utf-8'));
const first = chapters[0], last = chapters.at(-1);
const html = (n: number) => readFileSync(new URL(`../../dist/chapitre/${n}/index.html`, import.meta.url), 'utf-8');

describe('page chapitre', () => {
  it('une page par chapitre', () => { for (const c of chapters) expect(() => html(c.n)).not.toThrow(); });
  const page = html(first.n);
  it('titre, h1, fil d’Ariane', () => {
    expect(page).toContain(`<title>Player — Chapitre ${first.n}</title>`);
    expect(page).toMatch(new RegExp(`<h1[^>]*>Chapitre ${first.n}</h1>`));
    expect(page).toContain('aria-label="Fil d’Ariane"');
  });
  it('deux images par page, dimensions et alt', () => {
    expect((page.match(/<img class="en"/g) ?? []).length).toBe(first.pages.length);
    expect((page.match(/<img class="fr"/g) ?? []).length).toBe(first.pages.length);
    expect(page).toContain(`width="${first.pages[0].w}" height="${first.pages[0].h}"`);
    expect(page).toContain(`alt="Chapitre ${first.n}, page 1 (français)"`);
  });
  it('lazy sauf les deux premières pages', () => {
    expect(page).toMatch(/data-page="1"[^>]*fetchpriority="high"|fetchpriority="high"[^>]*data-page="1"/);
    expect(page).toMatch(/data-page="3"[^>]*loading="lazy"|loading="lazy"[^>]*data-page="3"/);
  });
  it('JSON-LD ComicIssue et BreadcrumbList', () => {
    expect(page).toContain('"@type":"ComicIssue"');
    expect(page).toContain('"@type":"BreadcrumbList"');
  });
  it('liens de fin : premier chapitre sans précédent, dernier sans suivant', () => {
    expect(page).not.toContain('rel="prev"');
    expect(page).toContain(`href="/chapitre/${chapters[1].n}/"`);
    expect(html(last.n)).not.toContain('rel="next"');
  });
});
```

Run : `pnpm run build && pnpm run test:dist` → FAIL.

- [ ] **Étape 2 : implémenter**

```astro
---
// site/src/pages/chapitre/[n].astro
import Base from '../../layouts/Base.astro';
import { getChapters, type Chapter } from '../../lib/chapters';
import { absolute, chapterPath, imageUrl } from '../../lib/urls';
import { IMAGE_BASE, SITE } from '../../config';

export async function getStaticPaths() {
  const chapters = await getChapters();
  return chapters.map((chapter, i) => ({
    params: { n: String(chapter.n) },
    props: { chapter, prev: chapters[i - 1]?.n ?? null, next: chapters[i + 1]?.n ?? null },
  }));
}

interface Props { chapter: Chapter; prev: number | null; next: number | null }
const { chapter, prev, next } = Astro.props;
const { n, pages } = chapter;
const total = pages.length;
const site = Astro.site!;
const LANGS = [
  { id: 'en', label: 'anglais' },
  { id: 'fr', label: 'français' },
] as const;

const jsonLd = [
  {
    '@context': 'https://schema.org',
    '@type': 'ComicIssue',
    name: `${SITE.series.title}, chapitre ${n}`,
    issueNumber: n,
    inLanguage: 'fr',
    url: absolute(chapterPath(n), site),
    image: absolute(`/thumbs/${n}.webp`, site),
    isPartOf: { '@type': 'ComicSeries', name: SITE.series.title, url: absolute('/', site) },
  },
  {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Accueil', item: absolute('/', site) },
      { '@type': 'ListItem', position: 2, name: `Chapitre ${n}`, item: absolute(chapterPath(n), site) },
    ],
  },
];
---
<Base
  title={`Player — Chapitre ${n}`}
  description={`Chapitre ${n} de Player en traduction française (${total} pages), lisible seul ou à côté de la version originale anglaise.`}
  image={`/thumbs/${n}.webp`}
  type="article"
  {jsonLd}
  {prev}
  {next}
>
  <nav class="crumbs" aria-label="Fil d’Ariane"><a href="/">Accueil</a> › <span aria-current="page">Chapitre {n}</span></nav>
  <section class="title-card">
    <div class="tag">// CHAPITRE</div>
    <h1>Chapitre {n}</h1>
    <div class="meta">
      <span><b>{total}</b> pages</span>
      <span class="view-label" data-for="en">Anglais seul</span>
      <span class="view-label" data-for="both">Anglais · Français</span>
      <span class="view-label" data-for="fr">Français seul</span>
      <span class="keys"><kbd>←</kbd> <kbd>→</kbd> chapitres · <kbd>1</kbd> <kbd>2</kbd> <kbd>3</kbd> affichage · <kbd>?</kbd> aide</span>
    </div>
  </section>

  <div class="strip" id="strip" tabindex="-1" data-chapter={n} data-total={total}>
    <div class="col-head en"><i>EN</i> ORIGINAL</div>
    <div class="col-head fr"><i>FR</i> TRADUCTION</div>
    {pages.flatMap((p, i) => LANGS.map(lang => (
      <img
        class={lang.id}
        src={imageUrl(IMAGE_BASE, p[lang.id])}
        width={p.w}
        height={p.h}
        alt={`Chapitre ${n}, page ${i + 1} (${lang.label})`}
        decoding="async"
        loading={i < 2 ? 'eager' : 'lazy'}
        fetchpriority={i < 2 ? 'high' : undefined}
        data-page={i + 1}
      />
    )))}
  </div>

  <section class="end" id="end">
    <div class="tag">// FIN DU CHAPITRE</div>
    <h2>Chapitre {n} terminé</h2>
    <div class="nav">
      {prev !== null && <a class="end-btn" href={chapterPath(prev)}>‹ Chapitre {prev}</a>}
      {next !== null
        ? <a class="end-btn primary" href={chapterPath(next)}>Chapitre {next} ›</a>
        : <a class="end-btn" href="/#chapitres">Dernier chapitre disponible · Accueil</a>}
    </div>
  </section>
</Base>
```

Note : `rel="prev"` / `rel="next"` ne sont émis que par `Seo.astro` (balises `<link>`), d'où les
assertions du test.

- [ ] **Étape 3 : vérifier**

Run : `pnpm run check && pnpm run build && pnpm run test:dist` → PASS.
Run : `pnpm run preview`, ouvrir `http://localhost:4321/chapitre/245/` → la bande s'affiche en EN|FR,
les images se chargent. Arrêter.

- [ ] **Étape 4 : commit**

```bash
git add site
git commit -m "feat(site): pages chapitre statiques avec SEO"
```

---

### Tâche 6 : lecteur `Reader.svelte` et tests de bout en bout

**Files :** Create `site/src/components/Reader.svelte`, `site/playwright.config.ts`,
`site/tests/e2e/reader.spec.ts`. Modify `site/src/pages/chapitre/[n].astro` (monter le lecteur),
`site/src/styles/global.css` (aide des raccourcis).

**Interfaces :**
- Consumes : `createStore`, `parseView`, `progressKey`, `readKey`, `VIEWS`, `type View` (storage) ;
  `anchorFrom`, `scrollTargetFor`, `parseAnchor`, `type Anchor` (position) ; `chapterPath` (urls) ;
  `navigate` de `astro:transitions/client` ; DOM : `#strip`, `img.en|img.fr[data-page]`, `#end`, `#progress`.
- Props : `{ chapter: number; total: number; prev: number | null; next: number | null; prefetch: { en: string; fr: string }[] }`.
- Écrit : `localStorage` `view`, `chapter`, `progress:N`, `read:N` ; `<html data-view>` et `data-chrome`.

- [ ] **Étape 1 : Playwright**

```bash
pnpm exec playwright install chromium
```

```ts
// site/playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: 'tests/e2e',
  use: { baseURL: 'http://localhost:4321' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: { command: 'node scripts/serve.mjs', url: 'http://localhost:4321/', reuseExistingServer: true },
});
```

- [ ] **Étape 2 : tests de bout en bout qui échouent**

```ts
// site/tests/e2e/reader.spec.ts
import { readFileSync } from 'node:fs';
import { expect, test, type Page } from '@playwright/test';

const chapters = JSON.parse(readFileSync(new URL('../../src/data/chapters.json', import.meta.url), 'utf-8'));
const FIRST = chapters[0].n, SECOND = chapters[1].n, LAST = chapters.at(-1).n;

const counter = (page: Page) => page.locator('.page-hud b');
async function scrollToPage(page: Page, p: number, frac = 0.5) {
  await page.evaluate(([p, frac]) => {
    const img = document.querySelector<HTMLImageElement>(`#strip img.fr[data-page="${p}"]`)!;
    const box = img.getBoundingClientRect();
    window.scrollTo(0, box.top + window.scrollY + frac * box.height);
  }, [p, frac]);
  await page.waitForTimeout(400); // sauvegarde différée de 250 ms
}

test.beforeEach(async ({ page }) => { await page.goto('/'); await page.evaluate(() => localStorage.clear()); });

test('mode par défaut EN|FR, changement au clavier', async ({ page }) => {
  await page.goto(`/chapitre/${FIRST}/`);
  await expect(page.locator('html')).toHaveAttribute('data-view', 'both');
  await page.keyboard.press('3');
  await expect(page.locator('html')).toHaveAttribute('data-view', 'fr');
  await expect(page.locator('#strip img.en').first()).toBeHidden();
  await expect(page.getByRole('button', { name: 'FR', exact: true })).toHaveAttribute('aria-pressed', 'true');
});

test('changer de mode garde la page en cours', async ({ page }) => {
  await page.goto(`/chapitre/${FIRST}/`);
  await scrollToPage(page, 3);
  await expect(counter(page)).toContainText('03');
  await page.keyboard.press('1');
  await page.waitForTimeout(200);
  await expect(counter(page)).toContainText('03');
});

test('la position est reprise après rechargement, le mode aussi', async ({ page }) => {
  await page.goto(`/chapitre/${FIRST}/`);
  await page.keyboard.press('3');
  await scrollToPage(page, 4);
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-view', 'fr');
  await expect(counter(page)).toContainText('04');
});

test('flèches : chapitre suivant, rien après le dernier', async ({ page }) => {
  await page.goto(`/chapitre/${FIRST}/`);
  await page.keyboard.press('ArrowRight');
  await expect(page).toHaveURL(new RegExp(`/chapitre/${SECOND}/$`));
  await page.goto(`/chapitre/${LAST}/`);
  await page.keyboard.press('ArrowRight');
  await page.waitForTimeout(300);
  await expect(page).toHaveURL(new RegExp(`/chapitre/${LAST}/$`));
});

test('fin de chapitre : marqué lu', async ({ page }) => {
  await page.goto(`/chapitre/${FIRST}/`);
  await page.locator('#end').scrollIntoViewIfNeeded();
  await page.waitForTimeout(400);
  expect(await page.evaluate(n => localStorage.getItem(`read:${n}`), FIRST)).toBe('1');
});

test('aide des raccourcis', async ({ page }) => {
  await page.goto(`/chapitre/${FIRST}/`);
  await page.keyboard.press('?');
  await expect(page.getByRole('dialog', { name: 'Raccourcis' })).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
});

test('sans JavaScript : lecture EN|FR', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(`/chapitre/${FIRST}/`);
  await expect(page.locator('#strip img.en').first()).toBeVisible();
  await expect(page.locator('#strip img.fr').first()).toBeVisible();
  await context.close();
});

test('mobile 390 px : pas de défilement horizontal', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  for (const path of ['/', `/chapitre/${FIRST}/`]) {
    await page.goto(path);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  }
});
```

Le test « sans JavaScript » demande que la vue par défaut sans `data-view` soit EN|FR : ajouter en
tête de `global.css` la règle `:root:not([data-view]) .strip { grid-template-columns: 1fr 1fr; width: min(1100px, 100%); }`.

Run : `pnpm run build && pnpm run e2e` → FAIL (pas de lecteur).

- [ ] **Étape 3 : le composant**

Consulter d'abord : `pnpm dlx @sveltejs/mcp get-documentation "$state,$derived,$effect,$props,onMount"`.

```svelte
<!-- site/src/components/Reader.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { navigate } from 'astro:transitions/client';
  import { createStore, parseView, progressKey, readKey, VIEWS, type View } from '../lib/storage';
  import { anchorFrom, parseAnchor, scrollTargetFor, type Anchor } from '../lib/position';
  import { chapterPath } from '../lib/urls';

  interface Props {
    chapter: number;
    total: number;
    prev: number | null;
    next: number | null;
    prefetch: { en: string; fr: string }[];
  }
  let { chapter, total, prev, next, prefetch }: Props = $props();

  const LABELS: Record<View, { short: string; title: string }> = {
    en: { short: 'EN', title: 'Anglais seul (1)' },
    both: { short: 'EN | FR', title: 'Les deux (2)' },
    fr: { short: 'FR', title: 'Français seul (3)' },
  };
  const store = createStore();
  const root = document.documentElement;

  let view = $state<View>(parseView(store.get('view')));
  let page = $state(1);
  let progress = $state(0);
  let helpOpen = $state(false);

  const pad = (n: number) => String(n).padStart(2, '0');
  const visibleImgs = () => [...document.querySelectorAll<HTMLImageElement>(`#strip img.${view === 'en' ? 'en' : 'fr'}`)];
  const boxes = () => visibleImgs().map(img => img.getBoundingClientRect());
  const goTo = (a: Anchor | null) => window.scrollTo(0, scrollTargetFor(a, boxes(), window.scrollY));

  function setView(next: View) {
    if (next === view) return;
    const a = anchorFrom(boxes());
    view = next;
    root.dataset.view = next; // tout de suite : la largeur change avant de recalculer la position
    goTo(a);
    store.set('view', next);
  }

  function save() {
    const end = document.getElementById('end');
    if (end && end.getBoundingClientRect().top < innerHeight) {
      store.set(progressKey(chapter), '');
      store.set(readKey(chapter), '1');
      return;
    }
    const a = anchorFrom(boxes());
    if (a) store.set(progressKey(chapter), a.page === 0 && a.frac === 0 ? '' : JSON.stringify(a));
  }

  function go(n: number | null) {
    if (n !== null) navigate(chapterPath(n));
  }

  // Compteur : page de la colonne visible au milieu de l'écran ; à refaire quand le mode change.
  $effect(() => {
    const observer = new IntersectionObserver(entries => {
      for (const e of entries) if (e.isIntersecting) page = Number((e.target as HTMLElement).dataset.page);
    }, { rootMargin: '-50% 0px -50% 0px' });
    document.querySelectorAll(`#strip img.${view === 'en' ? 'en' : 'fr'}`).forEach(img => observer.observe(img));
    return () => observer.disconnect();
  });

  $effect(() => {
    const bar = document.getElementById('progress');
    if (bar) bar.style.width = `${progress}%`;
  });

  onMount(() => {
    store.set('chapter', String(chapter));
    goTo(parseAnchor(store.get(progressKey(chapter))));

    let lastY = window.scrollY;
    let saveTimer: number | undefined;
    const onScroll = () => {
      const y = window.scrollY, max = root.scrollHeight - innerHeight;
      // Barre cachée en descendant, visible en remontant.
      if (y > lastY && y > 240) root.dataset.chrome = 'hidden';
      else delete root.dataset.chrome;
      progress = max > 0 ? Math.min(100, (y / max) * 100) : 0;
      lastY = y;
      clearTimeout(saveTimer);
      saveTimer = window.setTimeout(save, 250);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if ((e.target as HTMLElement).closest('input, select, textarea, [contenteditable]')) return;
      if (e.key === 'ArrowLeft') go(prev);
      else if (e.key === 'ArrowRight') go(next);
      else if (e.key === '1' || e.key === '2' || e.key === '3') setView(VIEWS[Number(e.key) - 1]);
      else if (e.key === '?') helpOpen = !helpOpen;
      else if (e.key === 'Escape') helpOpen = false;
    };
    // Sauvegarde avant que la navigation ne remplace la page (après, la bande est détachée).
    document.addEventListener('astro:before-preparation', save);
    window.addEventListener('pagehide', save);
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('keydown', onKey);
    // Premières pages du chapitre suivant en tâche de fond.
    const prefetchTimer = window.setTimeout(() => {
      const langs = view === 'both' ? (['en', 'fr'] as const) : [view];
      for (const p of prefetch) for (const lang of langs) new Image().src = p[lang];
    }, 2000);

    return () => {
      document.removeEventListener('astro:before-preparation', save);
      window.removeEventListener('pagehide', save);
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('keydown', onKey);
      clearTimeout(saveTimer);
      clearTimeout(prefetchTimer);
      delete root.dataset.chrome;
    };
  });
</script>

<div class="seg" role="group" aria-label="Affichage">
  {#each VIEWS as v (v)}
    <button type="button" aria-pressed={view === v} title={LABELS[v].title} onclick={() => setView(v)}>{LABELS[v].short}</button>
  {/each}
</div>

<aside class="page-hud" aria-live="polite">PAGE<b>{pad(page)}<span> / {pad(total)}</span></b></aside>

{#if helpOpen}
  <div class="help" role="dialog" aria-labelledby="help-title">
    <h2 id="help-title">Raccourcis</h2>
    <dl>
      <dt><kbd>←</kbd> <kbd>→</kbd></dt><dd>Chapitre précédent / suivant</dd>
      <dt><kbd>1</kbd> <kbd>2</kbd> <kbd>3</kbd></dt><dd>Anglais / les deux / français</dd>
      <dt><kbd>?</kbd></dt><dd>Afficher ou masquer cette aide</dd>
      <dt><kbd>Échap</kbd></dt><dd>Fermer</dd>
    </dl>
    <button type="button" class="end-btn" onclick={() => (helpOpen = false)}>Fermer</button>
  </div>
{/if}
```

Le lecteur est monté en `client:only="svelte"` : ses boutons ne servent à rien sans JS, il n'a donc
pas de rendu serveur, et `document` est utilisable dès l'initialisation.

- [ ] **Étape 4 : le monter dans la page et styler l'aide**

Dans `site/src/pages/chapitre/[n].astro`, ajouter à l'import :
`import Reader from '../../components/Reader.svelte';`, calculer dans le frontmatter

```ts
const chapters = await getChapters();
const nextChapter = chapters.find(c => c.n === next);
const prefetch = (nextChapter?.pages.slice(0, 3) ?? []).map(p => ({ en: imageUrl(IMAGE_BASE, p.en), fr: imageUrl(IMAGE_BASE, p.fr) }));
```

et placer juste après `</section>` de `#end` :

```astro
<Reader client:only="svelte" chapter={n} {total} {prev} {next} {prefetch} />
```

Ajouter à `global.css` :

```css
.help {
  position: fixed; inset: auto 50% 50% auto; transform: translate(50%, 50%); z-index: 40;
  width: min(420px, 100% - 32px); padding: 24px 28px; background: var(--ink-2);
  border: 1px solid var(--line-strong); box-shadow: 0 0 40px rgba(0, 0, 0, .6);
}
.help h2 { margin: 0 0 16px; font: 400 32px/1 var(--display); letter-spacing: .04em; }
.help dl { display: grid; grid-template-columns: auto 1fr; gap: 10px 16px; margin: 0 0 20px; }
.help dd { margin: 0; color: var(--muted); }
```

- [ ] **Étape 5 : contrôle Svelte, puis tests**

Run : `pnpm dlx @sveltejs/mcp svelte-autofixer ./src/components/Reader.svelte` → corriger chaque
remarque (ne pas en ignorer sans raison écrite dans le rapport de tâche).
Run : `pnpm run check && pnpm test && pnpm run build && pnpm run test:dist && pnpm run e2e` → tout PASS.

- [ ] **Étape 6 : commit**

```bash
git add site
git commit -m "feat(site): lecteur Svelte (modes, progression, raccourcis) et tests e2e"
```

---

### Tâche 7 : accueil, 404, robots.txt

**Files :** Create `site/src/components/ChapterCard.astro`, `site/src/pages/robots.txt.ts`,
`site/tests/dist/home.test.ts`, `site/tests/e2e/home.spec.ts`.
Modify (remplacer entièrement) : `site/src/pages/index.astro`, `site/src/pages/404.astro` ;
`site/src/styles/global.css` (grille).

**Interfaces :**
- Consumes : `getChapters`, `chapterPath`, `absolute`, `SITE`, `Base`, `createStore`, `chapterStatus`.
- Produces : cartes `a[data-chapter-card="N"]` avec `data-status` = `read` | `progress` | `''` ;
  `a#resume` (caché tant qu'il n'y a pas de chapitre en cours).

- [ ] **Étape 1 : tests qui échouent**

```ts
// site/tests/dist/home.test.ts
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const read = (p: string) => readFileSync(new URL(`../../dist/${p}`, import.meta.url), 'utf-8');
const chapters = JSON.parse(readFileSync(new URL('../../src/data/chapters.json', import.meta.url), 'utf-8'));

describe('accueil, 404, robots', () => {
  const home = read('index.html');
  it('h1 et une carte par chapitre', () => {
    expect(home).toMatch(/<h1[^>]*>Player<\/h1>/);
    expect((home.match(/data-chapter-card=/g) ?? []).length).toBe(chapters.length);
  });
  it('JSON-LD ComicSeries', () => expect(home).toContain('"@type":"ComicSeries"'));
  it('synopsis vide non affiché', () => expect(home).not.toContain('class="synopsis"'));
  it('404 en noindex', () => expect(read('404.html')).toContain('content="noindex"'));
  it('robots.txt pointe vers le sitemap', () =>
    expect(read('robots.txt')).toContain('Sitemap: https://player-fr.example/sitemap-index.xml'));
  it('sitemap généré', () => expect(read('sitemap-index.xml')).toContain('sitemap-0.xml'));
});
```

```ts
// site/tests/e2e/home.spec.ts
import { readFileSync } from 'node:fs';
import { expect, test } from '@playwright/test';

const chapters = JSON.parse(readFileSync(new URL('../../src/data/chapters.json', import.meta.url), 'utf-8'));
const FIRST = chapters[0].n, SECOND = chapters[1].n;

test('badges et bouton Reprendre', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#resume')).toBeHidden();
  await page.evaluate(([a, b]) => {
    localStorage.setItem(`read:${a}`, '1');
    localStorage.setItem(`progress:${b}`, '{"page":2,"frac":0.1}');
    localStorage.setItem('chapter', String(b));
  }, [FIRST, SECOND]);
  await page.reload();
  await expect(page.locator(`[data-chapter-card="${FIRST}"]`)).toHaveAttribute('data-status', 'read');
  await expect(page.locator(`[data-chapter-card="${SECOND}"]`)).toHaveAttribute('data-status', 'progress');
  await expect(page.locator('#resume')).toBeVisible();
  await expect(page.locator('#resume')).toHaveAttribute('href', `/chapitre/${SECOND}/`);
});
```

Run : `pnpm run build && pnpm run test:dist` → FAIL.

- [ ] **Étape 2 : implémenter**

```astro
---
// site/src/components/ChapterCard.astro
import { chapterPath } from '../lib/urls';
interface Props { n: number; pages: number }
const { n, pages } = Astro.props;
---
<li>
  <a class="card" href={chapterPath(n)} data-chapter-card={n} data-status="">
    <img src={`/thumbs/${n}.webp`} width="400" height="560" alt="" loading="lazy" decoding="async" />
    <span class="card-num">Chapitre {n}</span>
    <span class="card-meta">{pages} pages</span>
    <span class="badge badge-read">Lu</span>
    <span class="badge badge-progress">En cours</span>
  </a>
</li>
```

```astro
---
// site/src/pages/index.astro
import Base from '../layouts/Base.astro';
import ChapterCard from '../components/ChapterCard.astro';
import { getChapters } from '../lib/chapters';
import { absolute, chapterPath } from '../lib/urls';
import { SITE } from '../config';

const chapters = await getChapters();
const site = Astro.site!;
const { series } = SITE;
const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'ComicSeries',
  name: series.title,
  inLanguage: 'fr',
  url: absolute('/', site),
  ...(series.authors.length ? { author: series.authors.map(name => ({ '@type': 'Person', name })) } : {}),
  ...(series.synopsis ? { description: series.synopsis } : {}),
  hasPart: chapters.map(c => ({ '@type': 'ComicIssue', issueNumber: c.n, url: absolute(chapterPath(c.n), site) })),
};
const first = chapters[0].n, last = chapters.at(-1)!.n;
---
<Base title={SITE.name} description={SITE.description} {jsonLd}>
  <section class="title-card hero">
    <div class="tag">// WEBTOON · TRADUCTION FRANÇAISE</div>
    <h1>Player</h1>
    {series.synopsis && <p class="synopsis">{series.synopsis}</p>}
    <div class="meta">
      <span><b>{chapters.length}</b> chapitres</span>
      <span>Chapitres <b>{first}</b> à <b>{last}</b></span>
      {series.authors.length > 0 && <span>{series.authors.join(', ')}</span>}
    </div>
    <div class="hero-actions">
      <a class="end-btn primary" id="resume" href={chapterPath(first)} hidden>Reprendre au chapitre <b></b></a>
      <a class="end-btn" href={chapterPath(first)}>Commencer au chapitre {first}</a>
    </div>
  </section>

  <section class="chapters" id="chapitres" aria-labelledby="chapitres-titre">
    <h2 id="chapitres-titre">Chapitres</h2>
    <ul class="grid">
      {chapters.map(c => <ChapterCard n={c.n} pages={c.pages.length} />)}
    </ul>
  </section>
</Base>

<script>
  import { chapterStatus, createStore } from '../lib/storage';
  import { chapterPath } from '../lib/urls';

  // Badges « lu » / « en cours » et bouton Reprendre, d’après la progression enregistrée.
  function decorate() {
    const store = createStore();
    document.querySelectorAll<HTMLElement>('[data-chapter-card]').forEach(card => {
      card.dataset.status = chapterStatus(store, Number(card.dataset.chapterCard)) ?? '';
    });
    const resume = document.querySelector<HTMLAnchorElement>('#resume');
    const last = store.get('chapter');
    if (!resume || !last || !document.querySelector(`[data-chapter-card="${last}"]`)) return;
    resume.href = chapterPath(Number(last));
    resume.querySelector('b')!.textContent = last;
    resume.hidden = false;
  }
  document.addEventListener('astro:page-load', decorate);
</script>
```

```astro
---
// site/src/pages/404.astro
import Base from '../layouts/Base.astro';
---
<Base title="Page introuvable — Player" description="Cette page n’existe pas." noindex>
  <section class="end">
    <div class="tag">// ERREUR 404</div>
    <h2>Page introuvable</h2>
    <div class="nav"><a class="end-btn primary" href="/">Retour à l’accueil</a></div>
  </section>
</Base>
```

```ts
// site/src/pages/robots.txt.ts
import type { APIRoute } from 'astro';

export const GET: APIRoute = ({ site }) =>
  new Response(`User-agent: *\nAllow: /\n\nSitemap: ${new URL('sitemap-index.xml', site).href}\n`);
```

Ajouter à `global.css` :

```css
/* ---------- Accueil ---------- */
.hero { width: min(1100px, 100% - 32px); }
.synopsis { max-width: 60ch; color: var(--text); font-size: 15px; line-height: 1.6; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 24px; }
.chapters { position: relative; z-index: 1; width: min(1100px, 100% - 32px); margin: 0 auto 64px; }
.chapters h2 { font: 400 40px/1 var(--display); letter-spacing: .04em; margin: 0 0 20px; }
.grid { list-style: none; margin: 0; padding: 0; display: grid; gap: 16px; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }
.card {
  position: relative; display: grid; gap: 4px; text-decoration: none; padding-bottom: 10px;
  border: 1px solid var(--line); background: var(--panel); transition: border-color .2s, transform .2s;
}
.card:hover { border-color: var(--cyan); transform: translateY(-2px); }
.card img { width: 100%; height: auto; display: block; background: #111; }
.card-num { padding: 6px 10px 0; font: 400 24px/1 var(--display); letter-spacing: .04em; }
.card-meta { padding: 0 10px; font-size: 11px; letter-spacing: .12em; color: var(--muted); text-transform: uppercase; }
.badge {
  display: none; position: absolute; top: 8px; left: 8px; padding: 3px 8px;
  font: 700 10px var(--hud); letter-spacing: .2em; text-transform: uppercase;
}
.card[data-status="read"] .badge-read { display: block; background: var(--cyan); color: var(--ink); }
.card[data-status="progress"] .badge-progress { display: block; background: var(--karma); color: #fff; }
@media (prefers-reduced-motion: reduce) { .card:hover { transform: none; } }
```

- [ ] **Étape 3 : vérifier**

Run : `pnpm run check && pnpm run build && pnpm run test:dist && pnpm run e2e` → tout PASS.

- [ ] **Étape 4 : commit**

```bash
git add site
git commit -m "feat(site): accueil avec progression, 404 et robots.txt"
```

---

### Tâche 8 : audits et documentation

**Files :** Modify `CLAUDE.md`, `README.md`, et les fichiers du site selon les audits.

- [ ] **Étape 1 : Lighthouse**

Avec `pnpm run preview` lancé :

```bash
pnpm dlx lighthouse http://localhost:4321/ --only-categories=seo,accessibility,best-practices --chrome-flags="--headless" --output=json --output-path=../inventaire/lighthouse-home.json --quiet
pnpm dlx lighthouse http://localhost:4321/chapitre/245/ --only-categories=seo,accessibility,best-practices --chrome-flags="--headless" --output=json --output-path=../inventaire/lighthouse-chapitre.json --quiet
node -e "for (const f of ['home','chapitre']) { const r = require('../inventaire/lighthouse-' + f + '.json'); console.log(f, Object.values(r.categories).map(c => c.id + ' ' + Math.round(c.score * 100)).join(', ')); }"
```

Expected : SEO 100, accessibilité ≥ 95. Corriger chaque audit en échec (contraste, libellés…), puis
relancer `pnpm run e2e`.

- [ ] **Étape 2 : relecture par les skills**

Invoquer `web-design-guidelines` sur `site/src/` et `marketing:seo-audit` sur `dist/index.html` et une
page chapitre. Corriger les points justifiés ; noter dans le rapport ceux qu'on écarte et pourquoi.

- [ ] **Étape 3 : documentation**

Dans `CLAUDE.md`, remplacer la ligne `python scripts/make_viewer.py  # régénère viewer.html après chaque rendu` par :

```
python scripts/make_viewer.py                      # données du site + vignettes (+ viewer.html) après chaque rendu
cd site && pnpm run build && pnpm run preview        # site Astro sur http://localhost:4321/
```

et l'étape 7 du déroulé par « `make_viewer.py` puis `pnpm run build` dans `site/`, puis chapitre suivant
sans demander. »

Dans `README.md`, section « Lire » :

```
Site : `python scripts/make_viewer.py`, puis dans `site/` : `pnpm install` (une fois), `pnpm run build`,
`pnpm run preview` et ouvrir http://localhost:4321/. Développement : `pnpm run dev`.
Ancien lecteur (en attendant la validation du site) : `viewer.html` en double-clic.
```

et ajouter `site/` à la liste de la section « Structure » :
`site/  site Astro + Svelte (pages, lecteur, SEO), données écrites par make_viewer.py`.

- [ ] **Étape 4 : vérification finale**

Run (racine) : `python -m pytest tests -v`.
Run (`site/`) : `pnpm run check && pnpm test && pnpm run build && pnpm run test:dist && pnpm run e2e`.
Tout PASS ; `ls site/dist` ne montre ni `chapters_en` ni `chapters_fr`.

- [ ] **Étape 5 : commit**

```bash
git add -A
git commit -m "docs: site Astro dans le flux de travail ; corrections des audits"
```

La suppression de `viewer.html` et `scripts/viewer_template.html` attend la validation de
l'utilisateur : hors de ce plan.
