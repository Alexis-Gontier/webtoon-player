export const chapterPath = (n: number) => `/chapitre/${n}/`;

export const imageUrl = (base: string, path: string) => `${base.replace(/\/+$/, '')}/${path.replace(/^\/+/, '')}`;

export const absolute = (path: string, site: URL | string) => new URL(path, site).href;
