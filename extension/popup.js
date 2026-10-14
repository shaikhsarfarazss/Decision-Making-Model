// StudyShield Extension Popup Controller — 20 YouTube Categories (Study & Coding Separated)
document.addEventListener('DOMContentLoaded', async () => {
  const shieldToggle = document.getElementById('shieldToggle');
  const switchSub = document.getElementById('switchSub');
  const categoriesGrid = document.getElementById('categoriesGrid');
  const customInput = document.getElementById('customInput');
  const customAddBtn = document.getElementById('customAddBtn');
  const chipsContainer = document.getElementById('chipsContainer');
  const savePreferencesBtn = document.getElementById('savePreferencesBtn');
  const forceRescanBtn = document.getElementById('forceRescanBtn');
  const saveToast = document.getElementById('saveToast');
  const btnStudyOnly = document.getElementById('btnStudyOnly');
  const btnCodeOnly = document.getElementById('btnCodeOnly');
  const btnStudyAndCode = document.getElementById('btnStudyAndCode');
  const btnSelectAll = document.getElementById('btnSelectAll');
  const btnClearAll = document.getElementById('btnClearAll');
  const statusText = document.getElementById('statusText');
  const allowedStat = document.getElementById('allowedStat');
  const blockedStat = document.getElementById('blockedStat');

  let currentKeywords = [];

  function syncCategoryVisuals() {
    categoriesGrid.querySelectorAll('.category-label').forEach((label) => {
      const cb = label.querySelector('input');
      label.classList.toggle('active', cb.checked);
    });
  }

  function renderChips() {
    chipsContainer.innerHTML = '';
    currentKeywords.forEach((kw, idx) => {
      const chip = document.createElement('span');
      chip.className = 'chip';
      chip.innerHTML = `<span>#${kw}</span><span class="chip-del" data-idx="${idx}">×</span>`;
      chipsContainer.appendChild(chip);
    });
    chipsContainer.querySelectorAll('.chip-del').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const idx = parseInt(e.target.dataset.idx, 10);
        currentKeywords.splice(idx, 1);
        renderChips();
      });
    });
  }

  function applyStateToUI(isEnabled, activeCats, keywords) {
    shieldToggle.checked = isEnabled;
    switchSub.innerText = isEnabled
      ? 'Blurs non-selected YouTube categories'
      : 'Shield is OFF. All videos remain clear.';
    categoriesGrid.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.checked = activeCats.includes(cb.value);
    });
    syncCategoryVisuals();
    currentKeywords = keywords || [];
    renderChips();
  }

  const localData = await new Promise((resolve) => {
    chrome.storage.local.get(
      ['shieldEnabled', 'activeCategories', 'customKeywords', 'updated_at'],
      (res) => resolve(res || {})
    );
  });

  applyStateToUI(
    localData.shieldEnabled !== undefined ? localData.shieldEnabled : true,
    localData.activeCategories || ['study', 'coding'],
    localData.customKeywords || []
  );

  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 500);
    const pRes = await fetch('http://127.0.0.1:8000/preferences', { signal: controller.signal });
    clearTimeout(timer);
    if (pRes.ok) {
      const pData = await pRes.json();
      statusText.innerText = 'Laya 3-Layer (0.2ms)';
      allowedStat.innerText = pData.allowed_count || 0;
      blockedStat.innerText = pData.blocked_count || 0;
      if (!localData.updated_at || (pData.updated_at && pData.updated_at >= localData.updated_at)) {
        applyStateToUI(
          pData.shield_enabled !== undefined ? pData.shield_enabled : true,
          pData.active_categories || ['study', 'coding'],
          pData.custom_keywords || []
        );
      }
    }
  } catch (_) {
    statusText.innerText = 'In-Browser 3-Layer';
  }

  categoriesGrid.addEventListener('change', syncCategoryVisuals);

  btnStudyOnly.addEventListener('click', () => {
    categoriesGrid.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.checked = cb.value === 'study';
    });
    syncCategoryVisuals();
  });

  btnCodeOnly.addEventListener('click', () => {
    categoriesGrid.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.checked = cb.value === 'coding';
    });
    syncCategoryVisuals();
  });

  btnStudyAndCode.addEventListener('click', () => {
    categoriesGrid.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.checked = cb.value === 'study' || cb.value === 'coding';
    });
    syncCategoryVisuals();
  });

  btnSelectAll.addEventListener('click', () => {
    categoriesGrid.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.checked = true;
    });
    syncCategoryVisuals();
  });

  btnClearAll.addEventListener('click', () => {
    categoriesGrid.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.checked = false;
    });
    syncCategoryVisuals();
  });

  function addKeyword() {
    const val = customInput.value.trim().toLowerCase();
    if (val && !currentKeywords.includes(val)) {
      currentKeywords.push(val);
      customInput.value = '';
      renderChips();
    }
  }

  customAddBtn.addEventListener('click', addKeyword);
  customInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addKeyword();
    }
  });

  function savePreferences() {
    const activeCats = Array.from(
      categoriesGrid.querySelectorAll('input[type="checkbox"]:checked')
    ).map((cb) => cb.value);

    const isShieldOn = shieldToggle.checked;
    const timestamp = Date.now() / 1000;

    const payload = {
      shield_enabled: isShieldOn,
      shieldEnabled: isShieldOn,
      active_categories: activeCats,
      activeCategories: activeCats,
      custom_keywords: currentKeywords,
      customKeywords: currentKeywords,
      updated_at: timestamp
    };

    chrome.runtime.sendMessage({ action: 'SAVE_PREFERENCES', data: payload }, () => {
      saveToast.style.display = 'block';
      saveToast.innerText = `✅ Saved! (${activeCats.length} of 20 categories allowed)`;
      setTimeout(() => {
        saveToast.style.display = 'none';
      }, 2200);
    });
  }

  shieldToggle.addEventListener('change', () => {
    const isEnabled = shieldToggle.checked;
    switchSub.innerText = isEnabled
      ? 'Blurs non-selected YouTube categories'
      : 'Shield is OFF. All videos remain clear.';
    savePreferences();
  });

  savePreferencesBtn.addEventListener('click', savePreferences);

  forceRescanBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'FORCE_RESCAN' }, () => {
      forceRescanBtn.innerText = '✅ Re-Scanned!';
      setTimeout(() => {
        forceRescanBtn.innerText = '🔄 Force Re-Scan';
      }, 1400);
    });
  });
});
