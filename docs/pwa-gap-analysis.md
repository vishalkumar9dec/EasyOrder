# PWA Gap Analysis — EasyOrder Frontend

Status: **remediated (2026-07-13)**. The artifacts in section 4 are now implemented:
`vite-plugin-pwa` generates `manifest.webmanifest` + `sw.js` at build time, PWA meta
tags and icons (`public/icons/`) are in place, and `SessionPage` shows an offline
banner with mutations disabled via `useOnlineStatus`. The analysis below is kept as
the record of the original gap.

Original status: the project claims to ship a "PWA" throughout its documentation, but the
frontend contains none of the technical artifacts that define a Progressive Web
App. This document inventories the claims, the evidence, why it matters for this
specific product, and provides ready-to-use remediation artifacts.

## 1. The claim inventory

The term "PWA" appears **169 times** across `docs/` and `README.md`. Representative
load-bearing claims:

| Location | Claim |
| --- | --- |
| `docs/easyorder-prd.md:10` | "…PWA canvas. It has two complementary WhatsApp operating modes" |
| `docs/easyorder-prd.md:61` | "As a group guest, I want to open the shared PWA link…" |
| `docs/easyorder-prd.md:114` | "The PWA session page should show a compact timeline…" |
| `docs/builder-program-positioning.md:23` | "Seamless handoff from conversational UI (WhatsApp) to visual UI (Collaborative PWA)" |
| `docs/easyorder-pwa-design-review.md` | Entire document titled "EasyOrder PWA Design Directions" |
| `docs/easyorder-pwa-visual-philosophy.md` | Entire document about "the PWA" |
| `src/frontend/src/accountModel.ts:2` | Code comment: "The PWA renders the same records the WhatsApp chat answers with" |

## 2. The evidence: none of the PWA-defining artifacts exist

A PWA is defined by three technical requirements: a web app manifest, a service
worker, and HTTPS. The first two are entirely absent.

**No web app manifest.**
- `find src/frontend -name "manifest*"` (excluding node_modules) → no results.
- No `public/` directory exists at all in `src/frontend/`.
- `index.html` contains no `<link rel="manifest">`, no `theme-color` meta, no
  `apple-touch-icon`, no `apple-mobile-web-app-capable`. The only icon is an
  inline SVG data-URI favicon.

**No service worker.**
- Zero matches for `serviceWorker`, `workbox`, `registerSW`, or `navigator.serviceWorker`
  anywhere in `src/frontend/src`.
- `main.tsx` is 11 lines: React root render only, no SW registration.
- `vite.config.ts` has only `@vitejs/plugin-react` — no `vite-plugin-pwa`.
- `package.json` dependencies are exactly `react` and `react-dom`; devDependencies
  contain no PWA tooling.

**No offline capability.**
- The production build (`dist/`) contains only `index.html` and hashed assets —
  no `sw.js`, no `manifest.webmanifest` (verified by find).
- Every screen is a bare `fetch`; a failed load renders "Session could not be
  loaded" text. There is no cache fallback, no `navigator.onLine` check, no
  offline UI state at the app level.
- The only "offline" strings in the codebase (`useSupabaseCartRealtime.ts:19,40`,
  `styles.css:343`) belong to the polling-failure indicator — they describe the
  poll loop's state, not offline support.

**Installability check (what a reviewer would see).** Chrome DevTools → Application
→ Manifest would show "No manifest detected." Lighthouse's PWA audit would fail
every installability criterion. There is no "Add to Home Screen" install prompt
on Android; on iOS, adding to home screen would produce a white default icon and
launch with Safari chrome.

## 3. Why this matters more for EasyOrder than for a typical web app

This is not pedantry about a buzzword. The product's own funnel makes PWA
capabilities unusually relevant:

1. **The app is opened from a WhatsApp link on a phone.** That is the exact
   scenario PWA install/standalone display targets. A guest who orders with the
   group weekly has no way to return except finding the old WhatsApp message.
   `display: standalone` + install prompt converts a one-shot link into a
   recurring surface — directly relevant to the Phase-2 "persistent commerce
   assistant" ambition in the positioning doc.
