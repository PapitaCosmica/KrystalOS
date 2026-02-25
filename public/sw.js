const CACHE_NAME = 'krystal-os-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/public/css/glass.css',
  '/public/css/bento.css',
  '/public/js/krystal-core.js',
  '/public/manifest.json',
  // Alpine and Gridstack CDN fallback can be added here for full offline if downloaded locally
];

// Instalar el Service Worker y guardar en caché el "App Shell"
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[KrystalOS Service Worker] Caching App Shell');
        return cache.addAll(ASSETS_TO_CACHE);
      })
  );
  self.skipWaiting();
});

// Interceptar peticiones para devolver la caché si el usuario está Offline
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Retorna la caché si la encuentra, de lo contrario haz fetch a la red
        if (response) {
          return response;
        }
        
        // Estrategia Network-first para la API
        if (event.request.url.includes('/api/')) {
            return fetch(event.request).catch(() => {
                return new Response(JSON.stringify({ error: "Estás offline." }), {
                    status: 503,
                    headers: { 'Content-Type': 'application/json' }
                });
            });
        }

        return fetch(event.request);
      })
  );
});

// Limpiar cachés antiguas al activar una nueva versión
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
