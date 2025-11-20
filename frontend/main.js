/**
 * Global Insight Explorer - Main Application
 * (ES Module 리팩토링 버전)
 */

import { MESSAGES } from './modules/constants.js';
import { isValidUrl, isYouTubeUrl } from './modules/utils.js';
import { analyzeContent, findSources, loadPopularContent, loadRecentHistory } from './modules/api.js';
import {
  renderAnalysisResults,
  renderSourcesResults,
  renderHistoryList,
  toggleLoading,
  showError,
  clearError,
} from './modules/ui.js';

// DOM 요소
const elements = {
  urlInput: document.getElementById('urlInput'),
  analyzeBtn: document.getElementById('analyzeBtn'),
  factCheckBtn: document.getElementById('factCheckBtn'),
  loadingDiv: document.getElementById('loading'),
  resultsSection: document.getElementById('resultsSection'),
  keyClaimsDiv: document.getElementById('keyClaims'),
  factCheckSection: document.getElementById('factCheckSection'),
  factCheckResultsDiv: document.getElementById('factCheckResults'),
  errorDiv: document.getElementById('error'),
  inputTab: document.getElementById('inputTab'),
  popularTab: document.getElementById('popularTab'),
  recentTab: document.getElementById('recentTab'),
  popularList: document.getElementById('popularList'),
  recentList: document.getElementById('recentList'),
  tabBtns: document.querySelectorAll('.tab-btn'),
};

// 상태 관리
let currentAnalysis = null;

/**
 * 애플리케이션 초기화
 */
function init() {
  setupEventListeners();
  handleSharedUrl();
}

/**
 * 이벤트 리스너 설정
 */
function setupEventListeners() {
  // 탭 전환
  elements.tabBtns.forEach(btn => {
    btn.addEventListener('click', () => handleTabSwitch(btn.dataset.tab));
  });

  // Enter 키로 분석 시작
  elements.urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      elements.analyzeBtn.click();
    }
  });

  // 1차 분석
  elements.analyzeBtn.addEventListener('click', handleAnalyze);

  // 2차 분석
  elements.factCheckBtn.addEventListener('click', handleFindSources);
}

/**
 * URL 파라미터에서 URL 읽기 (공유 링크 지원)
 */
function handleSharedUrl() {
  const urlParams = new URLSearchParams(window.location.search);
  const sharedUrl = urlParams.get('url');

  if (sharedUrl) {
    elements.urlInput.value = decodeURIComponent(sharedUrl);

    // 자동 타입 감지
    if (isYouTubeUrl(sharedUrl)) {
      document.querySelector('input[value="youtube"]').checked = true;
    } else {
      document.querySelector('input[value="article"]').checked = true;
    }
  }
}

/**
 * 탭 전환 핸들러
 */
function handleTabSwitch(tabName) {
  // 모든 탭 버튼 비활성화
  elements.tabBtns.forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');

  // 모든 섹션 숨기기
  elements.inputTab.classList.add('hidden');
  elements.popularTab.classList.add('hidden');
  elements.recentTab.classList.add('hidden');
  elements.resultsSection.classList.add('hidden');

  // 선택된 탭 표시
  if (tabName === 'input') {
    elements.inputTab.classList.remove('hidden');
  } else if (tabName === 'popular') {
    elements.popularTab.classList.remove('hidden');
    handleLoadPopular();
  } else if (tabName === 'recent') {
    elements.recentTab.classList.remove('hidden');
    handleLoadRecent();
  }
}

/**
 * 1차 분석 핸들러 (주장 추출)
 */
async function handleAnalyze() {
  const url = elements.urlInput.value.trim();
  const inputType = document.querySelector('input[name="inputType"]:checked').value;

  // URL 유효성 검사
  if (!url) {
    showError(elements.errorDiv, MESSAGES.ERROR.NO_URL);
    return;
  }

  if (!isValidUrl(url)) {
    showError(elements.errorDiv, MESSAGES.ERROR.INVALID_URL);
    return;
  }

  toggleLoading(elements.loadingDiv, true, MESSAGES.LOADING.ANALYZING);
  clearError(elements.errorDiv);
  elements.resultsSection.classList.add('hidden');
  elements.factCheckSection.classList.add('hidden');
  elements.analyzeBtn.disabled = true;

  try {
    currentAnalysis = await analyzeContent(url, inputType);
    renderAnalysisResults(elements.keyClaimsDiv, currentAnalysis);
    elements.resultsSection.classList.remove('hidden');
    elements.factCheckSection.classList.remove('hidden');

    // URL 업데이트 (공유 가능하도록)
    const newUrl = new URL(window.location);
    newUrl.searchParams.set('url', url);
    window.history.pushState({}, '', newUrl);

  } catch (err) {
    showError(elements.errorDiv, err.message);
  } finally {
    toggleLoading(elements.loadingDiv, false);
    elements.analyzeBtn.disabled = false;
  }
}

