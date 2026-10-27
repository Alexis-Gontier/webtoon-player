import { afterEach, describe, expect, it } from 'vitest';
import { pageSrc } from '../../src/lib/pages';

describe('pageSrc', () => {
  afterEach(() => { delete process.env.PAGES_SOURCE; });
  it('en local : l’original du dépôt', () =>
    expect(pageSrc('chapters_fr/chapter-225/001.webp')).toBe('/chapters_fr/chapter-225/001.webp'));
  it('GitHub Pages : la copie de chapters_web/, avec sa vraie extension', () => {
    process.env.PAGES_SOURCE = 'web';
    expect(pageSrc('chapters_en/chapter-225/001.webp')).toBe('/chapters_web/en/chapter-225/001.webp');
    expect(pageSrc('chapters_fr/chapter-259/001.jpg')).toBe('/chapters_web/fr/chapter-259/001.webp');
  });
});
