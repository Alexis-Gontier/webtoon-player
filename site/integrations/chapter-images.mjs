// En local, les planches restent dans chapters_en/ et chapters_fr/ à la racine du dépôt : servies telles
// quelles, jamais copiées dans dist/ (1,4 Go). Pour GitHub Pages (PAGES_SOURCE=web), les copies WebP de
// chapters_web/ (~620 Mo, versionnées) sont copiées dans dist/ à la fin du build.
import sirv from 'sirv';
import { cpSync } from 'node:fs';
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
      'astro:build:done': ({ dir, logger }) => {
        if (process.env.PAGES_SOURCE !== 'web') return;
        cpSync(REPO + 'chapters_web', fileURLToPath(new URL('chapters_web', dir)), { recursive: true });
        logger.info('chapters_web/ copié dans le build');
      },
    },
  };
}
