// StudyShield Extension Popup Controller — 20 YouTube Categories (Real-Time Bidirectional Sync)
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
        savePreferences(false);
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

  // 1. Initial State from Local Storage (instant UI populate)
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

  // 2. Fetch Latest State from Backend ONCE at startup to get server state and live stats
  chrome.runtime.sendMessage({ action: 'GET_PREFERENCES' }, (response) => {
    if (!chrome.runtime.lastError && response && response.success && response.data) {
      const pData = response.data;
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
    } else {
      statusText.innerText = 'In-Browser 3-Layer';
    }
  });

  // 3. Periodic Telemetry Stats Polling ONLY (NEVER touches checkboxes to prevent unselecting!)
  function pollTelemetry() {
    chrome.runtime.sendMessage({ action: 'GET_PREFERENCES' }, (response) => {
      if (!chrome.runtime.lastError && response && response.success && response.data) {
        const pData = response.data;
        statusText.innerText = 'Laya 3-Layer (0.2ms)';
        allowedStat.innerText = pData.allowed_count || 0;
        blockedStat.innerText = pData.blocked_count || 0;
      }
    });
  }
  const pollTimer = setInterval(pollTelemetry, 2000);

  // 4. Save Preferences function
  function savePreferences(showToast = false) {
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

    // Immediately persist to local storage so user choices are never lost
    chrome.storage.local.set(payload);

    // Save to server & broadcast to all YouTube tabs
    chrome.runtime.sendMessage({ action: 'SAVE_PREFERENCES', data: payload }, (res) => {
      if (showToast) {
        saveToast.style.display = 'block';
        saveToast.innerText = `✅ Saved! (${activeCats.length} of 20 categories allowed)`;
        setTimeout(() => {
          saveToast.style.display = 'none';
        }, 1800);
      }
    });
  }

  // 5. User Interaction Listeners — Checkboxes stay selected permanently!
  categoriesGrid.addEventListener('change', () => {
    syncCategoryVisuals();
    savePreferences(false);
  });

  btnStudyOnly.addEventListener('click', () => {
    categoriesGrid.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.checked = cb.value === 'study';
    });
    syncCategoryVisuals();
    savePreferences(false);
  });

  btnCodeOnly.addEventListener('click', () => {
    categoriesGrid.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.checked = cb.value === 'coding';
    });
    syncCategoryVisuals();
    savePreferences(false);
  });

  btnStudyAndCode.addEventListener('click', () => {
    categoriesGrid.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.checked = cb.value === 'study' || cb.value === 'coding';
    });
    syncCategoryVisuals();
    savePreferences(false);
  });

  btnSelectAll.addEventListener('click', () => {
    categoriesGrid.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.checked = true;
    });
    syncCategoryVisuals();
    savePreferences(false);
  });

  btnClearAll.addEventListener('click', () => {
    categoriesGrid.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
      cb.checked = false;
    });
    syncCategoryVisuals();
    savePreferences(false);
  });

  function addKeyword() {
    const val = customInput.value.trim().toLowerCase();
    if (val && !currentKeywords.includes(val)) {
      currentKeywords.push(val);
      customInput.value = '';
      renderChips();
      savePreferences(false);
    }
  }

  customAddBtn.addEventListener('click', addKeyword);
  customInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addKeyword();
    }
  });

  shieldToggle.addEventListener('change', () => {
    const isEnabled = shieldToggle.checked;
    switchSub.innerText = isEnabled
      ? 'Blurs non-selected YouTube categories'
      : 'Shield is OFF. All videos remain clear.';
    savePreferences(true);
  });

  savePreferencesBtn.addEventListener('click', () => savePreferences(true));

  forceRescanBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'FORCE_RESCAN' }, () => {
      forceRescanBtn.innerText = '✅ Re-Scanned!';
      setTimeout(() => {
        forceRescanBtn.innerText = '🔄 Force Re-Scan';
      }, 1400);
    });
  });
});
