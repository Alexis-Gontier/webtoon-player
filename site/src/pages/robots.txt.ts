import type { APIRoute } from 'astro';

// Moteurs de recherche et assistants IA : tous autorisés, nommés pour qu’une règle ajoutée plus tard
// au groupe « * » ne les bloque pas par accident.
const AI_CRAWLERS = [
  'GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'Claude-User',
  'PerplexityBot', 'Perplexity-User', 'Google-Extended', 'Applebot-Extended', 'Bingbot', 'CCBot',
];

export const GET: APIRoute = ({ site }) => new Response(
  [
    'User-agent: *',
    'Allow: /',
    '',
    ...AI_CRAWLERS.map(bot => `User-agent: ${bot}`),
    'Allow: /',
    '',
    `Sitemap: ${new URL('sitemap-index.xml', site).href}`,
    '',
  ].join('\n'),
  { headers: { 'Content-Type': 'text/plain; charset=utf-8' } },
);
