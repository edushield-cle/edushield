const V = "edushield-m10";
const FILES = ["./", "index.html", "app.js", "config.js", "model.js", "blocklist.js", "detector.js", "sha256.js", "chinh-sach.html", "cai-dat.html", "cai-dat.js", "deco.js", "manifest.webmanifest", "icon-192.png", "icon-512.png", "drill.html", "drill.js", "drill.css", "drill-page.js"];
self.addEventListener("install", (e) => { e.waitUntil(caches.open(V).then((c) => c.addAll(FILES)).then(() => self.skipWaiting())); });
self.addEventListener("activate", (e) => { e.waitUntil(caches.keys().then((k) => Promise.all(k.filter((x) => x !== V).map((x) => caches.delete(x)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET" || new URL(e.request.url).origin !== location.origin) return; // không đụng tới yêu cầu gửi thống kê
  e.respondWith(caches.match(e.request, { ignoreSearch: true }).then((r) => r || fetch(e.request)));
});
// Bấm vào thông báo: mở lại (hoặc đưa lên trước) ứng dụng EduShield
self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((cs) => {
    const url = (e.notification.data && e.notification.data.url) || "./";
    if (url !== "./") return self.clients.openWindow(url);
    for (const c of cs) if ("focus" in c) return c.focus();
    return self.clients.openWindow("./");
  }));
});
