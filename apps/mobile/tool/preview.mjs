// Local Flutter preview. Read-only API proxy avoids broadening FastAPI CORS.
import http from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(fileURLToPath(new URL('../build/web/', import.meta.url)));
const mime = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.json': 'application/json',
  '.wasm': 'application/wasm', '.css': 'text/css', '.png': 'image/png', '.svg': 'image/svg+xml', '.ttf': 'font/ttf' };
const server = http.createServer(async (request, response) => {
  if (!['GET', 'HEAD'].includes(request.method)) { response.writeHead(405).end(); return; }
  const url = new URL(request.url, 'http://127.0.0.1:3100');
  if (url.pathname.startsWith('/api/v1/')) {
    const upstream = http.request({ hostname: '127.0.0.1', port: 8000, path: url.pathname + url.search,
      method: 'GET', headers: { Accept: 'application/json' }, timeout: 16000 }, (result) => {
      response.writeHead(result.statusCode ?? 502, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      result.pipe(response);
    });
    upstream.on('timeout', () => upstream.destroy());
    upstream.on('error', () => { if (!response.headersSent) response.writeHead(502, { 'Content-Type': 'application/json' }); response.end('{"error":{"message":"API locale indisponible"}}'); });
    upstream.end(); return;
  }
  try {
    const filename = path.resolve(root, `.${decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname)}`);
    if (!filename.startsWith(root + path.sep) || !(await stat(filename)).isFile()) { response.writeHead(404).end(); return; }
    const bytes = await readFile(filename);
    response.writeHead(200, { 'Content-Type': mime[path.extname(filename)] ?? 'application/octet-stream', 'Cache-Control': 'no-store' });
    response.end(request.method === 'HEAD' ? undefined : bytes);
  } catch { response.writeHead(404).end(); }
});
server.listen(3100, '127.0.0.1', () => console.log('AquaMaroc Flutter : http://127.0.0.1:3100/ (API locale sur 8000)'));
server.on('error', (error) => { console.error(error.message); process.exitCode = 1; });
