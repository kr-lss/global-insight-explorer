/**
 * 공유 유틸리티 함수
 * main.js와 popup.js에서 사용하는 공통 함수들
 */

/**
 * HTML 이스케이프 (XSS 방지)
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * 국가 코드에 따른 국기 이모지 반환
 */
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
    'ES': '🇪🇸',
    'IT': '🇮🇹',
    'CA': '🇨🇦',
    'AU': '🇦🇺',
    'IN': '🇮🇳',
    'BR': '🇧🇷',
    'RU': '🇷🇺',
  };
  return flags[countryCode] || '🌐';
}

/**
 * 1차 분석 결과 표시 (주장, 요약, 국가, 주제)
 * @param {HTMLElement} container - 결과를 표시할 컨테이너
 * @param {Object} analysis - 분석 결과 객체
 */
function displayAnalysisResults(container, analysis) {
  container.innerHTML = '';

  // 제목
  const title = document.createElement('h3');
  title.textContent = '📋 주요 주장';
  container.appendChild(title);

  // 주장 체크박스
  analysis.key_claims.forEach((claim, index) => {
    const claimEl = document.createElement('div');
    claimEl.className = 'claim-item';
    claimEl.innerHTML = `
      <input type="checkbox" id="claim-${index}" value="${escapeHtml(claim)}">
      <label for="claim-${index}">${escapeHtml(claim)}</label>
    `;
    container.appendChild(claimEl);
  });

  // 요약
  if (analysis.summary) {
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'info-section';
    summaryDiv.innerHTML = `
      <h4>📝 요약</h4>
      <p>${escapeHtml(analysis.summary)}</p>
    `;
    container.appendChild(summaryDiv);
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
    container.appendChild(countriesDiv);
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
    container.appendChild(topicsDiv);
  }
}

/**
 * 2차 분석 결과 표시 (관련 기사 및 신뢰도)
 * @param {HTMLElement} container - 결과를 표시할 컨테이너
 * @param {Object} analysis - 분석 결과 객체
 * @param {Array} articles - 기사 목록
 */
function displaySourcesResults(container, analysis, articles) {
  container.innerHTML = '';

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

    container.appendChild(resultEl);
  });

  // 신뢰도 안내
  const guideEl = document.createElement('div');
  guideEl.className = 'credibility-guide';
  guideEl.innerHTML = `
    <h5>📊 출처 정보 안내</h5>
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
  container.appendChild(guideEl);
}
