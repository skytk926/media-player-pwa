const CACHE = 'player-v4';
const ASSETS = [
  '/', '/index.html', '/manifest.json', '/icon-192.png', '/icon-512.png',
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
  // Inject COOP/COEP headers for navigate requests to enable SharedArrayBuffer
  if (e.request.mode === 'navigate') {
    e.respondWith(
      fetch(e.request).then((r) => {
        const h = new Headers(r.headers);
        h.set('Cross-Origin-Embedder-Policy', 'require-corp');
        h.set('Cross-Origin-Opener-Policy', 'same-origin');
        return new Response(r.body, { status: r.status, statusText: r.statusText, headers: h });
      }).catch(() => caches.match(e.request))
    );
    return;
  }
  e.respondWith(
    caches.match(e.request).then((r) => r || fetch(e.request))
  );
});