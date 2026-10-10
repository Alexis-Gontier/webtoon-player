import { getCollection } from 'astro:content';

export type Page = { name: string; en: string; fr: string; w: number; h: number };
export type Chapter = { n: number; pages: Page[] };

export async function getChapters(): Promise<Chapter[]> {
  return (await getCollection('chapters')).map(entry => entry.data).sort((a, b) => a.n - b.n);
}
