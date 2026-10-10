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
