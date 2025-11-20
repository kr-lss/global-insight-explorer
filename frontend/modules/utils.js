/**
 * 프론트엔드 유틸리티 함수 (ES Module)
 */

import { CREDIBILITY, COUNTRY_FLAGS, UI_DEFAULTS } from './constants.js';

/**
 * HTML 특수문자 이스케이프 (XSS 방지)
 * @param {string} text - 이스케이프할 텍스트
 * @returns {string} 이스케이프된 HTML
 */
export function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * 국가 코드로 국기 이모지 반환
 * @param {string} countryCode - ISO 국가 코드 (예: 'US', 'KR')
 * @returns {string} 국기 이모지
 */
export function getCountryFlag(countryCode) {
  return COUNTRY_FLAGS[countryCode] || '🌐';
}

/**
 * 신뢰도 점수에 따른 CSS 클래스 반환
 * @param {number} credibility - 신뢰도 점수 (0-100)
 * @returns {string} CSS 클래스명
 */
export function getCredibilityClass(credibility) {
  const score = credibility || UI_DEFAULTS.CREDIBILITY;

  if (score >= CREDIBILITY.HIGH.min) {
    return CREDIBILITY.HIGH.class;
  } else if (score >= CREDIBILITY.MEDIUM.min) {
    return CREDIBILITY.MEDIUM.class;
  } else {
    return CREDIBILITY.LOW.class;
  }
}

/**
 * 확신도를 퍼센트로 변환
 * @param {number} confidence - 확신도 (0-1)
 * @returns {string} 퍼센트 문자열 또는 'N/A'
 */
export function confidenceToPercent(confidence) {
  if (confidence === undefined || confidence === null) return 'N/A';
  return (confidence * 100).toFixed(UI_DEFAULTS.CONFIDENCE_DECIMALS);
}

/**
 * URL 유효성 검사
 * @param {string} url - 검사할 URL
 * @returns {boolean} 유효 여부
 */
export function isValidUrl(url) {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * YouTube URL 감지
 * @param {string} url - 검사할 URL
 * @returns {boolean} YouTube URL 여부
 */
export function isYouTubeUrl(url) {
  return url.includes('youtube.com') || url.includes('youtu.be');
}

/**
 * Firestore 타임스탬프를 로컬 날짜 문자열로 변환
 * @param {Object} timestamp - Firestore 타임스탬프 객체 {seconds, nanoseconds}
 * @returns {string} 로컬 날짜 문자열
 */
export function formatFirestoreTimestamp(timestamp) {
  if (!timestamp || !timestamp.seconds) return UI_DEFAULTS.DATE;
  return new Date(timestamp.seconds * 1000).toLocaleDateString('ko-KR');
}

/**
 * claim 객체에서 텍스트 추출 (구버전 호환)
 * @param {string|Object} claim - claim 문자열 또는 객체
 * @returns {string} claim 텍스트
 */
export function extractClaimText(claim) {
  return typeof claim === 'string' ? claim : claim.claim_kr;
}

/**
 * claim 객체에서 검색 키워드 추출
 * @param {string|Object} claim - claim 문자열 또는 객체
 * @returns {Array<string>} 검색 키워드 배열
 */
export function extractSearchKeywords(claim) {
  return typeof claim === 'object' ? (claim.search_keywords_en || []) : [];
}

/**
 * claim 객체에서 타겟 국가 코드 추출
 * @param {string|Object} claim - claim 문자열 또는 객체
 * @returns {Array<string>} 국가 코드 배열
 */
export function extractTargetCountries(claim) {
  return typeof claim === 'object' ? (claim.target_country_codes || []) : [];
}
