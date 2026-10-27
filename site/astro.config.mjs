import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
import sitemap from '@astrojs/sitemap';
import { chapterImages } from './integrations/chapter-images.mjs';

export default defineConfig({
  // Adresse publique : SITE_URL=https://mon-domaine.fr pnpm build. Toutes les URL absolues en dépendent.
  site: process.env.SITE_URL ?? 'https://player-fr.example',
  trailingSlash: 'always',
  prefetch: true,
  integrations: [svelte(), sitemap(), chapterImages()],
});
