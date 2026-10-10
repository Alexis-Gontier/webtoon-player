import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
import sitemap from '@astrojs/sitemap';
import { chapterImages } from './integrations/chapter-images.mjs';

export default defineConfig({
  site: 'https://player-fr.example',
  trailingSlash: 'always',
  prefetch: true,
  integrations: [svelte(), sitemap(), chapterImages()],
});
