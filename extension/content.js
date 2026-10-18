// StudyShield Content Script — Accurate Title Extraction, 20-Category AI & Thumbnail-Only Blur
(() => {
  console.log(
    '%c[StudyShield 🛡️] 3-Layer YouTube Classifier Active (Thumbnail-Only Blur • 20 Categories)',
    'color: #38bdf8; font-size: 13px; font-weight: bold; background: #0f172a; padding: 4px 8px; border-radius: 4px;'
  );

  let shieldEnabled = true;
  let activeCategories = ['study', 'coding'];
  let customKeywords = [];
  let lastUpdatedAt = 0;
  let scanDebounceTimer = null;
  const decisionCache = new Map();
  const processedCards = new WeakMap();

  const VIDEO_CARD_SELECTORS = [
    'ytd-rich-item-renderer',
    'ytd-video-renderer',
    'ytd-compact-video-renderer',
    'ytd-grid-video-renderer',
    'yt-lockup-view-model',
    'ytm-shorts-lockup-view-model',
    'ytm-shorts-lockup-view-model-v2',
    '.ytGridShelfViewModelGridShelfItem',
    'ytd-rich-grid-slim-media',
    'ytd-reel-item-renderer',
    'ytd-reel-video-renderer'
  ].join(', ');

  // 20 YouTube-Aligned Categories with Official YouTube Category IDs & Priors
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
        'anime', 'manga', 'manhwa', 'manhua', 'waifu', 'isekai', 'shonen', 'shounen', 'seinen',
        'shojo', 'amv', 'ova', 'ona', 'crunchyroll', 'funimation', 'aniplex', 'toei', 'mappa',
        'ufotable', 'madhouse', 'vtuber', 'hololive', 'nijisanji', 'english dub', 'eng sub',
        'dragon ball', 'dragon ball z', 'dragon ball super', 'dbz', 'dbs', 'dbgt', 'daima',
        'bardock', 'saiyan', 'super saiyan', 'ssj', 'goku', 'vegeta', 'gohan', 'trunks',
        'frieza', 'freeza', 'cell', 'majin buu', 'broly', 'piccolo', 'krillin', 'beerus', 'whis',
        'jiren', 'zamasu', 'goku black', 'vegito', 'gogeta', 'kamehameha', 'ultra instinct',
        'ultra ego', 'shenron', 'namek', 'naruto', 'shippuden', 'boruto', 'sasuke', 'uchiha',
        'itachi', 'madara', 'obito', 'kakashi', 'jiraiya', 'tsunade', 'orochimaru', 'minato',
        'hokage', 'sharingan', 'rinnegan', 'byakugan', 'akatsuki', 'rasengan', 'chidori',
        'kurama', 'tailed beast', 'shinobi', 'one piece', 'luffy', 'zoro', 'sanji', 'nami',
        'usopp', 'chopper', 'nico robin', 'franky', 'brook', 'jinbe', 'shanks', 'kaido',
        'big mom', 'whitebeard', 'blackbeard', 'akainu', 'gear 5', 'gear fifth', 'devil fruit',
        'haki', 'straw hat', 'mugiwara', 'wano', 'egghead', 'jujutsu kaisen', 'jjk', 'gojo',
        'satoru', 'sukuna', 'ryomen', 'yuji', 'itadori', 'megumi', 'fushiguro', 'domain expansion',
        'cursed technique', 'demon slayer', 'kimetsu no yaiba', 'kimetsu', 'tanjiro', 'nezuko',
        'zenitsu', 'inosuke', 'muzan', 'hashira', 'rengoku', 'akaza', 'kokushibo', 'attack on titan',
        'shingeki no kyojin', 'aot', 'eren yeager', 'eren', 'mikasa', 'levi', 'ackerman',
        'armin', 'titan', 'bleach', 'ichigo', 'kurosaki', 'aizen', 'bankai', 'shikai', 'espada',
        'thousand year blood war', 'tybw', 'my hero academia', 'boku no hero', 'mha', 'deku',
        'bakugo', 'todoroki', 'all might', 'shigaraki', 'one punch man', 'saitama', 'genos',
        'garou', 'chainsaw man', 'denji', 'makima', 'pochita', 'solo leveling', 'sung jinwoo',
        'jin-woo', 'hunter x hunter', 'hxh', 'gon', 'killua', 'hisoka', 'kurapika', 'death note',
        'light yagami', 'ryuk', 'fullmetal alchemist', 'edward elric', 'jojo', 'bizarre adventure',
        'jotaro', 'dio brando', 'blue lock', 'haikyuu', 'baki', 'vinland saga', 'frieren',
        'dandadan', 'studio ghibli', 'ghibli', 'tokyo ghoul', 'sword art online', 'berserk',
        'evangelion', 'opening ost', 'amv', 'anime scene', 'anime clip', 'anime edit', 'anime opening'
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

  // Pre-compile all 20-category regexes ONCE at startup (prevents 15,000x RegExp lag in decideLocally)
  const compiledTaxonomies = {};
  for (const [tag, info] of Object.entries(categoryTaxonomies)) {
    compiledTaxonomies[tag] = {
      ...info,
      channelsLower: (info.channels || []).map((c) => c.toLowerCase()),
      kwPatterns: (info.kws || []).map((kw) => ({
        regex: new RegExp('(?<!\\w)' + escapeRegex(kw.toLowerCase()) + '(?!\\w)', 'i'),
        weight: kw.split(' ').length * 2 + (kw.includes(' ') ? 1 : 0)
      }))
    };
  }

  function setCacheLRU(key, value) {
    if (decisionCache.has(key)) {
      decisionCache.delete(key);
    } else if (decisionCache.size >= 2000) {
      // Evict oldest entry (strict 2,000-item LRU bound)
      const oldestKey = decisionCache.keys().next().value;
      if (oldestKey !== undefined) decisionCache.delete(oldestKey);
    }
    decisionCache.set(key, value);
  }

  function decideLocally(title, channel = '') {
    const titleLower = (title || '').toLowerCase();
    const channelLower = (channel || '').toLowerCase();
    const cleanText = `${titleLower} ${channelLower}`.trim();

    const scores = {};
    for (const [tag, info] of Object.entries(compiledTaxonomies)) {
      let score = 0;
      if (channelLower && info.channelsLower) {
        for (const ch of info.channelsLower) {
          if (channelLower.includes(ch)) score += 5;
        }
      }
      for (const { regex, weight } of info.kwPatterns) {
        if (regex.test(cleanText)) {
          score += weight;
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

    // High-res media clip markers (e.g. 【4K UHD】)
    if (scores.study < 2 && scores.coding < 2) {
      if (/【.*4k.*】|\b4k\s*uhd\b|\b60\s*fps\b/i.test(titleLower)) {
        if (scores.anime > 0) scores.anime += 4;
        else if ((scores.clickbait || 0) <= 0 && (scores.gaming || 0) <= 0) scores.anime += 3;
      }
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
      name: '🎬 General Entertainment',
      ytId: '24',
      ytMacro: 'Entertainment'
    };

    if (!shieldEnabled) {
      return {
        is_allowed: true,
        allowed: true,
        should_blur: false,
        action: 'ALLOW',
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
      allowed: isAllowed,
      should_blur: !isAllowed,
      action: isAllowed ? 'ALLOW' : 'BLUR',
      category: bestInfo.name,
      category_tag: bestTag,
      youtube_category_id: bestInfo.ytId,
      youtube_macro_category: bestInfo.ytMacro,
      confidence: maxScore > 0 ? 0.98 : 0.85,
      matched_preference: matchedPref || 'Blocked'
    };
  }

  function getThumbnailContainer(card) {
    return (
      card.querySelector('ytd-thumbnail') ||
      card.querySelector('yt-thumbnail-view-model') ||
      card.querySelector('.yt-lockup-view-model__content-image') ||
      card.querySelector('.thumb-box') ||
      card.querySelector('.shortsLockupViewModelHostThumbnailContainer') ||
      card.querySelector('#thumbnail') ||
      card.querySelector('#player-container') ||
      card
    );
  }

  function extractVideoInfo(card) {
    let title = '';
    let channel = '';
    let videoId = '';
    let duration = '';
    let isArtist = false;

    // 1. Extract link & videoId
    const linkEl = card.querySelector(
      'a#thumbnail, a#video-title-link, a.shortsLockupViewModelHostEndpoint, a[href*="/watch?v="], a[href*="/shorts/"]'
    );
    const href = linkEl ? linkEl.getAttribute('href') : '';
    if (href) {
      const matchV = href.match(/[?&]v=([a-zA-Z0-9_-]{11})/);
      const matchS = href.match(/\/shorts\/([a-zA-Z0-9_-]{11})/);
      if (matchV) videoId = matchV[1];
      else if (matchS) videoId = matchS[1];
    }
    if (!videoId && card.getAttribute('id')) {
      const idAttr = card.getAttribute('id');
      if (idAttr && idAttr.length === 11) videoId = idAttr;
    }

    // 2. Extract Duration
    const timeEl = card.querySelector(
      'ytd-thumbnail-overlay-time-status-renderer, span.ytd-thumbnail-overlay-time-status-renderer, .badge-shape-wiz__text'
    );
    if (timeEl && timeEl.textContent.trim()) {
      duration = timeEl.textContent.trim();
    }

    // 3. Extract Official Artist Channel Badge
    const artistBadge = card.querySelector(
      '.badge-style-type-official-artist-badge, svg path[d*="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21"]'
    );
    if (artistBadge) {
      isArtist = true;
    }

    // 4. Extract Title (Resilient modern 2026 YouTube layout fallbacks)
    const modernShortsTitle = card.querySelector(
      '.shortsLockupViewModelHostOutsideMetadataTitle, h3.shortsLockupViewModelHostMetadataTitle, a.shortsLockupViewModelHostOutsideMetadataEndpoint, .ytShortsVideoTitleViewModelShortsVideoTitle'
    );
    if (modernShortsTitle && modernShortsTitle.textContent.trim()) {
      title = modernShortsTitle.textContent.trim();
    }

    if (!title) {
      const fullscreenTitle = card.querySelector(
        'yt-reel-metapanel-view-model h2, h2.reel-player-header-renderer, #overlay ytd-reel-player-header-renderer #title, yt-shorts-video-title-view-model span, h1.ytShortsVideoTitleViewModelShortsVideoTitle'
      );
      if (fullscreenTitle && fullscreenTitle.textContent.trim()) {
        title = fullscreenTitle.textContent.trim();
      }
    }

    if (!title) {
      const regularTitle = card.querySelector(
        '#video-title, #video-title-link, yt-formatted-string#video-title, .yt-lockup-metadata-view-model-wiz__title, .yt-lockup-metadata-view-model__title, h3 a'
      );
      if (regularTitle && regularTitle.textContent.trim()) {
        title = regularTitle.textContent.trim();
      }
    }

    if (!title && linkEl) {
      const attrTitle = linkEl.getAttribute('title');
      if (attrTitle && attrTitle.trim()) {
        title = attrTitle.trim();
      } else {
        const ariaLabel = linkEl.getAttribute('aria-label');
        if (ariaLabel && ariaLabel.trim()) {
          // ONLY strip trailing screen-reader duration/views when falling back to aria-label!
          title = ariaLabel.replace(/\s+\d+\s*(hours?|minutes?|seconds?)\s+[\d,]+\s+views?.*$/i, '').trim();
        }
      }
    }

    if (!title && window.location.pathname.startsWith('/shorts') && card.hasAttribute('is-active')) {
      const docT = document.title;
      if (docT && docT.toLowerCase() !== 'youtube') {
        // Fixed regex end-of-string anchor (was /- YouTube\$/i)
        title = docT.replace(/\s*-\s*YouTube$/i, '').trim();
      }
    }

    // 5. Extract Channel
    const channelEl = card.querySelector(
      '.shortsLockupViewModelHostMetadataSubhead, yt-reel-channel-bar-view-model a, .ytReelChannelBarViewModelChannelName, #channel-name, ytd-channel-name, .ytd-channel-name, .yt-content-metadata-view-model__metadata-row'
    );
    if (channelEl) {
      channel = channelEl.textContent.trim().split('\n')[0].trim();
      if (channel.includes('♪') || channel.includes('Official Artist')) {
        isArtist = true;
      }
    }

    return { title, channel, href, videoId, duration, isArtist };
  }

  // 35ms Debounced Batch Queue & Multi-Element Map
  const cardBatchQueue = [];
  let batchDebounceTimer = null;
  const cardElementsMap = new Map(); // videoId -> Set of card DOM nodes

  function queueCardForBatch(card, info) {
    const { videoId, title, channel, duration, isArtist } = info;
    const vid = videoId || `syn_${Math.abs(hashString(title + channel))}`;
    const prefKey = `${shieldEnabled}::${activeCategories.join(',')}::${customKeywords.join(',')}`;
    const cacheKey = `${vid}::${title.toLowerCase()}::${channel.toLowerCase()}::${prefKey}`;

    // 1. LRU Cache Hit (0.001ms)
    if (decisionCache.has(cacheKey)) {
      applyCardState(card, decisionCache.get(cacheKey));
      return;
    }

    // Map DOM card to this videoId for batch delivery
    if (!cardElementsMap.has(vid)) {
      cardElementsMap.set(vid, new Set());
    }
    cardElementsMap.get(vid).add(card);

    if (!cardBatchQueue.some((item) => item.id === vid)) {
      cardBatchQueue.push({
        id: vid,
        title,
        channel,
        duration,
        is_artist: isArtist
      });
    }

    if (!batchDebounceTimer) {
      batchDebounceTimer = setTimeout(flushBatchQueue, 35);
    }
  }

  function hashString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = (hash << 5) - hash + str.charCodeAt(i);
      hash |= 0;
    }
    return hash;
  }

  function flushBatchQueue() {
    batchDebounceTimer = null;
    if (cardBatchQueue.length === 0) return;

    const itemsToProcess = cardBatchQueue.splice(0, 25);

    // CRITICAL FIX: If more than 25 cards were queued, schedule the next batch immediately!
    if (cardBatchQueue.length > 0 && !batchDebounceTimer) {
      batchDebounceTimer = setTimeout(flushBatchQueue, 35);
    }

    const prefKey = `${shieldEnabled}::${activeCategories.join(',')}::${customKeywords.join(',')}`;

    chrome.runtime.sendMessage(
      { action: 'BATCH_DECIDE', items: itemsToProcess },
      (response) => {
        if (!chrome.runtime.lastError && response && response.success && response.data) {
          const results = response.data;
          itemsToProcess.forEach((item) => {
            const vid = item.id;
            const res = results[vid] || decideLocally(item.title, item.channel);
            const cacheKey = `${vid}::${item.title.toLowerCase()}::${item.channel.toLowerCase()}::${prefKey}`;
            setCacheLRU(cacheKey, res);

            const cards = cardElementsMap.get(vid);
            if (cards) {
              cards.forEach((card) => applyCardState(card, res));
              cardElementsMap.delete(vid);
            }

            // Tier 2 Async Failover: probe player category if flagged
            if (res.needs_probe && vid && !vid.startsWith('syn_')) {
              chrome.runtime.sendMessage(
                { action: 'PROBE_METADATA', videoId: vid },
                (probeResp) => {
                  if (
                    !chrome.runtime.lastError &&
                    probeResp &&
                    probeResp.success &&
                    probeResp.data
                  ) {
                    const updatedRes = probeResp.data;
                    setCacheLRU(cacheKey, updatedRes);
                    const activeCards = document.querySelectorAll(`[data-ss-video-id="${vid}"]`);
                    activeCards.forEach((c) => applyCardState(c, updatedRes));
                  }
                }
              );
            }
          });
        } else {
          // Offline fallback
          itemsToProcess.forEach((item) => {
            const vid = item.id;
            const fb = decideLocally(item.title, item.channel);
            const cacheKey = `${vid}::${item.title.toLowerCase()}::${item.channel.toLowerCase()}::${prefKey}`;
            setCacheLRU(cacheKey, fb);
            const cards = cardElementsMap.get(vid);
            if (cards) {
              cards.forEach((card) => applyCardState(card, fb));
              cardElementsMap.delete(vid);
            }
          });
        }
      }
    );
  }

  function applyCardState(card, result) {
    const thumbContainer = getThumbnailContainer(card);
    if (!thumbContainer) return;

    const isBlocked = Boolean(
      result.should_blur === true ||
      result.action === 'BLUR' ||
      result.is_allowed === false ||
      result.allowed === false
    );
    const category = result.category || (isBlocked ? 'Blocked Distraction' : 'Allowed Content');
    const ytIdLabel = result.youtube_category_id ? `ID ${result.youtube_category_id}` : '';

    // 1. Set data-ss-resolved for zero-flash CSS styling
    card.dataset.ssResolved = isBlocked ? 'BLUR' : 'ALLOW';
    card.dataset.studyshieldBlocked = isBlocked ? 'true' : 'false';
    card.classList.remove('studyshield-card-allowed', 'studyshield-card-blocked');
    card.classList.add(isBlocked ? 'studyshield-card-blocked' : 'studyshield-card-allowed');

    // 2. Ensure downside text/details are NEVER blurred
    const detailsEl = card.querySelector(
      '#details, #meta, .yt-lockup-metadata-view-model, .meta-box, .shortsLockupViewModelHostOutsideMetadata'
    );
    if (detailsEl) {
      detailsEl.style.setProperty('filter', 'none', 'important');
      detailsEl.style.setProperty('opacity', '1', 'important');
    }

    // 3. Blur ONLY the media elements inside the upper thumbnail container
    const mediaElements = thumbContainer.querySelectorAll(
      'img, video, ytd-moving-thumbnail-renderer, #video-preview, .thumb-box, .shortsLockupViewModelHostThumbnailContainer'
    );
    if (mediaElements.length > 0) {
      mediaElements.forEach((media) => {
        if (isBlocked && !card.dataset.studyshieldUserRevealed) {
          media.classList.add('studyshield-blur-media');
        } else {
          media.classList.remove('studyshield-blur-media');
        }
      });
    } else {
      if (isBlocked && !card.dataset.studyshieldUserRevealed) {
        thumbContainer.classList.add('studyshield-thumb-blurred');
      } else {
        thumbContainer.classList.remove('studyshield-thumb-blurred');
      }
    }

    // YouTube Shorts Audio Muting & Floating Center Pill
    const isShorts =
      window.location.pathname.startsWith('/shorts') ||
      card.tagName.toLowerCase() === 'ytd-reel-video-renderer';
    if (isShorts) {
      let pill = card.querySelector('.studyshield-shorts-pill');
      if (isBlocked && !card.dataset.studyshieldUserRevealed) {
        const vidEl = card.querySelector('video');
        if (vidEl) {
          vidEl.muted = true;
        }
        if (!pill) {
          pill = document.createElement('div');
          pill.className = 'studyshield-shorts-pill';
          pill.innerHTML = `<span>🛡️ ${category} Blurred (Click to Reveal)</span>`;
          pill.addEventListener('click', (e) => {
            e.stopPropagation();
            card.dataset.studyshieldUserRevealed = 'true';
            card.dataset.ssResolved = 'ALLOW';
            if (vidEl) vidEl.muted = false;
            pill.remove();
          });
          thumbContainer.appendChild(pill);
        }
      } else if (pill) {
        pill.remove();
      }
    }

    // 4. Add or update the badge inside the thumbnail container
    let badge = thumbContainer.querySelector('.studyshield-badge');
    if (!badge) {
      badge = document.createElement('div');
      badge.className = 'studyshield-badge';
      thumbContainer.appendChild(badge);
    }

    badge.classList.remove('studyshield-badge-study', 'studyshield-badge-blocked', 'studyshield-badge-anime');
    if (isBlocked) {
      badge.classList.add(category.includes('Anime') ? 'studyshield-badge-anime' : 'studyshield-badge-blocked');
      badge.innerHTML = `<span>🚫 ${category} ${ytIdLabel}</span>`;

      if (!card.dataset.studyshieldUserRevealed) {
        let unblurBtn = badge.querySelector('.studyshield-unblur-btn');
        if (!unblurBtn) {
          unblurBtn = document.createElement('button');
          unblurBtn.className = 'studyshield-unblur-btn';
          unblurBtn.textContent = '👁️ Reveal';
          unblurBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            card.dataset.studyshieldUserRevealed = 'true';
            card.dataset.ssResolved = 'ALLOW';
            card.classList.remove('studyshield-card-blocked');
            card.classList.add('studyshield-card-allowed');
            mediaElements.forEach((m) => m.classList.remove('studyshield-blur-media'));
            thumbContainer.classList.remove('studyshield-thumb-blurred');
            badge.remove();
            const vid = card.querySelector('video');
            if (vid) {
              vid.muted = false;
              vid.play().catch(() => {});
            }
          });
          badge.appendChild(unblurBtn);
        }
      }
    } else {
      badge.classList.add('studyshield-badge-study');
      badge.innerHTML = `<span>✓ ${category} ${ytIdLabel}</span>`;
    }
  }

  // Hover inline video preview blur protection
  document.addEventListener(
    'mouseover',
    (e) => {
      const card = e.target.closest(VIDEO_CARD_SELECTORS);
      const previewPlayer = document.querySelector('ytd-video-preview');
      if (!card || !previewPlayer) return;

      if (card.dataset.studyshieldBlocked === 'true' && !card.dataset.studyshieldUserRevealed) {
        previewPlayer.classList.add('studyshield-preview-blocked');
      } else {
        previewPlayer.classList.remove('studyshield-preview-blocked');
      }
    },
    true
  );

  // IntersectionObserver for lazy on-screen card classification
  const cardObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          classifyCard(entry.target);
        }
      });
    },
    { rootMargin: '300px 0px' }
  );

  function classifyCard(card) {
    const info = extractVideoInfo(card);
    if (!info.title || info.title.length < 2) return;

    // Polymer Recycling Detection:
    // If the videoId changed on this recycled DOM node, reset its state
    if (card.dataset.ssVideoId && card.dataset.ssVideoId !== info.videoId) {
      delete card.dataset.ssResolved;
      delete card.dataset.studyshieldDone;
      delete card.dataset.studyshieldUserRevealed;
    }

    if (card.dataset.ssResolved && card.dataset.ssVideoId === info.videoId) {
      return; // Already resolved for this exact video
    }

    card.dataset.ssVideoId = info.videoId || `syn_${Math.abs(hashString(info.title + info.channel))}`;
    card.dataset.studyshieldDone = 'true';
    processedCards.set(card, info.title);

    queueCardForBatch(card, info);
  }

  function scanAllContent() {
    // 1. Observe all feed cards via IntersectionObserver
    document.querySelectorAll(VIDEO_CARD_SELECTORS).forEach((card) => {
      cardObserver.observe(card);
    });

    // 2. Pre-cache next YouTube Shorts reel
    if (window.location.pathname.startsWith('/shorts')) {
      const activeReel = document.querySelector('ytd-reel-video-renderer[is-active]');
      if (activeReel) {
        classifyCard(activeReel);
        const nextReel = activeReel.nextElementSibling;
        if (nextReel && nextReel.tagName.toLowerCase() === 'ytd-reel-video-renderer') {
          classifyCard(nextReel);
        }
      }
    }
  }

  function scheduleScan() {
    if (scanDebounceTimer) return;
    scanDebounceTimer = setTimeout(() => {
      scanDebounceTimer = null;
      scanAllContent();
    }, 40);
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
    cardBatchQueue.length = 0;
    if (batchDebounceTimer) {
      clearTimeout(batchDebounceTimer);
      batchDebounceTimer = null;
    }
    cardElementsMap.clear();

    const cards = document.querySelectorAll(VIDEO_CARD_SELECTORS);
    cards.forEach((el) => {
      delete el.dataset.studyshieldDone;
      delete el.dataset.studyshieldSignature;
      delete el.dataset.studyshieldUserRevealed;
      delete el.dataset.ssResolved;
      delete el.dataset.ssVideoId;
    });

    // Immediately re-classify all cards currently in the DOM so on-screen videos blur/unblur instantly
    cards.forEach((card) => {
      classifyCard(card);
      cardObserver.observe(card);
    });

    if (window.location.pathname.startsWith('/shorts')) {
      const activeReel = document.querySelector('ytd-reel-video-renderer[is-active]');
      if (activeReel) classifyCard(activeReel);
    }

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
          const activeSorted = (activeCategories || []).slice().sort();
          const serverCatsSorted = (d.active_categories || []).slice().sort();
          const categoriesMatch = JSON.stringify(activeSorted) === JSON.stringify(serverCatsSorted);
          const shieldMatch =
            shieldEnabled === (d.shield_enabled !== undefined ? d.shield_enabled : true);
          const kwSorted = (customKeywords || []).slice().sort();
          const serverKwSorted = (d.custom_keywords || []).slice().sort();
          const kwMatch = JSON.stringify(kwSorted) === JSON.stringify(serverKwSorted);

          if (!categoriesMatch || !shieldMatch || !kwMatch || serverUpdated > lastUpdatedAt + 0.5) {
            shieldEnabled = d.shield_enabled !== undefined ? d.shield_enabled : true;
            activeCategories = d.active_categories || ['study', 'coding'];
            customKeywords = d.custom_keywords || [];
            lastUpdatedAt = serverUpdated;

            triggerImmediateReScan('Synced with Local Server');
          }
        }
      });
    } catch (_) {}
  }

  syncPreferences();
  setInterval(syncPreferences, 2000);

  const observer = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (
        m.target &&
        m.target.classList &&
        (m.target.classList.contains('studyshield-badge') ||
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
