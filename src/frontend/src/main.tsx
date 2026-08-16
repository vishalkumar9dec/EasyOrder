import React from 'react';
import ReactDOM from 'react-dom/client';

import { App } from './App';
import './styles.css';
import { isTunnelHost } from './tunnelHosts';

// Which build is this page actually running? A stale service worker can serve
// an old app shell long after the server has a new one, and the symptom
// (missing nav, broken images) looks like a code regression. Printing the
// stamp turns that into a five-second check — compare it with the build you
// deployed. See docs/runbooks/tunnel-408-502-blank-page.md.
console.info(`EasyOrder build ${__BUILD_STAMP__}`);

// Shed a service worker left behind on a demo tunnel host, along with its
// caches. Production keeps its PWA; see tunnelHosts.ts for why tunnels don't.
if (isTunnelHost(window.location.hostname) && 'serviceWorker' in navigator) {
  navigator.serviceWorker
    .getRegistrations()
    .then(async (registrations) => {
      if (registrations.length === 0) return;
      await Promise.all(registrations.map((registration) => registration.unregister()));
      if ('caches' in window) {
        const names = await caches.keys();
        await Promise.all(names.map((name) => caches.delete(name)));
      }
      console.info('EasyOrder: removed a service worker left on this tunnel host.');
    })
    .catch(() => {
      // Best effort. Never let cache hygiene stop the app from rendering.
    });
}

if (window.location.pathname === '/' && window.location.hash === '#demo') {
  window.history.replaceState(null, '', '/demo');
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
