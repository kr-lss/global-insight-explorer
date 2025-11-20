/**
 * Global Insight Explorer - Browser Extension Popup
 * (ES Module 리팩토링 버전 - claims_data 구조 적용)
 */

import { MESSAGES } from './modules/constants.js';
import { isValidUrl } from './modules/utils.js';
import { analyzeContent, findSources } from './modules/api.js';
import {
  renderAnalysisResults,
  renderSourcesResults,
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
};

// 상태 관리
let currentAnalysis = null;

/**
 * 애플리케이션 초기화
 */
function init() {
  setupEventListeners();
  loadCurrentTabUrl();
}

/**
 * 이벤트 리스너 설정
 */
function setupEventListeners() {
  // 1차 분석
  elements.analyzeBtn.addEventListener('click', handleAnalyze);

  // 2차 분석
  elements.factCheckBtn.addEventListener('click', handleFindSources);
}

/**
 * 현재 탭 URL 가져오기 (Chrome Extension API)
 */
function loadCurrentTabUrl() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0] && tabs[0].url) {
      elements.urlInput.value = tabs[0].url;

      // 자동 타입 감지
      if (tabs[0].url.includes('youtube.com') || tabs[0].url.includes('youtu.be')) {
        document.querySelector('input[value="youtube"]').checked = true;
      } else {
        document.querySelector('input[value="article"]').checked = true;
      }
    }
  });
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
  elements.analyzeBtn.disabled = true;

  try {
    currentAnalysis = await analyzeContent(url, inputType);
    renderAnalysisResults(elements.keyClaimsDiv, currentAnalysis);
    elements.resultsSection.classList.remove('hidden');
    elements.factCheckSection.classList.remove('hidden');

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

  // ✅ 수정: 선택된 체크박스에서 완전한 데이터 수집 (claims_data 구조)
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

  // 직접 입력한 주장은 claim_kr만 있고 나머지는 빈 배열 (백엔드에서 AI 생성)
  if (customClaim) {
    selectedClaimsData.push({
      claim_kr: customClaim,
      search_keywords_en: [],
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

    // ✅ 수정: findSources API에 claims_data 전달
    const { result, articles } = await findSources(url, inputType, selectedClaimsData);
    renderSourcesResults(elements.factCheckResultsDiv, result, articles);

  } catch (err) {
    showError(elements.errorDiv, err.message);
  } finally {
    toggleLoading(elements.loadingDiv, false);
    elements.factCheckBtn.disabled = false;
  }
}

// 애플리케이션 시작
document.addEventListener('DOMContentLoaded', init);
