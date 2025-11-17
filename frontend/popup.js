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

  // 백엔드 서버 주소 (환경에 따라 자동 설정)
  const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:8080'
    : `${window.location.protocol}//${window.location.hostname}${window.location.port ? ':' + window.location.port : ''}`;
  
  let currentAnalysis = null;

  // 현재 탭 URL 가져오기
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0] && tabs[0].url) {
      urlInput.value = tabs[0].url;
      
      // 자동 감지
      if (tabs[0].url.includes('youtube.com') || tabs[0].url.includes('youtu.be')) {
        document.querySelector('input[value="youtube"]').checked = true;
      } else {
        document.querySelector('input[value="article"]').checked = true;
      }
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

    showLoading(true, '주장을 분석하고 있습니다...');
    clearError();
    resultsSection.classList.add('hidden');
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

    } catch (err) {
      showError(err.message);
    } finally {
      showLoading(false);
      analyzeBtn.disabled = false;
    }
  });

  // 2차 분석: 관련 기사 찾기
  factCheckBtn.addEventListener('click', async () => {
    const selectedClaims = Array.from(
      document.querySelectorAll('#keyClaims input[type="checkbox"]:checked')
    ).map(input => input.value);

    if (selectedClaims.length === 0) {
      showError('확인할 주장을 최소 1개 선택해주세요');
      return;
    }

    showLoading(true, '관련 기사를 검색하고 있습니다...');
    clearError();
    factCheckBtn.disabled = true;

    try {
      const url = urlInput.value.trim();
      const inputType = document.querySelector('input[name="inputType"]:checked').value;
      
      const response = await fetch(`${API_BASE_URL}/api/find-sources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          url, 
          inputType,
          selected_claims: selectedClaims,
          search_keywords: currentAnalysis?.search_keywords?.flat() || selectedClaims,
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
    title.textContent = '📋 주요 주장';
    keyClaimsDiv.appendChild(title);
    
    // 주장 체크박스
    analysis.key_claims.forEach((claim, index) => {
      const claimEl = document.createElement('div');
      claimEl.className = 'claim-item';
      claimEl.innerHTML = `
        <input type="checkbox" id="claim-${index}" value="${escapeHtml(claim)}">
        <label for="claim-${index}">${escapeHtml(claim)}</label>
      `;
      keyClaimsDiv.appendChild(claimEl);
    });
    
    // 요약
    if (analysis.summary) {
      const summaryDiv = document.createElement('div');
      summaryDiv.className = 'info-section';
      summaryDiv.innerHTML = `
        <h4>📝 요약</h4>
        <p>${escapeHtml(analysis.summary)}</p>
      `;
      keyClaimsDiv.appendChild(summaryDiv);
    }
    
    // 관련 국가
    if (analysis.related_countries && analysis.related_countries.length > 0) {
      const countriesDiv = document.createElement('div');
      countriesDiv.className = 'info-section';
      countriesDiv.innerHTML = `
        <h4>🌏 관련 국가</h4>
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
        <h4>🏷️ 주제</h4>
        <div class="tags">
          ${analysis.topics.map(t => `<span class="tag tag-topic">${escapeHtml(t)}</span>`).join('')}
        </div>
      `;
      keyClaimsDiv.appendChild(topicsDiv);
    }
  }

  // 관련 기사 및 신뢰도 표시
  function displaySourcesResults(analysis, articles) {
    factCheckResultsDiv.innerHTML = '';
    
    const results = analysis.results || [];
    
    results.forEach((result, idx) => {
      const resultEl = document.createElement('div');
      resultEl.className = 'source-result';
      
      // 주장
      const claimEl = document.createElement('div');
      claimEl.className = 'claim-text';
      claimEl.textContent = result.claim;
      resultEl.appendChild(claimEl);
      
      // 관련 기사들
      const relatedArticles = result.related_articles || [];
      if (relatedArticles.length > 0) {
        const articlesContainer = document.createElement('div');
        articlesContainer.className = 'related-articles';
        
        const articlesTitle = document.createElement('h5');
        articlesTitle.textContent = `📰 관련 기사 (${relatedArticles.length}개)`;
        articlesContainer.appendChild(articlesTitle);
        
        relatedArticles.forEach(articleIdx => {
          const article = articles[articleIdx - 1]; // 1-based index
          if (!article) return;
          
          const articleEl = document.createElement('div');
          articleEl.className = 'article-card';
          
          // 신뢰도 점수에 따른 색상
          const credibility = article.credibility || 50;
          let credibilityClass = 'medium';
          if (credibility >= 80) credibilityClass = 'high';
          else if (credibility < 60) credibilityClass = 'low';
          
          articleEl.innerHTML = `
            <div class="article-header">
              <div class="article-source">
                <span class="source-name">${escapeHtml(article.source)}</span>
                <span class="country-flag">${getCountryFlag(article.country)}</span>
              </div>
              <div class="credibility-badge ${credibilityClass}">
                <span class="credibility-score">${credibility}</span>
                <span class="credibility-label">신뢰도</span>
              </div>
            </div>
            <div class="article-title">
              <a href="${escapeHtml(article.url)}" target="_blank">
                ${escapeHtml(article.title)}
              </a>
            </div>
            <div class="article-meta">
              <span class="bias-tag">${escapeHtml(article.bias)}</span>
              <span class="date">${escapeHtml(article.published_date || 'N/A')}</span>
            </div>
            <div class="article-snippet">${escapeHtml(article.snippet)}</div>
          `;
          
          articlesContainer.appendChild(articleEl);
        });
        
        resultEl.appendChild(articlesContainer);
      }
      
      // 관점 분석
      if (result.perspectives) {
        const perspectivesDiv = document.createElement('div');
        perspectivesDiv.className = 'perspectives-section';
        perspectivesDiv.innerHTML = '<h5>🔍 각 기사의 관점</h5>';
        
        Object.entries(result.perspectives).forEach(([key, value]) => {
          const perspectiveEl = document.createElement('div');
          perspectiveEl.className = 'perspective-item';
          perspectiveEl.innerHTML = `
            <strong>${key}:</strong> ${escapeHtml(value)}
          `;
          perspectivesDiv.appendChild(perspectiveEl);
        });
        
        resultEl.appendChild(perspectivesDiv);
      }
      
      // 추가 맥락
      if (result.additional_context) {
        const contextDiv = document.createElement('div');
        contextDiv.className = 'context-section';
        contextDiv.innerHTML = `
          <h5>💡 알아야 할 맥락</h5>
          <p>${escapeHtml(result.additional_context)}</p>
        `;
        resultEl.appendChild(contextDiv);
      }
      
      // 다루는 국가들
      if (result.coverage_countries && result.coverage_countries.length > 0) {
        const coverageDiv = document.createElement('div');
        coverageDiv.className = 'coverage-section';
        coverageDiv.innerHTML = `
          <h5>🌍 보도 국가</h5>
          <div class="tags">
            ${result.coverage_countries.map(c => `<span class="tag">${escapeHtml(c)}</span>`).join('')}
          </div>
        `;
        resultEl.appendChild(coverageDiv);
      }

      factCheckResultsDiv.appendChild(resultEl);
    });

    // 신뢰도 안내
    const guideEl = document.createElement('div');
    guideEl.className = 'credibility-guide';
    guideEl.innerHTML = `
      <h5>📊 신뢰도 점수 안내</h5>
      <div class="guide-content">
        <div class="guide-item">
          <span class="guide-badge high">80+</span>
          <span>높은 신뢰도 - 국제적으로 인정받는 언론사</span>
        </div>
        <div class="guide-item">
          <span class="guide-badge medium">60-79</span>
          <span>중간 신뢰도 - 일반적인 언론사</span>
        </div>
        <div class="guide-item">
          <span class="guide-badge low">&lt;60</span>
          <span>낮은 신뢰도 - 편향 가능성 주의</span>
        </div>
      </div>
      <p class="guide-note">
        ⚠️ 신뢰도는 참고용입니다. 최종 판단은 사용자가 직접 하세요.
      </p>
    `;
    factCheckResultsDiv.appendChild(guideEl);
  }

  // Helper functions
  function showLoading(isLoading, message = '분석 중...') {
    if (isLoading) {
      loadingDiv.querySelector('p').textContent = message;
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
    };
    return flags[countryCode] || '🌐';
  }
});