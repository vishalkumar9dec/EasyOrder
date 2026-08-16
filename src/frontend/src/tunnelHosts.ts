// Hostnames that are demo tunnels rather than a real deployment.
//
// A service worker on one of these is all cost and no benefit: offline support
// buys nothing during a five-minute demo, while a cached app shell outlives the
// build that produced it. localtunnel reuses subdomains, so the next session on
// the same URL inherits the previous one's stale UI — and its old bundle asks
// for asset hashes the server no longer has, which renders as missing images.
const TUNNEL_HOST_SUFFIXES = ['.loca.lt', '.ngrok-free.app', '.ngrok.io', '.trycloudflare.com'];

export function isTunnelHost(hostname: string): boolean {
  const normalized = hostname.toLowerCase();
  return TUNNEL_HOST_SUFFIXES.some((suffix) => normalized.endsWith(suffix));
}
