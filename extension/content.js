// StudyShield Content Script — 3-Layer YouTube Categorization Engine (20 Categories)
(() => {
  console.log(
    '%c[StudyShield 🛡️] 3-Layer YouTube Classifier Active (20 Categories: Study & Coding Separated)',
    'color: #38bdf8; font-size: 13px; font-weight: bold; background: #0f172a; padding: 4px 8px; border-radius: 4px;'
  );

  let shieldEnabled = true;
  let activeCategories = ['study', 'coding'];
  let customKeywords = [];
  let lastUpdatedAt = 0;
  let scanDebounceTimer = null;
  const decisionCache = new Map();

  // 20 YouTube-Aligned Categories with Official YouTube Category IDs & Channel Priors
  const categoryTaxonomies = {
    study: {
      name: '📚 Study & Academics',
      ytId: '27',
      ytMacro: 'Education',
      channels: [
        'mit opencourseware', '3blue1brown', 'statquest', 'neso academy', 'gate smashers',
        'knowledge gate', 'engineering lectures', 'physics wallah', 'unacademy', 'khan academy',
        'nptel', 'organic chemistry tutor'
      ],
      kws: [
        'lecture', 'lectures', 'calculus', 'linear algebra', 'discrete math', 'discrete mathematics',
        'graph theory', 'eigenvalues', 'eigenvectors', 'vector fields', 'multiple integrals',
        'differential equations', 'probability', 'statistics', 'engineering', 'gate exam', 'gate',
        'cracked gate', 'gate preparation', 'iit', 'iit bombay', 'exam', 'exams', 'university exams',
        'syllabus', 'semester', '5th sem', 'diploma', 'unit 1', 'unit 2', 'unit 3', 'physics',
        'chemistry', 'biology', 'thermodynamics', 'electromagnetism', 'organic chemistry',
        'digital electronics', 'logic gates', 'k-maps', 'boolean algebra', 'computer organization',
        'pipeline hazards', 'operating system', 'operating systems', 'process scheduling', 'fcfs',
        'round robin', 'computer network', 'computer networks', 'osi model', 'tcp/ip', 'dbms',
        'database management', 'history', 'geography', 'polity', 'notes', 'upsc', 'ncert',
        'study with me', 'class 10', 'class 11', 'class 12', 'neet', 'jee',
        'explained mathematically', 'mathematical intuition'
      ]
    },
    coding: {
      name: '💻 Coding & Dev',
      ytId: '28',
      ytMacro: 'Science & Technology',
      channels: [
        'freecodecamp', 'programming with mosh', 'traversy media', 'fireship', 'love babbar',
        'apna college', 'telusko', 'codewithharry', 'krish naik', 'campusx', 'andrej karpathy',
        'yannic kilcher', 'deeplizard', 'sentdex', "jenny's lectures", 'striver', 'neetcode',
        'chaiaurcode'
      ],
      kws: [
        'coding', 'programming', 'how to code', 'python', 'java', 'c++', 'c programming',
        'javascript', 'typescript', 'rust', 'golang', 'html', 'css', 'tailwind', 'react',
        'react js', 'nextjs', 'nodejs', 'django', 'flask', 'fastapi', 'spring boot',
        'rest api', 'rest apis', 'full stack', 'web development', 'frontend', 'backend',
        'data structure', 'data structures', 'dsa', 'algorithm', 'algorithms', 'leetcode',
        'codeforces', 'competitive programming', 'object oriented', 'oop', 'sql', 'postgresql',
        'mongodb', 'git', 'github', 'docker', 'kubernetes', 'devops', 'system design',
        'machine learning', 'deep learning', 'artificial intelligence', 'ai & ml', 'neural',
        'neural network', 'neural networks', 'reinforcement learning', 'q-learning',
        'unsupervised learning', 'k-means', 'clustering', 'decision tree', 'decision trees',
        'entropy', 'information gain', 'support vector', 'svm', 'kernel trick', 'convolutional',
        'cnn', 'cnns', 'nlp', 'natural language processing', 'hugging face', 'transformer',
        'transformers', 'bert', 'modernbert', 'bidirectional', 'attention', 'backpropagation',
        'gradient descent', 'pytorch', 'tensorflow', 'llm', 'from scratch', 'complete roadmap'
      ]
    },
    tech: {
      name: '🔧 Tech & Gadgets',
      ytId: '28',
      ytMacro: 'Science & Technology',
      channels: [
        'marques brownlee', 'mkbhd', 'linus tech tips', 'dave2d', 'mrwhosetheboss',
        'technical guruji', 'trakintech', 'geekyranjit', 'networkchuck'
      ],
      kws: [
        'technology', 'tech review', 'smartphone', 'iphone', 'android', 'samsung', 'laptop',
        'macbook', 'pc build', 'hardware', 'cpu', 'gpu', 'rtx', 'nvidia', 'amd', 'intel',
        'linux', 'ubuntu', 'windows 11', 'cloud computing', 'aws', 'cybersecurity',
        'ethical hacking', 'raspberry pi', 'arduino', 'robotics', 'unboxing', 'first look'
      ]
    },
    scifi: {
      name: '🚀 Science & Space',
      ytId: '28',
      ytMacro: 'Science & Technology',
      channels: [
        'kurzgesagt', 'veritasium', 'vsauce', 'smartereveryday', 'pbs space time',
        'nasa', 'isro', 'spacex', 'mark rober', 'star talk'
      ],
      kws: [
        'sci-fi', 'science fiction', 'space', 'astronomy', 'astrophysics', 'cosmos', 'galaxy',
        'nasa', 'isro', 'interstellar', 'black hole', 'wormhole', 'universe', 'multiverse',
        'relativity', 'quantum', 'dark matter', 'mars', 'spacex', 'starship', 'alien',
        'kurzgesagt', 'veritasium', 'james webb', 'telescope', 'time travel', 'cyberpunk', 'dune'
      ]
    },
    news: {
      name: '📰 News & Politics',
      ytId: '25',
      ytMacro: 'News & Politics',
      channels: ['wion', 'firstpost', 'ndtv', 'india today', 'bbc news', 'al jazeera', 'reuters', 'dw news'],
      kws: [
        'breaking news', 'world news', 'geopolitics', 'politics', 'election', 'parliament',
        'supreme court', 'foreign policy', 'current affairs', 'journalism', 'press conference',
        'headline', 'war update'
      ]
    },
    finance: {
      name: '📈 Finance & Business',
      ytId: '27',
      ytMacro: 'Education',
      channels: ['zerodha', 'pranjal kamra', 'akshat shrivastava', 'ca rachana ranade', 'warikoo', 'think school'],
      kws: [
        'finance', 'personal finance', 'investing', 'stock market', 'share market', 'nifty',
        'sensex', 'mutual funds', 'sip', 'options trading', 'portfolio', 'business',
        'startup', 'entrepreneurship', 'shark tank', 'ipo', 'marketing strategy', 'economics',
        'inflation', 'gdp', 'real estate', 'income tax'
      ]
    },
    howto: {
      name: '🛠️ How-To & DIY',
      ytId: '26',
      ytMacro: 'Howto & Style',
      channels: ['ali abdaal', 'thomas frank', 'jerryrigeverything', 'ifixit', 'chris fix', 'electroboom'],
      kws: [
        'how to', 'diy', 'step by step', 'woodworking', 'home improvement', 'repair',
        'restoration', '3d printing', 'productivity', 'time management', 'notion', 'obsidian',
        'communication skills', 'public speaking', 'resume', 'interview preparation',
        'graphic design', 'photoshop', 'figma', 'video editing', 'blender tutorial'
      ]
    },
    podcast: {
      name: '🎙️ Podcasts & Talks',
      ytId: '22',
      ytMacro: 'People & Blogs',
      channels: ['lex fridman', 'ted', 'tedx', 'huberman lab', 'diary of a ceo', 'joe rogan', 'trs', 'raj shamani'],
      kws: [
        'podcast', 'full episode', 'ted talk', 'tedx', 'lex fridman', 'huberman',
        'fireside chat', 'panel discussion', 'roundtable', 'documentary', 'full documentary',
        'biopic', 'untold story'
      ]
    },
    cooking: {
      name: '🍲 Cooking & Food',
      ytId: '26',
      ytMacro: 'Howto & Style',
      channels: ['ranveer brar', 'your food lab', "kabita's kitchen", 'gordon ramsay', 'nick digiovanni', 'first we feast'],
      kws: [
        'recipe', 'cooking', 'cook', 'food', 'street food', 'kitchen', 'chef', 'masterchef',
        'burger', 'pizza', 'pasta', 'biryani', 'paneer', 'cake', 'baking', 'eating', 'mukbang',
        'spicy wings', 'dessert', 'taste test', 'breakfast recipe', 'dinner recipe', 'restaurant'
      ]
    },
    autos: {
      name: '🚗 Autos & Vehicles',
      ytId: '2',
      ytMacro: 'Autos & Vehicles',
      channels: ['carwow', 'doug demuro', 'top gear', 'autocar india', 'motoroctane', 'faisal khan', 'powerdrift'],
      kws: [
        'car review', 'supercar', 'hypercar', 'suv', 'electric vehicle', 'tesla', 'ferrari',
        'lamborghini', 'porsche', 'bmw', 'motorcycle', 'superbike', 'bike review', 'offroad',
        'drag race', 'formula 1', 'f1', 'motogp', 'horsepower', 'automotive'
      ]
    },
    pets: {
      name: '🐾 Pets & Nature',
      ytId: '15',
      ytMacro: 'Pets & Animals',
      channels: ['national geographic', 'bbc earth', 'animal planet', 'the dodo', 'brave wilderness'],
      kws: [
        'wildlife', 'wild animals', 'national geographic', 'bbc earth', 'nature documentary',
        'animal rescue', 'puppy', 'puppies', 'dogs', 'kittens', 'cats', 'cute pets',
        'aquarium', 'sharks', 'lions', 'tigers', 'birds', 'jungle', 'safari'
      ]
    },
    travel: {
      name: '✈️ Travel & Culture',
      ytId: '19',
      ytMacro: 'Travel & Events',
      channels: ['drew binsky', 'kara and nate', 'bald and bankrupt', 'yes theory', 'sam chui', 'monkey magic'],
      kws: [
        'travel', 'travel guide', 'solo travel', 'backpacking', 'world tour', 'road trip',
        'tourist places', 'flight review', 'aviation', 'airport', 'hotel review', 'tourism',
        'mountain trekking', 'himalayas'
      ]
    },
    music: {
      name: '🎵 Music & Lofi',
      ytId: '10',
      ytMacro: 'Music',
      channels: ['lofi girl', 't-series', 'sony music', 'coke studio', 'vevo', 'ncs'],
      kws: [
        'music', 'song', 'official music video', 'official video', 'lyrics', 'audio song',
        'remix', 'mashup', 'lofi', 'lofi beats', 'chill beats', 'acoustic', 'concert',
        'singer', 'album', 'soundtrack', 'playlist', 'rap song', 'hip hop', 'instrumental',
        'cover song'
      ]
    },
    sports: {
      name: '🏏 Sports & Fitness',
      ytId: '17',
      ytMacro: 'Sports',
      channels: ['icc', 'icc official', 'bcci', 'star sports', 'espn', 'fifa', 'nba', 'ufc', 'wwe', 'athlean-x'],
      kws: [
        'cricket', 'ipl', 'world cup', 'super over', 'virat kohli', 'rohit sharma', 'ms dhoni',
        'football', 'premier league', 'champions league', 'messi', 'ronaldo', 'match highlights',
        'olympics', 'tennis', 'badminton', 'nba', 'workout', 'workout routine', 'gym',
        'gym fitness', 'bodybuilding', 'calisthenics', 'boxing', 'ufc', 'wwe'
      ]
    },
    anime: {
      name: '⚔️ Anime & Manga',
      ytId: '31',
      ytMacro: 'Anime/Animation',
      channels: ['crunchyroll', 'muse asia', 'ani-one asia', 'toei animation', 'mappa', 'animezone'],
      kws: [
        'anime', 'manga', 'otaku', 'naruto', 'shippuden', 'sasuke', 'itachi', 'one piece',
        'luffy', 'zoro', 'bleach', 'attack on titan', 'aot', 'jujutsu kaisen', 'jjk', 'gojo',
        'sukuna', 'demon slayer', 'tanjiro', 'dragon ball', 'dragon ball z', 'dragon ball super',
        'dbz', 'dbs', 'goku', 'vegeta', 'super saiyan', 'saiyan', 'ssj', 'bardock', 'gohan',
        'broly', 'frieza', 'piccolo', 'trunks', 'studio ghibli', 'ghibli', 'solo leveling',
        'sung jinwoo', 'chainsaw man', 'death note', 'vinland saga', 'my hero academia',
        'blue lock', 'one punch man', 'saitama', 'hunter x hunter', 'amv', 'anime scene', 'anime clip'
      ]
    },
    cartoon: {
      name: '🎨 Cartoon & Animation',
      ytId: '1',
      ytMacro: 'Film & Animation',
      channels: ['disney', 'pixar', 'cartoon network', 'nickelodeon', 'wb kids', 'alan becker'],
      kws: [
        'cartoon', 'cartoons', 'animated', 'animation', 'tom and jerry', 'disney', 'pixar',
        'ben 10', 'shinchan', 'doraemon', 'oggy', 'chhota bheem', 'motu patlu', 'peppa pig',
        'mr bean', 'looney tunes', 'spongebob', 'kids show'
      ]
    },
    gaming: {
      name: '🎮 Gaming & Esports',
      ytId: '20',
      ytMacro: 'Gaming',
      channels: [
        'dream', 'luke thenotable', 'tenz', 'total gaming', 'techno gamerz', 'mortal',
        'beastboyshub', 'ign', 'vaatividya'
      ],
      kws: [
        'game', 'gameplay', 'gaming', 'playthrough', 'walkthrough', 'speedrun', 'minecraft',
        'gta', 'gta 6', 'valorant', '1v5', 'clutch', 'fortnite', 'pubg', 'bgmi', 'free fire',
        'roblox', 'call of duty', 'warzone', 'cs2', 'apex legends', 'elden ring', 'dark souls',
        'god of war', 'esports', 'stream', 'twitch', 'boss fight', 'hardest boss', 'no armor',
        'ranked', 'ranked match', '50 kills', 'radiant ace'
      ]
    },
    vlog: {
      name: '💄 Vlogs & Lifestyle',
      ytId: '22',
      ytMacro: 'People & Blogs',
      channels: ['sourav joshi vlogs', 'flying beast', 'mumbiker nikhil', 'casey neistat', 'techvlogger'],
      kws: [
        'vlog', 'daily vlog', 'day in my life', 'travel vlog', 'room tour', 'house tour',
        'minimalist setup', 'flying beast', 'sourav joshi', 'family vlog', 'shopping haul',
        'skincare routine', 'grwm', 'morning routine', 'night routine', 'lifestyle'
      ]
    },
    comedy: {
      name: '😂 Comedy & Memes',
      ytId: '23',
      ytMacro: 'Comedy',
      channels: [
        'samay raina', 'zakir khan', 'anubhav singh bassi', 'bb ki vines', 'ashish chanchlani',
        'carryminati', 'round2hell', 'tanmay bhat', 'nelk', 'animalmemes'
      ],
      kws: [
        'prank', 'prank calling', 'comedy', 'stand-up', 'stand up comedy', 'funny', 'funniest',
        'joke', 'roast', 'meme', 'memes', 'try not to laugh', 'cringe', 'cringiest',
        'funny reaction', 'reacting to', 'parody', 'skit', 'fails', 'samay raina', 'zakir khan'
      ]
    },
    clickbait: {
      name: '🚨 Clickbait & Drama',
      ytId: '24',
      ytMacro: 'Entertainment',
      channels: ['mrbeast', 'dhar mann', 'airrack', 'fukra insaan', 'buzzfeed', 'gossipcentral', 'viraldrama', 'getrichfast', 'cryptoguru', 'hypetech', 'mysteryfiles'],
      kws: [
        'mrbeast', 'shocking', 'secret hack', 'wealth hack', 'make money fast', 'get rich',
        'zero effort', 'arrested', 'exposed', '$1 vs', '$1,000,000', 'blindfolded',
        'buying everything', '24 hours', '7 days straight', 'viral challenge',
        "you won't believe", 'you wont believe', 'must watch', 'billionaire', 'crypto',
        'conspiracy theories', 'abandoned island', 'destroyed android', 'red carpet',
        'unseen moments', 'hollywood', 'bollywood', 'celebrity'
      ]
    }
  };

  function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function decideLocally(title, channel = '') {
    const titleLower = (title || '').toLowerCase();
    const channelLower = (channel || '').toLowerCase();
    const cleanText = `${titleLower} ${channelLower}`.trim();

    const scores = {};
    for (const [tag, info] of Object.entries(categoryTaxonomies)) {
      let score = 0;
      if (channelLower && info.channels) {
        for (const ch of info.channels) {
          if (channelLower.includes(ch)) score += 5;
        }
      }
      for (const kw of info.kws) {
        const pattern = new RegExp('(?<!\\w)' + escapeRegex(kw.toLowerCase()) + '(?!\\w)', 'i');
        if (pattern.test(cleanText)) {
          score += kw.split(' ').length * 2 + (kw.includes(' ') ? 1 : 0);
        }
      }
      scores[tag] = score;
    }

    // Contextual Disambiguation: Study vs Coding
    const isInstructional = /\b(crash course|full course|complete course|lecture \d+|unit \d+|tutorial|for beginners|for students|explained|deep dive|walkthrough|from scratch|roadmap)\b/i.test(titleLower);
    if (isInstructional) {
      if (scores.coding > 0 && scores.coding >= scores.study) {
        scores.coding += 4.5;
      } else if (scores.study > 0) {
        scores.study += 4.5;
      } else if (scores.tech > 0) {
        scores.coding += 5;
      }
    }

    if (titleLower.includes('walkthrough') && (scores.study > 0 || scores.coding > 0)) {
      scores.gaming = Math.max(0, (scores.gaming || 0) - 4);
    }

    let bestTag = 'other';
    let maxScore = 0;
    for (const [tag, sc] of Object.entries(scores)) {
      if (sc > maxScore) {
        maxScore = sc;
        bestTag = tag;
      }
    }

    const bestInfo = categoryTaxonomies[bestTag] || {
      name: '🎭 General Entertainment',
      ytId: '24',
      ytMacro: 'Entertainment'
    };

    if (!shieldEnabled) {
      return {
        is_allowed: true,
        category: bestInfo.name,
        category_tag: bestTag,
        youtube_category_id: bestInfo.ytId,
        youtube_macro_category: bestInfo.ytMacro,
        confidence: 0.99,
        matched_preference: 'Shield OFF'
      };
    }

    let isAllowed = activeCategories.includes(bestTag);
    let matchedPref = isAllowed ? bestInfo.name : '';

    if (!isAllowed) {
      for (const custom of customKeywords) {
        const trimmed = custom.trim();
        if (trimmed) {
          const pattern = new RegExp('(?<!\\w)' + escapeRegex(trimmed.toLowerCase()) + '(?!\\w)', 'i');
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
      category: bestInfo.name,
      category_tag: bestTag,
      youtube_category_id: bestInfo.ytId,
      youtube_macro_category: bestInfo.ytMacro,
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

  try {
    chrome.storage.local.get(
      ['shieldEnabled', 'activeCategories', 'customKeywords', 'updated_at'],
      (res) => {
        if (!res) return;
        if (res.shieldEnabled !== undefined) shieldEnabled = res.shieldEnabled;
        if (Array.isArray(res.activeCategories)) activeCategories = res.activeCategories;
        if (Array.isArray(res.customKeywords)) customKeywords = res.customKeywords;
        if (res.updated_at) lastUpdatedAt = res.updated_at;
        triggerImmediateReScan('Initialized', false);
      }
    );
  } catch (_) {}

  try {
    chrome.storage.onChanged.addListener((changes, area) => {
      if (area === 'local') {
        let changed = false;
        if (changes.shieldEnabled !== undefined) {
          shieldEnabled = changes.shieldEnabled.newValue;
          changed = true;
        }
        if (changes.activeCategories !== undefined) {
          activeCategories = changes.activeCategories.newValue || ['study', 'coding'];
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
        if (changed) triggerImmediateReScan('Preferences Updated');
      }
    });
  } catch (_) {}

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
            activeCategories = d.active_categories || ['study', 'coding'];
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
        title = docT.replace(/- YouTube\$/i, '').trim();
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

  function getThumbnailContainer(el) {
    const ytdThumb = el.querySelector('ytd-thumbnail, #thumbnail, a#thumbnail');
    if (ytdThumb) return ytdThumb;

    const thumbBox = el.querySelector('.thumb-box');
    if (thumbBox) return thumbBox;

    const shortsThumb = el.querySelector(
      '.shortsLockupViewModelHostThumbnailContainer, .shortsLockupViewModelHostOutsideMetadataEndpoint'
    );
    if (shortsThumb) return shortsThumb;

    const lockupImg = el.querySelector(
      '.yt-lockup-view-model__content-image, .yt-lockup-metadata-view-model-wiz__thumbnail-container'
    );
    if (lockupImg) return lockupImg;

    const reelContainer = el.querySelector('#short-video-container, #player-container');
    if (reelContainer) return reelContainer;

    return el;
  }

  function getDecision(title, channel) {
    const key = `${title.toLowerCase()}::${channel.toLowerCase()}::${shieldEnabled}::${activeCategories.join(',')}`;
    if (decisionCache.has(key)) return Promise.resolve(decisionCache.get(key));

    return new Promise((resolve) => {
      let resolved = false;
      const fallbackTimer = setTimeout(() => {
        if (!resolved) {
          resolved = true;
          const fb = decideLocally(title, channel);
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
              const fb = decideLocally(title, channel);
              decisionCache.set(key, fb);
              resolve(fb);
            }
          }
        );
      } catch (_) {
        if (!resolved) {
          resolved = true;
          clearTimeout(fallbackTimer);
          const fb = decideLocally(title, channel);
          decisionCache.set(key, fb);
          resolve(fb);
        }
      }
    });
  }

  async function evaluateElement(el) {
    const { title, channel, href } = extractMetadata(el);
    if (!title || title.length < 2) return;

    const signature = `${href}::${title}`;
    if (el.dataset.studyshieldDone === 'true' && el.dataset.studyshieldSignature === signature) {
      return;
    }

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

    const ytIdLabel = decision.youtube_category_id ? `YT ID ${decision.youtube_category_id}` : 'YT Filter';

    if (!decision.is_allowed && !el.dataset.studyshieldUserRevealed) {
      // 🚫 BLUR ONLY THE VIDEO / THUMBNAIL (Never blur the title or description text below!)
      thumbEl.classList.add('studyshield-thumb-blurred');
      thumbEl.classList.remove('studyshield-thumb-verified');
      el.classList.remove('studyshield-study-verified');

      const existingPill = thumbEl.querySelector('.studyshield-study-pill') || el.querySelector('.studyshield-study-pill');
      if (existingPill) existingPill.remove();

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
          <span>🛡️ StudyShield • ${ytIdLabel}</span>
        </div>
        <div class="studyshield-badge-sub">
          <strong>${decision.category}</strong> (${confPct}%)
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
        pill.innerHTML = `<span>✓ ${decision.category} (${ytIdLabel})</span>`;
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
