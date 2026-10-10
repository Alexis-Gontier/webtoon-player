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
  it('sitemap généré, sans la 404', () => {
    expect(read('sitemap-index.xml')).toContain('sitemap-0.xml');
    const urls = read('sitemap-0.xml');
    expect(urls).toContain(`https://player-fr.example/chapitre/${chapters[0].n}/`);
    expect(urls).not.toContain('404');
  });
});