2. **WhatsApp's in-app browser and flaky mobile networks.** A cart canvas that
   white-screens on a dropped connection mid-session is a real failure mode for
   the core use case. An app-shell cache means the UI loads instantly and shows
   the last-known cart with a "reconnecting" banner instead of a blank page.
3. **The docs promise it 169 times.** For a builder-program reviewer, the gap
   between "Collaborative PWA" in the positioning doc and "no manifest detected"
   in DevTools is a 30-second credibility check that currently fails.

Honest alternatives: either implement the artifacts below (~half a day), or do a
find-and-replace of "PWA" → "mobile web app" across the docs. Both are defensible;
the current state is not.

## 4. Remediation artifacts

### 4.1 Install tooling

```bash
cd src/frontend
npm install -D vite-plugin-pwa
```

### 4.2 `vite.config.ts` (replace plugins line)

```ts
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [
      react(),
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
          // App shell: precache the build output.
          globPatterns: ['**/*.{js,css,html,png,svg,woff2}'],
          // Session API must stay network-first: the cart is collaborative
          // state polled every 2.5s; a stale cache would show wrong carts.
          runtimeCaching: [
            {
              urlPattern: /^\/api\/session\/.*/,
              handler: 'NetworkFirst',
              options: {
                cacheName: 'session-api',
                networkTimeoutSeconds: 4,
                expiration: { maxEntries: 10, maxAgeSeconds: 300 },
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
```

### 4.3 `index.html` additions (inside `<head>`)

```html
<meta name="theme-color" content="#ff6b35" />
<link rel="apple-touch-icon" href="/icons/icon-192.png" />
<meta name="mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="default" />
```

(`vite-plugin-pwa` injects the `<link rel="manifest">` automatically at build time.)

### 4.4 Icons

Create `src/frontend/public/icons/` with `icon-192.png`, `icon-512.png`, and
`icon-512-maskable.png` rendered from the existing inline SVG favicon (the orange
takeout-box mark in `index.html`). One-liner if `rsvg-convert` or similar is
available; otherwise export from any editor. The maskable variant needs ~10%
safe-zone padding.

### 4.5 Offline UX (minimal, honest version)

The service worker gives you an app shell that loads offline. Pair it with a
banner so the cached cart is not mistaken for live state:

```tsx
// useOnlineStatus.ts
import { useEffect, useState } from 'react';

export function useOnlineStatus(): boolean {
  const [online, setOnline] = useState(() => navigator.onLine);
  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => {
      window.removeEventListener('online', on);
      window.removeEventListener('offline', off);
    };
  }, []);
  return online;
}
```

In `SessionPage`, when `!online`: show a persistent "You're offline — showing the
last cart you saw. Edits are disabled." strip, and disable mutation buttons
(the global `isMutating` flag already provides the mechanism). Do **not** queue
offline cart mutations (Background Sync) in the MVP — for a collaborative cart,
replaying stale edits after reconnect is worse than blocking them.

### 4.6 Verification checklist

1. `npm run build && npx vite preview` — `dist/` must now contain
   `manifest.webmanifest` and `sw.js`.
2. Chrome DevTools → Application → Manifest: name, icons, installability all green.
3. Lighthouse → PWA category: installable, has SW, themed.
4. DevTools → Network → Offline → reload: app shell renders with the offline strip
   instead of a white page.
5. Android Chrome via the localtunnel URL: "Add to Home Screen" prompt appears;
   launched app opens standalone without browser chrome.
6. Kill the backend while a session is open: polling indicator degrades to
   "reconnecting/offline" and cached shell stays usable.

## 5. Scope estimate

Manifest + plugin + icons + meta tags: ~2 hours. Offline banner + disabled
mutations: ~2 hours. Verification across Android/iOS: ~1-2 hours. Total roughly
half a day to make the 169 documented mentions of "PWA" true.
