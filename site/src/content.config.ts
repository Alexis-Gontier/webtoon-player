import { defineCollection } from 'astro:content';
import { file } from 'astro/loaders';
import { z } from 'astro/zod';

const page = z.object({
  name: z.string(),
  en: z.string(),
  fr: z.string(),
  w: z.number().int().positive(),
  h: z.number().int().positive(),
});

const chapters = defineCollection({
  loader: file('src/data/chapters.json'),
  schema: z.object({ n: z.number().int().positive(), pages: z.array(page).min(1) }),
});

export const collections = { chapters };
