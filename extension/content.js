// StudyShield Content Script — Modern YouTube & Shorts Focus Engine

(() => {
  console.log(
    '%c[StudyShield 🛡️] Initialized. Monitoring YouTube Videos & Shorts.',
    'color: #38bdf8; font-size: 13px; font-weight: bold; background: #0f172a; padding: 4px 8px; border-radius: 4px;'
  );

  let shieldEnabled = true;
  let activeCategories = ['study'];
  let customKeywords = [];
  let lastUpdatedAt = 0;
  const decisionCache = new Map();

  // Load preferences from local storage
  chrome.storage.local.get(['shieldEnabled', 'activeCategories', 'customKeywords', 'updated_at'], (res) => {
    if (res.shieldEnabled !== undefined) shieldEnabled = res.shieldEnabled;
    if (res.activeCategories) activeCategories = res.activeCategories;
    if (res.customKeywords) customKeywords = res.customKeywords;
    if (res.updated_at) lastUpdatedAt = res.updated_at;
  });

  // Listen to chrome.storage changes in real-time
  try {
    chrome.storage.onChanged.addListener((changes, area) => {
      if (area === 'local') {
        let changed = false;
        if (changes.shieldEnabled !== undefined) {
          shieldEnabled = changes.shieldEnabled.newValue;
          changed = true;
        }
        if (changes.activeCategories !== undefined) {
          activeCategories = changes.activeCategories.newValue || ['study'];
          changed = true;
        }
        if (changes.customKeywords !== undefined) {
          customKeywords = changes.customKeywords.newValue || [];
          changed = true;
        }
        if (changes.updated_at !== undefined) {
          lastUpdatedAt = changes.updated_at.newValue || 0;
          changed = true;
        }
        if (changed) {
          triggerImmediateReScan('Preferences Updated');
        }
      }
    });
  } catch (e) {}

  // Listen for direct broadcast messages from Popup or Background
  try {
    chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
      if (msg.action === 'PREFERENCES_UPDATED') {
        if (msg.data) {
          if (msg.data.shield_enabled !== undefined) shieldEnabled = msg.data.shield_enabled;
          if (msg.data.shieldEnabled !== undefined) shieldEnabled = msg.data.shieldEnabled;
          if (msg.data.active_categories) activeCategories = msg.data.active_categories;
          if (msg.data.activeCategories) activeCategories = msg.data.activeCategories;
          if (msg.data.custom_keywords) customKeywords = msg.data.custom_keywords;
          if (msg.data.customKeywords) customKeywords = msg.data.customKeywords;
        }
        triggerImmediateReScan('Preferences Applied');
        if (sendResponse) sendResponse({ success: true });
        return true;
      }
      if (msg.action === 'FORCE_RESCAN') {
        triggerImmediateReScan('Manual Re-Scan');
        if (sendResponse) sendResponse({ success: true });
        return true;
      }
    });
  } catch (e) {}

  // Also support window message for simulation testing pages
  window.addEventListener('message', (event) => {
    if (event.data && event.data.action === 'PREFERENCES_UPDATED') {
      const d = event.data.data;
      if (d) {
        if (d.shield_enabled !== undefined) shieldEnabled = d.shield_enabled;
        if (d.shieldEnabled !== undefined) shieldEnabled = d.shieldEnabled;
        if (d.active_categories) activeCategories = d.active_categories;
        if (d.activeCategories) activeCategories = d.activeCategories;
      }
      triggerImmediateReScan('Preferences Saved & Applied');
    }
  });

  // Floating notification toast on YouTube
  function showToast(message) {
    let toast = document.getElementById('studyshield-live-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'studyshield-live-toast';
      toast.className = 'studyshield-toast';
      document.body.appendChild(toast);
    }
    const catList = activeCategories.map(c => c.charAt(0).toUpperCase() + c.slice(1)).join(', ');
    toast.innerHTML = `
      <div class="studyshield-toast-content">
        <span class="studyshield-toast-icon">🛡️</span>
        <div>
          <div class="studyshield-toast-title">StudyShield: ${message}</div>
          <div class="studyshield-toast-sub">Active Allowed: <strong>${catList || 'None (All Blurred)'}</strong></div>
        </div>
      </div>
    `;
    toast.classList.add('studyshield-toast-show');
    clearTimeout(toast._hideTimer);
    toast._hideTimer = setTimeout(() => {
      toast.classList.remove('studyshield-toast-show');
    }, 2800);
  }

  // Force re-evaluation of ALL elements on the page immediately
  function triggerImmediateReScan(reason = 'Updated') {
    decisionCache.clear();
    // Wipe evaluation flags from all existing cards and Shorts
    document.querySelectorAll('.studyshield-card-container, [data-studyshield-done]').forEach(el => {
      delete el.dataset.studyshieldDone;
      delete el.dataset.studyshieldId;
      delete el.dataset.studyshieldUserRevealed;
    });

    scanAllContent();
    showToast(reason);
  }

  // Periodically check local backend server for Desktop App changes
  function syncPreferences() {
    try {
      chrome.runtime.sendMessage({ action: 'GET_PREFERENCES' }, (response) => {
        if (response && response.success && response.data) {
          const d = response.data;
          const serverUpdated = d.updated_at || 0;
          const categoriesMatch = JSON.stringify(activeCategories) === JSON.stringify(d.active_categories);
          const shieldMatch = shieldEnabled === (d.shield_enabled !== undefined ? d.shield_enabled : true);

          if (!categoriesMatch || !shieldMatch || (serverUpdated && serverUpdated > lastUpdatedAt)) {
            shieldEnabled = d.shield_enabled !== undefined ? d.shield_enabled : true;
            activeCategories = d.active_categories || ['study'];
            customKeywords = d.custom_keywords || [];
            lastUpdatedAt = serverUpdated;

            chrome.storage.local.set({
              shieldEnabled: shieldEnabled,
              activeCategories: activeCategories,
              customKeywords: customKeywords,
              updated_at: lastUpdatedAt
            });

            triggerImmediateReScan('Preferences Synced');
          }
        }
      });
    } catch (e) {}
  }
  syncPreferences();
  setInterval(syncPreferences, 1200); // Fast 1.2s polling for instant Desktop App sync

  // Clean word-boundary taxonomies
  const categoryTaxonomies = {
    'cooking': {
      name: '🍲 Cooking & Food',
      kws: ['recipe', 'cooking', 'cook', 'food', 'street food', 'kitchen', 'chef', 'burger', 'pizza', 'biryani', 'cake', 'baking', 'eating', 'mukbang', 'dessert', 'taste test']
    },
    'cartoon': {
      name: '🎬 Cartoon & Animation',
      kws: ['cartoon', 'animated', 'animation', 'tom and jerry', 'disney', 'pixar', 'ben 10', 'shinchan', 'doraemon', 'oggy', 'chhota bheem', 'peppa pig', 'mr bean', 'looney tunes']
    },
    'anime': {
      name: '🎌 Anime & Manga',
      kws: ['anime', 'manga', 'naruto', 'one piece', 'bleach', 'attack on titan', 'aot', 'jujutsu kaisen', 'jjk', 'demon slayer', 'dragon ball', 'dbz', 'ghibli', 'solo leveling', 'chainsaw man']
    },
    'gaming': {
      name: '🎮 Gaming & Esports',
      kws: ['game', 'gameplay', 'gaming', 'minecraft', 'gta', 'valorant', 'fortnite', 'pubg', 'bgmi', 'roblox', 'call of duty', 'walkthrough', 'stream', 'twitch', 'esports', 'boss fight', 'clutch', '1v5', 'ace', 'ranked match']
    },
    'study': {
      name: '📚 Study & Education',
      kws: [
        'lecture', 'course', 'tutorial', 'algorithm', 'algorithms', 'python', 'neural',
        'calculus', 'linear algebra', 'discrete math', 'operating system', 'data structure',
        'dsa', 'machine learning', 'deep learning', 'artificial intelligence', 'engineering',
        'gate exam', 'exam', 'exams', 'syllabus', 'semester', 'diploma', 'coding', 'fastapi',
        'react js', 'programming', 'computer network', 'dbms', 'sql tutorial', 'mathematics',
        'physics lecture', 'chemistry lecture', 'biology lecture', 'cnn model', 'nlp model',
        'transformer model', 'backpropagation', 'gradient descent', 'freecodecamp', 'neso academy',
        'gate smashers', 'love babbar', 'campusx', 'upsc preparation', 'study with me', 'class 12 physics',
        'neet preparation', 'jee preparation', 'how to code', 'beginner tutorial'
      ]
    },
    'scifi': {
      name: '🚀 Science Fiction & Space',
      kws: ['sci-fi', 'science fiction', 'space', 'astronomy', 'cosmos', 'galaxy', 'nasa', 'interstellar', 'black hole', 'universe', 'relativity', 'quantum', 'mars', 'spacex', 'alien', 'kurzgesagt', 'veritasium', 'james webb']
    },
    'tech': {
      name: '💻 Technology & Software',
      kws: ['technology', 'software', 'developer', 'linux', 'git', 'github', 'docker', 'kubernetes', 'cloud', 'aws', 'cybersecurity', 'hardware', 'cpu', 'gpu', 'backend', 'frontend', 'system design']
    },
    'music': {
      name: '🎵 Music & Songs',
      kws: ['music', 'song', 'official music video', 'lyrics', 'audio song', 'remix', 'lofi beats', 'acoustic', 'concert', 'singer', 'album', 'soundtrack', 'playlist', 'rap song']
    },
    'vlog': {
      name: '💄 Vlog & Daily Life',
      kws: ['daily vlog', 'day in my life', 'travel vlog', 'room tour', 'house tour', 'flying beast', 'sourav joshi', 'family vlog', 'shopping haul', 'morning routine']
    },
    'comedy': {
      name: '😂 Comedy & Pranks',
      kws: ['prank', 'comedy', 'funny', 'stand-up', 'joke', 'roast', 'meme', 'memes', 'try not to laugh', 'cringe', 'funny reaction', 'parody', 'fails']
    },
    'sports': {
      name: '🏏 Sports & Fitness',
      kws: ['cricket', 'football', 'match highlights', 'world cup', 'ipl', 'workout routine', 'gym fitness', 'bodybuilding', 'boxing', 'ufc fight', 'wwe']
    },
    'clickbait': {
      name: '🚨 Clickbait & Distraction',
      kws: ['mrbeast', 'shocking', 'secret hack', 'wealth hack', 'make money fast', 'arrested', 'exposed', '$1 vs', 'blindfolded', 'viral challenge', 'you won\'t believe']
    }
  };

  function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // Pure word-boundary decision algorithm
  function decideLocally(text) {
    const cleanText = text.toLowerCase();
    let bestCat = 'Distraction / Entertainment';
    let bestTag = 'other';
    let maxScore = 0;

    for (const [tag, info] of Object.entries(categoryTaxonomies)) {
      let score = 0;
      for (const kw of info.kws) {
        const pattern = new RegExp('\\b' + escapeRegex(kw.toLowerCase()) + '\\b', 'i');
        if (pattern.test(cleanText)) {
          score += kw.split(' ').length * 2;
        }
      }
      if (score > maxScore) {
        maxScore = score;
        bestCat = info.name;
        bestTag = tag;
      }
    }

    if (!shieldEnabled) {
      return { is_allowed: true, category: bestCat, confidence: 0.99, matched_preference: 'Shield OFF' };
    }

    let isAllowed = false;
    let matchedPref = '';

    if (activeCategories.includes(bestTag)) {
      isAllowed = true;
      matchedPref = bestCat;
    }

    if (!isAllowed) {
      for (const custom of customKeywords) {
        const trimmed = custom.trim();
        if (trimmed) {
          const pattern = new RegExp('\\b' + escapeRegex(trimmed.toLowerCase()) + '\\b', 'i');
          if (pattern.test(cleanText)) {
            isAllowed = true;
            matchedPref = `Custom: ${trimmed}`;
            break;
          }
        }
      }
    }

    return {
      is_allowed: isAllowed,
      category: bestCat,
      confidence: maxScore > 0 ? 0.95 : 0.85,
      matched_preference: matchedPref || 'Blocked'
    };
  }

  // Extract clean metadata from YouTube video or Shorts element
  function extractMetadata(el) {
    let title = '';
    let channel = '';

    // A. YouTube Shorts in Modern Grid/Feed
    const modernShortsTitle = el.querySelector(
      '.shortsLockupViewModelHostOutsideMetadataTitle, h3.shortsLockupViewModelHostMetadataTitle, a.shortsLockupViewModelHostOutsideMetadataEndpoint, .ytShortsVideoTitleViewModelShortsVideoTitle'
    );
    if (modernShortsTitle && modernShortsTitle.textContent.trim()) {
      title = modernShortsTitle.textContent.trim();
    }

    // Fullscreen Shorts player header
    if (!title) {
      const fullscreenTitle = el.querySelector(
        'yt-shorts-video-title-view-model span, ytd-reel-player-header-renderer #title, .reel-player-header-renderer h2, h1.ytShortsVideoTitleViewModelShortsVideoTitle'
      );
      if (fullscreenTitle && fullscreenTitle.textContent.trim()) {
        title = fullscreenTitle.textContent.trim();
      }
    }

    // Anchor title or aria-label attribute
    if (!title) {
      const anchor = el.querySelector('a.shortsLockupViewModelHostEndpoint, a[href*="/shorts/"], a#thumbnail');
      if (anchor) {
        const attrTitle = anchor.getAttribute('title') || anchor.getAttribute('aria-label');
        if (attrTitle && attrTitle.trim()) {
          title = attrTitle.trim();
        }
      }
    }

    // Regular video titles
    if (!title) {
      const regularTitle = el.querySelector(
        '#video-title, #video-title-link, yt-formatted-string#video-title, .yt-lockup-metadata-view-model-wiz__title, h3 a'
      );
      if (regularTitle && regularTitle.textContent.trim()) {
        title = regularTitle.textContent.trim();
      }
    }

    // Fallback for active fullscreen short from document.title
    if (!title && window.location.pathname.startsWith('/shorts')) {
      const docT = document.title;
      if (docT && !docT.toLowerCase().includes('youtube')) {
        title = docT.replace('- YouTube', '').trim();
      }
    }

    if (title) {
      title = title.replace(/\b\d+\s*(hours?|minutes?|seconds?|views?)\b/gi, '').trim();
    }

    const channelEl = el.querySelector(
      '.shortsLockupViewModelHostMetadataSubhead, yt-reel-channel-bar-view-model a, #channel-name, ytd-channel-name, .ytd-channel-name'
    );
    if (channelEl) {
      channel = channelEl.textContent.trim();
    }

    return { title, channel };
  }

  // Get decision with local zero-latency fallback
  function getDecision(title, channel) {
    const key = `${title.toLowerCase()}::${channel.toLowerCase()}`;
    if (decisionCache.has(key)) return Promise.resolve(decisionCache.get(key));

    return new Promise((resolve) => {
      let resolved = false;

      const fallbackTimer = setTimeout(() => {
        if (!resolved) {
          resolved = true;
          const fb = decideLocally(`${title} ${channel}`);
          decisionCache.set(key, fb);
          resolve(fb);
        }
      }, 60);

      try {
        chrome.runtime.sendMessage(
          { action: 'DECIDE', data: { title, channel } },
          (response) => {
            if (!resolved) {
              resolved = true;
              clearTimeout(fallbackTimer);
              if (response && response.success && response.data) {
                decisionCache.set(key, response.data);
                resolve(response.data);
              } else {
                const fb = decideLocally(`${title} ${channel}`);
                decisionCache.set(key, fb);
                resolve(fb);
              }
            }
          }
        );
      } catch (err) {
        if (!resolved) {
          resolved = true;
          clearTimeout(fallbackTimer);
          const fb = decideLocally(`${title} ${channel}`);
          decisionCache.set(key, fb);
          resolve(fb);
        }
      }
    });
  }

  // Evaluate card or YouTube Short
  async function evaluateElement(el) {
    const anchor = el.querySelector('a[href*="/shorts/"]');
    const shortHref = anchor ? anchor.getAttribute('href') : (window.location.pathname.startsWith('/shorts') ? window.location.pathname : '');
    const currentVideoId = shortHref || el.id || '';

    if (el.dataset.studyshieldDone === 'true' && el.dataset.studyshieldId === currentVideoId) {
      return;
    }

    const { title, channel } = extractMetadata(el);
    if (!title || title.length < 2) return;

    el.classList.add('studyshield-card-container');
    const decision = await getDecision(title, channel);
    if (!decision) return;

    el.dataset.studyshieldDone = 'true';
    el.dataset.studyshieldId = currentVideoId;

    const isShort = el.tagName.toLowerCase().includes('reel') || 
                    el.classList.contains('shortsLockupViewModelHost') ||
                    el.classList.contains('ytm-shorts-lockup-view-model') ||
                    el.classList.contains('ytd-rich-grid-slim-media') ||
                    el.classList.contains('ytGridShelfViewModelGridShelfItem') ||
                    el.querySelector('a[href*="/shorts/"]') !== null;

    if (!decision.is_allowed) {
      // 🚫 BLUR THIS VIDEO / SHORT
      el.classList.add('studyshield-blurred');
      el.classList.remove('studyshield-study-verified');

      const existingPill = el.querySelector('.studyshield-study-pill');
      if (existingPill) existingPill.remove();

      const videoTag = el.querySelector('video') || (window.location.pathname.startsWith('/shorts') ? document.querySelector('video') : null);
      if (videoTag && !videoTag.paused && !el.dataset.studyshieldUserRevealed) {
        try {
          videoTag.pause();
          videoTag.muted = true;
        } catch (e) {}
      }

      let overlay = el.querySelector('.studyshield-overlay');
      if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'studyshield-overlay';
        if (isShort) overlay.classList.add('studyshield-overlay-shorts');

        const confPct = Math.round(decision.confidence * 100);
        overlay.innerHTML = `
          <div class="studyshield-badge-header">
            <span>🛡️ StudyShield</span>
          </div>
          <div class="studyshield-badge-sub">
            Blocked ${isShort ? 'Short' : 'Video'}: <strong>${decision.category}</strong> (${confPct}%)
          </div>
          <button class="studyshield-unblur-btn" type="button">👁️ Reveal & Play</button>
        `;

        const unblurBtn = overlay.querySelector('.studyshield-unblur-btn');
        unblurBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          e.preventDefault();
          el.dataset.studyshieldUserRevealed = 'true';
          el.classList.remove('studyshield-blurred');
          overlay.remove();
          if (videoTag) {
            videoTag.muted = false;
            videoTag.play();
          }
        });

        if (isShort && el.querySelector('#short-video-container')) {
          el.querySelector('#short-video-container').appendChild(overlay);
        } else {
          el.appendChild(overlay);
        }

        console.log(`%c🚫 [StudyShield] Blurred ${isShort ? 'Short' : 'Video'}: "${title.substring(0, 38)}..." [${decision.category}]`, 'color: #f87171;');
      }
    } else {
      // ✅ ALLOWED
      el.classList.remove('studyshield-blurred');
      el.classList.add('studyshield-study-verified');

      const existingOverlay = el.querySelector('.studyshield-overlay');
      if (existingOverlay) existingOverlay.remove();

      let pill = el.querySelector('.studyshield-study-pill');
      if (!pill && !isShort) {
        pill = document.createElement('div');
        pill.className = 'studyshield-study-pill';
        pill.innerHTML = `<span>${decision.category}</span>`;
        el.appendChild(pill);
      }
      console.log(`%c✅ [StudyShield] Allowed ${isShort ? 'Short' : 'Video'}: "${title.substring(0, 38)}..." [${decision.category}]`, 'color: #34d399;');
    }
  }

  // Scan all regular videos and Shorts on the page
  function scanAllContent() {
    const selectors = [
      'ytd-rich-item-renderer',
      'ytd-video-renderer',
      'ytd-compact-video-renderer',
      'ytd-grid-video-renderer',
      'ytm-shorts-lockup-view-model',
      'ytm-shorts-lockup-view-model-v2',
      '.ytGridShelfViewModelGridShelfItem',
      'ytd-rich-grid-slim-media',
      'ytd-reel-item-renderer',
      'yt-lockup-view-model',
      'ytd-reel-video-renderer',
      '#shorts-player',
      'ytd-shorts'
    ];

    document.querySelectorAll(selectors.join(',')).forEach(evaluateElement);

    if (window.location.pathname.startsWith('/shorts')) {
      const activeReel = document.querySelector('ytd-reel-video-renderer[is-active]') || document.querySelector('ytd-reel-video-renderer');
      if (activeReel) {
        evaluateElement(activeReel);
      }
    }
  }

  // MutationObserver for live scrolling
  const observer = new MutationObserver(() => {
    scanAllContent();
  });

  observer.observe(document.body, { childList: true, subtree: true });

  window.addEventListener('yt-navigate-finish', () => {
    setTimeout(scanAllContent, 300);
  });
  window.addEventListener('popstate', () => {
    setTimeout(scanAllContent, 300);
  });

  setInterval(scanAllContent, 600);
  scanAllContent();
})();
