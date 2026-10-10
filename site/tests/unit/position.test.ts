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
