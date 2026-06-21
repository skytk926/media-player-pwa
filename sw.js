const CACHE = 'player-v8';
// Only cache static assets that rarely change — never cache index.html
const ASSETS = [
  '/manifest.json', '/icon.png',
  'https://cdn.jsdelivr.net/npm/mp4box@0.5.3/dist/mp4box.all.min.js'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // HTML navigate requests: ALWAYS network, never cache
  if (e.request.mode === 'navigate') {
    e.respondWith(
      fetch(e.request).then((r) => {
        const h = new Headers(r.headers);
        h.set('Cross-Origin-Embedder-Policy', 'require-corp');
        h.set('Cross-Origin-Opener-Policy', 'same-origin');
        h.set('Cache-Control', 'no-cache, no-store, must-revalidate');
        return new Response(r.body, { status: r.status, statusText: r.statusText, headers: h });
      })
    );
    return;
  }
  // Static assets: cache first, network fallback
  e.respondWith(
    caches.match(e.request).then((r) => r || fetch(e.request))
  );
});