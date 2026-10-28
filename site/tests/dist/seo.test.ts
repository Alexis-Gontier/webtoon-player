import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const html = (path: string) => readFileSync(new URL(`../../dist/${path}`, import.meta.url), 'utf-8');

describe('head commun (accueil)', () => {
  const page = html('index.html');
  it('langue, titre, description', () => {
    expect(page).toMatch(/<html lang="fr"/);
    expect(page).toContain('<title>Player VF (플레이어) — manhwa d’Oh Hyeon-jun en français</title>');
    expect(page).toMatch(/<meta name="description" content="[^"]+"/);
  });
  it('canonique absolue avec barre oblique finale', () =>
    expect(page).toContain('<link rel="canonical" href="https://player-fr.example/"'));
  it('Open Graph et Twitter', () => {
    for (const p of ['og:title', 'og:description', 'og:url', 'og:image', 'og:type', 'og:locale'])
      expect(page).toContain(`property="${p}"`);
    expect(page).toContain('name="twitter:card" content="summary_large_image"');
    expect(page).toContain('property="og:image" content="https://player-fr.example/cover.webp"');
    expect(page).toContain('property="og:image:width" content="690"');
    expect(page).toContain('name="twitter:image:alt" content="Cover du webtoon Player"');
    expect(page).toContain('content="index, follow, max-image-preview:large"');
  });
  it('favicon, manifeste, sitemap', () => {
    expect(page).toContain('href="/favicon.svg"');
    expect(page).toContain('href="/manifest.webmanifest"');
    expect(page).toContain('href="/sitemap-index.xml"');
  });
  it('pas de Google Fonts', () => expect(page).not.toContain('fonts.googleapis.com'));
  it('lien d’évitement', () => expect(page).toContain('class="skip"'));
});

describe('données structurées et fichiers pour les robots', () => {
  const page = html('index.html');
  it('WebSite et ComicSeries avec auteurs et œuvre d’origine', () => {
    expect(page).toContain('"@type":"WebSite"');
    expect(page).toContain('"alternateName":"플레이어"');
    expect(page).toContain('"name":"Park Jong-seok"');
    expect(page).toContain('"translationOfWork"');
  });
  it('robots.txt nomme les robots des assistants IA', () => {
    const robots = html('robots.txt');
    for (const bot of ['GPTBot', 'ClaudeBot', 'PerplexityBot', 'Google-Extended']) expect(robots).toContain(`User-agent: ${bot}`);
    expect(robots).not.toMatch(/Disallow: \/$/m);
  });
  it('llms.txt décrit le site et liste les chapitres', () => {
    const llms = html('llms.txt');
    expect(llms).toMatch(/^# Player/);
    expect(llms).toContain('Park Jong-seok');
    expect(llms).toContain('https://player-fr.example/chapitre/225/');
  });
});