/**
 * 2차 분석 핸들러 (다양한 관점 찾기)
 */
async function handleFindSources() {
  const checkboxes = document.querySelectorAll('#keyClaims input[type="checkbox"]');

  // 선택된 체크박스에서 완전한 데이터 수집
  const selectedClaimsData = Array.from(checkboxes)
    .filter(cb => cb.checked)
    .map(cb => ({
      claim_kr: cb.value,
      search_keywords_en: JSON.parse(cb.dataset.keywords || '[]'),
      target_country_codes: JSON.parse(cb.dataset.countries || '[]')
    }));

  // 직접 입력한 주장 가져오기
  const customClaimInput = document.getElementById('customClaimInput');
  const customClaim = customClaimInput ? customClaimInput.value.trim() : '';

  // 직접 입력한 주장은 claim_kr만 있고 나머지는 빈 배열
  if (customClaim) {
    selectedClaimsData.push({
      claim_kr: customClaim,
      search_keywords_en: [],  // 백엔드에서 처리
      target_country_codes: []
    });
  }

  if (selectedClaimsData.length === 0) {
    showError(elements.errorDiv, MESSAGES.ERROR.NO_CLAIMS);
    return;
  }

  toggleLoading(elements.loadingDiv, true, MESSAGES.LOADING.SEARCHING);
  clearError(elements.errorDiv);
  elements.factCheckBtn.disabled = true;

  try {
    const url = elements.urlInput.value.trim();
    const inputType = document.querySelector('input[name="inputType"]:checked').value;

    const { result, articles } = await findSources(url, inputType, selectedClaimsData);
    renderSourcesResults(elements.factCheckResultsDiv, result, articles);

  } catch (err) {
    showError(elements.errorDiv, err.message);
  } finally {
    toggleLoading(elements.loadingDiv, false);
    elements.factCheckBtn.disabled = false;
  }
}

/**
 * 인기 콘텐츠 로드 핸들러
 */
async function handleLoadPopular() {
  try {
    elements.popularList.innerHTML = '<div class="loading-small">로딩 중...</div>';

    const items = await loadPopularContent(10, 7);

    if (items.length === 0) {
      elements.popularList.innerHTML = '<p class="no-results">아직 인기 콘텐츠가 없습니다</p>';
      return;
    }

    renderHistoryList(elements.popularList, items, handleHistoryItemClick);

  } catch (err) {
    console.error('인기 콘텐츠 로드 실패:', err);
    elements.popularList.innerHTML = `<p class="error-text">⚠️ 인기 콘텐츠를 불러올 수 없습니다<br><small>${err.message || '네트워크 오류'}</small></p>`;
  }
}

/**
 * 최근 분석 로드 핸들러
 */
async function handleLoadRecent() {
  try {
    elements.recentList.innerHTML = '<div class="loading-small">로딩 중...</div>';

    const items = await loadRecentHistory(20);

    if (items.length === 0) {
      elements.recentList.innerHTML = '<p class="no-results">아직 분석 기록이 없습니다</p>';
      return;
    }

    renderHistoryList(elements.recentList, items, handleHistoryItemClick);

  } catch (err) {
    console.error('최근 분석 로드 실패:', err);
    elements.recentList.innerHTML = `<p class="error-text">⚠️ 최근 분석을 불러올 수 없습니다<br><small>${err.message || '네트워크 오류'}</small></p>`;
  }
}

/**
 * 히스토리 아이템 클릭 핸들러
 */
function handleHistoryItemClick(item) {
  elements.urlInput.value = item.url;

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
}

// 애플리케이션 시작
document.addEventListener('DOMContentLoaded', init);
