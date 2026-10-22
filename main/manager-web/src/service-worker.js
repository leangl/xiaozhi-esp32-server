/* global self, workbox */

// Custom Service Worker installation and activation handling
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// CDN resource list
const CDN_CSS = [
  'https://unpkg.com/element-ui@2.15.14/lib/theme-chalk/index.css',
  'https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.min.css'
];

const CDN_JS = [
  'https://unpkg.com/vue@2.6.14/dist/vue.min.js',
  'https://unpkg.com/vue-router@3.6.5/dist/vue-router.min.js',
  'https://unpkg.com/vuex@3.6.2/dist/vuex.min.js',
  'https://unpkg.com/element-ui@2.15.14/lib/index.js',
  'https://unpkg.com/axios@0.27.2/dist/axios.min.js',
  'https://unpkg.com/opus-decoder@0.7.7/dist/opus-decoder.min.js'
];

// Run automatically after the Service Worker manifest is injected
const manifest = self.__WB_MANIFEST || [];

// Check whether CDN mode is enabled
const isCDNEnabled = manifest.some(entry => 
  entry.url === 'cdn-mode' && entry.revision === 'enabled'
);

console.log(`Service Worker initialized, CDN mode: ${isCDNEnabled ? 'enabled' : 'disabled'}`);

// Inject Workbox code
importScripts('https://storage.googleapis.com/workbox-cdn/releases/7.0.0/workbox-sw.js');
workbox.setConfig({ debug: false });

// Enable Workbox
workbox.core.skipWaiting();
workbox.core.clientsClaim();

// Precache the offline page
const OFFLINE_URL = '/offline.html';
workbox.precaching.precacheAndRoute([
  { url: OFFLINE_URL, revision: null }
]);

// Log installation from the installation-complete handler
self.addEventListener('install', event => {
  if (isCDNEnabled) {
    console.log('Service Worker installed; caching CDN resources');
  } else {
    console.log('Service Worker installed with CDN mode disabled; caching local resources only');
  }
  
  // Ensure the offline page is cached
  event.waitUntil(
    caches.open('offline-cache').then((cache) => {
      return cache.add(OFFLINE_URL);
    })
  );
});

// Add an activation handler
self.addEventListener('activate', event => {
  console.log('Service Worker activated and now controlling the page');
  
  // Clean up old cache versions
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(cacheName => {
          // Delete caches other than the current version
          return cacheName.startsWith('workbox-') && !workbox.core.cacheNames.runtime.includes(cacheName);
        }).map(cacheName => {
          return caches.delete(cacheName);
        })
      );
    })
  );
});

// Intercept fetch events to inspect CDN cache hits
self.addEventListener('fetch', event => {
  // Monitor CDN caching only in CDN mode
  if (isCDNEnabled) {
    const url = new URL(event.request.url);
    
    // Log whether CDN resources hit the cache
    if ([...CDN_CSS, ...CDN_JS].includes(url.href)) {
      // Add logging without interfering with the fetch flow
      console.log(`Requesting CDN resource: ${url.href}`);
    }
  }
});

// Cache CDN resources only in CDN mode
if (isCDNEnabled) {
  // Cache CDN CSS resources
  workbox.routing.registerRoute(
    ({ url }) => CDN_CSS.includes(url.href),
    new workbox.strategies.CacheFirst({
      cacheName: 'cdn-stylesheets',
      plugins: [
        new workbox.expiration.ExpirationPlugin({
          maxAgeSeconds: 365 * 24 * 60 * 60, // Cache for one year
          maxEntries: 10, // Cache up to 10 CSS files
        }),
        new workbox.cacheableResponse.CacheableResponsePlugin({
          statuses: [0, 200], // Cache successful responses
        }),
      ],
    })
  );

  // Cache CDN JavaScript resources
  workbox.routing.registerRoute(
    ({ url }) => CDN_JS.includes(url.href),
    new workbox.strategies.CacheFirst({
      cacheName: 'cdn-scripts',
      plugins: [
        new workbox.expiration.ExpirationPlugin({
          maxAgeSeconds: 365 * 24 * 60 * 60, // Cache for one year
          maxEntries: 20, // Cache up to 20 JavaScript files
        }),
        new workbox.cacheableResponse.CacheableResponsePlugin({
          statuses: [0, 200], // Cache successful responses
        }),
      ],
    })
  );
}

// Cache local static resources regardless of CDN mode
workbox.routing.registerRoute(
  /\.(?:js|css|png|jpg|jpeg|svg|gif|ico|woff|woff2|eot|ttf|otf)$/,
  new workbox.strategies.StaleWhileRevalidate({
    cacheName: 'static-resources',
    plugins: [
      new workbox.expiration.ExpirationPlugin({
        maxAgeSeconds: 7 * 24 * 60 * 60, // Cache for 7 days
        maxEntries: 50, // Cache up to 50 files
      }),
    ],
  })
);

// Cache HTML pages
workbox.routing.registerRoute(
  /\.html$/,
  new workbox.strategies.NetworkFirst({
    cacheName: 'html-cache',
    plugins: [
      new workbox.expiration.ExpirationPlugin({
        maxAgeSeconds: 1 * 24 * 60 * 60, // Cache for one day
        maxEntries: 10, // Cache up to 10 HTML files
      }),
    ],
  })
);

// Offline page: use more reliable handling
workbox.routing.setCatchHandler(async ({ event }) => {
  // Return the appropriate fallback for the request type
  switch (event.request.destination) {
    case 'document':
      // Return the offline page for page requests
      return caches.match(OFFLINE_URL);
    default:
      // Return errors for all other requests
      return Response.error();
  }
});
