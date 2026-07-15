# Tunnel 408/502 Blank (or Unstyled) Page — Root Cause & Fix

When the guest/host link sent to WhatsApp opened over a free tunnel
(`*.loca.lt`), the page either white-screened or rendered with **no styling**.
DevTools showed `408 Request Timeout` / `502 Bad Gateway` on specific assets
while the HTML document itself returned `200`.

This runbook documents the **payload-size** fix: make what the tunnel has to
carry small enough that a bandwidth-limited free tunnel can deliver it. It is
complementary to [ngrok-dev-tunnel.md](ngrok-dev-tunnel.md), which fixes the
same class of failure by switching to a more capable tunnel. Either approach
works; this one keeps loca.lt viable and also makes the deployed app faster.

## Symptoms

| What you see | Where |
|---|---|
| Blank white page, or page with unstyled raw text | Browser |
| `408` / `502` on `react-dom_client.js`, `index-*.css`, `manifest.webmanifest` | DevTools → Network |
| Document (`session/...`) is `200`, but assets after it fail | DevTools → Network |
| Small files (`App.tsx`, a source module) load; large files fail | DevTools → Network |
| Failing requests all die at ~10.9s | DevTools → Timing |

The tell is that **big responses fail and small ones succeed** — a throughput
and timeout problem, not an application error. Nothing is wrong with the
session, tokens, or app code.

## Root Cause

Free tunnels (loca.lt) give very little bandwidth per connection, cap
concurrent sockets at ~10, and enforce a **~10-second per-request cutoff**.
Two things were pushing far more than that through the tunnel:

1. **The Vite *dev server* was behind the tunnel.** Dev mode ships
   unminified, unbundled modules. `react-dom_client.js` alone was **~2.8 MB**.
   Locally it returns in ~25 ms; through loca.lt it consistently died at
   ~10.9 s with a `408`/`502`. Because React never loaded, every downstream
   module errored and the page came up blank.

2. **The service worker precached the entire build on first load.** Once the
   PWA landed, the SW's install step fetched *all* precached assets at once —
   including **~5 MB of landing-page dish/hero photos** — saturating the
   tunnel's ~10 sockets exactly while the page was still fetching its own CSS
   and manifest. Those got starved and returned `502`, producing the
   *loaded-but-unstyled* variant.

## The Fix

### 1. Serve the production build through the tunnel, not the dev server

The built app is one hashed, minified, gzipped bundle (~245 KB gzipped) instead
of dozens of multi-megabyte dev requests.

```bash
cd src/frontend
npm run build
npm run preview          # serves dist/ on :4173, /api still proxies to the backend
npx localtunnel --port 4173 --subdomain easyorder-web-dev
```

A `frontend-preview-built` config is in `.claude/launch.json` for this (the SW
only registers in the built output, so previewing the build is also how you
verify PWA behavior).

### 2. Keep the big images out of install-time precache

In `src/frontend/vite.config.ts`, the `VitePWA` Workbox config excludes the
photos from precache and caches them lazily at runtime instead:

```ts
workbox: {
  globPatterns: ['**/*.{js,css,html,png,svg,woff2}'],
  globIgnores: ['**/assets/*.png'],        // photos are NOT precached on install
  runtimeCaching: [
    // ...session API (NetworkFirst) and fonts...
    {
      urlPattern: /\/assets\/.*\.png$/,     // photos cached on first real use
      handler: 'CacheFirst',
      options: {
        cacheName: 'landing-images',
        expiration: { maxEntries: 12, maxAgeSeconds: 60 * 60 * 24 * 30 },
      },
    },
  ],
}
```

This dropped the first-visit precache from **~5 MB / 17 entries** to
**~317 KB / 11 entries**. Confirm it after a build:

```
npm run build
# ...
PWA vX.Y.Z
mode      generateSW
precache  11 entries (~317 KiB)      # not 17 entries / 5 MB
```

> Note: a second bug was fixed in the same config — the session-API runtime
> cache pattern was `^`-anchored (`/^\/api\/session\//`), but Workbox matches
> RegExp against the **full URL**, so it never matched. The un-anchored
> `/\/api\/session\//` is what actually enables network-first caching of
> session responses.

## Why This Compounds In Our Favor

After one successful load, the service worker has the app shell cached on the
device. Repeat opens of a WhatsApp link then serve the UI from cache and only
carry the small session JSON over the tunnel — so styling can never break on a
subsequent visit, even on a flaky connection.

## Verify

Fetch the key assets through the live tunnel — all should be `200`:

```bash
CSS=$(basename src/frontend/dist/assets/*.css)
for p in "" "assets/$CSS" "manifest.webmanifest" "sw.js"; do
  curl -s -o /dev/null -w "/$p -> %{http_code} (%{time_total}s)\n" \
    "https://easyorder-web-dev.loca.lt/$p" -H "User-Agent: curl-check" --max-time 30
done
```

Then open the WhatsApp guest/host link and reload once to let the new service
worker install.

## When To Use ngrok Instead

The payload fix keeps loca.lt usable, but on a **cold** load (empty SW cache)
loca.lt can still drop a request under a concurrent burst — that is the free
tunnel's capacity, not the app. For a genuinely stable URL (needed for
dev-mode HMR, or to stop re-pointing the Meta webhook), migrate to ngrok's free
static domain per [ngrok-dev-tunnel.md](ngrok-dev-tunnel.md). ngrok has no
~10-second cutoff, and `vite.config.ts` already allowlists `.ngrok-free.app`.

## TL;DR

| Do | Don't |
|---|---|
| Tunnel the **production build** (`npm run preview`, `:4173`) | Tunnel the Vite **dev server** (multi-MB dev chunks) |
| Keep large images out of SW precache (lazy runtime cache) | Precache the whole `dist/` including ~5 MB of photos |
| Reload once after deploy to let the new SW install | Assume a cold first load is instant over a free tunnel |
| Move to ngrok for a stable URL / HMR | Fight loca.lt zombie leases for a fixed subdomain |
