import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const chapters = JSON.parse(readFileSync(new URL('../../src/data/chapters.json', import.meta.url), 'utf-8'));
const first = chapters[0], last = chapters.at(-1);
const html = (n: number) => readFileSync(new URL(`../../dist/chapitre/${n}/index.html`, import.meta.url), 'utf-8');

describe('page chapitre', () => {
  it('une page par chapitre', () => { for (const c of chapters) expect(() => html(c.n)).not.toThrow(); });
  const page = html(first.n);
  it('titre, h1, fil d’Ariane', () => {
    expect(page).toContain(`<title>Player chapitre ${first.n} VF — manhwa en français, lecture EN / FR</title>`);
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
    expect(page).toMatch(/fetchpriority="high"[^>]*data-page="1"/);
    expect(page).toMatch(/loading="lazy"[^>]*data-page="3"/);
    expect(page).not.toMatch(/loading="lazy"[^>]*data-page="1"/);
  });
  it('JSON-LD ComicIssue et BreadcrumbList', () => {
    expect(page).toContain('"@type":"ComicIssue"');
    expect(page).toContain('"@type":"BreadcrumbList"');
  });
  it('liens de fin : premier chapitre sans précédent, dernier sans suivant', () => {
    expect(page).not.toContain('rel="prev"');
    expect(page).toContain(`rel="next" href="https://player-fr.example/chapitre/${chapters[1].n}/"`);
    expect(page).toContain(`href="/chapitre/${chapters[1].n}/"`);
    expect(html(last.n)).not.toContain('rel="next"');
  });
});
