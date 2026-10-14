// StudyShield Background Service Worker (Manifest V3)
// Handles local API calls without HTTPS/Mixed-Content restrictions and broadcasts preference changes

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'DECIDE') {
    fetch('http://localhost:8000/decide', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request.data)
    })
    .then(res => res.json())
    .then(data => sendResponse({ success: true, data: data }))
    .catch(err => {
      sendResponse({ success: false, error: err.message });
    });
    return true;
  }

  if (request.action === 'GET_PREFERENCES') {
    fetch('http://localhost:8000/preferences')
      .then(res => res.json())
      .then(data => sendResponse({ success: true, data: data }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (request.action === 'SAVE_PREFERENCES') {
    // 1. Post to local backend server
    fetch('http://localhost:8000/preferences', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request.data)
    })
    .then(res => res.json())
    .catch(() => {});

    // 2. Save directly to chrome.storage.local
    chrome.storage.local.set(request.data, () => {
      // 3. Immediately broadcast to all YouTube and mock tabs
      chrome.tabs.query({}, (tabs) => {
        tabs.forEach(tab => {
          if (tab.url && (tab.url.includes('youtube.com') || tab.url.includes('test_youtube_mock.html') || tab.url.startsWith('file://'))) {
            try {
              chrome.tabs.sendMessage(tab.id, { 
                action: 'PREFERENCES_UPDATED',
                data: request.data
              }, () => {
                // Ignore errors for unscripted tabs
                if (chrome.runtime.lastError) {}
              });
            } catch (e) {}
          }
        });
      });
      sendResponse({ success: true });
    });
    return true;
  }

  if (request.action === 'FORCE_RESCAN') {
    chrome.tabs.query({}, (tabs) => {
      tabs.forEach(tab => {
        if (tab.url && (tab.url.includes('youtube.com') || tab.url.includes('test_youtube_mock.html') || tab.url.startsWith('file://'))) {
          try {
            chrome.tabs.sendMessage(tab.id, { action: 'FORCE_RESCAN' }, () => {
              if (chrome.runtime.lastError) {}
            });
          } catch (e) {}
        }
      });
    });
    sendResponse({ success: true });
    return true;
  }
});
