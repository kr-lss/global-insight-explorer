/**
 * UI 렌더링 로직 (ES Module)
 */

import { UI_DEFAULTS, STANCE_CONFIG } from './constants.js';
import {
  escapeHtml,
  getCountryFlag,
  getCredibilityClass,
  confidenceToPercent,
  formatFirestoreTimestamp,
  extractClaimText,
  extractSearchKeywords,
  extractTargetCountries,
} from './utils.js';

/**
 * 1차 분석 결과 렌더링 (주장, 요약, 국가, 주제)
 * @param {HTMLElement} container - 결과를 표시할 컨테이너
 * @param {Object} analysis - 분석 결과 객체
 */
export function renderAnalysisResults(container, analysis) {
  container.innerHTML = '';

  // 제목
  const title = document.createElement('h3');
  title.textContent = '주요 주장';
  title.className = 'section-title';
  container.appendChild(title);

  // 주장 체크박스 리스트
  if (analysis.key_claims && analysis.key_claims.length > 0) {
    const claimsContainer = document.createElement('div');
    claimsContainer.className = 'claims-list';

    analysis.key_claims.forEach((claim, index) => {
      const claimEl = document.createElement('div');
      claimEl.className = 'claim-item';

      // claim이 객체인 경우와 문자열인 경우(구버전 호환) 모두 처리
      const claimText = extractClaimText(claim);
      const searchKeywords = extractSearchKeywords(claim);
      const targetCountries = extractTargetCountries(claim);

      claimEl.innerHTML = `
        <input type="checkbox"
               id="claim-${index}"
               value="${escapeHtml(claimText)}"
               data-keywords='${JSON.stringify(searchKeywords)}'
               data-countries='${JSON.stringify(targetCountries)}'
               class="claim-checkbox">
        <label for="claim-${index}" class="claim-label">${escapeHtml(claimText)}</label>
      `;
      claimsContainer.appendChild(claimEl);
    });

    container.appendChild(claimsContainer);
  }

  // 커스텀 주장 입력 추가
  const customClaimDiv = document.createElement('div');
  customClaimDiv.className = 'custom-claim-box';
  customClaimDiv.style.cssText = 'margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;';
  customClaimDiv.innerHTML = `
    <label for="customClaimInput" style="display:block; margin-bottom:5px; font-size:0.9rem; color:#666;">
      직접 궁금한 점 입력 (선택사항):
    </label>
    <input type="text" id="customClaimInput" class="url-input"
           placeholder="예: 이 영상에서 말하는 금리 인상 시기가 언제인가요?">
  `;
  container.appendChild(customClaimDiv);

  // 요약
  if (analysis.summary_kr) {
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'info-section';
    summaryDiv.innerHTML = `
      <h4 class="info-title">요약</h4>
      <p class="info-text">${escapeHtml(analysis.summary_kr)}</p>
    `;
    container.appendChild(summaryDiv);
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
    container.appendChild(countriesDiv);
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
    container.appendChild(topicsDiv);
  }
}

/**
 * 2차 분석 결과 렌더링 (입장별 그룹화된 기사 표시)
 * @param {HTMLElement} container - 결과를 표시할 컨테이너
 * @param {Object} analysis - 분석 결과 객체
 * @param {Array} articles - 기사 목록
 */
export function renderSourcesResults(container, analysis, articles) {
  container.innerHTML = '';

  const results = analysis.results || [];

  if (results.length === 0) {
    container.innerHTML = '<p class="no-results">다양한 관점의 출처를 찾을 수 없습니다.</p>';
    return;
  }

  results.forEach((result) => {
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
        neutralCoverage.articles,
        []
      );
      resultEl.appendChild(neutralContainer);
    }

    container.appendChild(resultEl);
  });

  // 신뢰도 안내
  container.appendChild(createCredibilityGuide());
}

