// Adresse d’une planche dans la page (rendu côté serveur uniquement : lit le disque).
import { readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { IMAGE_BASE } from '../config';
import { imageUrl, withBase } from './urls';

// Racine du dépôt : parent de site/, d’où tournent le build et les tests (import.meta.url change une fois empaqueté).
const REPO = resolve(process.cwd(), '..') + '/';
const listings = new Map<string, string[]>();

// chapters_en/chapter-225/001.png -> chapters_web/en/chapter-225/001.webp : les copies versionnées
// n’ont pas toujours l’extension de l’original (WebP, ou JPEG pour les pages trop hautes).
function webCopy(path: string) {
  const [root, chapter, file] = path.split('/');
  const dir = `chapters_web/${root.replace('chapters_', '')}/${chapter}`;
  if (!listings.has(dir)) listings.set(dir, readdirSync(REPO + dir));
  const stem = file.replace(/\.[^.]+$/, '');
  const found = listings.get(dir)!.find(f => f.replace(/\.[^.]+$/, '') === stem);
  if (!found) throw new Error(`Copie web introuvable pour ${path}`);
  return `${dir}/${found}`;
}

// PAGES_SOURCE=web (GitHub Pages) : copies de chapters_web/, copiées dans dist/ au build.
// Sinon : originaux du dépôt, servis par le serveur de dev et la preview.
export function pageSrc(path: string) {
  const file = process.env.PAGES_SOURCE === 'web' ? webCopy(path) : path;
  return IMAGE_BASE ? imageUrl(IMAGE_BASE, file) : withBase(`/${file}`);
}
