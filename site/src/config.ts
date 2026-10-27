export const SITE = {
  name: 'Player — Traduction française',
  shortName: 'Player FR',
  lang: 'fr',
  locale: 'fr_FR',
  description: 'Le webtoon Player en version originale et en traduction française, chapitre par chapitre, avec lecture côte à côte.',
  // Balise <title> de l’accueil : nom, titre original et ce que propose le site (≈ 60 caractères).
  homeTitle: 'Player (플레이어) en français — webtoon EN / FR côte à côte',
  series: {
    title: 'Player',
    // Œuvre d’origine : Naver Webtoon (voir docs/audit-2026-10-09.md).
    originalTitle: '플레이어',
    originalLanguage: 'ko',
    publisher: 'Naver Webtoon',
    authors: [
      { name: 'Park Jong-seok', role: 'Scénario' },
      { name: 'Oh Hyeon-jun', role: 'Dessin' },
    ],
    synopsis: '',
    // Cover officielle (fichier dans public/, ex. '/cover.webp'). Vide : vignette du chapitre en cours.
    cover: '/cover.webp',
  },
};

// Racine des planches : '/' en local (servies depuis le dépôt), URL d’un CDN en ligne.
export const IMAGE_BASE: string = import.meta.env.PUBLIC_IMAGE_BASE ?? '/';
