document.addEventListener('DOMContentLoaded', () => {
  const urlInput = document.getElementById('urlInput');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const factCheckBtn = document.getElementById('factCheckBtn');
  const loadingDiv = document.getElementById('loading');
  const resultsSection = document.getElementById('resultsSection');
  const keyClaimsDiv = document.getElementById('keyClaims');
  const factCheckSection = document.getElementById('factCheckSection');
  const factCheckResultsDiv = document.getElementById('factCheckResults');
  const errorDiv = document.getElementById('error');

  // 히스토리 UI 요소
  const inputTab = document.getElementById('inputTab');
  const popularTab = document.getElementById('popularTab');
  const recentTab = document.getElementById('recentTab');
  const popularList = document.getElementById('popularList');
  const recentList = document.getElementById('recentList');
  const tabBtns = document.querySelectorAll('.tab-btn');

  // 백엔드 서버 주소 (환경에 따라 자동 설정)
  const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:8080'
    : `${window.location.protocol}//${window.location.hostname}${window.location.port ? ':' + window.location.port : ''}`;

  let currentAnalysis = null;

  // 탭 전환 기능
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabName = btn.dataset.tab;

      // 모든 탭 버튼 비활성화
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // 모든 섹션 숨기기
      inputTab.classList.add('hidden');
      popularTab.classList.add('hidden');
      recentTab.classList.add('hidden');
      resultsSection.classList.add('hidden');

      // 선택된 탭 표시
      if (tabName === 'input') {
        inputTab.classList.remove('hidden');
      } else if (tabName === 'popular') {
        popularTab.classList.remove('hidden');
        loadPopularContent();
      } else if (tabName === 'recent') {
        recentTab.classList.remove('hidden');
        loadRecentHistory();
      }
    });
  });

  // URL 파라미터에서 URL 읽기 (공유 링크 지원)
  const urlParams = new URLSearchParams(window.location.search);
  const sharedUrl = urlParams.get('url');
  if (sharedUrl) {
    urlInput.value = decodeURIComponent(sharedUrl);

    // 자동 타입 감지
    if (sharedUrl.includes('youtube.com') || sharedUrl.includes('youtu.be')) {
      document.querySelector('input[value="youtube"]').checked = true;
    } else {
      document.querySelector('input[value="article"]').checked = true;
    }
  }

  // Enter 키로 분석 시작
  urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      analyzeBtn.click();
    }
  });

  // 1차 분석: 주장 추출
  analyzeBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    const inputType = document.querySelector('input[name="inputType"]:checked').value;

    if (!url) {
      showError('URL을 입력해주세요');
      return;
    }

    // URL 유효성 검사
    try {
      new URL(url);
    } catch {
      showError('올바른 URL 형식이 아닙니다');
      return;
    }

    showLoading(true, '주장을 분석하고 있습니다...');
    clearError();
    resultsSection.classList.add('hidden');
    factCheckSection.classList.add('hidden');
    analyzeBtn.disabled = true;

    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, inputType }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || '분석 실패');
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || '분석 실패');
      }

      currentAnalysis = data.analysis;
      displayAnalysisResults(currentAnalysis);
      resultsSection.classList.remove('hidden');
      factCheckSection.classList.remove('hidden');

      // URL 업데이트 (공유 가능하도록)
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

  // AI 쿼리 최적화 함수
  async function optimizeQuery(userInput, context) {
    const response = await fetch(`${API_BASE_URL}/api/optimize-query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_input: userInput,
        context: {
          video_title: context.video_title || '',
          key_claims: context.key_claims || [],
          related_countries: currentAnalysis?.related_countries || []
        }
      }),
    });

    if (!response.ok) {
      throw new Error('쿼리 최적화 실패');
    }

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.error || '쿼리 최적화 실패');
    }

    return {
      search_keywords_en: data.search_keywords || [userInput],
      target_country_codes: data.target_countries || [],
      interpreted_intent: data.interpreted_intent || userInput
    };
  }

  // 2차 분석: 다양한 관점 찾기 (AI 최적화 적용)
  factCheckBtn.addEventListener('click', async () => {
    const customClaimInput = document.getElementById('customClaimInput');
    const userInput = customClaimInput ? customClaimInput.value.trim() : '';

    // 0. 기본 선택된 주장들 수집
    const selectedClaims = Array.from(
      document.querySelectorAll('#keyClaims input[type="checkbox"]:checked')
    ).map(input => input.value);

    // 사용자 입력도 없고, 선택된 주장도 없으면 에러
    if (!userInput && selectedClaims.length === 0) {
      showError('위의 주장을 선택하거나, 직접 주장을 입력해주세요');
      return;
    }

    clearError();
    factCheckBtn.disabled = true;

    try {
      let allClaims = [...selectedClaims];

      // ============================================================
      // Step 1: 사용자 입력이 있다면 -> AI 최적화 (Optimize)
      // ============================================================
      if (userInput) {
        showLoading(true, '💭 AI가 질문을 분석하고 있습니다...');

        // 현재 분석 중인 영상의 맥락 정보
        const context = {
          video_title: currentAnalysis?.title || '',
          key_claims: currentAnalysis?.key_claims || []
        };

        try {
          const optimizedData = await optimizeQuery(userInput, context);

          // 💡 UX 핵심: 사용자에게 중간 과정 보여주기
          const keywordsPreview = optimizedData.search_keywords_en.slice(0, 3).join(', ');
          showLoading(true, `🔍 핵심 키워드 [${keywordsPreview}] 등으로 전 세계 검색 중...`);

          // 최적화된 결과를 검색 대상에 추가
          allClaims.push(userInput);

        } catch (optError) {
          console.warn('AI 최적화 실패, 원본 입력 사용:', optError);
          // 실패해도 멈추지 않고 원본 입력으로 검색 시도 (Fallback)
          allClaims.push(userInput);
          showLoading(true, '🔍 다양한 관점의 출처를 찾고 있습니다...');
        }
      } else {
        // 사용자 입력 없을 땐 바로 검색 메시지
        showLoading(true, '🔍 다양한 관점의 출처를 찾고 있습니다...');
      }

      // ============================================================
      // Step 2: 검색 실행
      // ============================================================
      const url = urlInput.value.trim();
      const inputType = document.querySelector('input[name="inputType"]:checked').value;

      // [중요] 기존 분석 키워드 + 이번에 추가된 키워드(allClaims)를 합쳐서 전송
      let finalSearchKeywords = currentAnalysis?.search_keywords?.flat() || [];
      finalSearchKeywords = finalSearchKeywords.concat(allClaims); // 배열 합치기

      const response = await fetch(`${API_BASE_URL}/api/find-sources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          inputType,
          selected_claims: allClaims,
          // 수정된 통합 키워드 목록 전송
          search_keywords: finalSearchKeywords,
          related_countries: currentAnalysis?.related_countries || []
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || '기사 검색 실패');
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || '기사 검색 실패');
      }

      displaySourcesResults(data.result, data.articles);

    } catch (err) {
      showError(err.message);
    } finally {
      showLoading(false);
      factCheckBtn.disabled = false;
    }
  });

  // 분석 결과 표시
  function displayAnalysisResults(analysis) {
    keyClaimsDiv.innerHTML = '';

    // 제목
    const title = document.createElement('h3');
    title.textContent = '주요 주장';
    title.className = 'section-title';
    keyClaimsDiv.appendChild(title);

    // 주장 체크박스
    if (analysis.key_claims && analysis.key_claims.length > 0) {
      const claimsContainer = document.createElement('div');
      claimsContainer.className = 'claims-list';

      analysis.key_claims.forEach((claim, index) => {
        const claimEl = document.createElement('div');
        claimEl.className = 'claim-item';
        claimEl.innerHTML = `
          <input type="checkbox" id="claim-${index}" value="${escapeHtml(claim)}" class="claim-checkbox">
          <label for="claim-${index}" class="claim-label">${escapeHtml(claim)}</label>
        `;
        claimsContainer.appendChild(claimEl);
      });

      keyClaimsDiv.appendChild(claimsContainer);
    }

    // 요약
    if (analysis.summary) {
      const summaryDiv = document.createElement('div');
      summaryDiv.className = 'info-section';
      summaryDiv.innerHTML = `
        <h4 class="info-title">요약</h4>
        <p class="info-text">${escapeHtml(analysis.summary)}</p>
      `;
      keyClaimsDiv.appendChild(summaryDiv);
    }

    // 관련 국가
    if (analysis.related_countries && analysis.related_countries.length > 0) {
      const countriesDiv = document.createElement('div');
      countriesDiv.className = 'info-section';
      countriesDiv.innerHTML = `
        <h4 class="info-title">관련 국가</h4>
        <div class="tags">
          ${analysis.related_countries.map(c => `<span class="tag">${escapeHtml(c)}</span>`).join('')}
        </div>
      `;
      keyClaimsDiv.appendChild(countriesDiv);
    }

    // 주제
    if (analysis.topics && analysis.topics.length > 0) {
      const topicsDiv = document.createElement('div');
      topicsDiv.className = 'info-section';
      topicsDiv.innerHTML = `
        <h4 class="info-title">주제</h4>
        <div class="tags">
          ${analysis.topics.map(t => `<span class="tag tag-topic">${escapeHtml(t)}</span>`).join('')}
        </div>
      `;
      keyClaimsDiv.appendChild(topicsDiv);
    }
  }

  // 관련 기사 및 신뢰도 표시 (입장별 그룹화)
  function displaySourcesResults(analysis, articles) {
    factCheckResultsDiv.innerHTML = '';

    const results = analysis.results || [];

    if (results.length === 0) {
      factCheckResultsDiv.innerHTML = '<p class="no-results">다양한 관점의 출처를 찾을 수 없습니다.</p>';
      return;
    }

    results.forEach((result, idx) => {
      const resultEl = document.createElement('div');
      resultEl.className = 'source-result';

      // 주장
      const claimEl = document.createElement('div');
      claimEl.className = 'claim-text';
      claimEl.textContent = `📌 "${result.claim}"`;
      resultEl.appendChild(claimEl);

      // 입장 분포 요약
      const metrics = result.diversity_metrics || {};
      const distribution = metrics.stance_distribution || {};
      const totalCount = metrics.total_sources || 0;

      if (totalCount > 0) {
        const summaryEl = document.createElement('div');
        summaryEl.className = 'stance-summary';
        summaryEl.innerHTML = `
          <h5 class="section-subtitle">입장 분포 (총 ${totalCount}개 기사)</h5>
          <div class="stance-stats">
            <span class="stance-stat supporting">✅ 지지: ${distribution.supporting || 0}개</span>
            <span class="stance-stat opposing">❌ 반대: ${distribution.opposing || 0}개</span>
            <span class="stance-stat neutral">⚪ 중립: ${distribution.neutral || 0}개</span>
          </div>
        `;
        resultEl.appendChild(summaryEl);
      }

      // 지지 입장 기사들
      const supportingEvidence = result.supporting_evidence || {};
      if (supportingEvidence.count > 0) {
        const supportingContainer = createStanceSection(
          'supporting',
          '✅ 이 주장을 지지하는 보도',
          supportingEvidence.articles,
          supportingEvidence.common_arguments
        );
        resultEl.appendChild(supportingContainer);
      }

      // 반대 입장 기사들
      const opposingEvidence = result.opposing_evidence || {};
      if (opposingEvidence.count > 0) {
        const opposingContainer = createStanceSection(
          'opposing',
          '❌ 이 주장에 반대하는 보도',
          opposingEvidence.articles,
          opposingEvidence.common_arguments
        );
        resultEl.appendChild(opposingContainer);
      }

      // 중립 보도
      const neutralCoverage = result.neutral_coverage || {};
      if (neutralCoverage.count > 0) {
        const neutralContainer = createStanceSection(
          'neutral',
          '⚪ 중립적/사실 중심 보도',
          neutralCoverage.articles,
          []
        );
        resultEl.appendChild(neutralContainer);
      }

      factCheckResultsDiv.appendChild(resultEl);
    });

    // 헬퍼 함수: 입장별 섹션 생성
    function createStanceSection(stanceType, title, articles, commonArguments) {
      const container = document.createElement('div');
      container.className = `stance-section stance-${stanceType}`;

      // 섹션 헤더
      const header = document.createElement('div');
      header.className = 'stance-header';
      header.innerHTML = `
        <h5 class="stance-title">${title} (${articles.length}개)</h5>
      `;
      container.appendChild(header);

      // 공통 논거 (있는 경우)
      if (commonArguments && commonArguments.length > 0) {
        const argsEl = document.createElement('div');
        argsEl.className = 'common-arguments';
        argsEl.innerHTML = `
          <strong>공통 논거:</strong>
          <ul>
            ${commonArguments.map(arg => `<li>${escapeHtml(arg)}</li>`).join('')}
          </ul>
        `;
        container.appendChild(argsEl);
      }

      // 기사 목록
      const articlesContainer = document.createElement('div');
      articlesContainer.className = 'related-articles';

      articles.forEach(article => {
        const articleEl = document.createElement('div');
        articleEl.className = 'article-card';

        // 신뢰도 점수에 따른 색상
        const credibility = article.credibility || 50;
        let credibilityClass = 'medium';
        if (credibility >= 80) credibilityClass = 'high';
        else if (credibility < 60) credibilityClass = 'low';

        // 분석 정보
        const analysis = article.analysis || {};
        const confidence = analysis.confidence ? (analysis.confidence * 100).toFixed(0) : 'N/A';
        const keyEvidence = analysis.key_evidence || [];
        const framing = analysis.framing || '';

        articleEl.innerHTML = `
          <div class="article-header">
            <div class="article-source">
              <span class="source-name">${escapeHtml(article.source)}</span>
              <span class="country-flag">${getCountryFlag(article.country)}</span>
            </div>
            <div class="article-badges">
              <div class="credibility-badge ${credibilityClass}">
                <span class="credibility-score">${credibility}</span>
                <span class="credibility-label">신뢰도</span>
              </div>
              <div class="confidence-badge">
                <span class="confidence-score">${confidence}%</span>
                <span class="confidence-label">확신도</span>
              </div>
            </div>
          </div>
          <div class="article-title">
            <a href="${escapeHtml(article.url)}" target="_blank" rel="noopener noreferrer">
              ${escapeHtml(article.title)}
            </a>
          </div>
          <div class="article-meta">
            <span class="bias-tag">${escapeHtml(article.bias || 'N/A')}</span>
            <span class="date">${escapeHtml(article.published_date || 'N/A')}</span>
          </div>
          <div class="article-snippet">${escapeHtml(article.snippet || '')}</div>
          ${keyEvidence.length > 0 ? `
            <div class="key-evidence">
              <strong>핵심 근거:</strong>
              <ul>
                ${keyEvidence.map(ev => `<li>${escapeHtml(ev)}</li>`).join('')}
              </ul>
            </div>
          ` : ''}
          ${framing ? `
            <div class="framing">
              <strong>프레임:</strong> ${escapeHtml(framing)}
            </div>
          ` : ''}
        `;

        articlesContainer.appendChild(articleEl);
      });

      container.appendChild(articlesContainer);
      return container;
    }

    // 신뢰도 안내
    const guideEl = document.createElement('div');
    guideEl.className = 'credibility-guide';
    guideEl.innerHTML = `
      <h5 class="guide-title">출처 정보 안내</h5>
      <div class="guide-content">
        <div class="guide-item">
          <span class="guide-badge high">80+</span>
          <span>주요 국제 언론사</span>
        </div>
        <div class="guide-item">
          <span class="guide-badge medium">60-79</span>
          <span>일반 언론사</span>
        </div>
        <div class="guide-item">
          <span class="guide-badge low">&lt;60</span>
          <span>기타 출처</span>
        </div>
      </div>
      <p class="guide-note">
        점수는 단순 참고용입니다. 각 출처의 내용을 직접 확인하고 판단하세요.
      </p>
    `;
    factCheckResultsDiv.appendChild(guideEl);
  }

  // Helper functions
  function showLoading(isLoading, message = '분석 중...') {
    if (isLoading) {
      const loadingText = loadingDiv.querySelector('.loading-text');
      if (loadingText) {
        loadingText.textContent = message;
      }
    }
    loadingDiv.classList.toggle('hidden', !isLoading);
  }

  function showError(message) {
    errorDiv.textContent = '⚠️ ' + message;
    errorDiv.classList.remove('hidden');
    setTimeout(() => {
      errorDiv.classList.add('hidden');
    }, 5000);
  }

  function clearError() {
    errorDiv.classList.add('hidden');
  }

  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function getCountryFlag(countryCode) {
    const flags = {
      'KR': '🇰🇷',
      'US': '🇺🇸',
      'UK': '🇬🇧',
      'JP': '🇯🇵',
      'CN': '🇨🇳',
      'DE': '🇩🇪',
      'FR': '🇫🇷',
      'QA': '🇶🇦',
      'RU': '🇷🇺',
      'IN': '🇮🇳',
      'BR': '🇧🇷',
      'CA': '🇨🇦',
      'AU': '🇦🇺',
      'IT': '🇮🇹',
      'ES': '🇪🇸',
    };
    return flags[countryCode] || '🌐';
  }

  // 인기 콘텐츠 로드
  async function loadPopularContent() {
    try {
      popularList.innerHTML = '<div class="loading-small">로딩 중...</div>';

      const response = await fetch(`${API_BASE_URL}/api/history/popular?limit=10&days=7`);
      const data = await response.json();

      if (!data.success || data.count === 0) {
        popularList.innerHTML = '<p class="no-results">아직 인기 콘텐츠가 없습니다</p>';
        return;
      }

      displayHistoryList(popularList, data.data);

    } catch (err) {
      console.error('인기 콘텐츠 로드 실패:', err);
      popularList.innerHTML = `<p class="error-text">⚠️ 인기 콘텐츠를 불러올 수 없습니다<br><small>${err.message || '네트워크 오류'}</small></p>`;
    }
  }

  // 최근 분석 로드
  async function loadRecentHistory() {
    try {
      recentList.innerHTML = '<div class="loading-small">로딩 중...</div>';

      const response = await fetch(`${API_BASE_URL}/api/history/recent?limit=20`);
      const data = await response.json();

      if (!data.success || data.count === 0) {
        recentList.innerHTML = '<p class="no-results">아직 분석 기록이 없습니다</p>';
        return;
      }

      displayHistoryList(recentList, data.data);

    } catch (err) {
      console.error('최근 분석 로드 실패:', err);
      recentList.innerHTML = `<p class="error-text">⚠️ 최근 분석을 불러올 수 없습니다<br><small>${err.message || '네트워크 오류'}</small></p>`;
    }
  }

  // 히스토리 목록 표시
  function displayHistoryList(container, items) {
    container.innerHTML = '';

    items.forEach(item => {
      const itemEl = document.createElement('div');
      itemEl.className = 'history-item';

      const typeIcon = item.input_type === 'youtube' ? '📺' : '📰';
      const date = item.last_analyzed_at
        ? new Date(item.last_analyzed_at.seconds * 1000).toLocaleDateString('ko-KR')
        : 'N/A';

      itemEl.innerHTML = `
        <div class="history-item-header">
          <span class="history-type">${typeIcon} ${item.input_type === 'youtube' ? 'YouTube' : 'Article'}</span>
          <span class="history-views">조회 ${item.view_count}회</span>
        </div>
        <div class="history-title">${escapeHtml(item.title || 'No title')}</div>
        <div class="history-meta">
          ${item.topics && item.topics.length > 0
            ? `<div class="tags">${item.topics.map(t => `<span class="tag tag-small">${escapeHtml(t)}</span>`).join('')}</div>`
            : ''}
          <span class="history-date">${date}</span>
        </div>
      `;

      // 클릭 시 해당 URL 분석
      itemEl.addEventListener('click', () => {
        urlInput.value = item.url;

        // 타입 자동 선택
        if (item.input_type === 'youtube') {
          document.querySelector('input[value="youtube"]').checked = true;
        } else {
          document.querySelector('input[value="article"]').checked = true;
        }

        // 입력 탭으로 전환
        document.querySelector('.tab-btn[data-tab="input"]').click();

        // 스크롤
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });

      container.appendChild(itemEl);
    });
  }
});
