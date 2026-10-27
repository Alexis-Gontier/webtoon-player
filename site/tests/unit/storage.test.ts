import { describe, expect, it } from 'vitest';
import { chapterStatus, createStore, markRead, markUnread, parseView, progressKey, readKey, type KV } from '../../src/lib/storage';

function memory(): KV & { data: Map<string, string> } {
  const data = new Map<string, string>();
  return { data, getItem: k => data.get(k) ?? null, setItem: (k, v) => void data.set(k, v), removeItem: k => void data.delete(k) };
}

describe('storage', () => {
  it('clés compatibles avec l’ancien lecteur', () => {
    expect(progressKey(245)).toBe('progress:245');
    expect(readKey(245)).toBe('read:245');
  });
  it('parseView refuse les valeurs inconnues', () => {
    expect(parseView('fr')).toBe('fr');
    expect(parseView('xx')).toBe('both');
    expect(parseView(null)).toBe('both');
  });
  it('set("") supprime la clé', () => {
    const kv = memory();
    const store = createStore(kv);
    store.set('a', '1');
    store.set('a', '');
    expect(kv.data.has('a')).toBe(false);
  });
  it('sans stockage disponible, ne lève pas', () => {
    const store = createStore(null);
    store.set('a', '1');
    expect(store.get('a')).toBeNull();
  });
  it('un stockage qui lève est ignoré', () => {
    const broken: KV = { getItem: () => { throw new Error(); }, setItem: () => { throw new Error(); }, removeItem: () => { throw new Error(); } };
    const store = createStore(broken);
    expect(() => store.set('a', '1')).not.toThrow();
    expect(store.get('a')).toBeNull();
  });
  it('chapterStatus', () => {
    const store = createStore(memory());
    expect(chapterStatus(store, 245)).toBeNull();
    store.set('progress:245', '{"page":3,"frac":0.5}');
    expect(chapterStatus(store, 245)).toBe('progress');
    store.set('read:245', '1');
    expect(chapterStatus(store, 245)).toBe('read');
  });
  it('markUnread efface lu, position et reprise de ce chapitre seulement', () => {
    const store = createStore(memory());
    store.set('read:245', '1');
    store.set('progress:245', '{"page":3,"frac":0}');
    store.set('chapter', '245');
    markUnread(store, 245);
    expect(chapterStatus(store, 245)).toBeNull();
    expect(store.get('chapter')).toBeNull();
    store.set('read:246', '1');
    store.set('chapter', '246');
    markUnread(store, 245);
    expect(store.get('chapter')).toBe('246');
  });
  it('markRead marque lu et oublie la position', () => {
    const store = createStore(memory());
    store.set('progress:245', '{"page":3,"frac":0}');
    markRead(store, 245);
    expect(chapterStatus(store, 245)).toBe('read');
    expect(store.get('progress:245')).toBeNull();
  });
});
