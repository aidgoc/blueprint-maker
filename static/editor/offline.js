// static/editor/offline.js
// Detects online/offline status, shows banner, flushes save queue on reconnect

(function() {
  'use strict';

  var banner = null;
  var dismissTimeout = null;

  function createBanner() {
    if (banner) return banner;
    banner = document.createElement('div');
    banner.id = 'offlineBanner';
    banner.className = 'offline-banner';
    banner.style.display = 'none';
    document.body.insertBefore(banner, document.body.firstChild);
    return banner;
  }

  function showBanner(message, type) {
    var b = createBanner();
    b.textContent = message;
    b.className = 'offline-banner offline-' + type;
    b.style.display = 'block';

    if (dismissTimeout) clearTimeout(dismissTimeout);
    if (type === 'synced') {
      dismissTimeout = setTimeout(function() {
        b.style.display = 'none';
      }, 3000);
    }
  }

  function hideBanner() {
    if (banner) banner.style.display = 'none';
  }

  function onOffline() {
    showBanner("You're offline \u2014 changes saved locally", 'offline');
  }

  function onOnline() {
    showBanner('Back online \u2014 syncing...', 'reconnecting');
    if (window.BlockEditor && BlockEditor.flushOfflineQueue) {
      BlockEditor.flushOfflineQueue();
    }
    setTimeout(function() {
      showBanner('All changes synced', 'synced');
    }, 1500);
  }

  window.addEventListener('offline', onOffline);
  window.addEventListener('online', onOnline);

  if (!navigator.onLine) {
    onOffline();
  }

  window.OfflineDetector = {
    isOnline: function() { return navigator.onLine; },
    showBanner: showBanner,
    hideBanner: hideBanner
  };
})();
