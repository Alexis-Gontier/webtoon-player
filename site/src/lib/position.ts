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
