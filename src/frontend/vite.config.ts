import { defineConfig, loadEnv, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

// Paths that must never be pinned by a browser or an intermediary proxy.
// Everything under /assets/ is content-hashed and safe to cache forever; the
// app shell and the service worker script are not, and a stale copy of either
// is silently fatal: the SW keeps serving an old index.html, that old bundle
// asks for asset filenames whose hashes no longer exist, and the page renders
// an old UI with broken images while the server has the right files all along.
const SHELL_PATHS = /^\/(index\.html)?$|^\/sw\.js$|^\/registerSW\.js$|^\/manifest\.webmanifest$/;

function noCacheAppShell(): Plugin {
  return {
    name: 'easyorder-no-cache-app-shell',
    configurePreviewServer(server) {
      server.middlewares.use((req, res, next) => {
        const path = (req.url ?? '').split('?')[0];
        if (SHELL_PATHS.test(path)) {
          res.setHeader('Cache-Control', 'no-cache, max-age=0, must-revalidate');
        }
        next();
      });
    },
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    // Stamped into the bundle so any running page can say which build it is —
    // the first question worth asking when the UI looks out of date.
    define: {
      __BUILD_STAMP__: JSON.stringify(new Date().toISOString()),
    },
    plugins: [
      react(),
      noCacheAppShell(),
      VitePWA({
        registerType: 'autoUpdate',
        manifest: {
          name: 'EasyOrder — Group Food Ordering',
          short_name: 'EasyOrder',
          description:
            'Plan group meals, manage budgets, and checkout through Swiggy together.',
          theme_color: '#ff6b35',
          background_color: '#fff7ed',
          display: 'standalone',
          start_url: '/',
          icons: [
            { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
            { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
            {
              src: '/icons/icon-512-maskable.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'maskable',
            },
          ],
        },
        workbox: {
          // App shell: precache the build output, except the large landing
          // page photos — precaching those all at once saturates tunnel
          // proxies (localtunnel allows ~10 sockets) and starves the page's
          // own CSS/API requests. They are cached lazily at runtime instead.
          globPatterns: ['**/*.{js,css,html,png,svg,woff2}'],
          globIgnores: ['**/assets/*.png'],
          // Session API must stay network-first: the cart is collaborative
          // state polled every 2.5s; a stale cache would show wrong carts.
          // Workbox matches RegExp patterns against the full URL, not the
          // pathname, so these must not be anchored with ^.
          runtimeCaching: [
            {
              urlPattern: /\/api\/session\//,
              handler: 'NetworkFirst',
              options: {
                cacheName: 'session-api',
                networkTimeoutSeconds: 4,
                expiration: { maxEntries: 10, maxAgeSeconds: 300 },
              },
            },
            {
              urlPattern: /\/assets\/.*\.png$/,
              handler: 'CacheFirst',
              options: {
                cacheName: 'landing-images',
                expiration: { maxEntries: 12, maxAgeSeconds: 60 * 60 * 24 * 30 },
              },
            },
            {
              urlPattern: /^https:\/\/fonts\.(googleapis|gstatic)\.com\/.*/,
              handler: 'CacheFirst',
              options: {
                cacheName: 'google-fonts',
                expiration: { maxEntries: 20, maxAgeSeconds: 60 * 60 * 24 * 365 },
              },
            },
          ],
          // Never cache mutations or auth.
          navigateFallbackDenylist: [/^\/api\//],
        },
      }),
    ],
    server: {
      allowedHosts: ['.ngrok-free.app', '.loca.lt', 'localhost', '127.0.0.1'],
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  };
});
