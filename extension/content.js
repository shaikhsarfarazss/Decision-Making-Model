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
  let scanDebounceTimer = null;
  const decisionCache = new Map();

  // Clean word-boundary taxonomies (synced with backend LayaDecisionEngine)
  const categoryTaxonomies = {
    study: {
      name: '📚 Study & Education',
      kws: [
        'lecture', 'lectures', 'course', 'crash course', 'full course', 'tutorial',
        'algorithm', 'algorithms', 'python', 'neural', 'calculus', 'linear algebra',
        'discrete math', 'discrete mathematics', 'graph theory', 'operating system',
        'operating systems', 'process scheduling', 'data structure', 'data structures',
        'dsa', 'machine learning', 'deep learning', 'artificial intelligence',
        'reinforcement learning', 'q-learning', 'unsupervised learning', 'k-means',
        'decision tree', 'decision trees', 'entropy', 'information gain', 'svm',
        'kernel trick', 'eigenvalues', 'eigenvectors', 'convolutional', 'cnn', 'cnns',
        'nlp', 'natural language processing', 'hugging face', 'transformer',
        'transformers', 'bert', 'modernbert', 'bidirectional', 'attention',
        'backpropagation', 'gradient descent', 'engineering', 'gate', 'gate exam', 'cracked gate',
        'gate preparation', 'gate smashers', 'iit', 'iit bombay', 'exam', 'exams',
        'syllabus', 'semester', 'diploma', 'coding', 'fastapi', 'rest api',
        'django', 'react', 'react js', 'programming', 'oop', 'java', 'c++',
        'c programming', 'computer network', 'computer networks', 'osi model',
        'tcp/ip', 'dbms', 'database management', 'sql', 'mathematics', 'physics',
        'chemistry', 'biology', 'digital electronics', 'logic gates', 'k-maps',
        'boolean algebra', 'pipeline hazards', 'architecture', 'freecodecamp',
        'neso academy', 'gate smashers', 'love babbar', 'campusx', 'statquest',
        '3blue1brown', 'mit opencourseware', 'krish naik', 'andrej karpathy',
        'yannic kilcher', 'deeplizard', 'traversy media', 'apna college', 'telusko',
        'sentdex', 'fireship', 'upsc', 'study with me', 'class 12', 'neet', 'jee',
        'how to code', 'for beginners', 'for students', 'roadmap'
      ]
    },
    tech: {
      name: '💻 Technology & Software',
      kws: [
        'technology', 'software', 'developer', 'linux', 'git', 'github', 'devops',
        'docker', 'kubernetes', 'cloud', 'aws', 'cybersecurity', 'hardware', 'cpu',
        'gpu', 'backend', 'frontend', 'system design', 'nvidia'
      ]
    },
    scifi: {
      name: '🚀 Science Fiction & Space',
      kws: [
        'sci-fi', 'science fiction', 'space', 'astronomy', 'astrophysics', 'cosmos',
        'galaxy', 'nasa', 'interstellar', 'black hole', 'universe', 'relativity',
        'quantum', 'mars', 'spacex', 'alien', 'kurzgesagt', 'veritasium', 'james webb',
        'cyberpunk', 'multiverse'
      ]
    },
    cooking: {
      name: '🍲 Cooking & Food',
      kws: [
        'recipe', 'cooking', 'cook', 'food', 'street food', 'kitchen', 'chef',
        'burger', 'pizza', 'biryani', 'cake', 'baking', 'eating', 'mukbang',
        'dessert', 'taste test', 'spicy wings'
      ]
    },
    cartoon: {
      name: '🎨 Cartoon & Animation',
      kws: [
        'cartoon', 'animated', 'animation', 'tom and jerry', 'disney', 'pixar',
        'ben 10', 'shinchan', 'doraemon', 'oggy', 'chhota bheem', 'peppa pig',
        'mr bean', 'looney tunes'
      ]
    },
    anime: {
      name: '⚔️ Anime & Manga',
      kws: [
        'anime', 'manga', 'naruto', 'shippuden', 'sasuke', 'itachi', 'madara',
        'one piece', 'luffy', 'zoro', 'sanji', 'bleach', 'ichigo', 'aizen', 'tybw',
        'attack on titan', 'aot', 'eren', 'levi', 'mikasa', 'jujutsu kaisen', 'jjk',
        'gojo', 'sukuna', 'megumi', 'demon slayer', 'kimetsu', 'tanjiro', 'nezuko',
        'dragon ball', 'dragon ball z', 'dragon ball super', 'dbz', 'dbs', 'goku',
        'super saiyan', 'saiyan', 'ssj', 'bardock', 'vegeta', 'gohan', 'broly', 'frieza',
        'piccolo', 'trunks', 'studio ghibli', 'ghibli', 'solo leveling', 'chainsaw man',
        'death note', 'vinland saga', 'my hero academia', 'deku', 'one punch man',
        'saitama', 'hunter x hunter', 'hxh', 'killua', 'tokyo ghoul', 'sword art online',
        'fullmetal alchemist', 'berserk', 'evangelion', 'jojo', 'crunchyroll',
        'funimation', 'opening ost', 'amv', 'anime edit', 'anime scene', 'anime clip'
      ]
    },
    gaming: {
      name: '🎮 Gaming & Esports',
      kws: [
        'game', 'gameplay', 'gaming', 'minecraft', 'gta', 'valorant', 'fortnite',
        'pubg', 'bgmi', 'roblox', 'call of duty', 'elden ring', 'walkthrough',
        'playthrough', 'stream', 'twitch', 'esports', 'boss fight', 'hardest boss',
        'clutch', '1v5', 'ace', 'ranked', 'ranked match'
      ]
    },
    music: {
      name: '🎵 Music & Songs',
      kws: [
        'music', 'song', 'official music video', 'lyrics', 'audio song', 'remix',
        'lofi', 'lofi beats', 'acoustic', 'concert', 'singer', 'album', 'soundtrack',
        'playlist', 'rap song'
      ]
    },
    vlog: {
      name: '💄 Vlog & Daily Life',
      kws: [
        'vlog', 'daily vlog', 'day in my life', 'travel vlog', 'room tour',
        'house tour', 'flying beast', 'sourav joshi', 'family vlog', 'shopping haul',
        'morning routine', 'minimalist setup'
      ]
    },
    comedy: {
      name: '😂 Comedy & Pranks',
      kws: [
        'prank', 'prank calling', 'comedy', 'funny', 'funniest', 'stand-up', 'joke',
        'roast', 'meme', 'memes', 'try not to laugh', 'cringe', 'cringiest',
        'funny reaction', 'parody', 'fails', 'samay raina'
      ]
    },
    sports: {
      name: '🏏 Sports & Fitness',
      kws: [
        'cricket', 'football', 'match highlights', 'world cup', 'super over', 'ipl',
        'workout', 'gym fitness', 'bodybuilding', 'boxing', 'ufc', 'wwe'
      ]
    },
    clickbait: {
      name: '🚨 Sensational & Clickbait',
      kws: [
        'mrbeast', 'shocking', 'secret hack', 'wealth hack', 'make money fast',
        'get rich', 'arrested', 'exposed', '$1 vs', 'blindfolded', 'buying everything',
        'viral challenge', "you won't believe", 'conspiracy theories', 'abandoned island',
        'red carpet', 'hollywood', 'bollywood'
      ]
    }
  };

  function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

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
          if (
            tag === 'study' &&
            ['crash course', 'full course', 'lecture', 'tutorial', 'for students', 'for beginners'].includes(kw)
          ) {
            score += 3;
          }
        }
      }
      if (score > maxScore) {
        maxScore = score;
        bestCat = info.name;
        bestTag = tag;
      }
    }

    if (!shieldEnabled) {
      return {
        is_allowed: true,
        category: bestCat,
        confidence: 0.99,
        matched_preference: 'Shield OFF'
      };
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
      confidence: maxScore > 0 ? 0.96 : 0.85,
      matched_preference: matchedPref || 'Blocked'
    };
  }

  function showToast(message) {
    if (!document.body) return;
    let toast = document.getElementById('studyshield-live-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'studyshield-live-toast';
      toast.className = 'studyshield-toast';
      document.body.appendChild(toast);
    }
    const catList = shieldEnabled
      ? activeCategories.map((c) => c.charAt(0).toUpperCase() + c.slice(1)).join(', ')
      : 'All Videos (Shield Paused)';
    toast.innerHTML = `
      <div class="studyshield-toast-content">
        <span class="studyshield-toast-icon">🛡️</span>
        <div>
          <div class="studyshield-toast-title">StudyShield: ${message}</div>
          <div class="studyshield-toast-sub">Allowed: <strong>${catList || 'None (All Blurred)'}</strong></div>
        </div>
      </div>
    `;
    toast.classList.add('studyshield-toast-show');
    clearTimeout(toast._hideTimer);
    toast._hideTimer = setTimeout(() => {
      toast.classList.remove('studyshield-toast-show');
    }, 2600);
  }

  function triggerImmediateReScan(reason = 'Preferences Updated', showNotification = true) {
    decisionCache.clear();
    document.querySelectorAll('.studyshield-card-container, .studyshield-thumb-container, [data-studyshield-done]').forEach((el) => {
      delete el.dataset.studyshieldDone;
      delete el.dataset.studyshieldSignature;
      delete el.dataset.studyshieldUserRevealed;
      el.classList.remove('studyshield-thumb-blurred', 'studyshield-thumb-verified', 'studyshield-blurred', 'studyshield-study-verified');
      const o = el.querySelector('.studyshield-overlay');
      if (o) o.remove();
      const p = el.querySelector('.studyshield-study-pill');
      if (p) p.remove();
    });
    scanAllContent();
    if (showNotification) showToast(reason);
  }

  // Load initial preferences from chrome.storage.local and immediately re-scan
  try {
    chrome.storage.local.get(
      ['shieldEnabled', 'activeCategories', 'customKeywords', 'updated_at'],
      (res) => {
        if (! res) return;
        if (res.shieldEnabled !== undefined) shieldEnabled = res.shieldEnabled;
        if (Array.isArray(res.activeCategories)) activeCategories = res.activeCategories;
        if (Array.isArray(res.customKeywords)) customKeywords = res.customKeywords;
        if (res.updated_at) lastUpdatedAt = res.updated_at;
        triggerImmediateReScan('Initialized', false);
      }
    );
  } catch (_) {}

  // Listen to storage updates
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
  } catch (_) {}

  // Direct message listener from Popup or Background
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
  } catch (_) {}

  // Support window postMessage for local test_youtube_mock.html
  window.addEventListener('message', (event) => {
    if (event.data && event.data.action === 'PREFERENCES_UPDATED') {
      const d = event.data.data;
      if (d) {
        if (d.shield_enabled !== undefined) shieldEnabled = d.shield_enabled;
        if (d.shieldEnabled !== undefined) shieldEnabled = d.shieldEnabled;
        if (d.active_categories) activeCategories = d.active_categories;
        if (d.activeCategories) activeCategories = d.activeCategories;
        if (d.custom_keywords) customKeywords = d.custom_keywords;
        if (d.customKeywords) customKeywords = d.customKeywords;
      }
      triggerImmediateReScan('Preferences Saved & Applied');
    }
  });

  function syncPreferences() {
    try {
      chrome.runtime.sendMessage({ action: 'GET_PREFERENCES' }, (response) => {
        if (chrome.runtime.lastError) return;
        if (response && response.success && response.data) {
          const d = response.data;
          const serverUpdated = d.updated_at || 0;
          const categoriesMatch =
            JSON.stringify(activeCategories) === JSON.stringify(d.active_categories);
          const shieldMatch =
            shieldEnabled === (d.shield_enabled !== undefined ? d.shield_enabled : true);
          const kwMatch =
            JSON.stringify(customKeywords) === JSON.stringify(d.custom_keywords || []);

          if (!categoriesMatch || !shieldMatch || !kwMatch || serverUpdated > lastUpdatedAt + 0.5) {
            shieldEnabled = d.shield_enabled !== undefined ? d.shield_enabled : true;
            activeCategories = d.active_categories || ['study'];
            customKeywords = d.custom_keywords || [];
            lastUpdatedAt = serverUpdated;

            chrome.storage.local.set({
              shieldEnabled,
              activeCategories,
              customKeywords,
              updated_at: lastUpdatedAt
            });
            triggerImmediateReScan('Synced with Local Server');
          }
        }
      });
    } catch (_) {}
  }

  syncPreferences();
  setInterval(syncPreferences, 2000);

  function extractMetadata(el) {
    let title = '';
    let channel = '';

    const modernShortsTitle = el.querySelector(
      '.shortsLockupViewModelHostOutsideMetadataTitle, h3.shortsLockupViewModelHostMetadataTitle, a.shortsLockupViewModelHostOutsideMetadataEndpoint, .ytShortsVideoTitleViewModelShortsVideoTitle'
    );
    if (modernShortsTitle && modernShortsTitle.textContent.trim()) {
      title = modernShortsTitle.textContent.trim();
    }

    if (!title) {
      const fullscreenTitle = el.querySelector(
        'yt-shorts-video-title-view-model span, ytd-reel-player-header-renderer #title, .reel-player-header-renderer h2, h1.ytShortsVideoTitleViewModelShortsVideoTitle'
      );
      if (fullscreenTitle && fullscreenTitle.textContent.trim()) {
        title = fullscreenTitle.textContent.trim();
      }
    }

    if (!title) {
      const regularTitle = el.querySelector(
        '#video-title, #video-title-link, yt-formatted-string#video-title, .yt-lockup-metadata-view-model-wiz__title, .yt-lockup-metadata-view-model__title, h3 a'
      );
      if (regularTitle && regularTitle.textContent.trim()) {
        title = regularTitle.textContent.trim();
      }
    }

    if (!title) {
      const anchor = el.querySelector(
        'a#video-title-link, a.shortsLockupViewModelHostEndpoint, a[href*="/shorts/"], a[href*="/watch?v="], a#thumbnail'
      );
      if (anchor) {
        const attrTitle = anchor.getAttribute('title') || anchor.getAttribute('aria-label');
        if (attrTitle && attrTitle.trim()) {
          title = attrTitle.trim();
        }
      }
    }

    if (!title && window.location.pathname.startsWith('/shorts') && el.hasAttribute('is-active')) {
      const docT = document.title;
      if (docT && docT.toLowerCase() !== 'youtube') {
        title = docT.replace(/- YouTube$/i, '').trim();
      }
    }

    if (title) {
      title = title.replace(/\b\d+\s*(hours?|minutes?|seconds?|views?)\b/gi, '').trim();
    }

    const channelEl = el.querySelector(
      '.shortsLockupViewModelHostMetadataSubhead, yt-reel-channel-bar-view-model a, #channel-name, ytd-channel-name, .ytd-channel-name'
    );
    if (channelEl) {
      channel = channelEl.textContent.trim().split('\n')[0].trim();
    }

    const linkEl = el.querySelector('a[href*="/watch?v="], a[href*="/shorts/"]');
    const href = linkEl ? linkEl.getAttribute('href') : '';

    return { title, channel, href };
  }

  function getDecision(title, channel) {
    const key = `${title.toLowerCase()}::${channel.toLowerCase()}::${shieldEnabled}::${activeCategories.join(',')}`;
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
      }, 220);

      try {
        chrome.runtime.sendMessage(
          { action: 'DECIDE', data: { title, channel } },
          (response) => {
            if (resolved) return;
            resolved = true;
            clearTimeout(fallbackTimer);
            if (!chrome.runtime.lastError && response && response.success && response.data) {
              decisionCache.set(key, response.data);
              resolve(response.data);
            } else {
              const fb = decideLocally(`${title} ${channel}`);
              decisionCache.set(key, fb);
              resolve(fb);
            }
          }
        );
      } catch (_) {
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

  function getThumbnailContainer(el) {
    // 1. YouTube standard video cards
    const ytdThumb = el.querySelector('ytd-thumbnail, #thumbnail, a#thumbnail');
    if (ytdThumb) return ytdThumb;

    // 2. Mock test page thumbnail box
    const thumbBox = el.querySelector('.thumb-box');
    if (thumbBox) return thumbBox;

    // 3. YouTube Shorts shelf items
    const shortsThumb = el.querySelector(
      '.shortsLockupViewModelHostThumbnailContainer, .shortsLockupViewModelHostOutsideMetadataEndpoint'
    );
    if (shortsThumb) return shortsThumb;

    // 4. Modern lockup view model
    const lockupImg = el.querySelector(
      '.yt-lockup-view-model__content-image, .yt-lockup-metadata-view-model-wiz__thumbnail-container'
    );
    if (lockupImg) return lockupImg;

    // 5. Fullscreen Shorts player container
    const reelContainer = el.querySelector('#short-video-container, #player-container');
    if (reelContainer) return reelContainer;

    return el;
  }

  async function evaluateElement(el) {
    const { title, channel, href } = extractMetadata(el);
    if (!title || title.length < 2) return;

    // Signature prevents stale overlays when YouTube recycles card DOM elements
    const signature = `${href}::${title}`;
    if (el.dataset.studyshieldDone === 'true' && el.dataset.studyshieldSignature === signature) {
      return;
    }

    // If YouTube recycled this DOM element for a different video, clear manual reveal flag
    if (el.dataset.studyshieldSignature && el.dataset.studyshieldSignature !== signature) {
      delete el.dataset.studyshieldUserRevealed;
    }

    el.classList.add('studyshield-card-container');
    const decision = await getDecision(title, channel);
    if (!decision) return;

    el.dataset.studyshieldDone = 'true';
    el.dataset.studyshieldSignature = signature;

    const thumbEl = getThumbnailContainer(el);
    thumbEl.classList.add('studyshield-thumb-container');

    const isShort =
      el.tagName.toLowerCase().includes('reel') ||
      el.classList.contains('shortsLockupViewModelHost') ||
      el.classList.contains('ytm-shorts-lockup-view-model') ||
      el.classList.contains('ytd-rich-grid-slim-media') ||
      el.classList.contains('ytGridShelfViewModelGridShelfItem') ||
      el.querySelector('a[href*="/shorts/"]') !== null;

    if (!decision.is_allowed && !el.dataset.studyshieldUserRevealed) {
      // 🚫 BLUR ONLY THE VIDEO / THUMBNAIL CONTAINER
      // The bottom written text (title, channel, views, description) remains 100% UNTOUCHED and VISIBLE!
      thumbEl.classList.add('studyshield-thumb-blurred');
      thumbEl.classList.remove('studyshield-thumb-verified');
      el.classList.remove('studyshield-study-verified');

      const existingPill = thumbEl.querySelector('.studyshield-study-pill') || el.querySelector('.studyshield-study-pill');
      if (existingPill) existingPill.remove();

      // Only pause video if it is inside THIS element (or this element is the active Short)
      const isActiveReel = el.hasAttribute('is-active') || el.id === 'shorts-player';
      const videoTag =
        el.querySelector('video') ||
        (window.location.pathname.startsWith('/shorts') && isActiveReel
          ? document.querySelector('ytd-reel-video-renderer[is-active] video')
          : null);

      if (videoTag && !videoTag.paused) {
        try {
          videoTag.pause();
          videoTag.muted = true;
        } catch (_) {}
      }

      let overlay = thumbEl.querySelector('.studyshield-overlay');
      if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'studyshield-overlay';
        if (isShort) overlay.classList.add('studyshield-overlay-shorts');
        const targetContainer = (isShort && el.querySelector('#short-video-container')) || thumbEl;
        targetContainer.appendChild(overlay);
      }

      const confPct = Math.round((decision.confidence || 0.95) * 100);
      overlay.innerHTML = `
        <div class="studyshield-badge-header">
          <span>🛡️ StudyShield</span>
        </div>
        <div class="studyshield-badge-sub">
          Blocked: <strong>${decision.category}</strong> (${confPct}%)
        </div>
        <button class="studyshield-unblur-btn" type="button">👁️ Reveal & Play</button>
      `;

      const unblurBtn = overlay.querySelector('.studyshield-unblur-btn');
      unblurBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        e.preventDefault();
        el.dataset.studyshieldUserRevealed = 'true';
        thumbEl.classList.remove('studyshield-thumb-blurred');
        overlay.remove();
        if (videoTag) {
          videoTag.muted = false;
          videoTag.play().catch(() => {});
        }
      });
    } else {
      // ✅ ALLOWED VIDEO
      thumbEl.classList.remove('studyshield-thumb-blurred');
      thumbEl.classList.add('studyshield-thumb-verified');
      el.classList.add('studyshield-study-verified');

      const existingOverlay = thumbEl.querySelector('.studyshield-overlay') || el.querySelector('.studyshield-overlay');
      if (existingOverlay) existingOverlay.remove();

      if (!isShort) {
        let pill = thumbEl.querySelector('.studyshield-study-pill');
        if (!pill) {
          pill = document.createElement('div');
          pill.className = 'studyshield-study-pill';
          thumbEl.appendChild(pill);
        }
        pill.innerHTML = `<span>✓ ${decision.category}</span>`;
      }
    }
  }

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
      'ytd-reel-video-renderer'
    ];
    document.querySelectorAll(selectors.join(',')).forEach(evaluateElement);
  }

  function scheduleScan() {
    if (scanDebounceTimer) return;
    scanDebounceTimer = setTimeout(() => {
      scanDebounceTimer = null;
      scanAllContent();
    }, 120);
  }

  const observer = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (
        m.target &&
        m.target.classList &&
        (m.target.classList.contains('studyshield-overlay') ||
          m.target.classList.contains('studyshield-study-pill') ||
          m.target.id === 'studyshield-live-toast')
      ) {
        continue;
      }
      scheduleScan();
      break;
    }
  });

  if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
  }

  window.addEventListener('yt-navigate-finish', () => setTimeout(scanAllContent, 250));
  window.addEventListener('popstate', () => setTimeout(scanAllContent, 250));
  setInterval(scanAllContent, 1500);
  scanAllContent();
})();
