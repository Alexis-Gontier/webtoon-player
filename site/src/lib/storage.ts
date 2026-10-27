export type View = 'en' | 'both' | 'fr';
export const VIEWS: readonly View[] = ['en', 'both', 'fr'];

export const parseView = (raw: string | null): View =>
  (VIEWS as readonly string[]).includes(raw ?? '') ? (raw as View) : 'both';
export const progressKey = (n: number) => `progress:${n}`;
export const readKey = (n: number) => `read:${n}`;

export interface KV {
  getItem(k: string): string | null;
  setItem(k: string, v: string): void;
  removeItem(k: string): void;
}
export type Store = { get(k: string): string | null; set(k: string, v: string): void };

function browserStorage(): KV | null {
  // Navigation privée, stockage bloqué ou rendu serveur : pas de stockage, sans erreur.
  try { return window.localStorage; } catch { return null; }
}

export function createStore(kv: KV | null = browserStorage()): Store {
  return {
    get(k) { try { return kv?.getItem(k) ?? null; } catch { return null; } },
    set(k, v) { try { if (v === '') kv?.removeItem(k); else kv?.setItem(k, v); } catch { /* stockage indisponible */ } },
  };
}

export function chapterStatus(store: Store, n: number): 'read' | 'progress' | null {
  if (store.get(readKey(n)) === '1') return 'read';
  return store.get(progressKey(n)) ? 'progress' : null;
}

// Annule une lecture marquée par erreur : plus lu, plus de position, et plus proposé par « Reprendre ».
export function markUnread(store: Store, n: number) {
  store.set(readKey(n), '');
  store.set(progressKey(n), '');
  if (store.get('chapter') === String(n)) store.set('chapter', '');
}

// Marque un chapitre comme lu à la main (la position enregistrée n’a plus d’intérêt).
export function markRead(store: Store, n: number) {
  store.set(readKey(n), '1');
  store.set(progressKey(n), '');
}
