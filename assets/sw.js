// A unique name for our cache
const CACHE_NAME = 'riskwatch-cache-v1';

// The files we want to cache on installation
const URLS_TO_CACHE = [
  '/',
  '/offline.html',
  '/assets/style.css',
  '/assets/riskwatch-logo.png',
  '/assets/profile icon.png'
];

// Install event: cache the core application shell
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(URLS_TO_CACHE);
      })
  );
});

// Fetch event: serve cached content when offline
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response
        if (response) {
          return response;
        }

        // Not in cache - try to fetch from network
        return fetch(event.request).catch(() => {
          // Network request failed, probably offline
          // For navigation requests, show the offline page
          if (event.request.mode === 'navigate') {
            return caches.match('/offline.html');
          }
        });
      })
  );
});

// Activate event: clean up old caches
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