/**
 * 입장별 섹션 생성 (헬퍼 함수)
 * @param {string} stanceType - 입장 타입 ('supporting', 'opposing', 'neutral')
 * @param {Array} articles - 해당 입장의 기사 목록
 * @param {Array} commonArguments - 공통 논거 (선택사항)
 * @returns {HTMLElement} 입장 섹션 엘리먼트
 */
function createStanceSection(stanceType, articles, commonArguments) {
  const config = STANCE_CONFIG[stanceType];
  const container = document.createElement('div');
  container.className = `stance-section ${config.colorClass}`;

  // 섹션 헤더
  const header = document.createElement('div');
  header.className = 'stance-header';
  header.innerHTML = `
    <h5 class="stance-title">${config.title} (${articles.length}개)</h5>
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
    articlesContainer.appendChild(createArticleCard(article));
  });

  container.appendChild(articlesContainer);
  return container;
}

/**
 * 기사 카드 생성 (헬퍼 함수)
 * @param {Object} article - 기사 객체
 * @returns {HTMLElement} 기사 카드 엘리먼트
 */
function createArticleCard(article) {
  const articleEl = document.createElement('div');
  articleEl.className = 'article-card';

  // 신뢰도 점수에 따른 색상
  const credibility = article.credibility || UI_DEFAULTS.CREDIBILITY;
  const credibilityClass = getCredibilityClass(credibility);

  // 분석 정보
  const analysis = article.analysis || {};
  const confidence = confidenceToPercent(analysis.confidence);
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
      <span class="bias-tag">${escapeHtml(article.bias || UI_DEFAULTS.BIAS)}</span>
      <span class="date">${escapeHtml(article.published_date || UI_DEFAULTS.DATE)}</span>
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

  return articleEl;
}

/**
 * 신뢰도 안내 생성 (헬퍼 함수)
 * @returns {HTMLElement} 신뢰도 안내 엘리먼트
 */
function createCredibilityGuide() {
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
  return guideEl;
}

/**
 * 히스토리 목록 렌더링
 * @param {HTMLElement} container - 결과를 표시할 컨테이너
 * @param {Array} items - 히스토리 아이템 배열
 * @param {Function} onItemClick - 아이템 클릭 콜백
 */
export function renderHistoryList(container, items, onItemClick) {
  container.innerHTML = '';

  if (items.length === 0) {
    container.innerHTML = '<p class="no-results">아직 분석 기록이 없습니다</p>';
    return;
  }

  items.forEach(item => {
    const itemEl = document.createElement('div');
    itemEl.className = 'history-item';

    const typeIcon = item.input_type === 'youtube' ? '📺' : '📰';
    const date = formatFirestoreTimestamp(item.last_analyzed_at);

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

    // 클릭 이벤트
    itemEl.addEventListener('click', () => onItemClick(item));

    container.appendChild(itemEl);
  });
}

/**
 * 로딩 상태 표시/숨김
 * @param {HTMLElement} loadingElement - 로딩 엘리먼트
 * @param {boolean} isLoading - 로딩 여부
 * @param {string} message - 로딩 메시지
 */
export function toggleLoading(loadingElement, isLoading, message = UI_DEFAULTS.LOADING_MESSAGE) {
  if (isLoading) {
    const loadingText = loadingElement.querySelector('.loading-text');
    if (loadingText) {
      loadingText.textContent = message;
    }
  }
  loadingElement.classList.toggle('hidden', !isLoading);
}

/**
 * 에러 메시지 표시
 * @param {HTMLElement} errorElement - 에러 엘리먼트
 * @param {string} message - 에러 메시지
 * @param {number} displayTime - 표시 시간 (ms)
 */
export function showError(errorElement, message, displayTime = UI_DEFAULTS.ERROR_DISPLAY_TIME) {
  errorElement.textContent = '⚠️ ' + message;
  errorElement.classList.remove('hidden');

  setTimeout(() => {
    errorElement.classList.add('hidden');
  }, displayTime);
}

/**
 * 에러 메시지 숨김
 * @param {HTMLElement} errorElement - 에러 엘리먼트
 */
export function clearError(errorElement) {
  errorElement.classList.add('hidden');
}
