// StudyShield Background Service Worker (Manifest V3)
// Handles local API calls without HTTPS/Mixed-Content restrictions and broadcasts preference changes

const API_BASE = 'http://127.0.0.1:8000';

async function fetchBackend(path, options = {}, timeoutMs = 450) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timer);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    clearTimeout(timer);
    throw err;
  }
}

function broadcastToTabs(payload) {
  chrome.tabs.query({}, (tabs) => {
    tabs.forEach((tab) => {
      const url = tab.url || '';
      if (
        url.includes('youtube.com') ||
        url.includes('test_youtube_mock.html') ||
        url.startsWith('file://')
      ) {
        try {
          chrome.tabs.sendMessage(tab.id, payload, () => {
            void chrome.runtime.lastError;
          });
        } catch (_) {}
      }
    });
  });
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'DECIDE') {
    fetchBackend('/decide', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request.data)
    })
      .then((data) => sendResponse({ success: true, data }))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (request.action === 'GET_PREFERENCES') {
    fetchBackend('/preferences', { method: 'GET' })
      .then((data) => sendResponse({ success: true, data }))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (request.action === 'SAVE_PREFERENCES') {
    fetchBackend('/preferences', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request.data)
    }).catch(() => {});

    chrome.storage.local.set(request.data, () => {
      broadcastToTabs({
        action: 'PREFERENCES_UPDATED',
        data: request.data
      });
      sendResponse({ success: true });
    });
    return true;
  }

  if (request.action === 'FORCE_RESCAN') {
    broadcastToTabs({ action: 'FORCE_RESCAN' });
    sendResponse({ success: true });
    return true;
  }
});
