// Les planches restent dans chapters_en/ et chapters_fr/ à la racine du dépôt : servies telles quelles,
// jamais copiées dans dist/ (1,4 Go). En ligne, PUBLIC_IMAGE_BASE pointerait vers un CDN.
import sirv from 'sirv';
import { fileURLToPath } from 'node:url';

const REPO = fileURLToPath(new URL('../../', import.meta.url));
const DIRS = ['chapters_en', 'chapters_fr'];

export function imageHandlers() {
  return DIRS.map(dir => [`/${dir}`, sirv(REPO + dir, { dev: true })]);
}

export function chapterImages() {
  return {
    name: 'chapter-images',
    hooks: {
      'astro:server:setup': ({ server }) => {
        for (const [prefix, handler] of imageHandlers()) server.middlewares.use(prefix, handler);
      },
    },
  };
}
