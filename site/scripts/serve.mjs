// Preview du build : dist/ + planches du dépôt, 404.html pour le reste.
import http from 'node:http';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import sirv from 'sirv';
import { imageHandlers } from '../integrations/chapter-images.mjs';

const dist = new URL('../dist/', import.meta.url);
const notFound = readFileSync(new URL('404.html', dist));
const site = sirv(fileURLToPath(dist), { etag: true });
const images = imageHandlers();
const port = Number(process.env.PORT) || 4321;

http.createServer((req, res) => {
  const fallback = () => {
    res.writeHead(404, { 'content-type': 'text/html; charset=utf-8' });
    res.end(notFound);
  };
  const match = images.find(([prefix]) => req.url.startsWith(prefix + '/'));
  if (match) {
    req.url = req.url.slice(match[0].length);
    return match[1](req, res, fallback);
  }
  site(req, res, fallback);
}).listen(port, () => console.log(`http://localhost:${port}/`));
