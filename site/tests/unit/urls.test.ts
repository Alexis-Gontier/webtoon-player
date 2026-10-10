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
