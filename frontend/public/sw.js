/* global self, caches, fetch */

const CACHE_VERSION = "qdi-static-v1";
const STATIC_CACHE = CACHE_VERSION;
const STATIC_ALLOWLIST_PREFIX = ["/_next/static/", "/brand/", "/icon", "/apple-icon", "/opengraph-image", "/twitter-image"];
const STATIC_ALLOWLIST_EXT = [".js", ".css", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".ico", ".woff2"];
const SENSITIVE_PREFIX = ["/api/", "/api-backend/", "/dashboard", "/diagnostico/", "/login", "/cadastro"];

const isStaticPath = (pathname) =>
  STATIC_ALLOWLIST_PREFIX.some((prefix) => pathname.startsWith(prefix)) ||
  STATIC_ALLOWLIST_EXT.some((ext) => pathname.endsWith(ext));

const isSensitivePath = (pathname) => SENSITIVE_PREFIX.some((prefix) => pathname.startsWith(prefix));

self.addEventListener("install", (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const names = await caches.keys();
      await Promise.all(names.filter((name) => name !== STATIC_CACHE).map((name) => caches.delete(name)));
      await self.clients.claim();
    })(),
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  const { pathname } = url;

  // Não cachear APIs nem áreas sensíveis de sessão.
  if (isSensitivePath(pathname)) return;

  if (!isStaticPath(pathname)) return;

  event.respondWith(
    (async () => {
      const cache = await caches.open(STATIC_CACHE);
      const cached = await cache.match(req);
      if (cached) {
        void fetch(req)
          .then((res) => {
            if (res.ok) return cache.put(req, res.clone());
            return undefined;
          })
          .catch(() => undefined);
        return cached;
      }

      const fresh = await fetch(req);
      if (fresh.ok) {
        await cache.put(req, fresh.clone());
      }
      return fresh;
    })(),
  );
});
