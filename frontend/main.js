document.addEventListener('DOMContentLoaded', () => {
  // --- [UI Elements] ---
  const urlInput = document.getElementById('urlInput');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const factCheckBtn = document.getElementById('factCheckBtn');
  const loadingDiv = document.getElementById('loading');
  const resultsSection = document.getElementById('resultsSection');
  const keyClaimsDiv = document.getElementById('keyClaims');
  const factCheckSection = document.getElementById('factCheckSection');
  const factCheckResultsDiv = document.getElementById('factCheckResults');
  const errorDiv = document.getElementById('error');

  // Human-in-the-loop UI
  const skipAIConfirmationCheckbox = document.getElementById('skipAIConfirmation');
  const aiConfirmationCard = document.getElementById('aiConfirmationCard');
  const confirmSearchBtn = document.getElementById('confirmSearchBtn');
  const aiInterpretedIntent = document.getElementById('aiInterpretedIntent');
  const aiKeywords = document.getElementById('aiKeywords');
  const aiCountries = document.getElementById('aiCountries');

  // History UI
  const inputTab = document.getElementById('inputTab');
  const popularTab = document.getElementById('popularTab');
  const recentTab = document.getElementById('recentTab');
  const popularList = document.getElementById('popularList');
  const recentList = document.getElementById('recentList');
  const tabBtns = document.querySelectorAll('.tab-btn');

  // --- [Configuration] ---
  const API_BASE_URL = '';

  let currentAnalysis = null;
  let pendingSearchData = null;

  // Load Settings
  if (skipAIConfirmationCheckbox) {
    const savedSkip = localStorage.getItem('skipAIConfirmation');
    if (savedSkip === 'true') skipAIConfirmationCheckbox.checked = true;
    skipAIConfirmationCheckbox.addEventListener('change', () => {
      localStorage.setItem('skipAIConfirmation', skipAIConfirmationCheckbox.checked);
    });
  }

  // --- [Tab Switching] ---
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabName = btn.dataset.tab;
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      if (inputTab) inputTab.classList.add('hidden');
      if (popularTab) popularTab.classList.add('hidden');
      if (recentTab) recentTab.classList.add('hidden');
      if (resultsSection) resultsSection.classList.add('hidden');

      if (tabName === 'input' && inputTab) inputTab.classList.remove('hidden');
      else if (tabName === 'popular' && popularTab) { popularTab.classList.remove('hidden'); loadPopularContent(); }
      else if (tabName === 'recent' && recentTab) { recentTab.classList.remove('hidden'); loadRecentHistory(); }
    });
  });

  // URL Parameter Check
  const urlParams = new URLSearchParams(window.location.search);
  const sharedUrl = urlParams.get('url');
  if (sharedUrl) {
    urlInput.value = decodeURIComponent(sharedUrl);
    if (sharedUrl.includes('youtube.com') || sharedUrl.includes('youtu.be')) {
      const ytRadio = document.querySelector('input[value="youtube"]');
      if(ytRadio) ytRadio.checked = true;
    }
  }

  if(urlInput) {
    urlInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') analyzeBtn.click();
    });
  }

  // --- [Step 1: Content Analysis] ---
  if (analyzeBtn) {
    analyzeBtn.addEventListener('click', async () => {
      const url = urlInput.value.trim();
      const inputTypeEl = document.querySelector('input[name="inputType"]:checked');
      const inputType = inputTypeEl ? inputTypeEl.value : 'youtube';

      if (!url) return showError('URL을 입력해주세요');

      showLoading(true, '콘텐츠를 분석하고 있습니다...');
      clearError();
      if (resultsSection) resultsSection.classList.add('hidden');
      if (factCheckSection) factCheckSection.classList.add('hidden');
      analyzeBtn.disabled = true;

      try {
        const response = await fetch(`${API_BASE_URL}/api/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url, inputType }),
        });

        if (!response.ok) throw new Error('분석 서버 응답 오류');
        const data = await response.json();
        if (!data.success) throw new Error(data.error || '분석 실패');

        currentAnalysis = data.analysis;
        displayAnalysisResults(currentAnalysis);
        if (resultsSection) resultsSection.classList.remove('hidden');
        if (factCheckSection) factCheckSection.classList.remove('hidden');

        const newUrl = new URL(window.location);
        newUrl.searchParams.set('url', url);
        window.history.pushState({}, '', newUrl);

      } catch (err) {
        showError(err.message);
      } finally {
        showLoading(false);
        analyzeBtn.disabled = false;
      }
    });
  }

  // --- [AI Query Optimization] ---
  async function optimizeQuery(userInput, context) {
    const response = await fetch(`${API_BASE_URL}/api/optimize-query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_input: userInput,
        context: {
          title_kr: context.title_kr || '',
          key_claims: context.key_claims || []
        }
      }),
    });

    if (!response.ok) throw new Error('쿼리 최적화 서버 오류');

    const data = await response.json();
    const resultData = data.success ? data.data : (data.data || data);
    
    let countries = resultData.target_countries || [];
    if (countries.length === 0) {
      console.warn("⚠️ 국가 정보 없음. 기본값(US, KR) 사용");
      countries = [{code: 'US', reason: 'Default'}, {code: 'KR', reason: 'Default'}];
    }

    return {
      issue_type: resultData.issue_type || 'multi_country',
      topic_en: resultData.topic_en || userInput, 
      target_countries: countries,
      gdelt_params: resultData.gdelt_params || { keywords: [userInput] },
      interpreted_intent: resultData.interpreted_intent || userInput,
      search_keywords_en: resultData.gdelt_params ? resultData.gdelt_params.keywords : [userInput],
      target_country_codes: countries.map(c => c.code)
    };
  }

  // --- [Step 2: Global Perspective Search] ---
  if (factCheckBtn) {
    factCheckBtn.addEventListener('click', async () => {
      const customClaimInput = document.getElementById('customClaimInput');
      let userInput = customClaimInput ? customClaimInput.value.trim() : '';

      if (!userInput) {
        const checkedBox = document.querySelector('#keyClaims input[type="checkbox"]:checked');
        if (checkedBox) {
          userInput = checkedBox.value;
          console.log("✅ 체크박스 선택됨, AI 분석 대상으로 설정:", userInput);
        }
      }

      if (!userInput) {
        return showError('위의 주장을 선택하거나, 직접 주장을 입력해주세요');
      }

      clearError();
      if (aiConfirmationCard) aiConfirmationCard.classList.add('hidden');

      const skipConfirmation = skipAIConfirmationCheckbox ? skipAIConfirmationCheckbox.checked : false;
      await showAIInterpretation(userInput, null, skipConfirmation);
    });
  }

  async function showAIInterpretation(userInput, unused, skipConfirmation = false) {
    factCheckBtn.disabled = true;

    try {
      showLoading(true, skipConfirmation ? '🚀 글로벌 뉴스 검색 중...' : '💭 AI가 질문을 분석하고 있습니다...');

      const context = {
        title_kr: currentAnalysis?.title_kr || '',
        key_claims: currentAnalysis?.key_claims || []
      };

      const optimizedData = await optimizeQuery(userInput, context);

      if (skipConfirmation) {
        showLoading(true, '🔍 전 세계 뉴스를 국가별로 검색하고 있습니다...');
        await executeFullSearchNew(optimizedData);
        return;
      }

      pendingSearchData = { optimizedData };

      if (aiInterpretedIntent) aiInterpretedIntent.textContent = optimizedData.interpreted_intent || userInput;
      
      if (aiKeywords) {
        aiKeywords.innerHTML = '';
        (optimizedData.search_keywords_en || []).forEach(k => {
          const tag = document.createElement('span');
          tag.className = 'keyword-tag';
          tag.textContent = k;
          aiKeywords.appendChild(tag);
        });
      }

      if (aiCountries) {
        aiCountries.innerHTML = '';
        (optimizedData.target_country_codes || []).forEach(c => {
          const code = typeof c === 'object' ? c.code : c;
          const tag = document.createElement('span');
          tag.className = 'country-tag';
          tag.innerHTML = `${getCountryFlag(code)} ${code}`;
          aiCountries.appendChild(tag);
        });
      }

      if (aiConfirmationCard) {
        aiConfirmationCard.classList.remove('hidden');
        setTimeout(() => aiConfirmationCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 100);
      }

    } catch (error) {
      console.warn('AI 분석 실패, 기본 검색으로 전환:', error);
      await executeFullSearchNew({
        topic_en: userInput,
        target_countries: [{code:'US'}, {code:'KR'}],
        gdelt_params: { keywords: [userInput] }
      });
    } finally {
      showLoading(false);
      factCheckBtn.disabled = false;
    }
  }

  if (confirmSearchBtn) {
    confirmSearchBtn.addEventListener('click', async () => {
      if (!pendingSearchData) return;
      if (aiConfirmationCard) aiConfirmationCard.classList.add('hidden');
      await executeFullSearchNew(pendingSearchData.optimizedData);
    });
  }

  async function executeFullSearchNew(searchParams) {
    factCheckBtn.disabled = true;
    if (confirmSearchBtn) confirmSearchBtn.disabled = true;

    try {
      showLoading(true, '🔍 전 세계 뉴스를 국가별로 검색하고 있습니다...');

      const response = await fetch(`${API_BASE_URL}/api/find-sources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ search_params: searchParams }),
      });

      if (!response.ok) throw new Error('검색 요청 실패');
      const data = await response.json();
      if (!data.success) throw new Error(data.error || '검색 실패');

      displaySourcesNew(data.result);

    } catch (err) {
      console.error(err);
      showError(err.message);
    } finally {
      showLoading(false);
      factCheckBtn.disabled = false;
      if (confirmSearchBtn) confirmSearchBtn.disabled = false;
    }
  }

  function displayAnalysisResults(analysis) {
    keyClaimsDiv.innerHTML = '';
    const title = document.createElement('h3');
    title.textContent = '주요 주장';
    title.className = 'section-title';
    keyClaimsDiv.appendChild(title);

    if (analysis.key_claims) {
      const list = document.createElement('div');
      list.className = 'claims-list';
      analysis.key_claims.forEach((claim, idx) => {
        const claimText = typeof claim === 'string' ? claim : claim.claim_kr;
        const item = document.createElement('div');
        item.className = 'claim-item';
        
        item.innerHTML = `
          <input type="checkbox" id="claim-${idx}" value="${escapeHtml(claimText)}" class="claim-checkbox">
          <label for="claim-${idx}" class="claim-label">${escapeHtml(claimText)}</label>
        `;
        list.appendChild(item);

        const checkbox = item.querySelector('input');
        checkbox.addEventListener('change', function() {
          if(this.checked) {
            document.querySelectorAll('.claim-checkbox').forEach(cb => {
              if(cb !== this) cb.checked = false;
            });
          }
        });
      });
      keyClaimsDiv.appendChild(list);
    }
  }

  function displaySourcesNew(data) {
    factCheckResultsDiv.innerHTML = '';

    if (!data || !data.data) {
      factCheckResultsDiv.innerHTML = '<div class="no-results">데이터 형식 오류</div>';
      return;
    }

    const countryKeys = Object.keys(data.data);
    if (countryKeys.length === 0) {
      factCheckResultsDiv.innerHTML = '<div class="no-results">관련 기사를 찾지 못했습니다. (0건)</div>';
      return;
    }

    countryKeys.forEach(countryCode => {
      const group = data.data[countryCode];
      const articles = group.articles || [];
      const role = group.role || '관련국';

      if (articles.length === 0) return;

      const section = document.createElement('div');
      section.className = 'country-section';
      section.style.marginBottom = '24px';

      section.innerHTML = `
        <h3 class="country-header" style="border-bottom: 2px solid #eee; padding-bottom: 8px; margin-bottom: 12px;">
          <span style="font-size: 1.2em; margin-right: 8px;">${getFlagEmoji(countryCode)}</span>
          ${countryCode} <span style="font-size: 0.8em; color: #666; font-weight: normal;">(${role})</span>
          <span style="float: right; font-size: 0.8em; color: #888;">총 ${articles.length}건</span>
        </h3>
      `;

      const ul = document.createElement('ul');
      ul.className = 'article-list';
      ul.style.listStyle = 'none';
      ul.style.padding = '0';

      articles.forEach(art => {
        ul.appendChild(createArticleItem(art));
      });
      
      section.appendChild(ul);
      factCheckResultsDiv.appendChild(section);
    });
  }

  function createArticleItem(article) {
    const li = document.createElement('li');
    li.style.marginBottom = '10px';
    li.style.padding = '12px';
    li.style.backgroundColor = '#f9f9f9';
    li.style.borderRadius = '8px';
    
    // [수정됨] 한글 제목(title_kr)이 있으면 우선 표시
    const titleToDisplay = article.title_kr || article.title || '제목 없음';
    const scoreBadge = article.relevance_score 
      ? `<span style="font-size:11px; color:#28a745; font-weight:bold;">(연관성: ${(article.relevance_score * 100).toFixed(0)}%)</span>` 
      : '';

    li.innerHTML = `
      <div style="font-size: 12px; color: #666; margin-bottom: 4px; display: flex; justify-content: space-between;">
        <strong>${escapeHtml(article.source)}</strong>
        <span>${escapeHtml(article.date || '')} ${scoreBadge}</span>
      </div>
      <a href="${escapeHtml(article.url)}" target="_blank" title="${escapeHtml(article.title)}" style="text-decoration: none; color: #1a0dab; font-weight: 500; font-size: 15px; display: block; line-height: 1.4;">
        ${escapeHtml(titleToDisplay)}
      </a>
    `;
    return li;
  }

  // --- [Utilities] ---
  function showLoading(show, msg) {
    if(loadingDiv) {
      loadingDiv.classList.toggle('hidden', !show);
      if(show && msg) loadingDiv.querySelector('.loading-text').textContent = msg;
    }
  }
  function showError(msg) {
    if(errorDiv) {
      errorDiv.textContent = '⚠️ ' + msg;
      errorDiv.classList.remove('hidden');
      setTimeout(() => errorDiv.classList.add('hidden'), 5000);
    }
  }
  function clearError() { if(errorDiv) errorDiv.classList.add('hidden'); }
  function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }
  function getCountryFlag(code) {
    if (!code || code === 'Unknown') return '🌐';
    return String.fromCodePoint(...code.toUpperCase().split('').map(c => 127397 + c.charCodeAt()));
  }
  function getFlagEmoji(code) { return getCountryFlag(code); }

  async function loadPopularContent() { if(popularList) popularList.innerHTML = '기능 준비 중'; }
  async function loadRecentHistory() { if(recentList) recentList.innerHTML = '기능 준비 중'; }
});