/**
 * The real read/command API's base URL, derived from whatever host Atlas
 * itself was loaded from — works unchanged whether Atlas is opened at
 * localhost (dev) or a remote Tailscale IP (viewing from another
 * device), since the backend always listens on the same host Atlas was
 * served from, port 8765. No IP is ever hardcoded here, so this never
 * needs updating if that IP changes.
 */
export function readApiBaseUrl(): string {
  const hostname = typeof window !== "undefined" ? window.location.hostname : "127.0.0.1";
  return `http://${hostname}:8765`;
}
