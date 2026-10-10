export const SITE = {
  name: 'Player — Traduction française',
  shortName: 'Player FR',
  lang: 'fr',
  locale: 'fr_FR',
  description: 'Le webtoon Player en version originale et en traduction française, chapitre par chapitre, avec lecture côte à côte.',
  series: {
    title: 'Player',
    authors: [] as string[], // à remplir : ne s’affiche pas tant que c’est vide
    synopsis: '',
  },
};

// Racine des planches : '/' en local (servies depuis le dépôt), URL d’un CDN en ligne.
export const IMAGE_BASE: string = import.meta.env.PUBLIC_IMAGE_BASE ?? '/';
