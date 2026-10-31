self.addEventListener('push', event => {
  let data = {};
  try { data = event.data.json(); } catch (_) {}
  const title = data.title || 'dope2000 LIVE通知';
  const options = {
    body: data.body || 'TikTokでライブが始まりました。',
    icon: '/static/icon-192.png',
    badge: '/static/icon-192.png',
    data: { url: data.url || 'https://www.tiktok.com/@dope2000/live' }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = event.notification.data && event.notification.data.url;
  event.waitUntil(clients.openWindow(url || 'https://www.tiktok.com/@dope2000/live'));
});
