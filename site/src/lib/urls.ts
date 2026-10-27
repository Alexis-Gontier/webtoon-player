// Préfixe du site : '/' en local, '/webtoon-player' sur GitHub Pages (option base d’Astro).
const BASE = import.meta.env.BASE_URL.replace(/\/+$/, '');

// Chemin interne au site (commençant par /), préfixé par la base.
export const withBase = (path: string) => BASE + path;

export const chapterPath = (n: number) => withBase(`/chapitre/${n}/`);

export const imageUrl = (base: string, path: string) => `${base.replace(/\/+$/, '')}/${path.replace(/^\/+/, '')}`;

export const absolute = (path: string, site: URL | string) => new URL(path, site).href;
