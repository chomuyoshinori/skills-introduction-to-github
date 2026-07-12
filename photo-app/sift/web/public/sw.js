// Sift Service Worker(PWA 用の最小構成)
// - /api/* は常にネットワーク(キャッシュしない — 判断状態が古くなるのを防ぐ)
// - /assets/*(ハッシュ付きで不変)はキャッシュ優先
// - それ以外(index.html 等)はネットワーク優先、オフライン時のみキャッシュ
const VER = 'sift-v1';

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VER).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin || url.pathname.startsWith('/api/')) return;

  if (url.pathname.startsWith('/assets/')) {
    e.respondWith(
      caches.open(VER).then(async (c) => {
        const hit = await c.match(e.request);
        if (hit) return hit;
        const res = await fetch(e.request);
        if (res.ok) c.put(e.request, res.clone());
        return res;
      })
    );
    return;
  }

  e.respondWith(
    fetch(e.request)
      .then((res) => {
        if (res.ok) {
          const clone = res.clone();
          caches.open(VER).then((c) => c.put(e.request, clone));
        }
        return res;
      })
      .catch(() => caches.match(e.request).then((hit) => hit ?? Response.error()))
  );
});
