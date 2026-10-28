export const SITE = {
  name: 'Player — Traduction française',
  shortName: 'Player FR',
  lang: 'fr',
  locale: 'fr_FR',
  // « VF », « manhwa » et l’auteur : les mots que les lecteurs tapent (« Player » seul désigne d’autres séries).
  description: 'Le manhwa Player d’Oh Hyeon-jun en VF : traduction française chapitre par chapitre, seule ou côte à côte avec la version anglaise.',
  // Balise <title> de l’accueil : nom, titre original et ce que propose le site (≈ 60 caractères).
  homeTitle: 'Player VF (플레이어) — manhwa d’Oh Hyeon-jun en français',
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

// Hôte des planches : vide = le site lui-même (dépôt en local, chapters_web/ sur GitHub Pages), sinon URL d’un CDN.
export const IMAGE_BASE: string = import.meta.env.PUBLIC_IMAGE_BASE ?? '';
