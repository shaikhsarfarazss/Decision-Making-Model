// StudyShield Extension Popup Controller

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
  const btnSelectAll = document.getElementById('btnSelectAll');
  const btnClearAll = document.getElementById('btnClearAll');
  const statusText = document.getElementById('statusText');

  let currentKeywords = [];

  // Update visual state of category labels
  function syncCategoryVisuals() {
    categoriesGrid.querySelectorAll('.category-label').forEach(label => {
      const cb = label.querySelector('input');
      if (cb.checked) {
        label.classList.add('active');
      } else {
        label.classList.remove('active');
      }
    });
  }

  // Render custom keyword badges
  function renderChips() {
    chipsContainer.innerHTML = '';
    currentKeywords.forEach((kw, idx) => {
      const chip = document.createElement('span');
      chip.className = 'chip';
      chip.innerHTML = `<span>🏷️ ${kw}</span><span class="chip-del" data-idx="${idx}">✕</span>`;
      chipsContainer.appendChild(chip);
    });

    chipsContainer.querySelectorAll('.chip-del').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const idx = parseInt(e.target.dataset.idx, 10);
        currentKeywords.splice(idx, 1);
        renderChips();
      });
    });
  }

  // Load state from local storage or server
  chrome.storage.local.get(['shieldEnabled', 'activeCategories', 'customKeywords'], (res) => {
    const isEnabled = res.shieldEnabled !== undefined ? res.shieldEnabled : true;
    shieldToggle.checked = isEnabled;
    switchSub.innerText = isEnabled ? 'Blurs non-selected content automatically' : 'Shield is OFF. All videos remain clear.';

    const active = res.activeCategories || ['study'];
    categoriesGrid.querySelectorAll('input[type="checkbox"]').forEach(cb => {
      cb.checked = active.includes(cb.value);
    });
    syncCategoryVisuals();

    currentKeywords = res.customKeywords || [];
    renderChips();
  });

  // Also check backend connection & sync if server is newer
  try {
    const pRes = await fetch('http://localhost:8000/preferences', { signal: AbortSignal.timeout(600) });
    if (pRes.ok) {
      const pData = await pRes.json();
      statusText.innerText = 'Laya Local (803MB)';
      if (pData.shield_enabled !== undefined) shieldToggle.checked = pData.shield_enabled;
      if (pData.active_categories) {
        categoriesGrid.querySelectorAll('input[type="checkbox"]').forEach(cb => {
          cb.checked = pData.active_categories.includes(cb.value);
        });
        syncCategoryVisuals();
      }
      if (pData.custom_keywords) {
        currentKeywords = pData.custom_keywords;
        renderChips();
      }
    }
  } catch (e) {
    statusText.innerText = 'In-Browser Fallback';
  }

  // Category checkbox change listener
  categoriesGrid.addEventListener('change', () => {
    syncCategoryVisuals();
  });

  // Preset Buttons
  btnStudyOnly.addEventListener('click', () => {
    categoriesGrid.querySelectorAll('input[type="checkbox"]').forEach(cb => {
      cb.checked = (cb.value === 'study');
    });
    syncCategoryVisuals();
  });

  btnSelectAll.addEventListener('click', () => {
    categoriesGrid.querySelectorAll('input[type="checkbox"]').forEach(cb => {
      cb.checked = true;
    });
    syncCategoryVisuals();
  });

  btnClearAll.addEventListener('click', () => {
    categoriesGrid.querySelectorAll('input[type="checkbox"]').forEach(cb => {
      cb.checked = false;
    });
    syncCategoryVisuals();
  });

  // Add custom keyword
  function addKeyword() {
    const val = customInput.value.trim().toLowerCase();
    if (val && !currentKeywords.includes(val)) {
      currentKeywords.push(val);
      customInput.value = '';
      renderChips();
    }
  }
  customAddBtn.addEventListener('click', addKeyword);
  customInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') addKeyword();
  });

  // Shield Toggle Switch
  shieldToggle.addEventListener('change', () => {
    const isEnabled = shieldToggle.checked;
    switchSub.innerText = isEnabled ? 'Blurs non-selected content automatically' : 'Shield is OFF. All videos remain clear.';
  });

  // 💾 SAVE PREFERENCES & APPLY IMMEDIATELY
  savePreferencesBtn.addEventListener('click', () => {
    const activeCats = Array.from(
      categoriesGrid.querySelectorAll('input[type="checkbox"]:checked')
    ).map(cb => cb.value);

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

    // 1. Send to background script (saves to storage & broadcasts to all tabs)
    chrome.runtime.sendMessage({
      action: 'SAVE_PREFERENCES',
      data: payload
    }, () => {
      // 2. Visual confirmation feedback in popup
      saveToast.style.display = 'block';
      saveToast.innerText = `✅ Preferences Saved! Applied immediately (${activeCats.length} topics allowed).`;

      const prevText = savePreferencesBtn.innerText;
      savePreferencesBtn.innerText = '✔ Applied to YouTube Tabs!';
      savePreferencesBtn.style.background = '#047857';

      setTimeout(() => {
        saveToast.style.display = 'none';
        savePreferencesBtn.innerText = prevText;
        savePreferencesBtn.style.background = '';
      }, 2400);
    });
  });

  // Force re-scan button
  forceRescanBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'FORCE_RESCAN' }, () => {
      forceRescanBtn.innerText = '✅ Scanning Done!';
      setTimeout(() => {
        forceRescanBtn.innerText = '🔄 Force Re-Scan Page Now';
      }, 1500);
    });
  });
});
