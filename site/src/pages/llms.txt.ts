import type { APIRoute } from 'astro';
import { SITE } from '../config';
import { getChapters } from '../lib/chapters';
import { absolute, chapterPath, withBase } from '../lib/urls';

// Résumé du site en texte brut pour les assistants IA (format llms.txt : titre, résumé, liens).
export const GET: APIRoute = async context => {
  const site = context.site!;
  const chapters = await getChapters();
  const { series } = SITE;
  const first = chapters[0].n, last = chapters.at(-1)!.n;
  const pages = chapters.reduce((sum, c) => sum + c.pages.length, 0);
  const credits = series.authors.map(a => `${a.role.toLowerCase()} : ${a.name}`).join(', ');
  const body = [
    `# ${SITE.name}`,
    '',
    `> ${SITE.description}`,
    '',
    `- Œuvre : ${series.title} (titre original ${series.originalTitle}), webtoon coréen publié par ${series.publisher} ; ${credits}.`,
    `- Contenu : chapitres ${first} à ${last} (${chapters.length} chapitres, ${pages} pages), en français, lisibles seuls ou à côté de la version anglaise.`,
    '- Traduction française non officielle, faite pour une lecture personnelle. « Player » appartient à ses auteurs.',
    '',
    '## Pages',
    '',
    `- [Accueil et liste des chapitres](${absolute(withBase('/'), site)})`,
    `- [Plan du site](${absolute(withBase('/sitemap-index.xml'), site)})`,
    '',
    '## Chapitres',
    '',
    ...chapters.map(c => `- [Chapitre ${c.n}](${absolute(chapterPath(c.n), site)}) : ${c.pages.length} pages`),
    '',
  ].join('\n');
  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
