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
