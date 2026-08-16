import { describe, expect, it } from 'vitest';

import { isTunnelHost } from './tunnelHosts';

describe('isTunnelHost', () => {
  it('recognises the tunnels this project actually uses', () => {
    for (const host of [
      'easyorder-web-dev.loca.lt',
      'easyorder-api-dev.loca.lt',
      'abc123.ngrok-free.app',
      'legacy.ngrok.io',
      'something.trycloudflare.com',
    ]) {
      expect(isTunnelHost(host)).toBe(true);
    }
  });

  it('leaves local development and real deployments alone', () => {
    for (const host of ['localhost', '127.0.0.1', 'easyorder.app', 'app.easyorder.in']) {
      expect(isTunnelHost(host)).toBe(false);
    }
  });

  it('is not fooled by a lookalike domain', () => {
    // Matches on a dotted suffix, so neither a host that merely contains a
    // tunnel domain nor one that merely ends with those letters counts —
    // `notloca.lt` is a different registrable domain, not a loca.lt subdomain.
    expect(isTunnelHost('loca.lt.example.com')).toBe(false);
    expect(isTunnelHost('notloca.lt')).toBe(false);
    expect(isTunnelHost('EASYORDER.LOCA.LT')).toBe(true);
  });
});
